import os
import re
import urllib.request

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) SpeechHackathon/1.0'}

files = [
    ('https://commons.wikimedia.org/wiki/File:Ronald_Reagan_speaks_on_the_Challenger_Space_Shuttle_Disaster.ogg', 'data/raw/reagan_challenger_1986.ogg'),
    ('https://commons.wikimedia.org/wiki/File:First_Inauguration_of_FDR_-_Fear_Itself_Excerpt.ogg', 'data/raw/fdr_fear_itself_1933.ogg')
]

for page_url, dest in files:
    try:
        req = urllib.request.Request(page_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        
        # Find upload.wikimedia.org link
        matches = re.findall(r'(https://upload\.wikimedia\.org/wikipedia/commons/[^\s"\'<>]+?\.(?:ogg|mp3))', html)
        if matches:
            audio_url = matches[0]
            print(f"[OK] Found audio URL: {audio_url}")
            req_audio = urllib.request.Request(audio_url, headers=headers)
            with urllib.request.urlopen(req_audio) as a_resp, open(dest, 'wb') as out_f:
                out_f.write(a_resp.read())
            print(f"[OK] Successfully downloaded {dest}, size: {os.path.getsize(dest)} bytes")
        else:
            print(f"[FAIL] Could not find audio link on {page_url}")
    except (urllib.error.URLError, OSError, RuntimeError) as e:
        print(f"[FAIL] Error processing {page_url}: {e}")
