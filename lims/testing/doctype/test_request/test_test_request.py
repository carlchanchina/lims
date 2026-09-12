# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt, today

from lims.testing.doctype.test_request.test_request import (
	STATUS_QUOTED,
	create_quotation,
)
from lims.api.requests import request_action


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
		self.industry = _create_industry("军工")

	def tearDown(self):
		frappe.db.rollback()

	def test_agreement_price_scope_must_be_unique(self):
		_create_agreement_price(self.item, price=100)
		with self.assertRaises(frappe.ValidationError):
			_create_agreement_price(self.item, price=80)

	def test_agreement_price_rejects_customer_and_industry_together(self):
		with self.assertRaises(frappe.ValidationError):
			_create_agreement_price(self.item, price=100, customer=self.customer, industry=self.industry)

	def test_create_quotation_from_request(self):
		_create_agreement_price(self.item, price=100, customer=self.customer)

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
		self.assertEqual(flt(quotation.items[1].rate), 100)
		self.assertIn("GB/T 2423.1", quotation.items[0].description)

		request.reload()
		self.assertEqual(request.quotation, quotation_name)
		self.assertEqual(request.status, STATUS_QUOTED)

	def test_industry_price_used_when_customer_has_no_own_price(self):
		frappe.db.set_value("Customer", self.customer, "lims_industry", self.industry)
		_create_agreement_price(self.item, price=150, industry=self.industry)

		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[{"sample": "样品 A", "standard": self.standard, "qty": 1}],
		)
		quotation = frappe.get_doc("Quotation", create_quotation(request.name))
		self.assertEqual(flt(quotation.items[0].rate), 150)

	def test_customer_price_wins_over_industry_price(self):
		frappe.db.set_value("Customer", self.customer, "lims_industry", self.industry)
		_create_agreement_price(self.item, price=90, customer=self.customer)
		_create_agreement_price(self.item, price=150, industry=self.industry)

		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[{"sample": "样品 A", "standard": self.standard, "qty": 1}],
		)
		quotation = frappe.get_doc("Quotation", create_quotation(request.name))
		self.assertEqual(flt(quotation.items[0].rate), 90)

	def test_generic_price_used_as_fallback(self):
		_create_agreement_price(self.item, price=200)

		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[{"sample": "样品 A", "standard": self.standard, "qty": 1}],
		)
		quotation = frappe.get_doc("Quotation", create_quotation(request.name))
		self.assertEqual(flt(quotation.items[0].rate), 200)

	def test_quotation_fails_when_agreement_price_missing(self):
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
				"status": "检测中",
				"conclusion": "符合要求",
				"items": [
					{
						"item": self.item,
						"standard": self.standard,
						"sample": sample,
						"requirement": "低温 -40℃ 保持 2h",
						"result": "外观正常,无裂纹",
						"verdict": "合格",
					}
				],
			}
		).insert(ignore_permissions=True)

		self.assertEqual(report.test_request, request.name)
		self.assertEqual(report.sample, sample)
		self.assertEqual(report.items[0].standard, self.standard)
		self.assertEqual(report.items[0].verdict, "合格")

		# 请求上的报告状态由报告派生(Test Report 的 doc_events 刷新)
		request.reload()
		self.assertEqual(request.report_status, "部分出具(1)")

	def test_request_action_guardrails(self):
		_create_agreement_price(self.item, price=100, customer=self.customer)
		request = _create_request(
			self.customer,
			self.company,
			self.item,
			[{"sample": "样品 A", "standard": self.standard, "qty": 1}],
		)

		request_action(request.name, "generate_quotation")
		request.reload()
		self.assertEqual(request.status, STATUS_QUOTED)

		with self.assertRaises(frappe.ValidationError):
			request_action(request.name, "mark_ready")

		frappe.db.set_value("Test Request", request.name, "sales_order", "SO-TEST-001")
		request_action(request.name, "mark_ready")
		request_action(request.name, "start")
		request_action(request.name, "complete")

		request.reload()
		self.assertEqual(request.status, "已完成")


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


def _create_industry(name):
	return (
		frappe.get_doc({"doctype": "Industry", "industry_name": name})
		.insert(ignore_permissions=True)
		.name
	)


def _create_agreement_price(item, price=100, customer=None, industry=None):
	"""协议价:范围要么是客户,要么是行业,要么都留空(通用价)。"""
	return (
		frappe.get_doc(
			{
				"doctype": "Test Agreement Price",
				"catalog_code": f"TC-{frappe.generate_hash(length=5)}",
				"catalog_name": "试验协议价",
				"item": item,
				"customer": customer,
				"industry": industry,
				"price": price,
				"uom": "Nos",
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
