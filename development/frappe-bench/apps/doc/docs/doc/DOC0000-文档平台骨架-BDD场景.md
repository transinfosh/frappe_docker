# DOC0000 文档平台骨架 BDD 场景

## Feature: 文档项目

### Scenario: 创建文档项目

```gherkin
Given 内部用户具备文档管理权限
When 用户创建标题为“支付系统”且 slug 为“payment”的 DOC0010
Then 系统应保存文档项目
And status 应为 active
And is_public 应为 0
```

### Scenario: 拒绝重复项目 slug

```gherkin
Given 已存在 slug 为 payment 的 DOC0010
When 用户再次创建 slug 为 payment 的 DOC0010
Then 系统应阻止保存
And 提示项目 slug 已存在
```

## Feature: 文档版本

### Scenario: 创建默认版本

```gherkin
Given 项目 payment 尚无默认版本
When 用户创建 version_key 为 v1 的 DOC0020
Then DOC0020.is_default 应为 1
And DOC0010.default_version 应指向该版本
```

### Scenario: 同一项目下版本 key 唯一

```gherkin
Given 项目 payment 已存在 version_key 为 v1 的 DOC0020
When 用户在 payment 下再次创建 version_key 为 v1 的 DOC0020
Then 系统应阻止保存
```

## Feature: 文档页面

### Scenario: 创建根页面

```gherkin
Given 项目 payment 存在 v1 文档版本
When 用户创建标题为“快速开始”且 slug 为 quick-start 的 DOC0030
Then 页面 path 应为 quick-start
And 页面 status 应为 draft
```

### Scenario: 创建子页面

```gherkin
Given 项目 payment 的 v1 下存在 path 为 api 的父页面
When 用户在 api 下创建 slug 为 create-order 的子页面
Then 子页面 path 应为 api/create-order
```

### Scenario: 父页面必须属于同一版本

```gherkin
Given 项目 payment 存在 v1 和 v2 两个版本
And v1 下存在 path 为 api 的页面
When 用户在 v2 页面中选择 v1 的 api 页面作为父页面
Then 系统应阻止保存
```

## Feature: 页面修订

### Scenario: 显式保存页面时创建修订

```gherkin
Given 项目 payment 的 v1 下存在页面 create-order
When 用户修改 Markdown 内容并保存
Then 系统应创建一条 DOC0031
And revision_no 应为该页面内的下一个序号
And DOC0030.latest_revision 应指向该修订
```

### Scenario: 基于历史修订恢复草稿

```gherkin
Given 页面 create-order 存在 revision_no 为 1 和 2 的修订
When 用户选择恢复 revision_no 为 1 的内容
Then DOC0030.content_markdown 应等于 revision_no 1 的内容
And 系统应创建一条 change_type 为 restore 的新修订
```
