# Controlled Browser

这个目录封装一个可被 AI agent 控制的浏览器容器：

- Chromium 运行在容器内。
- CDP 暴露给 agent 或宿主。
- noVNC 暴露给人工查看和接管。
- 浏览器 profile 使用 Docker volume 持久化。

## 默认端口

为避免和当前 `controlled-browser` 冲突，本模板默认使用：

- noVNC: `http://127.0.0.1:6083/vnc.html`
- CDP direct: `http://127.0.0.1:9234`
- CDP proxy: `http://127.0.0.1:9235`

推荐让 AI agent 使用 CDP proxy：

```text
http://127.0.0.1:9235
```

## 启动

```bash
cd controlled-browser
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
curl -sS http://127.0.0.1:9235/json/version
```

停止：

```bash
docker compose down
```

删除浏览器 profile：

```bash
docker compose down -v
```

## 自定义端口

```bash
NOVNC_HOST_PORT=6090 CDP_HOST_PORT=9240 CDP_PROXY_HOST_PORT=9241 docker compose up -d --build
```

## Agent 使用约束

给 AI agent 的要求：

- 只连接这个容器里的已有浏览器。
- 不要在宿主机启动浏览器。
- 不要在容器外新开浏览器实例。
- CDP 地址使用 `http://127.0.0.1:9235`，或你自定义的 `CDP_PROXY_HOST_PORT`。
- 需要人工登录或验证码时，通知用户打开 noVNC。

## 内部网络模式

如果另一个 agent 容器加入同一个 compose 网络，可以通过服务名访问：

```text
http://browser:9223
```

这与 `oneform-agent` 访问 `oneform-browser` 的方式相同。
