# Step-by-step guide

Commands run from the repo root on Linux/WSL. Paths in `romfs/`, `exefs/`, `dump/`, `export/`, `template/textures/`,
`packs/` and `build/` are your own working files and are git-ignored. **Never commit or share them.**

## 1. Dump the game and keys (on your Switch)

1. Update the console, then run **Lockpick_RCM** and copy `prod.keys` (and `title.keys`) to `~/.switch/`.
2. Dump Hello, Luigi! (`0100D8C0251AE000`, v0) with **nxdumptool** as an NSP. Remove console-specific ticket data
   (nxdumptool option), so the ticket is a common one.

## 2. Extract

```bash
python3 tools/pfs0.py -x game.nsp nsp/          # unpacks NCAs and writes nsp/title.keys from the ticket
cd tools/hx && dotnet build -c Release -o out && cd ../..
# the program NCA is the biggest .nca in nsp/
NCA=$(ls -S nsp/*.nca | head -1)
dotnet tools/hx/out/hx.dll ~/.switch/prod.keys nsp/title.keys $NCA 0 exefs
dotnet tools/hx/out/hx.dll ~/.switch/prod.keys nsp/title.keys $NCA 1 romfs
```

Why `hx`: the RomFS is compressed and hactool / nstool fail on it (PAINPOINTS §1).

## 3. Read the game's scripts (once)

Get **Il2CppDumper 6.7.46** (Perfare) and run:

```bash
dotnet Il2CppDumper.dll exefs/main romfs/Data/Managed/Metadata/global-metadata.dat dump/
```

You need `dump/DummyDll/`. UnityPy uses it to read the game's stripped MonoBehaviours (`tools/env.py`).

## 4. Python setup

```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sudo apt install ffmpeg            # and yt-dlp if you source audio from video
export OPENROUTER_API_KEY=...      # optional: AI art (tools/gen_image.py) and audio labelling (audio/label.py)
```

## 5. Export slots and metadata

```bash
python tools/inventory.py          # inventory.json: every bundle and what's in it
python tools/export_tex.py         # export/tex/*.png + export/textures.json (your copies of the textures)
python tools/make_template.py      # template/textures/<category>/<name>.png, per template/MANIFEST.csv
python tools/extract_meta.py       # export/svgfiles.pkl (face meshes) + export/mb_*.json (face/touch params)
```

`template/textures/` is your reference: open a slot, draw the replacement at the **same size and framing**, and save it
into `packs/<you>/textures/<SlotName>.png`. `template/AUDIO_SLOTS.csv` lists every sound by clip name.

## 6. Make a pack

```
packs/<you>/
  pack.json            {"name": "mychar-v1", "title_id": "0100D8C0251AE000"}
  textures/<Slot>.png  any texture from MANIFEST.csv (resized to the original size and re-encoded automatically)
  audio/<Clip>.wav     any clip from AUDIO_SLOTS.csv (mono 32 kHz by default)
  music_loops.json     {"<Clip>": [loop_start, loop_end]}: these clips are built stereo with FMOD loop points
  text.json            {"Luigi": "MyChar"}: exact on-screen strings to replace, in all languages
  shape/b2746480.json  optional face-shape field overrides (we freeze the gaze offset here)
  face_override/       written by tools/make_face.py (the new face meshes)
```

Start by copying `recipes/pikachu/` files into `packs/<you>/` and editing them.

### Face

1. Draw (or generate) **one flat, front-facing face on white**: solid fills, one dark outline, no shading, ears included.
   Look at `recipes/pikachu/` for the proportions that work.
2. `FACE_SRC=my_face.png PACK=packs/<you> EYE_CIRCLE=1 python tools/make_face.py`
   (Pikachu used `EYE_SCALE=1.017 EYE_CIRCLE=1 EYE_ASPECT=0.946`.)
3. Eyes: `PACK=packs/<you> python tools/pika_atlas.py recipes/pikachu/atlas_params.json` (copy and tune the params).
   The script names say "pika", but the recolouring rules work for any dark-eyed character.

### Items and backgrounds

Each item is a texture slot (`FaceEvent<Item>NN`, `FaceBtn<Item>00`). Keep the original framing: the game trims some
sprites to the original outline (the coin, for example), so art that pokes outside it gets cut off. See
`recipes/pikachu/items/` for the AI prompt template, the cut-out/fit script and the spin-frame renderers.

### Voice and sounds

Name each WAV after the clip it replaces. Match the original loudness (PAINPOINTS §5). `audio/split.py` cuts long
recordings into clips on silence, and `audio/label.py` labels them with an audio model, so you can map them by emotion.

### Music

Each track has 4 synced layers that are **added together** when the face is touched. Render them with
`audio/music/render.py` (uses `findloop.py` to find a seamless loop) and list the loop points in `music_loops.json`.

## 7. Build and install

```bash
python tools/build_mod.py packs/<you>
```

Copy `build/<name>/atmosphere/` to the root of your SD card (merge folders). Fully close and restart the game after
every change: bundles load once at start-up. Remove the folder `atmosphere/contents/0100D8C0251AE000/` to go back
to the original.

## 8. Test checklist

Most bugs only showed up in specific events, so play for a while and trigger everything:
- idle for several minutes (blink, sleepy, look-around)
- touch and drag the face, ears, cheeks and nose; pinch/squish
- every item in the ? menu, the camera, the background changer
- controller buttons ZL/ZR/+/−/X/Y fire random events
- let it fall asleep

If you can, screenshot continuously while someone plays, and look through the frames for white gaps, leftover
Luigi parts and clipped sprites. PAINPOINTS lists every failure we found and its fix.
