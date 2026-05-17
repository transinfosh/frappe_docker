import frappe


def copy_version_tree(source_version: str, target_version: str) -> dict[str, str]:
	source = frappe.get_doc("DOC0020", source_version)
	target = frappe.get_doc("DOC0020", target_version)
	if source.project != target.project:
		frappe.throw("来源版本和目标版本必须属于同一项目。")

	page_map = {}
	pages = frappe.get_all(
		"DOC0030",
		filters={"doc_version": source.name},
		fields=["name"],
		order_by="path asc",
	)

	for row in pages:
		old_page = frappe.get_doc("DOC0030", row.name)
		new_page = frappe.copy_doc(old_page)
		new_page.project = target.project
		new_page.doc_version = target.name
		new_page.parent_page = page_map.get(old_page.parent_page)
		new_page.latest_revision = None
		new_page.insert()
		page_map[old_page.name] = new_page.name

	return page_map
