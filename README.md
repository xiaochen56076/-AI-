# CampusHub · 校园活动服务平台

CampusHub 将校园活动的「发布 — 审核 — 报名 — 签到 — 复盘」做成一条完整闭环。后端基于 Django 5.2 + Django REST Framework，前端基于 Vue 3 + Element Plus。

## 当前进展

| 模块 | 状态 |
| --- | --- |
| 工程骨架、统一响应、请求 ID、OpenAPI 文档 | 已完成 |
| 学号账号、JWT、RBAC、用户管理 | 已完成 |
| 活动发布、检索、审核、收藏 | 开发中 |
| 报名、候补、并发防超卖 | 待开发 |
| 动态二维码签到 | 待开发 |
| 通知、统计看板、定时任务 | 待开发 |
| Vue 3 学生端 / 主办方端 / 管理端 | 待开发 |

详细变更与测试记录见 [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)。

## 技术栈

- Python 3.14（兼容 3.10+）、Django 5.2 LTS、DRF 3.18
- SimpleJWT（Access 2 小时 / Refresh 7 天，登出黑名单）
- bcrypt 密码哈希、MySQL 8 / SQLite 双数据库配置
- Redis 缓存（可选）、Celery（可选）；未启用 Redis 时使用本地缓存与数据库任务
- Vue 3、TypeScript、Vite、Element Plus、Pinia、ECharts（前端开发中）

## 本地启动

```bash
# 在仓库根目录创建虚拟环境
python -m venv .venv
source .venv/Scripts/activate       # Git Bash
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

- API：<http://127.0.0.1:8000/api/v1/>
- Swagger：<http://127.0.0.1:8000/api/v1/docs>
- Django Admin：<http://127.0.0.1:8000/admin/>

默认开发环境使用 SQLite，无需数据库服务。设置 `DB_ENGINE=mysql` 后启用 MySQL；设置 `REDIS_URL` 后自动启用 Redis 缓存。

## 测试

```bash
python -m pytest
python -m ruff check .
```

测试覆盖统一响应、请求 ID、注册登录、令牌刷新与登出失效、个人资料、RBAC 越权拦截、管理员用户管理等。

## 目录结构

```text
config/             Django 配置（base / dev / prod / test）、路由、Celery
apps/
  accounts/         用户、角色、权限、JWT 认证
  clubs/            社团
  activities/       活动、分类、标签、收藏、审核
  signups/          报名、候补、签到
  notifications/    站内通知
  analytics/        活动与全站看板
common/             统一响应、异常、分页、权限、请求 ID
tests/              跨模块 API 与集成测试
web/                Vue 3 前端
docs/               开发日志与项目文档
```

## 核心约定

- 所有 API 响应统一为 `{ code, message, data, request_id }`，分页数据位于 `data.results`。
- 视图只负责校验与调用服务，业务规则集中在 service 层，数据访问集中在查询/仓储层。
- 报名采用「条件原子更新 + 唯一索引 + 限流」保证不超卖和幂等。
- 动态签到码使用 HMAC-SHA256，30 秒时间窗，允许前后各一个窗口容错。
