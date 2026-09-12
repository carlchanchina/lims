# 客户门户 API(erpnext-nuxt 对接说明)

面向 **客户端** 的门户项目在 `~/claude/erpnext-nuxt/nuxt-app`(Nuxt 4,Nitro BFF),
它现在所有 `/api/**` 都返回 `server/mock/db.ts` 的假数据。本文说明怎么切到真实数据。

## 1. 整体链路

```text
浏览器 ──► Nuxt BFF(Nitro,/api/**)──► LIMS 门户接口(/api/method/lims.api.portal.*)──► ERPNext
                 │ 只读转发 + 附带 API Key/Secret(仅服务端)                │ 事实源:Test Request/Sample/Test Report/Quotation/HD Ticket
                 └─ DTO 与 shared/types/portal.ts 完全一致 ────────────────┘
```

- **员工侧**用 Frappe Desk(旭博检测中心OS);
- **客户侧**用这个 Nuxt 门户,通过 LIMS 门户接口读数据、在线委托、提工单;
- 客户看什么、能不能看,全部在 **LIMS 门户接口里判定**,门户不直接连数据库、也不直接调 `/api/resource`。

## 2. 两种调用身份

| 模式 | 调用方 | `customer` 参数 | 适用 |
| --- | --- | --- | --- |
| 集成账号(BFF) | 专用 API 用户,角色 `客户门户`(+ Helpdesk 的 `Agent`) | **必传**,代表当前登录的客户 | 门户自己维护登录态时 |
| 客户联系人登录 | Website User(客户联系人),Contact 挂在该客户下 | 不用传;传了也只能是自己公司 | 用 Frappe 门户账号登录时 |

两种模式都不可能出现跨客户读取:接口内部先解析"本次代表哪个客户",再对每张单据做归属校验。

## 3. 接口清单(前缀 `/api/method/lims.api.portal.`)

| 接口 | 参数 | 对应门户页面 / DTO |
| --- | --- | --- |
| `dashboard` | `customer` | `/dashboard` → `DashboardData`(stats + recent*) |
| `list_test_requests` | `customer, status?, keyword?, page?, page_length?` | `/test-requests` → `TestRequestSummary[]` |
| `get_test_request` | `name, customer` | `/test-requests/[id]` → `TestRequest`(含 samples/lines/timeline) |
| `list_quotations` | `customer, status?, page?, page_length?` | `/quotations` → `Quotation[]` |
| `get_quotation` | `name, customer` | `/quotations/[id]` → `Quotation` |
| `add_quotation_note` | `name, content, customer` | 报价详情留言 → 写进 Quotation 的 Comment(Desk 可见) |
| `acknowledge_quotation` | `name, action(accept/reject), reason?, customer` | 报价接受/拒绝 → 回写 `Quotation.lims_customer_ack` + 留言 |
| `list_reports` | `customer, page?, page_length?` | `/reports` → `Report[]` |
| `get_report` | `name, customer` | `/reports/[id]` → `Report`(含 rows) |
| `download_report_pdf` | `name, customer` | 报告下载 → 官方 PDF(带实验室抬头/CNAS/批准人) |
| `list_catalog` | `customer?, keyword?, category?` | `/inquiry`(询价页服务目录,价格按该客户协议价) |
| `create_inquiry` | `payload{customer, sampleName, sampleQty, services[], remark, ...}` | `/inquiry` 提交 → 建一张草稿委托单+样品+测试项 |
| `list_tickets` / `get_ticket` | `customer[, name]` | `/tickets`、`/tickets/[id]` → `Ticket[]`(落在 Helpdesk HD Ticket) |
| `create_ticket` | `subject, content, customer, test_request?` | `/tickets` 新建 → HD Ticket |
| `add_ticket_message` | `name, content, customer` | 工单回复 → 写进 HD Ticket Comment |

返回的 `id` / `number` 都用**单据编号字符串**(如 `RQ-2026-00001`、`SAL-QTN-2026-00001`),
所以门户侧的 `readNumericParam` 要换成读字符串(见第 6 节)。

## 4. 状态映射(门户枚举 ← 我们的中文状态)

| 门户 | 我们的值 |
| --- | --- |
| `pending_sample` | 草稿 / 已报价 |
| `testing` | 待检测 / 检测中 |
| `review` | 报告处于 待审核 / 待批准 |
| `completed` | 已完成 |
| `closed` | 已取消 |
| Report `draft` / `issued` | 报告未签发 / 已出具 |
| Quotation `pending` / `accepted` / `rejected` / `expired` | 草稿(未转单) / 已转销售订单 / 已作废 / 已过有效期 |
| Ticket `open` / `resolved` / `closed` | HD Ticket:Open·Replied / Resolved / Closed |

## 5. 门户侧配置(`nuxt-app/.env`)

本机开发环境的真实值(dev 站点,正式环境请换域名并重新生成密钥):

```dotenv
# 切到真实数据源
NUXT_DATA_SOURCE=erpnext

# ERPNext / LIMS(只服务端可见,不要加 NUXT_PUBLIC_ 前缀)
NUXT_ERPNEXT_BASE_URL=http://site1.local:8001
NUXT_ERPNEXT_API_KEY=b2b9fdb40a60037
NUXT_ERPNEXT_API_SECRET=fa97b8495f397e5

# 委托单用我们的真实 DocType(门户侧的容器名仍可叫 entrustment)
NUXT_ERPNEXT_ENTRUSTMENT_DOCTYPE=Test Request
NUXT_ERPNEXT_LEAD_DOCTYPE=Lead
NUXT_ERPNEXT_PRICE_LIST=Standard Selling

# 门户接口前缀(新增配置项,见第 6 节)
NUXT_ERPNEXT_PORTAL_METHOD_PREFIX=lims.api.portal
```

> 集成账号:`portal.service@lab.local`(角色 `客户门户` + `Agent`)。
> 生产环境请新建独立账号、只给 `客户门户` 角色、密钥走密钥管理,并定期轮换。

## 6. 门户侧要改的地方

### 6.1 `server/utils/erpnext.ts` 加一个 method 调用(已完成)

现有文件已经有 `frappeFetch`(带 API Key 认证);追加:

```ts
/** 调用 ERPNext 白名单方法(/api/method/...),门户接口都用这个。 */
export async function erpnextMethod<T>(method: string, params: Record<string, unknown> = {}): Promise<T> {
  const prefix = String(useRuntimeConfig().erpnextPortalMethodPrefix || 'lims.api.portal')
  const res = await frappeJson<{ message: T }>(
    `/api/method/${prefix}.${method}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    }
  )
  return res.message
}
```

### 6.2 每个 `/api/**` 路由从 mock 切到真实数据(已完成)

| 门户路由 | 改成 |
| --- | --- |
| `GET /api/dashboard` | `erpnextMethod('dashboard', { customer })` |
| `GET /api/test-requests` | `erpnextMethod('list_test_requests', { customer })` |
| `GET /api/test-requests/[id]` | `erpnextMethod('get_test_request', { name: id, customer })` |
| `GET /api/quotations` / `[id]` | `list_quotations` / `get_quotation` |
| `GET /api/reports` / `[id]` | `list_reports` / `get_report` |
| `GET /api/reports/[id]/file` | 代理 `download_report_pdf`(把响应的 PDF 流转发;或继续用门户自带的 pdf-lib 渲染) |
| `GET /api/catalog` | `list_catalog` |
| `POST /api/quotations` | `create_inquiry`(返回 `testRequestNumber`,门户侧映射成自己的报价请求 id) |
| `GET/POST /api/tickets`、`GET /api/tickets/[id]` | `list_tickets` / `create_ticket` / `get_ticket` |

路由里的 `customer` 必须来自**门户自己的登录态**(例如会话里存的客户编号),
不能直接取前端传来的值——前端传什么就查什么等于没有隔离。

示例(`server/api/test-requests/index.get.ts`):

```ts
import { erpnextConfigured, erpnextMethod } from '../../utils/erpnext'
import { listTestRequests } from '../../mock/db'

export default defineEventHandler(async (event) => {
  const customer = await requirePortalCustomer(event)   // 门户登录态里取
  if (!erpnextConfigured()) return listTestRequests()   // 没配就继续用 mock
  return erpnextMethod('list_test_requests', { customer })
})
```

实现方式:新增 `server/utils/portalDataSource.ts` 作为唯一开关——
`NUXT_DATA_SOURCE=erpnext` + 配好 API Key 时走真实接口,否则回落到 `server/mock/db.ts`;
各路由只调这一层,不直接碰 mock 或 ERPNext。

### 6.3 id 类型(已完成)

我们的单据号是字符串,门户现在用数字 id:

- `shared/types/portal.ts` 新增 `PortalId = string | number`(mock 用数字、ERPNext 用单据号),
  所有 `id` 字段用它;
- 路由参数改用 `readDocIdParam()`(字符串),页面里 `Number(route.params.id)` 已改成 `String(...)`;
- mock 的 `server/mock/db.ts` 不用改(仍用数字 id),两条数据源共存。

## 7. 报告 PDF 两种做法

1. **用后端的官方 PDF**:`GET /api/method/lims.api.portal.download_report_pdf?name=TR-…&customer=…`,
   返回带实验室抬头、CNAS/CMA 编号、检测-审核-批准三级签署的正式报告(与 Desk 打印一致)。
2. **门户自己渲染**:现在 `server/utils/reportPdf.ts` 用 pdf-lib 从 `Report.rows` 生成,
   适合做"客户预览版";正式版仍建议走 1。

## 8. 安全清单

- API Key/Secret 只放 `runtimeConfig` 顶层(Nuxt 不会下发到浏览器),**永远不要** `NUXT_PUBLIC_` 前缀;
- 集成账号只给 `客户门户`(+ 需要建工单时给 `Agent`),不要给 System Manager/Administrator;
- 门户侧所有取数都必须带"当前登录客户",服务端不接受前端直接传客户;
- 报告/委托单下载链接走后端校验(Frappe 的 `has_website_permission` 已按"客户联系人只能看自己公司"配置);
- 生产环境把 `NUXT_ERPNEXT_BASE_URL` 换成内网域名,并给集成账号开启 IP 白名单。
