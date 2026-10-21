# CampusHub 部署文档

本文覆盖后端（Django + DRF）、前端（Vue 3 SPA）与运维脚本的生产部署，以及上线后的端到端验收清单。

## 1. 架构概览

```text
浏览器 ──HTTPS──▶ Nginx
                   ├── /            web/dist 静态 SPA（Vue Router history 模式）
                   ├── /static/     Django collectstatic 产物
                   ├── /media/      用户上传（活动封面等）
                   └── /api/ /admin/ ──unix socket──▶ Gunicorn (config.wsgi)
                                                        ├── SQLite / MySQL 8
                                                        ├── Redis（可选：缓存 + Celery broker）
                                                        └── Celery worker / beat（可选）
```

- 未启用 Celery 时，活动结束、爽约标记与开场提醒由 systemd timer 调用 `python manage.py run_scheduled_tasks` 完成，功能等价。
- 全部接口响应为 `{ code, message, data, request_id }`，前端仅依赖该约定与 HTTP 状态码。

## 2. 环境要求

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.10 – 3.14 | 开发验证使用 3.14 |
| Node.js | 20+ | 仅构建前端时需要，可在 CI 机器上完成后只上传 `web/dist` |
| 数据库 | SQLite（默认）/ MySQL 8 | MySQL 走 `utf8mb4` + `STRICT_TRANS_TABLES`；SQLite 已配置 30s busy timeout 与 `IMMEDIATE` 事务模式 |
| Redis | 5+ | 可选，用于缓存与 Celery |
| Nginx | 1.20+ | 反向代理与静态资源 |

## 3. 目录与服务账号

```text
/srv/campushub                 代码仓库（git clone 后 checkout main）
/srv/campushub/.venv           后端虚拟环境
/srv/campushub/staticfiles     collectstatic 输出
/srv/campushub/media           用户上传
/etc/campushub/production.env  生产环境变量（权限 600，属主 campushub）
/run/campushub/gunicorn.sock   Gunicorn socket（systemd RuntimeDirectory 自动创建）
```

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin campushub
sudo mkdir -p /srv/campushub /etc/campushub
sudo chown -R campushub:campushub /srv/campushub /etc/campushub
```

## 4. 生产环境变量

`/etc/campushub/production.env` 示例（不要把真实密钥提交进仓库）：

```ini
DJANGO_SETTINGS_MODULE=config.settings.prod
DJANGO_SECRET_KEY=<python -c "from django.core.management.utils import get_random_secret_key as g; print(g())">
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=campus.example.edu
DJANGO_SECURE_SSL_REDIRECT=true

DB_ENGINE=mysql
DB_NAME=campushub
DB_USER=campushub
DB_PASSWORD=<强密码>
DB_HOST=127.0.0.1
DB_PORT=3306

REDIS_URL=redis://127.0.0.1:6379/1
CELERY_BROKER_URL=redis://127.0.0.1:6379/2
CELERY_TASK_ALWAYS_EAGER=false

# 前端与 API 同源部署时可不设置 CORS；跨域时需同时配置两类来源
CORS_ALLOWED_ORIGINS=https://campus.example.edu
CSRF_TRUSTED_ORIGINS=https://campus.example.edu

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=<smtp 服务器>
EMAIL_PORT=465
EMAIL_HOST_USER=<发件账号>
EMAIL_HOST_PASSWORD=<授权码>
EMAIL_USE_SSL=true
DEFAULT_FROM_EMAIL=CampusHub <no-reply@campus.example.edu>
```

## 5. 发布步骤

### 5.1 后端

```bash
cd /srv/campushub
git pull --ff-only origin main

sudo -u campushub python3.12 -m venv .venv           # 首次
sudo -u campushub .venv/bin/pip install -r requirements-prod.txt

sudo -u campushub env --unset=DJANGO_SETTINGS_MODULE \
  .venv/bin/python manage.py migrate
sudo -u campushub .venv/bin/python manage.py collectstatic --noinput
sudo -u campushub .venv/bin/python manage.py check --deploy
sudo -u campushub systemctl restart campushub-gunicorn
```

首次上线后创建管理员：

```bash
sudo -u campushub .venv/bin/python manage.py createsuperuser --noinput \
  --username admin --email admin@campus.example.edu
# 或直接用演示账号体系：为学号账号分配 ADMIN 角色（/console/users 页面）
```

### 5.2 前端

```bash
cd web
npm ci
npm run build          # 产物在 web/dist
```

`web/dist` 由 Nginx 直接托管（`root /srv/campushub/web/dist`）。前端请求固定以 `/api/v1` 为前缀（见 `web/src/api/http.ts` 的 `baseURL`），与站点同源，因此生产环境无需额外环境变量，只需 Nginx 把 `/api/` 转发给 Gunicorn。Vite 的 `/api` 代理只在 `npm run dev` 生效。

### 5.3 Nginx 与 systemd

```bash
sudo cp nginx/campushub.conf /etc/nginx/sites-available/campushub
sudo ln -sf /etc/nginx/sites-available/campushub /etc/nginx/sites-enabled/campushub
sudo nginx -t && sudo systemctl reload nginx

sudo cp deploy/*.service deploy/*.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now campushub-gunicorn
sudo systemctl enable --now campushub-scheduled-tasks.timer    # 无 Celery 时使用
# 使用 Celery 时改为：
sudo systemctl enable --now campushub-celery-worker.service campushub-celery-beat.service
```

Nginx 以 `www-data` 读取前端产物与静态目录，需要保证其他用户可读：

```bash
sudo chmod -R o+X /srv/campushub/web/dist /srv/campushub/staticfiles
sudo setfacl -R -m u:www-data:rx /srv/campushub/media    # 如需 Nginx 直出媒体文件
```

启用 Celery 后请停用 systemd timer，避免提醒任务被两条调度链路重复触发（提醒有业务去重键，不会重复发送，但仍应避免无谓负载）。

## 6. 数据与备份

```bash
# SQLite
sudo -u campushub cp db.sqlite3 /backup/campushub-$(date +%F).sqlite3

# MySQL
mysqldump --single-transaction --default-character-set=utf8mb4 campushub | gzip > /backup/campushub-$(date +%F).sql.gz

# 用户上传目录
tar czf /backup/media-$(date +%F).tar.gz -C /srv/campushub media
```

迁移回滚：`python manage.py migrate <app> <previous_migration>`。发布前建议先跑一次 `migrate --plan` 确认改动范围。

## 7. 健康检查

| 检查 | 命令 / 地址 | 期望 |
| --- | --- | --- |
| 进程 | `systemctl is-active campushub-gunicorn` | `active` |
| 接口存活 | `curl -s https://campus.example.edu/api/v1/health` | `{"code":0,...}` |
| OpenAPI | `https://campus.example.edu/api/v1/docs` | Swagger 页面 |
| 前端首屏 | `curl -sI https://campus.example.edu/` | `200`，`content-type: text/html` |
| 深链刷新 | `curl -sI https://campus.example.edu/activities/1` | `200`（history 回退到 index.html） |
| 静态资源 | `curl -sI https://campus.example.edu/assets/` | 目录可访问，`/static/` 返回 Django 静态文件 |
| 定时任务 | `systemctl list-timers campushub-scheduled-tasks.timer` | 下次触发时间存在 |
| 日志 | `journalctl -u campushub-gunicorn -f` | 无 5xx 与 Traceback |

## 8. 端到端验收清单

上线后按角色各跑一遍，全部通过才算可交付。

### 8.1 游客

- [ ] 首页展示分类、进行中活动与最新活动，图片/文案无占位残留。
- [ ] 活动广场可按分类、关键词、`进行中/即将开始/往期回顾` 与排序筛选，分页可翻页。
- [ ] 未登录访问 `/my/signups`、`/console` 被重定向到登录页，且登录后回到原目标页。
- [ ] 访问不存在的路径出现 404 页，页脚入口可点击。

### 8.2 学生

- [ ] 注册新学号 → 登录成功；重复学号注册返回「该学号已注册」而不是 500。
- [ ] 报名后计数 +1；名额满时进入候补并显示候补序号。
- [ ] 取消报名后候补自动转正，消息中心收到通知。
- [ ] 收藏活动在「我的收藏」可见，取消收藏后消失。
- [ ] 消息中心「全部已读」后顶部徽标归零。
- [ ] 活动开始 30 分钟内进入 `/checkin`，输入 8 位签到码 → 显示「签到成功」卡片。
- [ ] 签到码过期或错误时给出明确提示，且不改变报名状态。
- [ ] 「我的报名」按 全部 / 待参加 / 候补中 / 已参与 / 已取消 分组正确，空分组显示引导文案。

### 8.3 主办方

- [ ] 创建活动时必填项缺失有内联校验；保存草稿后停留在编辑页。
- [ ] 提交审核后活动从公开列表消失，进入审核工作台待审核队列。
- [ ] 已发布活动的编辑页只允许修改简介、详情、封面、标签，其余字段置灰；直接调用接口修改关键字段返回 409。
- [ ] 取消活动必须填写原因，取消后学生收到通知且列表不再展示。
- [ ] 报名名单页统计与表格行数一致；导出 CSV 在 Excel 中中文不乱码（含 BOM）。
- [ ] 签到管理页二维码每 30 秒刷新，窗口外提示「当前不在签到时间内」；手动补签可写入记录并带补录序号。
- [ ] 活动数据页四张图表有数据，签到率与名单口径一致。

### 8.4 审核员 / 管理员

- [ ] 审核员仅能看到 `activity:audit` 权限内的入口，越权访问 `/console/users` 跳 403。
- [ ] 驳回时未填写意见被拦截；通过后活动立即可在前台访问。
- [ ] 全站看板指标与 `manage.py shell` 查询结果一致。
- [ ] 用户管理可分配角色与禁用账号；被禁用账号无法登录，重新启用后可登录。
- [ ] 字典管理停用分类后，发布表单与筛选区不再出现该分类；重复 slug 返回冲突提示。

### 8.5 权限与安全

- [ ] 非主办方访问他人活动的名单/签到接口返回 403。
- [ ] Access 令牌过期时前端自动刷新一次，无感续期；Refresh 失效则跳登录并提示「登录状态已过期」。
- [ ] 登出后原 Refresh 令牌立即失效（黑名单）。
- [ ] `python manage.py check --deploy` 无 `(security.*)` 告警。剩余告警均为 `drf_spectacular.W002`（纯 `APIView` 无法自动推断响应序列化器，仅影响 Swagger 描述完整度，不影响接口行为）。
- [ ] `curl -sI https://<域名>/` 响应头含 `Strict-Transport-Security`、`X-Frame-Options: DENY`、`X-Content-Type-Options: nosniff`（由 `config/settings/prod.py` 与 Nginx 双层提供）。

### 8.6 任务与数据一致性

- [ ] 手工执行 `python manage.py run_scheduled_tasks`：过期活动自动结束、未签到报名被标记爽约、候补被清理。
- [ ] 重复执行同一批任务不产生重复通知（去重键生效）。
- [ ] 并发报名同一场满员活动不超卖（`pytest tests/test_signups.py -k concurrent` 覆盖）。

## 9. 常见故障

| 现象 | 排查 |
| --- | --- |
| 502 Bad Gateway | `systemctl status campushub-gunicorn`；确认 socket 路径与 Nginx `proxy_pass` 一致 |
| 接口 404 但路由存在 | 路径不带结尾斜杠，例如 `/api/v1/activities`；`ALLOWED_HOSTS` 是否包含该域名 |
| 刷新深链 404 | Nginx 缺少 `try_files $uri $uri/ /index.html;` |
| 上传的封面 404 | `MEDIA_ROOT` 权限与 `/media/` alias 路径不一致 |
| CORS 报错 | 同步设置 `CORS_ALLOWED_ORIGINS` 与 `CSRF_TRUSTED_ORIGINS` |
| 提醒不发送 | Redis 连通性、`CELERY_TASK_ALWAYS_EAGER`、`journalctl -u campushub-celery-worker` |
| SQLite 报 `database is locked` | 已设置 30s busy timeout 与 `IMMEDIATE` 事务；高并发写请切换到 MySQL，并保证 gunicorn worker 使用独立进程 |
