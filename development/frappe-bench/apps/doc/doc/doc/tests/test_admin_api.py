import frappe
from frappe.tests import UnitTestCase

from doc.doc.api.admin import get_page_detail, get_page_tree, get_project_spaces, get_versions, save_page_content


class TestAdminAPI(UnitTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def create_docs(self):
		project = frappe.get_doc(
			{
				"doctype": "DOC0010",
				"title": "支付系统",
				"slug": frappe.generate_hash(length=8),
				"description": "支付接口文档",
			}
		).insert()
		version = frappe.get_doc(
			{"doctype": "DOC0020", "project": project.name, "version_key": "v1", "title": "v1"}
		).insert()
		root = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"title": "API 文档",
				"slug": "api",
				"sort_order": 10,
				"content_markdown": "# API 文档",
			}
		).insert()
		child = frappe.get_doc(
			{
				"doctype": "DOC0030",
				"project": project.name,
				"doc_version": version.name,
				"parent_page": root.name,
				"title": "创建订单",
				"slug": "create-order",
				"sort_order": 20,
				"content_markdown": "# 创建订单",
			}
		).insert()
		return project, version, root, child

	def test_get_project_spaces_returns_default_version(self):
		project, version, _root, _child = self.create_docs()

		spaces = get_project_spaces()
		space_by_name = {space["name"]: space for space in spaces}

		self.assertEqual(space_by_name[project.name]["slug"], project.slug)
		self.assertEqual(space_by_name[project.name]["default_version"], version.name)

	def test_get_versions_returns_project_versions(self):
		project, version, _root, _child = self.create_docs()

		versions = get_versions(project.name)

		self.assertEqual(versions[0]["name"], version.name)
		self.assertEqual(versions[0]["version_key"], "v1")

	def test_get_page_tree_returns_nested_pages(self):
		_project, version, root, child = self.create_docs()

		tree = get_page_tree(version.name)

		self.assertEqual(tree[0]["name"], root.name)
		self.assertEqual(tree[0]["children"][0]["name"], child.name)
		self.assertEqual(tree[0]["children"][0]["path"], "api/create-order")

	def test_get_page_detail_returns_markdown(self):
		_project, _version, _root, child = self.create_docs()

		detail = get_page_detail(child.name)

		self.assertEqual(detail["title"], "创建订单")
		self.assertEqual(detail["content_markdown"], "# 创建订单")
		self.assertEqual(detail["status"], "draft")

	def test_save_page_content_updates_markdown(self):
		_project, _version, _root, child = self.create_docs()

		detail = save_page_content(child.name, "# 已更新")

		self.assertEqual(detail["content_markdown"], "# 已更新")
		self.assertEqual(frappe.db.get_value("DOC0030", child.name, "content_markdown"), "# 已更新")

	def test_save_page_content_preserves_mermaid_arrows(self):
		_project, _version, _root, child = self.create_docs()
		markdown = """业务流程图：

```mermaid
flowchart TD
    A["维护主数据"] --&gt; B["创建报检单"]
```
"""

		detail = save_page_content(child.name, markdown)

		self.assertIn('A["维护主数据"] --> B["创建报检单"]', detail["content_markdown"])
		self.assertNotIn("--&gt;", detail["content_markdown"])

	def test_save_page_content_restores_indented_mermaid_block(self):
		_project, _version, _root, child = self.create_docs()
		markdown = """业务流程图：

    flowchart TD
        A --&gt; B

后续内容"""

		detail = save_page_content(child.name, markdown)

		self.assertIn("```mermaid\nflowchart TD\n    A --> B\n```", detail["content_markdown"])
		self.assertIn("后续内容", detail["content_markdown"])
