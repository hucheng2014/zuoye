# AD 做题记录

每批题建议保存一个 JSON 文件：

```bash
python3 tools/validate_ad_batch.py --init records/2026-05-18_batch_001.json --count 5
```

填写完成后校验：

```bash
python3 tools/validate_ad_batch.py records/2026-05-18_batch_001.json --require-checked
```

记录文件是提交前复核依据：页面填写内容必须与记录一致。
