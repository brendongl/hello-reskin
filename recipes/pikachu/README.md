# Recipe: Pikachu over Luigi

The worked example. It holds everything we used to build the Pikachu version **except the finished art and audio**:
mappings, prompts, loop points, sources, fix settings and scripts. Run the steps below to regenerate it on your
machine, or use it as the template for your own character.

Pokémon and Pikachu are trademarks of Nintendo / Creatures / GAME FREAK / The Pokémon Company. This is an
unofficial fan recipe. The sources listed are fetched by you, for your own copy. Nothing is redistributed here.

## Files

| File | What it is |
|---|---|
| `pack.json` | pack name + title ID; copy to `packs/pikachu/` |
| `text.json` | on-screen text map (Luigi → Pikachu, enemy names). The game font has no capital R, D or V, so those names are lowercase |
| `music_loops.json` | loop start/end samples (32 kHz) for each music layer, written by `audio/music/render.py` |
| `audio_map.csv` | which Pikachu clip(s) replaced each of Luigi's 191 voice lines, with the emotion category |
| `shape/b2746480.json` | freezes the gaze UV offset so the eye highlight stays put |
| `atlas_params.json` | eye-atlas settings for `tools/pika_atlas.py` (pass 14: eye colour, highlight size/position, eyelid rim, seam fix, tongue) |
| `fetch_sources.sh` | downloads every audio source we used (voice, music, Eevee, cries) and splits the clips |
| `audio/make_audio.py` | maps Luigi's voice triggers to Pikachu emotion categories, matches loudness, joins clips for long lines |
| `items/spec.py` | the style prompt and per-item subject prompts for every item texture |
| `items/gen_all.sh` | generates all item art in parallel (OpenRouter, Gemini 3 Pro Image; ~30 images ≈ US$4) |
| `items/fit.py` | cuts out the white background and fits each image into the original sprite's footprint |
| `items/pokeball.py` | renders the 5 Poké Ball coin-spin frames procedurally |
| `items/starlist.py` | builds the 4×3 Thunder Stone spin sheet (`StarList00`) |
| `items/extras.py` | empty gift box (used block), gift menu icon, rivet-less menu frame |
| `backgrounds/bg02.sh` | regenerates the Mario sticker wallpaper (`BG02`) with Pokémon stickers |

## Order of work

```bash
mkdir -p packs/pikachu && cp recipes/pikachu/{pack.json,text.json,music_loops.json} packs/pikachu/
mkdir -p packs/pikachu/shape && cp recipes/pikachu/shape/*.json packs/pikachu/shape/

# 1. face: draw/generate a flat front-facing Pikachu face on white -> packs/pikachu-reference/neutral_v1.png
EYE_SCALE=1.017 EYE_CIRCLE=1 EYE_ASPECT=0.946 python tools/make_face.py
python tools/pika_atlas.py recipes/pikachu/atlas_params.json

# 2. items (needs OPENROUTER_API_KEY)
bash recipes/pikachu/items/gen_all.sh && python recipes/pikachu/items/fit.py
python recipes/pikachu/items/pokeball.py && python recipes/pikachu/items/starlist.py && python recipes/pikachu/items/extras.py
bash recipes/pikachu/backgrounds/bg02.sh          # then pick a variant (see its last line)

# 3. audio
bash recipes/pikachu/fetch_sources.sh
python audio/label.py audio/clips/letsgo          # repeat per clip folder (labels feed make_audio.py)
python recipes/pikachu/audio/make_audio.py
cd audio/music && python render.py && cd ../..    # writes the music WAVs + packs/pikachu/music_loops.json

# 4. build
python tools/build_mod.py packs/pikachu
```

The scripts are the ones we actually ran. Expect to adjust paths and to eyeball every generated image. The AI
regularly sneaks original Mario characters back into backgrounds and adds extra limbs to small sprites.

## Slot mapping

| Mario / Luigi thing | Pikachu version | Slots |
|---|---|---|
| Luigi's face | Pikachu face (ears are pull/spring parts like the moustache) | face meshes, `FaceAtlas_Luigi`, `LuigiFace00`, `TouchGuide_Luigi*` |
| Gloves | yellow paws (recoloured the game's own gloves, which beat AI art) | `FaceMarioHand*` |
| Coin | Poké Ball (coin-style spin, front face squashed per frame) | `FaceEventCoin00–04` |
| Super Mushroom | Rare Candy | `FaceEventMushroom00`, `FaceBtnMushroom00` |
| Super Star | Thunder Stone (+ spin sheet) | `FaceEventStar00`, `StarList00`, `FaceBtnStar00` |
| ? Block / used block / menu | Mystery Gift box / empty box / gift icon | `FaceEventHatenaBlock00`, `FaceEventBlock00`, `FaceEventMenuHatena00`, `FaceEventMenuFrame00` |
| Goomba | Rattata | `FaceEventKuribo00` |
| Boo | Gastly (5 frames) | `FaceEventTeresa00–04` |
| Cheep Cheep | Magikarp (3 frames) | `FaceEventPukupuku00–02` |
| Blooper | Tentacool (+4 mini swim poses) | `FaceEventGesso00`, `FaceEventGessoMini00–03` |
| Bob-omb | Voltorb | `FaceEventBomb00` |
| Koopa / Piranha Plant in pipe | Diglett / Bellsprout | `FaceEventDokanNokonoko00–01`, `FaceEventDokanPakkun00–01` |
| Apple | Oran Berry | `FaceEventApple00` |
| Luigi's cap | Ash's cap | `FaceEventCap01` |
| Note block (background changer) | Poké Flute (Jigglypuff's mic read as a pink blob at menu size) | `FaceEventNoteBlock00` |
| Toad photographer | Eevee | `FaceEventToad00/02`, `FaceEventToadHand00`, `FaceBtnCamera00` |
| Luigi's voice (191 lines) | Pikachu (Let's Go, Hey You Pikachu, SSBU, PokeAPI cry) | `Voice_Luigi_Face_*` |
| Toad "Ho-hoo!" / laugh after photo | Eevee voice / Eevee laugh | `Voice_KinopioBlue_HoHo`, `SE_FaceTakePhotoAfter` |
| Boo / Blooper sounds | Gastly / Tentacool cries | `WU_SE_EMY_TERESA*`, `SE_FaceGessoAppear` |
| Music | Pokémon Center, Route 1, Surf, Let's Go title, wild battle, Poké Flute (sleep) | `Face_Luigi_*`, `Face_Ground_*`, `Face_Underwater_*`, `Face_MWTitle_*`, `Face_Star*`, `Face_Sleep.sh` |
| Mario sticker wallpaper | Pokémon sticker wallpaper | `BG02` |

Still Mario: the green warp pipe in the Diglett/Bellsprout events, and faint Cheep Cheep/Blooper silhouettes in the underwater background.

## Fixes this recipe already includes (and why)

Full detail is in `docs/PAINPOINTS.md`.

- **Eye highlight frozen** (`shape/b2746480.json`): otherwise the gaze slides the highlight around.
- **Seam fix** (`atlas_params.json` `seam_fix`): event glances shifted the eye texture into a leftover white line, which showed as a white strip in the right eye.
- **Eyelid rim** (`lid_open_clear` / `lid_fill_px`): stops a white crescent when the eyeballs move sideways.
- **Yellow backing under the eyes** (`make_face.py` `EYE_BACKING=1`): in the squish event, the eye holes stretch wider than the eyeballs.
- **Pikachu mouths** (`PIKA_MOUTH=1`): Luigi's open mouths have teeth and skin-coloured lips. They're recoloured to a dark red inside with a pink tongue, without adding nodes.
- **Moustache hidden** (default): Luigi's moustache becomes tiny yellow specks. Making it a cheek copy looked wrong, because it doesn't follow the face's sway.
- **Music layers are additive**: the 3 extra layers are quiet filtered copies (−5, −11, −20 dB under the main track), not full mixes.
- **Text patched in raw bytes**: the text tables can't be re-saved by UnityPy, so `build_mod.py` patches the strings in place.
