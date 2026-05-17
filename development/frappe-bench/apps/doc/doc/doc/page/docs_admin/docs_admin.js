let docsAdminPage = null;
let docsAdminApp = null;

frappe.pages["docs-admin"].on_page_load = function (wrapper) {
	docsAdminPage = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("文档编辑器"),
		single_column: true,
	});

	$(docsAdminPage.main).empty().append('<div class="docs-admin-app"></div>');
};

frappe.pages["docs-admin"].on_page_show = async function (wrapper) {
	const $parent = $(wrapper).find(".docs-admin-app");
	$parent.empty();

	await frappe.require(["docs_admin.bundle.js", "docs_admin.bundle.css"]);
	docsAdminApp = frappe.ui.setup_docs_admin($parent);
};
