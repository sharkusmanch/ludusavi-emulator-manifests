# ludusavi-emulator-manifests

Per-game [Ludusavi](https://github.com/mtkennerly/ludusavi) secondary manifests for emulator
saves. Each game gets its own backup history instead of one blob per emulator.

A scheduled workflow rebuilds `manifests/*.yaml` from public game databases.

| Manifest | Root to add (store: other) | Keyed by | Source |
|---|---|---|---|
| `retroarch.yaml` | folder containing `saves/` and `states/` | ROM file name | libretro-database No-Intro/Redump DATs + `aliases.json` |
| `pcsx2.yaml` | PCSX2 `memcards` folder (folder memory cards only) | disc serial | PCSX2 `GameIndex.yaml` |
| `ppsspp.yaml` | PPSSPP `PSP` folder | game ID | libretro-database PSP DATs |
| `dolphin.yaml` | Dolphin user folder (GCI folders, not raw cards) | game ID | GameTDB via Dolphin |
| `azahar.yaml` | Azahar/Citra user folder | title ID | hax0kartik/3dsdb |

## Use

Every path is relative to `<root>`, so the manifests work on any machine: add each emulator's
data folder as a root and list the manifests you want.

```yaml
manifest:
  secondary:
    - url: https://raw.githubusercontent.com/<owner>/ludusavi-emulator-manifests/main/manifests/retroarch.yaml
roots:
  - path: ~/.var/app/org.libretro.RetroArch/config/retroarch
    store: other
```

Run headless with stdin closed, or the CLI waits for game names on stdin:

```sh
ludusavi backup --force </dev/null
```

## RetroArch names

RetroArch saves are matched by ROM file name. A title matches `Title.*` and `Title (*` under
`saves/` and `states/`, at any depth. ROMs named differently from the databases (renames, hacks,
homebrew) go in `aliases.json`: map the file's title to the database title to merge them, or to
`null` for a standalone entry.

## Coverage check

Ludusavi skips files no entry claims. `tools/check_coverage.py` lists them:

```sh
ludusavi backup --preview --api </dev/null > preview.json
python tools/check_coverage.py preview.json <root> [<root> ...]
```

## Limits

- Glob matching is case-sensitive, and brace alternation is not supported by Ludusavi.
- Same-titled games on different RetroArch systems share one entry.
- Single-file memory cards (PCSX2 `.ps2`, Dolphin `.raw`) cannot be split per game.
