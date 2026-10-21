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
