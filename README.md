# CampusHub · 校园活动服务平台

CampusHub 将校园活动的「发布 — 审核 — 报名 — 签到 — 复盘」做成一条完整闭环。后端基于 Django 5.2 + Django REST Framework，前端基于 Vue 3 + Element Plus。

## 当前进展

| 模块 | 状态 |
| --- | --- |
| 工程骨架、统一响应、请求 ID、OpenAPI 文档 | 已完成 |
| 学号账号、JWT、RBAC、用户管理 | 已完成 |
| 活动发布、检索、审核、收藏 | 已完成 |
| 报名、候补、并发防超卖 | 已完成 |
| 动态二维码签到、手动补签 | 已完成 |
| 站内通知、审核/报名/候补/提醒消息 | 已完成 |
| 活动数据看板、全站看板、分类标签字典管理 | 已完成 |
| 活动自动结束、爽约标记、开场提醒定时任务 | 已完成 |
| Vue 3 学生端 / 主办方端 / 管理端 | 已完成 |

详细变更与测试记录见 [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)。

## 技术栈

- Python 3.14（兼容 3.10+）、Django 5.2 LTS、DRF 3.18
- SimpleJWT（Access 2 小时 / Refresh 7 天，登出黑名单）
- bcrypt 密码哈希、MySQL 8 / SQLite 双数据库配置
- Redis 缓存（可选）、Celery（可选）；未启用 Redis 时使用本地缓存与数据库任务
- Vue 3、TypeScript、Vite 7、Element Plus 2.13、Pinia 3、Vue Router 4、ECharts 5、qrcode / qr-scanner

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

### 前端

```bash
cd web
npm install
npm run dev          # http://localhost:5173，/api 代理到 127.0.0.1:8000
npm run typecheck    # vue-tsc 严格类型检查
npm run build        # 产物输出到 web/dist
```

### 演示数据

```bash
python manage.py seed_demo_data            # 生成 19 场活动、4 类角色与完整报名签到链路
python manage.py seed_demo_data --reset    # 先清理旧的演示数据再重建
```

演示账号统一密码 `Campushub@2026`：管理员 `20210001`、审核员 `20190001`、主办方 `20220101`/`20220102`/`20220103`、学生 `20220201`–`20220218`。

未部署 Celery 时，可通过管理命令执行活动结束、爽约标记与开场提醒：

```bash
python manage.py run_scheduled_tasks
```

生产环境可由 Celery Beat 每 5 分钟调度 `apps.activities.tasks.close_expired_activities_task` 与 `apps.notifications.tasks.send_activity_reminders_task`。

## 测试

```bash
python -m pytest
python -m ruff check .
cd web && npm run typecheck && npm run build
```

测试覆盖统一响应、请求 ID、注册登录、令牌刷新与登出失效、个人资料、RBAC 越权拦截、管理员用户管理、活动状态流转、审核权限、活动编辑边界、检索筛选、收藏、报名候补、并发防超卖、动态签到码、手动补签、站内通知、提醒幂等、爽约标记、活动/全站统计与字典管理等。前端以 `vue-tsc` 严格类型检查与生产构建作为回归门槛。

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
web/                Vue 3 前端（api / stores / layouts / views/public / views/console / components）
docs/               开发日志与项目文档
```

## 核心约定

- 所有 API 响应统一为 `{ code, message, data, request_id }`，分页数据位于 `data.results`。
- 视图只负责校验与调用服务，业务规则集中在 service 层，数据访问集中在查询/仓储层。
- 报名采用「条件原子更新 + 唯一索引 + 限流」保证不超卖和幂等。
- 动态签到码使用 HMAC-SHA256，30 秒时间窗，允许前后各一个窗口容错。
- 通知在业务事务内落库，提醒任务使用业务去重键保证重复调度不重复发送。
- 活动数据看板提供报名转化、签到率、候补转正率、人群分布与近 7 天趋势；全站看板提供状态分布、热门分类与近 8 周趋势。
