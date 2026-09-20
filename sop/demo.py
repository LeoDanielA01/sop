# Copyright (c) 2026, Leo Daniel and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, nowdate

from sop.api import lifecycle
from sop.api import procedures as procedures_api
from sop.api import processes as processes_api
from sop.api import requirements as requirements_api
from sop.api import review as review_api
from sop.api import sessions as sessions_api
from sop.api import training as training_api

PEOPLE = [
	("sara.james@example.com", "Sara", "James", ["SOP Manager", "SOP Approver"]),
	("dan.walsh@example.com", "Dan", "Walsh", ["SOP Author"]),
	("leila.k@example.com", "Leila", "Karimian", ["SOP Approver", "SOP Trainer"]),
	("tom.r@example.com", "Tom", "Rivera", ["SOP Reader"]),
]

TEAM = "All Staff"

DEMO_CODES = ("OPS", "HR")

APP_PROCESSES = [
	("OPS", "Writing Procedures", ["Drafting", "Review & Approval", "Publishing"]),
	("OPS", "Running the app", ["Spaces & processes", "Insights & admin"]),
	("HR", "Training", ["Assigning training", "Recording outcomes"]),
]

PROCEDURES = [
	{
		"slug": "write",
		"title": "How to write a procedure in this app",
		"space": "OPS",
		"process": "Drafting",
		"summary": "From a blank page to a document your team can follow, in about five minutes.",
		"state": "effective",
		"effective_since": -120,
		"tags": ["getting-started"],
		"content": """<h2>Purpose</h2>
<p>Anyone with the Author role can write a procedure. This walks you from an empty page to a draft that is ready for review.</p>
<h2>Scope</h2>
<p>Covers writing and saving a draft. Sending it out for approval is {sop:review}; publishing it is {sop:publish}.</p>
<h2>Responsibilities</h2>
<ul>
<li><strong>Author</strong> — writes the draft and keeps it current. {user:author} wrote this one.</li>
<li><strong>Process owner</strong> — decides the procedure is needed and is accurate.</li>
</ul>
<h2>Procedure</h2>
<ol>
<li><strong>Open the space you are writing for</strong> — responsible: Author · records: none. Spaces sit in the left sidebar. The space code becomes the procedure number, so a procedure in OPS is numbered OPS-0001.</li>
<li><strong>Click New procedure</strong> — responsible: Author. Give it a title that answers "what does this make happen?" — "Release a batch", not "Batch release notes".</li>
<li><strong>Fill in the summary</strong> — responsible: Author. One line. It is what people see in search results and in the procedures list, so make it say who it is for.</li>
<li><strong>File it under a process</strong> — responsible: Author. Processes group related procedures inside a space. See {sop:spaces} for setting them up.</li>
<li><strong>Write the body</strong> — responsible: Author. Right-click anywhere in the editor for the full tool palette, or pin the toolbar. Every block you can use is listed in {sop:blocks}.</li>
<li><strong>Watch the clarity check</strong> — responsible: Author. The bar under the editor counts reading time and flags steps with no owner, vague words like "as required", and hazards with no warning next to them.</li>
<li><strong>Save</strong> — responsible: Author · records: draft. Ctrl S saves at any time. With "Save as you type" on in Settings, your draft is saved a couple of seconds after you stop typing.</li>
</ol>
<blockquote><p><strong>Note</strong> — a draft is only visible to you and to managers until you send it for review. Save as often as you like.</p></blockquote>
<h2>Records</h2>
<p>The draft itself. Nothing is issued to readers until it is published.</p>"""
	},
	{
		"slug": "blocks",
		"title": "Every block you can put in a procedure",
		"space": "OPS",
		"process": "Drafting",
		"summary": "Steps, warnings, record mentions, live values, checks, questions and branches — what each one is for.",
		"state": "effective",
		"effective_since": -110,
		"tags": ["getting-started", "reference"],
		"content": """<h2>Purpose</h2>
<p>The editor has blocks that do more than format text. This is the reference for all of them. Right-click in the editor to bring up the palette, or pin the toolbar from the same menu.</p>
<h2>Writing blocks</h2>
<ol>
<li><strong>Step</strong> — a numbered action. One action per step, with the person responsible and the record it produces.</li>
<li><strong>Warning</strong> — a hazard someone could be hurt by, or a mistake that ruins the batch. Put it immediately before the step it applies to, never after.</li>
<li><strong>Note</strong> — worth knowing, but nothing goes wrong if it is missed.</li>
<li><strong>Checklist</strong> — for things to tick off in any order, where a numbered step would imply a sequence that does not exist.</li>
<li><strong>Table</strong> — for limits, tolerances and settings. Far easier to check against than the same numbers buried in a sentence.</li>
</ol>
<blockquote><p><strong>Warning</strong> — a warning placed after its step has already been missed. The reader acts first and reads second.</p></blockquote>
<h2>Blocks that stay current</h2>
<ol>
<li><strong>Mention a record</strong> — type # to link a live record: another procedure, an item, a supplier, a form. The link shows the record's current title and status, so a renamed record does not leave a stale name behind. {sop:publish} above is a mention.</li>
<li><strong>Mention a person</strong> — type @ to name someone. {user:manager} is a person mention; it stays right when someone changes their name.</li>
<li><strong>Live value</strong> — a number or date pulled from a record each time the procedure is opened. Use it for a limit that is maintained somewhere else, so it can never drift out of date here.</li>
<li><strong>Check</strong> — the same idea, but it shows a green tick or a red cross: "stock is at least 50", "the calibration date has not passed". The reader sees the answer, not the raw number.</li>
</ol>
<h2>Blocks that change what is shown</h2>
<ol>
<li><strong>Question</strong> — asks the reader something and offers a set of answers.</li>
<li><strong>Branch</strong> — a section that only appears when a condition holds: an answer to a question, or a value on a record. Everyone else sees one line explaining why it does not apply to them.</li>
</ol>
<p>{sop:branches} shows both of these working, with a question you can answer.</p>
<blockquote><p><strong>Note</strong> — the clarity check also reviews your branches: an answer with nothing behind it, a branch whose question was deleted, or an empty branch all show up in the Procedure list under the editor.</p></blockquote>"""
	},
	{
		"slug": "branches",
		"title": "Make a procedure follow the situation",
		"space": "OPS",
		"process": "Drafting",
		"summary": "One procedure that shows each reader only the part that applies to them.",
		"state": "effective",
		"effective_since": -20,
		"tags": ["getting-started", "reference"],
		"content": """<h2>Purpose</h2>
<p>Most procedures have a "but if…" in them. Written flat, every reader has to work out which paragraphs are theirs. A branch does that for them: the parts that do not apply collapse to a single line saying why.</p>
<h2>Scope</h2>
<p>Covers questions and branches in the editor. The blocks themselves are listed in {sop:blocks}.</p>
<h2>Try it</h2>
<p>Answer the question below and watch the rest of this section change.</p>
<div data-sop-ask="q1" data-sop-options="Damaged|Wrong item|Nothing arrived">What was wrong with the delivery?</div>
<div data-sop-when="ask:q1:is:Damaged" data-sop-label="What was wrong with the delivery? — is &#8220;Damaged&#8221;">
<h3>Damaged goods</h3>
<ol>
<li><strong>Photograph the damage before anything is moved</strong> — responsible: Receiver · records: photographs.</li>
<li><strong>Quarantine the pallet</strong> — responsible: Receiver · records: quarantine label.</li>
<li><strong>Raise a supplier claim the same day</strong> — responsible: {user:manager} · records: claim reference.</li>
</ol>
</div>
<div data-sop-when="ask:q1:is:Wrong%20item" data-sop-label="What was wrong with the delivery? — is &#8220;Wrong item&#8221;">
<h3>Wrong item delivered</h3>
<ol>
<li><strong>Do not put it away</strong> — responsible: Receiver. Stock that is put away is very hard to send back.</li>
<li><strong>Check the order against the delivery note</strong> — responsible: Receiver · records: annotated delivery note.</li>
<li><strong>Arrange collection with the supplier</strong> — responsible: {user:manager} · records: collection reference.</li>
</ol>
</div>
<div data-sop-when="ask:q1:is:Nothing%20arrived" data-sop-label="What was wrong with the delivery? — is &#8220;Nothing arrived&#8221;">
<h3>Delivery did not arrive</h3>
<ol>
<li><strong>Confirm the delivery was dispatched</strong> — responsible: Receiver · records: carrier reference.</li>
<li><strong>Tell the line before the shortage bites</strong> — responsible: {user:manager}.</li>
</ol>
</div>
<h2>How to build one</h2>
<ol>
<li><strong>Add the question first</strong> — responsible: Author. Insert a Question block and type the answers into it. Each answer becomes a chip.</li>
<li><strong>Select the section that belongs to one answer</strong> — responsible: Author. Then choose Branch. The selected text is wrapped, and the header bar shows the condition in plain words.</li>
<li><strong>Pick the condition</strong> — responsible: Author. Either an answer to a question, or a value on a record — "only when the order is over 50,000", "only when the certificate has expired".</li>
<li><strong>Check every answer has somewhere to go</strong> — responsible: Author. The clarity check lists any answer with no branch behind it.</li>
</ol>
<blockquote><p><strong>Warning</strong> — branches hide text on screen, never on paper. A printed controlled copy always contains every branch, so an auditor reads the whole procedure.</p></blockquote>
<blockquote><p><strong>Note</strong> — when a branch depends on a record and that record cannot be read, the section is shown rather than hidden, with an amber line explaining why. Nothing disappears quietly.</p></blockquote>"""
	},
	{
		"slug": "review",
		"title": "How to send a procedure for review",
		"space": "OPS",
		"process": "Review & Approval",
		"summary": "When the draft is ready, one click puts it in front of the right approvers.",
		"state": "effective",
		"effective_since": -90,
		"tags": ["getting-started", "review"],
		"content": """<h2>Purpose</h2>
<p>Sending for review moves a draft out of your hands and routes it to the people who have to sign it off. It is the step that turns private writing into a controlled document.</p>
<h2>Before you send</h2>
<ul>
<li>Every step names who does it.</li>
<li>The clarity check is clear, or you can say why each remaining flag is fine.</li>
<li>Limits and tolerances are numbers, not "as appropriate".</li>
<li>Records the procedure produces are named.</li>
</ul>
<h2>Procedure</h2>
<ol>
<li><strong>Open the draft</strong> — responsible: Author. From your space, or from Waiting on you on your profile.</li>
<li><strong>Click Send for review</strong> — responsible: Author · records: review request. The status changes to In Review and the content is locked while approvers read it.</li>
<li><strong>Choose the approval route</strong> — responsible: Author. The dialog shows who will be asked and in what order. A route with two approvers asks the second only after the first has signed.</li>
<li><strong>Approvers are notified</strong> — responsible: System · records: notification. Each one can comment on the exact sentence they are questioning. {sop:approve} is what they do next.</li>
<li><strong>Answer the comments</strong> — responsible: Author. Reply in the thread, or edit and reply. Resolve each one so the approver can see it has been dealt with.</li>
<li><strong>Send again if it comes back</strong> — responsible: Author. Requested changes return the procedure to Draft with the comments still attached.</li>
</ol>
<blockquote><p><strong>Note</strong> — you can see the whole approval chain, and where it has got to, in the Reviewers panel while the procedure is open.</p></blockquote>
<h2>Records</h2>
<p>The review request, every comment and every decision stay on the procedure permanently, including for versions that were never published.</p>"""
	},
	{
		"slug": "approve",
		"title": "How to approve a procedure",
		"space": "OPS",
		"process": "Review & Approval",
		"summary": "Approvers read, comment, and either sign it off or send it back.",
		"state": "in_review",
		"tags": ["review"],
		"content": """<h2>Purpose</h2>
<p>An approval is a signature. It says the procedure is accurate, safe to follow, and something you are willing to have your name against.</p>
<h2>Responsibilities</h2>
<p>{user:trainer} and {user:manager} approve in this demo. An approver must not be the person who wrote the draft.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Open the request</strong> — responsible: Approver. From the notification, or from Waiting on you.</li>
<li><strong>Read it as the person who has to do the job</strong> — responsible: Approver. Could someone on their first week follow this without asking anyone?</li>
<li><strong>Comment on the exact words</strong> — responsible: Approver · records: review comment. Select the text and comment. A comment pinned to a sentence is acted on; "paragraph 3 is unclear" in an email is not.</li>
<li><strong>Check the branches</strong> — responsible: Approver. Answer each question and read what appears. A branch nobody can reach is a gap in the procedure.</li>
<li><strong>Approve, or request changes</strong> — responsible: Approver · records: approval decision. Both sit at the bottom of the page. Requesting changes sends it back to the author with your comments.</li>
</ol>
<blockquote><p><strong>Warning</strong> — approving is a signature against your name and it stays in the record. Only approve when you have actually read it.</p></blockquote>
<p>Once everyone has signed, a manager brings it into force — see {sop:publish}.</p>"""
	},
	{
		"slug": "publish",
		"title": "How to bring a procedure into force",
		"space": "OPS",
		"process": "Publishing",
		"summary": "Publishing sets the effective date, stamps a revision number, and starts training.",
		"state": "approved",
		"tags": ["getting-started"],
		"content": """<h2>Purpose</h2>
<p>Publishing is the moment a document becomes the official way of working. It fixes a revision number, sets the date it applies from, and hands the new version to everyone who has to be trained on it.</p>
<h2>Responsibilities</h2>
<p>Managers only. {user:manager} publishes in this demo.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Open the approved procedure</strong> — responsible: Manager. The header badge reads Approved.</li>
<li><strong>Click Bring into force</strong> — responsible: Manager · records: revision.</li>
<li><strong>Set the effective date</strong> — responsible: Manager. Today, or a date in the future when the change needs a new form printed or a machine setting changed first.</li>
<li><strong>Write the change summary</strong> — responsible: Manager · records: revision note. Say what changed and why, in a sentence someone can read a year later.</li>
<li><strong>Decide whether the change is material</strong> — responsible: Manager. Material means everyone is trained again. Not material means only people who have never been trained pick it up.</li>
<li><strong>Confirm</strong> — responsible: Manager · records: revision, training assignments. Training rules fire immediately — see {sop:training}.</li>
</ol>
<blockquote><p><strong>Warning</strong> — marking a real change as not material is how people end up working to a version they have never read. If in doubt, material.</p></blockquote>
<blockquote><p><strong>Note</strong> — readers who owe an acknowledgement see a banner the next time they open the procedure. Changing it later means a new revision — see {sop:revise}.</p></blockquote>"""
	},
	{
		"slug": "revise",
		"title": "How to revise a procedure that is already in force",
		"space": "OPS",
		"process": "Publishing",
		"summary": "Change a live procedure without anyone working to a half-edited copy.",
		"state": "effective",
		"effective_since": -45,
		"tags": ["review"],
		"content": """<h2>Purpose</h2>
<p>A procedure in force cannot be edited in place — people are following it right now. A revision gives you a private copy to work on while the current version stays live, then swaps them over on approval.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Open the effective procedure and choose Start a revision</strong> — responsible: Author · records: draft revision. The version in force keeps being served to readers.</li>
<li><strong>Make the changes</strong> — responsible: Author. Same editor, same blocks as {sop:write}.</li>
<li><strong>Compare against what is live</strong> — responsible: Author. Revision history shows the two versions side by side with the changes marked, so you can check you changed what you meant to and nothing else.</li>
<li><strong>Write the change summary as you go</strong> — responsible: Author. Easier now than after review, when you have forgotten the small edits.</li>
<li><strong>Send for review</strong> — responsible: Author. Same route as {sop:review}. Approvers see the comparison, not just the new text.</li>
<li><strong>Publish</strong> — responsible: Manager · records: revision. The new revision number takes over on its effective date and the old version moves into history.</li>
</ol>
<blockquote><p><strong>Note</strong> — every superseded version stays readable, with the acknowledgements that were signed against it. That is what makes the history worth anything in an audit.</p></blockquote>
<p>When a procedure should not come back at all, retire it instead — {sop:retire}.</p>"""
	},
	{
		"slug": "retire",
		"title": "How to retire a procedure that is no longer used",
		"space": "OPS",
		"process": "Publishing",
		"summary": "Take a procedure out of use without losing its history.",
		"state": "retired",
		"tags": ["admin"],
		"content": """<h2>Purpose</h2>
<p>When a procedure has been replaced or the work has stopped, retire it. It stops being issued and stops generating training, but every version and every signature stays readable.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Check what points at it</strong> — responsible: Manager. Other procedures may mention it. Fix those first or you leave readers at a dead end.</li>
<li><strong>Open the effective procedure</strong> — responsible: Manager. Only a procedure in force can be retired.</li>
<li><strong>Choose Retire from the menu</strong> — responsible: Manager · records: retirement note. Say what replaces it, or why the work stopped.</li>
<li><strong>Confirm</strong> — responsible: Manager. It moves to Retired at once and stops creating training assignments.</li>
</ol>
<blockquote><p><strong>Warning</strong> — retiring is not editing. If the work still happens and the method has just changed, start a revision instead — see {sop:revise}.</p></blockquote>"""
	},
	{
		"slug": "training",
		"title": "How to assign and track training",
		"space": "HR",
		"process": "Assigning training",
		"summary": "Rules that put the right procedures in front of the right people, without anyone keeping a list.",
		"state": "effective",
		"effective_since": -75,
		"tags": ["training", "getting-started"],
		"content": """<h2>Purpose</h2>
<p>A training rule connects a group of people to a set of procedures. Publish a procedure the rule covers and the assignments appear by themselves — nobody maintains a spreadsheet of who owes what.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Open Training rules</strong> — responsible: {user:trainer}. Under Training in the left navigation.</li>
<li><strong>Choose what the rule covers</strong> — responsible: Trainer. A whole space, or one process inside it. Covering a space means future procedures are included automatically.</li>
<li><strong>Choose who it applies to</strong> — responsible: Trainer. A team, one person, or everyone.</li>
<li><strong>Pick the method</strong> — responsible: Trainer. Read and understand means the person reads it and signs. On the job means a trainer watches them do it and signs. Classroom is a booked session — see {sop:sessions}.</li>
<li><strong>Set the due days and refresher</strong> — responsible: Trainer. Due days counts from the day the assignment is created. A refresher of twelve months brings it back round every year.</li>
<li><strong>Save and let it run</strong> — responsible: Trainer · records: training assignments. Assignments are created for everyone the rule covers.</li>
</ol>
<h2>Tracking it</h2>
<ol>
<li><strong>Open the Training matrix</strong> — responsible: Trainer. People down the side, procedures across the top, one cell per assignment.</li>
<li><strong>Work the red cells first</strong> — responsible: Trainer. Red is overdue: someone is doing the work without having read the current version.</li>
<li><strong>Check after every publish</strong> — responsible: Trainer. A material change in {sop:publish} reassigns everyone, and the matrix turns amber until they sign.</li>
</ol>
<blockquote><p><strong>Note</strong> — if someone has no assignments, check the team they are in and whether a rule covers their space. That is nearly always the reason.</p></blockquote>"""
	},
	{
		"slug": "quiz",
		"title": "How to check understanding with a quiz",
		"space": "HR",
		"process": "Recording outcomes",
		"summary": "A few questions that prove the procedure was read, not just opened.",
		"state": "effective",
		"effective_since": -30,
		"tags": ["training"],
		"content": """<h2>Purpose</h2>
<p>An acknowledgement proves someone clicked. A quiz proves they took something in. Attach one to a procedure where getting it wrong matters.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Open the procedure and choose Quiz</strong> — responsible: {user:trainer} · records: quiz.</li>
<li><strong>Write questions about decisions, not trivia</strong> — responsible: Trainer. "The seal is cracked — what do you do?" teaches. "How many bolts are there?" does not.</li>
<li><strong>Give each question one clearly right answer</strong> — responsible: Trainer. Wrong answers should be things people actually do by mistake.</li>
<li><strong>Set the pass mark</strong> — responsible: Trainer. Below it, the assignment stays open and they can take it again.</li>
<li><strong>Attach it to the training method</strong> — responsible: Trainer. Read and understand assignments then end with the quiz instead of a plain signature.</li>
</ol>
<h2>After the quiz</h2>
<p>A pass records the outcome against the assignment and, where the rule asks for one, produces a certificate the person can open from their profile. Results show up in the matrix alongside everything else — see {sop:training}.</p>
<blockquote><p><strong>Note</strong> — if nearly everyone misses the same question, the procedure is usually at fault rather than the people. Check the wording of that step.</p></blockquote>"""
	},
	{
		"slug": "sessions",
		"title": "How to run a classroom or on-the-job session",
		"space": "HR",
		"process": "Recording outcomes",
		"summary": "Book a session, record who came, and sign off the training in one go.",
		"state": "effective",
		"effective_since": -25,
		"tags": ["training"],
		"content": """<h2>Purpose</h2>
<p>Some procedures cannot be learned by reading. A session books the time, covers several procedures at once, and turns attendance into signed-off training.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Open Training sessions and create one</strong> — responsible: {user:trainer} · records: session.</li>
<li><strong>Add the procedures it covers</strong> — responsible: Trainer. A session can cover several; each attendee's assignments for those procedures are closed together.</li>
<li><strong>Invite the attendees</strong> — responsible: Trainer. Pick people, or pull in everyone with an open assignment on those procedures.</li>
<li><strong>Set when and where</strong> — responsible: Trainer. Attendees see it on their profile.</li>
<li><strong>Mark attendance on the day</strong> — responsible: Trainer · records: attendance. Only those actually present.</li>
<li><strong>Record the outcome</strong> — responsible: Trainer · records: training outcome. Competent closes the assignment. Not yet competent leaves it open with a note.</li>
</ol>
<blockquote><p><strong>Warning</strong> — do not sign for someone who left early. The signature says they can do the job, and it is your name on it.</p></blockquote>"""
	},
	{
		"slug": "onboard",
		"title": "Onboarding a new team member",
		"space": "HR",
		"process": "Recording outcomes",
		"summary": "What to do before someone's first day so their training is waiting for them.",
		"state": "draft",
		"tags": ["onboarding"],
		"content": """<h2>Purpose</h2>
<p>A new person should log in on day one and find their reading already queued. That only happens if the account, the role and the team are set up beforehand.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Create the account</strong> — responsible: {user:manager} · records: user account. Do this a day early so the welcome email is not their first-morning problem.</li>
<li><strong>Give them a role</strong> — responsible: Manager. Reader to read and sign. Author to write. Approver to sign off. Trainer to run training. Start at Reader and add more later.</li>
<li><strong>Put them in a team</strong> — responsible: Manager · records: team membership. This is what training rules match on, so a person in no team gets no training.</li>
<li><strong>Check their queue</strong> — responsible: {user:trainer}. Open the Training matrix and filter to their name. Empty means a rule does not cover them — see {sop:training}.</li>
<li><strong>Point them at the basics</strong> — responsible: Manager. {sop:write} for writing, {sop:blocks} for the editor.</li>
</ol>
<blockquote><p><strong>Note</strong> — this procedure is still a draft. It is here to show what a draft looks like next to published ones.</p></blockquote>"""
	},
	{
		"slug": "spaces",
		"title": "How to set up spaces and processes",
		"space": "OPS",
		"process": "Spaces & processes",
		"summary": "The structure everything else hangs off — get it roughly right and leave it alone.",
		"state": "effective",
		"effective_since": -100,
		"tags": ["admin", "getting-started"],
		"content": """<h2>Purpose</h2>
<p>A space is a body of procedures with an owner and a code. A process is a folder inside it. Together they decide procedure numbers, who can see what, and how training rules are scoped.</p>
<h2>Procedure</h2>
<ol>
<li><strong>Create a space per area of work</strong> — responsible: {user:manager} · records: space. Operations, Quality, People. Not one per department that might be reorganised next year.</li>
<li><strong>Choose the code carefully</strong> — responsible: Manager. Two to four letters. It becomes the procedure number — OPS-0001 — and those numbers get printed, quoted and filed, so changing it later is painful.</li>
<li><strong>Set the visibility and the team</strong> — responsible: Manager. The team decides who reads, writes and approves in that space.</li>
<li><strong>Start from a template if one fits</strong> — responsible: Manager. Templates lay out a ready-made process tree — manufacturing, service, office — which you can then prune.</li>
<li><strong>Build the process tree</strong> — responsible: Manager · records: processes. Follow the work in the order it happens. Two levels is usually enough; three is a filing system nobody browses.</li>
<li><strong>Check it against the sidebar</strong> — responsible: Manager. If you cannot guess where a new procedure belongs, neither can anyone else.</li>
</ol>
<blockquote><p><strong>Warning</strong> — deleting a space deletes every procedure in it, with its history. Retire the procedures instead — see {sop:retire}.</p></blockquote>"""
	},
	{
		"slug": "insights",
		"title": "How to read the insights",
		"space": "OPS",
		"process": "Insights & admin",
		"summary": "Which procedures are stale, which are ignored, and which are confusing people.",
		"state": "effective",
		"effective_since": -15,
		"tags": ["admin"],
		"content": """<h2>Purpose</h2>
<p>Insights answers the question a manager actually has: is any of this being used, and where is it going wrong?</p>
<h2>What to look at</h2>
<ol>
<li><strong>Overdue reviews</strong> — responsible: {user:manager}. A procedure past its review date is a procedure nobody has checked against reality. Start with the oldest.</li>
<li><strong>Acknowledgement rate</strong> — responsible: Manager. Published but unsigned means people are working to a version they have not read. Chase it through the matrix in {sop:training}.</li>
<li><strong>Never opened</strong> — responsible: Manager. Either the work is not happening, or people have a better way they are not writing down. Both are worth a conversation.</li>
<li><strong>Clarity feedback</strong> — responsible: Manager. Readers can flag a procedure as unclear from the bottom of the page. A cluster of flags is a rewrite, not a training problem.</li>
<li><strong>Training compliance</strong> — responsible: {user:trainer}. By space and by team, so you can see whether a gap is one person or one department.</li>
</ol>
<blockquote><p><strong>Note</strong> — check this monthly and act on one row. A dashboard that nobody acts on is a slower way of doing nothing.</p></blockquote>"""
	},
]

SHAPES = {
	"Completed": {"method": "Read & Understand", "due": -6, "outcome": "Competent", "done": 1},
	"In Progress": {"method": "On the Job", "due": 6, "outcome": "Pending", "done": 1},
	"Assigned": {"method": "Read & Understand", "due": 12, "outcome": "Pending", "done": 0},
	"Overdue": {"method": "Read & Understand", "due": -9, "outcome": "Pending", "done": 0},
}




def after_migrate():
	if not wanted():
		print("SOP demo data: off. Run `bench --site <site> set-config sop_demo_data 1` to seed it.")
		return

	if seeded():
		return

	result = install(force=1)
	print(f"SOP demo data: created {len(result.get('procedures', []))} procedures in OPS and HR.")


def seeded():
	return bool(frappe.db.exists("SOP Space", {"space_code": ("in", list(DEMO_CODES))}))


def demo_spaces():
	return frappe.get_all(
		"SOP Space",
		filters={"space_code": ("in", list(DEMO_CODES))},
		pluck="name",
		limit_page_length=0,
	)


def summary():
	spaces = frappe.get_all(
		"SOP Space",
		filters={"space_code": ("in", list(DEMO_CODES))},
		fields=["name", "title", "space_code"],
		limit_page_length=0,
	)
	names = [row.name for row in spaces]

	procedures = (
		frappe.get_all("SOP", filters={"space": ("in", names)}, pluck="name", limit_page_length=0)
		if names
		else []
	)

	counts = {}
	if procedures:
		for state in frappe.get_all(
			"SOP", filters={"name": ("in", procedures)}, pluck="status", limit_page_length=0
		):
			counts[state] = counts.get(state, 0) + 1

	return {
		"installed": bool(names),
		"spaces": spaces,
		"procedures": len(procedures),
		"by_status": counts,
		"processes": frappe.db.count("SOP Process", {"space": ("in", names)}) if names else 0,
		"assignments": frappe.db.count("SOP Training Assignment", {"sop": ("in", procedures)})
		if procedures
		else 0,
		"people": [email for email, *_rest in PEOPLE],
		"other_spaces": frappe.db.count("SOP Space") - len(names),
	}


def wanted():
	flag = frappe.conf.get("sop_demo_data")
	return bool(flag) if flag is not None else bool(frappe.conf.get("developer_mode"))


def install(force=0):
	if frappe.db.count("SOP") and not force:
		return {"skipped": "procedures already exist"}

	people = ensure_people()
	ensure_team(people)
	manager = people[0]

	spaces = {
		"OPS": ensure_space(
			manager,
			"Operations",
			"OPS",
			"How the team gets things done — the official way of working.",
		),
		"HR": ensure_space(
			manager, "People & Culture", "HR", "Onboarding, training and team practices."
		),
	}

	seed_app_processes(manager, spaces)

	created = []
	for definition in PROCEDURES:
		created.append(build(definition, spaces, people))

	inject_mentions(created, people)

	seed_training(spaces["OPS"], people)
	seed_session(people)
	frappe.db.commit()

	return {"space": list(spaces.values()), "procedures": created, "people": [p[0] for p in PEOPLE]}


def ensure_people():
	people = []

	for email, first, last, roles in PEOPLE:
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first,
					"last_name": last,
					"send_welcome_email": 0,
					"user_type": "System User",
				}
			)
			user.flags.ignore_permissions = True
			user.insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", email)

		for role in roles:
			if frappe.db.exists("Role", role) and role not in [row.role for row in user.roles]:
				user.append("roles", {"role": role})

		user.save(ignore_permissions=True)
		people.append(email)

	return people


def ensure_team(people):
	wanted = [
		(people[0], "Approver"),
		(frappe.session.user, "Approver"),
		(people[2], "Reviewer"),
		(people[1], "Author"),
		(people[3], "Reader"),
	]

	if frappe.db.exists("SOP Team", TEAM):
		doc = frappe.get_doc("SOP Team", TEAM)
	else:
		doc = frappe.get_doc(
			{
				"doctype": "SOP Team",
				"team_name": TEAM,
				"description": "Everyone who works a line, plus the supervisors who sign for them.",
			}
		)

	present = {row.user for row in doc.members}
	for user, role in wanted:
		if user not in present:
			doc.append("members", {"user": user, "team_role": role})
			present.add(user)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return doc.name


def ensure_space(manager, title, code, description, template=None):
	existing = frappe.db.get_value("SOP Space", {"space_code": code}, "name")
	if existing:
		return existing

	space = as_user(
		manager,
		procedures_api.create_space,
		title=title,
		space_code=code,
		description=description,
		template=template,
		team=TEAM,
	)

	return space["name"]


def seed_app_processes(manager, spaces):
	for index, (code, group, children) in enumerate(APP_PROCESSES, start=1):
		space = spaces[code]
		parent = ensure_process(manager, space, group, None, index * 10)

		for position, child in enumerate(children, start=1):
			ensure_process(manager, space, child, parent, position * 10)


def ensure_process(manager, space, title, parent, sequence):
	existing = frappe.db.get_value(
		"SOP Process", {"space": space, "title": title, "parent_process": parent}, "name"
	)
	if existing:
		return existing

	process = as_user(
		manager,
		processes_api.create_process,
		title=title,
		space=space,
		parent=parent,
		sequence=sequence,
	)

	return process["name"]


def build(definition, spaces, people):
	space = spaces[definition["space"]]
	process = frappe.db.get_value(
		"SOP Process", {"space": space, "title": definition["process"]}, "name"
	)

	draft = as_user(
		people[1],
		procedures_api.save_draft,
		space=space,
		title=definition["title"],
		summary=definition["summary"],
		content=definition["content"],
		process=process,
		risk_level="Medium",
		is_controlled=1,
	)

	for tag in definition["tags"]:
		add_tag(tag, "SOP", draft["name"])

	advance(draft["name"], definition["state"], people, definition.get("effective_since", -40))

	return draft["name"]


def inject_mentions(created, people):
	slug_to_name = {d["slug"]: sop for d, sop in zip(PROCEDURES, created)}

	user_map = {
		"manager": people[0],
		"author":  people[1],
		"trainer": people[2],
		"reader":  people[3],
	}

	for sop_name in created:
		doc = frappe.get_doc("SOP", sop_name)
		content = doc.content or ""
		changed = False

		for slug, target_name in slug_to_name.items():
			placeholder = f"{{sop:{slug}}}"
			if placeholder in content:
				title = frappe.db.get_value("SOP", target_name, "title")
				link = f'<a href="#mention:SOP:{target_name}">{title}</a>'
				content = content.replace(placeholder, link)
				changed = True

		for role, email in user_map.items():
			placeholder = f"{{user:{role}}}"
			if placeholder in content:
				full_name = frappe.db.get_value("User", email, "full_name") or email
				link = f'<a href="#mention:User:{email}">{full_name}</a>'
				content = content.replace(placeholder, link)
				changed = True

		if changed:
			frappe.db.set_value("SOP", sop_name, "content", content, update_modified=False)


def add_tag(tag, doctype, name):
	from frappe.desk.doctype.tag.tag import add_tag as tag_it

	tag_it(tag, doctype, name)


def advance(sop, state, people, since=-40):
	if state == "draft":
		return

	as_user(people[1], lifecycle.send_for_approval, sop)

	if state == "in_review":
		as_user(
			people[2],
			review_api.add_comment,
			sop,
			"Name the form this produces — an operator should not have to guess.",
		)
		return

	for approver in frappe.get_all(
		"SOP Approval",
		filters={"parent": sop, "parenttype": "SOP"},
		pluck="approver",
		order_by="idx asc",
		limit_page_length=0,
	):
		as_user(approver, lifecycle.decide, sop, "Approved", "Reads correctly.")

	if state == "approved":
		return

	as_user(
		people[0],
		lifecycle.publish,
		sop,
		effective_from=add_days(nowdate(), since),
		change_summary="First controlled issue.",
		is_material=1,
	)

	if state == "retired":
		as_user(
			people[0],
			lifecycle.retire,
			sop,
			"Superseded by the plant-wide sampling procedure.",
		)
		return

	sign(sop, people[2:])


def as_user(user, fn, *args, **kwargs):
	original = frappe.session.user
	frappe.set_user(user)

	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user(original)


def sign(sop, users):
	version = frappe.db.get_value("SOP", sop, "version")

	for user in users:
		as_user(user, procedures_api.acknowledge, sop, version)


def seed_training(space, people):
	manager, author, trainer, reader = people
	requirement = ensure_requirement(manager, space)

	effective = frappe.get_all(
		"SOP", filters={"space": space, "status": "Effective"}, pluck="name",
		order_by="creation asc", limit_page_length=5,
	)
	if not effective:
		return

	trainees = [frappe.session.user, author, trainer, reader]

	for index, sop in enumerate(effective):
		for position, trainee in enumerate(trainees):
			state = ("Completed", "In Progress", "Assigned", "Overdue")[(index + position) % 4]
			assign(manager, trainer, sop, trainee, state)

	as_user(manager, requirements_api.run_requirement, requirement)


def ensure_requirement(manager, space):
	existing = frappe.db.get_value(
		"SOP Training Requirement", {"scope": "Space", "space": space, "applies_to": "Team"}, "name"
	)
	if existing:
		return existing

	requirement = as_user(
		manager,
		requirements_api.save_requirement,
		enabled=1,
		applies_to="Team",
		team=TEAM,
		scope="Space",
		space=space,
		method="Read & Understand",
		due_days=14,
		refresher_months=12,
	)

	return requirement["name"]


def assign(manager, trainer, sop, trainee, state):
	shape = SHAPES[state]

	created = as_user(
		manager,
		training_api.assign,
		sop=sop,
		trainees=[trainee],
		method=shape["method"],
		due_days=shape["due"],
	)
	if not created:
		return None

	name = created[0]

	for idx in range(1, shape["done"] + 1):
		as_user(trainee, training_api.complete_task, name, idx)

	if shape["outcome"] != "Pending":
		assessor = manager if trainee == trainer else trainer
		as_user(assessor, training_api.record_outcome, name, shape["outcome"])

	return name


def seed_session(people):
	manager, author, trainer, reader = people

	covered = frappe.get_all(
		"SOP", filters={"status": "Effective"}, pluck="name", order_by="creation asc",
		limit_page_length=2,
	)
	if not covered or frappe.db.count("SOP Training Session"):
		return

	as_user(
		trainer,
		sessions_api.save_session,
		title="Line clearance refresher",
		trainer=trainer,
		scheduled_on=f"{add_days(nowdate(), 5)} 09:30:00",
		location="Training room, block B",
		method="Classroom",
		procedures=covered,
		attendees=[author, reader],
		notes="Walk the line after the classroom half. Bring a spare clearance record.",
	)


def status():
	return {
		"user": frappe.session.user,
		"developer_mode": bool(frappe.conf.get("developer_mode")),
		"demo_enabled": wanted(),
		"spaces": frappe.get_all("SOP Space", fields=["name", "title", "space_code", "visibility"], limit_page_length=0),
		"processes": frappe.db.count("SOP Process"),
		"procedures": frappe.db.count("SOP"),
		"by_status": by_status(),
		"acknowledgements": frappe.db.count("SOP Acknowledgement"),
		"assignments": frappe.db.count("SOP Training Assignment"),
		"can_read_spaces": frappe.has_permission("SOP Space", "read"),
		"spaces_api": len(frappe.call("sop.api.procedures.spaces")),
		"last_error": last_error(),
	}


def by_status():
	counts = {}
	for status in frappe.get_all("SOP", pluck="status", limit_page_length=0):
		counts[status] = counts.get(status, 0) + 1

	return counts


def last_error():
	rows = frappe.get_all(
		"Error Log",
		filters={"method": ("like", "%SOP demo%")},
		fields=["creation", "error"],
		order_by="creation desc",
		limit_page_length=1,
	)
	if not rows:
		return None

	return {"at": str(rows[0].creation), "tail": (rows[0].error or "").strip().splitlines()[-6:]}


def clear():
	frappe.flags.sop_removal = True

	try:
		return wipe_demo()
	finally:
		frappe.flags.sop_removal = False


def wipe_demo():
	spaces = demo_spaces()
	if not spaces:
		return {"cleared": 0, "spaces": []}

	procedures = frappe.get_all("SOP", filters={"space": ("in", spaces)}, pluck="name", limit_page_length=0)

	assignments = frappe.get_all(
		"SOP Training Assignment",
		filters={"sop": ("in", procedures or [""])},
		pluck="name",
		limit_page_length=0,
	)

	for doctype, field in (
		("SOP Training Assignment", "sop"),
		("SOP Acknowledgement", "sop"),
		("SOP Revision", "sop"),
		("SOP Review Comment", "sop"),
	):
		for name in frappe.get_all(doctype, filters={field: ("in", procedures or [""])}, pluck="name", limit_page_length=0):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)

	for name in procedures:
		frappe.delete_doc("SOP", name, force=True, ignore_permissions=True)

	for name in frappe.get_all(
		"SOP Training Requirement", filters={"space": ("in", spaces)}, pluck="name",
		limit_page_length=0,
	):
		frappe.delete_doc("SOP Training Requirement", name, force=True, ignore_permissions=True)

	for name in deepest_first(spaces):
		frappe.delete_doc("SOP Process", name, force=True, ignore_permissions=True)

	frappe.db.delete(
		"Notification Log",
		{
			"document_type": ("in", ["SOP", "SOP Training Assignment"]),
			"document_name": ("in", (procedures + assignments) or [""]),
		},
	)

	for name in sessions_covering(procedures):
		frappe.delete_doc("SOP Training Session", name, force=True, ignore_permissions=True)

	for name in spaces:
		frappe.delete_doc("SOP Space", name, force=True, ignore_permissions=True)

	frappe.db.commit()

	return {"cleared": len(procedures), "spaces": spaces}


def reset():
	cleared = clear()
	seeded = install(force=1)

	return {"cleared": cleared, "seeded": seeded, "status": status()}


def sessions_covering(procedures):
	if not procedures:
		return []

	return list(
		set(
			frappe.get_all(
				"SOP Session Procedure",
				filters={"sop": ("in", procedures), "parenttype": "SOP Training Session"},
				pluck="parent",
				limit_page_length=0,
			)
		)
	)


def deepest_first(spaces):
	rows = frappe.get_all(
		"SOP Process", filters={"space": ("in", spaces)}, fields=["name", "parent_process"],
		limit_page_length=0,
	)
	depth = {row.name: 0 for row in rows}
	parents = {row.name: row.parent_process for row in rows}

	for name in depth:
		current = parents.get(name)
		while current in parents:
			depth[name] += 1
			current = parents.get(current)

	return sorted(depth, key=lambda name: -depth[name])
