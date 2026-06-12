# autotrade

本项目的运行态和关键恢复信息统一放在 `D:\autotrade` 下，本地 Docker 容器通过目录挂载直接使用这里的数据，因此容器重建后状态仍然保留。

## 持久化布局

- `D:\autotrade\docker-compose.yml`
  Docker 编排入口，当前将 `./user_data` 和 `./postgres_data` 挂载到容器内。
- `D:\autotrade\Dockerfile.freqtrade-pg`
  自定义 Freqtrade 镜像，包含运行期补丁。
- `D:\autotrade\user_data`
  Freqtrade/FreqAI 的核心目录，包含策略、RL 模型、配置、训练产物、日志和历史数据。
- `D:\autotrade\postgres_data`
  PostgreSQL 数据目录，保存 live / paper 交易库。
- `D:\autotrade\backups`
  本地快照备份目录，保存数据库导出、关键配置副本和运行摘要。
- `D:\autotrade\tools`
  监控、评估、SQL、备份脚本。

## Git 跟踪范围

Git 仓库只跟踪这些可维护文件：

- Docker 编排和镜像文件
- 策略代码与 RL 模型代码
- 工具脚本和 SQL
- 文档
- 不含敏感信息的配置样例
- 当前 paper 覆盖配置 `user_data/config.paper.json`

Git 默认不跟踪这些运行态数据：

- `postgres_data`
- `backups`
- `user_data/logs`
- `user_data/data`
- `user_data/models`
- `user_data/rl_state`
- SQLite 临时库和 WAL 文件
- 含敏感信息的 `user_data/config.json`、`user_data/config.live.json`

## 本地快照备份

执行下面命令会在 `D:\autotrade\backups` 下生成一个时间戳目录：

```powershell
powershell -ExecutionPolicy Bypass -File D:\autotrade\tools\backup_project.ps1
```

快照内容包括：

- `docker-compose.yml`
- `Dockerfile.freqtrade-pg`
- 实际运行配置文件副本
- 策略与 RL 模型源码
- `freqtrade` / `freqtrade_paper` PostgreSQL SQL 导出
- 模型目录、数据目录、日志目录、数据库目录摘要
- 容器状态、API `show_config` 响应、Git 状态

## 恢复原则

1. 保留 `D:\autotrade\user_data` 和 `D:\autotrade\postgres_data` 不删除。
2. 如需回滚配置或数据库，从 `D:\autotrade\backups\project_snapshot_*` 中恢复。
3. 切换容器时优先使用 `docker compose up -d --force-recreate`，不要手工清空上述目录。
4. 如果以后要推送到远程仓库，先确认不把真实密钥文件加入 Git。

## 本机启动

1. 将整个项目放在 `D:\autotrade`。
2. 本机安装并启动 Docker Desktop。
3. 首次迁移自外置盘时，运行：

```powershell
powershell -ExecutionPolicy Bypass -File D:\autotrade\tools\start_local.ps1
```

说明：

- 启动脚本会先检查 Docker 是否可用。
- 如果检测到复制过来的 `postgres_data\postmaster.pid`，会先备份到 `backups\migration_*` 再移除，避免 PostgreSQL 因旧锁文件拒绝启动。
- 默认执行 `docker compose up -d --build`，以便重建自定义 Freqtrade 镜像。
- `docker-compose.yml` 当前将宿主机 `8088` 映射到 Freq UI/API 的 `8080`，对局域网可连接，不再只绑定 `127.0.0.1`。
- 如果要启动后连续观察 10 分钟日志，可运行：

```powershell
powershell -ExecutionPolicy Bypass -File D:\autotrade\tools\start_and_watch_10m.ps1
```

- 如果这台机器还没有 Docker/WSL，可在管理员 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File D:\autotrade\tools\install_docker_runtime.ps1
```
