# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from test.testing.doctype.testing_entrustment.testing_entrustment import (
	STATUS_QUOTATION_ACCEPTED,
	STATUS_QUOTATION_CREATED,
	create_quotation,
)


class TestTestingEntrustment(IntegrationTestCase):
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

	def tearDown(self):
		frappe.db.rollback()

	def test_validate_calculates_amounts(self):
		entrustment = _create_entrustment(self.customer, self.company, self.item)
		self.assertEqual(flt(entrustment.estimated_amount), 260)
		self.assertEqual(flt(entrustment.items[0].amount), 200)
		self.assertEqual(flt(entrustment.items[1].amount), 60)

	def test_create_quotation_links_back(self):
		entrustment = _create_entrustment(self.customer, self.company, self.item)
		entrustment.submit()

		quotation_name = create_quotation(entrustment.name)
		quotation = frappe.get_doc("Quotation", quotation_name)

		self.assertEqual(quotation.party_name, self.customer)
		self.assertEqual(len(quotation.items), 2)
		self.assertEqual(flt(quotation.items[0].rate), 100)
		self.assertEqual(quotation.testing_entrustment, entrustment.name)

		entrustment.reload()
		self.assertEqual(entrustment.quotation, quotation_name)
		self.assertEqual(entrustment.status, STATUS_QUOTATION_CREATED)

		quotation.submit()
		entrustment.reload()
		self.assertEqual(entrustment.status, STATUS_QUOTATION_ACCEPTED)

	def test_cannot_create_quotation_before_submit(self):
		entrustment = _create_entrustment(self.customer, self.company, self.item)
		with self.assertRaises(frappe.ValidationError):
			create_quotation(entrustment.name)

	def test_sample_and_test_report_link_to_entrustment(self):
		entrustment = _create_entrustment(self.customer, self.company, self.item)

		sample = (
			frappe.get_doc(
				{
					"doctype": "Sample",
					"entrustment": entrustment.name,
					"sample_name": "样品 A",
					"item": self.item,
					"quantity": 2,
				}
			)
			.insert(ignore_permissions=True)
		)
		report = (
			frappe.get_doc(
				{
					"doctype": "Test Report",
					"entrustment": entrustment.name,
					"sample": sample.name,
					"item": self.item,
					"status": "检测中",
				}
			)
			.insert(ignore_permissions=True)
		)

		self.assertEqual(sample.entrustment, entrustment.name)
		self.assertEqual(report.entrustment, entrustment.name)
		self.assertEqual(report.sample, sample.name)


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

	return frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": name,
			"customer_group": customer_group,
			"territory": territory,
		}
	).insert(ignore_permissions=True).name


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


def _create_entrustment(customer, company, item):
	entrustment = frappe.get_doc(
		{
			"doctype": "Testing Entrustment",
			"customer": customer,
			"company": company,
			"transaction_date": frappe.utils.today(),
			"items": [
				{
					"item": item,
					"qty": 2,
					"rate": 100,
					"testing_standard": "GB/T 12345",
				},
				{
					"item": item,
					"qty": 1,
					"rate": 60,
					"testing_standard": "ISO 9001",
				},
			],
		}
	)
	# save() also runs update_amounts(); 260 == 2*100 + 1*60
	entrustment.insert(ignore_permissions=True)
	return entrustment
