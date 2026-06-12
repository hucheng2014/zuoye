# 作业项目使用指南 (macOS)

## 前置准备

### 1. 安装 Docker Desktop
```bash
# 下载安装 (需要管理员密码)
# https://docs.docker.com/desktop/install/mac-install/
# 安装后启动 Docker Desktop，等状态栏图标变为稳定
```

### 2. 安装 Conda 环境 (ASR 用)
```bash
cd ~/zuoye/putonghuaasr
bash setup-macos-env.sh
```

### 3. 设置代理 (如需要)
```bash
export HTTP_PROXY=http://192.168.5.64:7897
export HTTPS_PROXY=http://192.168.5.64:7897
```

---

## 各子项目启动方式

### 📋 putonghuaasr (普通话 ASR 标注)

**Docker 模式** (含浏览器 + agent 容器):
```bash
cd ~/zuoye/putonghuaasr/docker
docker compose up -d          # 启动浏览器+agent容器
docker compose logs -f agent  # 查看agent日志
```

**本地模式** (只用 ASR，不需要 Docker):
```bash
conda activate asr
cd ~/zuoye/putonghuaasr

# 运行双模型 ASR
python3 _work_context/local_segment_dual_asr.py \
  --url "音频URL" \
  --segments '[{"id":1,"start":0.0,"end":3.5}]'
```

---

### 📋 oneform (多任务标注)

```bash
cd ~/zuoye/oneform/docker
docker compose up -d          # 启动浏览器+agent
```

浏览器访问 noVNC: http://127.0.0.1:6081/vnc.html

---

### 📋 alibabaxiangmu (阿里标注)

```bash
cd ~/zuoye/alibabaxiangmu
docker compose up -d          # 启动浏览器
```

浏览器访问 noVNC: http://127.0.0.1:6084/vnc.html

---

### 📋 duomotai (多模态标注)

```bash
cd ~/zuoye/duomotai
docker compose up -d          # 启动浏览器
```

浏览器访问 noVNC: http://127.0.0.1:6085/vnc.html

---

### 📋 controlled-browser (通用受控浏览器)

```bash
cd ~/zuoye/controlled-browser
docker compose up -d
```

浏览器访问 noVNC: http://127.0.0.1:6082/vnc.html

---

### 📋 autotrade (量化交易)

```bash
cd ~/zuoye/autotrade
docker compose up -d          # 启动 PostgreSQL + Freqtrade
```

Freqtrade UI: http://127.0.0.1:8088

---

### 📋 henanhuaaser (河南话 ASR)

不需要 Docker，直接运行脚本:
```bash
conda activate asr
cd ~/zuoye/henanhuaaser
python3 scripts/appen_semi_auto.py
```

---

### 📋 英语TTS (英语语音标注)

```bash
conda activate asr
cd ~/zuoye/英语TTS
# 按需运行 codex-browser/ 或 codex-audio/ 下的脚本
```

---

### 📋 traedocker (Trae 试标)

按需运行 `fill_and_submit_resume_v7.py` 等脚本。

---

## 常用端口一览

| 服务 | 端口 | 说明 |
|------|------|------|
| putonghuaasr noVNC | 6080 | ASR 浏览器 |
| oneform noVNC | 6081 | Oneform 浏览器 |
| controlled-browser noVNC | 6082 | 通用浏览器 |
| traedocker noVNC | 6083 | Trae 浏览器 |
| alibabaxiangmu noVNC | 6084 | 阿里标注浏览器 |
| duomotai noVNC | 6085 | 多模态浏览器 |
| autotrade UI | 8088 | Freqtrade |
| mihomo 代理 | 7897 | 192.168.5.64 上运行 |

---

## 常见问题

**Q: Docker 容器启动失败？**
确保 Docker Desktop 已启动，且磁盘空间充足（项目约 40GB）。

**Q: ASR 识别很慢？**
Apple Silicon Mac 上 RTF 约 0.55（比 Ubuntu AMD 快），如更慢检查是否有其他进程占用 CPU。

**Q: 浏览器连不上？**
检查容器状态: `docker ps`，查看日志: `docker compose logs browser`。

**Q: 需要代理？**
```bash
export HTTP_PROXY=http://192.168.5.64:7897
export HTTPS_PROXY=http://192.168.5.64:7897
```
