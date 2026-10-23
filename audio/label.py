#!/usr/bin/env python3
"""Label short Pikachu clips with Gemini audio via OpenRouter. usage: label.py <clipdir> [batch]"""
import base64, json, os, sys, glob, urllib.request, subprocess, re
KEY=os.environ.get('OPENROUTER_API_KEY') or sys.exit('set OPENROUTER_API_KEY')
MODEL='google/gemini-3.8-flash'
CATS="grab_short, pulled_strain, happy, laugh, giggle, excited_cheer, surprised, scared, angry, sad, hurt, sneeze, yawn, snore_sleep, sleepy, singing, dizzy, greeting_hello, goodbye, name_pikachu, pika_short, chaa_attack, effort_grunt, tired_sigh, curious_question, kiss_affection, nonvoice_sfx, other"
def b64wav(p):
    out=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar','16000','-f','wav','-'],capture_output=True).stdout
    return base64.b64encode(out).decode()
def ask(files):
    content=[{'type':'text','text':f"You will hear {len(files)} short audio clips of the Pokemon Pikachu (or other sounds). For EACH clip return one JSON object per line: {{\"clip\": <number>, \"cat\": <one of: {CATS}>, \"words\": \"what is said phonetically e.g. pika, pikachu, chaaa\", \"emotion\": \"short words\", \"clean\": true if only Pikachu voice with no music/other voices/noise, \"pikachu\": true if it is Pikachu's voice}}. Output only the JSON lines."}]
    for i,f in enumerate(files):
        content.append({'type':'text','text':f'Clip {i+1}:'})
        content.append({'type':'input_audio','input_audio':{'data':b64wav(f),'format':'wav'}})
    body={'model':MODEL,'messages':[{'role':'user','content':content}],'temperature':0}
    req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',json.dumps(body).encode(),{'Authorization':'Bearer '+KEY,'Content-Type':'application/json'})
    r=json.load(urllib.request.urlopen(req,timeout=300))
    txt=r['choices'][0]['message']['content']; cost=r.get('usage',{}).get('cost',0)
    res=[]
    for line in txt.splitlines():
        line=line.strip().strip(',')
        if line.startswith('{'):
            try: res.append(json.loads(line))
            except Exception: pass
    return res,cost
if __name__=='__main__':
    d=sys.argv[1]; bs=int(sys.argv[2]) if len(sys.argv)>2 else 15
    files=sorted(glob.glob(f'{d}/*.wav')); out={}; total=0
    for i in range(0,len(files),bs):
        chunk=files[i:i+bs]
        try: res,cost=ask(chunk)
        except Exception as e: print('err',e); continue
        total+=cost or 0
        for r in res:
            k=r.get('clip')
            if isinstance(k,int) and 1<=k<=len(chunk): out[os.path.basename(chunk[k-1])]=r
    json.dump(out,open(f'{d}/labels.json','w'),indent=1)
    print(d,len(out),'/',len(files),'labelled cost $%.3f'%total)
