# 环境试验 LIMS Vue 前端实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `test` App 中新增 `/lims` 独立 Vue SPA 与 whitelisted API,交付源码/构建配置,覆盖配置、请求、样品、报价与报告主流程。

**Architecture:** Vue 3 + Vite + frappe-ui 前端放仓库根 `desk/`,构建到 `test/public/lims`;Frappe 用 `test/www/lims/index.py` 提供 boot;`test/api/*.py` 暴露白名单接口,复用现有 DocType 逻辑。

**Tech Stack:** Vue 3、Vue Router、Pinia、frappe-ui、Vite、Tailwind;Python/Frappe whitelisted API。

**Spec:** `docs/superpowers/specs/2026-09-10-lims-frontend-design.md`

## Global Constraints

- 不改 ERPNext DocType、不新增 DocField/hook 到 Sales Order/Quotation。
- 不删除现有 7 个 DocType;只新增 `test/api/`、`test/www/lims/`、根目录 `desk/` 与测试/文档。
- API 全部要求登录并在服务端按 Testing Manager / Testing User 角色校验。
- 前端第一版中文界面;不做 i18n、实时推送、PDF。

---

### Task 1: Frappe 页面 boot 与目录结构

**Files:**
- Create: `test/www/lims/index.py`
- Create: `test/www/lims/index.html`
- Create: `test/www/lims/__init__.py`

**Interfaces:**
- Produces: `GET /lims` 返回 Vue HTML 与 `boot` JSON;Guest 跳转 `/login?redirect-to=/lims`。

- [ ] Step 1: 创建三个文件;`index.py` 设置 `no_cache=1`、`login_required` 检查、`get_context` 注入 csrf/session/roles/default_route。
- [ ] Step 2: `index.html` 声明 title「环境试验 LIMS」、`{{ boot }}` 为 JSON、引用 `/assets/test/lims/...` 构建产物(由 Vite 注入模板语法)。
- [ ] Step 3: 校验 Python 语法与目录结构。

### Task 2: 后端 API 模块

**Files:**
- Create: `test/api/__init__.py`
- Create: `test/api/security.py`
- Create: `test/api/dashboard.py`
- Create: `test/api/master.py`
- Create: `test/api/samples.py`
- Create: `test/api/requests.py`
- Create: `test/api/reports.py`
- Create: `test/api/reference.py`

**Interfaces:**
- Produces API method names(见 spec §4),供前端 `frappeRequest` 调用。
- `security.ensure_role(roles)` 做角色校验;所有方法在入口调用。

- [ ] Step 1: 实现 `security.py`。
- [ ] Step 2: 实现 `master.py` 的标准/设备/目录 list/get/save/delete,删除前检查引用并阻止。
- [ ] Step 3: 实现 `requests.py`:list/get/save/request_action;`create_quotation` 委托现有 doctype controller。
- [ ] Step 4: 实现 `samples.py`、`reports.py`、`dashboard.py`、`reference.py`。
- [ ] Step 5: 新增 Frappe 集成测试覆盖角色与状态防错;`py_compile` 通过。

### Task 3: 前端脚手架

**Files:**
- Create: `desk/package.json`
- Create: `desk/vite.config.js`
- Create: `desk/postcss.config.js`
- Create: `desk/tailwind.config.js`
- Create: `desk/index.html`
- Create: `desk/src/main.js`
- Create: `desk/src/App.vue`
- Create: `desk/src/index.css`

**Interfaces:**
- Produces: `yarn install && yarn build` 输出到 `../test/public/lims`,页面模板 `../test/www/lims/index.html`。

- [ ] Step 1: package.json 依赖 Vue3/Vite/frappe-ui/Pinia/router;脚本 `dev`、`build`。
- [ ] Step 2: vite.config.js 使用 `frappe-ui/vite` 插件,`buildConfig.outDir = ../test/public/lims`、`indexHtmlPath = ../test/www/lims/index.html`。
- [ ] Step 3: main.js 注册 FrappeUI/Pinia/router;App.vue 输出 RouterView。

### Task 4: API 封装与数据层

**Files:**
- Create: `desk/src/api/index.js`
- Create: `desk/src/stores/user.js`

**Interfaces:**
- Produces `api.request(method, args)`、`api.customerSearch(txt)`、`api.itemSearch(txt)`、`api.erpnextUrl(doctype, name)`。

- [ ] Step 1: 封装 `frappeRequest` 与通用错误抛出。
- [ ] Step 2: user store 读取 boot,提供 `canManage`/`user`。

### Task 5: 外壳、路由、仪表盘

**Files:**
- Create: `desk/src/router/index.js`
- Create: `desk/src/components/AppSidebar.vue`
- Create: `desk/src/pages/DashboardPage.vue`

**Interfaces:**
- Produces 路由:`/lims`(重定向 dashboard)、`/lims/standards`、`/lims/equipment`、`/lims/catalog`、`/lims/requests`、`/lims/requests/:name`、`/lims/reports`、`/lims/reports/:name`。

- [ ] Step 1: 注册路由与守卫(Guest 跳登录)。
- [ ] Step 2: 实现侧边栏与顶栏。
- [ ] Step 3: Dashboard 调用 `dashboard.get_summary/get_pending`。

### Task 6: 主数据页面

**Files:**
- Create: `desk/src/pages/StandardsPage.vue`
- Create: `desk/src/pages/EquipmentPage.vue`
- Create: `desk/src/pages/CatalogPage.vue`

**Interfaces:**
- Consumes `api.master.get*`、`save*`、`delete*`、`setDefaultCatalog`。

- [ ] Step 1: 写通用 `MasterList` 局部组件(搜索、表格、新建/编辑弹层、删除确认)。
- [ ] Step 2: 三个页面配置各自字段与禁用规则。

### Task 7: Test Request 列表与详情

**Files:**
- Create: `desk/src/pages/RequestsPage.vue`
- Create: `desk/src/pages/RequestDetailPage.vue`
- Create: `desk/src/components/RequestFormDialog.vue`
- Create: `desk/src/components/SamplePanel.vue`
- Create: `desk/src/components/RequestItemsPanel.vue`

**Interfaces:**
- Consumes `requests.*`、`samples.*`、`reference.*`。

- [ ] Step 1: 列表页筛选/状态 Badge/行跳转。
- [ ] Step 2: 新建请求向导。
- [ ] Step 3: 详情页样品面板(新建/编辑/删除 Sample)。
- [ ] Step 4: 测试项面板(行选 Sample/Item/Standard)。
- [ ] Step 5: 动作按钮与报价生成(打开 ERPNext 链接)。

### Task 8: Test Report 页面

**Files:**
- Create: `desk/src/pages/ReportsPage.vue`
- Create: `desk/src/pages/ReportDetailPage.vue`

- [ ] Step 1: 列表与新建报告表单。
- [ ] Step 2: 详情/编辑、状态推进、打开 Test Request 链接。

### Task 9: 校验与文档

**Files:**
- Modify: `README.md`(加入 `/lims` 说明与构建命令)

- [ ] Step 1: `python3 -m py_compile`、JSON parse、`node --check`(如可用)。
- [ ] Step 2: 运行现有 Frappe 测试命令并补充文档;提交 commit。
