### Testing / 检测委托管理

一个以 **检测委托单(Testing Entrustment)** 为核心的 ERPNext 自定义 Frappe App。

ERPNext 是事实源(Source of Truth),本 App **不改动 ERPNext 的 Sales Order**:
报价、销售定单继续按 ERPNext 标准流程走,委托单从已提交定单的明细中导入试验/检测项目,
样品作为委托单内部的子表维护,检测报告再关联回委托单。

---

### 业务流转

```
ERPNext 报价单(Quotation)
        │
        ▼
ERPNext 销售定单(Sales Order)   ← 本 App 不做任何字段/流程改动
        │
        ▼  新建检测委托单,点击「从定单导入试验项目」
检测委托单(Testing Entrustment)
        ├── 试验/检测项目(Testing Entrustment Item,子表,从定单明细带入)
        └── 样品信息(Testing Entrustment Sample,子表,一张委托单可有多行)
                │
                ▼
检测报告(Test Report)   ← 关联委托单,可指定委托单下的某个样品
```

委托单内**不再包含报价单字段、预计金额、Rate / Amount**,金额信息以 ERPNext 定单为准。

---

### DocType 列表

#### 1. Testing Entrustment(检测委托单)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 客户 | `customer` | Link `Customer` | 必填,可从定单带入 |
| 联系人 | `contact` | Link `Contact` | 按客户过滤 |
| 委托日期 | `transaction_date` | Date | 默认今天 |
| 状态 | `status` | Select | 草稿 / 待检测 / 检测中 / 已完成 / 已取消 |
| 公司 | `company` | Link `Company` | 可从定单带入 |
| 销售定单 | `sales_order` | Link `Sales Order` | 只做关联,不改定单 |
| 项目 | `project` | Link `Project` | 后续关联 |
| 试验/检测项目 | `items` | Table `Testing Entrustment Item` | 从定单明细导入 |
| 样品信息 | `samples` | Table `Testing Entrustment Sample` | 一行一个样品 |

编号规则:`TE-{YYYY}-{#####}`。

#### 2. Testing Entrustment Item(试验/检测项目,子表)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 试验/检测项目 | `item` | Link `Item` | 从定单明细带入 |
| 项目名称 | `item_name` | Data | 自动带出 |
| 数量 | `qty` | Float | |
| 单位 | `uom` | Link `UOM` | 自动补全 |
| 检测标准 | `testing_standard` | Data | 如 GB/T、ISO 标准 |
| 备注 | `remarks` | Text | |

> 不含 Rate / Amount。

#### 3. Testing Entrustment Sample(样品信息,子表)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 样品名称 | `sample_name` | Data | 必填 |
| 检测项目 | `item` | Link `Item` | 可选 |
| 数量 | `qty` | Float | |
| 单位 | `uom` | Link `UOM` | |
| 收样日期 | `received_date` | Date | |
| 样品状态 | `status` | Select | 待收样 / 已收样 / 检测中 / 已检测 / 已退样 |
| 备注 | `remarks` | Text | |

#### 4. Test Report(检测报告)

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 检测委托 | `entrustment` | Link `Testing Entrustment` | 必填 |
| 样品 | `sample` | Link `Testing Entrustment Sample` | 只显示当前委托单的样品 |
| 样品名称 | `sample_name` | Data | 选中样品后带出 |
| 报告日期 | `report_date` | Date | 默认今天 |
| 状态 | `status` | Select | 待检测 / 检测中 / 已出具 / 已作废 |
| 客户 | `customer` | Link `Customer` | 从委托单带出 |
| 检测项目 | `item` | Link `Item` | |
| 检测标准 | `testing_standard` | Data | |
| 检测人 | `tested_by` | Link `User` | |
| 检测结论 | `conclusion` | Text Editor | |
| 备注 | `remarks` | Text | |

编号规则:`TR-{YYYY}-{#####}`。

---

### 操作方式

1. 新建检测委托单;
2. 在「来源与关联」中选择一张**已提交**的销售定单;
3. 点击 **从定单导入试验项目**,定单明细自动变成委托单的试验/检测项目(定单本身不改变);
4. 在「样品信息」中维护一行或多行样品;
5. 保存并提交委托单;
6. 点击 **新建报告**,报告自动关联当前委托单,并可指定其中的一个样品。

---

### 目录结构

```text
test/
├── hooks.py                       # required_apps = erpnext
├── modules.txt                    # Testing
├── setup/
│   └── install.py                 # 角色创建 + 清理旧 Quotation 回链字段
└── testing/
    ├── doctype/
    │   ├── testing_entrustment/          # 主表(委托单)
    │   ├── testing_entrustment_item/     # 试验/检测项目子表
    │   ├── testing_entrustment_sample/   # 样品信息子表
    │   └── test_report/                  # 检测报告
    └── workspace/testing/                # Testing 模块工作台
```

---

### Installation

在已有 ERPNext bench 上:

```bash
bench get-app https://github.com/<your-org>/test --branch <branch>
bench --site <your-site> install-app test
bench --site <your-site> migrate
```

用户需要 `Testing Manager` / `Testing User` 角色,并且能从定单导入明细,
因此还需要对应 `Sales Order` 的读取权限(通常直接授予 ERPNext `Sales User`)。

运行测试:

```bash
bench --site <your-site> run-tests --app test
```

### License

mit
