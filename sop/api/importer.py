import io
import posixpath
import re
import zipfile
from html import escape
from xml.etree import ElementTree

import frappe
from frappe import _

from sop.api.mentions import record_url

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
ID_PATTERN = re.compile(r"\b((?:SOP|RA|LOG)-[A-Z]+-\d{3})\b")
NUMBERED = re.compile(r"^\s*\d+[.)]\s*")
WARNING = re.compile(r"^\s*⚠\s*")
DANISH = re.compile(r"(?:^|[\s_-])(DA|Dansk)$", re.I)
ENGLISH = re.compile(r"(?:^|[\s_-])(EN|Eng|English)$", re.I)
FOLDER_NOISE = re.compile(r"\b(updated?s?|sops?|sop)\b|[-_]+", re.I)
HUES = 8


def can_import():
	roles = set(frappe.get_roles())
	if not {"SOP Author", "SOP Manager", "System Manager"} & roles:
		frappe.throw(_("Only SOP authors can import procedures."), frappe.PermissionError)


def file_bytes(file_url):
	file = frappe.get_doc("File", {"file_url": file_url})
	file.check_permission("read")
	content = file.get_content()
	return content if isinstance(content, bytes) else content.encode()


def word_files(file_url):
	data = file_bytes(file_url)
	name = posixpath.basename(file_url)
	if name.lower().endswith(".docx"):
		return [(name, data)], []

	files, skipped = [], []
	with zipfile.ZipFile(io.BytesIO(data)) as archive:
		for entry in archive.infolist():
			path = entry.filename.replace("\\", "/")
			base = posixpath.basename(path)
			if entry.is_dir() or not base or base.startswith(("~$", ".")) or "__MACOSX" in path:
				continue
			if base.lower().endswith(".docx"):
				files.append((path, archive.read(entry)))
			else:
				skipped.append(
					{"file": path, "reason": _("Not a Word file — attach it to a resource instead")}
				)
	return files, skipped


def paragraph_text(element):
	parts = []
	for node in element.iter():
		if node.tag == W + "t":
			parts.append(node.text or "")
		elif node.tag in (W + "tab", W + "br"):
			parts.append(" ")
	return re.sub(r"\s+", " ", "".join(parts)).strip()


def blocks_of(data):
	root = ElementTree.fromstring(zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"))
	blocks = []
	for element in root.find(W + "body"):
		if element.tag == W + "p":
			text = paragraph_text(element)
			if text:
				style = element.find(f"{W}pPr/{W}pStyle")
				blocks.append(
					{"kind": "p", "text": text, "style": style.get(W + "val") if style is not None else ""}
				)
		elif element.tag == W + "tbl":
			rows = []
			for row in element.findall(W + "tr"):
				cells = []
				for cell in row.findall(W + "tc"):
					cells.append([text for text in (paragraph_text(p) for p in cell.iter(W + "p")) if text])
				rows.append(cells)
			if rows:
				blocks.append({"kind": "table", "rows": rows})
	return blocks


def cell_text(cell):
	return " ".join(cell).strip()


def language_of(path):
	stem = posixpath.splitext(posixpath.basename(path))[0].strip()
	if DANISH.search(stem):
		return "DA"
	if ENGLISH.search(stem):
		return "EN"
	return ""


def process_title(path):
	folders = [part for part in posixpath.dirname(path).split("/") if part]
	for folder in reversed(folders):
		title = re.sub(r"\s+", " ", FOLDER_NOISE.sub(" ", folder)).strip()
		if title:
			title = title.capitalize() if title.isupper() else title
			return title[:1].upper() + title[1:]
	return ""


def header_of(table):
	rows = table["rows"]
	if len(rows) < 2:
		return None
	keys = [cell_text(cell).lower() for cell in rows[0]]
	if "document id" not in keys:
		return None
	return {key: cell_text(value) for key, value in zip(keys, rows[1], strict=False)}


def is_critical(table):
	rows = table["rows"]
	return len(rows) == 1 and len(rows[0]) == 1 and rows[0][0] and WARNING.match(rows[0][0][0])


def is_single_cell(table):
	rows = table["rows"]
	return len(rows) == 1 and len(rows[0]) == 1 and bool(rows[0][0])


def is_box_row(table):
	rows = table["rows"]
	return len(rows) == 1 and 1 < len(rows[0]) <= 4 and all(rows[0])


def box_title(lines):
	if len(lines) > 1 and len(lines[0]) <= 60:
		return WARNING.sub("", lines[0]), lines[1:]
	return None, lines


def phases_of(table):
	cells = [cell_text(cell) for row in table["rows"] for cell in row]
	if not any("colour guide" in cell.lower() or "color guide" in cell.lower() for cell in cells):
		return None
	return [cell for cell in cells if cell and "guide" not in cell.lower()]


def step_columns(table):
	keys = [cell_text(cell).lower() for cell in table["rows"][0]]
	if "#" not in keys or not any(key.startswith("action") for key in keys):
		return None

	def find(*names):
		return next((i for i, key in enumerate(keys) if any(key.startswith(n) for n in names)), None)

	return {
		"phase": find("phase"),
		"action": find("action"),
		"details": find("details", "key points"),
		"where": find("equipment", "location"),
	}


REFERENCE = re.compile("@@REF:(" + ID_PATTERN.pattern[3:-3] + ")@@")


class Builder:
	def __init__(self):
		self.html = []
		self.phases = []

	def text(self, value):
		return ID_PATTERN.sub(lambda match: f"@@REF:{match.group(1)}@@", escape(value))

	def callout(self, tone, lines, title=None):
		body = "".join(f"<p>{self.text(line)}</p>" for line in lines)
		lead = f"<p><strong>{self.text(title)}</strong></p>" if title else ""
		return f'<div data-sop="callout" data-tone="{tone}">{lead}{body}</div>'

	def hue(self, phase):
		if not phase:
			return 0
		key = phase.upper()
		if key not in self.phases:
			self.phases.append(key)
		return self.phases.index(key) % HUES + 1

	def step(self, row, columns):
		def cell(key):
			index = columns.get(key)
			return row[index] if index is not None and index < len(row) else []

		action = cell("action")
		phase = cell_text(cell("phase"))
		parts = []
		if action:
			parts.append(f"<p><strong>{self.text(action[0])}</strong></p>")
			if len(action) > 1:
				parts.append(f"<p><em>{self.text(' '.join(action[1:]))}</em></p>")

		items, warnings = [], []
		for line in cell("details"):
			if WARNING.match(line):
				warnings.append(WARNING.sub("", line))
			else:
				items.append(NUMBERED.sub("", line))
		if items:
			parts.append("<ol>" + "".join(f"<li><p>{self.text(item)}</p></li>" for item in items) + "</ol>")
		for line in warnings:
			parts.append(self.callout("warning", [line]))

		where = cell_text(cell("where"))
		if where:
			parts.append(f'<p data-sop="step-meta">{self.text(where)}</p>')

		if not parts:
			return ""
		return (
			f'<div data-sop="step" data-phase="{escape(phase.upper())}" data-hue="{self.hue(phase)}">'
			+ "".join(parts)
			+ "</div>"
		)

	def table(self, rows):
		head, *body = rows
		out = ["<table><tbody>"]
		out.append("<tr>" + "".join(f"<th><p>{self.text(cell_text(c))}</p></th>" for c in head) + "</tr>")
		for row in body:
			out.append(
				"<tr>"
				+ "".join(
					"<td>" + "".join(f"<p>{self.text(line)}</p>" for line in cell) + "</td>" for cell in row
				)
				+ "</tr>"
			)
		out.append("</tbody></table>")
		return "".join(out)


RECURRING = (
	(re.compile(r"\b(daily|every day|each day)\b", re.I), "Daily"),
	(re.compile(r"\b(weekly|once a week|every week|each week)\b", re.I), "Weekly"),
	(re.compile(r"\b(monthly|once a month|every month)\b", re.I), "Monthly"),
	(re.compile(r"\b(quarterly|every quarter|every 3 months)\b", re.I), "Quarterly"),
	(re.compile(r"\b(yearly|annually|once a year|every year)\b", re.I), "Yearly"),
)
NOTHING_MORE = re.compile(r"^\s*(none|n/a|-|—)?(\s+beyond\s+sop)?\s*\.?\s*$", re.I)


def register_columns(table):
	keys = [cell_text(cell).strip().lower() for cell in table["rows"][0]]
	if "hazard" not in keys or keys.count("l") < 1 or keys.count("s") < 1:
		return None

	def first(*names):
		return next((i for i, key in enumerate(keys) if any(key.startswith(n) for n in names)), None)

	likes = [i for i, key in enumerate(keys) if key == "l"]
	severities = [i for i, key in enumerate(keys) if key == "s"]
	return {
		"id": first("id"),
		"task": first("task"),
		"hazard": keys.index("hazard"),
		"consequence": first("consequence"),
		"controls": first("existing"),
		"actions": first("additional"),
		"likelihood": likes[0],
		"severity": severities[0],
		"residual_likelihood": likes[1] if len(likes) > 1 else None,
		"residual_severity": severities[1] if len(severities) > 1 else None,
	}


def hazard_of(row, columns):
	def value(key):
		index = columns.get(key)
		return cell_text(row[index]) if index is not None and index < len(row) else ""

	def number(key):
		digits = re.match(r"\d+", value(key))
		return int(digits.group()) if digits else 0

	action = value("actions")
	every = next((period for pattern, period in RECURRING if pattern.search(action)), "")
	if NOTHING_MORE.match(action):
		status, action = "Not needed", ""
	else:
		status = "Not needed" if every else "Open"
	return {
		"hazard_id": value("id"),
		"task": value("task"),
		"hazard": value("hazard") or value("task") or "—",
		"consequence": value("consequence"),
		"existing_controls": value("controls"),
		"likelihood": number("likelihood"),
		"severity": number("severity"),
		"additional_actions": action,
		"action_status": status,
		"residual_likelihood": number("residual_likelihood"),
		"residual_severity": number("residual_severity"),
		"recurring_check": action if every else "",
		"check_every": every,
	}


def parse(path, data):
	blocks = blocks_of(data)
	builder = Builder()
	found = {"path": path, "language": language_of(path), "warnings": [], "steps": 0, "hazards": []}
	intro = []
	header = None
	in_notes = False

	for block in blocks:
		if block["kind"] == "p":
			text = block["text"]
			if header is None and len(intro) < 2:
				intro.append(text)
				continue
			if re.match(r"^step[- ]by[- ]step", text, re.I):
				builder.html.append(f"<h2>{escape(re.split(r'\s[–-]\s', text)[0])}</h2>")
			elif re.match(r"^notes?\b", text, re.I) or block["style"].lower().startswith("heading"):
				in_notes = text.lower().startswith("notes")
				builder.html.append(f"<h2>{builder.text(text)}</h2>")
			elif WARNING.match(text):
				builder.html.append(builder.callout("warning", [WARNING.sub("", text)]))
			else:
				builder.html.append(f"<p>{builder.text(text)}</p>")
			continue

		table = block
		if header is None and (meta := header_of(table)):
			header = meta
			continue
		if (phases := phases_of(table)) is not None:
			for phase in phases:
				builder.hue(phase)
			continue
		if is_critical(table):
			lines = table["rows"][0][0]
			builder.html.append(builder.callout("critical", lines[1:], WARNING.sub("", lines[0])))
			continue
		if is_box_row(table):
			for lines in table["rows"][0]:
				tone = "critical" if WARNING.match(lines[0]) else "note"
				title, body = box_title(lines)
				builder.html.append(builder.callout(tone, body, title))
			continue
		if register := register_columns(table):
			for row in table["rows"][1:]:
				if any(row):
					found["hazards"].append(hazard_of(row, register))
			continue
		if columns := step_columns(table):
			for row in table["rows"][1:]:
				if html := builder.step(row, columns):
					builder.html.append(html)
					found["steps"] += 1
			continue
		if is_single_cell(table):
			lines = table["rows"][0][0]
			if in_notes and len(lines) > 1:
				builder.html.append(
					f"<h3>{builder.text(lines[0])}</h3><ul>"
					+ "".join(f"<li><p>{builder.text(line)}</p></li>" for line in lines[1:])
					+ "</ul>"
				)
			else:
				builder.html.append(builder.callout("note", lines))
			continue
		builder.html.append(builder.table(table["rows"]))

	header = header or {}
	sop_id = header.get("document id") or ""
	match = ID_PATTERN.search(sop_id) or ID_PATTERN.search(posixpath.basename(path))
	sop_id = match.group(1) if match else ""
	subtitle = intro[1] if len(intro) > 1 else ""

	if sop_id.startswith("RA-") and found["hazards"]:
		document_type = "Risk Assessment"
	elif sop_id.startswith(("RA-", "LOG-")):
		document_type = "Appendix"
	elif "equipment sop" in subtitle.lower():
		document_type = "Equipment SOP"
	else:
		document_type = "Process SOP"

	if not sop_id:
		found["warnings"].append(_("No Document ID found"))
	if not header:
		found["warnings"].append(_("No header table — version and department not read"))
	if b"<w:drawing" in zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml"):
		found["warnings"].append(_("Has pictures — add them in the editor after import"))

	found.update(
		{
			"sop_no": sop_id,
			"title": intro[0] if intro else posixpath.splitext(posixpath.basename(path))[0],
			"summary": subtitle,
			"document_type": document_type,
			"source_version": header.get("version") or "",
			"department": header.get("department") or "",
			"approved_by": header.get("approved by") or "",
			"source_status": header.get("status") or "",
			"process": process_title(path),
			"content": "".join(builder.html),
			"applies_to": [
				ref for ref in dict.fromkeys(ID_PATTERN.findall(subtitle)) if ref.startswith(("SOP-", "LOG-"))
			],
		}
	)
	return found


def doctype_of(doc_id):
	return "SOP Risk Assessment" if doc_id.startswith("RA-") else "SOP"


def exists(doc_id):
	return bool(frappe.db.exists(doctype_of(doc_id), doc_id) or frappe.db.exists("SOP", doc_id))


def link_references(doc, ids):
	mentioned = set()

	def link(match):
		ref = match.group(1)
		if ref == doc["sop_no"] or ref not in ids:
			return ref
		mentioned.add(ref)
		target = ids[ref]
		return f'<a href="#mention:{target}:{ref}">{ref}</a>'

	doc["content"] = REFERENCE.sub(link, doc["content"])
	doc["mentions"] = sorted(mentioned)


def collect(file_url):
	files, skipped = word_files(file_url)
	parsed, seen = [], {}
	for path, data in sorted(files, key=lambda row: (row[0].count("/"), row[0])):
		if language_of(path) == "DA":
			skipped.append({"file": path, "reason": _("Danish copy — translations are not imported yet")})
			continue
		try:
			doc = parse(path, data)
		except Exception:
			skipped.append({"file": path, "reason": _("Could not read this Word file")})
			continue
		if not doc["sop_no"]:
			skipped.append({"file": path, "reason": _("No Document ID (SOP-, RA- or LOG-) in the file")})
			continue

		key = doc["sop_no"]
		if key in seen:
			first = seen[key]
			if first["title"].strip().lower() == doc["title"].strip().lower():
				skipped.append({"file": path, "reason": _("Duplicate of {0}").format(first["path"])})
				continue
			doc["sop_no"] = f"{key}-B"
			doc["warnings"].append(
				_("{0} is also used by “{1}”. Imported as {2} — confirm which is right.").format(
					key, first["title"], doc["sop_no"]
				)
			)
		seen[doc["sop_no"]] = doc
		doc["exists"] = exists(doc["sop_no"])
		parsed.append(doc)

	ids = {
		doc["sop_no"]: "SOP Risk Assessment" if doc["document_type"] == "Risk Assessment" else "SOP"
		for doc in parsed
	}
	for doc in parsed:
		for match in REFERENCE.finditer(doc["content"]):
			ref = match.group(1)
			if ref in ids:
				continue
			if frappe.db.exists("SOP Risk Assessment", ref):
				ids[ref] = "SOP Risk Assessment"
			elif frappe.db.exists("SOP", ref):
				ids[ref] = "SOP"
	for doc in parsed:
		link_references(doc, ids)

	return parsed, skipped


@frappe.whitelist()
def preview(file_url: str) -> dict:
	can_import()
	parsed, skipped = collect(file_url)
	return {
		"procedures": [{k: v for k, v in doc.items() if k != "content"} for doc in parsed],
		"skipped": skipped,
	}


def department_of(label):
	if not label:
		return None
	return frappe.db.get_value("Department", {"department_name": label}) or frappe.db.get_value(
		"Department", {"name": ("like", f"{label}%")}
	)


def process_for(space, title, cache):
	if not title:
		return None
	if title in cache:
		return cache[title]
	name = frappe.db.get_value("SOP Process", {"space": space, "title": title})
	if not name:
		from sop.api.processes import create_process

		name = create_process(title=title, space=space)["name"]
	cache[title] = name
	return name


@frappe.whitelist()
def run(file_url: str, space: str, processes: dict | str | None = None) -> dict:
	can_import()
	frappe.get_doc("SOP Space", space).check_permission("read")
	names = frappe.parse_json(processes) or {}
	parsed, skipped = collect(file_url)
	created, cache = [], {}
	assessments = [doc for doc in parsed if doc["document_type"] == "Risk Assessment"]

	for doc in parsed:
		if doc["exists"]:
			skipped.append({"file": doc["path"], "reason": _("{0} already exists").format(doc["sop_no"])})
			continue
		if doc in assessments:
			continue

		title = names.get(doc["sop_no"], doc["process"])
		note = source_note(doc)
		sop = frappe.get_doc(
			{
				"doctype": "SOP",
				"sop_no": doc["sop_no"],
				"title": doc["title"][:140],
				"summary": doc["summary"],
				"space": space,
				"sop_process": process_for(space, title, cache),
				"document_type": doc["document_type"],
				"process_owner": frappe.session.user,
				"department": department_of(doc["department"]),
				"status": "Draft",
				"content": doc["content"],
			}
		)
		sop.insert()
		sop.add_comment("Comment", note)
		created.append({"name": sop.name, "title": sop.title, "warnings": doc["warnings"]})

	for doc in assessments:
		if doc["exists"]:
			continue
		assessment = frappe.get_doc(
			{
				"doctype": "SOP Risk Assessment",
				"ra_no": doc["sop_no"],
				"title": doc["title"][:140],
				"space": space,
				"status": "Draft",
				"version_label": doc["source_version"] or "1.0",
				"assessed_by": frappe.session.user,
				"notes": doc["content"],
				"applies_to": [{"sop": ref} for ref in doc["applies_to"] if frappe.db.exists("SOP", ref)],
				"hazards": doc["hazards"],
			}
		)
		assessment.insert()
		assessment.add_comment("Comment", source_note(doc))
		created.append(
			{
				"name": assessment.name,
				"title": assessment.title,
				"warnings": doc["warnings"],
				"url": record_url("SOP Risk Assessment", assessment.name),
			}
		)

	return {"created": created, "skipped": skipped}


def source_note(doc):
	return _("Imported from {0} (version {1}, {2}, approved by {3}).").format(
		posixpath.basename(doc["path"]),
		doc["source_version"] or "—",
		doc["source_status"] or "—",
		doc["approved_by"] or "—",
	)
