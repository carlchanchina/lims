# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles


@frappe.whitelist()
def customer_search(txt=None):
	require_roles(ALL_STAFF_ROLES)
	txt = (txt or "").strip()
	filters = {"name": ["like", f"%{txt}%"]} if txt else {}
	docs = frappe.get_list(
		"Customer",
		filters=filters,
		fields=["name", "customer_name"],
		order_by="customer_name",
		limit_page_length=20,
	)
	return [{"value": d.name, "label": f"{d.name} - {d.customer_name}"} for d in docs]


@frappe.whitelist()
def item_search(txt=None):
	require_roles(ALL_STAFF_ROLES)
	txt = (txt or "").strip()
	filters = {"name": ["like", f"%{txt}%"]} if txt else {}
	docs = frappe.get_list(
		"Item",
		filters=filters,
		fields=["name", "item_name"],
		order_by="item_name",
		limit_page_length=20,
	)
	return [{"value": d.name, "label": f"{d.name} - {d.item_name}"} for d in docs]


@frappe.whitelist()
def company_options():
	require_roles(ALL_STAFF_ROLES)
	docs = frappe.get_all("Company", fields=["name"], order_by="name")
	return [{"value": d.name, "label": d.name} for d in docs]


@frappe.whitelist()
def get_erpnext_url(doctype, name):
	require_roles(ALL_STAFF_ROLES)
	return f"/app/{doctype.replace(' ', '-').lower()}/{name}"
