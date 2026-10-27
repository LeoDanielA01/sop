# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import json
import re

import frappe
from frappe.utils import add_days, nowdate

from sop import training
from sop.api import chat as chat_api
from sop.api import clarity as clarity_api
from sop.api import lifecycle
from sop.api import logs as logs_api
from sop.api import procedures as procedures_api
from sop.api import processes as processes_api
from sop.api import quiz as quiz_api
from sop.api import requirements as requirements_api
from sop.api import review as review_api
from sop.api import risks as risks_api
from sop.api import sessions as sessions_api
from sop.api import teams as teams_api
from sop.api import training as training_api
from sop.demo_content import (
	CHAT,
	CLARITY,
	DEMO_CODES,
	LOGS,
	PEOPLE,
	PROCEDURES,
	PROCESSES,
	QUIZ,
	RESOURCE_TYPES,
	RESOURCES,
	REVIEW_COMMENTS,
	REVISION,
	RISKS,
	RULES,
	SESSIONS,
	SPACES,
	TEAMS,
	TRAINING,
)

SHAPES = {
	"Completed": {"method": "Read & Understand", "due": -6, "outcome": "Competent", "done": 1},
	"In Progress": {"method": "On the Job", "due": 6, "outcome": "Pending", "done": 1},
	"Assigned": {"method": "Read & Understand", "due": 12, "outcome": "Pending", "done": 0},
	"Overdue": {"method": "Read & Understand", "due": -9, "outcome": "Pending", "done": 0},
}
PROFICIENCY = [("trainer", 5), ("storekeeper", 3), ("manager", 1)]


def after_migrate():
	if not wanted():
		print("SOP demo data: off. Run `bench --site <site> set-config sop_demo_data 1` to seed it.")
		return

	if seeded():
		return

	result = install(force=1)
	print(f"SOP demo data: created {len(result.get('procedures', []))} procedures in {', '.join(DEMO_CODES)}.")


def seeded():
	return bool(frappe.db.exists("SOP Space", {"space_code": ("in", list(DEMO_CODES))}))


def demo_spaces():
	return frappe.get_all(
		"SOP Space",
		filters={"space_code": ("in", list(DEMO_CODES))},
		pluck="name",
		limit_page_length=0,
	)


def summary():
	spaces = frappe.get_all(
		"SOP Space",
		filters={"space_code": ("in", list(DEMO_CODES))},
		fields=["name", "title", "space_code"],
		limit_page_length=0,
	)
	names = [row.name for row in spaces]
	procedures = (
		frappe.get_all("SOP", filters={"space": ("in", names)}, pluck="name", limit_page_length=0)
		if names
		else []
	)

	counts = {}
	for state in frappe.get_all("SOP", filters={"name": ("in", procedures or [""])}, pluck="status", limit_page_length=0):
		counts[state] = counts.get(state, 0) + 1

	return {
		"installed": bool(names),
		"spaces": spaces,
		"procedures": len(procedures),
		"by_status": counts,
		"processes": frappe.db.count("SOP Process", {"space": ("in", names)}) if names else 0,
		"assignments": frappe.db.count("SOP Training Assignment", {"sop": ("in", procedures)}) if procedures else 0,
		"people": [person["email"] for person in PEOPLE.values()],
		"other_spaces": frappe.db.count("SOP Space") - len(names),
	}


def wanted():
	flag = frappe.conf.get("sop_demo_data")
	return bool(flag) if flag is not None else bool(frappe.conf.get("developer_mode"))


def install(force=0):
	if frappe.db.count("SOP") and not force:
		return {"skipped": "procedures already exist"}

	people = ensure_people()
	seed_record_types()
	ensure_resources()
	ensure_teams(people)
	spaces = ensure_spaces(people)
	ensure_processes(people, spaces)

	created = {}
	for definition in PROCEDURES:
		created[definition["slug"]] = build(definition, spaces, people)
	link_mentions(created, people)
	for definition in PROCEDURES:
		advance(created[definition["slug"]], definition, people)

	revise(created, people)
	seed_rules(created, spaces, people)
	seed_training(created, people)
	seed_quiz(created, people)
	seed_sessions(created, people)
	seed_proficiency(created, people)
	seed_risks(created, spaces, people)
	seed_logs(created, people)
	seed_review_comments(created, people)
	seed_clarity(created, people)
	seed_chat(created, people)
	frappe.db.commit()

	return {"spaces": list(spaces.values()), "procedures": list(created.values()), "people": list(people.values())}


def ensure_people():
	people = {}
	for key, person in PEOPLE.items():
		email = person["email"]
		new = not frappe.db.exists("User", email)
		user = (
			frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": person["first"],
					"last_name": person["last"],
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			if new
			else frappe.get_doc("User", email)
		)
		for role in person["roles"]:
			if frappe.db.exists("Role", role) and role not in [row.role for row in user.roles]:
				user.append("roles", {"role": role})
		user.insert(ignore_permissions=True) if new else user.save(ignore_permissions=True)
		people[key] = email
	return people


def seed_record_types():
	from sop.patches.seed_safety_record_types import execute

	execute()


def ensure_resources():
	from sop.patches.migrate_to_resources import ensure_type

	for definition in RESOURCE_TYPES:
		ensure_type(definition)

	for row in RESOURCES:
		if frappe.db.exists("SOP Resource", row["resource_name"]):
			continue
		doc = {"doctype": "SOP Resource", **{k: v for k, v in row.items() if k != "check_in"}}
		if "check_in" in row:
			doc["check_date"] = add_days(nowdate(), row["check_in"])
		frappe.get_doc(doc).insert(ignore_permissions=True)


def ensure_teams(people):
	for team in TEAMS:
		members = [{"user": people[key], "team_role": role} for key, role in team["members"]]
		existing = frappe.db.exists("SOP Team", team["name"])
		as_user(
			people["manager"],
			teams_api.save_team,
			team_name=team["name"],
			members=members,
			description=team["description"],
			name=team["name"] if existing else None,
		)


def ensure_spaces(people):
	spaces = {}
	for space in SPACES:
		existing = frappe.db.get_value("SOP Space", {"space_code": space["code"]}, "name")
		if not existing:
			existing = as_user(
				people["manager"],
				procedures_api.create_space,
				title=space["title"],
				space_code=space["code"],
				description=space["description"],
				team=space["team"],
				visibility=space.get("visibility", "Public"),
			)["name"]
		spaces[space["code"]] = existing
	return spaces


def ensure_processes(people, spaces):
	for code, tree in PROCESSES.items():
		for index, (group, children) in enumerate(tree, start=1):
			parent = ensure_process(people["manager"], spaces[code], group, None, index * 10)
			for position, child in enumerate(children, start=1):
				ensure_process(people["manager"], spaces[code], child, parent, position * 10)


def ensure_process(manager, space, title, parent, sequence):
	existing = frappe.db.get_value("SOP Process", {"space": space, "title": title, "parent_process": parent}, "name")
	if existing:
		return existing
	return as_user(
		manager, processes_api.create_process, title=title, space=space, parent=parent, sequence=sequence
	)["name"]


def build(definition, spaces, people):
	space = spaces[definition["space"]]
	process = frappe.db.get_value("SOP Process", {"space": space, "title": definition["process"]}, "name")
	draft = as_user(
		people[definition.get("author", "author")],
		procedures_api.save_draft,
		space=space,
		title=definition["title"],
		summary=definition["summary"],
		content=definition["content"],
		process=process,
		risk_level=definition.get("risk_level", "Medium"),
		is_controlled=1,
	)
	if definition.get("document_type"):
		frappe.db.set_value("SOP", draft["name"], "document_type", definition["document_type"], update_modified=False)
	for tag in definition.get("tags", []):
		add_tag(tag, "SOP", draft["name"])
	return draft["name"]


def link_mentions(created, people):
	for definition in PROCEDURES:
		name = created[definition["slug"]]
		doc = frappe.get_doc("SOP", name)
		content = linked(doc.content or "", created, people)
		if content != doc.content:
			doc.content = content
			doc.save(ignore_permissions=True)


def linked(content, created, people):
	def sop(match):
		target = created.get(match.group(1))
		if not target:
			return match.group(0)
		title = frappe.db.get_value("SOP", target, "title")
		return f'<a href="#mention:SOP:{target}">{title}</a>'

	def user(match):
		email = people.get(match.group(1))
		if not email:
			return match.group(0)
		full_name = frappe.db.get_value("User", email, "full_name") or email
		return f'<a href="#mention:User:{email}">{full_name}</a>'

	def resource(match):
		return f'<a href="#mention:SOP Resource:{match.group(1)}">{match.group(1)}</a>'

	content = re.sub(r"\{sop:([a-z0-9-]+)\}", sop, content)
	content = re.sub(r"\{user:([a-z]+)\}", user, content)
	return re.sub(r"\{res:([^}]+)\}", resource, content)


def advance(sop, definition, people):
	state = definition["state"]
	if state == "draft":
		return

	as_user(people[definition.get("author", "author")], lifecycle.send_for_approval, sop)
	if state == "in_review":
		return

	for approver in frappe.get_all(
		"SOP Approval",
		filters={"parent": sop, "parenttype": "SOP"},
		pluck="approver",
		order_by="idx asc",
		limit_page_length=0,
	):
		as_user(approver, lifecycle.decide, sop, "Approved", "Reads correctly.")
	if state == "approved":
		return

	as_user(
		people["manager"],
		lifecycle.publish,
		sop,
		effective_from=add_days(nowdate(), definition.get("effective_since", -40)),
		change_summary="First controlled issue.",
		is_material=1,
	)
	if state == "retired":
		as_user(people["manager"], lifecycle.retire, sop, definition.get("retire_reason") or "No longer used.")
		return

	sign(sop, [people[key] for key in definition.get("signed_by", [])])


def revise(created, people):
	sop = created[REVISION["slug"]]
	as_user(people["author"], lifecycle.start_revision, sop)
	doc = frappe.get_doc("SOP", sop)
	content = doc.content
	for old, new in REVISION["changes"]:
		content = content.replace(old, new)
	as_user(
		people["author"],
		procedures_api.save_draft,
		space=doc.space,
		title=doc.title,
		name=sop,
		summary=doc.summary,
		content=content,
		process=doc.sop_process,
	)
	as_user(people["author"], lifecycle.send_for_approval, sop)
	for approver in frappe.get_all("SOP Approval", filters={"parent": sop, "parenttype": "SOP"}, pluck="approver"):
		as_user(approver, lifecycle.decide, sop, "Approved", REVISION["approval_note"])
	as_user(
		people["manager"],
		lifecycle.publish,
		sop,
		effective_from=add_days(nowdate(), -3),
		change_summary=REVISION["change_summary"],
		is_material=1,
	)


def as_user(user, fn, *args, **kwargs):
	original = frappe.session.user
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user(original)


def add_tag(tag, doctype, name):
	from frappe.desk.doctype.tag.tag import add_tag as tag_it

	tag_it(tag, doctype, name)


def sign(sop, users):
	version = frappe.db.get_value("SOP", sop, "version")
	for user in users:
		as_user(user, procedures_api.acknowledge, sop, version)


def seed_rules(created, spaces, people):
	for rule in RULES:
		values = {k: v for k, v in rule.items() if k not in ("space_code", "slug", "team_key", "user_key")}
		if rule.get("space_code"):
			values["space"] = spaces[rule["space_code"]]
		if rule.get("slug"):
			values["sop"] = created[rule["slug"]]
		if rule.get("user_key"):
			values["user"] = people[rule["user_key"]]
		name = as_user(people["trainer"], requirements_api.save_requirement, enabled=1, **values)["name"]
		as_user(people["trainer"], requirements_api.run_requirement, name)


def seed_training(created, people):
	for slug, trainee, state in TRAINING:
		assign(people, created[slug], people[trainee], state)


def assign(people, sop, trainee, state):
	shape = SHAPES[state]
	open_one = frappe.db.get_value(
		"SOP Training Assignment", {"sop": sop, "trainee": trainee, "status": ("in", training.OPEN_STATES)}, "name"
	)
	if open_one:
		name = open_one
		frappe.db.set_value(
			"SOP Training Assignment", name, "due_on", add_days(nowdate(), shape["due"]), update_modified=False
		)
	else:
		created = as_user(
			people["trainer"], training_api.assign, sop=sop, trainees=[trainee], method=shape["method"], due_days=shape["due"]
		)
		if not created:
			return None
		name = created[0]

	for idx in range(1, shape["done"] + 1):
		as_user(trainee, training_api.complete_task, name, idx)
	if shape["outcome"] != "Pending":
		assessor = people["manager"] if trainee == people["trainer"] else people["trainer"]
		as_user(assessor, training_api.record_outcome, name, shape["outcome"])
	if state == "Overdue":
		frappe.db.set_value("SOP Training Assignment", name, "status", "Overdue", update_modified=False)
	return name


def seed_quiz(created, people):
	for slug, questions in QUIZ["questions"].items():
		for row in questions:
			as_user(
				people["trainer"],
				quiz_api.save_question,
				created[slug],
				row["question"],
				[{"option": option, "correct": int(index in row["correct"])} for index, option in enumerate(row["options"])],
				kind="Several answers" if len(row["correct"]) > 1 else "One answer",
				explanation=row.get("explanation"),
			)

	for slug, trainee, outcomes in QUIZ["attempts"]:
		assignment = frappe.db.get_value(
			"SOP Training Assignment",
			{"sop": created[slug], "trainee": people[trainee], "status": ("in", training.OPEN_STATES)},
			"name",
		)
		if not assignment:
			continue
		for passed in outcomes:
			take_quiz(people[trainee], assignment, passed)


def take_quiz(trainee, assignment, passed):
	doc = frappe.get_doc("SOP Training Assignment", assignment)
	for row in doc.tasks:
		if row.task_type != "Assessment" and not row.completed:
			as_user(trainee, training_api.complete_task, assignment, row.idx)
	started = as_user(trainee, quiz_api.start, assignment)
	attempt = frappe.get_doc("SOP Quiz Attempt", started["attempt"])
	paper = json.loads(attempt.paper or "[]")
	questions = {row["name"]: row for row in quiz_api.bank(attempt.sop)}
	answers = {}
	for position, sheet in enumerate(paper):
		options = questions[sheet["question"]]["options"]
		right = [shown for shown, index in enumerate(sheet["order"]) if options[index]["correct"]]
		wrong = [shown for shown, index in enumerate(sheet["order"]) if not options[index]["correct"]]
		answers[str(position)] = right if passed or position % 2 else wrong[:1]
	as_user(trainee, quiz_api.submit, attempt.name, answers)


def seed_sessions(created, people):
	for session in SESSIONS:
		procedures = [created[slug] for slug in session["procedures"]]
		attendees = [people[key] for key in session["attendees"]]
		for trainee in attendees:
			for sop in procedures:
				if not frappe.db.exists("SOP Training Assignment", {"sop": sop, "trainee": trainee}):
					as_user(
						people["trainer"], training_api.assign, sop=sop, trainees=[trainee], method=session["method"], due_days=10
					)
		name = as_user(
			people["trainer"],
			sessions_api.save_session,
			title=session["title"],
			trainer=people["trainer"],
			scheduled_on=f"{add_days(nowdate(), session['in_days'])} {session['time']}",
			location=session["location"],
			method=session["method"],
			procedures=procedures,
			attendees=attendees,
			notes=session["notes"],
		)["name"]
		if session.get("outcomes"):
			rows = [
				{
					"user": people[key],
					"attended": outcome != "Absent",
					"outcome": "Pending" if outcome == "Absent" else outcome,
					"score": 90 if outcome == "Competent" else (60 if outcome != "Absent" else None),
					"remarks": remark,
				}
				for key, outcome, remark in session["outcomes"]
			]
			as_user(people["trainer"], sessions_api.record_attendance, name, rows)


def seed_proficiency(created, people):
	doc = frappe.get_doc("SOP", created[QUIZ["proficiency_slug"]])
	for key, times in PROFICIENCY:
		trainee = people[key]
		previous = None
		for _attempt in range(times):
			name = training.create_assignment(doc, None, trainee, cause="Demo refresher", is_refresher=1, supersedes=previous)
			if not name:
				break
			assignment = frappe.get_doc("SOP Training Assignment", name)
			for row in assignment.tasks:
				if row.task_type != "Assessment":
					as_user(trainee, training_api.complete_task, name, row.idx)
			assessor = people["manager"] if trainee == people["trainer"] else people["trainer"]
			as_user(assessor, training_api.record_outcome, name, "Competent")
			previous = name


def seed_risks(created, spaces, people):
	for risk in RISKS:
		hazards = []
		for row in risk["hazards"]:
			hazard = {k: v for k, v in row.items() if k not in ("owner", "due_in", "checked_in")}
			if row.get("owner"):
				hazard["action_owner"] = people[row["owner"]]
			if row.get("due_in") is not None:
				hazard["action_due"] = add_days(nowdate(), row["due_in"])
			if row.get("checked_in") is not None:
				hazard["next_check"] = add_days(nowdate(), row["checked_in"])
			hazards.append(hazard)
		doc = frappe.get_doc(
			{
				"doctype": "SOP Risk Assessment",
				"ra_no": risk["ra_no"],
				"title": risk["title"],
				"space": spaces[risk["space"]],
				"status": risk["status"],
				"version_label": risk.get("version", "1.0"),
				"assessed_by": people[risk["assessed_by"]],
				"assessed_on": add_days(nowdate(), risk.get("assessed_in", -30)),
				"review_due": add_days(nowdate(), risk.get("review_in", 335)),
				"scoring_note": risk.get("scoring_note"),
				"notes": risk.get("notes"),
				"applies_to": [{"sop": created[slug]} for slug in risk["applies_to"]],
				"hazards": hazards,
			}
		)
		doc.insert(ignore_permissions=True)
		for hazard_id in risk.get("complete_checks", []):
			row = next(item for item in doc.hazards if item.hazard_id == hazard_id)
			as_user(
				people["operator"],
				risks_api.complete_check,
				doc.name,
				row.name,
				notes="Checked during the demo walk-round. All fine.",
				sop=created[risk["applies_to"][0]],
			)


def seed_logs(created, people):
	for entry in LOGS:
		values = {k: v for k, v in entry.items() if k not in ("slug", "by", "checker", "days_ago")}
		if entry.get("checker"):
			values["checked_by"] = people[entry["checker"]]
		name = as_user(people[entry["by"]], logs_api.create, created[entry["slug"]], values)["name"]
		frappe.db.set_value(
			"SOP Log Entry",
			name,
			"logged_at",
			f"{add_days(nowdate(), -entry['days_ago'])} {entry.get('time', '08:00:00')}",
			update_modified=False,
		)


def seed_review_comments(created, people):
	for slug, key, comment, quote, resolved in REVIEW_COMMENTS:
		result = as_user(people[key], review_api.add_comment, created[slug], comment, quote=quote)
		name = result.get("name") if isinstance(result, dict) else result
		if resolved and name:
			as_user(people["author"], review_api.resolve_comment, name)


def seed_clarity(created, people):
	for slug, key, clear, note in CLARITY:
		as_user(people[key], clarity_api.vote, created[slug], clear, note)


def seed_chat(created, people):
	for slug, key, text in CHAT["room"]:
		as_user(people[key], chat_api.send, content=text, sop=created[slug], room=1)
	for sender, recipient, slug, text in CHAT["direct"]:
		as_user(people[sender], chat_api.send, content=text, to=people[recipient], sop=created.get(slug))


def status():
	return {
		"user": frappe.session.user,
		"developer_mode": bool(frappe.conf.get("developer_mode")),
		"demo_enabled": wanted(),
		"spaces": frappe.get_all("SOP Space", fields=["name", "title", "space_code", "visibility"], limit_page_length=0),
		"processes": frappe.db.count("SOP Process"),
		"procedures": frappe.db.count("SOP"),
		"by_status": by_status(),
		"acknowledgements": frappe.db.count("SOP Acknowledgement"),
		"assignments": frappe.db.count("SOP Training Assignment"),
		"can_read_spaces": frappe.has_permission("SOP Space", "read"),
		"spaces_api": len(frappe.call("sop.api.procedures.spaces")),
		"last_error": last_error(),
	}


def by_status():
	counts = {}
	for state in frappe.get_all("SOP", pluck="status", limit_page_length=0):
		counts[state] = counts.get(state, 0) + 1
	return counts


def last_error():
	rows = frappe.get_all(
		"Error Log",
		filters={"method": ("like", "%SOP demo%")},
		fields=["creation", "error"],
		order_by="creation desc",
		limit_page_length=1,
	)
	if not rows:
		return None
	return {"at": str(rows[0].creation), "tail": (rows[0].error or "").strip().splitlines()[-6:]}


def clear():
	frappe.flags.sop_removal = True
	try:
		return wipe_demo()
	finally:
		frappe.flags.sop_removal = False


def drop(doctype, filters):
	for name in frappe.get_all(doctype, filters=filters, pluck="name", limit_page_length=0):
		frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)


def wipe_demo():
	spaces = demo_spaces()
	if not spaces:
		return {"cleared": 0, "spaces": []}

	procedures = frappe.get_all("SOP", filters={"space": ("in", spaces)}, pluck="name", limit_page_length=0)
	scope = procedures or [""]
	assessments = frappe.get_all("SOP Risk Assessment", filters={"space": ("in", spaces)}, pluck="name", limit_page_length=0)
	assignments = frappe.get_all("SOP Training Assignment", filters={"sop": ("in", scope)}, pluck="name", limit_page_length=0)

	drop("SOP Log Entry", {"sop": ("in", scope)})
	drop("SOP Log Entry", {"risk_assessment": ("in", assessments or [""])})
	for name in assessments:
		frappe.delete_doc("SOP Risk Assessment", name, force=True, ignore_permissions=True)
	drop("SOP Quiz Attempt", {"sop": ("in", scope)})
	drop("SOP Quiz Question", {"sop": ("in", scope)})
	for doctype in ("SOP Clarity Vote", "SOP Message", "SOP Chat Seen"):
		frappe.db.delete(doctype, {"sop": ("in", scope)})
	for doctype in ("SOP Training Assignment", "SOP Acknowledgement", "SOP Revision", "SOP Review Comment"):
		drop(doctype, {"sop": ("in", scope)})
	for name in sessions_covering(procedures):
		frappe.delete_doc("SOP Training Session", name, force=True, ignore_permissions=True)
	drop("SOP Training Requirement", {"space": ("in", spaces)})
	drop("SOP Training Requirement", {"sop": ("in", scope)})
	for name in procedures:
		frappe.delete_doc("SOP", name, force=True, ignore_permissions=True)
	for name in deepest_first(spaces):
		frappe.delete_doc("SOP Process", name, force=True, ignore_permissions=True)
	frappe.db.delete(
		"Notification Log",
		{"document_type": ("in", ["SOP", "SOP Training Assignment", "SOP Risk Assessment"]), "document_name": ("in", (procedures + assignments + assessments) or [""])},
	)
	for name in spaces:
		frappe.delete_doc("SOP Space", name, force=True, ignore_permissions=True)

	people = [person["email"] for person in PEOPLE.values()]
	frappe.db.delete("SOP Message", {"sender": ("in", people), "recipient": ("in", people)})
	for team in TEAMS:
		if frappe.db.exists("SOP Team", team["name"]) and not frappe.db.exists("SOP Space", {"team": team["name"]}):
			frappe.delete_doc("SOP Team", team["name"], force=True, ignore_permissions=True)

	for row in reversed(RESOURCES):
		if frappe.db.exists("SOP Resource", row["resource_name"]):
			frappe.delete_doc("SOP Resource", row["resource_name"], force=True, ignore_permissions=True)
	for definition in RESOURCE_TYPES:
		name = definition["type_name"]
		if frappe.db.exists("SOP Resource Type", name) and not frappe.db.exists("SOP Resource", {"resource_type": name}):
			frappe.delete_doc("SOP Resource Type", name, force=True, ignore_permissions=True)

	frappe.db.commit()
	return {"cleared": len(procedures), "spaces": spaces}


def reset():
	cleared = clear()
	seeded = install(force=1)
	return {"cleared": cleared, "seeded": seeded, "status": status()}


def sessions_covering(procedures):
	if not procedures:
		return []
	return list(
		set(
			frappe.get_all(
				"SOP Session Procedure",
				filters={"sop": ("in", procedures), "parenttype": "SOP Training Session"},
				pluck="parent",
				limit_page_length=0,
			)
		)
	)


def deepest_first(spaces):
	rows = frappe.get_all(
		"SOP Process", filters={"space": ("in", spaces)}, fields=["name", "parent_process"], limit_page_length=0
	)
	depth = {row.name: 0 for row in rows}
	parents = {row.name: row.parent_process for row in rows}
	for name in depth:
		current = parents.get(name)
		while current in parents:
			depth[name] += 1
			current = parents.get(current)
	return sorted(depth, key=lambda name: -depth[name])
