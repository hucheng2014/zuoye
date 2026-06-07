import requests, json, websocket, re
from pathlib import Path

SCRATCH = Path('/home/jianglei/zuoye/alibabaxiangmu/scratch')


def convert_timestamps(text):
    pattern = re.compile(r'\[(\d{2}):(\d{2}):(\d{2}\.\d{3})-(\d{2}):(\d{2}):(\d{2}\.\d{3})\]')
    def replace(m):
        hh1, mm1, ss1, hh2, mm2, ss2 = m.groups()
        return f"[{int(hh1)*60+int(mm1):02d}:{ss1}-{int(hh2)*60+int(mm2):02d}:{ss2}]"
    return pattern.sub(replace, text)


resp = requests.post("http://127.0.0.1:9237/json/list")
ws_url = next(t["webSocketDebuggerUrl"] for t in resp.json() if t.get("type") == "page")
ws = websocket.create_connection(ws_url)

expr = """
(function() {
  const items = document.querySelectorAll('.labelRender-item');
  const out = [];
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const video = item.querySelector('video');
    const duration = (video && Number.isFinite(video.duration)) ? video.duration : 0;
    const videoSrc = video ? (video.currentSrc || video.src || '') : '';
    const blocks = item.querySelectorAll('[class*="captionBlock"]');
    const texts = Array.from(blocks).map(b => b.innerText.trim()).filter(t => t && t !== '```' && t !== '```text');
    const originalCaption = texts.join('\\n');
    const checked = (item.querySelector('input[type=radio]:checked') || {}).value || '';
    out.push({idx: i, duration, videoSrc, originalCaption, checked});
  }
  return JSON.stringify(out);
})()
"""
ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                    "params": {"expression": expr, "returnByValue": True}}))
result = json.loads(ws.recv())
page_items = json.loads(result["result"]["result"]["value"])
ws.close()

results = []
for it in page_items:
    i = it["idx"] + 1
    cap_file = SCRATCH / f"batch_item_{i:02d}_caption_final.txt"
    rev_file = SCRATCH / f"batch_item_{i:02d}_review_final.json"
    caption = convert_timestamps(cap_file.read_text(encoding='utf-8'))
    review = json.loads(rev_file.read_text(encoding='utf-8')) if rev_file.exists() else {}
    video_path = str(SCRATCH / f"batch_item_{i:02d}_video.mp4")
    results.append({
        "index": it["idx"],
        "originalCaption": it["originalCaption"],
        "videoSrc": it["videoSrc"],
        "duration": it["duration"],
        "checked": it["checked"],
        "currentTextLength": len(caption),
        "choice": it["checked"],
        "caption": caption,
        "review": review,
        "languageErrors": [],
        "hardErrors": [],
        "blocking": [],
        "videoPath": video_path,
    })

out = SCRATCH / 'batch_current_results.json'
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"写入 {out} ({len(results)} 条)")

for r in results:
    old = re.findall(r'\[\d{2}:\d{2}:\d{2}\.\d{3}', r['caption'])
    print(f"item {r['index']+1}: duration={r['duration']:.3f}, choice={r['choice']}, old_ts={len(old)}")
