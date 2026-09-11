# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""LIMS 里新建的主数据,直接写到 ERPNext,再同步回 LIMS 镜像表。

和 erpnext_party.py 的分工:那边负责 ERPNext -> LIMS 的镜像同步,这里负责
LIMS -> ERPNext 的写入。事实源永远是 ERPNext:所以这里先建 ERPNext 单据,
镜像表由 Customer/Contact 的 doc_events 钩子(或调用方显式补一次)刷新。
"""

import frappe
from frappe.utils import flt, today


def default_customer_group():
	return (
		frappe.db.get_single_value("Selling Settings", "customer_group")
		or "All Customer Groups"
	)


def default_territory():
	return (
		frappe.db.get_single_value("Selling Settings", "territory")
		or "All Territories"
	)


def create_customer(data):
	"""新建 ERPNext Customer,可顺带建一个主要联系人并挂到该客户上。

	客户名称重复时直接报错,避免和 ERPNext 里已有的记录并行成两条。
	"""
	data = data or {}
	customer_name = (data.get("customer_name") or "").strip()
	if not customer_name:
		frappe.throw("请填写客户名称")
	if frappe.db.exists("Customer", {"customer_name": customer_name}):
		frappe.throw(f"客户「{customer_name}」已存在,请直接搜索选择")

	doc = frappe.new_doc("Customer")
	doc.customer_name = customer_name
	doc.customer_type = data.get("customer_type") or "Company"
	doc.customer_group = data.get("customer_group") or default_customer_group()
	doc.territory = data.get("territory") or default_territory()
	doc.insert(ignore_permissions=True)

	contact = data.get("contact") or {}
	if contact.get("first_name") or contact.get("email") or contact.get("phone"):
		create_contact({**contact, "customer": doc.name})

	return doc.name


def create_contact(data):
	"""新建 ERPNext Contact,可挂到一个客户上。

	邮箱已存在时复用那条联系人(并补挂客户),不重复建,和 helpdesk 的
	create_contact 行为一致。
	"""
	data = data or {}
	first_name = (data.get("first_name") or data.get("full_name") or "").strip()
	email = (data.get("email") or data.get("email_id") or "").strip()
	phone = (data.get("phone") or data.get("mobile_no") or "").strip()
	customer = data.get("customer")

	if not (first_name or email):
		frappe.throw("请填写联系人姓名或邮箱")
	if not first_name:
		first_name = email.split("@")[0]

	if email:
		existing = frappe.db.get_value("Contact", {"email_id": email}, "name")
		if existing:
			if customer:
				link_contact_to_customer(existing, customer)
			return existing

	doc = frappe.new_doc("Contact")
	doc.first_name = first_name
	if data.get("last_name"):
		doc.last_name = data["last_name"]
	if data.get("designation"):
		doc.designation = data["designation"]
	if email:
		doc.append("email_ids", {"email_id": email, "is_primary": 1})
	if phone:
		doc.append(
			"phone_nos",
			{"phone": phone, "is_primary_phone": 1, "is_primary_mobile_no": 1},
		)
	if customer:
		doc.append("links", {"link_doctype": "Customer", "link_name": customer})

	doc.insert(ignore_permissions=True)
	return doc.name


def link_contact_to_customer(contact, customer):
	"""把已有联系人挂到客户上(Contact 的 links 子表,ERPNext 原生关系)。"""
	if not contact or not customer:
		return
	if frappe.db.exists(
		"Dynamic Link",
		{
			"parenttype": "Contact",
			"parent": contact,
			"link_doctype": "Customer",
			"link_name": customer,
		},
	):
		return
	doc = frappe.get_doc("Contact", contact)
	doc.append("links", {"link_doctype": "Customer", "link_name": customer})
	doc.save(ignore_permissions=True)


def create_asset(data):
	"""新建 ERPNext Asset 作为检测设备。

	按"登记已有设备"处理(is_existing_asset),所以不要求采购单/发票;
	但不走折旧(calculate_depreciation=0),只当设备台账用。
	"""
	data = data or {}
	asset_name = (data.get("asset_name") or "").strip()
	item_code = (data.get("item_code") or "").strip()
	company = data.get("company")
	location = data.get("location")

	missing = [
		label
		for value, label in (
			(asset_name, "设备名称"),
			(item_code, "资产项目(Item)"),
			(company, "公司"),
			(location, "位置"),
		)
		if not value
	]
	if missing:
		frappe.throw("请填写:" + "、".join(missing))

	gross_purchase_amount = flt(data.get("gross_purchase_amount"))
	if not gross_purchase_amount:
		frappe.throw("请填写购置金额(ERPNext 的 Asset 必须要有)")

	purchase_date = data.get("purchase_date") or today()
	doc = frappe.new_doc("Asset")
	doc.asset_name = asset_name
	doc.item_code = item_code
	doc.company = company
	doc.location = location
	doc.custodian = data.get("custodian") or None
	doc.cost_center = data.get("cost_center") or frappe.get_cached_value(
		"Company", company, "depreciation_cost_center"
	)
	doc.purchase_date = purchase_date
	doc.available_for_use_date = data.get("available_for_use_date") or purchase_date
	doc.gross_purchase_amount = gross_purchase_amount
	doc.is_existing_asset = 1
	doc.calculate_depreciation = 0
	doc.insert(ignore_permissions=True)
	return doc.name


def default_item_group():
	return (
		frappe.db.get_value("Item Group", {"is_group": 0}, "name")
		or frappe.db.get_single_value("Stock Settings", "item_group")
		or "Products"
	)


def create_item(data):
	"""新建检测项目:ERPNext Item,按"服务型销售物料"建。

	检测项目就是 ERPNext 的 Item:协议价按它定价,报价单也按它开行。
	"""
	data = data or {}
	item_name = (data.get("item_name") or "").strip()
	item_code = (data.get("item_code") or "").strip() or item_name
	if not item_code:
		frappe.throw("请填写检测项目名称或编码")
	if frappe.db.exists("Item", item_code):
		frappe.throw(f"检测项目「{item_code}」已存在,请直接搜索选择")

	doc = frappe.new_doc("Item")
	doc.item_code = item_code
	doc.item_name = item_name or item_code
	doc.item_group = data.get("item_group") or default_item_group()
	doc.stock_uom = data.get("uom") or "Nos"
	doc.description = data.get("description")
	# 检测服务不管理库存,但可以卖。
	doc.is_stock_item = 0
	doc.is_sales_item = 1
	doc.is_purchase_item = 0
	doc.insert(ignore_permissions=True)
	return doc.name


def item_form_options():
	return {
		"item_groups": frappe.get_all(
			"Item Group",
			filters={"is_group": 0},
			fields=["name"],
			order_by="name",
			limit_page_length=200,
		),
		"uoms": frappe.get_all(
			"UOM", fields=["name"], order_by="name", limit_page_length=200
		),
		"defaults": {"item_group": default_item_group(), "uom": "Nos"},
	}


def fixed_asset_item_options():
	"""能建 Asset 的 Item:固定资产、非库存、未停用。"""
	return frappe.get_all(
		"Item",
		filters={"is_fixed_asset": 1, "is_stock_item": 0, "disabled": 0},
		fields=["name", "item_name", "asset_category"],
		order_by="item_name asc",
		limit_page_length=200,
	)


def location_options():
	return frappe.get_all("Location", fields=["name"], order_by="name", limit_page_length=200)


def custodian_options():
	return frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "employee_name"],
		order_by="employee_name asc",
		limit_page_length=200,
	)
