# 3D 点云分割试标题全自动工具

## 目标

实现 Appen 平台“3D 点云分割”试标题的全程无人介入自动化：

1. 连接已登录的 Chrome CDP 浏览器
2. 抓取任务点云数据（PCD）
3. 使用 RANSAC + 高度阈值完成地面/非地面/噪声分割
4. 构造标注结果并通过 `/api/v1/tdl/submit` 提交
5. 全程无需人工点击或确认

## 环境要求

- Python 3.9+
- Playwright（已安装 Chromium）
- 远程或本地 Chrome CDP 端口（默认 `http://192.168.50.97:9239`）

## 安装依赖

```bash
pip3 install -r requirements.txt
playwright install chromium
```

## 运行

```bash
python3 main.py
```

## 配置

编辑 `config.yaml`：

- `browser.cdp_url`: CDP 地址
- `page.*`: 任务 ID 参数（已内置当前任务）
- `segmentation.*`: 分割算法参数
- `heartbeat.interval_seconds`: 防掉线心跳间隔

## 文件结构

```
.
├── main.py                    # 主控入口
├── config.yaml                # 配置文件
├── browser/
│   ├── controller.py          # CDP 连接、心跳、弹窗检测
│   └── injector.py            # 页面结果注入（备用）
├── data/
│   ├── fetcher.py             # 抓取 taskData 与 PCD
│   ├── parser.py              # PCD/BIN/LAS 解析
│   ├── annotation_encoder.py  # 标注结果编码
│   └── submitter.py           # API/UI 提交
├── segmentation/
│   ├── ground_ransac.py       # RANSAC 地面提取
│   ├── height_filter.py       # 高度分类
│   └── noise_filter.py        # 噪声过滤
├── utils/
│   ├── logger.py              # 日志
│   └── screenshot.py          # 截图
└── tests/                     # 单元测试
```

## 测试

```bash
python3 -m pytest tests/ -v
```

## 注意事项

- 工具依赖浏览器已经登录 Appen 并处于正确的任务页面。
- 如果页面出现“长时间未操作”弹窗，系统会在后台继续执行，但浏览器容器不稳定可能导致超时。
- 提交成功后会保存截图到 `logs/screenshots/`。
