import frappe
from frappe.tests import IntegrationTestCase

from doc.doc.doctype.doc0030.doc0030 import restore_revision


class TestDOC0030Restore(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_restore_revision_updates_draft_and_creates_restore_revision(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		version = frappe.get_doc({"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}).insert()
		page = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"title": "创建订单",
				"slug": "create-order",
				"content_markdown": "# old",
			}
		).insert()
		old_revision = page.latest_revision
		page.content_markdown = "# new"
		page.save()

		restore_revision(page.name, old_revision)
		page.reload()

		self.assertEqual(page.content_markdown, "# old")
		restore = frappe.get_doc("DOC0031", page.latest_revision)
		self.assertEqual(restore.change_type, "restore")
		self.assertEqual(restore.content_markdown, "# old")
