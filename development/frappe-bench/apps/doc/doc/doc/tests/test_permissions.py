import frappe
from frappe.tests import IntegrationTestCase

from doc.doc.services.permissions import get_project_role, has_project_role


class TestProjectPermissions(IntegrationTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def create_user(self):
		email = f"doc-editor-{frappe.generate_hash(length=8)}@example.com"
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "Doc Editor",
				"enabled": 1,
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
		return email

	def test_system_manager_has_manager_role(self):
		project = frappe.get_doc({"doctype": "DOC0010", "title": "支付系统", "slug": frappe.generate_hash(length=8)}).insert()
		self.assertEqual(get_project_role(project.name, "Administrator"), "manager")

	def test_member_role_is_returned(self):
		user = self.create_user()
		project = frappe.get_doc(
			{
				"doctype": "DOC0010",
				"title": "支付系统",
				"slug": frappe.generate_hash(length=8),
				"members": [{"user": user, "role": "editor"}],
			}
		).insert()
		self.assertTrue(has_project_role(project.name, user, "viewer"))
		self.assertTrue(has_project_role(project.name, user, "editor"))
		self.assertFalse(has_project_role(project.name, user, "publisher"))
