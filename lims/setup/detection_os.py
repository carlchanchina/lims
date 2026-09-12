# Copyright (c) 2026, Carl and contributors
# For license information, please see license.txt

"""旭博检测中心OS 的站点级设置(幂等,每次 migrate 后执行)。

- 把旧角色(Testing Manager / Testing User)的用户迁移到新角色并停用旧角色;
- 清掉旧版本遗留的 Workspace / Workspace Sidebar / 应用图标;
- 站点默认 app 指向 lims,所有系统用户默认落地「首页」Workspace。

Workspace / Workspace Sidebar / Number Card / Dashboard Chart 都由
`frappe/model/sync.py` 从 app 模块目录里的 JSON 文件同步,不在这里创建。
"""

import frappe

HOME_WORKSPACE = "首页"

# 旧角色 -> 新角色(一个旧角色可以拆成多个新角色)
LEGACY_ROLE_MAPPING = {
	"Testing Manager": ("总经理", "项目经理"),
	"Testing User": ("检测工程师",),
}

# 旧版本的单一 Workspace(带 /lims 入口),已被 9 个中心取代。
LEGACY_WORKSPACES = ("Testing",)

# 旧版本存在库里、但 app 里已经没有对应文件的 Workspace Sidebar。
# 它的 items 还指向已删除的 Testing 工作区,点进去会报
# "Workspace <b>Testing</b> does not exist"。
LEGACY_SIDEBARS = ("Testing",)

APP_NAME = "lims"


def setup_detection_os():
	remove_legacy_workspaces()
	remove_legacy_sidebars()
	remove_orphan_desktop_icons()
	migrate_legacy_roles()
	fix_app_desktop_icon()
	set_default_app()
	set_default_workspaces()


def remove_legacy_workspaces():
	for name in LEGACY_WORKSPACES:
		if frappe.db.exists("Workspace", name):
			frappe.delete_doc("Workspace", name, force=True, ignore_missing=True)


def remove_legacy_sidebars():
	"""删除库里残留、且不是由 app 文件管理的旧侧边栏。"""
	for name in LEGACY_SIDEBARS:
		if not frappe.db.exists("Workspace Sidebar", name):
			continue
		if frappe.db.get_value("Workspace Sidebar", name, "standard"):
			# 由 app 里的 JSON 文件管理,交给 migrate 处理。
			continue
		frappe.delete_doc("Workspace Sidebar", name, force=True, ignore_missing=True)


def remove_orphan_desktop_icons():
	"""删掉指向已卸载 app 的桌面图标(例如卸载 CRM 后残留的「Frappe CRM」)。"""
	installed = set(frappe.get_installed_apps())
	for icon in frappe.get_all("Desktop Icon", fields=["name", "app"], limit_page_length=0):
		if icon.app and icon.app not in installed:
			frappe.delete_doc("Desktop Icon", icon.name, force=True, ignore_missing=True)


def fix_app_desktop_icon():
	"""纠正历史遗留的应用图标(旧版叫 Testing 且指向已删除的 /lims)。

	Frappe 只在安装时按 add_to_apps_screen 建这个图标,
	之后改了 app_title / route 不会自动更新,只能这里修正。
	"""
	app_details = frappe.get_hooks("add_to_apps_screen", app_name=APP_NAME)
	app_titles = frappe.get_hooks("app_title", app_name=APP_NAME)
	if not app_details or not app_titles:
		return

	app_title = app_titles[0]
	detail = app_details[0]
	route, logo = detail.get("route"), detail.get("logo")

	name = frappe.db.exists("Desktop Icon", {"app": APP_NAME, "icon_type": "App"})
	if not name:
		return

	if name != app_title:
		if frappe.db.exists("Desktop Icon", app_title):
			# 新名字被其它图标占用,删掉旧的应用图标即可(Frappe 后续安装会重建)。
			frappe.delete_doc("Desktop Icon", name, force=True, ignore_missing=True)
			return
		# frappe.rename_doc 顶层封装不支持 ignore_permissions,migrate 时以 Administrator 执行。
		frappe.rename_doc("Desktop Icon", name, app_title, force=True)
		name = app_title

	doc = frappe.get_doc("Desktop Icon", name)
	if (doc.link, doc.logo_url, doc.hidden) != (route, logo, 0):
		doc.link = route
		doc.logo_url = logo
		doc.hidden = 0
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)


def migrate_legacy_roles():
	"""把持有旧角色的用户迁到新角色,然后停用旧角色。"""
	for legacy_role, new_roles in LEGACY_ROLE_MAPPING.items():
		if not frappe.db.exists("Role", legacy_role):
			continue

		users = frappe.get_all(
			"Has Role", filters={"role": legacy_role, "parenttype": "User"}, pluck="parent"
		)
		for user in users:
			doc = frappe.get_doc("User", user)
			existing = {row.role for row in doc.roles}
			changed = False
			for role in new_roles:
				if role not in existing:
					doc.append("roles", {"role": role})
					changed = True
			doc.roles = [row for row in doc.roles if row.role != legacy_role]
			if changed or legacy_role in existing:
				doc.flags.ignore_permissions = True
				doc.save(ignore_permissions=True)

		if not frappe.db.get_value("Role", legacy_role, "disabled"):
			frappe.db.set_value("Role", legacy_role, "disabled", 1)


def set_default_app():
	"""登录后默认进入 lims(旭博检测中心OS)。"""
	# System Settings 是 Single DocType(存在 tabSingles 里,没有自己的表),
	# 所以只能用 meta 判断字段,用 set_single_value 写值。
	if not frappe.get_meta("System Settings").has_field("default_app"):
		return
	if frappe.db.get_single_value("System Settings", "default_app") != "lims":
		frappe.db.set_single_value("System Settings", "default_app", "lims")


def set_default_workspaces():
	"""系统用户没设过默认落地页时,设为「首页」(之后尊重用户自己的选择)。"""
	if not frappe.db.exists("Workspace", HOME_WORKSPACE):
		return
	frappe.db.sql(
		"""
		UPDATE `tabUser`
		SET default_workspace = %(workspace)s
		WHERE user_type = 'System User'
			AND enabled = 1
			AND name NOT IN ('Guest', 'Administrator')
			AND (default_workspace IS NULL OR default_workspace = '')
		""",
		{"workspace": HOME_WORKSPACE},
	)
