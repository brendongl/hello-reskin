#!/bin/bash
# Download the audio the Pikachu recipe was built from (run from the repo root). Needs yt-dlp + ffmpeg.
# Nothing here is redistributed by this repo: you fetch it yourself, for your own copy.
set -e
mkdir -p audio/sources audio/music/src audio/eevee audio/cries
yt() { yt-dlp -q -x --audio-format wav ${3:+--download-sections "*0-$3"} -o "$1.%(ext)s" "https://www.youtube.com/watch?v=$2"; echo "ok $1"; }
# --- Pikachu voice sources (split into short clips, labelled, then mapped onto Luigi's 191 lines) ---
cd audio/sources
yt yt_letsgo NXJMTDGhjBk; yt yt_heyyou_jp ti5AAFQw1_c; yt yt_heyyou_a qvciVpXKLaE; yt yt_yawn 5yZPvHIsE20
yt yt_laugh Vau5LBrvrao; yt yt_sneeze IkecZSaiMno; yt yt_singing XtkR4AM582Q
yt yt_ssbu_pikachu_voice Z5kVUlqeu4o; yt yt_ssbu_pikachu_sfx U_1q7Zo2GZw
curl -sL -o pikachu_cry_pokeapi_latest.ogg https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/25.ogg
cd ../music/src   # --- background music (Let's Go OST); loop points are found by audio/music/findloop.py ---
yt center v4UGB5riDsE 240; yt route1x OlM_z4t3ZSU 160; yt surf eSnLuPBqKrI 125; yt title R_05Cn2rFBQ 110
yt flute 5cwEE4jgXRQ 25; yt battle X5q68IAZcMI 130
cd ../../eevee; yt src qvqsf2aZdIc      # --- Eevee (photographer) voice; clips ev_030 + ev_053 used ---
cd ../cries         # --- item Pokémon cries (Gastly, Tentacool, Magikarp, Voltorb) ---
for p in gastly:92 tentacool:72 magikarp:129 voltorb:100; do curl -sL -o ${p%%:*}.ogg https://raw.githubusercontent.com/PokeAPI/cries/main/cries/pokemon/latest/${p##*:}.ogg; done
cd ../..
for n in letsgo heyyou_jp heyyou_a yawn laugh sneeze singing; do python3 audio/split.py audio/sources/yt_$n.wav audio/clips/$n $n; done
python3 audio/split.py audio/sources/yt_ssbu_pikachu_voice.wav audio/clips/ssbu_voice ssbuv
python3 audio/split.py audio/eevee/src.wav audio/eevee/clips ev
echo "sources ready"
