// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Test Report", {
	refresh(frm) {
		setup_sample_query(frm);
		if (!frm.is_new() && frm.doc.test_request) {
			frm.add_custom_button(
				__("打开检测请求"),
				() => frappe.set_route("Form", "Test Request", frm.doc.test_request),
				__("关联")
			);
		}
	},

	test_request(frm) {
		setup_sample_query(frm);
		if (frm.doc.sample) {
			frm.set_value("sample", null);
		}
	},
});

function setup_sample_query(frm) {
	frm.set_query("sample", () => ({
		query: "lims.testing.doctype.test_report.test_report.request_sample_query",
		filters: { test_request: frm.doc.test_request || "" },
	}));
}
