# Hello-Reskin

Put your own character into **Hello, Luigi!** on Nintendo Switch: face, eyes, mouths, voice, items, music and on-screen text.
You build the mod on your own computer from your own copy of the game, then load it with Atmosphère's LayeredFS.

The repo includes a full worked example, **Pikachu over Luigi**, as a recipe: every slot mapping, prompt, loop point and fix we needed.
It does **not** include any game files or finished Pikachu assets. You regenerate those yourself (see `recipes/pikachu/`).

> **Unofficial fan project.** Not affiliated with, endorsed by or connected to Nintendo, The Pokémon Company or Game Freak.
> No game files, keys, or copyrighted assets are included or will be accepted. You need your own legally owned copy of the
> game and your own console. Nothing here is for sale.

## What you can change

| Part | How | Notes |
|---|---|---|
| Face (head, ears, cheeks, nose, ~25 mouths) | Vector meshes rebuilt from one flat drawing | `tools/make_face.py`; the hardest part |
| Eyes (pupil, highlight, blink/sleepy lids) | Recoloured eye texture atlas | `tools/pika_atlas.py` + a params file |
| Items, enemies, hands, buttons, backgrounds | PNG replacements by texture name | `template/MANIFEST.csv` lists all 195 slots |
| Voice (191 lines) and sound effects | WAV replacements by clip name | `template/AUDIO_SLOTS.csv` lists all clips |
| Music (6 tracks × 4 layers, looping) | WAV + loop points | `audio/music/` finds seamless loops |
| On-screen text ("Luigi", enemy names) | Text map, all 12 languages | the game font has a limited character set |

## Quick start

1. Read **[docs/GUIDE.md](docs/GUIDE.md)**: dump the game and keys from your Switch, extract it, set up Python, export the slot templates.
2. Read **[docs/PAINPOINTS.md](docs/PAINPOINTS.md)**: everything that went wrong for us and how we fixed it.
3. Copy the recipe layout from **[recipes/pikachu/](recipes/pikachu/)** into `packs/<your-character>/` and replace the art and sounds.
4. Build: `python tools/build_mod.py packs/<your-character>`, then copy `build/<name>/atmosphere` to the root of your SD card.

## Requirements

- A Switch with custom firmware (Atmosphère) and your own copy of Hello, Luigi! (title ID `0100D8C0251AE000`, v0)
- Your own `prod.keys` / `title.keys` (Lockpick_RCM), and the game dumped with nxdumptool
- Linux or WSL, Python 3.12, ffmpeg, .NET 8 SDK (for the RomFS extractor), Il2CppDumper
- Optional: an OpenRouter API key for AI art and audio labelling, and yt-dlp for sourcing audio

## Layout

```
tools/          build + extraction scripts (build_mod, make_face, pika_atlas, fsb5, hx RomFS extractor, ...)
audio/          clip splitter, AI labeller, music loop finder/renderer
template/       slot lists only (texture names/sizes, audio clip names/lengths): no game data
recipes/pikachu worked example: mappings, prompts, loop points, sources, fix settings, scripts
docs/           GUIDE.md (step by step) and PAINPOINTS.md (lessons)
packs/          your packs go here (ignored by git)
```

## Sharing your character

Share your **pack sources** (your own art and sounds, plus the json files), never the built `atmosphere/` folder:
that folder contains modified copies of the game's files. Don't use other people's copyrighted art or audio in a public pack.

## License

Code: MIT (see `LICENSE`). Game names and characters belong to their owners.
