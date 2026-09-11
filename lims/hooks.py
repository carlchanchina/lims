app_name = "lims"
app_title = "Testing"
app_publisher = "Carl"
app_description = "环境试验 LIMS - 以 ERPNext 为事实源的自定义业务 App"
app_email = "cowin3332@gmail.com"
app_license = "mit"
app_icon = "octicon octicon-checklist"
app_color = "green"

# Apps
# ------------------

required_apps = ["erpnext"]

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "lims",
		"logo": "/assets/lims/images/lims.svg",
		"title": "环境试验 LIMS",
		"route": "/lims",
		"has_permission": "lims.api.permission.has_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lims/css/lims.css"
# app_include_js = "/assets/lims/js/lims.js"

# include js, css files in header of web template
# web_include_css = "/assets/lims/css/lims.css"
# web_include_js = "/assets/lims/js/lims.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lims/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lims/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lims.utils.jinja_methods",
# 	"filters": "lims.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "lims.setup.install.after_install"
after_migrate = ["lims.setup.install.run_schema_cleanup"]

# Uninstallation
# ------------

# before_uninstall = "lims.uninstall.before_uninstall"
# after_uninstall = "lims.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lims.utils.before_app_install"
# after_app_install = "lims.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lims.utils.before_app_uninstall"
# after_app_uninstall = "lims.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "lims.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lims.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["lims.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------

doc_events = {
	# 方向约定:单向 LIMS → ERPNext。LIMS 不反向同步 ERPNext 主数据,
	# 客户/联系人/报价/订单都直接以 ERPNext 为事实源(LIMS 只读 + 定制字段)。
	# 委托请求保存后自动生成 ERPNext Project,测试项同步为 Project Task。
	"Test Request": {
		"after_insert": "lims.integrations.erpnext_projects.create_project_from_request",
		"on_update": "lims.integrations.erpnext_projects.sync_tasks",
	},
	# Test Report 是 LIMS 自己的单据,报告状态联动委托请求(LIMS 内部,非 ERPNext 回写)。
	"Test Report": {
		"after_insert": "lims.testing.doctype.test_request.test_request.sync_request_report_status",
		"on_update": "lims.testing.doctype.test_request.test_request.sync_request_report_status",
		"on_trash": "lims.testing.doctype.test_request.test_request.sync_request_report_status",
	},
}

# Custom Fields
# -------------
# LIMS 与 ERPNext 共用同一张表:ERPNext DocType 上加 lims_* 定制字段,
# 安装/migrate 时由 Frappe 自动同步,不需要镜像表。

custom_fields = {
	"Customer": [
		{
			"fieldname": "lims_industry",
			"label": "LIMS 行业",
			"fieldtype": "Link",
			"options": "Industry",
			"insert_after": "customer_group",
			"no_copy": 1,
		},
	],
	"Quotation": [
		{
			"fieldname": "lims_test_request",
			"label": "LIMS 委托请求",
			"fieldtype": "Link",
			"options": "Test Request",
			"insert_after": "transaction_date",
			"read_only": 1,
			"no_copy": 1,
		},
	],
	"Sales Order": [
		{
			"fieldname": "lims_test_request",
			"label": "LIMS 委托请求",
			"fieldtype": "Link",
			"options": "Test Request",
			"insert_after": "transaction_date",
			"read_only": 1,
			"no_copy": 1,
		},
	],
	"Project": [
		{
			"fieldname": "lims_test_request",
			"label": "LIMS 委托请求",
			"fieldtype": "Link",
			"options": "Test Request",
			"insert_after": "project_name",
			"read_only": 1,
			"no_copy": 1,
		},
	],
	"Task": [
		{
			"fieldname": "lims_test_request_item",
			"label": "LIMS 测试项",
			"fieldtype": "Link",
			"options": "Test Request Item",
			"insert_after": "subject",
			"read_only": 1,
			"no_copy": 1,
		},
	],
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lims.tasks.all"
# 	],
# 	"daily": [
# 		"lims.tasks.daily"
# 	],
# 	"hourly": [
# 		"lims.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lims.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lims.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lims.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "lims.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lims.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lims.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lims.utils.before_request"]
# after_request = ["lims.utils.after_request"]

# Job Events
# ----------
# before_job = ["lims.utils.before_job"]
# after_job = ["lims.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lims.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
