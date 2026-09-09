### Testing / 检测委托管理

一个以 **检测委托单(Testing Entrustment)** 为核心的 ERPNext 自定义 Frappe App。

ERPNext 是事实源(Source of Truth)。本 App 不复制、不同步客户/项目/报价单据,而是直接 `Link` 到
ERPNext 的 `Customer`、`Item`、`Quotation`、`Project` 等 DocType,只在 ERPNext 的
`Quotation` 上增加一个回链字段,用于把"委托单 → 报价单"打通。

---

### 第一层:ERP 核心

```
ERPNext
  Customer       客户(事实源)
  Item           检测项目(事实源)
  Quotation      报价单(事实源,由委托单生成)
  Sales Order    销售订单(ERPNext 标准流程)
  Invoice        发票(ERPNext 标准流程)
  Project        项目(后续关联)
  Task           任务(后续关联)

Frappe Custom App (本 App)
  Testing Entrustment      检测委托单
  Testing Entrustment Item 委托项目(子表)
  Sample                  样品
  Test Report             检测报告
```

---

### DocType 1:Testing Entrustment(检测委托单)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 客户 | `customer` | Link `Customer` | 必填 |
| 联系人 | `contact` | Link `Contact` | 按客户过滤 |
| 委托日期 | `transaction_date` | Date | 默认今天 |
| 状态 | `status` | Select | 草稿 / 待报价 / 已报价 / 报价已确认 / 检测中 / 已完成 / 已取消 |
| 公司 | `company` | Link `Company` | 生成报价单时使用 |
| 币种 | `currency` | Link `Currency` | 自动带出公司默认币种 |
| 委托项目 | `items` | Table `Testing Entrustment Item` | 明细 |
| 预计金额 | `estimated_amount` | Currency | 子表金额合计,只读 |
| 报价单 | `quotation` | Link `Quotation` | 「创建报价」后自动回填 |
| 项目 | `project` | Link `Project` | 后续关联项目 |

编号规则:`TE-{YYYY}-{#####}`。

### DocType 2:Testing Entrustment Item(委托项目,子表)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 检测项目 | `item` | Link `Item` | 必填 |
| 项目名称 | `item_name` | Data | 从 Item 带出 |
| 数量 | `qty` | Float | 默认 1 |
| 单价 | `rate` | Currency | |
| 金额 | `amount` | Currency | `qty × rate`,自动计算 |
| 检测标准 | `testing_standard` | Data | 例如 GB/T、ISO 标准号 |
| 备注 | `remarks` | Text | |

---

### DocType 3:Sample(样品)

样品挂在检测委托单下,收样后按委托单继续流转到检测报告。

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 检测委托 | `entrustment` | Link `Testing Entrustment` | 必填 |
| 样品名称 | `sample_name` | Data | 必填 |
| 收样日期 | `received_date` | Date | 默认今天 |
| 样品状态 | `status` | Select | 待收样 / 已收样 / 检测中 / 已检测 / 已退样 |
| 客户 | `customer` | Link `Customer` | 从委托单自动带出 |
| 检测项目 | `item` | Link `Item` | 对应委托单中的检测项目 |
| 样品数量 | `quantity` | Float | 默认 1 |
| 单位 | `uom` | Link `UOM` | |
| 备注 | `remarks` | Text | |

编号规则:`SPL-{YYYY}-{#####}`。

### DocType 4:Test Report(检测报告)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 检测委托 | `entrustment` | Link `Testing Entrustment` | 必填 |
| 样品 | `sample` | Link `Sample` | 仅显示同一委托单下的样品 |
| 报告日期 | `report_date` | Date | 默认今天 |
| 状态 | `status` | Select | 待检测 / 检测中 / 已出具 / 已作废 |
| 客户 | `customer` | Link `Customer` | 从委托单自动带出 |
| 检测项目 | `item` | Link `Item` | |
| 检测标准 | `testing_standard` | Data | |
| 检测人 | `tested_by` | Link `User` | |
| 检测结论 | `conclusion` | Text Editor | |
| 备注 | `remarks` | Text | |

编号规则:`TR-{YYYY}-{#####}`。

在委托单页面可通过 **检测业务 → 新建样品 / 新建报告** 快速创建,创建后自动带回委托单;委托单表单的
关联面板也会展示这些 Sample / Test Report。

---

### 创建报价按钮(打通 ERPNext)

委托单提交后,工具栏出现 **创建报价**:

```
Testing Entrustment(已提交)
        │  创建报价(自动)
        ▼
Quotation(Draft)
        │  Quotation.testing_entrustment 回链
        ▼
Testing Entrustment.status = 已报价
```

自动生成的 Quotation:

- 客户、联系人、日期、公司、币种来自委托单;
- 明细行逐行转为 Quotation Item(`item/qty/rate/amount/检测标准备注进入描述`);
- 价目表按客户默认价目表 → Selling Settings 默认价目表 → 同币种启用销售价目表 的顺序自动选取;
- ERPNext 仍可正常编辑、提交该报价单。

Quotation 提交后,委托单状态自动变为 **报价已确认**;报价单取消/删除后,委托单回到 **待报价** 并可重新创建报价。

---

### 目录结构

参考 frappe/helpdesk 的模块化组织方式:

```text
test/
├── hooks.py                       # required_apps = erpnext, doc_events(Quotation)
├── modules.txt                    # Testing
├── integrations/
│   └── erpnext_quotation.py       # Quotation ↔ 委托单回写
├── setup/
│   └── install.py                 # 角色 + Quotation 回链字段(幂等)
└── testing/
    ├── doctype/
    │   ├── testing_entrustment/       # 主表
    │   │   ├── testing_entrustment.json
    │   │   ├── testing_entrustment.py # 金额/状态/创建报价
    │   │   ├── testing_entrustment.js # 创建报价按钮/行金额/联系人过滤
    │   │   └── test_testing_entrustment.py
    │   ├── testing_entrustment_item/  # 委托项目(子表)
    │   ├── sample/                    # 样品
    │   └── test_report/               # 检测报告
    └── workspace/testing/             # Testing 模块首页
```

---

### Installation

在已有 ERPNext bench 上:

```bash
bench get-app https://github.com/<your-org>/test --branch <branch>
bench --site <your-site> install-app test
bench --site <your-site> migrate
```

前置条件:

- 站点已安装 ERPNext;
- 已配置至少一家 Company 及其默认币种;
- 已存在适用的销售价目表(Selling Price List);
- 用户需要 `Testing Manager` / `Testing User` 角色;若要生成/提交报价,还需 ERPNext 的
  `Sales User` 或 `Sales Manager` 权限(ERPNext 是报价单的事实源)。

### 运行测试

```bash
bench --site <your-site> run-tests --app test
```

### License

mit
