// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Test Request", {
	refresh(frm) {
		setup_contact_query(frm);
		setup_sample_query(frm);

		if (frm.doc.name && frm.doc.items && frm.doc.items.length && !frm.doc.quotation) {
			frm.add_custom_button(__("生成报价"), () => create_quotation(frm), __("报价"));
		}
		if (frm.doc.quotation) {
			frm.add_custom_button(
				__("打开报价单"),
				() => frappe.set_route("Form", "Quotation", frm.doc.quotation),
				__("关联")
			);
		}
		if (frm.doc.sales_order) {
			frm.add_custom_button(
				__("打开销售定单"),
				() => frappe.set_route("Form", "Sales Order", frm.doc.sales_order),
				__("关联")
			);
		}
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("新建样品"),
				() => {
					frappe.route_options = { test_request: frm.doc.name };
					frappe.new_doc("Sample");
				},
				__("检测业务")
			);
			frm.add_custom_button(
				__("新建报告"),
				() => {
					frappe.route_options = { test_request: frm.doc.name };
					frappe.new_doc("Test Report");
				},
				__("检测业务")
			);
		}
	},

	customer(frm) {
		setup_contact_query(frm);
		if (frm.doc.contact) {
			frm.set_value("contact", null);
		}
	},
});

function setup_contact_query(frm) {
	if (!frm.doc.customer) return;
	frm.set_query("contact", () => ({
		query: "frappe.contacts.doctype.contact.contact.contact_query",
		filters: {
			link_doctype: "Customer",
			link_name: frm.doc.customer,
		},
	}));
}

function setup_sample_query(frm) {
	if (!frm.doc.name) {
		frm.set_query("sample", "items", () => ({ filters: { name: "" } }));
		return;
	}
	frm.set_query("sample", "items", () => ({
		query: "test.testing.doctype.test_request.test_request.sample_query",
		filters: { test_request: frm.doc.name },
	}));
}

function create_quotation(frm) {
	frappe.confirm(
		__("将按 Test Catalog 价格生成 ERPNext 报价单,是否继续?"),
		() => {
			frappe.xcall(
				"test.testing.doctype.test_request.test_request.create_quotation",
				{ name: frm.doc.name }
			).then((quotation) => {
				frappe.show_alert({
					message: __("报价单 {0} 已生成", [quotation]),
					indicator: "green",
				});
				frm.reload_doc();
			});
		}
	);
}
