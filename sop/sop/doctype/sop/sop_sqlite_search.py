# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import re
from html import unescape
from typing import ClassVar

import frappe
from frappe.search.sqlite_search import SQLiteSearch

TAG = re.compile(r"<[^>]+>")
LOOSE_SIMILARITY = 0.5
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

	def find(self, words, phrases=(), excluded=(), filters=None):
		self.raise_if_not_indexed()

		corrected, corrections = self._expand_query_with_corrections(" ".join(words)) if words else ("", None)
		names = self.matching(corrected.split(), phrases, excluded, filters)

		if not names and words:
			loose = {}
			for word in words:
				suggestions = self._find_similar_words(word, min_similarity=LOOSE_SIMILARITY)
				if suggestions and suggestions[0] != word.lower():
					loose[word] = suggestions[0]
			if loose:
				names = self.matching([loose.get(word, word) for word in words], phrases, excluded, filters)
				corrections = loose if names else corrections

		return names, corrections

	def matching(self, words, phrases=(), excluded=(), filters=None):
		terms = [term(word, prefix=True) for word in words] + [term(phrase) for phrase in phrases]
		if not terms:
			return []

		fts = " ".join(terms)
		if excluded:
			fts = f"{fts} NOT ({' OR '.join(term(word, prefix=True) for word in excluded)})"

		rows = self._execute_search_query(fts, False, filters or {})
		results = self._process_search_results(rows, " ".join([*words, *phrases]))

		return [row.get("name") or row.get("id") for row in results]

	def prepare_document(self, doc):
		prepared = super().prepare_document(doc)
		if not prepared:
			return prepared

		prepared["content"] = plain(prepared.get("content"))

		return prepared


def term(text, prefix=False):
	quoted = '"' + text.replace('"', '""') + '"'
	return f"{quoted}*" if prefix and len(text) > 1 else quoted


def plain(html):
	if not html:
		return ""

	return SPACE.sub(" ", unescape(TAG.sub(" ", html))).strip()


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
