import frappe
from frappe.tests import IntegrationTestCase


class TestDOC0030(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def create_version(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		version = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		return project, version

	def test_root_page_path(self):
		project, version = self.create_version()
		page = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": version.name, "title": "API", "slug": "API"}
		).insert()

		self.assertEqual(page.slug, "api")
		self.assertEqual(page.path, "api")

	def test_child_page_path(self):
		project, version = self.create_version()
		parent = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": version.name, "title": "API", "slug": "api"}
		).insert()
		child = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"parent_page": parent.name,
				"title": "创建订单",
				"slug": "create-order",
			}
		).insert()

		self.assertEqual(child.path, "api/create-order")

	def test_parent_must_be_same_version(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		v1 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		v2 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v2", "title": "v2"}).insert()
		parent = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": v1.name, "title": "API", "slug": "api"}
		).insert()

		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "DOC0030",
					"project": project.name,
					"doc_version": v2.name,
					"parent_page": parent.name,
					"title": "创建订单",
					"slug": "create-order",
				}
			).insert()

	def test_save_creates_revision(self):
		project, version = self.create_version()
		page = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"title": "创建订单",
				"slug": "create-order",
				"content_markdown": "# 创建订单",
			}
		).insert()

		self.assertTrue(page.latest_revision)
		revision = frappe.get_doc("DOC0031", page.latest_revision)
		self.assertEqual(revision.revision_no, 1)
		self.assertEqual(revision.content_markdown, "# 创建订单")
