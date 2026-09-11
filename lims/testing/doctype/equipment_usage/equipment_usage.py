# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from lims.integrations.erpnext_masters import asset_calibration_state


class EquipmentUsage(Document):
	def validate(self):
		self.validate_period()
		self.validate_calibration()

	def validate_period(self):
		if self.to_datetime and getdate(self.to_datetime) < getdate(self.from_datetime):
			frappe.throw(_("结束时间不能早于开始时间"))

	def validate_calibration(self):
		"""校准过期(或没有校准信息)的设备不允许登记使用。"""
		state = asset_calibration_state(self.asset)
		if state["status"] == "expired":
			frappe.throw(
				_("设备 {0} 的校准已于 {1} 到期,请先校准后再使用").format(
					self.asset, state["due_date"]
				),
				title=_("设备校准过期"),
			)
		if state["status"] == "unknown":
			frappe.msgprint(
				_("设备 {0} 还没有校准记录,请补充校准信息").format(self.asset),
				indicator="orange",
				alert=True,
			)
