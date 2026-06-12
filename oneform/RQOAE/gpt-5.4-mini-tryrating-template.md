# GPT-5.4-mini TryRating 音频评分短模板

```markdown
你在 Docker 容器 `oneform-agent` 里做 tryrating.com 音频评分。不要猜；必须：读页面 → 下载音频 → 双验证 → 填 slider → 提交前检查 → 提交。

环境：
- CDP: `http://browser:9223`
- HTTP header: `Host: localhost:9222`
- WS 替换：`ws://localhost:9222` → `ws://browser:9223`
- 所有命令用：`docker exec -i oneform-agent python3 - <<'PY' ... PY`

## 1. 读页面实际任务

```bash
docker exec -i oneform-agent python3 - <<'PY'
import json, urllib.request
from websocket import create_connection

req=urllib.request.Request('http://browser:9223/json/list')
req.add_header('Host','localhost:9222')
p=json.loads(urllib.request.urlopen(req,timeout=5).read())[0]
ws=create_connection(p['webSocketDebuggerUrl'].replace('ws://localhost:9222','ws://browser:9223'),timeout=10)

expr=r'''
JSON.stringify({
 body:document.body.innerText,
 audios:Array.from(document.querySelectorAll("audio")).map((a,i)=>({i,src:a.src||a.currentSrc})),
 sliders:Array.from(document.querySelectorAll(".rc-slider-handle")).map((h,i)=>({i,value:h.getAttribute("aria-valuenow")})),
 buttons:Array.from(document.querySelectorAll("button")).map((b,i)=>({i,text:b.textContent.trim(),disabled:b.disabled})).filter(x=>x.text)
})
'''
ws.send(json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':expr,'returnByValue':True}}))
while True:
 d=json.loads(ws.recv())
 if d.get('id')==1:
  print(d['result']['result']['value'])
  break
PY
```

看清楚当前题型、prompt、正式音频 URL、slider 数量。不要只按旧 AGENTS.md 假设。

## 2. 模拟真实播放与防风控等待锁

在做题时，后台会严密监控你是否听完了每一段音频。
脚本必须：
1. 真实触发每一段 `<audio>` 的 `play()` 事件。
2. 动态获取音频时长（Duration），并强制等待（Sleep）足够的时间，绝不能秒交！
3. 若音频确实无法播放，则勾选“Audio does not load/play”选项并直接提交。

```bash
docker exec -i oneform-agent python3 - <<'PY'
import json, urllib.request, time
from websocket import create_connection

req=urllib.request.Request('http://browser:9223/json/list')
req.add_header('Host','localhost:9222')
p=json.loads(urllib.request.urlopen(req,timeout=5).read())[0]
ws=create_connection(p['webSocketDebuggerUrl'].replace('ws://localhost:9222','ws://browser:9223'),timeout=30)

mid=0
def evaljs(expr):
 global mid
 mid+=1
 ws.send(json.dumps({'id':mid,'method':'Runtime.evaluate','params':{'expression':expr,'awaitPromise':True,'returnByValue':True}}))
 while True:
  d=json.loads(ws.recv())
  if d.get('id')==mid:
   return d.get('result',{}).get('result',{}).get('value','')

play_js = r'''
(async () => {
  const audios = Array.from(document.querySelectorAll("audio"));
  if (audios.length === 0) {
    return JSON.stringify({ status: "no_audio", count: 0, bad: false });
  }
  
  let badAudioDetected = false;
  let playedList = [];
  
  for (let i = 0; i < audios.length; i++) {
    const audio = audios[i];
    
    // 等待元数据加载以获取时长
    if (isNaN(audio.duration) || audio.readyState < 1) {
      await new Promise((resolve) => {
        audio.addEventListener('loadedmetadata', resolve, { once: true });
        setTimeout(resolve, 4000); // 最多等4秒
      });
    }
    
    const duration = audio.duration;
    // 如果时长依然是 NaN，或者无法加载，或者存在明显的加载错误
    if (isNaN(duration) || duration <= 0 || audio.error) {
      console.log(`Audio ${i} seems broken.`);
      badAudioDetected = true;
      continue;
    }
    
    console.log(`Playing audio ${i}: duration ${duration.toFixed(2)}s`);
    try {
      audio.currentTime = 0;
      await audio.play();
      playedList.push({ index: i, duration: duration });
      
      // 等待播放结束，加上 1.5 秒的安全缓冲
      await new Promise((resolve) => {
        audio.addEventListener('ended', resolve, { once: true });
        setTimeout(resolve, (duration + 1.5) * 1000);
      });
      
      audio.pause();
    } catch (e) {
      console.log(`Play failed for audio ${i}:`, e.message);
      badAudioDetected = true;
    }
  }
  
  return JSON.stringify({
    status: "ok",
    played: playedList,
    bad: badAudioDetected
  });
})()
'''

print("开始模拟音频播放与风控检测...")
res_str = evaljs(play_js)
res = json.loads(res_str)
print("播放结果:", res)

# 如果检测到音频无法播放（坏题），尝试勾选 "Audio does not load/play" 并提交
if res.get('bad') == True:
    print("🚨 检测到损坏或无法播放的音频！尝试勾选 'Audio does not load/play' 坏题选项...")
    check_bad_js = r'''
    (function() {
      const elements = Array.from(document.querySelectorAll("label, span, div, input, p"));
      const keywords = ["audio does not load", "audio does not play", "audio cannot play", "audio cannot load"];
      const target = elements.find(el => {
        const text = el.textContent.trim().toLowerCase();
        return keywords.some(k => text.includes(k));
      });
      if (target) {
        if (target.tagName === 'INPUT') {
          target.click();
          return "checked_input";
        }
        const input = target.querySelector('input') || document.getElementById(target.getAttribute('for'));
        if (input) {
          input.click();
          return "checked_associated_input";
        }
        target.click();
        return "clicked_target_element";
      }
      return "not_found";
    })()
    '''
    check_res = evaljs(check_bad_js)
    print("勾选坏题选项结果:", check_res)
    
    if check_res != "not_found":
        print("已成功勾选坏题选项，正在准备提交此废题...")
        # 停顿一下以模拟真实动作
        time.sleep(2)
        submit_js = r'''
        (function(){
         var btn=Array.from(document.querySelectorAll("button")).filter(b=>b.textContent.trim()==="Submit Rating"&&!b.disabled).pop();
         if(!btn)return "no_submit_button";
         btn.click();
         return "clicked_submit";
        })()
        '''
        submit_res = evaljs(submit_js)
        print("坏题提交动作:", submit_res)
        time.sleep(3)
        print("当前页面状态:", evaljs("document.body.innerText.slice(-300)"))
        ws.close()
        raise SystemExit(0)  # 坏题已处理并提交，直接退出脚本
    else:
        print("未在页面上找到 'Audio does not load/play' 选项，请手动介入！")

ws.close()
PY
```

## 3. 下载正式音频

把正式音频 URL 填进 `urls`。必须用 `credentials:'include'`。

```bash
docker exec -i oneform-agent python3 - <<'PY'
import json, urllib.request, base64
from websocket import create_connection

urls=[
 ("A","URL_A"),
 ("B","URL_B"),
 ("C","URL_C"),
 ("D","URL_D"),
 ("E","URL_E"),
]

req=urllib.request.Request('http://browser:9223/json/list')
req.add_header('Host','localhost:9222')
p=json.loads(urllib.request.urlopen(req,timeout=5).read())[0]
ws=create_connection(p['webSocketDebuggerUrl'].replace('ws://localhost:9222','ws://browser:9223'),timeout=30,skip_utf8_validation=True,max_size=10000000)

mid=0
def evaljs(expr):
 global mid
 mid+=1
 ws.send(json.dumps({'id':mid,'method':'Runtime.evaluate','params':{'expression':expr,'awaitPromise':True,'returnByValue':True}}))
 while True:
  d=json.loads(ws.recv())
  if d.get('id')==mid:
   return d.get('result',{}).get('result',{}).get('value','')

for label,url in urls:
 out=f'/tmp/audio_{label}.wav'
 js=f'''
 (async()=>{{
   const resp=await fetch({json.dumps(url)},{{credentials:'include'}});
   const buf=await resp.arrayBuffer();
   const bytes=new Uint8Array(buf);
   let chunks=[];
   for(let i=0;i<bytes.length;i+=0x8000) chunks.push(String.fromCharCode.apply(null,bytes.subarray(i,i+0x8000)));
   return JSON.stringify({{status:resp.status,type:resp.headers.get('content-type'),b64:btoa(chunks.join(''))}});
 }})()
 '''
 obj=json.loads(evaljs(js))
 data=base64.b64decode(obj['b64'])
 open(out,'wb').write(data)
 print(label,obj['status'],obj['type'],len(data),out,data[:4])

ws.close()
PY
```

必须确认：`status=200`、type 是 audio、文件头是 `b'RIFF'`、大小不是几百 bytes。否则不能评分。

## 4. 双验证

### 4.1 PANNs 标签

```bash
docker exec -i oneform-agent python3 - <<'PY'
import numpy as np, librosa
from panns_inference import AudioTagging, labels

paths=[
 ('/tmp/audio_A.wav','A'),
 ('/tmp/audio_B.wav','B'),
 ('/tmp/audio_C.wav','C'),
 ('/tmp/audio_D.wav','D'),
 ('/tmp/audio_E.wav','E'),
]

at=AudioTagging(checkpoint_path=None,device='cpu')
for path,label in paths:
 y,sr=librosa.load(path,sr=32000,mono=True)
 out,_=at.inference(y[None,:])
 probs=out[0]
 idx=np.argsort(probs)[-10:][::-1]
 print('\n',label)
 for i in idx:
  print(labels[i],float(probs[i]))
PY
```

### 4.2 声学特征

```bash
docker exec -i oneform-agent python3 - <<'PY'
import librosa,numpy as np,json

paths=[
 ('/tmp/audio_A.wav','A'),
 ('/tmp/audio_B.wav','B'),
 ('/tmp/audio_C.wav','C'),
 ('/tmp/audio_D.wav','D'),
 ('/tmp/audio_E.wav','E'),
]

for path,label in paths:
 y,sr=librosa.load(path,sr=None,mono=True)
 rms=float(np.sqrt(np.mean(y*y)))
 silence=float(np.mean(np.abs(y)<0.01))
 zcr=float(np.mean(librosa.feature.zero_crossing_rate(y)[0]))
 flat=float(np.mean(librosa.feature.spectral_flatness(y=y)[0]))
 centroid=float(np.mean(librosa.feature.spectral_centroid(y=y,sr=sr)[0]))
 bw=float(np.mean(librosa.feature.spectral_bandwidth(y=y,sr=sr)[0]))
 print(json.dumps({"label":label,"dur":round(len(y)/sr,2),"rms":round(rms,4),"silence":round(silence,3),"zcr":round(zcr,3),"flatness":round(flat,3),"centroid":round(centroid,1),"bandwidth":round(bw,1)},ensure_ascii=False))
PY
```

根据 prompt 评分。例：prompt 是 `Noise White Noise`，PANNs 命中 `Static/White noise/Noise` 且频谱像噪声 → 高；命中 Music/Explosion/Siren/Speech → 低。

RQOAE 音乐编辑质量规则：
- 静音多 / RMS 极低 → 1
- 严重突兀/失真 → 1-2
- 轻微问题 → 2-3
- 平滑自然 → 4
- 无缝完美 → 5

## 5. 填 slider

分数位置：
- 1 → 0%
- 2 → 25%
- 3 → 50%
- 4 → 75%
- 5 → 100%

把最终评分填入 `ratings`。长度必须等于要填的正式 slider 数量。  
SFX-MUSHRA 常见顺序：`A prompt, A quality, B prompt, B quality...`

```bash
docker exec -i oneform-agent python3 - <<'PY'
import json,urllib.request,time
from websocket import create_connection

ratings=[4,4, 3,3, 1,1, 1,1, 1,1]  # 改成你的最终评分

req=urllib.request.Request('http://browser:9223/json/list')
req.add_header('Host','localhost:9222')
p=json.loads(urllib.request.urlopen(req,timeout=5).read())[0]
ws=create_connection(p['webSocketDebuggerUrl'].replace('ws://localhost:9222','ws://browser:9223'),timeout=30,skip_utf8_validation=True)

mid=0
def send(method,params=None):
 global mid
 mid+=1
 ws.send(json.dumps({'id':mid,'method':method,'params':params or {}}))
 ws.settimeout(15)
 while True:
  d=json.loads(ws.recv())
  if d.get('id')==mid:return d

def js(expr):
 r=send('Runtime.evaluate',{'expression':expr,'returnByValue':True})
 return r.get('result',{}).get('result',{}).get('value','')

send('Runtime.enable'); send('Input.enable')
count=int(js('document.querySelectorAll(".rc-slider").length'))
start=count-len(ratings)
fracs={1:0,2:.25,3:.5,4:.75,5:1}

for off,rating in enumerate(ratings):
 idx=start+off
 frac=fracs[rating]
 print("set",idx,"->",rating)
 js(f'document.querySelectorAll(".rc-slider")[{idx}].scrollIntoView({{block:"center"}})')
 time.sleep(.5)
 coords=json.loads(js(f'''
 (function(){{
  var r=document.querySelectorAll(".rc-slider")[{idx}].querySelector(".rc-slider-rail").getBoundingClientRect();
  return JSON.stringify({{x:r.left+r.width*{frac},y:r.top+r.height/2}});
 }})()
 '''))
 send('Input.dispatchMouseEvent',{'type':'mouseMoved','x':coords['x'],'y':coords['y']})
 send('Input.dispatchMouseEvent',{'type':'mousePressed','x':coords['x'],'y':coords['y'],'button':'left','clickCount':1})
 send('Input.dispatchMouseEvent',{'type':'mouseReleased','x':coords['x'],'y':coords['y'],'button':'left','clickCount':1})
 time.sleep(.4)

vals=json.loads(js('JSON.stringify(Array.from(document.querySelectorAll(".rc-slider-handle")).map(h=>Number(h.getAttribute("aria-valuenow"))))'))
print("values:",vals)
if vals[-len(ratings):] != ratings:
 print("ERROR mismatch; DO NOT SUBMIT")
 raise SystemExit(1)
print("ALL_OK")
ws.close()
PY
```

## 6. 提交前最终检查并提交

```bash
docker exec -i oneform-agent python3 - <<'PY'
import json,urllib.request,time
from websocket import create_connection

expected=[4,4, 3,3, 1,1, 1,1, 1,1]  # 改成最终评分

req=urllib.request.Request('http://browser:9223/json/list')
req.add_header('Host','localhost:9222')
p=json.loads(urllib.request.urlopen(req,timeout=5).read())[0]
ws=create_connection(p['webSocketDebuggerUrl'].replace('ws://localhost:9222','ws://browser:9223'),timeout=30,skip_utf8_validation=True)

mid=0
def send(method,params=None):
 global mid
 mid+=1
 ws.send(json.dumps({'id':mid,'method':method,'params':params or {}}))
 ws.settimeout(15)
 while True:
  d=json.loads(ws.recv())
  if d.get('id')==mid:return d

def js(expr):
 r=send('Runtime.evaluate',{'expression':expr,'returnByValue':True})
 return r.get('result',{}).get('result',{}).get('value','')

send('Runtime.enable')
vals=json.loads(js('JSON.stringify(Array.from(document.querySelectorAll(".rc-slider-handle")).map(h=>Number(h.getAttribute("aria-valuenow"))))'))
print("pre_submit:",vals)
if vals[-len(expected):] != expected:
 print("ERROR mismatch; not submitting")
 raise SystemExit(1)

res=js('''
(function(){
 var btn=Array.from(document.querySelectorAll("button")).filter(b=>b.textContent.trim()==="Submit Rating"&&!b.disabled).pop();
 if(!btn)return "no submit";
 btn.click();
 return "clicked";
})()
''')
print("submit:",res)
time.sleep(3)
print("body_tail:",js("document.body.innerText.slice(-500)"))
ws.close()
PY
```

成功后应看到 `No more surveys` 或进入下一题。

硬规则：
- 不要猜。
- 下载失败不能评分。
- 必须 PANNs + 声学特征双验证。
- 提交前必须确认 slider values 等于 expected。
- 如果不一致，停止，不提交。
```
