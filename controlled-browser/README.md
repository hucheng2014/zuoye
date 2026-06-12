# Controlled Browser

独立可复用的受控浏览器容器，提供：
- headed Chromium
- noVNC 人工查看/接管
- CDP 给容器外 AI Agent 使用
- Docker 内部也可通过服务名连接

## 文件
- `docker-compose.yml`
- `browser/Dockerfile`
- `browser/start-browser.sh`
- `.env.example`

## 启动
```bash
cd /Users/xaa/zuoye/controlled-browser
cp .env.example .env
docker compose up -d --build
```

## 访问
- noVNC: `http://127.0.0.1:6082/vnc.html`
- 宿主机 CDP（推荐）: `http://127.0.0.1:9233`
- 宿主机直连 CDP: `http://127.0.0.1:9232`
- 容器内 CDP: `http://browser:9223`

## 检查
```bash
curl http://127.0.0.1:9232/json/version
curl -H "Host: localhost:9222" http://127.0.0.1:9233/json/version
```
