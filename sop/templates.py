# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe import _

MANUFACTURING = [
	(
		"Materials",
		[
			"Receiving and incoming inspection",
			"Storage and handling",
			"Weighing and dispensing",
			"Material issue to the line",
		],
	),
	(
		"Production",
		[
			"Line clearance and setup",
			"Batch start and documentation",
			"Mixing and blending",
			"Granulation and drying",
			"Forming, compression or moulding",
			"Assembly",
			"In-process adjustment and rework",
		],
	),
	(
		"Packing and dispatch",
		[
			"Primary packing",
			"Secondary packing and cartoning",
			"Labelling, coding and serialisation",
			"Palletising and loading",
		],
	),
	(
		"Quality",
		[
			"In-process checks",
			"Sampling and testing",
			"Batch record review and release",
			"Non-conformance and deviation",
			"Corrective and preventive action",
			"Customer complaint handling",
		],
	),
	(
		"Equipment",
		[
			"Startup and shutdown",
			"Changeover",
			"Cleaning and sanitation",
			"Preventive maintenance",
			"Calibration",
			"Breakdown response",
		],
	),
	(
		"Safety and environment",
		[
			"PPE and hazard control",
			"Lockout and tagout",
			"Chemical handling and spills",
			"Waste segregation and disposal",
			"Emergency response",
		],
	),
	(
		"People",
		[
			"Induction and on-the-job training",
			"Shift handover",
			"Hygiene and gowning",
		],
	),
]

TEMPLATES = {
	"manufacturing": {
		"title": "Manufacturing",
		"description": "Materials, production, packing, quality, equipment, safety and people — 7 groups and 35 processes.",
		"processes": MANUFACTURING,
	}
}


def apply_template(space, template, with_drafts=0):
	definition = TEMPLATES.get(template)
	if not definition:
		frappe.throw(_("{0} is not a template.").format(template))

	if not frappe.db.exists("SOP Space", space):
		frappe.throw(_("{0} is not a space.").format(space))

	processes = 0
	drafts = 0

	for index, (group, steps) in enumerate(definition["processes"], start=1):
		parent = ensure_process(space, group, None, index * 10)
		processes += 1

		for position, step in enumerate(steps, start=1):
			child = ensure_process(space, step, parent, position * 10)
			processes += 1

			if with_drafts and ensure_draft(space, child, step):
				drafts += 1

	return {"processes": processes, "drafts": drafts}


def ensure_process(space, title, parent, sequence):
	existing = frappe.db.get_value(
		"SOP Process", {"space": space, "title": title, "parent_process": parent}, "name"
	)
	if existing:
		return existing

	return (
		frappe.get_doc(
			{
				"doctype": "SOP Process",
				"title": title,
				"space": space,
				"parent_process": parent,
				"sequence": sequence,
			}
		)
		.insert()
		.name
	)


def ensure_draft(space, process, title):
	if frappe.db.exists("SOP", {"space": space, "process": process}):
		return None

	doc = frappe.get_doc(
		{
			"doctype": "SOP",
			"title": title,
			"space": space,
			"process": process,
			"status": "Draft",
			"process_owner": frappe.session.user,
			"summary": _("Outline to be written by whoever owns {0}.").format(title.lower()),
			"content": skeleton(title),
		}
	).insert()

	return doc.name


def skeleton(title):
	return f"""<h2>Purpose</h2>
<p>Why {title.lower()} is carried out, and the result it has to produce.</p>
<h2>Scope</h2>
<p>Which lines, shifts, products or materials this covers — and what it does not.</p>
<h2>Responsibilities</h2>
<ul>
<li>Operator — carries out the steps and records what happened.</li>
<li>Line supervisor — confirms the work was done as written.</li>
<li>Quality — checks the record and releases the batch.</li>
</ul>
<h2>Procedure</h2>
<div data-sop="step"><p><strong>Step 1</strong> — what is done, in the order it is done.</p>
<p data-sop="step-meta">Responsible: role · Records: document</p></div>
<div data-sop="callout" data-tone="warning"><p>The hazard or the mistake that matters most here.</p></div>
<h2>Records</h2>
<p>The form, log or system entry this procedure produces, and where it is kept.</p>
<h2>References</h2>
<p>Work instructions, drawings, specifications and standards this depends on.</p>"""


def install_manufacturing(space_code="MFG", with_drafts=0):
	space = frappe.db.get_value("SOP Space", {"space_code": space_code}, "name")

	if not space:
		space = (
			frappe.get_doc(
				{
					"doctype": "SOP Space",
					"title": "Manufacturing",
					"space_code": space_code,
					"visibility": "Public",
					"review_interval_months": 12,
					"description": "How the plant makes, checks and packs what it ships.",
				}
			)
			.insert()
			.name
		)

	result = apply_template(space, "manufacturing", with_drafts=with_drafts)
	frappe.db.commit()

	return dict(result, space=space)
