# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, nowdate

from sop.api import lifecycle
from sop.api import procedures as procedures_api
from sop.api import processes as processes_api
from sop.api import requirements as requirements_api
from sop.api import review as review_api
from sop.api import sessions as sessions_api
from sop.api import training as training_api

PEOPLE = [
	("sara.james@example.com", "Sara", "James", ["SOP Manager", "SOP Approver"]),
	("dan.walsh@example.com", "Dan", "Walsh", ["SOP Author"]),
	("leila.k@example.com", "Leila", "Karimian", ["SOP Approver", "SOP Trainer"]),
	("tom.r@example.com", "Tom", "Rivera", ["SOP Reader"]),
]

TEAM = "All Staff"

APP_PROCESSES = [
	("Writing Procedures", ["Drafting", "Review & Approval", "Publishing"]),
	("Training", ["Assigning training", "Recording outcomes"]),
]

PROCEDURES = [
	{
		"slug": "write",
		"title": "How to write a procedure in this app",
		"space": "OPS",
		"process": "Drafting",
		"summary": "Open the app, pick a space, and write your first procedure in under five minutes.",
		"state": "effective",
		"tags": ["getting-started"],
		"content": """<h2>Purpose</h2>
<p>Anyone on the team can create a procedure. This guide walks you through it from a blank page to a published document.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Open your space</strong> — click the space name in the left sidebar. A space groups related procedures together (e.g. Operations, HR).</p></div>
<div data-sop="step"><p><strong>Create a new procedure</strong> — click <em>New procedure</em> in the top right. Give it a short, action-oriented title.</p></div>
<div data-sop="step"><p><strong>Write the content</strong> — use the editor to add steps, callouts and headings. Keep each step to one action.</p>
<p data-sop="step-meta">Tip: use the <em>Step</em> block from the toolbar to get numbered steps automatically.</p></div>
<div data-sop="step"><p><strong>Save your draft</strong> — your draft is private until you send it for review. Save often.</p></div>
<div data-sop="callout" data-tone="note"><p>A good title answers the question "What does this procedure make happen?" — not just "What is this about?"</p></div>
<h2>What's next</h2>
<p>Once the draft looks right, send it for review — see {sop:review} for the full steps.</p>""",
	},
	{
		"slug": "review",
		"title": "How to send a procedure for review",
		"space": "OPS",
		"process": "Review & Approval",
		"summary": "When your draft is ready, one click puts it in front of the right approvers.",
		"state": "effective",
		"effective_since": -60,
		"tags": ["getting-started", "review"],
		"content": """<h2>Purpose</h2>
<p>Sending for review locks the content and routes it to the people who need to approve it before it goes live.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Open the draft</strong> — find it in your space or in the <em>Waiting on you</em> section of your profile. {user:manager} will be notified once you send.</p></div>
<div data-sop="step"><p><strong>Click "Send for review"</strong> — this button appears in the top bar when your draft is ready to go. The procedure moves to <em>In Review</em> status.</p></div>
<div data-sop="step"><p><strong>Approvers are notified</strong> — each person in the approval chain gets a notification. They can add comments directly on the text. See {sop:approve} for what they do next.</p></div>
<div data-sop="step"><p><strong>Watch for comments</strong> — if an approver requests changes, the procedure comes back to you. Make the edits and send again.</p></div>
<div data-sop="callout" data-tone="note"><p>You can see who is in the approval chain by clicking <em>Reviewers</em> in the sidebar while the procedure is open.</p></div>""",
	},
	{
		"slug": "approve",
		"title": "How to approve a procedure",
		"space": "OPS",
		"process": "Review & Approval",
		"summary": "Approvers read, comment, and either approve or send the procedure back for changes.",
		"state": "in_review",
		"tags": ["review"],
		"content": """<h2>Purpose</h2>
<p>As an approver your job is to make sure the procedure is accurate, complete and safe to follow before it becomes the official way of working.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Open the notification</strong> — click the link in your email or notification. The procedure opens in read mode.</p></div>
<div data-sop="step"><p><strong>Read carefully</strong> — highlight any text and click <em>Comment</em> to pin a note to that exact spot. Comments stay visible to {user:author}.</p></div>
<div data-sop="step"><p><strong>Approve or request changes</strong> — use the buttons at the bottom of the page. Once approved, {user:manager} can publish it — see {sop:publish}.</p></div>
<div data-sop="callout" data-tone="warning"><p>Approving means you have read and are satisfied with the procedure as written. Only approve when you are sure.</p></div>""",
	},
	{
		"slug": "publish",
		"title": "How to bring a procedure into force",
		"space": "OPS",
		"process": "Publishing",
		"summary": "Publishing sets the effective date, assigns a revision number, and notifies everyone who needs training.",
		"state": "approved",
		"tags": ["getting-started"],
		"content": """<h2>Purpose</h2>
<p>Once all approvers have signed off, a Manager can publish the procedure. Publishing gives it a revision number and sets the date it becomes the official way of working.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Open the approved procedure</strong> — its status shows <em>Approved</em> in the header badge.</p></div>
<div data-sop="step"><p><strong>Click "Bring into force"</strong> — a dialog asks for the effective date and a short summary of what changed.</p></div>
<div data-sop="step"><p><strong>Set the effective date</strong> — this can be today or a future date. Training is assigned automatically — see {sop:training} for how that works.</p></div>
<div data-sop="step"><p><strong>Mark material changes</strong> — tick the checkbox if the change is significant enough that everyone must be trained again, not just new staff.</p></div>
<div data-sop="callout" data-tone="note"><p>After publishing, readers who need to acknowledge the procedure will see a banner the next time they open it.</p></div>""",
	},
	{
		"slug": "training",
		"title": "How to assign and track training",
		"space": "HR",
		"process": "Assigning training",
		"summary": "Training rules automatically assign the right procedures to the right people. Here is how to set them up.",
		"state": "effective",
		"tags": ["training", "getting-started"],
		"content": """<h2>Purpose</h2>
<p>Training rules connect a group of people to a set of procedures. When a new procedure is published — like {sop:publish} — assignments are created automatically.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Go to Training rules</strong> — find it in the left navigation under Training.</p></div>
<div data-sop="step"><p><strong>Create a rule</strong> — pick whether it covers a whole space (all procedures in that space) or a specific process.</p></div>
<div data-sop="step"><p><strong>Set the audience</strong> — a team, a single person, or everyone. {user:trainer} manages training sign-offs for this demo.</p></div>
<div data-sop="step"><p><strong>Choose the method and due days</strong> — Read & Understand means they read the procedure and acknowledge it. On the Job needs a trainer to sign off.</p></div>
<div data-sop="callout" data-tone="note"><p>Check the Training matrix to see who is compliant, overdue, or not yet assigned across the whole space at a glance.</p></div>""",
	},
	{
		"slug": "onboard",
		"title": "Onboarding a new team member",
		"space": "HR",
		"process": "Recording outcomes",
		"summary": "What to do before a new person's first day so they are set up in the app on day one.",
		"state": "draft",
		"tags": ["onboarding"],
		"content": """<h2>Purpose</h2>
<p>New team members need an account, the right role, and their first training assignments waiting for them when they log in. See {sop:training} for how training rules work.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Create the user account</strong> — go to Settings &gt; Users in the desk and add them. Assign the SOP Reader role as a minimum.</p></div>
<div data-sop="step"><p><strong>Add them to a team</strong> — go to Settings &gt; Teams, open the right team and add them. Their training rules apply immediately. Contact {user:manager} if you need a new team created.</p></div>
<div data-sop="step"><p><strong>Check their training queue</strong> — open Training &gt; Matrix, filter by their name, and confirm the right assignments are showing.</p></div>
<div data-sop="callout" data-tone="note"><p>If no assignments appear, check that a training rule covers the team they joined and covers the space or process you expect.</p></div>""",
	},
	{
		"slug": "retire",
		"title": "How to retire a procedure that is no longer used",
		"space": "OPS",
		"process": "Drafting",
		"summary": "Retiring removes a procedure from active use without deleting its history.",
		"state": "retired",
		"tags": ["admin"],
		"content": """<h2>Purpose</h2>
<p>When a procedure is replaced or no longer needed, retire it. The history and all acknowledgements are preserved, but it no longer appears as active. For the full lifecycle — from {sop:write} through to retirement — this is the final step.</p>
<h2>Steps</h2>
<div data-sop="step"><p><strong>Open the effective procedure</strong> — only an effective procedure can be retired.</p></div>
<div data-sop="step"><p><strong>Click the three-dot menu</strong> — choose <em>Retire</em> from the list. Only {user:manager} and users with the Manager role can do this.</p></div>
<div data-sop="step"><p><strong>Confirm</strong> — the procedure moves to <em>Retired</em> status immediately. It will no longer trigger new training assignments.</p></div>
<div data-sop="callout" data-tone="warning"><p>Retiring is permanent. If you need to update a procedure instead, use <em>Start a revision</em> — that keeps the current version in force while you work on the next one.</p></div>""",
	},
]

SHAPES = {
	"Completed": {"method": "Read & Understand", "due": -6, "outcome": "Competent", "done": 1},
	"In Progress": {"method": "On the Job", "due": 6, "outcome": "Pending", "done": 1},
	"Assigned": {"method": "Read & Understand", "due": 12, "outcome": "Pending", "done": 0},
	"Overdue": {"method": "Read & Understand", "due": -9, "outcome": "Pending", "done": 0},
}




def after_migrate():
	if not wanted():
		print("SOP demo data: off. Run `bench --site <site> set-config sop_demo_data 1` to seed it.")
		return

	if seeded():
		return

	result = install(force=1)
	print(f"SOP demo data: created {len(result.get('procedures', []))} procedures in OPS and HR.")


def seeded():
	return bool(frappe.db.exists("SOP Space", {"space_code": ("in", ["OPS", "HR"])}))


def wanted():
	flag = frappe.conf.get("sop_demo_data")
	return bool(flag) if flag is not None else bool(frappe.conf.get("developer_mode"))


def install(force=0):
	if frappe.db.count("SOP") and not force:
		return {"skipped": "procedures already exist"}

	people = ensure_people()
	ensure_team(people)
	manager = people[0]

	spaces = {
		"OPS": ensure_space(
			manager,
			"Operations",
			"OPS",
			"How the team gets things done — the official way of working.",
		),
		"HR": ensure_space(
			manager, "People & Culture", "HR", "Onboarding, training and team practices."
		),
	}

	seed_app_processes(manager, spaces)

	created = []
	for definition in PROCEDURES:
		created.append(build(definition, spaces, people))

	inject_mentions(created, people)

	seed_training(spaces["OPS"], people)
	seed_session(people)
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
	wanted = [
		(people[0], "Approver"),
		(frappe.session.user, "Approver"),
		(people[2], "Reviewer"),
		(people[1], "Author"),
		(people[3], "Reader"),
	]

	if frappe.db.exists("SOP Team", TEAM):
		doc = frappe.get_doc("SOP Team", TEAM)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "SOP Team",
				"team_name": TEAM,
				"description": "Everyone who works a line, plus the supervisors who sign for them.",
			}
		)

	present = {row.user for row in doc.members}
	for user, role in wanted:
		if user not in present:
			doc.append("members", {"user": user, "team_role": role})
			present.add(user)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return doc.name


def ensure_space(manager, title, code, description, template=None):
	existing = frappe.db.get_value("SOP Space", {"space_code": code}, "name")
	if existing:
		return existing

	space = as_user(
		manager,
		procedures_api.create_space,
		title=title,
		space_code=code,
		description=description,
		template=template,
		team=TEAM,
	)

	return space["name"]


def seed_app_processes(manager, spaces):
	for index, (group, children) in enumerate(APP_PROCESSES, start=1):
		space = spaces["OPS"] if group == "Writing Procedures" else spaces["HR"]
		parent = ensure_process(manager, space, group, None, index * 10)

		for position, child in enumerate(children, start=1):
			ensure_process(manager, space, child, parent, position * 10)


def ensure_process(manager, space, title, parent, sequence):
	existing = frappe.db.get_value(
		"SOP Process", {"space": space, "title": title, "parent_process": parent}, "name"
	)
	if existing:
		return existing

	process = as_user(
		manager,
		processes_api.create_process,
		title=title,
		space=space,
		parent=parent,
		sequence=sequence,
	)

	return process["name"]


def build(definition, spaces, people):
	space = spaces[definition["space"]]
	process = frappe.db.get_value(
		"SOP Process", {"space": space, "title": definition["process"]}, "name"
	)

	draft = as_user(
		people[1],
		procedures_api.save_draft,
		space=space,
		title=definition["title"],
		summary=definition["summary"],
		content=definition["content"],
		process=process,
		risk_level="Medium",
		is_controlled=1,
	)

	for tag in definition["tags"]:
		add_tag(tag, "SOP", draft["name"])

	advance(draft["name"], definition["state"], people, definition.get("effective_since", -40))

	return draft["name"]


def inject_mentions(created, people):
	slug_to_name = {d["slug"]: sop for d, sop in zip(PROCEDURES, created)}

	user_map = {
		"manager": people[0],
		"author":  people[1],
		"trainer": people[2],
		"reader":  people[3],
	}

	for sop_name in created:
		doc = frappe.get_doc("SOP", sop_name)
		content = doc.content or ""
		changed = False

		for slug, target_name in slug_to_name.items():
			placeholder = f"{{sop:{slug}}}"
			if placeholder in content:
				title = frappe.db.get_value("SOP", target_name, "title")
				link = f'<a href="#mention:SOP:{target_name}">{title}</a>'
				content = content.replace(placeholder, link)
				changed = True

		for role, email in user_map.items():
			placeholder = f"{{user:{role}}}"
			if placeholder in content:
				full_name = frappe.db.get_value("User", email, "full_name") or email
				link = f'<a href="#mention:User:{email}">{full_name}</a>'
				content = content.replace(placeholder, link)
				changed = True

		if changed:
			frappe.db.set_value("SOP", sop_name, "content", content, update_modified=False)


def add_tag(tag, doctype, name):
	from frappe.desk.doctype.tag.tag import add_tag as tag_it

	tag_it(tag, doctype, name)


def advance(sop, state, people, since=-40):
	if state == "draft":
		return

	as_user(people[1], lifecycle.send_for_approval, sop)

	if state == "in_review":
		as_user(
			people[2],
			review_api.add_comment,
			sop,
			"Name the form this produces — an operator should not have to guess.",
		)
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
		people[0],
		lifecycle.publish,
		sop,
		effective_from=add_days(nowdate(), since),
		change_summary="First controlled issue.",
		is_material=1,
	)

	if state == "retired":
		as_user(
			people[0],
			lifecycle.retire,
			sop,
			"Superseded by the plant-wide sampling procedure.",
		)
		return

	sign(sop, people[2:])


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
		as_user(user, procedures_api.acknowledge, sop, version)


def seed_training(space, people):
	manager, author, trainer, reader = people
	requirement = ensure_requirement(manager, space)

	effective = frappe.get_all(
		"SOP", filters={"space": space, "status": "Effective"}, pluck="name",
		limit_page_length=0,
	)
	if not effective:
		return

	trainees = [frappe.session.user, author, trainer, reader]

	for index, sop in enumerate(effective):
		for position, trainee in enumerate(trainees):
			state = ("Completed", "In Progress", "Assigned", "Overdue")[(index + position) % 4]
			assign(manager, trainer, sop, trainee, state)

	as_user(manager, requirements_api.run_requirement, requirement)


def ensure_requirement(manager, space):
	existing = frappe.db.get_value(
		"SOP Training Requirement", {"scope": "Space", "space": space, "applies_to": "Team"}, "name"
	)
	if existing:
		return existing

	requirement = as_user(
		manager,
		requirements_api.save_requirement,
		enabled=1,
		applies_to="Team",
		team=TEAM,
		scope="Space",
		space=space,
		method="Read & Understand",
		due_days=14,
		refresher_months=12,
	)

	return requirement["name"]


def assign(manager, trainer, sop, trainee, state):
	shape = SHAPES[state]

	created = as_user(
		manager,
		training_api.assign,
		sop=sop,
		trainees=[trainee],
		method=shape["method"],
		due_days=shape["due"],
	)
	if not created:
		return None

	name = created[0]

	for idx in range(1, shape["done"] + 1):
		as_user(trainee, training_api.complete_task, name, idx)

	if shape["outcome"] != "Pending":
		assessor = manager if trainee == trainer else trainer
		as_user(assessor, training_api.record_outcome, name, shape["outcome"])

	return name


def seed_session(people):
	manager, author, trainer, reader = people

	covered = frappe.get_all(
		"SOP", filters={"status": "Effective"}, pluck="name", order_by="creation asc",
		limit_page_length=2,
	)
	if not covered or frappe.db.count("SOP Training Session"):
		return

	as_user(
		trainer,
		sessions_api.save_session,
		title="Line clearance refresher",
		trainer=trainer,
		scheduled_on=f"{add_days(nowdate(), 5)} 09:30:00",
		location="Training room, block B",
		method="Classroom",
		procedures=covered,
		attendees=[author, reader],
		notes="Walk the line after the classroom half. Bring a spare clearance record.",
	)


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
	frappe.flags.sop_removal = True

	try:
		return wipe_demo()
	finally:
		frappe.flags.sop_removal = False


def wipe_demo():
	spaces = frappe.get_all(
		"SOP Space", pluck="name",
		limit_page_length=0,
	)
	if not spaces:
		return {"cleared": 0}

	procedures = frappe.get_all("SOP", filters={"space": ("in", spaces)}, pluck="name", limit_page_length=0)

	assignments = frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": ("in", procedures or [""])},
		pluck="name",
		limit_page_length=0,
	)

	for doctype, field in (
		("SOP Training Assignment", "sop"),
		("SOP Acknowledgement", "sop"),
		("SOP Revision", "sop"),
		("SOP Review Comment", "sop"),
	):
		for name in frappe.get_all(doctype, filters={field: ("in", procedures or [""])}, pluck="name", limit_page_length=0):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	for name in procedures:
		frappe.delete_doc("SOP", name, force=True, ignore_permissions=True)

	for name in frappe.get_all(
		"SOP Training Requirement", filters={"space": ("in", spaces)}, pluck="name",
		limit_page_length=0,
	):
		frappe.delete_doc("SOP Training Requirement", name, force=True, ignore_permissions=True)

	for name in deepest_first(spaces):
		frappe.delete_doc("SOP Process", name, force=True, ignore_permissions=True)

	frappe.db.delete(
		"Notification Log",
		{
			"document_type": ("in", ["SOP", "SOP Training Assignment"]),
			"document_name": ("in", (procedures + assignments) or [""]),
		},
	)

	for name in sessions_covering(procedures):
		frappe.delete_doc("SOP Training Session", name, force=True, ignore_permissions=True)

	for name in spaces:
		frappe.delete_doc("SOP Space", name, force=True, ignore_permissions=True)

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
		"SOP Process", filters={"space": ("in", spaces)}, fields=["name", "parent_process"],
		limit_page_length=0,
	)
	depth = {row.name: 0 for row in rows}
	parents = {row.name: row.parent_process for row in rows}

	for name in depth:
		current = parents.get(name)
		while current in parents:
			depth[name] += 1
			current = parents.get(current)

	return sorted(depth, key=lambda name: -depth[name])
