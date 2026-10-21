# 开发日志

本文件按功能记录交付内容、关键改动位置和测试结果。每次推送前必须先通过测试。

## 2026-10-21 · 项目骨架与账号权限

### 做了什么

- 建立 Django 5.2 + DRF 分层工程，拆分 `base/dev/prod/test` 四套配置，默认 SQLite 开发、支持 MySQL/Redis/Celery。
- 统一 API 响应为 `code / message / data / request_id`，增加请求 ID 中间件、全局异常处理、分页类与 API JSON 404。
- 接入 Swagger/OpenAPI，提供健康检查接口。
- 实现学号登录自定义用户、bcrypt 密码哈希、学生/主办方/审核员/管理员四类 RBAC 角色与权限种子。
- 实现注册、登录、刷新令牌、登出黑名单、个人资料、修改密码、管理员用户查询与状态/角色调整。
- 创建 pytest 测试体系与 Git 仓库。

### 改动位置

- 配置：`config/settings/base.py`、`config/settings/dev.py`、`config/settings/prod.py`、`config/settings/test.py`、`config/urls.py`
- 公共能力：`common/api/responses.py`、`common/exceptions.py`、`common/middleware/request_id.py`、`common/permissions.py`、`common/pagination.py`
- 账号域：`apps/accounts/models.py`、`apps/accounts/serializers.py`、`apps/accounts/services.py`、`apps/accounts/views.py`、`apps/accounts/authentication.py`
- 数据迁移：`apps/accounts/migrations/0001_initial.py`、`apps/accounts/migrations/0002_seed_rbac.py`
- 测试：`tests/test_accounts.py`、`tests/test_health.py`、`tests/conftest.py`
- 工程文档：`README.md`、`.env.example`、`requirements.txt`、`pyproject.toml`

### 验证

```text
Django system check: 0 issues
pytest: 15 passed
```

覆盖点：统一响应与请求 ID、API 404、注册、重复学号、密码一致性、登录、错误密码、禁用账号、刷新令牌轮换、登出后 Access/Refresh 均失效、个人资料、修改密码、RBAC 越权、管理员筛选用户、管理员改角色、禁止自禁用。

## 2026-10-21 · 活动域与审核流

### 做了什么

- 新增社团、活动分类、标签、活动、审核记录与收藏模型，活动状态覆盖草稿/待审核/已发布/已结束/已取消/已驳回。
- 实现活动公开检索（关键词/分类/标签/日期/时间范围/热度排序/分页）、详情浏览、浏览计数与收藏。
- 实现主办方创建活动草稿、编辑活动、提交审核、取消/下架活动；首次发布自动创建主办方社团空间。
- 实现审核员待审列表、通过/驳回，驳回强制填写意见，审核记录只增不改；重复审核返回冲突提示。
- 已发布活动仅允许修改简介、详情、封面与标签，关键信息变更被服务层拦截。
- 增加 6 个活动分类与 4 个标签的种子数据，并完成主办方/审核员数据级权限校验。

### 改动位置

- 模型：`apps/clubs/models.py`、`apps/activities/models.py`
- 查询与业务：`apps/activities/repositories.py`、`apps/activities/services.py`
- 序列化与接口：`apps/activities/serializers.py`、`apps/activities/views.py`、`apps/activities/urls.py`
- 管理后台：`apps/clubs/admin.py`、`apps/activities/admin.py`
- 迁移：`apps/clubs/migrations/0001_initial.py`、`apps/activities/migrations/0001_initial.py`、`apps/activities/migrations/0002_seed_categories.py`
- 路由：`config/urls.py`
- 测试：`tests/test_activities.py`

### 验证

```text
Django system check: 0 issues
pytest: 28 passed
ruff: All checks passed
```

覆盖点：主办方创建草稿与自动建社团、学生创建拦截、时间合法性、提交审核、审核列表、通过发布、驳回意见校验、驳回后重新提交、非本人编辑拦截、已发布字段限制、公开检索筛选排序、详情浏览量、收藏幂等/取消收藏、草稿对外隐藏、取消原因校验、分类标签公开读取。

## 2026-10-21 · 报名、候补与并发防超卖

### 做了什么

- 新增报名实体，状态覆盖候补、报名成功、已取消、已签到、已爽约，保留候补序号与时间轨迹。
- 实现报名主链路：活动状态/报名时间窗/账号有效性校验、满员自动进入候补、候补上限、重复报名幂等、已取消用户重新报名。
- 并发控制采用「活动行锁 + 条件原子更新 `signup_count < capacity` + `(activity, user)` 唯一索引 + 报名接口限流」四层防护。
- 取消报名：成功名额释放后在同一事务内按 `queue_no` 递补候补首位；候补取消同步修正计数；截止后禁止取消。
- 活动取消时自动取消全部有效报名并归零计数。
- 实现我的报名分组查询、主办方实时名单筛选、CSV 导出（含 UTF-8 BOM 与表格公式注入防护）。
- 增加 100 并发抢 10 个名额的真实线程测试，验证无超卖、无重复用户。

### 改动位置

- 模型：`apps/signups/models.py`
- 业务与查询：`apps/signups/services.py`、`apps/signups/repositories.py`
- 接口：`apps/signups/views.py`、`apps/signups/urls.py`、`apps/signups/serializers.py`
- 限流：`apps/signups/throttles.py`、`config/settings/base.py`
- 活动联动：`apps/activities/services.py`
- 迁移：`apps/signups/migrations/0001_initial.py`
- 测试：`tests/test_signups.py`、`tests/conftest.py`、`config/settings/test.py`

### 验证

```text
pytest: 40 passed（包含 100 并发报名测试）
ruff: All checks passed
```

并发测试结果：100 名用户同时抢容量为 10 的活动，恰好 10 人成功，`signup_count = 10`，无超卖、无重复记录。

## 2026-10-21 · 动态二维码签到与手动补签

### 做了什么

- 新增签到记录模型，一条报名仅对应一条签到记录；记录签到方式（扫码/手动补签）、经纬度、设备信息、补签操作人与原因、签到时间。
- 实现 HMAC-SHA256 动态签到码：以「活动 ID + 30 秒时间桶 + 活动密钥」计算 8 位签到码，校验时容忍前后各一个时间桶，兼容时钟偏差与网络延迟。
- 支持静态码与动态码两种模式；二维码内容采用 `campushub://checkin?activity_id=...&code=...` 自定义协议，便于前端生成与扫码解析。
- 扫码签到校验活动状态、签到时间窗（开始前 30 分钟至结束）、报名状态、重复签到与签到码有效性；签到成功同步报名状态为「已签到」。
- 主办方签到台接口返回当前签到码、过期时间、服务器时间、签到窗口与已签到人数；活动详情新增签到开关、签到窗口、已签到人数与当前用户报名状态。
- 手动补签强制填写原因并记录操作人，仅活动主办方或管理员可操作；补签同样受签到时间窗与重复签到校验。
- 修复签到密钥通过活动详情接口泄露的问题，API 不再返回 `checkin_secret`。
- 签到记录写入使用嵌套事务与唯一约束兜底，并发重复签到返回业务错误而非 500。

### 改动位置

- 签到算法：`apps/signups/checkin.py`
- 模型与后台：`apps/signups/models.py`、`apps/signups/admin.py`
- 业务与接口：`apps/signups/services.py`、`apps/signups/serializers.py`、`apps/signups/views.py`、`apps/signups/urls.py`
- 活动详情联动：`apps/activities/serializers.py`
- 迁移：`apps/signups/migrations/0002_checkinrecord.py`
- 测试：`tests/test_signups.py`、`tests/test_activities.py`

### 新增接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/activities/{id}/checkin-code` | 主办方生成签到码 |
| POST | `/api/v1/checkin` | 学生扫码签到 |
| POST | `/api/v1/activities/{id}/checkin-manual` | 主办方手动补签 |

### 验证

```text
Django system check: 0 issues
pytest: 49 passed
ruff: All checks passed
```

覆盖点：动态码生成与成功签到、篡改码/过期码拦截、未报名用户拦截、重复签到拦截、签到时间窗外拦截、静态码签到、手动补签审计字段、补签权限/原因/学号校验、非主办方生成签到码拦截、活动详情不再泄露签到密钥。
