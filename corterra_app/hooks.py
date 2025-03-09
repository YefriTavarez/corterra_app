app_name = "corterra_app"
app_title = "Corterra"
app_publisher = "Yefri & Ezequiel"
app_description = "Corterra Customizations"
app_email = "yefritavarez@gmail.com"
app_license = "mit"

# Fixtures
# --------

fixtures = [
	{
		"dt": "DocType",
		"filters": {
			"name": [
				"in", [
					"Orden de Produccion",
					"Troqueladora",
					"Configuracion Corterra",
				],
			],
		},
	},
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "corterra_app",
# 		"logo": "/assets/corterra_app/logo.png",
# 		"title": "Corterra",
# 		"route": "/corterra_app",
# 		"has_permission": "corterra_app.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/corterra_app/css/corterra_app.css"
# app_include_js = "/assets/corterra_app/js/corterra_app.js"

# include js, css files in header of web template
# web_include_css = "/assets/corterra_app/css/corterra_app.css"
# web_include_js = "/assets/corterra_app/js/corterra_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "corterra_app/public/scss/website"

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
# app_include_icons = "corterra_app/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "corterra_app.utils.jinja_methods",
# 	"filters": "corterra_app.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "corterra_app.install.before_install"
# after_install = "corterra_app.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "corterra_app.uninstall.before_uninstall"
# after_uninstall = "corterra_app.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "corterra_app.utils.before_app_install"
# after_app_install = "corterra_app.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "corterra_app.utils.before_app_uninstall"
# after_app_uninstall = "corterra_app.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "corterra_app.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"File": {
		"on_update": "corterra_app.controllers.file.on_update",
	},
	"Orden de Produccion": {
		"autoname": "corterra_app.client.production_order.autoname",
	},
	"Quotation": {
		"autoname": "corterra_app.controllers.quotation.autoname",
	},
	"Sales Order": {
		"autoname": "corterra_app.client.sales_order.sales_order.autoname",
		"on_submit": "corterra_app.client.sales_order.sales_order.on_submit",
	},
	"Sales Invoice": {
		"on_submit": "corterra_app.controllers.sales_invoice.on_submit",
	},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"corterra_app.tasks.all"
# 	],
# 	"daily": [
# 		"corterra_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"corterra_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"corterra_app.tasks.weekly"
# 	],
# 	"monthly": [
# 		"corterra_app.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "corterra_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"corterra.client.make_sales_order": "corterra_app.client.quotation.make_sales_order",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "corterra_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["corterra_app.utils.before_request"]
# after_request = ["corterra_app.utils.after_request"]

# Job Events
# ----------
# before_job = ["corterra_app.utils.before_job"]
# after_job = ["corterra_app.utils.after_job"]

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
# 	"corterra_app.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
