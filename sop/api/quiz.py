# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import json
import random

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from sop.training import OPEN_STATES

DEFAULT_PASS = 80
KINDS = ("One answer", "Several answers")


def can_manage(sop):
	if {"SOP Manager", "SOP Trainer", "System Manager"} & set(frappe.get_roles()):
		return True

	return frappe.has_permission("SOP", "write", doc=sop)


def ensure_manager(sop):
	if not can_manage(sop):
		frappe.throw(_("Only the author, a trainer or a manager can change this quiz."), frappe.PermissionError)


def bank(sop):
	rows = frappe.get_all(
		"SOP Quiz Question",
		filters={"sop": sop},
		fields=["name", "question", "kind", "enabled", "explanation", "sequence", "creation"],
		order_by="sequence asc, creation asc",
		limit_page_length=0,
	)
	if not rows:
		return []

	options = {}
	for row in frappe.get_all(
		"SOP Quiz Option",
		filters={"parenttype": "SOP Quiz Question", "parent": ("in", [row.name for row in rows])},
		fields=["parent", "option", "correct", "idx"],
		order_by="idx asc",
		limit_page_length=0,
	):
		options.setdefault(row.parent, []).append({"option": row.option, "correct": cint(row.get("correct"))})

	return [
		{
			"name": row.name,
			"question": row.question,
			"kind": row.kind or "One answer",
			"enabled": cint(row.enabled),
			"explanation": row.explanation,
			"options": options.get(row.name, []),
		}
		for row in rows
	]


@frappe.whitelist()
def questions(sop):
	ensure_manager(sop)
	return bank(sop)


def clean_options(kind, options):
	if isinstance(options, str):
		options = frappe.parse_json(options)

	rows = [
		{"option": (row.get("option") or "").strip(), "correct": 1 if row.get("correct") else 0}
		for row in options or []
		if (row.get("option") or "").strip()
	]

	if len(rows) < 2:
		frappe.throw(_("Give at least two answers to choose from."))

	right = len([row for row in rows if row["correct"]])
	if not right:
		frappe.throw(_("Mark which answer is correct."))

	if kind == "One answer" and right > 1:
		frappe.throw(_("Only one answer can be correct. Switch to “Several answers” to allow more."))

	return rows


@frappe.whitelist()
def save_question(sop, question, options, kind="One answer", explanation=None, enabled=1, name=None):
	ensure_manager(sop)

	question = (question or "").strip()
	if not question:
		frappe.throw(_("Write the question."))

	kind = kind if kind in KINDS else "One answer"
	rows = clean_options(kind, options)

	if name:
		doc = frappe.get_doc("SOP Quiz Question", name)
		if doc.sop != sop:
			frappe.throw(_("That question belongs to another procedure."))
	else:
		doc = frappe.new_doc("SOP Quiz Question")
		doc.sop = sop
		doc.sequence = frappe.db.count("SOP Quiz Question", {"sop": sop}) + 1

	doc.question = question
	doc.kind = kind
	doc.explanation = (explanation or "").strip()
	doc.enabled = cint(enabled)
	doc.set("options", rows)
	doc.save(ignore_permissions=True)

	return {"name": doc.name}


@frappe.whitelist()
def delete_question(name):
	sop = frappe.db.get_value("SOP Quiz Question", name, "sop")
	if not sop:
		return

	ensure_manager(sop)
	frappe.delete_doc("SOP Quiz Question", name, ignore_permissions=True)


def assessment_task(doc):
	return next((row for row in doc.tasks if row.task_type == "Assessment"), None)


def used(assignment):
	return frappe.db.count("SOP Quiz Attempt", {"assignment": assignment, "status": "Submitted"})


def pass_mark(doc):
	return flt(doc.pass_mark) or DEFAULT_PASS


def own_assignment(name):
	doc = frappe.get_doc("SOP Training Assignment", name)
	if doc.trainee != frappe.session.user:
		frappe.throw(_("Only {0} can take this quiz.").format(doc.trainee), frappe.PermissionError)
	return doc


def summary(doc):
	task = assessment_task(doc)
	live = [row for row in bank(doc.sop) if row["enabled"]]
	attempts = frappe.get_all(
		"SOP Quiz Attempt",
		filters={"assignment": doc.name, "status": "Submitted"},
		fields=["name", "score", "passed", "submitted_at"],
		order_by="submitted_at asc",
		limit_page_length=0,
	)
	limit = cint(doc.max_attempts) or 3
	count = cint(doc.question_count)

	return {
		"available": bool(task and live),
		"open": bool(task and not task.completed and doc.status in OPEN_STATES),
		"questions": min(count, len(live)) if count else len(live),
		"pass_mark": pass_mark(doc),
		"attempts_allowed": limit,
		"attempts_left": max(0, limit - len(attempts)),
		"best": max((flt(row.score) for row in attempts), default=None),
		"attempts": [
			{"score": flt(row.score), "passed": cint(row.passed), "submitted_at": row.submitted_at}
			for row in attempts
		],
	}


@frappe.whitelist()
def status(assignment):
	doc = frappe.get_doc("SOP Training Assignment", assignment)
	doc.check_permission("read")
	return summary(doc)


def paper_for(doc):
	live = [row for row in bank(doc.sop) if row["enabled"]]
	random.shuffle(live)

	count = cint(doc.question_count)
	if count:
		live = live[:count]

	paper = []
	for row in live:
		order = list(range(len(row["options"])))
		random.shuffle(order)
		paper.append({"question": row["name"], "order": order})

	return paper


def shown(paper, questions):
	out = []
	for position, sheet in enumerate(paper):
		row = questions.get(sheet["question"])
		if not row:
			continue
		out.append(
			{
				"key": position,
				"question": row["question"],
				"kind": row["kind"],
				"options": [row["options"][index]["option"] for index in sheet["order"]],
			}
		)
	return out


@frappe.whitelist()
def start(assignment):
	doc = own_assignment(assignment)
	info = summary(doc)

	if not info["available"]:
		frappe.throw(_("There is no quiz for this training."))

	if not info["open"]:
		frappe.throw(_("This quiz is already done."))

	questions = {row["name"]: row for row in bank(doc.sop)}
	current = frappe.db.get_value(
		"SOP Quiz Attempt", {"assignment": doc.name, "status": "Open"}, ["name", "paper"], as_dict=True
	)

	if current:
		paper = json.loads(current.paper or "[]")
		attempt = current.name
	else:
		if not info["attempts_left"]:
			frappe.throw(_("You have used all your attempts."))

		paper = paper_for(doc)
		attempt = (
			frappe.get_doc(
				{
					"doctype": "SOP Quiz Attempt",
					"assignment": doc.name,
					"trainee": doc.trainee,
					"sop": doc.sop,
					"version": doc.version,
					"status": "Open",
					"started_at": now_datetime(),
					"paper": json.dumps(paper),
				}
			)
			.insert(ignore_permissions=True)
			.name
		)

	return {
		"attempt": attempt,
		"pass_mark": info["pass_mark"],
		"attempt_number": info["attempts_allowed"] - info["attempts_left"] + 1,
		"attempts_allowed": info["attempts_allowed"],
		"questions": shown(paper, questions),
	}


def grade(paper, questions, answers):
	review = []
	right = 0

	for position, sheet in enumerate(paper):
		row = questions.get(sheet["question"])
		if not row:
			continue

		correct = {shown_at for shown_at, index in enumerate(sheet["order"]) if row["options"][index]["correct"]}
		chosen = {cint(value) for value in (answers.get(str(position)) or answers.get(position) or [])}
		ok = chosen == correct
		right += 1 if ok else 0

		review.append(
			{
				"key": position,
				"question": row["question"],
				"chosen": sorted(chosen),
				"correct": sorted(correct),
				"ok": ok,
				"explanation": row.get("explanation"),
			}
		)

	total = len(review)
	return (round(right * 100 / total) if total else 0), review


@frappe.whitelist()
def submit(attempt, answers):
	record = frappe.get_doc("SOP Quiz Attempt", attempt)
	doc = own_assignment(record.assignment)

	if record.status != "Open":
		frappe.throw(_("This attempt was already submitted."))

	if isinstance(answers, str):
		answers = frappe.parse_json(answers)

	paper = json.loads(record.paper or "[]")
	questions = {row["name"]: row for row in bank(doc.sop)}
	score, review = grade(paper, questions, answers or {})
	passed = score >= pass_mark(doc)

	record.status = "Submitted"
	record.submitted_at = now_datetime()
	record.score = score
	record.passed = 1 if passed else 0
	record.answers = json.dumps(answers or {})
	record.save(ignore_permissions=True)

	left = max(0, (cint(doc.max_attempts) or 3) - used(doc.name))
	settle(doc, score, passed, left)

	reveal = passed or not left
	if not reveal:
		for row in review:
			row["correct"] = None

	return {
		"score": score,
		"passed": passed,
		"pass_mark": pass_mark(doc),
		"attempts_left": left,
		"review": review,
		"retraining": not passed and not left,
	}


def settle(doc, score, passed, left):
	doc.reload()
	doc.score = score
	doc.assessed_by_quiz = 1

	if passed:
		task = assessment_task(doc)
		if task and not task.completed:
			task.completed = 1
			task.completed_on = now_datetime()
			task.completed_by = doc.trainee
			task.note = _("Passed the quiz with {0}%").format(score)
	elif not left:
		doc.outcome = "Not Competent"
		doc.remarks = _("Did not reach the pass mark in {0} quiz attempts").format(cint(doc.max_attempts) or 3)

	doc.save(ignore_permissions=True)
