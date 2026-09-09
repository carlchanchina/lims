// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sample", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.test_request) {
			frm.add_custom_button(
				__("打开检测请求"),
				() => frappe.set_route("Form", "Test Request", frm.doc.test_request),
				__("关联")
			);
			frm.add_custom_button(
				__("新建报告"),
				() => {
					frappe.route_options = {
						test_request: frm.doc.test_request,
						sample: frm.doc.name,
					};
					frappe.new_doc("Test Report");
				},
				__("检测业务")
			);
		}
	},
});
