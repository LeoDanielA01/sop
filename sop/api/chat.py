# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, escape_html

from sop.api.session import can_use_app

LIMIT = 4000
FIELDS = ["name", "sender", "recipient", "kind", "content", "sop", "duration", "read", "creation"]


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


def shape(row):
	return {
		"name": row.name,
		"sender": row.sender,
		"recipient": row.recipient,
		"kind": row.kind or "Text",
		"content": row.content,
		"sop": row.sop,
		"duration": cint(row.duration),
		"read": cint(row.read),
		"creation": str(row.creation),
	}


def post(sender, recipient, content, kind="Text", sop=None, duration=0):
	doc = frappe.get_doc(
		{
			"doctype": "SOP Message",
			"sender": sender,
			"recipient": recipient,
			"kind": kind,
			"content": content,
			"sop": sop if sop and frappe.db.exists("SOP", sop) else None,
			"duration": cint(duration),
		}
	).insert(ignore_permissions=True)

	message = shape(doc)
	message["sender_name"] = person(sender)["full_name"]

	for user in (sender, recipient):
		frappe.publish_realtime("sop_message", message, user=user, after_commit=True)

	return message


@frappe.whitelist()
def send(to, content, sop=None):
	reachable(to)

	content = (content or "").strip()
	if not content:
		frappe.throw(_("Write something first."))

	if len(content) > LIMIT:
		frappe.throw(_("Keep it under {0} characters.").format(LIMIT))

	return post(frappe.session.user, to, content, sop=sop)


@frappe.whitelist()
def history(user, before=None, limit=50):
	me = frappe.session.user
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
		other = row.recipient if row.sender == me else row.sender
		if other == me:
			continue

		thread = out.get(other)
		if not thread:
			thread = out[other] = {"person": person(other), "last": shape(row), "unread": 0}

		if row.recipient == me and not row.read:
			thread["unread"] += 1

	return list(out.values())


@frappe.whitelist()
def mark_read(user):
	me = frappe.session.user

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
	return frappe.db.count("SOP Message", {"recipient": frappe.session.user, "read": 0})


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

	frappe.sendmail(
		recipients=[email],
		cc=addresses(cc),
		bcc=[me.email] if cint(copy_me) else None,
		subject=subject,
		message=body,
		reply_to=me.email,
		attachments=files,
		reference_doctype="SOP" if sop else None,
		reference_name=sop,
		now=False,
	)

	return {"sent": email}
