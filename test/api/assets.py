# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe

from test.api.security import ALL_STAFF_ROLES, require_roles
from test.integrations.erpnext_masters import (
	custodian_options,
	fixed_asset_item_options,
	location_options,
)
from test.integrations.erpnext_masters import create_asset as create_erpnext_asset

ASSET_FIELDS = [
	"name",
	"asset_name",
	"item_code",
	"asset_category",
	"status",
	"location",
	"custodian",
	"company",
]


def _asset_option(name):
	row = frappe.db.get_value("Asset", name, ["name", "asset_name", "item_code"], as_dict=True)
	if not row:
		return {"name": name, "value": name, "label": name}
	return {
		"name": row.name,
		"value": row.name,
		"label": f"{row.name} - {row.asset_name or row.item_code or ''}".strip(" -"),
	}


@frappe.whitelist()
def list_assets(txt=None):
	"""ERPNext Asset 作为检测设备主数据。"""
	require_roles(ALL_STAFF_ROLES)
	or_filters = None
	if txt:
		or_filters = [
			["name", "like", f"%{txt}%"],
			["asset_name", "like", f"%{txt}%"],
			["item_code", "like", f"%{txt}%"],
			["location", "like", f"%{txt}%"],
		]
	return frappe.get_list(
		"Asset",
		or_filters=or_filters,
		fields=ASSET_FIELDS,
		order_by="asset_name asc",
		limit_page_length=50,
		ignore_permissions=True,
	)


@frappe.whitelist()
def create_asset(data=None):
	"""新建设备:先写 ERPNext Asset(登记已有设备),返回可直接选中的值。"""
	require_roles(ALL_STAFF_ROLES)
	if isinstance(data, str):
		data = frappe.parse_json(data) or {}
	name = create_erpnext_asset(data or {})
	return _asset_option(name)


@frappe.whitelist()
def asset_form_options():
	"""新建设备表单要用的下拉项:固定资产 Item / 位置 / 保管人 / 公司。"""
	require_roles(ALL_STAFF_ROLES)
	companies = frappe.get_all("Company", fields=["name"], order_by="name")
	default_company = frappe.defaults.get_user_default("Company") or (
		companies[0].name if companies else ""
	)
	return {
		"items": fixed_asset_item_options(),
		"locations": location_options(),
		"custodians": custodian_options(),
		"companies": companies,
		"defaults": {"company": default_company},
	}
