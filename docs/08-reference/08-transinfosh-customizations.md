---
title: TransInfoSH 定制索引
---

# TransInfoSH 定制索引

本页只作为导航。具体说明嵌入在对应的官方章节中，便于阅读上下文，也便于以后同步
上游文档时逐项核对。

所有定制段落均由下面的注释包围：

```html
<!-- transinfosh:start -->
<!-- transinfosh:end -->
```

被本 fork 替换的官方行为使用删除线标识；命令和配置代码块只保留当前可执行版本。

## 当前定制

- [开发环境](/05-development/01-development)：默认 PostgreSQL 18、SSH
  访问、GitHub CLI、Codex CLI、空应用清单和安装器参数。
- [调试](/05-development/02-debugging)：Bench 虚拟环境 Python、Ruff
  保存时格式化及开发扩展。
- [自定义应用](/09-concepts/01-custom-app#transinfosh-应用仓库约定)：业务应用
  使用独立 Git 仓库，`frappe_docker` 不跟踪 Bench 中的应用源码。
- [Fork 管理](/08-reference/03-fork-management#keeping-fork-updated)：常规上游
  同步直接快进 `main`，高风险变更再使用 Pull Request。

## 维护规则

同步官方仓库后，应检查每一组 `transinfosh` 标记：官方内容未变化时保留定制；
官方已经实现同等能力时删除重复说明；发生冲突时按当前实际配置更新文档，避免文档
描述超前于代码。
