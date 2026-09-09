# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe


def after_install():
	"""Runs once after the app is installed on a site."""
	run_schema_cleanup()


def run_schema_cleanup():
	"""安装与每次 migrate 后执行,保证角色/字段状态与当前版本一致。"""
	create_roles()
	remove_legacy_quotation_link_field()


def create_roles():
	"""Create app roles referenced by Doctype permissions."""
	for role in ("Testing Manager", "Testing User"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)


def remove_legacy_quotation_link_field():
	"""
	清理早期版本加在 Quotation 上的回链字段。

	当前版本改为「定单 → 委托单」方向,委托单不再与 Quotation 双向打通,
	Sales Order 也保持 ERPNext 原样。
	"""
	field_name = frappe.db.exists(
		"Custom Field",
		{"dt": "Quotation", "fieldname": "testing_entrustment"},
	)
	if field_name:
		frappe.delete_doc("Custom Field", field_name, force=1)
