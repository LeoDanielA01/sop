# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, now_datetime, nowdate

from sop import templates

PEOPLE = [
	("priya.nair@example.com", "Priya", "Nair", ["SOP Manager", "SOP Approver"]),
	("arun.kumar@example.com", "Arun", "Kumar", ["SOP Author"]),
	("mei.tan@example.com", "Mei", "Tan", ["SOP Approver", "SOP Trainer"]),
	("sam.oduya@example.com", "Sam", "Oduya", ["SOP Reader"]),
]

TEAM = "Plant Floor"

QUALITY_PROCESSES = [
	("Documentation", ["Writing a procedure", "Change control", "Record retention"]),
	("Audits", ["Internal audit", "Supplier audit", "Regulatory inspection"]),
]

PROCEDURES = [
	{
		"title": "Line clearance before a batch",
		"space": "MFG",
		"process": "Line clearance and setup",
		"summary": "What two people must confirm before any material reaches a clean line.",
		"state": "effective",
		"tags": ["gmp", "batch-start"],
		"steps": [
			("Stop the line and hang the CLEARANCE IN PROGRESS board.", "Operator", None),
			("Remove every component, label and printed record from the previous batch.", "Operator", None),
			("Wipe contact surfaces and check the line is visibly clean and dry.", "Operator", None),
			("A second person checks independently and signs the clearance record.", "Line supervisor", None),
			("Release the line and record the clearance time on the batch record.", "Line supervisor", None),
		],
		"content": """<h2>Purpose</h2>
<p>No batch starts on a line that still holds anything from the batch before it. Line clearance is the check that proves it, and it is signed by two people.</p>
<h2>Scope</h2>
<p>Every production and packing line, at every changeover and at the start of every shift where the product changes.</p>
<h2>Responsibilities</h2>
<ul>
<li>Operator — carries out the clearance.</li>
<li>Line supervisor — checks it independently and signs.</li>
<li>Quality — audits clearance records weekly.</li>
</ul>
<h2>Procedure</h2>
<div data-sop="step"><p><strong>Stop and mark the line</strong> — hang the board so nobody feeds material while the check runs.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Line clearance record</p></div>
<div data-sop="step"><p><strong>Strip the line</strong> — components, labels, printed records and part-used containers all leave the area.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Line clearance record</p></div>
<div data-sop="callout" data-tone="warning"><p>A single label from the previous batch is a mix-up. Check under the conveyor and inside the reject bin.</p></div>
<div data-sop="step"><p><strong>Independent check</strong> — a second person repeats the walk and signs. The same person cannot do both.</p>
<p data-sop="step-meta">Responsible: Line supervisor · Records: Line clearance record</p></div>
<h2>Records</h2>
<p>Line clearance record, filed with the batch record. Kept for the shelf life of the product plus one year.</p>""",
	},
	{
		"title": "Weighing and dispensing raw material",
		"space": "MFG",
		"process": "Weighing and dispensing",
		"summary": "How material is weighed, labelled and reconciled so a batch can be traced back.",
		"state": "effective",
		"effective_since": -380,
		"tags": ["gmp"],
		"steps": [
			("Check the balance calibration sticker is in date.", "Operator", None),
			("Confirm the material, lot and quantity against the batch record.", "Operator", None),
			("Weigh into a clean container and label it with material, lot, weight and batch.", "Operator", None),
			("A second person verifies the weight and signs.", "Line supervisor", None),
			("Reconcile what was issued against what was returned.", "Operator", None),
		],
		"content": """<h2>Purpose</h2>
<p>Every gram that enters a batch is traceable to a material, a lot and the person who weighed it.</p>
<h2>Scope</h2>
<p>All raw material and in-process material dispensed in the weighing booth.</p>
<h2>Procedure</h2>
<div data-sop="step"><p><strong>Check the balance</strong> — calibration in date, pan clean, zero stable.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Balance log</p></div>
<div data-sop="step"><p><strong>Identify the material</strong> — material code, lot number and released status against the batch record.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Batch record</p></div>
<div data-sop="callout" data-tone="warning"><p>Never weigh from a container without a release label. Quarantine material stays in quarantine.</p></div>
<div data-sop="step"><p><strong>Weigh, label, verify</strong> — a second person confirms the weight before the container leaves the booth.</p>
<p data-sop="step-meta">Responsible: Line supervisor · Records: Dispensing record</p></div>
<h2>Records</h2>
<p>Dispensing record and balance log.</p>""",
	},
	{
		"title": "Changeover on the filling line",
		"space": "MFG",
		"process": "Changeover",
		"summary": "Stripping, cleaning and re-setting the filler between products.",
		"state": "in_review",
		"tags": ["maintenance"],
		"steps": [
			("Isolate the machine and apply lockout.", "Line supervisor", None),
			("Strip change parts and send them for cleaning.", "Operator", None),
			("Fit the change parts for the next product and set the fill weight.", "Operator", None),
			("Run five containers and check the fill weight before release.", "Line supervisor", None),
		],
		"content": """<h2>Purpose</h2>
<p>A changeover is finished when the line is clean, the right parts are fitted, and the first containers are within the fill tolerance.</p>
<h2>Procedure</h2>
<div data-sop="step"><p><strong>Isolate</strong> — lockout and tagout before a guard is opened.</p>
<p data-sop="step-meta">Responsible: Line supervisor · Records: Lockout register</p></div>
<div data-sop="step"><p><strong>Strip and clean</strong> — change parts go to the wash bay with their identification tags.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Cleaning log</p></div>
<div data-sop="step"><p><strong>Set and prove</strong> — five containers checked against the fill tolerance before normal running.</p>
<p data-sop="step-meta">Responsible: Line supervisor · Records: Setup record</p></div>""",
	},
	{
		"title": "Raising a deviation",
		"space": "QA",
		"process": "Change control",
		"summary": "What to do in the first hour after something does not go to plan.",
		"state": "approved",
		"tags": ["gmp", "quality"],
		"steps": [
			("Stop and make the material safe.", "Operator", None),
			("Tell the shift supervisor and Quality within the hour.", "Operator", None),
			("Write down what happened, when, and what was affected.", "Line supervisor", None),
			("Quality decides whether the batch continues.", None, None),
		],
		"content": """<h2>Purpose</h2>
<p>A deviation is anything that did not happen the way a procedure says. Reporting it quickly is what keeps a batch defensible.</p>
<h2>Scope</h2>
<p>Every department. Quality owns the outcome; the shift owns the first hour.</p>
<h2>Procedure</h2>
<div data-sop="step"><p><strong>Make it safe</strong> — stop, segregate the affected material, label it on hold.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Hold label</p></div>
<div data-sop="step"><p><strong>Report within the hour</strong> — supervisor and Quality, verbally, then in writing.</p>
<p data-sop="step-meta">Responsible: Operator · Records: Deviation form</p></div>
<div data-sop="callout" data-tone="note"><p>Write what you saw, not what you think caused it. The investigation decides the cause.</p></div>""",
	},
	{
		"title": "Gowning for the clean area",
		"space": "MFG",
		"process": "Hygiene and gowning",
		"summary": "The order the change room is used, and what never goes past the step-over bench.",
		"state": "draft",
		"tags": ["hygiene"],
		"steps": [
			("Remove outdoor clothing and jewellery in the grey side.", None, None),
			("Wash and dry hands.", None, None),
			("Gown in order: hairnet, coverall, overshoes, gloves.", None, None),
			("Cross the step-over bench without touching the floor behind you.", None, None),
		],
		"content": """<h2>Purpose</h2>
<p>The change room only works if it is used in one direction, in one order.</p>
<h2>Procedure</h2>
<div data-sop="step"><p><strong>Grey side</strong> — outdoor clothing, watches and jewellery come off here.</p></div>
<div data-sop="step"><p><strong>Wash and dry</strong> — twenty seconds, then a single-use towel.</p></div>
<div data-sop="step"><p><strong>Gown in order</strong> — hairnet, coverall, overshoes, gloves. Gloves go on last.</p></div>
<div data-sop="callout" data-tone="warning"><p>Nothing from the grey side crosses the bench — no phones, no notebooks, no pens.</p></div>""",
	},
	{
		"title": "Retained samples (old process)",
		"space": "QA",
		"process": "Record retention",
		"summary": "Superseded by the sampling and testing procedure.",
		"state": "retired",
		"tags": ["quality"],
		"steps": [("Keep two units per batch in the sample store.", None, None)],
		"content": """<h2>Purpose</h2>
<p>Replaced. Retained samples are now covered by the sampling and testing procedure for the whole plant.</p>""",
	},
]

SHAPES = {
	"Completed": {
		"method": "Read & Understand",
		"assigned": -20,
		"due": -6,
		"outcome": "Competent",
		"tasks": [("Read the procedure", "Read Procedure", True)],
	},
	"In Progress": {
		"method": "On the Job",
		"assigned": -8,
		"due": 6,
		"outcome": "Pending",
		"tasks": [
			("Read the procedure", "Read Procedure", True),
			("Carry out the procedure under supervision", "Practical", False),
		],
	},
	"Assigned": {
		"method": "Read & Understand",
		"assigned": -2,
		"due": 12,
		"outcome": "Pending",
		"tasks": [("Read the procedure", "Read Procedure", False)],
	},
	"Overdue": {
		"method": "Read & Understand",
		"assigned": -30,
		"due": -9,
		"outcome": "Pending",
		"tasks": [("Read the procedure", "Read Procedure", False)],
	},
}



def after_migrate():
	if not wanted():
		return

	if frappe.db.count("SOP"):
		return

	install()


def wanted():
	flag = frappe.conf.get("sop_demo_data")
	return bool(flag) if flag is not None else bool(frappe.conf.get("developer_mode"))


def install(force=0):
	if frappe.db.count("SOP") and not force:
		return {"skipped": "procedures already exist"}

	people = ensure_people()
	ensure_team(people)

	spaces = {
		"MFG": ensure_space("Manufacturing", "MFG", "How the plant makes, checks and packs what it ships."),
		"QA": ensure_space("Quality", "QA", "How the plant proves what it shipped was right."),
	}

	templates.apply_template(spaces["MFG"], "manufacturing")
	seed_quality_processes(spaces["QA"])

	created = []
	for definition in PROCEDURES:
		created.append(build(definition, spaces, people))

	seed_training(spaces["MFG"], people)
	frappe.db.commit()

	return {"space": list(spaces.values()), "procedures": created, "people": [p[0] for p in PEOPLE]}


def ensure_people():
	people = []

	for email, first, last, roles in PEOPLE:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.flags.ignore_permissions = True
			user.insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", email)

		for role in roles:
			if frappe.db.exists("Role", role) and role not in [row.role for row in user.roles]:
				user.append("roles", {"role": role})

		user.save(ignore_permissions=True)
		people.append(email)

	return people


def ensure_team(people):
	if frappe.db.exists("SOP Team", TEAM):
		return TEAM

	doc = frappe.get_doc(
		{
			"doctype": "SOP Team",
			"team_name": TEAM,
			"description": "Everyone who works a line, plus the supervisors who sign for them.",
			"members": [
				{"user": people[1], "team_role": "Author"},
				{"user": people[2], "team_role": "Approver"},
				{"user": people[3], "team_role": "Reader"},
			],
		}
	)
	doc.insert(ignore_permissions=True)

	return doc.name


def ensure_space(title, code, description):
	existing = frappe.db.get_value("SOP Space", {"space_code": code}, "name")
	if existing:
		return existing

	return (
		frappe.get_doc(
			{
				"doctype": "SOP Space",
				"title": title,
				"space_code": code,
				"visibility": "Public",
				"review_interval_months": 12,
				"description": description,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def seed_quality_processes(space):
	for index, (group, steps) in enumerate(QUALITY_PROCESSES, start=1):
		parent = templates.ensure_process(space, group, None, index * 10)
		for position, step in enumerate(steps, start=1):
			templates.ensure_process(space, step, parent, position * 10)


def build(definition, spaces, people):
	space = spaces[definition["space"]]
	process = frappe.db.get_value(
		"SOP Process", {"space": space, "title": definition["process"]}, "name"
	)

	doc = frappe.get_doc(
		{
			"doctype": "SOP",
			"title": definition["title"],
			"space": space,
			"sop_process": process,
			"summary": definition["summary"],
			"content": definition["content"],
			"process_owner": people[1],
			"is_controlled": 1,
			"risk_level": "High" if definition["space"] == "MFG" else "Medium",
			"steps": [
				{"instruction": text, "responsible_role": role_of(role), "record_to_capture": record}
				for text, role, record in definition["steps"]
			],
			"tags": [{"tag": ensure_tag(tag)} for tag in definition["tags"]],
		}
	)
	doc.insert(ignore_permissions=True)

	advance(doc, definition["state"], people, definition.get("effective_since", -40))

	return doc.name


def role_of(role):
	return role if role and frappe.db.exists("Role", role) else None


def ensure_tag(tag):
	if not frappe.db.exists("Tag", tag):
		frappe.get_doc({"doctype": "Tag", "name": tag}).insert(ignore_permissions=True)

	return tag


def advance(doc, state, people, since=-40):
	from sop.api import lifecycle

	if state == "draft":
		return

	approvers = [
		{"approver": people[0], "approval_role": "Quality"},
		{"approver": frappe.session.user, "approval_role": "Approver"},
	]

	if state == "in_review":
		as_user(people[1], lifecycle.send_for_approval, doc.name, approvers)
		return

	as_user(people[1], lifecycle.send_for_approval, doc.name, approvers)
	as_user(people[0], lifecycle.decide, doc.name, "Approved", "Reads correctly.")
	as_user(frappe.session.user, lifecycle.decide, doc.name, "Approved")

	if state == "approved":
		return

	lifecycle.publish(
		doc.name,
		effective_from=add_days(nowdate(), since),
		change_summary="First controlled issue.",
		is_material=1,
	)

	if state == "retired":
		lifecycle.retire(doc.name, "Superseded by the plant-wide sampling procedure.")
		return

	sign(doc.name, people[2:])


def as_user(user, fn, *args, **kwargs):
	original = frappe.session.user
	frappe.set_user(user)

	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user(original)


def sign(sop, users):
	version = frappe.db.get_value("SOP", sop, "version")

	for user in users:
		if frappe.db.exists("SOP Acknowledgement", {"sop": sop, "version": version, "user": user}):
			continue

		frappe.get_doc(
			{
				"doctype": "SOP Acknowledgement",
				"sop": sop,
				"version": version,
				"user": user,
				"acknowledged_at": now_datetime(),
				"method": "Web",
			}
		).insert(ignore_permissions=True)


def seed_training(space, people):
	requirement = ensure_requirement(space)
	effective = frappe.get_all(
		"SOP", filters={"space": space, "status": "Effective"}, fields=["name", "version", "title"]
	)
	if not effective:
		return

	trainees = [frappe.session.user] + people[1:]

	for index, procedure in enumerate(effective):
		for position, trainee in enumerate(trainees):
			state = ("Completed", "In Progress", "Assigned", "Overdue")[(index + position) % 4]
			assign(procedure, trainee, requirement, state)


def ensure_requirement(space):
	existing = frappe.db.get_value(
		"SOP Training Requirement", {"scope": "Space", "space": space, "applies_to": "Team"}, "name"
	)
	if existing:
		return existing

	return (
		frappe.get_doc(
			{
				"doctype": "SOP Training Requirement",
				"enabled": 1,
				"applies_to": "Team",
				"team": TEAM,
				"scope": "Space",
				"space": space,
				"method": "Read & Understand",
				"due_days": 14,
				"refresher_months": 12,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def assign(procedure, trainee, requirement, state):
	if frappe.db.exists(
		"SOP Training Assignment",
		{"sop": procedure.name, "trainee": trainee, "version": procedure.version},
	):
		return

	shape = SHAPES[state]

	doc = frappe.get_doc(
		{
			"doctype": "SOP Training Assignment",
			"sop": procedure.name,
			"version": procedure.version,
			"trainee": trainee,
			"requirement": requirement,
			"method": shape["method"],
			"assigned_on": add_days(nowdate(), shape["assigned"]),
			"due_on": add_days(nowdate(), shape["due"]),
			"outcome": shape["outcome"],
			"assessed_by": frappe.session.user if shape["outcome"] != "Pending" else None,
			"tasks": [task(text, kind, done, trainee) for text, kind, done in shape["tasks"]],
		}
	)
	doc.insert(ignore_permissions=True)

	return doc.name


def task(text, kind, done, trainee):
	return {
		"task": text,
		"task_type": kind,
		"completed": 1 if done else 0,
		"completed_on": now_datetime() if done else None,
		"completed_by": trainee if done else None,
	}


def status():
	return {
		"user": frappe.session.user,
		"developer_mode": bool(frappe.conf.get("developer_mode")),
		"demo_enabled": wanted(),
		"spaces": frappe.get_all("SOP Space", fields=["name", "title", "space_code", "visibility"]),
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
	for status in frappe.get_all("SOP", pluck="status", limit_page_length=0):
		counts[status] = counts.get(status, 0) + 1

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
	spaces = frappe.get_all(
		"SOP Space", filters={"space_code": ("in", ["MFG", "QA"])}, pluck="name"
	)
	if not spaces:
		return {"cleared": 0}

	procedures = frappe.get_all("SOP", filters={"space": ("in", spaces)}, pluck="name")

	for doctype, field in (
		("SOP Training Assignment", "sop"),
		("SOP Acknowledgement", "sop"),
		("SOP Revision", "sop"),
	):
		for name in frappe.get_all(doctype, filters={field: ("in", procedures or [""])}, pluck="name"):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	for name in procedures:
		frappe.delete_doc("SOP", name, force=True, ignore_permissions=True)

	for name in frappe.get_all(
		"SOP Training Requirement", filters={"space": ("in", spaces)}, pluck="name"
	):
		frappe.delete_doc("SOP Training Requirement", name, force=True, ignore_permissions=True)

	for name in deepest_first(spaces):
		frappe.delete_doc("SOP Process", name, force=True, ignore_permissions=True)

	frappe.db.commit()

	return {"cleared": len(procedures), "spaces": spaces}


def deepest_first(spaces):
	rows = frappe.get_all(
		"SOP Process", filters={"space": ("in", spaces)}, fields=["name", "parent_process"]
	)
	depth = {row.name: 0 for row in rows}
	parents = {row.name: row.parent_process for row in rows}

	for name in depth:
		current = parents.get(name)
		while current in parents:
			depth[name] += 1
			current = parents.get(current)

	return sorted(depth, key=lambda name: -depth[name])
