# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

from collections import defaultdict
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, date_diff, get_datetime, getdate, nowdate

APP_ROLES = [
	"SOP Manager",
	"SOP Author",
	"SOP Approver",
	"SOP Reviewer",
	"SOP Trainer",
	"SOP Reader",
	"System Manager",
]
LIFECYCLE = ["Draft", "In Review", "Approved", "Effective", "Under Revision", "Retired"]
IN_FORCE = ("Effective", "Under Revision")
PERIODS = (30, 90, 365)
SOON = 30
TOP = 8
FIELDS = [
	"name",
	"sop_no",
	"title",
	"status",
	"version",
	"space",
	"owner",
	"process_owner",
	"review_due",
]


def scope_of_viewer():
	roles = set(frappe.get_roles())

	if {"SOP Manager", "System Manager"} & roles:
		return "all"

	if "SOP Author" in roles:
		return "mine"

	frappe.throw(_("Insights are available to authors and managers."), frappe.PermissionError)


def procedures(scope, space):
	filters = {"space": space} if space else {}

	if scope == "mine":
		me = frappe.session.user
		return frappe.get_all(
			"SOP",
			filters=filters,
			or_filters={"owner": me, "process_owner": me},
			fields=FIELDS,
			limit_page_length=0,
		)

	return frappe.get_all("SOP", filters=filters, fields=FIELDS, limit_page_length=0)


def audience():
	holders = set(
		frappe.get_all(
			"Has Role",
			filters={"parenttype": "User", "role": ("in", APP_ROLES)},
			pluck="parent",
			limit_page_length=0,
		)
	) - {"Administrator", "Guest"}

	if not holders:
		return set()

	return set(
		frappe.get_all(
			"User",
			filters={"name": ("in", list(holders)), "enabled": 1, "user_type": "System User"},
			pluck="name",
			limit_page_length=0,
		)
	)


def people(users):
	users = [user for user in set(users) if user]
	if not users:
		return {}

	rows = frappe.get_all(
		"User",
		filters={"name": ("in", users)},
		fields=["name", "full_name", "user_image"],
		limit_page_length=0,
	)
	return {
		row.name: {"name": row.name, "full_name": row.full_name or row.name, "image": row.user_image}
		for row in rows
	}


def percent(part, whole):
	return round(part * 100 / whole) if whole else None


def buckets(days):
	today = getdate(nowdate())
	start = today - timedelta(days=days - 1)

	if days <= 31:
		return "day", [start + timedelta(days=offset) for offset in range(days)]

	first = start - timedelta(days=start.weekday())
	out = []
	while first <= today:
		out.append(first)
		first += timedelta(days=7)
	return "week", out


def bucket_of(value, grain):
	day = getdate(value)
	return day if grain == "day" else day - timedelta(days=day.weekday())


def reading(effective, names, users, start):
	current = {row.name: row.version for row in effective}
	signed = defaultdict(set)
	recent = []

	if names:
		for row in frappe.get_all(
			"SOP Acknowledgement",
			filters={"sop": ("in", names)},
			fields=["sop", "version", "user", "acknowledged_at"],
			limit_page_length=0,
		):
			if row.sop in current and row.version == current[row.sop] and row.user in users:
				signed[row.sop].add(row.user)
			if row.acknowledged_at and get_datetime(row.acknowledged_at) >= start:
				recent.append(row.acknowledged_at)

	return signed, recent


def training(names):
	if not names:
		return []

	return frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": ("in", names), "status": ("!=", "Waived")},
		fields=["sop", "trainee", "status", "due_on", "completed_on"],
		limit_page_length=0,
	)


def clarity(names, start):
	if not names:
		return []

	return frappe.get_all(
		"SOP Clarity Vote",
		filters={"sop": ("in", names), "creation": (">=", start)},
		fields=["sop", "clear", "note", "creation"],
		order_by="creation desc",
		limit_page_length=0,
	)


def waiting(in_review):
	names = [row.name for row in in_review]
	if not names:
		return []

	pending = defaultdict(list)
	for row in frappe.get_all(
		"SOP Approval",
		filters={"parenttype": "SOP", "parent": ("in", names), "decision": "Pending"},
		fields=["parent", "approver", "creation"],
		limit_page_length=0,
	):
		pending[row.parent].append(row)

	approvers = people([row.approver for rows in pending.values() for row in rows])
	today = getdate(nowdate())
	out = []

	for doc in in_review:
		rows = pending.get(doc.name)
		if not rows:
			continue

		since = min(getdate(row.creation) for row in rows)
		out.append(
			{
				"name": doc.name,
				"sop_no": doc.sop_no,
				"title": doc.title,
				"days": date_diff(today, since),
				"waiting_on": [
					approvers.get(row.approver, {"full_name": row.approver})["full_name"] for row in rows
				],
			}
		)

	return sorted(out, key=lambda row: -row["days"])[:TOP]


@frappe.whitelist()
def overview(space=None, days=90):
	scope = scope_of_viewer()
	days = cint(days) if cint(days) in PERIODS else 90

	today = getdate(nowdate())
	start = get_datetime(today - timedelta(days=days - 1))
	grain, periods = buckets(days)

	rows = procedures(scope, space)
	names = [row.name for row in rows]
	effective = [row for row in rows if row.status in IN_FORCE]
	users = audience()
	reach = len(users)

	signed, recent_signatures = reading(effective, names, users, start)
	assignments = training(names)
	votes = clarity(names, start)

	stage = {status: 0 for status in LIFECYCLE}
	for row in rows:
		if row.status in stage:
			stage[row.status] += 1

	signatures = sum(len(signed[row.name]) for row in effective)
	needed = len(effective) * reach

	done = [row for row in assignments if row.status == "Completed"]
	overdue = [row for row in assignments if row.status == "Overdue"]

	due = []
	for row in effective:
		if not row.review_due:
			continue
		left = date_diff(row.review_due, today)
		if left <= SOON:
			due.append(
				{
					"name": row.name,
					"sop_no": row.sop_no,
					"title": row.title,
					"review_due": row.review_due,
					"days": left,
				}
			)
	due.sort(key=lambda row: row["days"])

	coverage = sorted(
		(
			{
				"name": row.name,
				"sop_no": row.sop_no,
				"title": row.title,
				"version": row.version,
				"signed": len(signed[row.name]),
				"audience": reach,
				"percent": percent(len(signed[row.name]), reach),
			}
			for row in effective
		),
		key=lambda row: (row["percent"] if row["percent"] is not None else 101, row["sop_no"] or ""),
	)

	by_sop = {row.name: row for row in rows}
	unclear = defaultdict(lambda: {"votes": 0, "unclear": 0, "note": None})
	for vote in votes:
		entry = unclear[vote.sop]
		entry["votes"] += 1
		if not vote.get("clear"):
			entry["unclear"] += 1
			if not entry["note"] and vote.note:
				entry["note"] = vote.note

	hardest = sorted(
		(
			{
				"name": sop,
				"sop_no": by_sop[sop].sop_no,
				"title": by_sop[sop].title,
				"votes": entry["votes"],
				"unclear": entry["unclear"],
				"percent": percent(entry["unclear"], entry["votes"]),
				"note": entry["note"],
			}
			for sop, entry in unclear.items()
			if entry["unclear"] and sop in by_sop
		),
		key=lambda row: (-row["unclear"], -(row["percent"] or 0)),
	)[:TOP]

	late = defaultdict(lambda: {"overdue": 0, "open": 0})
	for row in assignments:
		if row.status == "Overdue":
			late[row.trainee]["overdue"] += 1
		if row.status in ("Assigned", "In Progress", "Overdue"):
			late[row.trainee]["open"] += 1

	trainees = people([user for user, entry in late.items() if entry["overdue"]])
	behind = sorted(
		(
			{**trainees.get(user, {"name": user, "full_name": user, "image": None}), **entry}
			for user, entry in late.items()
			if entry["overdue"]
		),
		key=lambda row: (-row["overdue"], row["full_name"]),
	)[:TOP]

	signed_series = defaultdict(int)
	for moment in recent_signatures:
		signed_series[bucket_of(moment, grain)] += 1

	trained_series = defaultdict(int)
	for row in done:
		if row.completed_on and get_datetime(row.completed_on) >= start:
			trained_series[bucket_of(row.completed_on, grain)] += 1

	titles = dict(frappe.get_all("SOP Space", fields=["name", "title"], as_list=True))
	spaces = defaultdict(lambda: {"in_force": 0, "signed": 0, "reviews_overdue": 0, "trained": 0, "assigned": 0})
	for row in rows:
		spaces[row.space]
	for row in effective:
		entry = spaces[row.space]
		entry["in_force"] += 1
		entry["signed"] += len(signed[row.name])
		if row.review_due and date_diff(row.review_due, today) < 0:
			entry["reviews_overdue"] += 1
	for row in assignments:
		space_of = by_sop[row.sop].space if row.sop in by_sop else None
		spaces[space_of]["assigned"] += 1
		if row.status == "Completed":
			spaces[space_of]["trained"] += 1

	return {
		"scope": scope,
		"days": days,
		"audience": reach,
		"kpis": {
			"in_force": len(effective),
			"drafts": stage["Draft"],
			"in_review": stage["In Review"],
			"signed_percent": percent(signatures, needed),
			"signatures": signatures,
			"signatures_needed": needed,
			"training_percent": percent(len(done), len(assignments)),
			"training_done": len(done),
			"training_total": len(assignments),
			"training_overdue": len(overdue),
			"reviews_overdue": len([row for row in due if row["days"] < 0]),
			"reviews_soon": len([row for row in due if row["days"] >= 0]),
			"clear_percent": percent(len([vote for vote in votes if vote.get("clear")]), len(votes)),
			"votes": len(votes),
		},
		"stages": [{"status": status, "count": stage[status]} for status in LIFECYCLE],
		"trend": {
			"grain": grain,
			"periods": [str(period) for period in periods],
			"signed": [signed_series.get(period, 0) for period in periods],
			"trained": [trained_series.get(period, 0) for period in periods],
		},
		"reviews": due[:TOP],
		"coverage": coverage[:TOP],
		"waiting": waiting([row for row in rows if row.status == "In Review"]),
		"unclear": hardest,
		"behind": behind,
		"spaces": sorted(
			(
				{
					"space": key,
					"title": titles.get(key) or key or _("No space"),
					"in_force": entry["in_force"],
					"signed_percent": percent(entry["signed"], entry["in_force"] * reach),
					"training_percent": percent(entry["trained"], entry["assigned"]),
					"reviews_overdue": entry["reviews_overdue"],
				}
				for key, entry in spaces.items()
			),
			key=lambda row: row["title"].lower(),
		),
	}
