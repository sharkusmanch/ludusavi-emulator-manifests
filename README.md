# ludusavi-emulator-manifests

Per-game [Ludusavi](https://github.com/mtkennerly/ludusavi) secondary manifests for emulator
saves. Each emulated game gets its own backup history and can be restored on its own, instead of
one blob per emulator.

A scheduled GitHub Actions workflow rebuilds `manifests/*.yaml` from public game databases.

| Manifest | System | Root to add (store: other) | Keyed by | Source |
|---|---|---|---|---|
| `retroarch.yaml` | many | folder containing `saves/` and `states/` | ROM file name | libretro-database No-Intro/Redump DATs + `aliases.json` |
| `duckstation.yaml` | PS1 | DuckStation data folder (`memcards/`, `savestates/`), or either of those folders on its own | card title and disc serial | DuckStation `gamedb.yaml` + `discsets.yaml` |
| `pcsx2.yaml` | PS2 | PCSX2 `memcards` folder (folder memory cards only) | disc serial | PCSX2 `GameIndex.yaml` |
| `rpcs3.yaml` | PS3 | RPCS3 config folder (contains `dev_hdd0/`) | serial | RPCS3 compatibility API + Redump PS3 DAT |
| `shadps4.yaml` | PS4 | shadPS4 user folder | serial | andshrew/PlayStation-Titles |
| `ppsspp.yaml` | PSP | PPSSPP `PSP` folder | game ID | libretro-database PSP DATs |
| `vita3k.yaml` | PS Vita | Vita3K data folder (contains `ux0/`) | title ID | Vita3K compatibility list + No-Intro Vita DAT |
| `dolphin.yaml` | GameCube, Wii | Dolphin user folder (GCI folders, not raw cards) | game ID | GameTDB via Dolphin |
| `cemu.yaml` | Wii U | Cemu `mlc01` folder | title ID | WiiUBrew title database |
| `azahar.yaml` | 3DS | Azahar/Citra user folder | title ID | hax0kartik/3dsdb |
| `switch.yaml` | Switch | user folder of Eden, Citron, Suyu or yuzu (contains `nand/`) | title ID | blawar/titledb |
| `ryujinx.yaml` | Switch | Ryujinx data folder (contains `bis/`) | not per game - one entry | static |
| `xenia.yaml` | Xbox 360 | Xenia `content` folder (master or Canary) | title ID | xenia-manager/database + IronRingX/xbox360-gamelist |
| `scummvm.yaml` | ScummVM | ScummVM save folder | game ID | scummvm-web `games.yaml` |

**Tested against real saves:** RetroArch, PCSX2, PPSSPP, Dolphin (GameCube) and Azahar. The other
manifests were built from each emulator's source code and checked only against synthetic folder
layouts - please report mismatches.

### Default folder locations

| Emulator | Linux | Windows |
|---|---|---|
| DuckStation | `~/.local/share/duckstation` | `Documents\DuckStation`, else `%LOCALAPPDATA%\DuckStation` |
| RPCS3 | `~/.config/rpcs3` | folder containing `rpcs3.exe` |
| shadPS4 | `~/.local/share/shadPS4` | `%APPDATA%\shadPS4` |
| Vita3K | `~/.local/share/Vita3K/Vita3K` | `%APPDATA%\Vita3K\Vita3K` |
| Eden / Citron / Suyu / yuzu | `~/.local/share/<name>` | `%APPDATA%\<name>` |
| Ryujinx | `~/.config/Ryujinx` | `%APPDATA%\Ryujinx` |
| Cemu | `~/.local/share/Cemu/mlc01` | `%APPDATA%\Cemu\mlc01` |
| Xenia | `~/.local/share/Xenia/content` | `content` next to the exe (Canary), `Documents\Xenia\content` (master) |

Portable installs, Flatpaks and custom paths differ: point the root at wherever the folders named
in the first table actually are.

## Use

Every path is relative to `<root>`, so the same manifests work on any machine and any install
method: add each emulator's data folder as an "other" root and list the manifests you want.

```yaml
manifest:
  secondary:
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/retroarch.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/duckstation.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/pcsx2.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/rpcs3.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/shadps4.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/ppsspp.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/vita3k.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/dolphin.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/cemu.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/azahar.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/switch.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/ryujinx.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/xenia.yaml
    - url: https://raw.githubusercontent.com/sharkusmanch/ludusavi-emulator-manifests/main/manifests/scummvm.yaml
roots:
  # Typical Linux locations - point each at your own folder. One root per emulator, in any order.
  - path: ~/.var/app/org.libretro.RetroArch/config/retroarch  # RetroArch (Flatpak)
    store: other
  - path: ~/.local/share/duckstation  # DuckStation
    store: other
  - path: ~/.config/PCSX2/memcards  # PCSX2 (folder memory cards)
    store: other
  - path: ~/.config/rpcs3  # RPCS3
    store: other
  - path: ~/.local/share/shadPS4  # shadPS4
    store: other
  - path: ~/.var/app/org.ppsspp.PPSSPP/config/ppsspp/PSP  # PPSSPP (Flatpak)
    store: other
  - path: ~/.local/share/Vita3K/Vita3K  # Vita3K
    store: other
  - path: ~/.var/app/org.DolphinEmu.dolphin-emu/data/dolphin-emu  # Dolphin (Flatpak)
    store: other
  - path: ~/.local/share/Cemu/mlc01  # Cemu
    store: other
  - path: ~/.local/share/azahar-emu  # Azahar
    store: other
  - path: ~/.local/share/eden  # Eden (or citron, suyu, yuzu)
    store: other
  - path: ~/.config/Ryujinx  # Ryujinx
    store: other
  - path: ~/.local/share/Xenia/content  # Xenia
    store: other
  - path: ~/.local/share/scummvm/saves  # ScummVM
    store: other
```

List only the emulators you use: drop the manifest and root lines for the rest. The paths above are
common defaults, not guarantees - Flatpak, EmuDeck, portable and Windows installs keep these folders
elsewhere (see the table above), and what matters is that the root contains the folders named in the
first table.

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

- **DuckStation** - per-game memory cards named by title (`<root>/memcards/<title>_?.mcd`, using
  the database's `saveName`) or by serial, plus `<root>/savestates/<serial>_*.sav`. Multi-disc
  games are one entry.
- **PCSX2** - each serial in `GameIndex.yaml` becomes `<root>/*/B?<serial>*`, matching that game's
  save folders inside any folder memory card.
- **RPCS3** - `<root>/dev_hdd0/home/*/savedata/<serial>*`, save states and PS1-classic cards. Save
  folder names are chosen by each game; nearly all start with the serial, but not all.
- **shadPS4** - `<root>/home/*/savedata/<serial>` (v0.16+) and `<root>/savedata/*/<serial>` (older).
- **PPSSPP** - each serial becomes `<root>/SAVEDATA/<id>*` and `<root>/PPSSPP_STATE/<id>_*`.
- **Vita3K** - `<root>/ux0/user/*/savedata/<title id>`.
- **Dolphin** - each GameTDB ID becomes a GCI glob (`<root>/GC/*/*/<maker>-<code>-*.gci`), a Wii
  title folder (`<root>/Wii/title/00010000/<hex id>`) and its save states.
- **Cemu** - `<root>/usr/save/00050000/<title id low half>`. Titles the wiki has no name for are
  listed by ID.
- **Azahar** - each title ID becomes its `title/00040000/<id>` and matching `extdata` folder under
  `<root>/sdmc/Nintendo 3DS/*/*/`.
- **Switch (yuzu family)** - `<root>/nand/user/save/0000000000000000/*/<title id>` and the cache
  save folder.
- **Ryujinx** - saves live in numbered folders with no title ID in the path, so this is a single
  "all saves" entry.
- **Xenia** - `<root>/<title id>/00000001` (master) and `<root>/*/<title id>/00000001` (Canary).
  DLC and title updates are left out.
- **ScummVM** - `<root>/<game id>.*` and `<root>/<game id>-*.*`, which is how ScummVM names saves
  for a game added with its default name; games whose engine uses fixed save names are listed
  explicitly. Renamed targets are not matched.
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
- A manifest is not regenerated if a source is unreachable or the result would shrink by more
  than 10%; the previous file stays in place and the workflow run fails.
- Ludusavi stores backups by absolute path; restoring on another machine needs
  [redirects](https://github.com/mtkennerly/ludusavi/blob/master/docs/help/redirects.md).

## Data sources

Not affiliated with Ludusavi or any of these projects.

- [libretro-database](https://github.com/libretro/libretro-database) (No-Intro and Redump DATs)
- [PCSX2](https://github.com/PCSX2/pcsx2) `GameIndex.yaml`
- [GameTDB](https://www.gametdb.com) via [Dolphin](https://github.com/dolphin-emu/dolphin)
- [hax0kartik/3dsdb](https://github.com/hax0kartik/3dsdb)
- [DuckStation](https://github.com/stenzek/duckstation) `gamedb.yaml`
- [RPCS3](https://rpcs3.net/compatibility) compatibility list
- [andshrew/PlayStation-Titles](https://github.com/andshrew/PlayStation-Titles)
- [Vita3K](https://vita3k.org/compatibility) compatibility list
- [blawar/titledb](https://github.com/blawar/titledb)
- [WiiUBrew](https://wiiubrew.org/wiki/Title_database) title database
- [xenia-manager/database](https://github.com/xenia-manager/database) and [IronRingX/xbox360-gamelist](https://github.com/IronRingX/xbox360-gamelist)
- [scummvm-web](https://github.com/scummvm/scummvm-web)
