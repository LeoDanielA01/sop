# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import add_days, add_months, cint, getdate, nowdate

PERIODS = {"Daily": (1, 0), "Weekly": (7, 0), "Monthly": (0, 1), "Quarterly": (0, 3), "Yearly": (0, 12)}


def level_of(score):
	if not score:
		return ""
	if score <= 4:
		return "Low"
	if score <= 9:
		return "Medium"
	if score <= 16:
		return "High"
	return "Very High"


def next_due(period, start=None):
	days, months = PERIODS.get(period, (0, 0))
	start = getdate(start or nowdate())
	return add_months(start, months) if months else add_days(start, days)


class SOPRiskAssessment(Document):
	def validate(self):
		today = getdate(nowdate())
		highest = 0
		for row in self.hazards:
			row.risk_score = cint(row.likelihood) * cint(row.severity)
			row.risk_level = level_of(row.risk_score)
			row.residual_score = cint(row.residual_likelihood) * cint(row.residual_severity)
			row.residual_level = level_of(row.residual_score)
			if row.check_every and not row.next_check:
				row.next_check = next_due(row.check_every, row.last_checked)
			highest = max(highest, row.risk_score)

		self.highest_risk = highest
		self.highest_level = level_of(highest)
		self.open_actions = sum(1 for row in self.hazards if row.action_status == "Open")
		self.checks_due = sum(
			1 for row in self.hazards if row.next_check and getdate(row.next_check) <= today
		)
