<template>
	<div class="docs-admin">
		<div class="docs-admin__body">
			<aside class="docs-admin__tree">
				<div v-if="loading" class="docs-admin__empty">加载中</div>
				<div v-else-if="!pageTree.length" class="docs-admin__empty">暂无文档页面</div>
				<ul v-else>
					<DocTreeNode
						v-for="page in pageTree"
						:key="page.name"
						:node="page"
						:selected-page="selectedPage"
						@select="selectPage"
					/>
				</ul>
			</aside>

			<main class="docs-admin__editor">
				<section v-if="currentPage" class="docs-admin__editor-shell">
					<div v-if="editorMode === 'Milkdown'" ref="milkdownRoot" class="docs-admin__milkdown"></div>
					<textarea
						v-else
						v-model="contentMarkdown"
						class="docs-admin__textarea"
						spellcheck="false"
					></textarea>
				</section>
				<section v-else class="docs-admin__welcome">
					<h2>选择左侧文档开始编辑</h2>
				</section>
			</main>
		</div>
	</div>
</template>

<script setup>
import { defaultValueCtx, Editor, editorViewOptionsCtx, rootCtx } from "@milkdown/core";
import { listener, listenerCtx } from "@milkdown/plugin-listener";
import { commonmark } from "@milkdown/preset-commonmark";
import { getMarkdown, markdownToSlice } from "@milkdown/utils";
import { computed, defineComponent, h, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

const props = defineProps({
	pageControls: { type: Object, default: () => ({}) },
});

const projects = ref([]);
const versions = ref([]);
const pageTree = ref([]);
const selectedProject = ref("");
const selectedVersion = ref("");
const selectedPage = ref("");
const currentPage = ref(null);
const contentMarkdown = ref("");
const loading = ref(false);
const saving = ref(false);
const milkdownRoot = ref(null);
const milkdownEditor = ref(null);
const milkdownAvailable = ref(true);

const editorMode = computed(() => (milkdownAvailable.value ? "Milkdown" : "Markdown"));

const DocTreeNode = defineComponent({
	name: "DocTreeNode",
	props: {
		node: { type: Object, required: true },
		selectedPage: { type: String, default: "" },
	},
	emits: ["select"],
	setup(props, { emit }) {
		return () =>
			h("li", { class: "docs-admin__tree-node" }, [
				h(
					"button",
					{
						class: {
							"docs-admin__tree-button": true,
							"is-active": props.node.name === props.selectedPage,
						},
						onClick: () => emit("select", props.node.name),
					},
					props.node.title
				),
				props.node.children?.length
					? h(
							"ul",
							props.node.children.map((child) =>
								h(DocTreeNode, {
									key: child.name,
									node: child,
									selectedPage: props.selectedPage,
									onSelect: (name) => emit("select", name),
								})
							)
						)
					: null,
			]);
	},
});

onMounted(async () => {
	await loadProjects();
});

onBeforeUnmount(() => {
	destroyMilkdown();
});

defineExpose({
	savePage,
	setProject,
	setVersion,
});

async function call(method, args = {}) {
	const result = await frappe.call({ method, args });
	return result.message || [];
}

async function loadProjects() {
	loading.value = true;
	try {
		projects.value = await call("doc.doc.api.admin.get_project_spaces");
		selectedProject.value = projects.value[0]?.name || "";
		setSelectOptions(
			props.pageControls.project,
			projects.value.map((project) => ({ value: project.name, label: project.title })),
			selectedProject.value
		);
		await onProjectChange();
	} finally {
		loading.value = false;
	}
}

async function onProjectChange() {
	currentPage.value = null;
	selectedPage.value = "";
	pageTree.value = [];
	versions.value = selectedProject.value
		? await call("doc.doc.api.admin.get_versions", { project: selectedProject.value })
		: [];
	selectedVersion.value =
		versions.value.find((version) => version.is_default)?.name || versions.value[0]?.name || "";
	setSelectOptions(
		props.pageControls.version,
		versions.value.map((version) => ({
			value: version.name,
			label: version.title || version.version_key,
		})),
		selectedVersion.value
	);
	await loadTree();
}

async function setProject(project) {
	if (!project || project === selectedProject.value) return;

	selectedProject.value = project;
	await onProjectChange();
}

async function setVersion(version) {
	if (!version || version === selectedVersion.value) return;

	selectedVersion.value = version;
	await loadTree();
}

async function loadTree() {
	currentPage.value = null;
	selectedPage.value = "";
	destroyMilkdown();
	if (!selectedVersion.value) {
		pageTree.value = [];
		return;
	}

	pageTree.value = await call("doc.doc.api.admin.get_page_tree", { doc_version: selectedVersion.value });
	const firstPage = findFirstPage(pageTree.value);
	if (firstPage) {
		await selectPage(firstPage.name);
	}
}

async function selectPage(pageName) {
	selectedPage.value = pageName;
	currentPage.value = await call("doc.doc.api.admin.get_page_detail", { page: pageName });
	contentMarkdown.value = currentPage.value.content_markdown || "";
	await mountMilkdown();
}

async function savePage() {
	if (!currentPage.value) {
		frappe.show_alert({ message: __("请选择文档页面"), indicator: "orange" });
		return;
	}

	saving.value = true;
	try {
		if (milkdownEditor.value) {
			contentMarkdown.value = normalizeMermaidMarkdown(milkdownEditor.value.action(getMarkdown()));
		}
		currentPage.value = await call("doc.doc.api.admin.save_page_content", {
			page: currentPage.value.name,
			content_markdown: contentMarkdown.value,
		});
		contentMarkdown.value = currentPage.value.content_markdown || "";
		frappe.show_alert({ message: __("已保存"), indicator: "green" });
		await mountMilkdown();
	} finally {
		saving.value = false;
	}
}

function findFirstPage(nodes) {
	for (const node of nodes) {
		return node;
	}
	return null;
}

function setSelectOptions(field, options, value) {
	if (!field) return;

	field.df.options = options.map((option) => ({ value: option.value, label: option.label }));
	field.set_options(value);
	field.set_value(value);
}

async function mountMilkdown() {
	destroyMilkdown();
	if (!milkdownAvailable.value || !currentPage.value) return;

	await nextTick();
	if (!milkdownRoot.value) return;

	try {
		const editor = Editor.make()
			.config((ctx) => {
				ctx.set(rootCtx, milkdownRoot.value);
				ctx.set(defaultValueCtx, contentMarkdown.value);
				ctx.update(editorViewOptionsCtx, (options) => ({
					...options,
					handlePaste(view, event) {
						const text = event.clipboardData?.getData("text/plain") || "";
						if (!shouldParseMarkdownPaste(text)) return false;

						event.preventDefault();
						const slice = markdownToSlice(text)(ctx);
						view.dispatch(view.state.tr.replaceSelection(slice).scrollIntoView());
						return true;
					},
				}));
				ctx.get(listenerCtx).markdownUpdated((_ctx, markdown) => {
					contentMarkdown.value = markdown;
				});
			})
			.use(commonmark)
			.use(listener);
		await editor.create();
		milkdownEditor.value = editor;
	} catch (error) {
		console.warn("Milkdown 初始化失败，已切换到 Markdown 文本编辑。", error);
		milkdownAvailable.value = false;
	}
}

function shouldParseMarkdownPaste(text) {
	if (!text.trim()) return false;

	return [
		/^#{1,6}\s+\S/m,
		/^```/m,
		/^\s*[-*+]\s+\S/m,
		/^\s*\d+\.\s+\S/m,
		/^\s*>\s+\S/m,
		/^\|.+\|\s*$/m,
		/^\s*\|?\s*:?-{3,}:?\s*\|/m,
		/\[[^\]]+\]\([^)]+\)/,
		/(\*\*|__)[^*_]+(\*\*|__)/,
		/`[^`]+`/,
	].some((pattern) => pattern.test(text));
}

function normalizeMermaidMarkdown(markdown) {
	return normalizeIndentedMermaidBlocks(normalizeFencedMermaidBlocks(markdown || ""));
}

function normalizeFencedMermaidBlocks(markdown) {
	return markdown.replace(/```(\w*)\n([\s\S]*?)```/g, (match, language, content) => {
		if (language && language !== "mermaid") return match;

		const decodedContent = decodeMermaidEntities(content);
		if (language === "mermaid" || isMermaidContent(decodedContent)) {
			return `\`\`\`mermaid\n${decodedContent.replace(/\s+$/, "")}\n\`\`\``;
		}
		return match;
	});
}

function normalizeIndentedMermaidBlocks(markdown) {
	const lines = markdown.split("\n");
	const normalized = [];

	for (let index = 0; index < lines.length; index += 1) {
		const line = lines[index];
		if (!/^( {4}|\t)/.test(line)) {
			normalized.push(line);
			continue;
		}

		const block = [];
		while (index < lines.length && /^( {4}|\t|$)/.test(lines[index])) {
			block.push(lines[index].replace(/^( {4}|\t)/, ""));
			index += 1;
		}
		index -= 1;

		const content = decodeMermaidEntities(block.join("\n").replace(/\s+$/, ""));
		if (isMermaidContent(content)) {
			normalized.push("```mermaid", content, "```");
		} else {
			normalized.push(...block.map((blockLine) => (blockLine ? `    ${blockLine}` : "")));
		}
	}

	return normalized.join("\n");
}

function isMermaidContent(content) {
	return /^\s*(flowchart|graph|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|journey|pie|mindmap|timeline|gitGraph|quadrantChart)\b/m.test(
		content
	);
}

function decodeMermaidEntities(content) {
	return content
		.replace(/&gt;/g, ">")
		.replace(/&lt;/g, "<")
		.replace(/&amp;/g, "&")
		.replace(/&quot;/g, '"')
		.replace(/&#39;/g, "'");
}

function destroyMilkdown() {
	if (!milkdownEditor.value) return;
	milkdownEditor.value.destroy();
	milkdownEditor.value = null;
}
</script>
