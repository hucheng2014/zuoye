import urllib.request
import json

req_data = {
    'text': '你好，能听见我的声音吗。这是一个测试。',
    'text_lang': 'zh',
    'ref_audio_path': r'D:\oneform\generated_audio\sovits_refs\myvoice_cpu_v2pro_zh_ref.wav',
    'prompt_text': '这是测试',
    'prompt_lang': 'zh'
}

req = urllib.request.Request(
    'http://127.0.0.1:9880/tts',
    data=json.dumps(req_data).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req) as response:
        audio = response.read()
    with open(r'd:\oneform\test_api.wav', 'wb') as f:
        f.write(audio)
    print('Saved test_api.wav size:', len(audio))
except Exception as e:
    print('Failed:', e)
