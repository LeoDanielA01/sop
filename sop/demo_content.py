# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

from sop.demo_guide import GUIDE_PROCEDURES, callout, step
from sop.patches.migrate_to_resources import CHEMICAL_TYPE, PPE_TYPE

DEMO_CODES = ("GUIDE", "PLANT")

PEOPLE = {
	"manager": {"email": "sara.james@example.com", "first": "Sara", "last": "James", "roles": ["SOP Manager", "SOP Approver"]},
	"author": {"email": "dan.walsh@example.com", "first": "Dan", "last": "Walsh", "roles": ["SOP Author"]},
	"trainer": {"email": "leila.k@example.com", "first": "Leila", "last": "Karimian", "roles": ["SOP Approver", "SOP Trainer"]},
	"reviewer": {"email": "priya.nair@example.com", "first": "Priya", "last": "Nair", "roles": ["SOP Reviewer"]},
	"reader": {"email": "tom.r@example.com", "first": "Tom", "last": "Rivera", "roles": ["SOP Reader"]},
	"operator": {"email": "maria.lopez@example.com", "first": "Maria", "last": "Lopez", "roles": ["SOP Reader"]},
	"storekeeper": {"email": "ken.ito@example.com", "first": "Ken", "last": "Ito", "roles": ["SOP Reader"]},
}

TEAMS = [
	{
		"name": "All Staff",
		"description": "Everyone who uses the app. Owns the guide space, so every new procedure there is read by all.",
		"members": [
			("manager", "Approver"),
			("trainer", "Approver"),
			("reviewer", "Reviewer"),
			("author", "Author"),
			("reader", "Reader"),
			("operator", "Reader"),
			("storekeeper", "Reader"),
		],
	},
	{
		"name": "Production",
		"description": "Operators on the line plus the people who write and approve their procedures.",
		"members": [
			("manager", "Approver"),
			("reviewer", "Reviewer"),
			("author", "Author"),
			("reader", "Reader"),
			("operator", "Reader"),
		],
	},
	{
		"name": "Quality",
		"description": "Reviews and signs off every controlled document.",
		"members": [("manager", "Approver"), ("trainer", "Approver"), ("reviewer", "Reviewer")],
	},
	{
		"name": "Warehouse",
		"description": "Goods in, stores and dispensing.",
		"members": [("manager", "Approver"), ("author", "Author"), ("storekeeper", "Reader")],
	},
]

SPACES = [
	{
		"code": "GUIDE",
		"title": "SOP App Guide",
		"team": "All Staff",
		"description": "How to set up and run this app: users, spaces, teams, writing, approval, training, safety and records.",
	},
	{
		"code": "PLANT",
		"title": "Demo Plant",
		"team": "Production",
		"description": "A small sample plant with real procedures, so every screen in the guide has something to show.",
	},
]

PROCESSES = {
	"GUIDE": [
		("Getting started", ["Users & roles", "Spaces & teams", "Settings"]),
		("Writing procedures", ["Drafting", "Importing"]),
		("Review & publishing", ["Approval", "Publishing"]),
		("Training", ["Training rules", "Sessions & quizzes", "Training records"]),
		("Safety & records", ["Risk assessments", "Logs & signs", "Resources"]),
		("Running the app", ["Insights", "Collaboration"]),
	],
	"PLANT": [
		("Production", ["Weighing", "Mixing", "Cleaning"]),
		("Warehouse", ["Receiving", "Dispensing"]),
		("Equipment", ["Extraction"]),
	],
}

ROOM_TYPE = {
	"type_name": "Room",
	"icon": "lucide-door-open",
	"description": "Production rooms. Cleaning logs set the room status shown on procedures.",
	"is_tree": 0,
	"show_in_procedure": 1,
	"can_be_issued": 0,
	"attributes": [{"label": "Area", "fieldtype": "Data", "show_in_procedure": 1}],
}

EQUIPMENT_TYPE = {
	"type_name": "Equipment",
	"icon": "lucide-wrench",
	"description": "Machines and fixed equipment with a service or calibration date.",
	"is_tree": 0,
	"show_in_procedure": 1,
	"can_be_issued": 0,
	"review_label": "Next service",
	"attributes": [{"label": "Model", "fieldtype": "Data", "show_in_procedure": 1}],
}

RESOURCE_TYPES = [PPE_TYPE, CHEMICAL_TYPE, ROOM_TYPE, EQUIPMENT_TYPE]


def ppe(name, parent, is_group, standard, consumable, description):
	return {
		"resource_name": name,
		"resource_type": "PPE",
		"parent_sop_resource": parent,
		"is_group": is_group,
		"is_consumable": consumable,
		"description": description,
		"values": [{"attribute": "Standard", "value": standard}],
	}


def chemical(name, cas, signal, hazard, precautions, exposure, first_aid, storage, required, check_in):
	return {
		"resource_name": name,
		"resource_type": "Chemical",
		"check_in": check_in,
		"values": [
			{"attribute": "CAS Number", "value": cas},
			{"attribute": "Signal Word", "value": signal},
			{"attribute": "Hazard Class", "value": hazard},
			{"attribute": "Precautions", "value": precautions},
			{"attribute": "Exposure Risks", "value": exposure},
			{"attribute": "First Aid", "value": first_aid},
			{"attribute": "Storage And Disposal", "value": storage},
		],
		"requires": [{"resource": item} for item in required],
	}


RESOURCES = [
	ppe("Respiratory protection", None, 1, "", 0, "Anything worn to keep fumes, vapours and dust out of the lungs."),
	ppe("FFP3 dust mask", "Respiratory protection", 0, "EN 149", 1, "Single use. For powders in the weighing room."),
	ppe("Half-face respirator", "Respiratory protection", 1, "EN 140", 0, "Kept by one person. Check the seal before every use."),
	ppe("ABEK1 filter", "Half-face respirator", 0, "EN 14387", 1, "Swap after eight hours of use, or sooner if you smell anything."),
	ppe("Eye protection", None, 1, "", 0, "Goggles and face shields."),
	ppe("Chemical splash goggles", "Eye protection", 0, "EN 166", 0, "Indirect vents. Not safety glasses."),
	ppe("Hand protection", None, 1, "", 0, "Gloves, chosen for the job."),
	ppe("Nitrile gloves", "Hand protection", 0, "EN 374", 1, "Single use. Change when torn or splashed."),
	ppe("Body protection", None, 1, "", 0, "Coats, aprons and suits."),
	ppe("Clean room coat", "Body protection", 0, "EN 13034", 0, "Production areas only. Never worn outside."),
	chemical(
		"Isopropyl alcohol",
		"67-63-0",
		"Danger",
		"Flammable",
		"No flames or sparks. Keep containers closed. Earth the drum before opening.",
		"Highly flammable vapour. Causes eye irritation and drowsiness.",
		"Move to fresh air. Rinse eyes with water for 15 minutes.",
		"Flammables cabinet, below 25 °C. Empty drums back to the supplier.",
		["Chemical splash goggles", "Nitrile gloves"],
		180,
	),
	chemical(
		"Sodium hypochlorite 12%",
		"7681-52-9",
		"Danger",
		"Corrosive",
		"Never mix with acids: it releases chlorine gas.",
		"Burns skin and eyes. Chlorine gas if it meets acid.",
		"Rinse with water for 15 minutes. Move to fresh air if gas is released.",
		"Cool, dark, away from acids.",
		["Chemical splash goggles", "Nitrile gloves"],
		-5,
	),
	{"resource_name": "Weighing room", "resource_type": "Room", "values": [{"attribute": "Area", "value": "Production, ground floor"}]},
	{"resource_name": "Mixing room", "resource_type": "Room", "values": [{"attribute": "Area", "value": "Production, ground floor"}]},
	{"resource_name": "Packing room", "resource_type": "Room", "values": [{"attribute": "Area", "value": "Production, first floor"}]},
	{
		"resource_name": "Planetary mixer PM-40",
		"resource_type": "Equipment",
		"check_in": 40,
		"values": [{"attribute": "Model", "value": "PM-40, 40 L bowl"}],
		"description": "Bowl, beater and guard are washed after every batch.",
	},
	{
		"resource_name": "Extraction unit EX-2",
		"resource_type": "Equipment",
		"check_in": 12,
		"values": [{"attribute": "Model", "value": "EX-2 with F9 bag filter"}],
		"description": "Serves the weighing and mixing rooms. Filter changed monthly.",
	},
	{
		"resource_name": "Precision balance B-1",
		"resource_type": "Equipment",
		"check_in": -2,
		"values": [{"attribute": "Model", "value": "0.01 g readability, 6 kg"}],
		"description": "Calibrated every six months. Daily check with the 1 kg weight.",
	},
]


PLANT_PROCEDURES = [
	{
		"slug": "weigh",
		"title": "Weigh raw materials for a batch",
		"space": "PLANT",
		"process": "Weighing",
		"summary": "Weigh every ingredient on the batch sheet to tolerance, label it and stage it for mixing.",
		"document_type": "Process SOP",
		"risk_level": "High",
		"state": "effective",
		"effective_since": -60,
		"signed_by": ["reader", "operator"],
		"tags": ["production", "weighing"],
		"content": "".join(
			[
				"<h2>Purpose</h2><p>Every batch starts with the right amount of the right material. This procedure makes the weighing traceable from the batch sheet to the labelled container.</p>",
				"<h2>Scope</h2><p>All raw materials weighed in the {res:Weighing room} for production batches. Mixing is {sop:mix}.</p>",
				callout("critical", ["Wear the {res:FFP3 dust mask} and {res:Nitrile gloves} for every powder.", "Never weigh two materials on the balance at the same time."], "Stop and check"),
				"<h2>Step by step</h2>",
				step("PREPARE", 1, "Check the balance", "A balance that is off ruins every batch weighed on it.", ["Place the 1 kg check weight on {res:Precision balance B-1}.", "The reading must be 1000.0 g ± 0.5 g.", "Write the reading on the batch sheet."], "Weighing room · Balance B-1", "If the reading is outside tolerance, stop and tell the shift lead. Do not weigh."),
				step("PREPARE", 1, "Collect the materials", "", ["Pick each material listed on the batch sheet.", "Check the lot number against the sheet."], "Weighing room · Staging rack"),
				step("WEIGH", 2, "Weigh each material", "Weigh into a clean, labelled container.", ["Tare the empty container.", "Add material until the target weight is reached within ± 0.5 g.", "Record the actual weight and lot number."], "Weighing room · Balance B-1"),
				step("WEIGH", 2, "Label the container", "", ["Batch number, material, lot, weight, your initials."], "Weighing room"),
				step("HAND OVER", 3, "Stage for mixing", "", ["Place containers on the mixing trolley in the order on the batch sheet.", "Sign the batch sheet."], "Mixing room · Trolley"),
				"<h2>Records</h2><p>The signed batch sheet with every weight and lot number.</p>",
			]
		),
	},
	{
		"slug": "mix",
		"title": "Mix a batch in the planetary mixer",
		"space": "PLANT",
		"process": "Mixing",
		"summary": "Load, mix and discharge a batch in the PM-40 mixer.",
		"document_type": "Process SOP",
		"state": "effective",
		"effective_since": -50,
		"signed_by": ["operator"],
		"tags": ["production", "mixing"],
		"content": "".join(
			[
				"<h2>Purpose</h2><p>A uniform mix every time, with the guard closed while the beater turns.</p>",
				"<h2>Scope</h2><p>Batches mixed on {res:Planetary mixer PM-40} in the {res:Mixing room}. Materials come weighed from {sop:weigh}.</p>",
				callout("critical", ["Never open the guard while the beater is turning. Wait for it to stop completely."], "Moving parts"),
				"<h2>Step by step</h2>",
				step("LOAD", 1, "Check the mixer is clean", "", ["Bowl, beater and guard visibly clean.", "Last cleaning log entry signed."], "Mixing room · PM-40"),
				step("LOAD", 1, "Load the materials", "Load in the order on the batch sheet.", ["Liquids first, then powders.", "Scrape each container."], "Mixing room · PM-40"),
				step("MIX", 2, "Mix", "", ["Close the guard.", "Speed 1 for 2 minutes, then speed 2 for 8 minutes."], "Mixing room · PM-40"),
				step("DISCHARGE", 3, "Discharge and record", "", ["Tip the bowl into the labelled tub.", "Record start and end time on the batch sheet."], "Mixing room"),
			]
		),
	},
	{
		"slug": "clean",
		"title": "Minor cleaning of a production room",
		"space": "PLANT",
		"process": "Cleaning",
		"summary": "The clean between products or at the end of the day, and the log that proves it.",
		"document_type": "Process SOP",
		"state": "effective",
		"effective_since": -90,
		"signed_by": ["reader", "operator"],
		"tags": ["cleaning"],
		"content": "".join(
			[
				"<h2>Purpose</h2><p>No residue from one product reaches the next. Every clean is logged so the room status is always known.</p>",
				"<h2>Scope</h2><p>The {res:Weighing room}, {res:Mixing room} and {res:Packing room}. A deep clean is a major clean and is out of scope.</p>",
				callout("warning", ["Use {res:Sodium hypochlorite 12%} only diluted 1:50. Never mix it with any acid cleaner."], "Chemical"),
				"<h2>Step by step</h2>",
				step("CLEAR", 1, "Clear the room", "", ["Remove all product, labels and paperwork from the last batch."], "Room being cleaned"),
				step("CLEAN", 2, "Wipe all surfaces", "", ["Top to bottom: shelves, benches, equipment outsides, then the floor.", "Use the diluted cleaner, then clean water."], "Room being cleaned"),
				step("CHECK", 3, "Check and log", "The log entry sets the room status everyone else sees.", ["Walk the room with the checker.", "Open the Log panel on this procedure and add a Cleaning entry: room, Minor, reason, product before."], "Room being cleaned"),
				"<h2>Records</h2><p>The cleaning log entry. It updates the room status shown on every procedure that uses the room.</p>",
			]
		),
	},
	{
		"slug": "receive",
		"title": "Receive raw materials",
		"space": "PLANT",
		"process": "Receiving",
		"summary": "From the delivery van to the quarantine rack, without losing the paperwork.",
		"document_type": "Process SOP",
		"author": "author",
		"state": "effective",
		"effective_since": -70,
		"signed_by": ["storekeeper"],
		"tags": ["warehouse"],
		"content": "".join(
			[
				"<h2>Purpose</h2><p>Every delivery is checked, recorded and kept apart until quality releases it.</p>",
				"<h2>Step by step</h2>",
				step("CHECK", 1, "Check the delivery", "", ["Count the pallets against the delivery note.", "Look for damage before signing."], "Dock 1"),
				step("CHECK", 1, "Check the labels", "", ["Material, lot and expiry on every pack.", "Certificate of analysis attached."], "Dock 1"),
				step("BOOK", 2, "Book it in", "", ["Create the purchase receipt.", "Print quarantine labels."], "Goods-in office"),
				step("STORE", 3, "Move to quarantine", "", ["Put away on Rack Q. Flammables go to the flammables cabinet — see {sop:ipa}."], "Warehouse · Rack Q"),
			]
		),
	},
	{
		"slug": "ipa",
		"title": "Dispense isopropyl alcohol",
		"space": "PLANT",
		"process": "Dispensing",
		"summary": "Decanting IPA from the drum into labelled wash bottles.",
		"document_type": "Process SOP",
		"risk_level": "High",
		"state": "effective",
		"effective_since": -30,
		"signed_by": ["storekeeper"],
		"tags": ["chemicals", "warehouse"],
		"content": "".join(
			[
				"<h2>Purpose</h2><p>Gets {res:Isopropyl alcohol} into wash bottles without spills or vapour build-up.</p>",
				callout("critical", ["No hot work or naked flame within 10 m.", "Earth the drum before you open it."], "Fire risk"),
				"<h2>Step by step</h2>",
				step("PREPARE", 1, "Put on PPE", "", ["{res:Chemical splash goggles}", "{res:Nitrile gloves}"], "Flammables store"),
				step("DISPENSE", 2, "Earth the drum and fill", "", ["Clip the earth lead to the drum.", "Fill each bottle to the line, no more."], "Flammables store"),
				step("FINISH", 3, "Label and close", "", ["Label every bottle.", "Close the drum and return it to the cabinet."], "Flammables store"),
			]
		),
	},
	{
		"slug": "filter",
		"title": "Change the extraction filter",
		"space": "PLANT",
		"process": "Extraction",
		"summary": "Monthly bag-filter change on extraction unit EX-2, with the unit isolated.",
		"document_type": "Equipment SOP",
		"risk_level": "High",
		"state": "effective",
		"effective_since": -80,
		"signed_by": ["operator"],
		"tags": ["equipment", "maintenance"],
		"content": "".join(
			[
				"<h2>Purpose</h2><p>Keeps the air in the weighing and mixing rooms clean. A blocked filter means dust in the room.</p>",
				"<h2>Scope</h2><p>{res:Extraction unit EX-2}. Print the machine sign for this procedure and fix it to the unit.</p>",
				callout("critical", ["Isolate and lock off EX-2 before opening the filter housing.", "Wear the {res:FFP3 dust mask} — the old filter is full of fine powder."], "Before you open the housing"),
				callout("warning", ["Bag the old filter inside the housing. Never shake it out."], "Dust"),
				"<h2>Step by step</h2>",
				step("ISOLATE", 1, "Isolate the unit", "", ["Switch off at the panel.", "Fit your padlock and tag."], "Plant room · EX-2 panel"),
				step("CHANGE", 2, "Remove the old filter", "", ["Open the housing.", "Pull a bag over the old filter and seal it."], "Plant room · EX-2"),
				step("CHANGE", 2, "Fit the new filter", "", ["Check the seal is seated all round.", "Close the housing."], "Plant room · EX-2"),
				step("RESTART", 3, "Restart and log", "", ["Remove your lock.", "Run for 5 minutes and check the pressure gauge is in the green.", "Add a Service entry in the Log panel: Filter change."], "Plant room · EX-2"),
			]
		),
	},
]

PROCEDURES = GUIDE_PROCEDURES + PLANT_PROCEDURES

REVISION = {
	"slug": "weigh",
	"changes": [
		("within ± 0.5 g", "within ± 0.2 g"),
		("<li><p>Write the reading on the batch sheet.</p></li>", "<li><p>Write the reading on the batch sheet.</p></li><li><p>Check the level bubble is centred.</p></li>"),
	],
	"change_summary": "Tighter weighing tolerance (± 0.2 g) after the audit, and a level check before weighing.",
	"approval_note": "Matches the new specification.",
}

RULES = [
	{"applies_to": "Team", "team": "All Staff", "scope": "Space", "space_code": "GUIDE", "method": "Read & Understand", "due_days": 14, "refresher_months": 12},
	{"applies_to": "Team", "team": "Production", "scope": "Space", "space_code": "PLANT", "method": "Assessment", "due_days": 7, "requires_assessment": 1, "pass_mark": 80, "max_attempts": 3, "question_count": 3, "refresher_months": 12},
	{"applies_to": "Team", "team": "Warehouse", "scope": "Procedure", "slug": "ipa", "method": "On the Job", "due_days": 5, "refresher_months": 6},
	{"applies_to": "Role", "role": "SOP Author", "scope": "Procedure", "slug": "write", "method": "Read & Understand", "due_days": 10},
]

TRAINING = [
	("roles", "reader", "Completed"),
	("roles", "operator", "Overdue"),
	("roles", "storekeeper", "In Progress"),
	("write", "author", "Completed"),
	("write", "reviewer", "Assigned"),
	("blocks", "author", "Completed"),
	("blocks", "reader", "Overdue"),
	("rules", "manager", "Completed"),
	("rules", "reviewer", "In Progress"),
	("risk", "operator", "Completed"),
	("risk", "storekeeper", "Overdue"),
	("logs", "operator", "Completed"),
	("logs", "reader", "Completed"),
	("signs", "storekeeper", "Assigned"),
	("insights", "manager", "Completed"),
	("insights", "trainer", "Overdue"),
]

QUIZ = {
	"proficiency_slug": "clean",
	"questions": {
		"weigh": [
			{"question": "The check weight reads 1001.2 g. What do you do?", "options": ["Weigh anyway, it is close enough", "Stop and tell the shift lead", "Tare the balance and carry on"], "correct": [1], "explanation": "Outside ± 0.5 g means the balance cannot be trusted. Stop before weighing."},
			{"question": "Which PPE is needed for weighing powders?", "options": ["FFP3 dust mask", "Nitrile gloves", "Welding visor"], "correct": [0, 1]},
			{"question": "What goes on the container label?", "options": ["Batch number, material, lot, weight, initials", "Material name only", "The time of weighing"], "correct": [0]},
			{"question": "Two materials are needed from the same rack. Can you weigh them together?", "options": ["Yes, to save time", "No, one material on the balance at a time"], "correct": [1]},
		],
		"clean": [
			{"question": "How is the hypochlorite cleaner diluted?", "options": ["1:50 with water", "Used neat", "Mixed with the acid cleaner"], "correct": [0], "explanation": "Never with acid: it releases chlorine gas."},
			{"question": "What sets the room status after a clean?", "options": ["The cleaning log entry", "A note on the door", "Nothing, it is automatic"], "correct": [0]},
			{"question": "In what order are surfaces wiped?", "options": ["Floor first", "Top to bottom, floor last", "Any order"], "correct": [1]},
		],
	},
	"attempts": [
		("weigh", "operator", [True]),
		("weigh", "reader", [False, True]),
		("clean", "reader", [False]),
	],
}

SESSIONS = [
	{
		"title": "Weighing room induction",
		"in_days": -6,
		"time": "09:00:00",
		"location": "Weighing room",
		"method": "On the Job",
		"procedures": ["weigh", "mix"],
		"attendees": ["operator", "reader", "storekeeper"],
		"notes": "Walk the room, then each person weighs a dummy batch under supervision.",
		"outcomes": [
			("operator", "Competent", "Weighed the dummy batch without help."),
			("reader", "Needs More Practice", "Mixed up the tare order twice. Repeat next week."),
			("storekeeper", "Absent", ""),
		],
	},
	{
		"title": "Extraction filter change — hands-on",
		"in_days": 5,
		"time": "14:00:00",
		"location": "Plant room",
		"method": "On the Job",
		"procedures": ["filter"],
		"attendees": ["operator", "author"],
		"notes": "Bring your own padlock. The unit is isolated before we start.",
	},
	{
		"title": "Getting started with the SOP app",
		"in_days": 2,
		"time": "10:30:00",
		"location": "Training room",
		"method": "Classroom",
		"procedures": ["write", "review", "rules"],
		"attendees": ["reviewer", "storekeeper"],
		"notes": "Laptops needed. We write a short procedure together and send it for review.",
	},
]

RISKS = [
	{
		"ra_no": "RA-DMO-001",
		"title": "Risk assessment: weighing and mixing",
		"space": "PLANT",
		"status": "Approved",
		"assessed_by": "manager",
		"applies_to": ["weigh", "mix"],
		"scoring_note": "Likelihood and severity 1–5. Score = L × S. 1–4 Low, 5–9 Medium, 10–16 High, 20+ Very High.",
		"hazards": [
			{"hazard_id": "H1", "task": "Weighing powders", "hazard": "Inhaling fine powder", "consequence": "Respiratory irritation", "existing_controls": "Extraction EX-2, FFP3 mask", "likelihood": 3, "severity": 3, "additional_actions": "Fit a local extraction hood over balance B-1", "action_status": "Open", "owner": "manager", "due_in": -3, "residual_likelihood": 1, "residual_severity": 3},
			{"hazard_id": "H2", "task": "Weighing", "hazard": "Wrong amount weighed", "consequence": "Batch out of specification", "existing_controls": "Daily balance check, second-person check", "likelihood": 2, "severity": 4, "additional_actions": "", "action_status": "Not needed", "residual_likelihood": 1, "residual_severity": 4, "recurring_check": "Check balance B-1 with the 1 kg weight", "check_every": "Daily", "checked_in": -1},
			{"hazard_id": "H3", "task": "Mixing", "hazard": "Hand caught by the beater", "consequence": "Crush injury", "existing_controls": "Interlocked guard", "likelihood": 2, "severity": 5, "additional_actions": "Test the guard interlock", "action_status": "Not needed", "residual_likelihood": 1, "residual_severity": 5, "recurring_check": "Test the PM-40 guard interlock", "check_every": "Weekly", "checked_in": 3},
			{"hazard_id": "H4", "task": "Moving tubs", "hazard": "Lifting heavy tubs", "consequence": "Back injury", "existing_controls": "Trolley, two-person lift over 20 kg", "likelihood": 3, "severity": 2, "additional_actions": "Manual handling refresher for operators", "action_status": "Done", "owner": "trainer", "due_in": -20, "residual_likelihood": 2, "residual_severity": 2},
		],
	},
	{
		"ra_no": "RA-DMO-002",
		"title": "Risk assessment: extraction filter change",
		"space": "PLANT",
		"status": "Approved",
		"assessed_by": "trainer",
		"applies_to": ["filter"],
		"hazards": [
			{"hazard_id": "E1", "task": "Opening the housing", "hazard": "Unit starts while hands are inside", "consequence": "Serious injury", "existing_controls": "Lock-off and tag", "likelihood": 1, "severity": 5, "additional_actions": "", "action_status": "Not needed", "residual_likelihood": 1, "residual_severity": 5},
			{"hazard_id": "E2", "task": "Removing the filter", "hazard": "Dust released from the old filter", "consequence": "Inhalation, room contamination", "existing_controls": "Bag in place, FFP3 mask", "likelihood": 3, "severity": 3, "additional_actions": "Buy a bag-in/bag-out housing", "action_status": "Open", "owner": "author", "due_in": 21, "residual_likelihood": 2, "residual_severity": 2},
			{"hazard_id": "E3", "task": "Running the unit", "hazard": "Blocked filter not noticed", "consequence": "Dust in production rooms", "existing_controls": "Pressure gauge on the unit", "likelihood": 3, "severity": 3, "additional_actions": "", "action_status": "Not needed", "residual_likelihood": 2, "residual_severity": 3, "recurring_check": "Read the EX-2 pressure gauge", "check_every": "Weekly", "checked_in": -2},
		],
		"complete_checks": ["E3"],
	},
	{
		"ra_no": "RA-DMO-003",
		"title": "Risk assessment: cleaning and dispensing chemicals",
		"space": "PLANT",
		"status": "Draft",
		"assessed_by": "reviewer",
		"applies_to": ["clean", "ipa"],
		"hazards": [
			{"hazard_id": "C1", "task": "Diluting hypochlorite", "hazard": "Splash to the eyes", "consequence": "Eye burn", "existing_controls": "Splash goggles", "likelihood": 2, "severity": 4, "additional_actions": "Fit an eyewash station by the sink", "action_status": "Open", "owner": "manager", "due_in": 14, "residual_likelihood": 1, "residual_severity": 4},
			{"hazard_id": "C2", "task": "Dispensing IPA", "hazard": "Vapour ignition", "consequence": "Fire", "existing_controls": "Earthing, no hot work within 10 m", "likelihood": 2, "severity": 5, "additional_actions": "", "action_status": "Not needed", "residual_likelihood": 1, "residual_severity": 5, "recurring_check": "Test the drum earth lead", "check_every": "Monthly", "checked_in": 10},
		],
	},
]

LOGS = [
	{"slug": "clean", "by": "operator", "checker": "reader", "days_ago": 6, "time": "16:30:00", "log_type": "Cleaning", "location": "Weighing room", "cleaning_type": "Minor", "reason": "Last batch of the day", "product_before": "Batch 2611", "room_status": "Minor cleaned"},
	{"slug": "clean", "by": "reader", "checker": "operator", "days_ago": 4, "time": "11:15:00", "log_type": "Cleaning", "location": "Mixing room", "cleaning_type": "Minor", "reason": "SKU change", "product_before": "Batch 2614", "room_status": "Minor cleaned"},
	{"slug": "clean", "by": "operator", "checker": "manager", "days_ago": 1, "time": "17:00:00", "log_type": "Cleaning", "location": "Weighing room", "cleaning_type": "Minor", "reason": "Last batch of the day", "product_before": "Batch 2620", "room_status": "Minor cleaned"},
	{"slug": "clean", "by": "reader", "days_ago": 0, "time": "07:45:00", "log_type": "Cleaning", "location": "Packing room", "cleaning_type": "Minor", "reason": "Not clean on arrival", "room_status": "Production", "notes": "Found labels from yesterday on the bench. Cleaned and released."},
	{"slug": "filter", "by": "operator", "checker": "author", "days_ago": 28, "time": "13:00:00", "log_type": "Service", "service_type": "Filter change", "location_text": "Extraction unit EX-2", "notes": "Old filter heavily loaded. Gauge back in the green after the change."},
	{"slug": "filter", "by": "author", "days_ago": 9, "time": "10:00:00", "log_type": "Service", "service_type": "Inspection", "location_text": "Extraction unit EX-2", "notes": "Housing seal worn on one side. New seal ordered."},
]

REVIEW_COMMENTS = [
	("approve", "reviewer", "Say what happens when two approvers disagree — does the first decision stand?", "Approve, or request changes", False),
	("approve", "trainer", "Add a line on approving on behalf of someone who is away. People will ask.", "", False),
	("approve", "manager", "Typo fixed in step 3, thanks.", "", True),
]

CLARITY = [
	("weigh", "operator", 1, ""),
	("weigh", "reader", 0, "Step 3 says ± 0.2 g but the batch sheet still prints ± 0.5 g."),
	("clean", "operator", 1, ""),
	("clean", "storekeeper", 0, "Does the Packing room count as production for the reason list?"),
	("blocks", "reader", 0, "The difference between a live value and a check is not clear to me."),
	("rules", "storekeeper", 1, ""),
]

CHAT = {
	"room": [
		("weigh", "author", "Heads-up: the new version tightens the balance check to ± 0.2 g. A reading of 1000.3 g is now a stop."),
		("weigh", "reviewer", "Agreed. The batch sheet template still prints ± 0.5 g — Tom flagged it in the clarity vote."),
		("weigh", "manager", "I'll get the template reprinted this week. Leave the procedure as it is."),
		("filter", "author", "New housing seal arrives Thursday. I will do the change with Maria and log it here."),
		("filter", "manager", "Thanks. Reprint the machine sign afterwards — the version on it is out of date."),
	],
	"direct": [
		("trainer", "reader", "weigh", "Your weighing quiz is open again — have another go after reading step 3."),
		("reader", "trainer", "weigh", "Will do this afternoon."),
		("operator", "author", "weigh", "Balance B-1 read 1000.3 g this morning. I stopped and told the shift lead."),
		("manager", "reviewer", "approve", "Can you finish your review of the approval guide by Friday?"),
	],
}
