import base64
import io
import re
from html import unescape
from urllib.parse import quote

import frappe

from sop.api.safety import for_sop

CRITICAL = re.compile(r'<div[^>]*data-tone="critical"[^>]*>(.*?)</div>', re.S)
STRONG = re.compile(r"<strong>(.*?)</strong>", re.S)
TAGS = re.compile(r"<[^>]+>")


def plain(html):
	return re.sub(r"\s+", " ", unescape(TAGS.sub(" ", html or ""))).strip()


def criticals(content):
	out = []
	for block in CRITICAL.findall(content or ""):
		title = STRONG.search(block)
		heading = plain(title.group(1)) if title else ""
		body = plain(STRONG.sub("", block, count=1) if title else block)
		out.append({"title": heading, "text": body})
	return out


def qr_code(url):
	try:
		import pyqrcode
	except ImportError:
		return None
	buffer = io.BytesIO()
	pyqrcode.create(url).svg(buffer, scale=6, quiet_zone=2)
	return "data:image/svg+xml;base64," + base64.b64encode(buffer.getvalue()).decode()


@frappe.whitelist()
def sign(sop: str) -> dict:
	doc = frappe.get_doc("SOP", sop)
	doc.check_permission("read")
	safety = for_sop(sop)
	url = frappe.utils.get_url(f"/sop/{quote(doc.name)}")
	gear = [
		{
			"label": row.get("title") or row.get("path") or row.get("name"),
			"type": row.get("type_label"),
			"icon": row.get("icon"),
		}
		for row in (safety.get("records") or []) + (safety.get("related") or [])
	]
	return {
		"name": doc.name,
		"sop_no": doc.sop_no,
		"title": doc.title,
		"summary": doc.summary,
		"version": doc.version,
		"status": doc.status,
		"criticals": criticals(doc.content),
		"gear": gear,
		"url": url,
		"qr": qr_code(url),
	}
