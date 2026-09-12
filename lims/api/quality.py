# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""质量相关:设备使用记录 + 不符合/异常记录。"""

import frappe
from frappe.utils import today

from lims.api.security import ALL_STAFF_ROLES, require_roles
from lims.integrations.erpnext_masters import asset_calibration_state

USAGE_FIELDS = [
	"name",
	"asset",
	"used_by",
	"from_datetime",
	"to_datetime",
	"test_request",
	"test_request_item",
	"task",
	"remarks",
]

NONCONFORMANCE_FIELDS = [
	"name",
	"test_request",
	"test_request_item",
	"report",
	"source",
	"severity",
	"status",
	"description",
	"action",
	"owner_user",
	"closed_on",
	"remarks",
]


def _as_dict(value):
	if isinstance(value, str):
		return frappe.parse_json(value) or {}
	return value or {}


@frappe.whitelist()
def list_equipment_usage(test_request=None):
	require_roles(ALL_STAFF_ROLES)
	filters = {"test_request": test_request} if test_request else {}
	return frappe.get_all(
		"Equipment Usage",
		filters=filters,
		fields=USAGE_FIELDS,
		order_by="from_datetime desc",
		limit_page_length=100,
	)


@frappe.whitelist()
def create_equipment_usage(data=None):
	require_roles(ALL_STAFF_ROLES)
	data = _as_dict(data)
	doc = frappe.new_doc("Equipment Usage")
	for field in USAGE_FIELDS:
		if field in data:
			doc.set(field, data[field])
	doc.insert(ignore_permissions=True)
	return {"name": doc.name}


@frappe.whitelist()
def calibration_states(assets=None):
	"""一次查多台设备的校准状态,给排产/选设备时提示用。"""
	require_roles(ALL_STAFF_ROLES)
	if isinstance(assets, str):
		assets = frappe.parse_json(assets) or []
	return {asset: asset_calibration_state(asset) for asset in (assets or [])}


@frappe.whitelist()
def list_nonconformances(test_request=None):
	require_roles(ALL_STAFF_ROLES)
	filters = {"test_request": test_request} if test_request else {}
	return frappe.get_all(
		"Test Nonconformance",
		filters=filters,
		fields=NONCONFORMANCE_FIELDS,
		order_by="modified desc",
		limit_page_length=100,
	)


@frappe.whitelist()
def save_nonconformance(data=None):
	require_roles(ALL_STAFF_ROLES)
	data = _as_dict(data)
	name = data.get("name")
	doc = (
		frappe.get_doc("Test Nonconformance", name)
		if name
		else frappe.new_doc("Test Nonconformance")
	)
	for field in NONCONFORMANCE_FIELDS:
		if field in data:
			doc.set(field, data[field])
	if doc.status == "已关闭" and not doc.closed_on:
		doc.closed_on = today()
	doc.save(ignore_permissions=True)
	return {"name": doc.name}
