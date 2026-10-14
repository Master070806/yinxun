"""Local, reproducible CLAP smoke experiment. No audio is uploaded."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent
os.environ['HF_HOME'] = str(ROOT / '.cache' / 'huggingface')
os.environ['LIBROSA_DATA_DIR'] = str(ROOT / 'data' / 'examples')
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

import librosa
import numpy as np
import soundfile as sf
import soxr
import torch
import torch.nn.functional as F
from transformers import ClapModel, ClapProcessor

MODEL = 'laion/clap-htsat-unfused'
REVISION = '8fa0f1c6d0433df6e97c127f64b2a1d6c0dcda8a'
# Deliberately broad baseline. These are experiment candidates, not a final taxonomy.
LABELS = {
    'classical': 'Classical orchestral music with strings and acoustic instruments.',
    'jazz': 'Jazz music with swing rhythm and improvised instrumental solos.',
    'folk': 'Folk music with acoustic instruments and a singer.',
    'pop': 'Pop music with a catchy vocal melody and a steady rhythm.',
    'rock': 'Rock music with electric guitars, bass and drums.',
    'metal': 'Heavy metal music with distorted guitars and aggressive drums.',
    'hip_hop': 'Hip hop music with rapping over a rhythmic beat.',
    'electronic': 'Electronic music with synthesizers and programmed drums.',
    'blues': 'Blues music with expressive guitar and blues phrasing.',
    'country': 'Country music with acoustic guitar, twang and storytelling vocals.',
    'reggae': 'Reggae music with offbeat guitar chords and a prominent bass line.',
    'funk': 'Funk music with syncopated bass and tight rhythmic grooves.',
}


def style_scores(vector, texts):
    scores = (vector @ texts.T).detach().cpu().numpy().reshape(-1)
    names = list(LABELS)
    return [{'label': names[i], 'cosine_similarity': round(float(scores[i]), 5)}
            for i in np.argsort(-scores)]


def main():
    out = ROOT / 'outputs'
    out.mkdir(exist_ok=True)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable. Install the GPU build before this experiment.')
    torch.manual_seed(0)
    np.random.seed(0)
    print('GPU:', torch.cuda.get_device_name(0), flush=True)
    # Downloads public example recordings and their accompanying license notices.
    samples = []
    with (out / 'sample_sources.txt').open('w', encoding='utf-8') as notices:
        for key in ['brahms', 'choice', 'fishin']:
            path = librosa.example(key)
            with contextlib.redirect_stdout(notices):
                librosa.util.example_info(key)
            samples.append((key, path))
    print('Loading model:', MODEL, flush=True)
    processor = ClapProcessor.from_pretrained(MODEL, revision=REVISION)
    # Official checkpoint is distributed as .bin; keep weights_only loading enabled.
    model = ClapModel.from_pretrained(MODEL, revision=REVISION, weights_only=True).to('cuda').eval()
    sr = processor.feature_extractor.sampling_rate
    text_inputs = processor(text=list(LABELS.values()), padding=True, return_tensors='pt').to('cuda')
    with torch.inference_mode():
        text_vectors = F.normalize(model.get_text_features(**text_inputs), dim=-1)
    pairwise = text_vectors @ text_vectors.T
    off_diagonal = pairwise[~torch.eye(len(LABELS), dtype=torch.bool, device='cuda')]
    if not torch.isfinite(text_vectors).all() or off_diagonal.mean().item() > 0.98:
        raise RuntimeError('Text embedding sanity check failed; do not use this checkpoint for tagging.')
    report = {'model': MODEL, 'model_revision': model.config._commit_hash,
              'torch': torch.__version__, 'gpu': torch.cuda.get_device_name(0),
              'sampling_rate': sr, 'prompts': LABELS,
              'mean_pairwise_text_cosine': off_diagonal.mean().item(),
              'analysis_scope': 'entire_input_file',
              'aggregation': 'duration_weighted_mean_of_normalized_window_embeddings_then_l2_normalize',
              'note': 'Similarity is not probability. This is not an accuracy benchmark.',
              'samples': []}
    for key, path in samples:
        with sf.SoundFile(path) as source:
            original_sr = source.samplerate
            audio = source.read(dtype='float32', always_2d=True).mean(axis=1)
        if original_sr != sr:
            audio = soxr.resample(audio, original_sr, sr)
        if audio.size == 0 or not np.isfinite(audio).all() or np.max(np.abs(audio)) < 1e-6:
            raise ValueError(f'Invalid or silent audio: {key}')
        windows = [audio[i:i + 10 * sr] for i in range(0, len(audio), 10 * sr)]
        torch.cuda.synchronize()
        started = time.perf_counter()
        batches = []
        max_repeat_diff = 0.0
        with torch.inference_mode():
            for offset in range(0, len(windows), 4):
                inputs = processor(audio=windows[offset:offset + 4], sampling_rate=sr,
                                   return_tensors='pt').to('cuda')
                batch = F.normalize(model.get_audio_features(**inputs), dim=-1)
                repeated = F.normalize(model.get_audio_features(**inputs), dim=-1)
                max_repeat_diff = max(max_repeat_diff, float((batch - repeated).abs().max()))
                batches.append(batch)
        vectors = torch.cat(batches, dim=0)
        torch.cuda.synchronize()
        if not torch.isfinite(vectors).all():
            raise ValueError('Non-finite embedding')
        weights = torch.tensor([len(window) for window in windows], device='cuda', dtype=vectors.dtype)
        aggregate = F.normalize((vectors * weights[:, None]).sum(dim=0, keepdim=True) / weights.sum(), dim=-1)
        item = {'key': key, 'source_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                'clip_start': 0, 'clip_seconds': len(audio) / sr,
                'embedding_dimension': vectors.shape[-1],
                'preprocessing_and_two_inference_passes_seconds': round(time.perf_counter() - started, 3),
                'repeat_max_abs_diff': max_repeat_diff,
                'style_scores': style_scores(aggregate, text_vectors)}
        np.save(out / f'{key}_embedding.npy', aggregate.squeeze(0).cpu().numpy())
        report['samples'].append(item)
        print(key, json.dumps(item, ensure_ascii=False), flush=True)
    pending = out / 'results.pending.json'
    pending.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    pending.replace(out / 'results.json')
    print('Saved:', out / 'results.json', flush=True)


if __name__ == '__main__':
    main()
