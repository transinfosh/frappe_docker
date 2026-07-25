---
title: Debugging
---

Add the following configuration to `launch.json` `configurations` array to start bench console and use debugger. Replace `development.localhost` with appropriate site. Also replace `frappe-bench` with name of the bench directory.

```json
{
  "name": "Bench Console",
  "type": "python",
  "request": "launch",
  "program": "${workspaceFolder}/frappe-bench/apps/frappe/frappe/utils/bench_helper.py",
  "args": ["frappe", "--site", "development.localhost", "console"],
  "pythonPath": "${workspaceFolder}/frappe-bench/env/bin/python",
  "cwd": "${workspaceFolder}/frappe-bench/sites",
  "env": {
    "DEV_SERVER": "1"
  }
}
```

<!-- transinfosh:start -->

## TransInfoSH 调试配置

::: info TransInfoSH 定制
复制 `development/vscode-example` 后，现有 `launch.json` 会明确使用
`${workspaceFolder}/frappe-bench/env/bin/python`，避免调试器误用容器的系统
Python。`settings.json` 使用 Ruff 格式化 Python 文件并在保存时执行格式化，
其配置来源为 Frappe 自身的 `pyproject.toml`。

Dev Container 还预装 PostgreSQL、Redis、Unicode Preview 和 EditorConfig
扩展，便于在同一工作区检查数据库、缓存和文本编码。
:::

<!-- transinfosh:end -->
