// Copyright (c) 2026, Leo Daniel and contributors
// For license information, please see license.txt

frappe.ui.form.on("SOP Resource", {
	setup(frm) {
		frm.set_query("parent_sop_resource", () => ({
			filters: { resource_type: frm.doc.resource_type || "", is_group: 1, name: ["!=", frm.doc.name || ""] },
		}));
	},

	refresh(frm) {
		apply_type(frm, false);
	},

	resource_type(frm) {
		frm.set_value("parent_sop_resource", null);
		apply_type(frm, true);
	},
});

function apply_type(frm, refill) {
	const type = frm.doc.resource_type;
	if (!type) {
		show(frm, {});
		return;
	}

	frappe.call({
		method: "sop.resources.type_settings",
		args: { resource_type: type },
		callback({ message }) {
			show(frm, message || {});
			if (refill) fill_values(frm, message.attributes || []);
		},
	});
}

function show(frm, settings) {
	const tree = Boolean(settings.is_tree);
	frm.toggle_display(["parent_sop_resource", "is_group"], tree);
	frm.toggle_display("is_consumable", Boolean(settings.can_be_issued));
	frm.toggle_display("section_break_values", Boolean((settings.attributes || []).length));

	frm.toggle_display("document", Boolean(settings.document_label));
	frm.toggle_display("check_date", Boolean(settings.review_label));
	frm.toggle_display("section_break_document", Boolean(settings.document_label || settings.review_label));
	if (settings.document_label) frm.set_df_property("document", "label", settings.document_label);
	if (settings.review_label) frm.set_df_property("check_date", "label", settings.review_label);
}

function fill_values(frm, attributes) {
	const entered = {};
	(frm.doc.values || []).forEach((row) => {
		entered[(row.attribute || "").trim().toLowerCase()] = row.value;
	});

	frm.clear_table("values");
	attributes.forEach((attribute) => {
		const row = frm.add_child("values");
		row.attribute = attribute.label;
		row.value = entered[attribute.label.trim().toLowerCase()] || "";
	});
	frm.refresh_field("values");
}
