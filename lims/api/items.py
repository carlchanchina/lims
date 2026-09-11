# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""检测项目(ERPNext Item):可以选已有的,也可以新建。"""

import frappe

from lims.api.security import ALL_STAFF_ROLES, require_roles
from lims.integrations.erpnext_masters import (
	create_item as create_erpnext_item,
	item_form_options,
)

ITEM_FIELDS = [
	"name",
	"item_name",
	"item_group",
	"stock_uom",
	"is_stock_item",
	"is_fixed_asset",
	"disabled",
	"description",
]


@frappe.whitelist()
def list_items(txt=None, page=0, page_length=50):
	require_roles(ALL_STAFF_ROLES)
	txt = (txt or "").strip()
	or_filters = None
	if txt:
		or_filters = [
			["name", "like", f"%{txt}%"],
			["item_name", "like", f"%{txt}%"],
			["item_group", "like", f"%{txt}%"],
		]
	return frappe.get_list(
		"Item",
		or_filters=or_filters,
		fields=ITEM_FIELDS,
		order_by="item_name asc",
		start=int(page or 0),
		page_length=int(page_length or 50),
		ignore_permissions=True,
	)


@frappe.whitelist()
def create_item(data=None):
	"""新建检测项目:写到 ERPNext Item。"""
	require_roles(ALL_STAFF_ROLES)
	if isinstance(data, str):
		data = frappe.parse_json(data) or {}
	name = create_erpnext_item(data or {})
	row = frappe.db.get_value(
		"Item", name, ["name", "item_name", "stock_uom"], as_dict=True
	)
	return {
		"name": row.name,
		"value": row.name,
		"label": f"{row.name} - {row.item_name or ''}".strip(" -"),
	}


@frappe.whitelist()
def get_item_form_options():
	require_roles(ALL_STAFF_ROLES)
	return item_form_options()
