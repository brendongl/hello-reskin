#!/bin/bash
# BG01 = the blue underwater background with faint Cheep Cheep / Blooper silhouettes (2520x1080).
# Same approach as bg02.sh: generate 2 variants from your own exported original, pick one.
set -e
REF=$(ls template/textures/*/BG01.png | head -1); OUT=work/bg; mkdir -p $OUT packs/pikachu/textures
P="Redraw this underwater wallpaper with water Pokemon instead of the Mario sea creatures. Keep EXACTLY the same style, colours and layout: the same flat bright blue water, the same lighter-blue wavy sea floor at the bottom, the same tall pale-blue seaweed plants in the same places, the same small bubbles, and the creatures drawn as the same flat pale-blue silhouettes (slightly lighter than the water, no outlines, no other colours) at the same size and positions as the original fish and squid. Replace every Cheep Cheep fish with Magikarp (crown-like dorsal fin, whiskers, big round eye) and every Blooper squid with Tentacool (jellyfish dome with two gems and two long tentacles). Silhouettes only, no Mario characters, no text, no border."
for v in a b; do python tools/gen_image.py -o $OUT/BG01_$v.png -i "$REF" --aspect 21:9 "$P" & done; wait
echo "pick one, then: python -c \"from PIL import Image;o=Image.open('$REF');Image.open('$OUT/BG01_b.png').convert('RGB').resize(o.size,Image.LANCZOS).save('packs/pikachu/textures/BG01.png')\""
