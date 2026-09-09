// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Testing Entrustment", {
	refresh(frm) {
		setup_contact_query(frm);

		if (frm.doc.docstatus === 0 && frm.doc.sales_order) {
			frm.add_custom_button(
				__("从定单导入试验项目"),
				() => import_items_from_sales_order(frm),
				__("来源")
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
				__("新建报告"),
				() => {
					frappe.route_options = { entrustment: frm.doc.name };
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

function import_items_from_sales_order(frm) {
	if (!frm.doc.sales_order) {
		frappe.msgprint(__("请先在「来源与关联」中选择销售定单"));
		return;
	}
	if (frm.doc.items && frm.doc.items.length) {
		frappe.confirm(
			__("导入会覆盖当前试验/检测项目,是否继续?"),
			() => call_sales_order_import(frm)
		);
		return;
	}
	call_sales_order_import(frm);
}

function call_sales_order_import(frm) {
	frappe.call({
		method:
			"test.testing.doctype.testing_entrustment.testing_entrustment.get_sales_order_items",
		args: { sales_order: frm.doc.sales_order },
		callback(r) {
			if (!r.message) return;

			frm.clear_table("items");
			(r.message.items || []).forEach((row) => {
				frm.add_child("items", row);
			});

			if (r.message.customer && !frm.doc.customer) {
				frm.set_value("customer", r.message.customer);
			}
			if (r.message.contact && !frm.doc.contact) {
				frm.set_value("contact", r.message.contact);
			}
			if (r.message.company && !frm.doc.company) {
				frm.set_value("company", r.message.company);
			}
			if (r.message.transaction_date) {
				frm.set_value("transaction_date", r.message.transaction_date);
			}

			frm.refresh_field("items");
			frappe.show_alert({
				message: __("已从定单 {0} 导入 {1} 个试验/检测项目", [
					frm.doc.sales_order,
					r.message.items.length,
				]),
				indicator: "green",
			});
		},
	});
}
