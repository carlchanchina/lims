# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	"""Runs once after the app is installed on a site."""
	create_roles()
	sync_custom_fields()


def create_roles():
	"""Create app roles referenced by Doctype permissions."""
	for role in ("Testing Manager", "Testing User"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)


def sync_custom_fields():
	"""
	Keep app-owned fields on ERPNext DocTypes in sync.

	ERPNext remains the source of truth. This app only adds a back-reference
	field on Quotation so that a generated quote points back to the Testing
	Entrustment document.
	"""
	create_custom_fields(
		{
			"Quotation": [
				{
					"fieldname": "testing_entrustment",
					"label": "检测委托",
					"fieldtype": "Link",
					"options": "Testing Entrustment",
					"insert_after": "transaction_date",
					"no_copy": 1,
					"in_list_view": 0,
					"print_hide": 1,
					"description": "由「创建报价」按钮自动关联的检测委托单",
				}
			]
		},
		ignore_validate=True,
	)
