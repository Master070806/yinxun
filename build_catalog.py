"""Download attributed public tracks, then analyze every sample of every track locally."""
import json, hashlib, time, sys
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
import requests
ROOT=Path(__file__).resolve().parent
TITLES=['Aquarium','Hall of the Mountain King','Backbay Lounge','Hot Swing','Porch Swing Days - slower','Carefree','Aerosol of my Love','Life of Riley','Surf Shimmy','Twisted','Metalmania','Ready Aim Fire','Too Cool','Basic Implosion','Rhinoceros','Cipher','Whiskey on the Mississippi','Boogie Party','Bama Country','Guts and Bourbon','Gonna Start','Maccary Bay','Funkorama','Aces High']
def download():
    source_path=ROOT/'.cache/pieces.json'
    if not source_path.exists():
        response=requests.get('https://incompetech.com/music/royalty-free/pieces.json',timeout=60)
        response.raise_for_status()
        source_path.parent.mkdir(parents=True,exist_ok=True)
        source_path.write_text(response.text,encoding='utf-8')
    source=json.loads(source_path.read_text(encoding='utf-8'))
    tracks=[]
    for title in TITLES:
        p=next(x for x in source if x['title']==title)
        tracks.append(dict(id=p['isrc'],title=title,artist='Kevin MacLeod',source_genre_id=p['genre'],description=p.get('description'),source_url='https://incompetech.com/music/royalty-free/music.html',audio_url='https://incompetech.com/music/royalty-free/mp3-royaltyfree/'+quote(p['filename']),license='CC BY 4.0',license_url='https://creativecommons.org/licenses/by/4.0/'))
    target=ROOT/'data/catalog'; target.mkdir(parents=True,exist_ok=True)
    def one(t):
        path=target/(t['id']+'.mp3')
        if not path.exists():
            for attempt in range(4):
                try:
                    r=requests.get(t['audio_url'],timeout=(20,120)); r.raise_for_status()
                    tmp=path.with_suffix('.part');tmp.write_bytes(r.content)
                    import soundfile as sf
                    with sf.SoundFile(tmp) as f: assert f.frames>f.samplerate*20
                    tmp.replace(path);break
                except Exception:
                    if attempt==3: raise
                    time.sleep(2)
        print('Downloaded',t['title'],path.stat().st_size,flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(one,tracks))
    (ROOT/'catalog_sources.json').write_text(json.dumps(tracks,ensure_ascii=False,indent=2),encoding='utf-8')
def analyze():
    from experiment import MODEL,REVISION,LABELS,ClapProcessor,ClapModel,torch,F,np,sf,soxr,style_scores
    torch.manual_seed(0);np.random.seed(0)
    offline='--offline' in sys.argv
    if not torch.cuda.is_available():raise RuntimeError('Analysis requires CUDA PyTorch. The web prototype alone does not require a GPU.')
    processor=ClapProcessor.from_pretrained(MODEL,revision=REVISION,local_files_only=offline)
    model=ClapModel.from_pretrained(MODEL,revision=REVISION,local_files_only=offline,weights_only=True).to('cuda').eval()
    sr=processor.feature_extractor.sampling_rate
    with torch.inference_mode():
        texts=F.normalize(model.get_text_features(**processor(text=list(LABELS.values()),padding=True,return_tensors='pt').to('cuda')),dim=-1)
    mask=~torch.eye(12,dtype=torch.bool,device='cuda')
    assert torch.isfinite(texts).all() and (texts@texts.T)[mask].mean()<.98
    tracks=json.loads((ROOT/'catalog_sources.json').read_text(encoding='utf-8'))
    configuration=hashlib.sha256(json.dumps([MODEL,REVISION,LABELS,'duration-weighted-normalized-10s-v1'],sort_keys=True).encode()).hexdigest()
    out=ROOT/'outputs/catalog';out.mkdir(parents=True,exist_ok=True)
    for t in tracks:
        path=ROOT/'data/catalog'/(t['id']+'.mp3');digest=hashlib.sha256(path.read_bytes()).hexdigest()
        cached=out/(t['id']+'.json')
        if cached.exists():
            prev=json.loads(cached.read_text(encoding='utf-8'))
            if prev['sha256']==digest and prev.get('configuration')==configuration: t.update(prev);continue
        audio,original_sr=sf.read(path,dtype='float32',always_2d=True);audio=audio.mean(axis=1)
        if original_sr!=sr:audio=soxr.resample(audio,original_sr,sr)
        assert len(audio)>0 and np.isfinite(audio).all() and np.abs(audio).max()>1e-6
        windows=[audio[i:i+sr*10] for i in range(0,len(audio),sr*10)]
        batches=[]
        with torch.inference_mode():
            for i in range(0,len(windows),4):
                inputs=processor(audio=windows[i:i+4],sampling_rate=sr,return_tensors='pt').to('cuda')
                batches.append(F.normalize(model.get_audio_features(**inputs),dim=-1))
        vectors=torch.cat(batches);weights=torch.tensor([len(w) for w in windows],device='cuda',dtype=vectors.dtype)
        aggregate=F.normalize((vectors*weights[:,None]).sum(0,keepdim=True)/weights.sum(),dim=-1)
        assert torch.isfinite(aggregate).all()
        np.save(out/(t['id']+'.npy'),aggregate.squeeze(0).cpu().numpy())
        t.update(duration=round(len(audio)/sr,2),sha256=digest,configuration=configuration,style_scores=style_scores(aggregate,texts),audio='/audio/'+t['id']+'.mp3')
        cached.write_text(json.dumps(t,ensure_ascii=False,indent=2),encoding='utf-8')
        print('Analyzed',t['title'],t['style_scores'][:3],flush=True)
    report=dict(model=MODEL,revision=REVISION,aggregation='Duration-weighted mean of normalized 10-second embeddings, then normalized',prompts=LABELS,tracks=tracks)
    pending=ROOT/'web/catalog.pending.json'
    pending.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    pending.replace(ROOT/'web/catalog.json')
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--analyze' in sys.argv:analyze()
    else:download()
