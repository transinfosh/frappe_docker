import { createApp, h } from "vue";
import DocsAdmin from "./DocsAdmin.vue";

export function setup_docs_admin(wrapper) {
	const app = createApp({
		render() {
			return h(DocsAdmin);
		},
	});

	app.mount(wrapper.get(0));
	return app;
}

frappe.ui.setup_docs_admin = setup_docs_admin;
