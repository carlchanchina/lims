### Testing / 环境试验 LIMS MVP

以 **Test Request(检测请求)** 为核心的 ERPNext 自定义 Frappe App,面向
**GJB 150 / GB/T 2423** 环境试验场景优先跑通主流程:

```text
Test Request(可直接新建,也可从 ERPNext Sales Order 带出客户与明细)
  ├─ Sample(独立样品 DocType,一个请求可有多个样品)
  └─ Test Request Item(测试项:样品 + 检测项目 Item + Test Standard[可选])
          │ 生成报价
          ▼
协议价(Test Catalog)按 item 取价:客户协议价 → 行业协议价 → 通用协议价
          ▼
ERPNext Quotation(草稿,含价格但不暴露设备)
          ▼ 提交报价单后转单(也可关联ERPNext里已有的报价单/订单)
ERPNext Sales Order
          ▼
Test Report(人工填写结论,关联 Test Request / Sample)
```

**分工原则**

- ERPNext 负责 `Item`(检测项目,如“低温试验”)、Customer、Contact、Asset、Quotation、Sales Order 等主数据与商务单据;
- LIMS 侧只额外维护 `Test Standard`、`Industry`(行业)、`Test Catalog`(协议价)。客户/联系人/设备/检测项目都支持“选 ERPNext 里已有的,或从 LIMS 新建并写回 ERPNext”;
- Test Request 内不保存 Rate/Amount,也不向客户展示设备;
- Sales Order 保持 ERPNext 原样,不做任何字段/流程改动。

---

### DocType 列表

#### 主数据

**Test Standard(检测标准)**

| 字段 | Fieldname | 类型 |
| --- | --- | --- |
| 标准编码 | `standard_code` | Data,必填,如 `GJB 150.4A` |
| 标准名称 | `standard_name` | Data,必填 |
| 发布/归口单位 | `organization` | Data |
| 标准状态 | `status` | 现行 / 废止 |

**Equipment(设备)**

| 字段 | Fieldname | 类型 |
| --- | --- | --- |
| 设备编码 | `equipment_code` | Data,必填 |
| 设备名称 | `equipment_name` | Data,必填 |
| 型号/规格 | `model` | Data |
| 设备状态 | `status` | 可用 / 维修中 / 停用 |

**Test Catalog(协议价)**

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 协议编号 | `catalog_code` | Data | 如 `JG-2026-001` |
| 协议价名称 | `catalog_name` | Data | 如 `军工低温试验协议价` |
| 检测项目 | `item` | Link `Item` | 必填,ERPNext 检测项目 |
| 客户 | `customer` | Link `Customer` | 与行业二选一,针对单个客户 |
| 行业 | `industry` | Link `Industry` | 与客户二选一,如 `军工` |
| 协议价 | `price` | Currency | 必填,报价取该值 |
| 单位 | `uom` | Link `UOM` | |
| 周期(天) | `tat_days` | Float | |
| 启用 | `enabled` | Check | |

> 同一 `item` + 范围(客户/行业/通用)只允许一条启用的协议价。取价顺序:
> **客户协议价 → 客户所属行业的协议价 → 通用协议价**。

#### 业务单据

**Test Request(检测请求)**

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 客户 | `customer` | Link `Customer` | |
| 联系人 | `contact` | Link `Contact` | |
| 请求日期 | `transaction_date` | Date | |
| 状态 | `status` | Select | 草稿 / 已报价 / 待检测 / 检测中 / 已完成 / 已取消 |
| 公司 | `company` | Link `Company` | |
| 报价单 | `quotation` | Link `Quotation` | 生成报价后自动回填,只读 |
| 销售定单 | `sales_order` | Link `Sales Order` | 客户确认后人工关联 |
| 测试项 | `items` | Table `Test Request Item` | |

**Test Request Item(测试项,子表)**

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 样品 | `sample` | Link `Sample` | 只能选择当前请求的样品 |
| 检测项目 | `item` | Link `Item` | ERPNext 粗粒度项目 |
| 检测标准 | `standard` | Link `Test Standard` | |
| 数量 | `qty` | Float | 默认 1 |
| 单位 | `uom` | Link `UOM` | |
| 备注 | `remarks` | Text | |

> 不含 Rate / Amount / Equipment。

**Sample(样品)**

| 字段 | Fieldname | 类型 |
| --- | --- | --- |
| 检测请求 | `test_request` | Link `Test Request`,必填 |
| 样品名称 | `sample_name` | Data,必填 |
| 收样日期 | `received_date` | Date |
| 样品状态 | `status` | 待收样 / 已收样 / 检测中 / 已检测 / 已退样 |
| 客户 | `customer` | Link `Customer`,从请求带出 |
| 数量 / 单位 | `qty` / `uom` | |
| 备注 | `remarks` | Text |

**Test Report(检测报告)**

| 字段 | Fieldname | 类型 | 说明 |
| --- | --- | --- | --- |
| 检测请求 | `test_request` | Link `Test Request`,必填 | |
| 样品 | `sample` | Link `Sample` | 只显示当前请求样品 |
| 报告日期 / 状态 | `report_date` / `status` | Date / Select | 待检测 / 检测中 / 已出具 / 已作废 |
| 客户 | `customer` | Link `Customer` | 从请求带出 |
| 检测项目 / 标准 / 设备 | `item` / `standard` / `equipment` | Link | 报告展示用 |
| 检测结论 | `conclusion` | Text Editor | MVP 人工填写 |
| 备注 | `remarks` | Text | |

---

### 报价动作

`Test Request` 工具栏提供 **生成报价**:

1. 服务端逐行按 `item` 取协议价:先找该客户的协议价,再找客户所属行业的协议价,最后找通用协议价;三条都没有就明确报错,不会生成半张报价单;
2. 匹配成功后把 Quotation 明细写为:
   - `item_code = Test Request Item.item`
   - `description = 协议价名称 + 标准(填了才带) + 样品`
   - `rate = 协议价.price`
   - `qty = Test Request Item.qty`
3. 报价单只保留在 ERPNext,回填 `Test Request.quotation`,状态自动变为 **已报价**;
4. 报价单/订单除了在 LIMS 里生成,也可以**关联 ERPNext 中已有的**:详情页填单号即可挂上,客户不一致会拦下;
5. **从报价单生成销售订单**:ERPNext 要求报价单已提交,草稿报价单会先提交再转单,LIMS 回收 `sales_order`;
6. **从销售订单建检测请求**:新建请求时选"从销售订单建立",会带出客户与订单明细(每条明细生成一个样品和一个测试项,标准可稍后补)。

### Installation

```bash
bench get-app https://github.com/<your-org>/test --branch <branch>
bench --site <your-site> install-app test
bench --site <your-site> migrate
bench --site <your-site> run-tests --app test
```

用户需要 `Testing Manager` / `Testing User` 角色;生成报价依赖 ERPNext 的
Customer/Company/币种/Selling Price List 等标准配置。

### Vue 前端(/lims)

前端源码位于仓库根目录 `desk/`,详见 `desk/README.md`。

```bash
cd desk
yarn install
yarn build
```

构建后访问 `https://<your-site>/lims`,使用内部 Frappe 账号登录。

### License

mit
