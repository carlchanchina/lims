# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from test.testing.doctype.test_request.test_request import (
	STATUS_QUOTED,
	create_quotation,
)


class TestTestRequest(IntegrationTestCase):
	def setUp(self):
		self.company = _get_company()
		if not self.company:
			self.skipTest("当前站点没有 Company,无法验证 Quotation 联动")

		currency = frappe.db.get_value("Company", self.company, "default_currency")
		self.customer = _create_customer()
		self.item = _create_item()
		self.price_list = _create_price_list(currency)
		frappe.db.set_value(
			"Customer", self.customer, "default_price_list", self.price_list
		)

		self.standard = _create_standard("GB/T 2423.1", "低温试验")
		self.standard_2 = _create_standard("GJB 150.4A", "低温试验(军标)")
		self.equipment = _create_equipment()

	def tearDown(self):
		frappe.db.rollback()

	def test_catalog_requires_single_default(self):
		_create_catalog(self.item, self.standard, self.equipment, price=100)
		with self.assertRaises(frappe.ValidationError):
			_create_catalog(self.item, self.standard, None, price=80, is_default=1)

	def test_create_quotation_from_request(self):
		_create_catalog(self.item, self.standard, self.equipment, price=100)
		_create_catalog(self.item, self.standard_2, self.equipment, price=150)

		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[
				{"sample": "样品 A", "standard": self.standard, "qty": 1},
				{"sample": "样品 B", "standard": self.standard_2, "qty": 2},
			],
		)

		self.assertFalse(request.meta.has_field("rate"))
		self.assertFalse(request.meta.has_field("amount"))

		quotation_name = create_quotation(request.name)
		quotation = frappe.get_doc("Quotation", quotation_name)

		self.assertEqual(quotation.party_name, self.customer)
		self.assertEqual(len(quotation.items), 2)
		self.assertEqual(flt(quotation.items[0].rate), 100)
		self.assertEqual(flt(quotation.items[1].rate), 150)
		self.assertIn("GB/T 2423.1", quotation.items[0].description)

		request.reload()
		self.assertEqual(request.quotation, quotation_name)
		self.assertEqual(request.status, STATUS_QUOTED)

	def test_quotation_fails_when_catalog_missing(self):
		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[{"sample": "样品 A", "standard": self.standard, "qty": 1}],
		)
		with self.assertRaises(frappe.ValidationError):
			create_quotation(request.name)

	def test_sample_and_report_link_to_request(self):
		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[{"sample": "样品 A", "standard": self.standard, "qty": 1}],
		)
		sample = request.items[0].sample

		report = frappe.get_doc(
			{
				"doctype": "Test Report",
				"test_request": request.name,
				"sample": sample,
				"sample_name": "样品 A",
				"item": self.item,
				"standard": self.standard,
				"equipment": self.equipment,
				"status": "检测中",
				"conclusion": "符合要求",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(report.test_request, request.name)
		self.assertEqual(report.sample, sample)
		self.assertEqual(report.standard, self.standard)


def _get_company():
	company = (
		frappe.defaults.get_user_default("Company")
		or frappe.defaults.get_global_default("company")
	)
	if not company:
		companies = frappe.db.get_all("Company", pluck="name", limit=1)
		company = companies[0] if companies else None
	return company


def _create_customer():
	name = f"LIMS-Test-Customer-{frappe.generate_hash(length=5)}"
	customer_group = frappe.db.get_value(
		"Customer Group", {"is_group": 0}, "name"
	) or frappe.db.get_single_value("Selling Settings", "customer_group")
	territory = frappe.db.get_value(
		"Territory", {"is_group": 0}, "name"
	) or frappe.db.get_single_value("Selling Settings", "territory")

	return (
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_group": customer_group,
				"territory": territory,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_item():
	name = f"LIMS-Test-Item-{frappe.generate_hash(length=5)}"
	item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	return (
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": name,
				"item_name": "环境试验服务",
				"item_group": item_group or "Products",
				"stock_uom": "Nos",
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_price_list(currency):
	name = f"LIMS-Test-Selling-{frappe.generate_hash(length=5)}"
	return (
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": name,
				"currency": currency,
				"selling": 1,
				"enabled": 1,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_standard(code, name):
	return (
		frappe.get_doc(
			{
				"doctype": "Test Standard",
				"standard_code": code,
				"standard_name": name,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_equipment():
	return (
		frappe.get_doc(
			{
				"doctype": "Equipment",
				"equipment_code": f"EQ-{frappe.generate_hash(length=4)}",
				"equipment_name": "低温试验箱",
				"model": "LTD-100",
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_catalog(item, standard, equipment=None, price=100, is_default=1):
	return (
		frappe.get_doc(
			{
				"doctype": "Test Catalog",
				"catalog_code": f"TC-{frappe.generate_hash(length=5)}",
				"catalog_name": f"{standard} 试验",
				"item": item,
				"standard": standard,
				"equipment": equipment,
				"price": price,
				"uom": "Nos",
				"is_default": is_default,
				"enabled": 1,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_request(customer, company, item, test_items):
	request = frappe.get_doc(
		{
			"doctype": "Test Request",
			"customer": customer,
			"company": company,
			"transaction_date": today(),
		}
	).insert(ignore_permissions=True)

	sample_names = []
	for row in test_items:
		if row["sample"] in sample_names:
			continue
		sample_names.append(row["sample"])
		frappe.get_doc(
			{
				"doctype": "Sample",
				"test_request": request.name,
				"sample_name": row["sample"],
				"qty": row["qty"],
				"uom": "Nos",
			}
		).insert(ignore_permissions=True)

	samples = {
		row["sample"]: frappe.db.get_value(
			"Sample",
			{"test_request": request.name, "sample_name": row["sample"]},
			"name",
		)
		for row in test_items
	}

	for row in test_items:
		request.append(
			"items",
			{
				"sample": samples[row["sample"]],
				"item": item,
				"standard": row["standard"],
				"qty": row["qty"],
			},
		)

	request.save(ignore_permissions=True)
	return request
