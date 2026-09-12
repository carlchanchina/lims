# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""设备校准记录。

校准证书的原始事实放在这张表,Asset 上的
calibration_status / last_calibration_date / calibration_due_date
只是「最新一条记录」的快照,供设备使用登记做拦截。
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today

CALIBRATION_STATUS_OK = "合格"
CALIBRATION_STATUS_NG = "不合格"
CALIBRATION_STATUS_UNKNOWN = "未校准"


class CalibrationRecord(Document):
	def validate(self):
		self.set_due_date()
		self.validate_period()

	def set_due_date(self):
		"""没填下次校准日期时,按 Asset 上的校准周期推算。"""
		if self.due_date or not self.asset or not self.calibration_date:
			return
		interval = frappe.db.get_value("Asset", self.asset, "calibration_interval_days")
		if interval:
			self.due_date = add_days(self.calibration_date, int(interval))

	def validate_period(self):
		if self.due_date and self.calibration_date and getdate(self.due_date) <= getdate(
			self.calibration_date
		):
			frappe.throw(_("下次校准日期必须晚于校准日期"), title=_("日期不正确"))


def sync_asset_calibration(doc, method=None):
	"""Calibration Record 增删改后,把最新记录回写到 Asset 的校准快照。"""
	asset = doc.get("asset") if hasattr(doc, "get") else None
	if not asset or not frappe.db.exists("Asset", asset):
		return
	if not frappe.db.has_column("Asset", "calibration_due_date"):
		return

	# on_trash 在数据库删除之前触发,所以要把正在删除的这条排除掉,
	# 否则删掉最后一条记录后快照不会回退到「未校准」。
	filters = {"asset": asset}
	if method in ("on_trash", "after_delete") and doc.get("name"):
		filters["name"] = ["!=", doc.get("name")]

	latest = frappe.get_all(
		"Calibration Record",
		filters=filters,
		fields=["name", "calibration_date", "due_date", "result"],
		order_by="calibration_date desc, creation desc",
		limit=1,
	)

	if not latest:
		frappe.db.set_value(
			"Asset",
			asset,
			{
				"calibration_status": CALIBRATION_STATUS_UNKNOWN,
				"last_calibration_date": None,
				"calibration_due_date": None,
			},
			update_modified=False,
		)
		return

	record = latest[0]
	frappe.db.set_value(
		"Asset",
		asset,
		{
			"calibration_status": calibration_status(record),
			"last_calibration_date": record.calibration_date,
			"calibration_due_date": record.due_date,
		},
		update_modified=False,
	)


def calibration_status(record):
	"""校准状态:结果不合格,或有效期已过,都算不合格。"""
	if record.result == CALIBRATION_STATUS_NG:
		return CALIBRATION_STATUS_NG
	if record.due_date and getdate(record.due_date) < getdate(today()):
		return CALIBRATION_STATUS_NG
	return CALIBRATION_STATUS_OK
