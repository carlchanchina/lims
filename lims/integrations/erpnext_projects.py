# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""LIMS 委托请求 → ERPNext Project / Task 集成。

每张 Test Request 保存后自动生成一个 ERPNext Project(项目名 = 委托单号),
委托单上的每个测试项同步为一条 Project Task(带预计起止日期)。
ERPNext Project 自带 Gantt 时间线,替代原 test_plan 的手工日期/任务表。

方向约定:单向 LIMS → ERPNext,Project/Task 都落在 ERPNext,
通过 lims_test_request / lims_test_request_item 定制字段关联回 LIMS。
"""

import frappe
from frappe import _


def create_project_from_request(doc, method=None):
	"""Test Request after_insert:自动建 ERPNext Project 并同步测试项为 Task。"""
	if getattr(doc, "project", None) and frappe.db.exists("Project", doc.project):
		sync_tasks(doc)
		return

	project = frappe.new_doc("Project")
	project.project_name = doc.name
	project.customer = doc.customer
	project.expected_start_date = doc.transaction_date
	project.expected_end_date = doc.required_by
	project.notes = doc.remarks or _("由 LIMS 委托请求 {0} 自动生成").format(doc.name)
	_set_lims_field(project, "lims_test_request", doc.name)
	project.flags.ignore_permissions = True
	project.insert(ignore_permissions=True)

	doc.db_set("project", project.name)
	sync_tasks(doc, project.name)


def sync_tasks(doc, method=None):
	"""Test Request on_update:把测试项增量同步为 Project Task(按项去重)。"""
	project = getattr(doc, "project", None)
	if not project or not frappe.db.exists("Project", project):
		return

	for row in doc.get("items") or []:
		if frappe.db.exists(
			"Task", {"project": project, "lims_test_request_item": row.name}
		):
			continue

		sample_name = frappe.db.get_value("Sample", row.sample, "sample_name") or ""
		subject = " / ".join(
			filter(None, [row.item_name or row.item, sample_name])
		) or row.name

		desc_lines = []
		if row.standard:
			desc_lines.append(_("检测标准: {0}").format(row.standard))
		if row.qty:
			desc_lines.append(_("数量: {0} {1}").format(row.qty, row.uom or ""))
		if row.equipment:
			desc_lines.append(_("设备: {0}").format(row.equipment))
		if row.subcontracted:
			desc_lines.append(_("分包: {0}").format(row.subcontractor or "-"))
		if row.remarks:
			desc_lines.append(row.remarks)

		task = frappe.new_doc("Task")
		task.subject = subject
		task.project = project
		task.exp_start_date = doc.transaction_date
		task.exp_end_date = doc.required_by
		task.description = "\n".join(desc_lines)
		_set_lims_field(task, "lims_test_request_item", row.name)
		task.flags.ignore_permissions = True
		task.insert(ignore_permissions=True)


def _set_lims_field(doc, fieldname, value):
	"""定制字段未同步(migrate)前优雅降级,不因缺列中断主流程。"""
	if frappe.db.has_column(doc.doctype, fieldname):
		doc.set(fieldname, value)
