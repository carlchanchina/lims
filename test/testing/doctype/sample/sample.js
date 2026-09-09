// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Sample", {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.entrustment) {
			frm.add_custom_button(
				__("打开检测委托"),
				() => frappe.set_route("Form", "Testing Entrustment", frm.doc.entrustment),
				__("关联")
			);
			frm.add_custom_button(
				__("新建报告"),
				() => {
					frappe.route_options = {
						entrustment: frm.doc.entrustment,
						sample: frm.doc.name,
					};
					frappe.new_doc("Test Report");
				},
				__("检测业务")
			);
		}
	},
});
