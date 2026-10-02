# ludusavi-emulator-manifests

Per-game [Ludusavi](https://github.com/mtkennerly/ludusavi) secondary manifests for emulator
saves. Each emulated game gets its own backup history and can be restored on its own, instead of
one blob per emulator.

A scheduled GitHub Actions workflow rebuilds `manifests/*.yaml` from public game databases.

| Manifest | Root to add (store: other) | Keyed by | Games | Source |
|---|---|---|---|---|
| `retroarch.yaml` | folder containing `saves/` and `states/` | ROM file name | ~32,000 | libretro-database No-Intro/Redump DATs + `aliases.json` |
| `pcsx2.yaml` | PCSX2 `memcards` folder (folder memory cards only) | disc serial | ~9,000 | PCSX2 `GameIndex.yaml` |
| `ppsspp.yaml` | PPSSPP `PSP` folder | game ID | ~3,100 | libretro-database PSP DATs |
| `dolphin.yaml` | Dolphin user folder (GCI folders, not raw cards) | game ID | ~4,500 | GameTDB via Dolphin |
| `azahar.yaml` | Azahar/Citra user folder | title ID | ~3,100 | hax0kartik/3dsdb |

## Use

Every path is relative to `<root>`, so the same manifests work on any machine and any install
method: add each emulator's data folder as an "other" root and list the manifests you want.

```yaml
manifest:
  secondary:
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/retroarch.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/pcsx2.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/ppsspp.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/dolphin.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/azahar.yaml
roots:
  # Example paths for Flatpak / EmuDeck installs on Linux - point these at your own folders.
  - path: ~/.var/app/org.libretro.RetroArch/config/retroarch
    store: other
  - path: ~/Emulation/saves/pcsx2/saves
    store: other
  - path: ~/.var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP
    store: other
  - path: ~/.var/app/org.DolphinEmu.dolphin-emu/data/dolphin-emu
    store: other
  - path: ~/Emulation/storage/azahar
    store: other
```

In the GUI these are the "other" screen: add each URL under manifests and each folder under roots.

Run headless with stdin closed, or the CLI waits for game names on stdin:

```sh
ludusavi backup --force </dev/null
```

Games show up with a platform suffix, such as `Tales of the Abyss (PS2)` or
`Pokemon - FireRed Version (RetroArch)`, so they never merge with a PC game of the same name in
Ludusavi's primary manifest.

## How each manifest is generated

`generate.py` (Python standard library only) downloads each source, groups IDs by game title and
writes one entry per title. Regional releases of a game share one entry.

- **PCSX2** - each serial in `GameIndex.yaml` becomes `<root>/*/B?<serial>*`, matching that game's
  save folders inside any folder memory card.
- **PPSSPP** - each serial becomes `<root>/SAVEDATA/<id>*` and `<root>/PPSSPP_STATE/<id>_*`.
- **Dolphin** - each GameTDB ID becomes a GCI glob (`<root>/GC/*/*/<maker>-<code>-*.gci`), a Wii
  title folder (`<root>/Wii/title/00010000/<hex id>`) and its save states.
- **Azahar** - each title ID becomes its `title/00040000/<id>` and matching `extdata` folder under
  `<root>/sdmc/Nintendo 3DS/*/*/`.
- **RetroArch** - see below.

Each emulator also gets a `(system)` entry for shared files that belong to no single game.

### RetroArch

RetroArch names a save after the ROM file, and nothing inside the save identifies the game, so
this manifest matches on names:

1. Take every ROM name from the No-Intro and Redump DATs for the systems listed in `generate.py`.
2. Strip trailing tags: `Pokemon - FireRed Version (USA, Europe) (Rev 1)` becomes
   `Pokemon - FireRed Version`.
3. Write one entry per title with four patterns: `Title.*` and `Title (*`, under both `saves/`
   and `states/`, at any depth (so per-core subfolders are optional).

Those two shapes keep similar titles apart: `Final Fantasy VII (*` cannot match
`Final Fantasy VIII (USA)`.

ROMs named differently from the databases (renames, hacks, homebrew) match nothing until they are
listed in `aliases.json`. Map the file's title to the database title to merge it into that entry,
or to `null` for a standalone entry:

```json
{
  "retroarch": {
    "Pokémon Emerald Version": "Pokemon - Emerald Version",
    "Celeste Classic": null
  }
}
```

## Coverage check

Ludusavi silently skips files that no entry claims. `tools/check_coverage.py` lists them, along
with any file claimed by more than one game:

```sh
ludusavi backup --preview --api </dev/null > preview.json
python tools/check_coverage.py preview.json <root> [<root> ...]
```

## Limits

- Glob matching is case-sensitive, and Ludusavi does not support brace alternation.
- Same-titled games on different RetroArch systems share one entry, and so do saves for one game
  made by different cores.
- Single-file memory cards (PCSX2 `.ps2`, Dolphin `.raw`) cannot be split per game.
- Wii entries are generated but untested.
- Ludusavi stores backups by absolute path; restoring on another machine needs
  [redirects](https://github.com/mtkennerly/ludusavi/blob/master/docs/help/redirects.md).

## Data sources

Not affiliated with Ludusavi or any of these projects.

- [libretro-database](https://github.com/libretro/libretro-database) (No-Intro and Redump DATs)
- [PCSX2](https://github.com/PCSX2/pcsx2) `GameIndex.yaml`
- [GameTDB](https://www.gametdb.com) via [Dolphin](https://github.com/dolphin-emu/dolphin)
- [hax0kartik/3dsdb](https://github.com/hax0kartik/3dsdb)
