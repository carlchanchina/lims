// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Test Report", {
	refresh(frm) {
		setup_sample_query(frm);
		if (!frm.is_new() && frm.doc.entrustment) {
			frm.add_custom_button(
				__("打开检测委托"),
				() => frappe.set_route("Form", "Testing Entrustment", frm.doc.entrustment),
				__("关联")
			);
		}
	},

	entrustment(frm) {
		setup_sample_query(frm);
		if (frm.doc.sample) {
			frm.set_value("sample", null);
		}
	},
});

function setup_sample_query(frm) {
	if (!frm.doc.entrustment) return;
	frm.set_query("sample", () => ({
		filters: { entrustment: frm.doc.entrustment },
	}));
}
