# AGENTS.md — 旭博检测中心OS(app: `lims`)

给在这个仓库里干活的 AI 和工程师:先读这份,再读 `README.md`。
这份文件同时是**产品需求 + 工程约定**的入口,改代码前先看第 1 节硬约束。

---

## 0. 一句话定位

以 **ERPNext 为唯一事实源**的检测中心 SaaS:用户在 Frappe **Desk** 里看到的是
「旭博检测中心OS」的 9 个业务中心(首页/客户/销售/检测/实验室/质量/客服/AI/系统管理),
而不是 ERPNext、LIMS、Helpdesk 这些技术组件。

app 名 `lims`,模块 `Testing`,包目录 `lims/`,Desk 入口 `/desk/首页`。

---

## 1. 硬约束(违反会出事故)

1. **不新建 app、不改 ERPNext 原生 DocType 结构**。扩展只用两种方式:
   - ERPNext DocType 上加定制字段 → 写在 `lims/setup/install.py::sync_custom_fields()`,字段名 `lims_` 前缀;
   - 新业务 DocType → 放 `lims/testing/doctype/`,`module = Testing`。
2. **不要给 ERPNext 主数据建镜像表**(早期做过 `LIMS Customer`/`LIMS Contact`,已删除)。
   客户/联系人/报价/订单/项目/任务/资产都是 ERPNext 的,LIMS 只读 + 定制字段。
3. **Desk 结构文件即事实源**:`lims/testing/workspace/`、`lims/workspace_sidebar/`、
   `number_card/`、`dashboard_chart/` 下的 JSON 由 migrate 导入(app 里没有对应文件的会被当孤儿删掉)。
   改完 JSON **必须把 `modified` 改成比库里更新的时间戳**,否则 migrate 会跳过
   (`frappe/modules/import_file.py` 的时间戳/哈希判断)。
4. **Workspace 名必须与同名 Workspace Sidebar 成对**:Frappe 用工作区名去取侧边栏,
   名字对不上左侧导航就是空的。
5. `Number Card` / `Dashboard Chart` 的 **`dynamic_filters_json` 在浏览器里 eval**:
   只能写 `frappe.datetime.*`、`frappe.defaults.*`、`frappe.boot.*`;写 `frappe.utils.*` 会报
   “Invalid expression set in filter”。
6. **权限只用中文角色**(见第 3 节),新增 DocType 必须带 permissions;
   新增 ERPNext 单据的只读权限加到 `lims/setup/install.py::ERPNext_READ_GRANTS`。
7. **所有 setup 逻辑必须幂等**,挂到 `after_migrate`
   (`lims/setup/install.py::run_schema_cleanup()` / `lims/setup/detection_os.py::setup_detection_os()`)。
8. 改数据库结构前**先备份站点**;不要直接手改生产库。

---

## 2. 环境与常用命令

```bash
# 本地 bench(开发环境)
/Users/carl/pilot/benches/carl         # site1.local
# apps: frappe / erpnext / lims / telephony / helpdesk

# 把工作区代码同步到 bench 并迁移
rsync -a --exclude='.git' --exclude='node_modules' <repo>/ \
  /Users/carl/pilot/benches/carl/apps/lims/
/Users/carl/pilot/bin/pilot --bench carl frappe --site site1.local migrate
```

验证约定(重要):**一次性脚本 + 单事务 + 最后 `frappe.db.rollback()`**,
不要往 dev 站点留测试数据。每次改动至少跑:
① migrate 两次(幂等)② 端到端冒烟 ③ 角色可见性 ④ 工作区块解析(`unresolved=[]`)。

批量维护 9 个中心的结构用 `dev_tools/build_desk_structure.py`
(会重写那些 JSON 并自动盖新的 `modified` 时间戳)。

---

## 3. 角色与权限

10 个中文角色(`desk_access=1`),权限矩阵写在每个 DocType 的 `permissions` 里:

| 角色 | 可见中心 | 关键写权限 |
| --- | --- | --- |
| 总经理 | 全部(业务单据只读) | 无(全只读) |
| 销售经理 | 客户中心、销售中心 | Test Agreement Price、Industry(全权) |
| 销售 | 客户中心、销售中心 | 无(只读) |
| 项目经理 | 客户中心、检测中心、实验室 | Test Request/Sample/Test Plan/Test Report/Nonconformance/Equipment Usage(全权) |
| 检测工程师 | 检测中心、实验室 | Test Request/Sample/Test Report/Nonconformance/Equipment Usage(读+写+建) |
| 实验员 | 检测中心、实验室、质量中心 | Test Plan、Calibration Record、Equipment Usage(读+写+建) |
| 技术负责人 | 实验室、质量中心 | Test Standard/Test Method、Quality Document、Calibration Record |
| 质量负责人 | 检测中心、质量中心 | Test Report、Test Nonconformance、Quality Document、Test Standard/Test Method |
| 客服 | 客户中心、客服中心 | 工单(Helpdesk HD Ticket) |
| AI管理员 | AI中心 | Test Standard/Test Method、Quality Document(只读,作为知识源) |

另:首页 / AI中心 对所有登录用户可见;系统管理只对 System Manager 可见。
旧角色 `Testing Manager`/`Testing User` 已停用,用户迁移到「总经理+项目经理」/「检测工程师」。

Helpdesk 有自己的角色体系(它的 DocType 只认这些):`客服`/`销售` → `Agent`,
`销售经理`/`总经理` → `Agent Manager`,由 `ensure_helpdesk_roles()` 在 migrate 时补齐。

---

## 4. 九大中心的开发要求

> 每个中心的入口/快捷按钮/指标卡定义在 `lims/testing/workspace/<中心>/<中心>.json`,
> 左侧导航在 `lims/workspace_sidebar/<中心>.json`(9 个中心条目一致)。

### 4.1 首页(home)

- 定位:登录落地页,回答「今天有什么要干」。
- 内容:9 个中心入口(URL 快捷方式)+ 6 张指标卡(待报价、检测中、待出报告、本月销售、进行中项目、本月报告)。
- 数据来源:Test Request / Test Report / Sales Order / Project。
- 验收:卡片数字与下钻列表口径一致。
- 待办:今日待办 / 超期预警卡片。

### 4.2 客户中心(customers)

- 定位:客户与联系人主数据,直接用 ERPNext `Customer` / `Contact` / `Address`,**不建镜像表**。
- 入口:客户、联系人、客户分组、地区、地址;快捷:+新建客户 / +新建联系人。
- 中国企业约定:
  - `customer_name` = **工商全称**(客户主键),`lims_short_name` = 简称;
  - `tax_id` = **统一社会信用代码**(18 位校验,同税号不允许重复建客户);
  - `lims_enterprise_nature`(军工集团/国有企业/民营企业/外资企业/高校与科研院所/政府机构/事业单位/其他)、
    `lims_customer_tier`(战略/重点/普通/潜在)、`lims_legal_representative`、`lims_registered_address`;
  - 开票资料:名称=客户名称、税号=tax_id、地址电话走 Address(ERPNext 自带 China 地址模板),
    开户行/账号/开票电话用 `lims_bank_name` / `lims_bank_account` / `lims_invoice_phone`;
  - 地区用 Territory 树(`China` 组 → 34 省级;地级市按需补 `lims/data/china_regions.py`);
  - 客户分组已初始化中文分类(军工集团/国有企业/民营企业/外资企业/高校与科研院所/政府机构/同业分包)。
- 联系人:整名写 `first_name`(如「李四」),`last_name` 留空;`lims_role`(商务/技术/财务/收样/管理层/其他)、
  `lims_wechat`、`lims_extension`、`lims_receives_report`、`lims_receives_invoice`;
  一个联系人可挂多个客户(原生 Dynamic Link,集团客户常见)。
- 验收:带行业建客户 → 行业协议价能命中;重复/非法税号被拦。

### 4.3 销售中心(sales)

- 数据来源:ERPNext CRM 模块(Lead / Opportunity / Prospect / Contract)+ Quotation / Sales Order / Project。
  **不装独立 CRM app**(erpnext 自带的能力已经够用)。
- 入口:线索、商机、潜在客户、报价单、销售订单、合同、项目;快捷:+商机 / +报价 / +合同。
- 指标卡:待跟进商机、待处理报价;图表:销售漏斗(Opportunity 按 status 分组)。
- 业务规则:生成报价单时**单据主体取「发票抬头」(不填=委托单位)**,协议价仍按委托单位取;
  转 Sales Order 必须补 `delivery_date`(ERPNext v16 强制,已做兜底)。
- 验收:报价单主体=发票抬头、单价=委托单位协议价、转单成功。

### 4.4 检测中心(testing,核心)

- 数据来源:本 app 的 Test Request / Test Request Item / Sample / Test Plan / Test Report /
  Test Nonconformance / Equipment Usage + ERPNext 的 Project/Task
  (委托单保存后自动建 Project,测试项同步为 Task)。
- 入口:检测委托、样品、试验计划、设备使用记录、项目、试验任务、检测报告、不合格/异常;
  快捷:+检测委托 / +样品登记 / +试验计划 / +检测报告。
- 指标卡:待受理、检测中、待审核报告、已完成、超期(`required_by < 今天` 且未完成/未取消)。
- 关键规则:
  - 委托单上的三个主体:委托单位 `customer`、发票抬头 `invoice_customer`、报告抬头 `report_customer`
    (后两者可空,不填即与委托单位一致);
  - 委托单里不出现 Rate/Amount,也不向客户展示设备;
  - Test Report 的「报告抬头」按 `report_customer or customer` 带出,报告状态回写到委托单 `report_status`;
  - 状态机:草稿 → 已报价 → 待检测 → 检测中 → 已完成 / 已取消;取消前必须先取消关联报价单。
- 验收:委托 → 报价 → 转单 → 报告 → 状态回写全链路。

### 4.5 实验室(lab)

- 数据来源:ERPNext Asset(设备台账)+ 本 app 的 Calibration Record、Equipment Usage
  + ERPNext Asset Maintenance / Maintenance Log / Asset Repair、Location。
- 入口:设备、实验室/位置、校准记录、维护计划/记录、维修、设备使用记录;快捷:+设备 / +校准记录。
- 设备字段(Asset 定制):`calibration_status`、`last_calibration_date`、`calibration_due_date`、
  `calibration_interval_days`、`cnas_no`、`capability_scope`、`frequency_range`、`thrust`。
- 关键规则:Calibration Record 增删改都要回写 Asset 的校准快照(删掉最后一条要回退成「未校准」);
  设备使用登记会拦下校准过期的设备。
- 指标卡:待校准设备(30 天内到期或已过期)、维修中设备、停机设备。
- 验收:建校准记录 → Asset 快照更新 → 过期设备登记使用被拦。

### 4.6 质量中心(quality)

- 数据来源:Test Standard、Test Method、Quality Document(受控文件)、Test Nonconformance、Test Report。
- 入口:检测标准、检测方法、质量文件、不合格/异常、检测报告;快捷:+标准 / +方法 / +受控文件。
- 关键规则:质量文件转「受控」前必须有批准人;文件编号+版本不可重复;
  `review_due_date` 到期前提示复审;普通实验员对质量中心只读。
- 指标卡:标准总数、受控文件数、待复审文件。
- 待办:文件发放/回收/修订记录、期间核查、能力验证、人员资质与培训、试剂耗材。

### 4.7 客服中心(support)

- 数据来源:**Helpdesk**(HD Ticket / HD Team / HD SLA / HD Article)
  + ERPNext Warranty Claim / Customer / Contact。
- 入口:工单、工单类型、优先级、工单状态、客服组、服务协议、服务日历、知识文章、文章分类、保修索赔、客户、联系人;
  快捷:+新建工单。
- 指标卡:待处理工单(`status ∈ Open/Replied`)、超时工单(`agreement_status = Failed`)。
- 验收:客服角色能建单/看单,Desk 与 Helpdesk 门户都能看到同一批工单。
- 待办:客户门户(自助提单/查进度)、满意度调查。

### 4.8 AI中心(ai,规划中)

- 现状:占位工作区,只放说明,**不放会 404 的链接**。
- 规划:报价助手、标准助手、报告助手、实验室助手、销售助手;知识源 = 质量中心的标准/方法/受控文件。
- 落地要求(做的时候):新增「AI 会话 / 提示词 / 技能」类 DocType(module=Testing);
  LLM 调用与配额必须走服务端;权限先给 AI管理员;AI 产出必须能追溯到来源文档。

### 4.9 系统管理(settings)

- 只对 System Manager 可见:用户、角色、角色档案、系统设置、表单定制、自定义字段、工作流、邮件账户、错误日志。
- 验收:非 System Manager 看不到这个中心。

---

## 5. 数据模型速查

| 分组 | DocType |
| --- | --- |
| 检测业务 | Test Request、Test Request Item、Sample、Test Report、Test Report Item、Test Nonconformance、Equipment Usage、Test Plan、Test Task |
| 主数据 | Test Standard、Test Method、Industry、Test Agreement Price |
| 实验室 | Calibration Record |
| 质量 | Quality Document、Quality Document Standard |
| 系统 | LIMS Settings(机构名称/CNAS/CMA/报告声明/默认报价条款) |

约定:业务单据用 `format:XX-{YYYY}-{#####}` 自动命名;字段 label 用中文;
会被列表/指标卡过滤的字段加 `search_index: 1`(`status`、日期、外键已覆盖)。

**打印格式**:`lims/testing/print_format/` 下三个模板(检测委托单 / 检测报价单 / 检测报告),
由 `dev_tools/build_print_formats.py` 生成并设为对应单据的默认打印格式;
抬头与页脚读 `LIMS Settings`。改版式:改脚本 → 运行 → migrate。

**检测报告签发**:Test Report 是**可提交单据**,状态机 = Frappe Workflow「检测报告签发」
(定义在 `lims/setup/quality_workflow.py`,幂等创建):

```text
待检测 → 检测中 → 待审核 → 待批准 → 已出具(docstatus=1) → 已作废(docstatus=2)
                     ↑  └─ 退回修改 ─┘
```

- 权限:批准签发需要 `submit`、作废需要 `cancel`(只给了项目经理/质量负责人/总经理);
- 留痕字段:`tested_by` / `reviewed_by+reviewed_on` / `approved_by+approved_on+issued_on` /
  `void_reason+voided_by+voided_on`,由 `test_report.py::stamp_sign_off()` 与 `before_cancel()` 打;
- **坑**:提交(submit)时 Frappe 只跑 `validate` + `before_submit`,**不跑 `before_save`**,
  所以签发留痕必须写在 `validate` 里;作废原因字段要 `allow_on_submit=1`(已签发的报告上要能填);
- `api/reports.save_report` 不接受前端传 `status`,状态只能通过工作流流转。

**初始主数据**:`lims/data/starter_masters.py`(14 标准 + 14 方法 + 8 检测项目),
安装时自动补齐,老站点调 `lims.api.master.seed_starter_masters`;只补缺不覆盖。
批量导入客户/联系人/设备用 `lims/data/import_templates/*.csv`。

**客户门户(erpnext-nuxt)**:客户端门户是独立项目 `~/claude/erpnext-nuxt/nuxt-app`,
通过 `lims/api/portal.py` 取数(契约与门户的 `shared/types/portal.ts` 一致)。

- 身份两种:门户集成账号(角色 `客户门户` + Helpdesk `Agent`,必须显式传 `customer`);
  客户联系人登录(Website User + Contact 关联客户,自动定位自己公司)。
- 任何接口都先 `resolve_customer()` 再做单据归属校验,禁止跨客户读取;
  hooks 里的 `has_website_permission` 覆盖 Test Request / Test Report / Quotation,
  客户联系人用 Frappe 原生接口/打印视图也只能看到自己公司的单据。
- 工单走 Helpdesk:`HD Customer` 由 ERPNext Customer 映射而来(带 HD Customer Member 联系人),
  `HD Ticket.lims_test_request` 定制字段回链委托单;非 Agent 用户不能代客户建单,所以集成账号要给 `Agent`。
- 对接步骤、门户 `.env`、状态映射、路由改造清单见 `docs/portal-api.md`。

---

## 6. 部署与性能

- 开发用 pilot 的 dev/lite 模式(会 watch、空闲 5 分钟重启 worker);**正式环境必须走 production**
  (`pilot setup production`:gunicorn + nginx + gzip/brotli)。Desk 首屏 JS 约 3.6MB 未压缩,
  生产环境压缩 + 缓存后首屏明显更快,也没有空闲重启带来的冷启动。
- 实测(dev 环境,warm):Desk 页面 15–21ms、`get_bootinfo` ~150ms、工作区/指标卡近 0ms ——
  服务端不是瓶颈,慢在首屏 JS 与冷启动。
- 装了 helpdesk/telephony 后 boot 会多遍历它们的侧边栏/工作区,可接受;
  装了但长期不用的 app 建议卸载。
- **卸载 app 后要清残留**:`sites/apps.txt`、`site_config.installed_apps`、桌面图标(已由
  `remove_orphan_desktop_icons()` 自动清理)、孤儿表。
- 数据量大后先看 `EXPLAIN` 再谈缓存;我们的过滤字段都建了索引。

---

## 7. 路线图

**P0(不做就会被业务催)**

1. ~~打印模板:检测委托单、报价单、检测报告 PDF~~ ✅ 已完成(`lims/testing/print_format/`)
2. ~~报告三级签发与作废留痕~~ ✅ 已完成(Workflow「检测报告签发」)
3. ~~初始主数据:标准/方法/检测项目~~ ✅ 已完成;客户/联系人/设备用 CSV 模板导入
4. 生产环境部署 + gzip,并隐藏非本 app 的工作区(只留 9 个中心)。← 剩下的 P0

**P1(从「能跑」到「好用」)**

5. AI 中心首批助手(报价/标准/报告助手),知识源 = 质量中心。
6. 客户门户:客户自助查进度、下载报告、提交工单(Helpdesk 门户)。
7. 样品流转与条码(收样→流转→留样→处置)、设备期间核查/能力验证、试剂耗材台账。
8. 多公司/多实验室隔离(User Permission 按公司/实验室)。

**P2(规模化与商业化)**

9. 计费与订阅(按中心/用户/报告量)、AI 用量计费。
10. 电子签章、报告防篡改(哈希存证)、审计日志导出。
11. 移动端/小程序(复用 `lims/api/` 现有接口)、离线收样。
12. SaaS 多租户(一租户一 site,或单站点多公司 + 权限隔离)。

---

## 8. 常见坑(踩过的)

| 坑 | 现象 | 正解 |
| --- | --- | --- |
| hooks 里写 `custom_fields` | 字段一个都建不出来 | 用 `install.py::create_custom_fields` |
| Workspace JSON 的 `modified` 没更新 | migrate 跳过导入,页面还是旧的 | 盖一个新的时间戳 |
| Workspace 名 ≠ Sidebar 名 | 左侧导航空白 | 成对命名 |
| `dynamic_filters_json` 写了 `frappe.utils.*` | “Invalid expression set in filter” | 改用 `frappe.datetime.*` |
| 某个 link 指向不存在的 DocType | 整组卡片静默消失 | 先用脚本扫一遍链接再 migrate |
| 派生字段用 `frappe.db.set_value` 改父单据 | 保存中的单据报 TimestampMismatch | 加 `update_modified=False` |
| 删掉最后一条校准记录 | Asset 快照不回退 | `on_trash` 时排除自身再查 |
| 只删了 app 目录 | 残留图标/表/`apps.txt` 条目 | 用 `pilot uninstall-app`,再清残留 |
