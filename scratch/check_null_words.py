import json
from backend.pipeline.orchestrator import run_speech_pipeline

transcript = '140000 miles away from the control station in Houston a giant rocket more than 300 feet tall the length of this football field made of new metal alloys some of which have not yet been embedded capable of standing heat and stresses several times more than have ever been experienced pitted together with a precision better than the finest watch carrying all the equipment needed for propulsion guidance control communication food and survival on an untried mission to an unknown celestial body and then return it safely to earth re-entering the atmosphere at speeds of over 25000 miles per hour causing heat about half that on the temperature of the sun almost as hot as it is here today and do all this and do all this and do it right and do it first if all this thick heat is out then we must be bald .'

res_orig = run_speech_pipeline('data/processed/jfk_rice_excerpt_real.wav', transcript)
res_null = run_speech_pipeline('data/injected/scratch_null.wav', transcript, reference_words=res_orig['words'])

print('Words in span 18.0 - 22.0s:')
for w, bw in zip(res_null['words'], res_orig['words']):
    if 18.0 <= w['start'] <= 22.0:
        z = w['z_by_feature'].get('f0_range_st_z')
        print(f"{w['text']}: obs_r={w['f0_range_st']} base_r={bw['f0_range_st']} obs_std={w['f0_std_st']} base_std={bw['f0_std_st']} z={z}")
