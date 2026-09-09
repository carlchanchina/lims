# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, flt, today

from test.testing.doctype.testing_entrustment.testing_entrustment import (
	STATUS_TO_TEST,
	get_sales_order_items,
)


class TestTestingEntrustment(IntegrationTestCase):
	def setUp(self):
		self.company = _get_company()
		if not self.company:
			self.skipTest("当前站点没有 Company,无法验证 Sales Order 联动")

		currency = frappe.db.get_value("Company", self.company, "default_currency")
		self.customer = _create_customer()
		self.item = _create_item()
		self.price_list = _create_price_list(currency)
		frappe.db.set_value(
			"Customer", self.customer, "default_price_list", self.price_list
		)

	def tearDown(self):
		frappe.db.rollback()

	def test_get_sales_order_items_returns_test_items(self):
		sales_order = _create_sales_order(
			self.customer, self.company, self.price_list, self.item
		)

		result = get_sales_order_items(sales_order.name)

		self.assertEqual(result["customer"], self.customer)
		self.assertEqual(len(result["items"]), 2)
		self.assertEqual(result["items"][0]["item"], self.item)
		self.assertEqual(flt(result["items"][0]["qty"]), 2)
		self.assertFalse(result["items"][0].get("rate"))

	def test_get_sales_order_items_requires_submitted_order(self):
		sales_order = _create_sales_order(
			self.customer,
			self.company,
			self.price_list,
			self.item,
			submit=False,
		)
		with self.assertRaises(frappe.ValidationError):
			get_sales_order_items(sales_order.name)

	def test_entrustment_with_samples_and_report(self):
		sales_order = _create_sales_order(
			self.customer, self.company, self.price_list, self.item
		)
		result = get_sales_order_items(sales_order.name)

		entrustment = frappe.get_doc(
			{
				"doctype": "Testing Entrustment",
				"customer": self.customer,
				"company": self.company,
				"sales_order": sales_order.name,
				"transaction_date": today(),
				"items": result["items"],
				"samples": [
					{
						"sample_name": "样品 A",
						"item": self.item,
						"qty": 2,
						"uom": "Nos",
					}
				],
			}
		).insert(ignore_permissions=True)

		self.assertEqual(len(entrustment.items), 2)
		self.assertEqual(entrustment.sales_order, sales_order.name)

		entrustment.submit()
		entrustment.reload()
		self.assertEqual(entrustment.status, STATUS_TO_TEST)

		sample_row = entrustment.samples[0]
		report = frappe.get_doc(
			{
				"doctype": "Test Report",
				"entrustment": entrustment.name,
				"sample": sample_row.name,
				"sample_name": sample_row.sample_name,
				"item": self.item,
				"status": "检测中",
			}
		).insert(ignore_permissions=True)

		self.assertEqual(report.entrustment, entrustment.name)
		self.assertEqual(report.sample, sample_row.name)
		self.assertEqual(report.sample_name, "样品 A")


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
	name = f"TE-Test-Customer-{frappe.generate_hash(length=5)}"
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
	name = f"TE-Test-Item-{frappe.generate_hash(length=5)}"
	item_group = frappe.db.get_value("Item Group", {"is_group": 0}, "name")
	return (
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": name,
				"item_name": name,
				"item_group": item_group or "Products",
				"stock_uom": "Nos",
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_price_list(currency):
	name = f"TE-Test-Selling-{frappe.generate_hash(length=5)}"
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


def _create_sales_order(customer, company, price_list, item, submit=True):
	series = frappe.get_meta("Sales Order").get_field("naming_series").options
	naming_series = series.splitlines()[0]
	currency = frappe.db.get_value("Price List", price_list, "currency")

	sales_order = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"naming_series": naming_series,
			"customer": customer,
			"order_type": "Sales",
			"company": company,
			"transaction_date": today(),
			"delivery_date": add_days(today(), 7),
			"currency": currency,
			"conversion_rate": 1,
			"selling_price_list": price_list,
			"price_list_currency": currency,
			"plc_conversion_rate": 1,
			"items": [
				{
					"item_code": item,
					"item_name": item,
					"qty": 2,
					"uom": "Nos",
					"conversion_factor": 1,
					"rate": 100,
					"delivery_date": add_days(today(), 7),
				},
				{
					"item_code": item,
					"item_name": item,
					"qty": 1,
					"uom": "Nos",
					"conversion_factor": 1,
					"rate": 60,
					"delivery_date": add_days(today(), 7),
				},
			],
		}
	).insert(ignore_permissions=True)

	if submit:
		sales_order.submit()
	return sales_order
