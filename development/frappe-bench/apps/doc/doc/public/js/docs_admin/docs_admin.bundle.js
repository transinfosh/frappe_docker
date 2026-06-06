import { createApp, h, ref } from "vue";
import DocsAdmin from "./DocsAdmin.vue";

export function setup_docs_admin(wrapper, options = {}) {
	const rootRef = ref(null);
	const app = createApp({
		setup() {
			return { rootRef };
		},
		render() {
			return h(DocsAdmin, {
				ref: rootRef,
				pageControls: options.pageControls || {},
			});
		},
	});

	app.mount(wrapper.get(0));
	app.rootRef = rootRef;
	return app;
}

frappe.ui.setup_docs_admin = setup_docs_admin;
