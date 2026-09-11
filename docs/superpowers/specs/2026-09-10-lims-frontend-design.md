# 环境试验 LIMS 独立 Vue 前端设计(第一版)

日期:2026-09-10
状态:待用户审阅

## 1. Summary

为 `test` App(环境试验 LIMS MVP)新增一套**内部实验室人员使用**的独立 Vue SPA,风格与访问方式参考 frappe/helpdesk 的现代前端。第一版页面由侧边栏 + 仪表盘 + 5 个模块(Test Standard、Equipment、Test Catalog、Test Request、Test Report)组成;Test Request 详情页承载样品/测试项维护、生成报价与状态推进。SPA 部署在 `/lims`,不套 Frappe Desk 外壳。

ERPNext 仍是商务事实源:Vue 内用 Autocomplete 选择 Customer/Item,报价生成由现有 Catalog 匹配逻辑完成并在 ERPNext 生成 Quotation;Sales Order 由用户在请求详情页人工关联,ERPNext DocType 不做任何修改。

## 2. Scope

第一版包含:

- 独立 Vue SPA 源码、Vite/frappe-ui 构建配置与 Frappe 挂载页;
- 后端 whitelisted API(会话沿用 Frappe);
- Test Standard / Equipment / Test Catalog 的完整 CRUD 页面;
- Test Request 列表与详情页(样品、测试项、报价、定单关联、状态流转);
- Test Report 列表与编辑页;
- 仪表盘(状态计数、快捷入口、待处理列表)。

第一版不做:用户/角色管理、实时 WebSocket、报告 PDF 套打、结果数值子表、OOS/不符合项、设备排程、客户门户、i18n(界面先中文)。

## 3. Architecture

仓库结构(参考 helpdesk):

```text
<repo>/
├── desk/                         # Vue 3 + Vite + frappe-ui 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── router/index.ts
│       ├── components/
│       ├── pages/
│       │   ├── DashboardPage.vue
│       │   ├── StandardsPage.vue
│       │   ├── EquipmentPage.vue
│       │   ├── CatalogPage.vue
│       │   ├── RequestsPage.vue
│       │   ├── RequestDetailPage.vue
│       │   └── ReportsPage.vue
│       └── api/                  # frappe-ui resource 封装
├── test/
│   ├── api/                      # 后端 whitelisted API
│   │   ├── dashboard.py
│   │   ├── master.py
│   │   ├── requests.py
│   │   ├── samples.py
│   │   ├── reports.py
│   │   └── reference.py
│   ├── www/lims/
│   │   ├── index.html            # 构建产物注入的 Jinja 模板
│   │   └── index.py              # boot context、登录校验
│   └── public/lims/              # Vite build 输出(构建生成,不提交)
```

技术栈:Vue 3、Vite、Vue Router、Pinia、Tailwind CSS、frappe-ui(含 `frappe-ui/vite` 插件)、FrappeUI 基础组件。构建使用与 helpdesk 相同的模式:Vite 将产物写入 `test/public/lims`,`index.html` 使用 Jinja 输出 `boot`。

访问方式:`https://<site>/lims`。`test/www/lims/index.py`:

- `no_cache = 1`;
- Guest 会话重定向到 Frappe 登录页,登录后跳回 `/lims`;
- 构建 boot 数据:site_name、csrf_token、session_user、角色、语言/时区、date/time format、默认路由 `/lims/dashboard`。

## 4. Backend API

统一前缀 `test.api.`;前端通过 `frappeRequest` 调 `/api/method/...`。所有接口均要求登录,服务端检查角色与状态。

### master.py(主数据)

- `test.api.master.get_standards(filters, page)`
- `test.api.master.get_standard(name)`
- `test.api.master.save_standard(doc)`
- `test.api.master.delete_standard(name)`
- `test.api.master.get_equipment_list(filters, page)`、`get_equipment(name)`、`save_equipment(doc)`、`delete_equipment(name)`
- `test.api.master.get_catalog_list(filters, page)`、`get_catalog(name)`、`save_catalog(doc)`、`delete_catalog(name)`、`set_default_catalog(name)`

删除约束:被 Test Request Item / Test Catalog 引用的 Standard、被 Catalog 引用的 Equipment、被请求行引用的 Catalog 不允许删除,只允许停用。

### requests.py

- `test.api.requests.list_requests(filters, page)`;默认排序 `modified desc`;
- `test.api.requests.get_request(name)` 返回请求头 + items + 关联 Sample 摘要 + 已生成报价/报告数量;
- `test.api.requests.save_request(doc)` 新建/更新草稿(只允许 `草稿` 或 `已报价` 状态可编辑);
- `test.api.requests.request_action(name, action)` 执行状态动作,动作集合见第 6 节;
- `test.api.requests.create_quotation(name)` 直接复用现有 DocType controller 逻辑,返回 Quotation name。

### samples.py

- `test.api.samples.list_by_request(test_request)`
- `test.api.samples.create_sample(doc)` / `update_sample(doc)` / `delete_sample(name)`:校验 Sample.test_request 存在且请求未完成/取消。

### reports.py

- `test.api.reports.list_reports(filters, page)`
- `test.api.reports.get_report(name)`
- `test.api.reports.save_report(doc)`;报告字段沿用现有 DocType(含人工 conclusion),不做数值子表。

### reference.py(ERPNext 联动)

- `test.api.reference.customer_search(txt)`、`test.api.reference.item_search(txt)`:基于当前用户对 ERPNext DocType 的读取权限返回匹配项;
- `test.api.reference.get_erpnext_url(doctype, name)`:返回 `/app/<doctype>/<name>` 前端打开链接。

### dashboard.py

- `test.api.dashboard.get_summary()`:各状态请求计数;
- `test.api.dashboard.get_pending()`:检测中请求与未出报告请求两组列表。

## 5. Frontend Pages

通用外壳:左侧导航(环境试验 LIMS;仪表盘、检测请求、检测报告、测试标准、设备、报价目录),顶栏显示当前用户与退出。样式使用 FrappeUI 默认视觉与 status Badge 色块。

### 仪表盘

状态计数卡(草稿/已报价/待检测/检测中/已完成/已取消)、快捷按钮(新建检测请求、新建报告)、待处理列表。

### Test Standard / Equipment / Test Catalog

统一列表模式:搜索框 + 状态筛选 + 表格 + 「新建」。主数据表单用弹层或独立路由(新建/编辑);Catalog 表单含 `item+standard` 联动校验、默认项开关、价格/周期字段。Catalog 与 Equipment 页面通过徽标展示启用状态。

### Test Request

列表页:状态筛选、客户/日期搜索、行内摘要(客户、报价号、样品数、报告数、最近修改)。

详情页:

- 信息头:请求号、客户、公司、日期、状态、Quotation / Sales Order 链接;
- 「样品」区:新增/编辑 Sample(名称、数量、单位、收样日期、状态);
- 「测试项」区:每行 Sample + Item(Autocomplete)+ Test Standard(Autocomplete)+ qty/uom/备注;
- 动作条按当前状态显示按钮;
- 未保存修改离开时二次确认。

新建请求:向导式弹层(客户 → 公司/日期),保存后进入详情继续维护样品与测试项。

### Test Report

列表页支持按请求/状态筛选;新建报告选择 Test Request 与 Sample,自动带出客户与样品名称;编辑表单含检测项目/标准/设备、检测人、结论、状态。报告详情中提供打开 Test Request 的链接。

## 6. Status Actions

状态由服务端动作驱动,前端只渲染当前可用动作,不做自由下拉。

| 当前状态 | 可用动作 | 目标状态 | 校验 |
| --- | --- | --- | --- |
| 草稿 | 生成报价 | 已报价 | 至少一行测试项;未存在未取消报价;Catalog 完整 |
| 已报价 | 标记待检测 | 待检测 | 已填写 sales_order |
| 待检测 | 开始检测 | 检测中 | 有样品且测试项完整 |
| 检测中 | 完成 | 已完成 | 无额外前置 |
| 草稿 | 取消 | 已取消 | — |
| 已报价(报价已取消/删除) | 取消 | 已取消 | ERPNext 报价已取消 |

已完成 / 已取消为终态,第一版不做重开。

## 7. Security

- 所有 API 服务端校验 `frappe.session.user`,按现有角色:Testing Manager 可管理主数据并可删除/取消;Testing User 可日常增改与推进;System Manager 全量。
- API 接收 `doc` 时仅映射白名单字段到 `frappe.get_doc`,不允许客户端传任意字段覆盖只读字段(status/quotation 等)。
- 前端未隐藏为安全边界;所有状态与删除/重复报价校验均在后端执行。

## 8. Build & Development

前置条件:真实 bench(含 Frappe + ERPNext)与 Node/Yarn。本机目前没有可用 bench,因此交付源码 + 构建脚本 + 文档,不本机跑完整构建。

```bash
# 1) 将本 App 放入 bench
cd <bench>/apps
git clone <repo> test

# 2) 安装 App 与站点
bench get-app lims --from-path /path/to/lims
bench --site <site> install-app test

# 3) 前端
cd <bench>/apps/lims/desk
yarn install
yarn build      # 产物写入 ../test/public/lims

# 4) 访问
https://<site>/lims
```

开发模式:`yarn dev`,frappe-ui Vite 插件代理 `/api` 与 `/assets` 到已运行的 bench site;具体地址按 frappe-ui/vite 约定配置。

## 9. Testing & Acceptance

后端:

- `bench --site <site> run-tests --app test` 继续通过;
- 新增 API 集成测试:角色权限、状态非法流转、重复报价拦截、删除被引用主数据拦截、Catalog 缺失/默认冲突报错。

前端验收:

- `yarn build` 无错误,产物可被 `/lims` 页面加载;
- 冒烟流程:登录内部账号 → 建 Test Standard/Equipment/Test Catalog → 新建 Test Request → 添加 Sample 与测试项 → 生成报价(在 ERPNext 出现草稿 Quotation)→ 关联 Sales Order → 开始检测 → 新建 Test Report。

## 10. Assumptions

- 交付源码与构建配置;完整构建验证在用户的真实 bench 进行。
- ERPNext 的 Customer/Item/Quotation/Sales Order 不新增自定义字段与 hook。
- 现有 7 个 DocType 的数据模型保持不动,只新增 `test/api` 与 `www/lims`;如 API 需要补充服务端方法,直接扩展对应模块。
- 界面第一版为中文;不做 i18n 与实时通知。
