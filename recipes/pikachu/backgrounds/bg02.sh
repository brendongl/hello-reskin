#!/bin/bash
# BG02 = the faded all-over Mario sticker wallpaper (2520x1080). Regenerate it with Pokémon, from your own exported original.
# Generate 2+ variants and eyeball them: our first one sneaked Goombas and a Piranha Plant back in.
set -e
REF=$(ls template/textures/*/BG02.png | head -1); OUT=work/bg; mkdir -p $OUT packs/pikachu/textures
P="Redraw this wallpaper with Pokemon instead of Mario characters. Keep EXACTLY the same style: a dense all-over scattered pattern of small cute stickers on an off-white background, every sticker very washed-out and pale (low contrast pastel, about 35% opacity look), thin soft outlines, flat colours, same sticker size and spacing, slightly rotated at random. Use these Pokemon and items, each appearing several times: Poke Ball, Rattata, Gastly, Magikarp, Tentacool, Voltorb, Diglett, Bellsprout, Eevee, Jigglypuff, Rare Candy (blue wrapped candy), Thunder Stone (green stone with yellow lightning bolt), Oran Berry (blue berry), red-and-white gift box with yellow bow. No Pikachu. No Mario characters, no text, no logos, no border."
for v in a b; do python tools/gen_image.py -o $OUT/BG02_$v.png -i "$REF" --aspect 21:9 "$P" & done; wait
echo "pick one, then: python -c \"from PIL import Image;o=Image.open('$REF');Image.open('$OUT/BG02_b.png').convert('RGB').resize(o.size,Image.LANCZOS).save('packs/pikachu/textures/BG02.png')\""
