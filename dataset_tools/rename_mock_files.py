import json
import os

# 1. Rename files in data/cached_results
cached_dir = 'data/cached_results'
if os.path.exists(cached_dir):
    for fname in os.listdir(cached_dir):
        if fname.endswith('.json') and not fname.startswith('mock_'):
            old_p = os.path.join(cached_dir, fname)
            new_p = os.path.join(cached_dir, f'mock_{fname}')
            
            # Read and update analysis_id inside
            try:
                with open(old_p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data['meta']['analysis_id'] = f"mock_{data['meta']['analysis_id']}"
                data['meta']['is_mock_data'] = True
                with open(new_p, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                os.remove(old_p)
                print(f"[RENAME] {old_p} -> {new_p}")
            except (json.JSONDecodeError, OSError, KeyError) as e:
                print(f"[ERR] {e}")

# 2. Rename files in data/demo_audio
audio_dir = 'data/demo_audio'
if os.path.exists(audio_dir):
    for fname in os.listdir(audio_dir):
        if fname.endswith('.wav') and not fname.startswith('mock_'):
            old_p = os.path.join(audio_dir, fname)
            new_p = os.path.join(audio_dir, f'mock_{fname}')
            os.rename(old_p, new_p)
            print(f"[RENAME] {old_p} -> {new_p}")
