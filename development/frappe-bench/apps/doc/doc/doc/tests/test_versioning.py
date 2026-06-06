import frappe
from frappe.tests import IntegrationTestCase

from doc.doc.services.versioning import copy_version_tree


class TestVersioningService(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_copy_version_tree_copies_parent_child_paths(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		v1 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		v2 = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v2", "title": "v2"}).insert()
		parent = frappe.get_doc(
			{"doctype": "DOC0030", "project": project.name, "doc_version": v1.name, "title": "API", "slug": "api"}
		).insert()
		frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": v1.name,
				"parent_page": parent.name,
				"title": "创建订单",
				"slug": "create-order",
				"content_markdown": "# 创建订单",
			}
		).insert()

		copy_version_tree(v1.name, v2.name)

		copied_paths = frappe.get_all("DOC0030", filters={"doc_version": v2.name}, pluck="path")
		self.assertEqual(set(copied_paths), {"api", "api/create-order"})
