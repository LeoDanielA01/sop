# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re
from typing import ClassVar

import frappe
from frappe.search.sqlite_search import SQLiteSearch

TAG = re.compile(r"<[^>]+>")
SPACE = re.compile(r"\s+")


class SOPSQLiteSearch(SQLiteSearch):
	INDEX_NAME = "sop_search.db"

	INDEX_SCHEMA: ClassVar[dict] = {
		"text_fields": ["title", "summary", "content"],
		"metadata_fields": [
			"doctype",
			"name",
			"sop_no",
			"space",
			"sop_process",
			"status",
			"version",
			"modified",
		],
		"tokenizer": "unicode61 remove_diacritics 2 tokenchars '-_'",
	}

	INDEXABLE_DOCTYPES: ClassVar[dict] = {
		"SOP": {
			"fields": [
				"name",
				"title",
				"summary",
				"content",
				"sop_no",
				"space",
				"sop_process",
				"status",
				"version",
				"modified",
			],
			"filters": {"status": ("!=", "Retired")},
		}
	}

	def get_search_filters(self):
		return {}

	def prepare_document(self, doc):
		prepared = super().prepare_document(doc)
		if not prepared:
			return prepared

		prepared["content"] = plain(prepared.get("content"))

		return prepared


def plain(html):
	if not html:
		return ""

	return SPACE.sub(" ", TAG.sub(" ", html)).strip()


def build():
	search = SOPSQLiteSearch()
	search.build_index()

	return {"index": search.INDEX_NAME, "ready": search.index_exists()}


def readable(rows):
	allowed = []

	for row in rows:
		name = row.get("name") or row.get("id")
		if name and frappe.has_permission("SOP", "read", doc=name):
			allowed.append(row)

	return allowed
