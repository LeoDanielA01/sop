# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt


def step(phase, hue, action, why, items, where="", warning=""):
	parts = [f"<p><strong>{action}</strong></p>"]
	if why:
		parts.append(f"<p><em>{why}</em></p>")
	if items:
		parts.append("<ol>" + "".join(f"<li><p>{item}</p></li>" for item in items) + "</ol>")
	if warning:
		parts.append(callout("warning", [warning]))
	if where:
		parts.append(f'<p data-sop="step-meta">{where}</p>')
	return f'<div data-sop="step" data-phase="{phase}" data-hue="{hue}">' + "".join(parts) + "</div>"


def callout(tone, lines, title=None):
	lead = f"<p><strong>{title}</strong></p>" if title else ""
	return f'<div data-sop="callout" data-tone="{tone}">{lead}' + "".join(f"<p>{line}</p>" for line in lines) + "</div>"


def page(purpose, scope, *blocks, records=""):
	parts = [f"<h2>Purpose</h2><p>{purpose}</p>"]
	if scope:
		parts.append(f"<h2>Scope</h2><p>{scope}</p>")
	parts.append("<h2>Step by step</h2>")
	parts.extend(blocks)
	if records:
		parts.append(f"<h2>Records</h2><p>{records}</p>")
	return "".join(parts)


def guide(slug, title, process, summary, content, state="effective", since=-60, tags=(), signed=("reader", "operator", "storekeeper"), **extra):
	return {
		"slug": slug,
		"title": title,
		"space": "GUIDE",
		"process": process,
		"summary": summary,
		"state": state,
		"effective_since": since,
		"tags": list(tags),
		"signed_by": list(signed),
		"document_type": "Process SOP",
		"risk_level": "Low",
		"content": content,
		**extra,
	}


SETTINGS = "Rail › Settings"
ADMIN = "Settings › Administration"

GUIDE_PROCEDURES = [
	guide(
		"roles",
		"Set up users and give them roles",
		"Users & roles",
		"Who can read, write, review, approve, train and manage — and how to give someone that role.",
		page(
			"Everything a person can do in the app comes from their roles. Get these right first and the rest of the set-up falls into place.",
			"Creating users and giving them SOP roles. Teams are {sop:teams}; a new starter's first day is {sop:onboard}.",
			"<table><tbody><tr><th><p>Role</p></th><th><p>What it allows</p></th></tr>"
			"<tr><td><p>SOP Reader</p></td><td><p>Reads effective procedures, signs “I have read this”, takes training and quizzes.</p></td></tr>"
			"<tr><td><p>SOP Author</p></td><td><p>Writes drafts, imports from Word, sees Insights and Find and replace.</p></td></tr>"
			"<tr><td><p>SOP Reviewer</p></td><td><p>Comments on drafts in review and approves when a team names them.</p></td></tr>"
			"<tr><td><p>SOP Approver</p></td><td><p>Signs off procedures. Used as the approver when a space has no team.</p></td></tr>"
			"<tr><td><p>SOP Trainer</p></td><td><p>Writes training rules, plans sessions, records outcomes and quiz questions.</p></td></tr>"
			"<tr><td><p>SOP Manager</p></td><td><p>Everything above, plus spaces, teams, organisation settings and retiring.</p></td></tr></tbody></table>",
			step("ACCOUNT", 1, "Create the user", "The app uses the normal user list of the site.", ["Settings › Preferences › Open the desk.", "User list › Add User. Enter the e-mail, first and last name.", "Leave “Send welcome email” on if they should set their own password."], "Desk › User"),
			step("ROLES", 2, "Give the SOP roles", "Start small — Reader — and add roles as people take on more.", ["Open the user › Roles.", "Tick the SOP roles from the table above.", "Save. The new rail items appear the next time they open the app."], "Desk › User › Roles"),
			step("CHECK", 3, "Check what they see", "", ["Log in as the user, or ask them to open the app.", "Authors see Insights and the Create › Procedure menu; readers do not."], "SOP app"),
			callout("note", ["A person with no SOP role and no System Manager role cannot open the app at all."]),
		),
		since=-120,
		tags=["getting-started", "admin"],
	),
	guide(
		"spaces",
		"Set up spaces and processes",
		"Spaces & teams",
		"Spaces are the binders, processes are the chapters. Get them roughly right and leave them alone.",
		page(
			"A space is a body of procedures with a code and an approving team. A process is a folder inside it. Together they decide procedure numbers and how training rules are scoped.",
			"Creating spaces and processes. Who signs off in a space is set with a team — see {sop:teams}.",
			step("SPACE", 1, "Create the space", "One space per area of work, not per department that might be reorganised.", ["Rail › Create › Space (or Procedures sidebar › Spaces › New space).", "Name: e.g. Production. Code: 2–5 letters — procedures here are numbered SOP-CODE-0001.", "Who can see it: Public for most spaces.", "Review every (months): 12 unless a regulation says otherwise.", "Start from: An empty space, or a template to get a ready-made process tree.", "Create space."], "Create › Space", "The code becomes part of every procedure number that gets printed and quoted. Choose it once."),
			step("PROCESS", 2, "Add the processes", "Follow the work in the order it happens. Two levels is usually enough.", ["Hover the space in the sidebar and click + (Add a process to this space).", "Name and Sequence (lower comes first). Add process.", "For a sub-process, hover the process and click + (Add a process inside this one)."], "Procedures sidebar"),
			step("TEAM", 3, "Pick the approving team", "Without a team, everyone with the SOP Approver role is asked to approve.", ["Settings › Spaces.", "Approving team: pick the team for this space."], ADMIN + " › Spaces"),
			step("CHECK", 4, "Check the tree", "", ["Expand the space in the sidebar. If you cannot guess where a new procedure belongs, neither can anyone else."], "Procedures sidebar"),
			callout("warning", ["Deleting a space deletes every procedure in it. Retire procedures instead — see {sop:retire}."]),
		),
		since=-110,
		tags=["getting-started", "admin"],
	),
	guide(
		"teams",
		"Create teams and allocate people",
		"Spaces & teams",
		"Teams decide who signs off in a space and who gets trained on it.",
		page(
			"A team is a named group of people, each with a team role. Linked to a space, it becomes that space's approval route. Training rules can also target a team.",
			"Creating and maintaining teams. Roles of individual users are {sop:roles}.",
			step("TEAM", 1, "Create the team", "Managers only.", ["Settings › Administration › Teams › New team.", "Team name and What this team does."], ADMIN + " › Teams"),
			step("PEOPLE", 2, "Add the people", "", ["Add a person: search and pick each member.", "Set the team role: Reader, Author, Reviewer or Approver.", "Save."], ADMIN + " › Teams", "Reviewers and Approvers sign off every procedure in the team's spaces. Do not make the author of most procedures an Approver — nobody approves their own work."),
			step("LINK", 3, "Link it to a space", "A team card saying “Not linked to a space yet” is not doing any approving.", ["Settings › Spaces › Approving team: pick the team."], ADMIN + " › Spaces"),
			step("TRAIN", 4, "Use it in a training rule", "", ["Training › Rules › New rule › Applies to: Team. See {sop:rules}."], "Training › Rules"),
			"<h2>In this demo</h2><p>All Staff owns the SOP App Guide space, Production owns the Demo Plant. Quality and Warehouse show smaller teams. {user:manager} is an Approver in every team; {user:author} writes most drafts.</p>",
		),
		since=-105,
		tags=["getting-started", "admin", "teams"],
	),
	guide(
		"settings",
		"Configure the app settings",
		"Settings",
		"Your own preferences, and the organisation-wide switches only a manager can change.",
		page(
			"Settings has two halves: My settings, which only affect you, and Administration, which affect everyone.",
			"",
			step("MINE", 1, "Set your preferences", "", ["Rail › Settings › Preferences: Appearance, Save as you type, Rows per page, Language.", "Notifications: Approval requests, Newly effective procedures, Training reminders, Review digest."], SETTINGS),
			step("ORGANISATION", 2, "Set the organisation profile", "Managers only.", ["Administration › Organisation › Profile: General or Public sector. Public sector turns off Allow permanent deletion.", "Writing language and Show week numbers.", "Start from the standard layout — Edit layout to change the headings every new procedure starts with.", "Proficiency levels: when someone counts as Intermediate and Expert."], ADMIN + " › Organisation"),
			step("RECORDS", 3, "Choose the linked records", "These are the records authors can mention with # and that can appear in the Safety box.", ["Administration › Linked records › Add record type.", "Label, Icon and the fields to show.", "Show in procedure: switch on for things people need before they start — PPE, chemicals, equipment."], ADMIN + " › Linked records"),
			step("DEMO", 4, "Demo data", "System Managers only.", ["Administration › Demo data: Insert demo data, Rebuild, or Remove demo data."], ADMIN + " › Demo data"),
		),
		since=-100,
		tags=["admin"],
	),
	guide(
		"onboard",
		"Onboard a new team member",
		"Users & roles",
		"What to do before someone's first day so their reading is already waiting for them.",
		page(
			"A new person should log in on day one and find their training queued. That only happens if the account, the role and the team are set up beforehand.",
			"",
			step("BEFORE", 1, "Create the account and role", "", ["Follow {sop:roles}. Start at SOP Reader."], "Desk › User"),
			step("BEFORE", 1, "Add them to their team", "Training rules match on team, so a person in no team gets no training.", ["Follow {sop:teams}."], ADMIN + " › Teams"),
			step("DAY ONE", 2, "Run the rules", "", ["Training › Rules › Run now on each rule that covers their team."], "Training › Rules"),
			step("DAY ONE", 2, "Check their queue", "", ["Training matrix › filter With gaps. Their row should show Assigned cells."], "Training › Training matrix"),
			callout("note", ["This procedure is still a draft. It is here to show what a draft looks like next to published ones."]),
		),
		state="draft",
		tags=["onboarding"],
		signed=(),
	),
	guide(
		"write",
		"Write a procedure",
		"Drafting",
		"From a blank page to a draft your team can follow.",
		page(
			"Anyone with the Author role can write a procedure. This walks from an empty page to a draft that is ready for review.",
			"Writing and saving a draft. Sending it out is {sop:review}. Every block you can use is in {sop:blocks}.",
			step("START", 1, "Create the draft", "", ["Rail › Create › Procedure, or right-click a process › New procedure here.", "Title: what this procedure makes happen — “Release a batch”, not “Batch release notes”.", "Space, Process and a one-line Summary — it is what people see in search."], "Create › Procedure"),
			step("WRITE", 2, "Write the steps", "The standard layout gives you Purpose, Scope, Responsibilities, Safety and PPE, Steps and Records.", ["Right-click for tools, or Pin tools to keep a toolbar.", "Insert › Step for each action. Give it a Phase — steps with the same phase share a colour.", "Fill “What is done”, “Why it matters”, the actions and the equipment or location."], "Editor"),
			step("WRITE", 2, "Add the safety", "Warnings go before the step they apply to — the reader acts first and reads second.", ["Insert › Critical for life-safety rules (shown in red, and printed on the machine sign).", "Insert › Warning for hazards, Note for tips."], "Editor"),
			step("CHECK", 3, "Fix the clarity check", "", ["The bar under the editor shows Easy to read / Fairly hard / Hard to read.", "Expand it and fix the flags: Owner, Record, Safety, Vague and so on. Each has a fix button."], "Editor › clarity bar"),
			step("SAVE", 4, "Save the draft", "", ["Save draft, or Ctrl+S. With Save as you type on, it saves by itself."], "Editor"),
			callout("note", ["A draft is only visible to you and to managers until you send it for review."]),
		),
		since=-95,
		tags=["getting-started", "writing"],
		author="author",
	),
	guide(
		"blocks",
		"Every block you can use in a procedure",
		"Drafting",
		"Steps, callouts, mentions, live values, checks, questions and branches — what each one is for.",
		page(
			"The editor has blocks that do more than format text. This is the reference for all of them. Right-click in the editor to open the tools.",
			"",
			"<table><tbody><tr><th><p>Block</p></th><th><p>Use it for</p></th></tr>"
			"<tr><td><p>Step</p></td><td><p>One numbered action with a phase, why, actions and equipment / location.</p></td></tr>"
			"<tr><td><p>Critical</p></td><td><p>A life-safety rule. Shown in red and printed on the machine sign.</p></td></tr>"
			"<tr><td><p>Warning</p></td><td><p>A hazard people must not miss. Place it before the step.</p></td></tr>"
			"<tr><td><p>Note</p></td><td><p>Worth knowing, not a hazard.</p></td></tr>"
			"<tr><td><p>Mention a record (#)</p></td><td><p>Links a live record — another procedure, PPE, a chemical, a room. Shows its current name.</p></td></tr>"
			"<tr><td><p>Mention a person (@)</p></td><td><p>Names someone; stays right if they change their name.</p></td></tr>"
			"<tr><td><p>Live value</p></td><td><p>A number or date pulled from a record each time the procedure is opened.</p></td></tr>"
			"<tr><td><p>Check</p></td><td><p>A green tick or red cross from live data — “calibration date not passed”.</p></td></tr>"
			"<tr><td><p>Question + Branch</p></td><td><p>Let the reader pick a situation; show only the section that applies. See {sop:branches}.</p></td></tr>"
			"<tr><td><p>Table, Checklist, Image</p></td><td><p>Limits and settings, things to tick in any order, pictures.</p></td></tr></tbody></table>",
			callout("note", ["The step you are reading is a Step block. The box you are reading now is a Note. {sop:weigh} in the Demo Plant uses all of them."]),
		),
		since=-90,
		tags=["getting-started", "reference"],
	),
	guide(
		"branches",
		"Make a procedure follow the situation",
		"Drafting",
		"One procedure that shows each reader only the part that applies to them.",
		"<h2>Purpose</h2><p>Most procedures have a “but if…”. A branch hides the paragraphs that do not apply, and says why.</p>"
		"<h2>Try it</h2><p>Answer the question below and watch the rest of this section change.</p>"
		'<div data-sop-ask="q1" data-sop-options="Damaged|Wrong item|Nothing arrived">What was wrong with the delivery?</div>'
		'<div data-sop-when="ask:q1:is:Damaged" data-sop-label="What was wrong with the delivery? — is &#8220;Damaged&#8221;"><h3>Damaged goods</h3>'
		+ step("ACT", 1, "Photograph and quarantine", "", ["Photograph the damage before anything is moved.", "Quarantine the pallet.", "{user:manager} raises a supplier claim the same day."], "Dock 1")
		+ "</div>"
		'<div data-sop-when="ask:q1:is:Wrong%20item" data-sop-label="What was wrong with the delivery? — is &#8220;Wrong item&#8221;"><h3>Wrong item delivered</h3>'
		+ step("ACT", 1, "Do not put it away", "Stock that is put away is very hard to send back.", ["Check the order against the delivery note.", "Arrange collection with the supplier."], "Dock 1")
		+ "</div>"
		'<div data-sop-when="ask:q1:is:Nothing%20arrived" data-sop-label="What was wrong with the delivery? — is &#8220;Nothing arrived&#8221;"><h3>Delivery did not arrive</h3>'
		+ step("ACT", 1, "Chase the carrier", "", ["Confirm the delivery was dispatched.", "Tell the line before the shortage bites."], "Goods-in office")
		+ "</div>"
		"<h2>How to build one</h2>"
		+ step("BUILD", 2, "Add the question", "", ["Insert › Question. Type each answer in “Add an answer…”."], "Editor")
		+ step("BUILD", 2, "Wrap each section in a branch", "", ["Select the section, Insert › Branch.", "On an answer: pick the question and the answer. On record data: pick a record and a condition.", "Add branch. The header reads “Only when …”."], "Editor")
		+ callout("warning", ["Branches hide text on screen, never on paper. A printed controlled copy always contains every branch."]),
		since=-85,
		tags=["reference"],
	),
	guide(
		"import",
		"Import procedures from Word",
		"Importing",
		"Turn a folder of Word SOPs and risk assessments into drafts in one go.",
		page(
			"Most companies already have their SOPs in Word. The importer reads them, keeps the steps, warnings and hazard tables, and creates drafts you can review.",
			"English .docx files, one at a time or in a .zip. Danish copies and non-Word files are listed as skipped.",
			step("PREPARE", 1, "Prepare the files", "The importer reads the document ID from the header table.", ["Each file has a header table with Document ID (SOP-ABC-001, RA-ABC-001 or LOG-ABC-001), Version and Department.", "Put related files in one folder per process; zip the folders."], "Your computer"),
			step("UPLOAD", 2, "Upload", "", ["Procedures › Import.", "Into space: pick the space.", "Choose .zip or .docx."], "Procedures › Import"),
			step("CHECK", 3, "Check the preview", "", ["Each group is a process — rename it in Process name if the folder name is not right.", "Read the ⚠ warnings: missing IDs, pictures to add by hand, duplicate numbers.", "Open “N files not imported” to see why each was skipped."], "Import preview"),
			step("IMPORT", 4, "Import", "", ["Import N as drafts. Risk assessments are created with their hazards and linked to their SOPs.", "Go to procedures and send each draft for review — {sop:review}."], "Import preview"),
		),
		since=-40,
		tags=["writing", "import"],
	),
	guide(
		"mentions",
		"Link records, resources and other procedures",
		"Drafting",
		"Mentions keep names current and let you see everywhere a record is used.",
		page(
			"A mention is a live link. It shows the record's current name, puts PPE and chemicals in the Safety box, and powers Where used.",
			"",
			step("LINK", 1, "Mention a record", "", ["Type # in the editor, pick the record type, search, pick.", "PPE, chemicals, rooms and equipment come from Resources — see {sop:resources}."], "Editor"),
			step("LINK", 1, "Mention a person", "", ["Type @ and pick the person."], "Editor"),
			step("FIND", 2, "See where a record is used", "Before you change or retire something, check what points at it.", ["Rail › Records › Where used.", "Record type and Search records. It lists every procedure, with a snippet."], "Records › Where used"),
		),
		state="approved",
		tags=["writing", "reference"],
		signed=(),
	),
	guide(
		"review",
		"Send a procedure for review",
		"Approval",
		"When the draft is ready, one click puts it in front of the right reviewers.",
		page(
			"Sending for review moves a draft to the people who sign it off. It is the step that turns private writing into a controlled document.",
			"",
			step("CHECK", 1, "Check before you send", "", ["Every step names who does it.", "The clarity check is clear, or you can say why each flag is fine."], "Editor"),
			step("SEND", 2, "Send for review", "Reviewers come from the space's approving team — see {sop:teams}.", ["Open the draft › Send for review.", "The dialog lists each reviewer and their role. Send for review.", "Status changes to In Review."], "Procedure page"),
			step("ANSWER", 3, "Answer the comments", "", ["Review comments sit on the exact words. Reply, or edit and reply.", "Mark resolved when dealt with — Approve stays disabled until every comment is resolved."], "Procedure page › Review comments"),
			callout("note", ["“Request changes” sends it back to Draft with the comments still attached. Fix and send again."]),
		),
		since=-80,
		tags=["getting-started", "review"],
	),
	guide(
		"approve",
		"Approve or send back a procedure",
		"Approval",
		"Approvers read, comment on the exact words, and either approve or send it back.",
		page(
			"An approval is a signature. It says the procedure is accurate, safe and something you are willing to have your name against.",
			"",
			step("READ", 1, "Open the request", "", ["Procedures sidebar › Needs attention › Awaiting my approval, or the notification."], "Procedures sidebar"),
			step("READ", 1, "Read it as the person who has to do the job", "", ["Could someone in their first week follow this without asking?", "Answer every question block and read each branch."], "Procedure page"),
			step("COMMENT", 2, "Comment on the exact words", "", ["Select the text › Comment.", "General points go under Comments without a passage."], "Procedure page"),
			step("DECIDE", 3, "Approve or request changes", "", ["Approve, once every comment is resolved.", "Or Request changes › What has to change › Send it back."], "Procedure page › bottom bar", "Approving is a signature against your name. Only approve when you have actually read it."),
			"<p>When everyone has approved, a manager brings it into force — {sop:publish}.</p>",
		),
		state="in_review",
		tags=["review"],
		signed=(),
	),
	guide(
		"publish",
		"Bring a procedure into force",
		"Publishing",
		"Publishing sets the effective date, fixes a version number and starts training.",
		page(
			"Publishing is the moment a document becomes the official way of working.",
			"",
			step("OPEN", 1, "Open the approved procedure", "The status badge is blue: Approved.", [], "Procedure page"),
			step("PUBLISH", 2, "Bring into force", "", ["Bring into force.", "Effective from: today, or a later date when a form or machine setting has to change first.", "What changed: a sentence someone can read in a year.", "Material change — everyone has to be trained again: leave ticked unless the change is cosmetic.", "Publish vN.0."], "Bring into force dialog", "Marking a real change as not material is how people end up working to a version they never read."),
			step("AFTER", 3, "Watch the sign-offs", "", ["Readers see “Confirm you have read and understood…” and sign with I have read this.", "Training rules create assignments straight away — {sop:rules}."], "Procedure page"),
		),
		since=-75,
		tags=["getting-started", "review"],
	),
	guide(
		"revise",
		"Revise a procedure that is in force",
		"Publishing",
		"Change a live procedure without anyone working to a half-edited copy.",
		page(
			"A procedure in force cannot be edited in place. A revision gives you a working copy while the current version stays live.",
			"",
			step("START", 1, "Start a revision", "", ["Open the effective procedure › Start a revision. The editor opens; readers still see the version in force."], "Procedure page"),
			step("EDIT", 2, "Make the change and send it", "", ["Edit as in {sop:write}.", "Send for review — {sop:review}."], "Editor"),
			step("COMPARE", 3, "Compare the versions", "", ["More › Compare revisions: Inline View or Side by Side.", "More › Revision history lists every version with Compare on each row."], "Procedure page › More"),
			step("PUBLISH", 4, "Publish the new version", "", ["Bring into force, as in {sop:publish}."], "Procedure page"),
			callout("note", ["{sop:weigh} in the Demo Plant is on its second version — open Compare revisions to see what changed."]),
		),
		since=-70,
		tags=["review"],
	),
	guide(
		"retire",
		"Retire a procedure",
		"Publishing",
		"Take a procedure out of use without losing its history.",
		page(
			"When the work has stopped or another procedure replaces it, retire it. It stops creating training, but every version and signature stays readable.",
			"",
			step("CHECK", 1, "Check what points at it", "", ["Records › Where used — fix procedures that mention it first."], "Records › Where used"),
			step("RETIRE", 2, "Retire it", "", ["Open the effective procedure › More › Retire. There is no confirmation — be sure."], "Procedure page › More", "If the work still happens and only the method changed, revise it instead — {sop:revise}."),
		),
		state="retired",
		tags=["admin"],
		signed=(),
		retire_reason="Kept as an example of a retired procedure.",
	),
	guide(
		"rules",
		"Set up training rules",
		"Training rules",
		"Rules put the right procedures in front of the right people, without anyone keeping a list.",
		page(
			"A training rule connects a group of people to a space or a procedure. Publish a procedure the rule covers and the assignments appear by themselves.",
			"",
			step("RULE", 1, "Write the rule", "Trainers and managers.", ["Training › Rules › New rule (or Create › Training rule).", "Applies to: Role, Team, User, Designation or Department.", "Covers: a whole Space, or one Procedure."], "Training › Rules"),
			step("RULE", 1, "Say how they train", "", ["How they train: Read & Understand, Classroom, On the Job or Assessment.", "Due within (days) and Repeat every (months) for refreshers.", "For a quiz: How they train = Assessment, tick “An assessment decides whether they passed”, and set Pass mark %, Quiz attempts allowed and Questions per quiz."], "Training › Rules"),
			step("RUN", 2, "Save and run", "", ["Save rule. Each rule reads “X must train on Y”.", "Run now to create assignments for everyone it covers today."], "Training › Rules"),
			"<h2>In this demo</h2><p>All Staff must read the SOP App Guide. Production must pass a quiz on every Demo Plant procedure. Warehouse trains on the job on {sop:ipa}. Every SOP Author must read {sop:write}.</p>",
		),
		since=-65,
		tags=["training", "getting-started"],
	),
	guide(
		"assign",
		"Assign training and work the matrix",
		"Training records",
		"One-off assignments, and the matrix that shows who is behind.",
		page(
			"Rules cover the routine. For a one-off — a new hazard, a near miss — assign training by hand. The matrix shows everyone at a glance.",
			"",
			step("ASSIGN", 1, "Assign training", "", ["Training › Training matrix › Assign training.", "Procedure, How they train, Due in (days), the people. Assign."], "Training › Training matrix"),
			step("TRACK", 2, "Work the matrix", "Red first: someone doing the work without having read the current version.", ["Filter: Everyone, With gaps, Overdue.", "Cells read Trained, In progress, Assigned, Overdue, Waived or Not assigned."], "Training › Training matrix"),
			step("ASSESS", 3, "Record outcomes", "", ["Open the assignment › Assess › Record outcome: Competent, Needs More Practice or Not Competent, Score %, Remarks. Save outcome."], "Training › My training"),
			step("EXPORT", 4, "Export for an audit", "Managers only.", ["Training matrix › Export records."], "Training › Training matrix"),
		),
		since=-60,
		tags=["training"],
	),
	guide(
		"quiz",
		"Check understanding with a quiz",
		"Sessions & quizzes",
		"A few questions that prove the procedure was understood, not just opened.",
		page(
			"An acknowledgement proves someone clicked. A quiz proves they took something in.",
			"",
			step("WRITE", 1, "Write the questions", "Author, trainer or manager.", ["Open the procedure › side panel › Quiz questions › Add a question.", "Question, Readers pick (One answer or Several answers), 2–6 answers with the correct ones toggled, an optional Explanation.", "Save question."], "Procedure page › Quiz questions"),
			step("RULE", 2, "Require it in a rule", "", ["In the training rule set How they train to Assessment, tick “An assessment decides whether they passed” and set the Pass mark % — {sop:rules}.", "With any other method there is no quiz to take, even if questions exist."], "Training › Rules"),
			step("TAKE", 3, "What the trainee sees", "", ["My training › Take the quiz. “Attempt X of Y · pass mark Z%”.", "Submit answers. Below the mark: Try again. Out of attempts: retraining is assigned.", "A pass completes the assignment and opens the Certificate."], "Training › My training"),
			callout("note", ["If nearly everyone misses the same question, the procedure is usually at fault, not the people."]),
		),
		since=-55,
		tags=["training"],
	),
	guide(
		"sessions",
		"Run a classroom or on-the-job session",
		"Sessions & quizzes",
		"Book a session, record who came, and sign off the training in one go.",
		page(
			"Some procedures cannot be learned by reading. A session covers several procedures and turns attendance into signed-off training.",
			"",
			step("PLAN", 1, "Plan the session", "", ["Training › Sessions › Plan a session.", "What it covers, Date, Time, How it runs, Where, Procedures covered, Who attends, Notes. Plan it."], "Training › Sessions"),
			step("HOLD", 2, "Record attendance", "", ["Open the session on the day.", "Switch on attended for each person and pick the outcome: Competent, Needs More Practice or Not Competent.", "Save attendance. Competent closes their assignments for every procedure covered."], "Training › Sessions", "Do not mark someone as attended who left early. The signature says they can do the job."),
		),
		since=-50,
		tags=["training"],
	),
	guide(
		"records",
		"Training records and certificates",
		"Training records",
		"Where the proof of training lives, and how to hand it to an auditor.",
		page(
			"Every completed assignment is a record: who, which version, how, when and who assessed it.",
			"",
			step("SEE", 1, "See your own record", "", ["Training › My training › Done."], "Training › My training"),
			step("PRINT", 2, "Print a certificate", "", ["Open a completed, Competent assignment › Certificate.", "Print or save as PDF. Refreshers print as “Certificate of refresher training”."], "Certificate page"),
			step("PROFICIENCY", 3, "Proficiency", "Repeated competent training builds a level — Intermediate, then Expert — set in Settings › Organisation.", [], "Settings › Organisation"),
		),
		since=-45,
		tags=["training"],
	),
	guide(
		"risk",
		"Keep a risk assessment",
		"Risk assessments",
		"Hazards, scores, actions and recurring checks — linked to the procedures they cover.",
		page(
			"A risk assessment lists each hazard of a job, how likely and how bad it is, what controls it, and what is still to be done.",
			"Risk assessments are imported from Word with their hazard table ({sop:import}) or written in the desk. They show on every procedure they apply to.",
			step("WRITE", 1, "Fill in the hazards", "Score = Likelihood × Severity, each 1–5.", ["Hazard, consequence and existing controls.", "Likelihood and Severity, then the residual scores after the actions.", "Additional actions with an owner and a due date; status Open, Done or Not needed."], "Desk › SOP Risk Assessment"),
			step("LINK", 2, "Link the procedures", "", ["Applies to: add every procedure the assessment covers."], "Desk › SOP Risk Assessment"),
			step("CHECK", 3, "Recurring checks", "", ["Give a hazard a Recurring check and Check every (Daily … Yearly).", "When it is due, the Risk assessment panel on the procedure shows “due now” with Mark done. Marking it done logs the check."], "Procedure page › Risk assessment"),
			callout("note", ["See it working on {sop:weigh}: an overdue action, a daily balance check that is due, and a weekly interlock test."]),
		),
		since=-35,
		tags=["safety"],
	),
	guide(
		"logs",
		"Log cleaning and service work",
		"Logs & signs",
		"The cleaning and service log that sits on the procedure itself.",
		page(
			"Logging on the procedure ties the record to the instruction that was followed, and keeps every room's status current.",
			"Procedures that mention a room or machine show the Cleaning & service log panel.",
			step("CLEAN", 1, "Log a cleaning", "", ["Open the procedure › Log cleaning.", "Room / machine, Cleaning (Minor or Major), Reason, Product before, Set room status to, Checked by, Notes.", "Save log entry. The room's status chip updates for everyone."], "Procedure page › Cleaning & service log"),
			step("SERVICE", 2, "Log a service", "", ["Log service: Inspection, Function test, Maintenance, Repair or Filter change."], "Procedure page › Cleaning & service log"),
			callout("note", ["{sop:clean} and {sop:filter} in the Demo Plant already have entries."]),
		),
		since=-30,
		tags=["records"],
	),
	guide(
		"signs",
		"Print a machine sign",
		"Logs & signs",
		"A sign with the critical rules, the gear needed and a QR code to the current procedure.",
		page(
			"A sign on the machine is read; a binder in the office is not. The QR code always opens the version in force.",
			"",
			step("PRINT", 1, "Print the sign", "", ["Open the procedure › More › Print sign with QR code.", "The sign shows the number and version, the Critical boxes and “Required before you start”.", "Print sign."], "Procedure page › More"),
			step("FIX", 2, "Fix it and keep it current", "", ["Fix it at the point of use.", "Reprint after every new version — the version is printed on it."], "Point of use"),
			callout("note", ["Only Critical blocks are printed. Write the life-safety rules as Critical — see {sop:blocks}. Try it on {sop:filter}."]),
		),
		since=-25,
		tags=["safety", "records"],
	),
	guide(
		"resources",
		"Manage PPE, chemicals and other resources",
		"Resources",
		"The registers behind the Safety box: PPE, chemicals, rooms and equipment.",
		page(
			"Resources are the things a procedure needs. Mention them and they appear in “Before you start” with what they require.",
			"",
			step("SET UP", 1, "Resource types", "", ["Desk › SOP Resource Type: PPE, Chemical, Room, Equipment — with the attributes each shows.", "Show in procedure puts them in the Safety box; Can be issued allows issuing to employees."], "Desk › SOP Resource Type"),
			step("SET UP", 1, "Add the resources", "", ["Desk › SOP Resource: name, type, attribute values, the date it needs checking, and what it requires (a chemical requires its PPE)."], "Desk › SOP Resource"),
			step("USE", 2, "Mention them in procedures", "", ["Type # › pick the resource. See {sop:mentions}."], "Editor"),
			step("ISSUE", 3, "Issue to an employee", "When ERPNext is installed.", ["Records › Issue to employee: Type, Resource, Employee. Consumables come from stock; kept items are handed over as an asset."], "Records › Issue to employee"),
		),
		since=-20,
		tags=["safety"],
	),
	guide(
		"insights",
		"Read the insights and clarity feedback",
		"Insights",
		"Which procedures are stale, unread or confusing — and what to do about it.",
		page(
			"Insights answers the question a manager actually has: is any of this being used, and where is it going wrong?",
			"Authors and managers. Non-managers see the procedures they own.",
			step("READ", 1, "Read the tiles", "", ["Rail › Insights: In force, Read and signed, Training done, Reviews overdue, Found it clear."], "Insights"),
			step("ACT", 2, "Work Needs attention", "Act on one row a month. A dashboard nobody acts on is a slower way of doing nothing.", ["Reviews coming due, Least read, Waiting for approval, Hard to follow."], "Insights › Needs attention"),
			step("LISTEN", 3, "Read the clarity votes", "", ["Readers answer “Was this clear?” at the bottom of every effective procedure. “No” asks what was unclear.", "A cluster of No votes is a rewrite, not a training problem."], "Procedure page"),
		),
		since=-15,
		tags=["admin"],
	),
	guide(
		"chat",
		"Talk about a procedure",
		"Collaboration",
		"Questions about a procedure belong next to the procedure, not in someone's inbox.",
		page(
			"Every procedure has a discussion room. Messages there stay with the procedure, so the next person sees the answer.",
			"",
			step("ROOM", 1, "Use the discussion", "", ["Open the procedure › side panel › Discussion.", "“Message everyone on SOP-…” — owners, approvers and past posters see it.", "Share a file or image if a photo says it better."], "Procedure page › Discussion"),
			step("DIRECT", 2, "Message one person", "", ["Rail › Messages › Find someone. Direct messages can also Call or Email."], "Rail › Messages"),
			callout("note", ["{sop:weigh} has a short discussion about the new tolerance — open Discussion to read it."]),
		),
		since=-10,
		tags=["collaboration"],
	),
]
