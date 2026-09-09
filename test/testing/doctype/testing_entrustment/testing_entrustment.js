// Copyright (c) 2026, Carl and contributors
// For license information, please see license.txt

frappe.ui.form.on("Testing Entrustment", {
	refresh(frm) {
		setup_contact_query(frm);

		frm.remove_custom_button(__("创建报价"));
		if (frm.doc.docstatus === 1 && !frm.doc.quotation) {
			frm.add_custom_button(__("创建报价"), () => create_quotation(frm), __("创建"));
		}
	},

	customer(frm) {
		setup_contact_query(frm);
		if (frm.doc.contact) {
			frm.set_value("contact", null);
		}
	},
});

frappe.ui.form.on("Testing Entrustment Item", {
	qty(frm, cdt, cdn) {
		recalculate_row_amount(frm, cdt, cdn);
	},

	rate(frm, cdt, cdn) {
		recalculate_row_amount(frm, cdt, cdn);
	},

	items_remove(frm) {
		recalculate_total(frm);
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

function recalculate_row_amount(frm, cdt, cdn) {
	const row = frappe.get_doc(cdt, cdn);
	row.amount = flt(row.qty) * flt(row.rate);
	frm.refresh_field("items");
	recalculate_total(frm);
}

function recalculate_total(frm) {
	let total = 0;
	(frm.doc.items || []).forEach((row) => {
		total += flt(row.amount);
	});
	frm.set_value("estimated_amount", flt(total));
}

function create_quotation(frm) {
	frappe.xcall(
		"test.testing.doctype.testing_entrustment.testing_entrustment.create_quotation",
		{ name: frm.doc.name }
	).then((quotation) => {
		frappe.show_alert(
			{
				message: __("报价单 {0} 已创建", [quotation]),
				indicator: "green",
			},
			5
		);
		frappe.set_route("Form", "Quotation", quotation);
	});
}
