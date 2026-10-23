# Hello-Reskin: pain points and lessons

Everything that went wrong while building the Pikachu-over-Luigi reskin by hand (October 2026), with the cause
and the fix. Read this before you start your own character: most of these will bite you too.
(Some notes mention a future "web app": the long-term idea is one reference image in, a finished mod out.)

Target: Hello, Luigi! 0100D8C0251AE000 v0 (Unity 6000.0.76f1, IL2CPP, Addressables 2.9.1).
Peach 01008790251AC000 and Yoshi 0100D060251AA000 are the same engine (not yet checked).

---

## 0. Pipeline overview (what the app has to run)

| Stage | Tool | Automatable? |
|---|---|---|
| Unpack NSP, extract exefs/romfs | hactool / nstool / LibHac tool `tools/hx` | Yes, run once per game version; ship pre-extracted metadata only |
| Read stripped MonoBehaviours | Il2CppDumper DummyDll + UnityPy TypeTreeGenerator | Yes, once per game version |
| Reference image → clean flat face | Image model (Gemini 3 Pro Image via OpenRouter) | Yes, with a human approve/regenerate loop |
| Face image → vector parts on Luigi's skeleton | `tools/make_face.py` | Partly, see §3 (segmentation needs per-image hints) |
| Eye texture atlas | `tools/pika_atlas.py` | Yes (recolour rules) |
| Hands, icons, touch guides | Recolour originals / cut out reference art | Yes |
| Voice | yt-dlp/web sources → split → Gemini audio labelling → `recipes/pikachu/audio/make_audio.py` | Mostly; sourcing is the legal/practical problem (§5) |
| Build bundles | `tools/build_mod.py packs/<name>` | Yes |
| Deliver | Zip `atmosphere/…`, or push over sys-autopilot `/files` | Yes |

---

## 1. Unpacking / keys

- **Keys too old.** The game needs recent keys (key generation 0x16). Dump current `prod.keys` from **your
  own console** with Lockpick_RCM after updating it. Never share or commit keys.
- **Compressed RomFS.** hactool and nstool 1.9.2 fail ("Failed to read RomFS directory cache" /
  hash layer fail). Fix: a small C# tool on the LibHac 0.19.0 NuGet package (`tools/hx`).
  The LibHac GitHub repo is gone, but NuGet still serves the package.
- **Stripped typetrees.** MonoBehaviours have no typetree, so you need Il2CppDumper → DummyDll →
  UnityPy `TypeTreeGenerator('6000.0.76f1')`. All 30 bundles must be loaded together, because the
  scripts live in another CAB.

## 2. Bundles / loading

- No IPS is needed: images and audio are LayeredFS file replacements under
  `atmosphere/contents/<TID>/romfs/Data/StreamingAssets/aa/Switch/<bundle>`.
- The Addressables catalog has **crc=0** for every bundle, so modified bundles load without
  editing `catalog.bin`. *Check this per game version.*
- The original bundles are stored uncompressed (35 MB serialized). Saving with LZ4 is fine and much smaller.
- UnityPy rebuilds are **not byte-identical** between runs, so compare files by content, not hash, when
  deciding what to re-upload.
- Textures: ASTC 6x6 with the Switch swizzle. UnityPy re-encodes and swizzles correctly, and the images
  are resized to the original dimensions.

## 3. Face (the hard part)

The face is **not a bitmap**. `FaceSvgImageFile` holds pre-tessellated vector meshes per named part
(Cap, Face00/01, Hair, Ear, Eye layers, about 25 Mouth shapes, Eyebrow, Beard, Nose). Code deforms
them by name.

| Pain point | Cause | Fix / rule for the app |
|---|---|---|
| Colours looked wrong | BaseColor is **ABGR** uint32 | Always convert RGB↔ABGR |
| Preview upside-down | Vertex space is y-down; hinge space is y-up relative to canvas centre (1875,1875) | Keep both conventions explicit |
| **Head randomly vanished** (white face, v1–v2) | (a) Some nodes held **more than one geometry**; every original node holds exactly one. (b) Luigi has a **second head copy `Face01`** that the game swaps to while sleeping, twitching or being pinched. I had blanked it. | **One geometry per node. Never blank Face01**: give it the same head fill/outline/cheeks as Face00 |
| Meshes 4–8× denser than the original | Over-densified perimeters | Simplify + max segment ~30 units. Total stayed below the original (4.7k vs 7.8k vertices) |
| Yellow ring around eyes | The eye textures include an eyelid "skin" margin; I scaled the eye layers to the texture bbox | Map **Luigi's eye hole perimeter** (from Face00/0 holes) onto the new eye circle, and scale the eye layers by the same transform. Their margins then hide under the head |
| Eyes looked like concentric rings | Iris, pupil and sclera in different shades | Unify to one dark colour; keep only the highlight |
| Highlight too small / not Pikachu-like | Luigi's tiny highlight dot | Draw a big up-left ellipse in each pupil rect. Draw it **tall (aspect 211/148)** because the game squashes the atlas content into a circle |
| X/spiral dizzy eyes invisible | Dark glyph on a dark eye | Turn glyph strokes white. Note: anti-aliased edges look like skin colour, so use a strict skin threshold (ΔE<25) |
| Hidden parts still interactive | Code needs the Cap/Hair/Beard/Eyebrow nodes and their collision | Shrink them to tiny specks coloured like whatever is underneath (yellow on the head, **red on cheeks**) |
| Ears wanted as a grab spot | — | `EarL/R_Normal00` already have pull/spring physics. Put the new ears there and move `cHingedPos` to the ear base (in `FaceSvgPage<Char>.cPartsParamArray`). The moustache's extra behaviours (swing, swipe-down to sleep) are tied to the Beard nodes in code |
| Ear base gap when pulled | Ears are drawn behind the head | Extend each ear polygon under the head (union with head ∩ ear.buffer(60)) |
| Ears/head are one connected region in the drawing | The art joins them at the base | Needed **manual split points** (left/right ear-base lines). *App:* ask the image model for parts on separate layers, or ask the user to tap the ear bases |
| Talking mouths still Luigi's | 25 mouth shapes; only the neutral one was redrawn | *App:* generate a mouth sheet (closed, a/i/u/e/o, laugh, surprise, sad, fear, grin) from the approved face, then vectorise each into the matching `Mouth_*` node |
| Highlight drifts/clips with gaze | The pupil sprite is UV-offset by gaze (`FaceSvgShapeLuigi.mDefaultUVOffsetSpriteEyeL/R` = ∓0.14, `mUVOffsetMaxSpriteEye` 0.5) | For flat "disc + highlight" eyes, freeze it: `packs/<p>/shape/<bundle8>.json` sets all three to 0 (build_mod applies it) |
| Grey/brown rim around the eye | The open **eyelid** texture cell has a dark outline ring around its transparent hole | Recolour or clear it |
| Eye outline faceted (octagon) | (a) mesh simplify tol 1.5 left about 13 edges on the eye holes; (b) **the real cause**: eyelid dark fill grown with `binary_dilation` (diamond-shaped) | Euclidean distance growth (`distance_transform_edt`); fine tessellation (tol 0.15) on the head fill |
| Highlight lumpy / egg-shaped / notched | (a) the atlas is minified about 4.4× on screen, so hard edges alias; (b) **the real cause**: the open-eyelid cell's opening is smaller than the eye circle, so it clips the highlight with a straight edge | Draw the highlight with a ~9 px anti-aliased edge; **clear the rim of the open-eyelid cells** (only those two cells; the sleepy and blink cells keep their lid lines) |
| Eye texture layers are 25-point polygons | Replacing them with circles changed the texture scale (the game maps UVs to the layer's own bounds) | Leave their shape alone; control the outline with the head hole |
| Eye shows a white crescent when glancing sideways | Clearing the eyelid rim exposed the background when gaze moves the eyeball **geometry** (UV freeze doesn't stop it) | Open the lid hole only enough for the highlight (32 px) and keep a dark rim beyond (75 px) |
| Which atlas cell is which eye | Unknown mapping of SettingIndexes → atlas rect | Diagnostic build: colour each iris differently and screenshot. Idle = the two big-iris cells; viewer-left eye = the cell at x 1437, right eye = x 763; open eyelids = cells at (1157,2646) and (875,3160) |
| Star mode recolours whole face | The game's Star effect cycles node colours | Expected behaviour, not a bug |

Technical facts the converter relies on:
- Perimeters are lists of vertex-index loops (outer + holes). Earcut handles holes.
  UV = position normalised to the bounds, with y flipped.
- `mCalculateNodeParameters` is empty, so vertex counts can change freely.
- Touch zones are data: `cPartsParamArray` (cPath, cHingedPos, cNodeMoveMax,
  CollisionSetting{Path, Expand, Push, Left/Right/Top/Bottom}).
- The colour-pattern table exists only for Yoshi.

| White strip inside an eye during event glances | Event glances UV-shift the eye sprite even with gaze max 0; shift samples a white seam left at the old sclera cell edge | `pika_atlas seam_fix`: darken thin white seams touching dark eye cells |
| Highlight slides to the eye edge and clips into a half-moon | Highlight was painted on the UV-shifted eye sprite | Paint it on the open-eyelid cells instead (`hl_lid`, `no_iris_hl`); the lid layer never shifts |
| Background shows as white wedges beside the eyes in the squish event | Head eye-holes deform wider than the eyeballs | Hole-free yellow backing drawn before the eye layers (reuse Cap_Back00) |
| Open mouths look human (teeth, lips) | Luigi mouths recoloured skin→yellow only | Restyle: inside → maroon, tongue pink-red, fill lip band; never add nodes, only recolour/regeometry existing ones |
| Stray red speck by the cheek | Hidden moustache parts left as tiny red triangles | Give them the cheek polygon |

## 4. Other images

- **Image models refuse branded characters at times**: the built-in tool blocked Pikachu twice
  ("safety rejection, category other"). OpenRouter → `google/gemini-3-pro-image` worked.
  *App:* use a provider path that allows user-supplied fan art, and show clear errors on refusal.
- Generated hands drifted (one merged two poses). **Recolouring the game's own white gloves**
  beat image generation: exact poses at zero cost. *App rule:* if an asset is a flat-colour
  silhouette, recolour it rather than generating it.
- Touch-guide outline/glow/silhouette are **derived from the figure in code** (outline = 12 px
  dilation ring at padding (35,54); glow = 18 px dilation + 16 px blur), so only the figure needs art.
- The touch-guide frame is tall (300×512), so wide poses come out small. *App:* ask for an upright pose.
- Web search for "good vector art" mostly found poor SVGs (glitter textures, cut files).
  The user's own reference + image generation was best for the face.
- Costs measured: Pro image $0.14, Flash $0.068, Flash-Lite $0.034 (Lite drifted badly).

## 4b. Items (Pokémon swap)

- Items are named textures (`FaceEvent*`, `FaceBtn*`), but **one item can have hidden extra sheets**: the flying Super Star is the 12-frame `StarList00` spin sheet. *App:* keep a per-game map of every texture an item uses (event sprite, frames, menu button, spin sheets).
- Generating with the original sprite as the reference keeps the pose, framing and line style. It still needed re-rolls: legs and a key on Voltorb, extra tentacles, a human hand for a paw, a background disc. *App:* show a before/after sheet and offer per-item re-roll.
- A spinning coin is better rendered procedurally (a Poké Ball turned on its axis) than generated frame by frame.
- Some items are tinted at runtime (egg colour, ink, star particles). Leave them alone or replace only the line layer.
- Menu items have meanings the art doesn't show: the note block is the background changer and the ? block is a random-event gift.

## 5. Audio

- Format: FMOD FSB5 inside the bundle's `.resource` stream, mostly Vorbis, but 6 clips are PCM16.
  **Writing a PCM16 FSB5 needs no encoder**: a 60-byte header + 36-byte sample header + raw PCM.
  FMOD decodes it sample-exact (checked through UnityPy/fmod_toolkit). Set the AudioClip's
  `m_CompressionFormat=0`, frequency, channels, bits=16, length, and `m_Resource` offset/size, then
  append to the `.resource` stream. 32 kHz mono keeps the size sane (+17 MB for 191 lines).
- Luigi has **191 voice lines over 65 triggers (about 306 s)**. The common SFX and the per-character
  music themes are separate and not yet replaced.
- **Sourcing is the main problem.** The Sounds Resource and the Fandom wikis now sit behind
  Cloudflare **interactive Turnstile**, which automation (even real Chrome + click) could not pass.
  The working path was YouTube rips (yt-dlp) of game voice compilations (SSBU, Let's Go Pikachu,
  Hey You Pikachu), split on silence. Anime clips often carry music or other voices.
- **Labelling without listening**: Gemini audio models via OpenRouter (`google/gemini-3.8-flash`)
  labelled 438 clips into categories with clean/pikachu flags for **$0.21**. The labels are
  plausible but unverified (a "yawn" video came back labelled happy/scared). *App:* let the user
  audition and swap.
- Gaps: no real snoring (synthesised from quiet sleepy clips + silence), few angry/hurt/dizzy/grab
  clips. Long "self" demo lines (3–5 s) are built by joining 2–3 clips. Loudness is matched to each
  original Luigi line.
- Copyright: the voice clips are Nintendo/TPC audio. That's fine for a personal mod; **a public web app
  can't host them**. It must let users bring their own audio or use TTS/voice-clone, and ship
  only the mapping logic.


**Music (BGM).** Clips are FSB5 Vorbis with a loop chunk (type 3: start, end samples). Each track = 4 synced stems that are **additive layers** (Main −29 dB, BigTouch −34, Touch −40, MiniTouch −49 rms), mixed in on touch. A web app must: detect a seamless loop in the user's track (chroma self-similarity + sample xcorr), write the loop chunk, and derive the 3 extra layers (band-filtered copies at those levels). Writing PCM instead of Vorbis is fine but grows the bundle ~10×.

## 6. Testing loop

- **Remote relaunch (no touch needed):** HOME → X (close) → A (confirm) → wait 3 s → A (launch). About 36 s later the caution screen needs A (detect it: grey banner pixels at (640,20)/(640,60) ≈ 228). Then a "Try pulling!" intro runs about 30 s and the idle face appears on its own. `gauntlet/deploy.sh <tag>` does build, upload, relaunch and capture in about 3 min.
- Automated eye metrics (`gauntlet/measure.py`, `metrics.py`, median over frames; squash frames filtered by aspect) plus a blind masked-eye A/B crop (`pair.py`) for a fresh critic agent. The critic's verdicts were noisy (it praised our own artefacts); the metrics were the dependable signal.

- Push to the console with sys-autopilot `PUT /files` and verify with `/files/hash`. A hash request can
  time out and come back empty, which reads as a false mismatch, so retry before trusting it.
- Changes load only on a **full game relaunch**.
- `GET /screenshot` gives about 7 fps (130 ms per frame). A systemd-run capture loop (`capture/cap.sh`) plus
  automatic frame triage (yellow coverage / background gaps) found the vanishing-head bug quickly.
  *App:* a hosted service can't do this, so give users a "report glitch + screenshot" flow.


- sys-autopilot is single-threaded: no screenshots while a swipe/hold runs, and virtual Capture-button video saved nothing. Visual bugs during drags need a human player while a screenshot loop runs (or post-release frames). Automatic detectors over ~9 fps capture loops (eye-edge white, mouth colours) catch event-only bugs.

## 7. Implications for the web app

1. **Don't distribute game files.** Ship per-game *recipes* (node maps, transforms, atlas rules,
   clip lists). Rebuild bundles on the user's side, or ask users to upload their own extracted
   bundles. Distribution rules: see wiki *game-mod-distribution-share-patches-not-game-files*.
2. Character template = Luigi skeleton (Mario is the same layout; Peach and Yoshi differ). Each new
   character still needs: head, ears/extra grab parts, eyes, nose, a mouth sheet, cheeks/colour, and hands.
3. Human-in-the-loop checkpoints: approve the face, mark ear/part split points, approve the mouth sheet,
   and audition the voice mapping.
4. Validation the app must run automatically: one geometry per node, Face01 present, vertex
   budget, eye-hole mapping, a render of every mouth/eye state, and decode of every audio clip.
