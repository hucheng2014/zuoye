# Road Bounding Box 做题流程（给 GPT-5.4-mini 用）

本项目任务类型：`Roads_PaintedFeatures_3D w/ Bounding Box`。先读 `tutorial_summary_bilingual.md`，但实际做题按下面流程执行。

## 1. 连接页面（所有命令固定用这个外壳）

```bash
docker exec -i oneform-agent python3 - <<'PY'
# python code here
PY
```

CDP 连接要点：
- HTTP: `http://browser:9223`
- HTTP header: `Host: localhost:9222`
- websocket URL 中把 `ws://localhost:9222` 替换成 `ws://browser:9223`
- websocket header 同样加 `Host: localhost:9222`

最小连接模板：

```python
import urllib.request, json, websocket, itertools, time, base64
base='http://browser:9223'
headers={'Host':'localhost:9222'}
ws=json.load(urllib.request.urlopen(urllib.request.Request(base+'/json/list',headers=headers)))[0]['webSocketDebuggerUrl']
ws=ws.replace('ws://localhost:9222','ws://browser:9223')
sock=websocket.create_connection(ws, header=['Host: localhost:9222'], timeout=10)
c=itertools.count(1)
def send(method, params=None):
    i=next(c)
    sock.send(json.dumps({'id':i,'method':method,'params':params or {}}))
    while True:
        msg=json.loads(sock.recv())
        if msg.get('id')==i:
            return msg
send('Runtime.enable')
# ...do work...
sock.close()
```

## 2. 抽取当前题图片

页面第一张 `document.images[0]` 通常就是 768×768 的道路截图，bounding box 已画在图上（紫/粉色框）。用浏览器凭证 fetch 后写到共享目录 `/app/RQOAE/`，宿主机可用 `../RQOAE/...` 读取。

```python
expr = r'''
(async () => {
  const img=document.images[0];
  const res=await fetch(img.currentSrc||img.src,{credentials:'include'});
  const buf=await res.arrayBuffer();
  let binary='';
  const bytes=new Uint8Array(buf), chunk=0x8000;
  for(let i=0;i<bytes.length;i+=chunk) binary+=String.fromCharCode(...bytes.subarray(i,i+chunk));
  return {src:img.currentSrc||img.src,status:res.status,b64:btoa(binary)};
})()
'''
val=send('Runtime.evaluate', {'expression':expr,'returnByValue':True,'awaitPromise':True})['result']['result']['value']
open('/app/RQOAE/current_roadbbox_task.jpg','wb').write(base64.b64decode(val['b64']))
print(val['status'], val['src'])
```

若需要放大 bounding box，可用 PIL 裁剪/放大保存到 `/app/RQOAE/current_roadbbox_crop.png`，再用宿主机路径 `../RQOAE/current_roadbbox_crop.png` 查看。

## 3. 判题规则（只看 bounding box 内）

1. **只评估紫/粉色 bounding box 内的问题**；框外完全忽略。
2. 不查卫星图、街景或真实世界；只看截图渲染。
3. 先判断严重程度：
   - `major`：不放大也明显、普通人一眼能看到，或框内整体明显有问题。
   - `minor`：需要仔细看或放大才确认，整体影响不大。
   - `no_issue`：框内道路可见且无可见问题。
   - `not_visible`：没有 3D 道路/道路渲染。
4. 如果选择 `major` 或 `minor`，必须勾选所有适用问题类型。

常见特征与标签：
- Painted Median：白色斜线填充/导流区/禁行喷绘区。边界弯曲、突兀折线、形状异常 → `Painted Median Issues / Poor Geometry`。
- Lane Marking：车道线、中心线、停止线等。锯齿、断裂、错误线型、多余线 → Lane Marking 对应项。
- Colored Lane：绿色自行车道、红/黄公交/HOV 等；不要把 crosswalk 当 colored lane。
- RSM Text：STOP、BUS ONLY、KEEP CLEAR 等文字。
- RSM Glyph：箭头、自行车图标、合流图标等。

问题类型：
- Poor Geometry：形状/边界/线型/闭合/端点/平滑度错误。
- Collide with another feature：两个本应独立的特征不应重叠却重叠。
- Void Issue：明显应该连续/存在的位置缺失。
- Excess Paint：不该有的喷绘或延伸太远。
- Other Issue：以上都不适合；要写简短说明。

不要标的问题：半透明地图箭头、道路标签、灰色铁路线、painted median 内部设计性的断续斜线、透明线穿过 sidewalk/crosswalk、州界线、RSM 周围轻微白边、正常模糊双黄线、非 painted features 缺失。

## 4. 表单操作

评分 radio 的 value 固定常见为：`major`、`minor`、`no_issue`、`not_visible`。

```python
# 选择严重程度，例如 major
send('Runtime.evaluate', {'expression':"document.querySelector('input[type=radio][value=\"major\"]').click()", 'returnByValue':True})
time.sleep(0.5)
```

选择 major/minor 后会出现 checkbox。当前 UI 的 checkbox 顺序通常是：

| index | feature | issue |
|---:|---|---|
| 0 | Painted Median | Poor Geometry |
| 1 | Painted Median | Excess Paint |
| 2 | Painted Median | Void Issue |
| 3 | Painted Median | Other Issue |
| 4 | Lane Marking | Poor Geometry |
| 5 | Lane Marking | Excess Paint |
| 6 | Lane Marking | Collide with another feature |
| 7 | Lane Marking | Void Issue |
| 8 | Lane Marking | Other Issue |
| 9 | Colored Lane | Poor Geometry |
| 10 | Colored Lane | Collide with another feature |
| 11 | Colored Lane | Excess Paint |
| 12 | Colored Lane | Void Issue |
| 13 | Colored Lane | Other Issue |
| 14 | Pavement signage text (RSM) | Poor Geometry |
| 15 | Pavement signage text (RSM) | Excess Paint |
| 16 | Pavement signage text (RSM) | Collide with another feature |
| 17 | Pavement signage text (RSM) | Void Issue |
| 18 | Pavement signage text (RSM) | Other Issue |
| 19 | Pavement signage glyph (RSM) | Poor Geometry |
| 20 | Pavement signage glyph (RSM) | Excess Paint |
| 21 | Pavement signage glyph (RSM) | Collide with another feature |
| 22 | Pavement signage glyph (RSM) | Void Issue |
| 23 | Pavement signage glyph (RSM) | Other Issue |
| 24 | Other Issues | Other/Unclear Feature Type Void Issue |
| 25 | Other Issues | Other Issue |

勾选 checkbox（例：Painted Median / Poor Geometry）：

```python
send('Runtime.evaluate', {'expression':"document.querySelectorAll('input[type=checkbox]')[0].click()", 'returnByValue':True})
```

如果 UI 变化，先打印 checkbox 列表再选：

```python
expr=r'''(() => [...document.querySelectorAll('input[type=checkbox]')].map((e,i)=>({i,label:(e.closest('label')?.innerText||e.parentElement?.innerText||'').trim(),checked:e.checked})))()'''
print(send('Runtime.evaluate', {'expression':expr,'returnByValue':True})['result']['result']['value'])
```

提交：

```python
expr=r'''(() => {
  const buttons=[...document.querySelectorAll('button')];
  const btn=buttons.reverse().find(b=>/Submit Rating/.test(b.innerText||''));
  if(!btn) return {ok:false,error:'Submit button not found'};
  btn.click();
  return {ok:true,text:btn.innerText};
})()'''
print(send('Runtime.evaluate', {'expression':expr,'returnByValue':True})['result']['result']['value'])
time.sleep(3)
```

提交后再次抽取 `document.images[0].src` 或 Task ID，确认已进入下一题。

## 5. 本轮当前题的判定记录

当前截图文件名：`6429_37.3327368,-121.8924181_image_0_0_0_0_0_bbox_3.jpg`。

bounding box 内是白色斜线 painted median/导流区，框中央偏右的下边界出现明显突兀折线/不规则凹凸，属于 painted median 的几何形状错误。判定：
- Severity: `Major issue seen within bounding box`
- Checkbox: `Painted Median Issues / Poor Geometry`
- 不需要 Other 评论。
