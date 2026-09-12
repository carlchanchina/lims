# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, today

from lims.integrations.erpnext_masters import asset_calibration_state


class TestCalibrationRecord(IntegrationTestCase):
	def setUp(self):
		self.asset = _create_asset()

	def tearDown(self):
		frappe.db.rollback()

	def test_latest_record_writes_back_to_asset(self):
		_create_calibration(self.asset, calibration_date=today(), due_date=add_days(today(), 365))
		asset = frappe.get_doc("Asset", self.asset)
		self.assertEqual(asset.calibration_status, "合格")
		self.assertEqual(str(asset.calibration_due_date), str(add_days(today(), 365)))
		self.assertEqual(asset_calibration_state(self.asset)["status"], "ok")

	def test_overdue_record_marks_asset_expired(self):
		_create_calibration(
			self.asset, calibration_date=add_days(today(), -400), due_date=add_days(today(), -40)
		)
		self.assertEqual(frappe.db.get_value("Asset", self.asset, "calibration_status"), "不合格")
		self.assertEqual(asset_calibration_state(self.asset)["status"], "expired")

	def test_due_date_derived_from_asset_interval(self):
		frappe.db.set_value("Asset", self.asset, "calibration_interval_days", 180)
		record = _create_calibration(self.asset, calibration_date=today(), due_date=None)
		self.assertEqual(str(record.due_date), str(add_days(today(), 180)))

	def test_deleting_last_record_resets_asset_snapshot(self):
		record = _create_calibration(
			self.asset, calibration_date=today(), due_date=add_days(today(), 365)
		)
		self.assertEqual(frappe.db.get_value("Asset", self.asset, "calibration_status"), "合格")

		frappe.delete_doc("Calibration Record", record.name, force=1, ignore_permissions=True)
		asset = frappe.get_doc("Asset", self.asset)
		self.assertFalse(asset.calibration_due_date)
		self.assertEqual(asset.calibration_status, "未校准")
		self.assertEqual(asset_calibration_state(self.asset)["status"], "unknown")

	def test_due_date_must_be_after_calibration_date(self):
		with self.assertRaises(frappe.ValidationError):
			_create_calibration(self.asset, calibration_date=today(), due_date=add_days(today(), -1))


def _create_asset():
	category = _ensure_asset_category()
	item_code = f"LIMS-CAL-ITEM-{frappe.generate_hash(length=5)}"
	item = frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": item_code,
			"item_name": "校准测试用固定资产",
			"item_group": frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "Products",
			"stock_uom": "Nos",
			"is_stock_item": 0,
			"is_fixed_asset": 1,
			"asset_category": category,
		}
	).insert(ignore_permissions=True)
	company = frappe.db.get_value("Company", {}, "name")
	return (
		frappe.get_doc(
			{
				"doctype": "Asset",
				"item_code": item.name,
				"asset_name": "LIMS 校准测试设备",
				"company": company,
				"location": frappe.db.get_value("Location", {}, "name"),
				"purchase_date": today(),
				"available_for_use_date": today(),
				"gross_purchase_amount": 1000,
				"is_existing_asset": 1,
				"calculate_depreciation": 0,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _ensure_asset_category():
	"""找一个可用的固定资产类别;没有就按公司科目建一个。"""
	existing = frappe.db.get_value("Asset Category", {}, "name")
	if existing:
		return existing

	company = frappe.db.get_value("Company", {}, "name")
	fixed_asset = _ensure_account(company, "Asset", "Fixed Asset")
	accumulated = _ensure_account(company, "Asset", "Accumulated Depreciation")
	expense = _ensure_account(company, "Expense", "Depreciation")
	if not (fixed_asset and accumulated and expense):
		frappe.skipTest("当前站点没有可用于固定资产的会计科目,跳过资产相关用例")

	return (
		frappe.get_doc(
			{
				"doctype": "Asset Category",
				"asset_category_name": "LIMS 测试设备",
				"total_number_of_depreciations": 3,
				"frequency_of_depreciation": 12,
				"accounts": [
					{
						"company_name": company,
						"fixed_asset_account": fixed_asset,
						"accumulated_depreciation_account": accumulated,
						"depreciation_expense_account": expense,
					}
				],
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _ensure_account(company, root_type, account_type):
	"""找(或建)一个指定 account_type 的科目,固定资产类别需要专用科目类型。"""
	existing = frappe.db.get_value(
		"Account", {"company": company, "account_type": account_type, "is_group": 0}, "name"
	)
	if existing:
		return existing
	parent = frappe.db.get_value(
		"Account", {"company": company, "root_type": root_type, "is_group": 1}, "name"
	)
	if not parent:
		return None
	return (
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": f"LIMS {account_type}",
				"parent_account": parent,
				"company": company,
				"root_type": root_type,
				"account_type": account_type,
				"is_group": 0,
			}
		)
		.insert(ignore_permissions=True)
		.name
	)


def _create_calibration(asset, calibration_date, due_date):
	return frappe.get_doc(
		{
			"doctype": "Calibration Record",
			"asset": asset,
			"calibration_date": calibration_date,
			"due_date": due_date,
			"certificate_no": f"CAL-{frappe.generate_hash(length=5)}",
			"result": "合格",
		}
	).insert(ignore_permissions=True)
