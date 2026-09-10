# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission


def after_install():
	"""Runs once after the app is installed on a site."""
	run_schema_cleanup()
	backfill_parties()


def run_schema_cleanup():
	"""安装与每次 migrate 后执行,保证角色/字段状态与当前版本一致。"""
	create_roles()
	sync_custom_fields()
	grant_erpnext_read_permissions()
	remove_legacy_quotation_link_field()


def backfill_parties():
	from test.integrations.erpnext_party import backfill_parties as _backfill

	_backfill()


def create_roles():
	"""Create app roles referenced by Doctype permissions."""
	for role in ("Testing Manager", "Testing User"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc(
				{"doctype": "Role", "role_name": role, "desk_access": 1}
			).insert(ignore_permissions=True)


def sync_custom_fields():
	"""LIMS 需要写回 ERPNext Quotation Item 的试验属性。"""
	create_custom_fields(
		{
			"Quotation Item": [
				{
					"fieldname": "test_catalog",
					"label": "检测目录",
					"fieldtype": "Link",
					"options": "Test Catalog",
					"insert_after": "item_code",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "equipment",
					"label": "设备(Asset)",
					"fieldtype": "Link",
					"options": "Asset",
					"insert_after": "test_catalog",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "hours",
					"label": "试验时长(h)",
					"fieldtype": "Float",
					"insert_after": "equipment",
					"read_only": 1,
					"no_copy": 1,
				},
				{
					"fieldname": "cycles",
					"label": "循环次数",
					"fieldtype": "Float",
					"insert_after": "hours",
					"read_only": 1,
					"no_copy": 1,
				},
			]
		},
		ignore_validate=True,
	)


def grant_erpnext_read_permissions():
	"""让 Testing 角色能读取 LIMS 依赖的 ERPNext 主数据。"""
	for doctype in (
		"Customer",
		"Contact",
		"Item",
		"Asset",
		"Project",
		"Quotation",
		"Sales Order",
	):
		for role in ("Testing Manager", "Testing User"):
			try:
				add_permission(doctype, role)
			except Exception:
				pass


def remove_legacy_quotation_link_field():
	"""清理早期版本加在 Quotation 上的回链字段。"""
	field_name = frappe.db.exists(
		"Custom Field",
		{"dt": "Quotation", "fieldname": "testing_entrustment"},
	)
	if field_name:
		frappe.delete_doc("Custom Field", field_name, force=1)
