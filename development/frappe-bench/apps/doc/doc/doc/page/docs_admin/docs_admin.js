let docsAdminPage = null;
let docsAdminApp = null;
let projectField = null;
let versionField = null;

frappe.pages["docs-admin"].on_page_load = function (wrapper) {
	docsAdminPage = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("文档编辑器"),
		single_column: true,
	});

	projectField = docsAdminPage.add_field({
		fieldname: "doc_project",
		label: __("项目"),
		fieldtype: "Select",
		change() {
			docsAdminApp?.rootRef?.value?.setProject(this.get_value());
		},
	});
	versionField = docsAdminPage.add_field({
		fieldname: "doc_version",
		label: __("版本"),
		fieldtype: "Select",
		change() {
			docsAdminApp?.rootRef?.value?.setVersion(this.get_value());
		},
	});
	docsAdminPage.set_primary_action(__("保存"), () => {
		docsAdminApp?.rootRef?.value?.savePage();
	});

	$(docsAdminPage.main).empty().append('<div class="docs-admin-app"></div>');
};

frappe.pages["docs-admin"].on_page_show = async function (wrapper) {
	const $parent = $(wrapper).find(".docs-admin-app");
	$parent.empty();

	await frappe.require(["docs_admin.bundle.js", "docs_admin.bundle.css"]);
	docsAdminApp = frappe.ui.setup_docs_admin($parent, {
		pageControls: {
			project: projectField,
			version: versionField,
		},
	});
};
