# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, escape_html, get_datetime, now_datetime

from sop.api.session import can_use_app

LIMIT = 4000
IMAGES = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "avif"}
QUIET = {"Email"}
FIELDS = [
	"name",
	"channel",
	"sender",
	"recipient",
	"kind",
	"content",
	"email_to",
	"sop",
	"duration",
	"read",
	"file",
	"file_name",
	"file_size",
	"is_image",
	"creation",
]


def reachable(user):
	if not can_use_app():
		frappe.throw(_("You do not have access to Procedures."), frappe.PermissionError)

	if not user or user == frappe.session.user:
		frappe.throw(_("Pick someone else."))

	if not frappe.db.get_value("User", user, "enabled"):
		frappe.throw(_("That person no longer has access."))

	if not can_use_app(user):
		frappe.throw(_("That person does not use Procedures."))


def person(user):
	row = frappe.db.get_value("User", user, ["name", "full_name", "user_image"], as_dict=True)
	if not row:
		return {"name": user, "full_name": user, "image": None}

	return {"name": row.name, "full_name": row.full_name or row.name, "image": row.user_image}


def members(sop):
	row = frappe.db.get_value("SOP", sop, ["owner", "process_owner"], as_dict=True)
	if not row:
		return set()

	users = {row.owner, row.process_owner}
	users.update(frappe.get_all("SOP Approval", filters={"parent": sop, "parenttype": "SOP"}, pluck="approver"))
	users.update(
		frappe.get_all(
			"SOP Message",
			filters={"sop": sop, "channel": "Procedure"},
			pluck="sender",
			distinct=True,
		)
	)
	users = [user for user in users if user and user != "Guest"]
	if not users:
		return set()

	return set(frappe.get_all("User", filters={"name": ("in", users), "enabled": 1}, pluck="name"))


def joinable(sop, user=None):
	user = user or frappe.session.user

	if not sop or not frappe.db.exists("SOP", sop):
		return False

	if not frappe.has_permission("SOP", "read", doc=sop, user=user):
		return False

	return user in members(sop) or bool({"SOP Manager", "System Manager"} & set(frappe.get_roles(user)))


def ensure_room(sop):
	if not can_use_app() or not joinable(sop):
		frappe.throw(_("You are not part of this procedure's discussion."), frappe.PermissionError)


def room_info(sop):
	row = frappe.db.get_value("SOP", sop, ["name", "sop_no", "title"], as_dict=True) or {}
	return {"sop": sop, "sop_no": row.get("sop_no") or sop, "title": row.get("title") or sop}


def shape(row):
	return {
		"name": row.name,
		"channel": row.channel or "Direct",
		"sender": row.sender,
		"recipient": row.recipient,
		"kind": row.kind or "Text",
		"content": row.content,
		"email_to": row.email_to,
		"sop": row.sop,
		"duration": cint(row.duration),
		"read": cint(row.read),
		"file": row.file,
		"file_name": row.file_name,
		"file_size": cint(row.file_size),
		"is_image": cint(row.is_image),
		"creation": str(row.creation),
	}


def post(sender, content="", recipient=None, kind="Text", sop=None, channel="Direct", **extra):
	sop = sop if sop and frappe.db.exists("SOP", sop) else None
	values = {
		"doctype": "SOP Message",
		"channel": channel,
		"sender": sender,
		"recipient": recipient,
		"kind": kind,
		"content": content,
		"sop": sop,
		"duration": cint(extra.get("duration")),
		"email_to": extra.get("email_to"),
	}

	file = extra.get("file")
	if file:
		row = frappe.db.get_value("File", file, ["name", "file_name", "file_size", "owner"], as_dict=True)
		if not row or row.owner != sender:
			frappe.throw(_("You can only share files you uploaded."), frappe.PermissionError)

		extension = (row.file_name or "").rsplit(".", 1)[-1].lower()
		values.update(
			file=row.name,
			file_name=row.file_name,
			file_size=cint(row.file_size),
			is_image=1 if extension in IMAGES else 0,
		)

	doc = frappe.get_doc(values).insert(ignore_permissions=True)

	if file:
		frappe.db.set_value(
			"File",
			file,
			{"attached_to_doctype": "SOP Message", "attached_to_name": doc.name},
			update_modified=False,
		)

	message = shape(doc)
	message["sender_name"] = person(sender)["full_name"]

	if channel == "Procedure":
		message["room"] = room_info(sop)
		audience = members(sop) | {sender}
	else:
		audience = {sender, recipient}

	for user in audience:
		frappe.publish_realtime("sop_message", message, user=user, after_commit=True)

	return message


@frappe.whitelist()
def send(content=None, to=None, sop=None, file=None, room=0):
	content = (content or "").strip()

	if not content and not file:
		frappe.throw(_("Write something first."))

	if len(content) > LIMIT:
		frappe.throw(_("Keep it under {0} characters.").format(LIMIT))

	kind = "File" if file else "Text"

	if cint(room):
		ensure_room(sop)
		return post(frappe.session.user, content, kind=kind, sop=sop, channel="Procedure", file=file)

	reachable(to)
	return post(frappe.session.user, content, recipient=to, kind=kind, sop=sop, file=file)


@frappe.whitelist()
def room(sop):
	ensure_room(sop)

	people = sorted((person(user) for user in members(sop)), key=lambda row: row["full_name"].lower())
	return {**room_info(sop), "members": people}


@frappe.whitelist()
def history(user=None, sop=None, before=None, limit=50):
	me = frappe.session.user

	if sop and not user:
		ensure_room(sop)
		filters = {"sop": sop, "channel": "Procedure"}
	else:
		filters = {"sender": ("in", [me, user]), "recipient": ("in", [me, user])}

	if before:
		filters["creation"] = ("<", before)

	rows = frappe.get_all(
		"SOP Message",
		filters=filters,
		fields=FIELDS,
		order_by="creation desc",
		limit_page_length=min(cint(limit) or 50, 200),
	)

	return [shape(row) for row in reversed(rows)]


def seen_marks(user):
	return {
		row.sop: get_datetime(row.seen_at)
		for row in frappe.get_all("SOP Chat Seen", filters={"user": user}, fields=["sop", "seen_at"])
	}


def room_threads(me):
	rows = frappe.get_all(
		"SOP Message",
		filters={"channel": "Procedure"},
		fields=FIELDS,
		order_by="creation desc",
		limit_page_length=1000,
	)

	marks = seen_marks(me)
	allowed = {}
	out = {}

	for row in rows:
		if row.sop not in allowed:
			allowed[row.sop] = me in members(row.sop) and frappe.has_permission("SOP", "read", doc=row.sop)
		if not allowed[row.sop]:
			continue

		thread = out.get(row.sop)
		if not thread:
			last = shape(row)
			last["sender_name"] = person(row.sender)["full_name"]
			thread = out[row.sop] = {"room": room_info(row.sop), "last": last, "unread": 0}

		mark = marks.get(row.sop)
		fresh = mark is None or get_datetime(row.creation) > mark
		if row.sender != me and row.kind not in QUIET and fresh:
			thread["unread"] += 1

	return list(out.values())


@frappe.whitelist()
def threads():
	me = frappe.session.user

	rows = frappe.get_all(
		"SOP Message",
		or_filters={"sender": me, "recipient": me},
		fields=FIELDS,
		order_by="creation desc",
		limit_page_length=500,
	)

	out = {}
	for row in rows:
		if row.channel == "Procedure" or not row.recipient:
			continue

		other = row.recipient if row.sender == me else row.sender
		if other == me:
			continue

		thread = out.get(other)
		if not thread:
			thread = out[other] = {"person": person(other), "last": shape(row), "unread": 0}

		if row.recipient == me and not row.read and row.kind not in QUIET:
			thread["unread"] += 1

	combined = list(out.values()) + room_threads(me)
	return sorted(combined, key=lambda thread: thread["last"]["creation"], reverse=True)


def mark_seen(sop, user):
	name = frappe.db.get_value("SOP Chat Seen", {"user": user, "sop": sop})

	if name:
		frappe.db.set_value("SOP Chat Seen", name, "seen_at", now_datetime(), update_modified=False)
		return

	frappe.get_doc({"doctype": "SOP Chat Seen", "user": user, "sop": sop, "seen_at": now_datetime()}).insert(
		ignore_permissions=True
	)


@frappe.whitelist()
def mark_read(user=None, sop=None):
	me = frappe.session.user

	if sop and not user:
		ensure_room(sop)
		mark_seen(sop, me)
		return {"read": 1}

	names = frappe.get_all(
		"SOP Message",
		filters={"sender": user, "recipient": me, "read": 0},
		pluck="name",
		limit_page_length=0,
	)

	for name in names:
		frappe.db.set_value("SOP Message", name, "read", 1, update_modified=False)

	if names:
		frappe.publish_realtime("sop_message_read", {"by": me}, user=user, after_commit=True)

	return {"read": len(names)}


@frappe.whitelist()
def unread():
	me = frappe.session.user
	direct = frappe.db.count("SOP Message", {"recipient": me, "read": 0, "kind": ("not in", list(QUIET))})
	rooms = {thread["room"]["sop"]: thread["unread"] for thread in room_threads(me) if thread["unread"]}

	return {"total": direct + sum(rooms.values()), "direct": direct, "rooms": rooms}


@frappe.whitelist()
def typing(to=None, sop=None):
	me = person(frappe.session.user)

	if sop and not to:
		if not joinable(sop):
			return
		for user in members(sop) - {me["name"]}:
			frappe.publish_realtime("sop_typing", {"from": me, "sop": sop}, user=user)
		return

	reachable(to)
	frappe.publish_realtime("sop_typing", {"from": me}, user=to)


@frappe.whitelist()
def attachment(message):
	row = frappe.db.get_value(
		"SOP Message", message, ["sender", "recipient", "channel", "sop", "file", "is_image"], as_dict=True
	)
	if not row or not row.file:
		raise frappe.DoesNotExistError

	me = frappe.session.user
	allowed = joinable(row.sop) if row.channel == "Procedure" else me in (row.sender, row.recipient)
	if not allowed:
		raise frappe.PermissionError

	file = frappe.get_doc("File", row.file)
	frappe.local.response.update(
		{
			"type": "download",
			"filename": file.file_name,
			"filecontent": file.get_content(),
			"display_content_as": "inline" if row.is_image else "attachment",
		}
	)


@frappe.whitelist()
def people(query=None):
	if not can_use_app():
		return []

	filters = {
		"enabled": 1,
		"user_type": "System User",
		"name": ("not in", ["Administrator", "Guest", frappe.session.user]),
	}
	or_filters = None

	if query:
		or_filters = {"full_name": ("like", f"%{query}%"), "name": ("like", f"%{query}%")}

	rows = frappe.get_all(
		"User",
		filters=filters,
		or_filters=or_filters,
		fields=["name", "full_name", "user_image"],
		order_by="full_name asc",
		limit_page_length=40,
	)

	return [
		{"name": row.name, "full_name": row.full_name or row.name, "image": row.user_image}
		for row in rows
		if can_use_app(row.name)
	]


def addresses(value):
	if not value:
		return []

	if isinstance(value, str):
		value = value.replace(";", ",").split(",")

	out = []
	for entry in value:
		entry = (entry or "").strip()
		if not entry:
			continue

		email = frappe.db.get_value("User", entry, "email") or entry
		if not frappe.utils.validate_email_address(email):
			frappe.throw(_("{0} is not a valid email address.").format(escape_html(entry)))

		out.append(email)

	return out


def mail_context(to, sop=None):
	recipient = frappe.get_cached_doc("User", to)
	sender = frappe.get_cached_doc("User", frappe.session.user)

	context = {
		"recipient_name": recipient.full_name or recipient.name,
		"recipient_first_name": recipient.first_name or recipient.full_name or recipient.name,
		"sender_name": sender.full_name or sender.name,
		"recipient": {"name": recipient.name, "full_name": recipient.full_name, "email": recipient.email},
		"sender": {"name": sender.name, "full_name": sender.full_name, "email": sender.email},
	}

	if sop and frappe.db.exists("SOP", sop) and frappe.has_permission("SOP", "read", doc=sop):
		doc = frappe.get_doc("SOP", sop).as_dict(no_default_fields=True)
		doc.pop("content", None)
		doc["link"] = frappe.utils.get_url(f"/sop/{sop}")
		context.update(doc)
		context["doc"] = doc

	return context


@frappe.whitelist()
def templates():
	return frappe.get_all(
		"Email Template",
		fields=["name", "subject"],
		order_by="name asc",
		limit_page_length=200,
	)


@frappe.whitelist()
def use_template(template, to, sop=None):
	reachable(to)

	row = frappe.get_doc("Email Template", template)
	context = mail_context(to, sop)
	body = row.response_html if row.use_html else row.response

	return {
		"subject": frappe.render_template(row.subject or "", context),
		"message": frappe.render_template(body or "", context),
	}


@frappe.whitelist()
def save_template(title, subject, message):
	if not {"SOP Manager", "SOP Author", "System Manager"} & set(frappe.get_roles()):
		frappe.throw(_("Only authors and managers can save templates."), frappe.PermissionError)

	title = (title or "").strip()
	if not title:
		frappe.throw(_("Give the template a name."))

	if frappe.db.exists("Email Template", title):
		doc = frappe.get_doc("Email Template", title)
	else:
		doc = frappe.new_doc("Email Template")
		doc.name = title
		doc.set("__newname", title)

	doc.subject = subject
	doc.use_html = 0
	doc.response = message
	doc.flags.ignore_permissions = True
	doc.save()

	return {"name": doc.name}


@frappe.whitelist()
def mail(to, subject, message, sop=None, cc=None, attachments=None, copy_me=0, add_link=1):
	from frappe.utils.html_utils import sanitize_html

	reachable(to)

	subject = (subject or "").strip()
	body = sanitize_html(message or "")

	if not subject or not frappe.utils.strip_html(body).strip():
		frappe.throw(_("Add a subject and a message."))

	email = frappe.db.get_value("User", to, "email") or to
	me = frappe.get_cached_doc("User", frappe.session.user)

	if sop and frappe.db.exists("SOP", sop):
		if cint(add_link):
			link = frappe.utils.get_url(f"/sop/{sop}")
			body += f"<p style='margin-top:16px'><a href='{link}'>{escape_html(_('Open the procedure'))}</a></p>"
	else:
		sop = None

	if isinstance(attachments, str):
		attachments = frappe.parse_json(attachments)

	files = []
	for name in attachments or []:
		owner = frappe.db.get_value("File", name, "owner")
		if owner != frappe.session.user:
			frappe.throw(_("You can only attach files you uploaded."), frappe.PermissionError)
		files.append({"fid": name})

	copies = addresses(cc)

	frappe.sendmail(
		recipients=[email],
		cc=copies,
		bcc=[me.email] if cint(copy_me) else None,
		subject=subject,
		message=body,
		reply_to=me.email,
		attachments=files,
		reference_doctype="SOP" if sop else None,
		reference_name=sop,
		now=False,
	)

	record_email(to, email, copies, subject, body, sop)

	return {"sent": email}


def record_email(to, email, copies, subject, body, sop):
	me = frappe.session.user
	name = person(to)["full_name"]

	post(me, subject, recipient=to, kind="Email", sop=sop, email_to=name)

	if not sop:
		return

	if joinable(sop):
		post(me, subject, kind="Email", sop=sop, channel="Procedure", email_to=name)

	sender = frappe.get_cached_doc("User", me)
	frappe.db.savepoint("sop_email_trail")

	try:
		frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Sent",
				"subject": subject,
				"content": body,
				"sender": sender.email,
				"sender_full_name": sender.full_name,
				"recipients": email,
				"cc": ", ".join(copies),
				"reference_doctype": "SOP",
				"reference_name": sop,
				"status": "Linked",
			}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.db.rollback(save_point="sop_email_trail")
		frappe.log_error(title=f"SOP email trail failed for {sop}")
