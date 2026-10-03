#!/usr/bin/env python3
"""Build per-game Ludusavi secondary manifests for emulator saves.

Every path is relative to <root>: add each emulator's data folder to Ludusavi as
an "other" root (see README). One output file per emulator in manifests/.
Standard library only.

A manifest that would shrink by more than 10% is not written (set FORCE=1 to
override), so a broken or unreachable source cannot wipe out a good file.
"""
import csv
import html
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache")
OUT = os.path.join(HERE, "manifests")
LIBRETRO = "https://raw.githubusercontent.com/libretro/libretro-database/master/metadat/"
UA = "Mozilla/5.0 (compatible; ludusavi-emulator-manifests; +https://github.com/sharkusmanch/ludusavi-emulator-manifests)"

SOURCES = {
    "ps2": "https://raw.githubusercontent.com/PCSX2/pcsx2/master/bin/resources/GameIndex.yaml",
    "tdb": "https://raw.githubusercontent.com/dolphin-emu/dolphin/master/Data/Sys/wiitdb-en.txt",
    "3ds_US": "https://raw.githubusercontent.com/hax0kartik/3dsdb/master/jsons/list_US.json",
    "3ds_GB": "https://raw.githubusercontent.com/hax0kartik/3dsdb/master/jsons/list_GB.json",
    "3ds_JP": "https://raw.githubusercontent.com/hax0kartik/3dsdb/master/jsons/list_JP.json",
    "ps1": "https://raw.githubusercontent.com/stenzek/duckstation/master/data/resources/gamedb.yaml",
    "ps1_sets": "https://raw.githubusercontent.com/stenzek/duckstation/master/data/resources/discsets.yaml",
    "ps3_api": "https://rpcs3.net/compatibility?api=v1&type=0&r=200&p={page}",
    "ps4": "https://raw.githubusercontent.com/andshrew/PlayStation-Titles/main/PS4_Titles.tsv",
    "vita": "https://api.vita3k.org/list/commercial",
    "switch_US": "https://raw.githubusercontent.com/blawar/titledb/master/US.en.json",
    "switch_GB": "https://raw.githubusercontent.com/blawar/titledb/master/GB.en.json",
    "wiiu": "https://wiiubrew.org/w/index.php?title=Title_database&action=raw",
    "x360_list": "https://raw.githubusercontent.com/IronRingX/xbox360-gamelist/main/xbox360_gamelist.csv",
    "x360_stable": "https://raw.githubusercontent.com/xenia-manager/database/main/data/game-compatibility/stable.json",
    "x360_canary": "https://raw.githubusercontent.com/xenia-manager/database/main/data/game-compatibility/canary.json",
    "scummvm": "https://raw.githubusercontent.com/scummvm/scummvm-web/master/data/en/games.yaml",
}
PSP_DATS = ["no-intro/Sony - PlayStation Portable.dat", "no-intro/Sony - PlayStation Portable (PSN).dat",
            "redump/Sony - PlayStation Portable.dat"]
# ROM-name databases for systems played through RetroArch cores.
RETROARCH_DATS = [
    "no-intro/Atari - 2600.dat", "no-intro/Atari - 7800.dat", "no-intro/Atari - Lynx.dat",
    "no-intro/Bandai - WonderSwan.dat", "no-intro/Bandai - WonderSwan Color.dat",
    "no-intro/NEC - PC Engine - TurboGrafx 16.dat", "no-intro/NEC - PC Engine SuperGrafx.dat",
    "no-intro/Nintendo - Family Computer Disk System.dat", "no-intro/Nintendo - Game Boy.dat",
    "no-intro/Nintendo - Game Boy Color.dat", "no-intro/Nintendo - Game Boy Advance.dat",
    "no-intro/Nintendo - Nintendo 64.dat", "no-intro/Nintendo - Nintendo DS.dat",
    "no-intro/Nintendo - Nintendo DSi.dat", "no-intro/Nintendo - Nintendo Entertainment System.dat",
    "no-intro/Nintendo - Pokemon Mini.dat", "no-intro/Nintendo - Super Nintendo Entertainment System.dat",
    "no-intro/Nintendo - Virtual Boy.dat", "no-intro/SNK - Neo Geo Pocket.dat",
    "no-intro/SNK - Neo Geo Pocket Color.dat", "no-intro/Sega - 32X.dat", "no-intro/Sega - Game Gear.dat",
    "no-intro/Sega - Master System - Mark III.dat", "no-intro/Sega - Mega Drive - Genesis.dat",
    "no-intro/Sega - SG-1000.dat", "no-intro/Sony - PlayStation Portable.dat",
    "redump/NEC - PC Engine CD - TurboGrafx-CD.dat", "redump/Sega - Dreamcast.dat",
    "redump/Sega - Mega-CD - Sega CD.dat", "redump/Sega - Saturn.dat", "redump/Sony - PlayStation.dat",
]
# ScummVM engines whose saves have one fixed name whatever the game was added as.
SCUMMVM_ENGINE_FIXED = {
    "sky": ("Beneath a Steel Sky", ["SKY-VM.*"]),
    "sword1": ("Broken Sword: The Shadow of the Templars", ["sword1.*"]),
    "queen": ("Flight of the Amazon Queen", ["queen.*"]),
    "dreamweb": ("DreamWeb", ["DREAMWEB.D*"]),
    "ngi": ("Full Pipe", ["fullpipe.*"]),
    "buried": ("The Journeyman Project 2: Buried in Time", ["buried.*", "buried-*.sav"]),
    "pegasus": ("The Journeyman Project: Pegasus Prime", ["pegasus-*.sav"]),
}
# ScummVM games ("engine:gameid") with fixed save names of their own.
SCUMMVM_GAME_FIXED = {
    "grim:grim": ["grim??.gsv"],
    "grim:monkey4": ["efmi???.gsv"],
    "myst3:myst3": ["*.m3s"],
}
# Extra save names some ScummVM games write besides the default ones.
SCUMMVM_GAME_EXTRA = {
    "zvision:znemesis": ["nemsav*.sav"],
    "zvision:zgi": ["inqsav*.sav"],
}


def fetch(key, url):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^A-Za-z0-9.]+", "_", key))
    if not os.path.exists(path):
        print(f"fetch {url}", file=sys.stderr)
        req = urllib.request.Request(urllib.parse.quote(url, safe=":/?&="), headers={"User-Agent": UA})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    body = r.read()
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(5 * (attempt + 1))
        with open(path + ".part", "wb") as f:
            f.write(body)
        os.replace(path + ".part", path)
    return open(path, encoding="utf-8", errors="replace").read()


def dat(rel):
    return fetch(rel, LIBRETRO + rel)


def dat_games(rel):
    """Yield (name, block) for each game in a clrmamepro DAT."""
    for block in dat(rel).split("\ngame (")[1:]:
        n = re.search(r'name "([^"]+)"', block)
        if n:
            yield n.group(1), block


def clean(name):
    """Tidy a database title into a display name."""
    name = html.unescape(re.sub(r"<br\s*/?>", " ", name))
    name = re.sub(r"[™®©]", "", name)
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", name)).strip()


def strip_tags(name):
    """'Game (USA) (Rev 1) [b]' -> 'Game'."""
    return re.sub(r"(\s*[(\[][^)\]]*[)\]])+\s*$", "", name).strip() or name


def glob_escape(s):
    return re.sub(r"([\[\]*?{}])", r"[\1]", s)


def group(names, suffix, paths):
    """Group IDs sharing a title into one game. names: id -> title; paths: id -> iterable of globs."""
    games = defaultdict(set)
    for ident, name in names.items():
        games[f"{clean(name) or ident} ({suffix})"].update(paths(ident))
    return games


def write(emulator, games, header):
    path = os.path.join(OUT, f"{emulator}.yaml")
    if os.path.exists(path) and not os.environ.get("FORCE"):
        old = sum(1 for line in open(path, encoding="utf-8") if line.startswith('"'))
        if len(games) < 0.9 * old:
            raise RuntimeError(f"{emulator}: {len(games)} games, was {old}; refusing to overwrite (FORCE=1 to override)")
    with open(path + ".part", "w", encoding="utf-8") as f:
        f.write(f"# Generated by generate.py - do not edit. {header}\n---\n")
        for name in sorted(games):
            f.write(f"{json.dumps(name, ensure_ascii=False)}:\n  files:\n")
            for p in sorted(games[name]):
                f.write(f"    {json.dumps(p, ensure_ascii=False)}:\n      tags:\n        - save\n")
    os.replace(path + ".part", path)
    print(f"{emulator}: {len(games)} games, {sum(map(len, games.values()))} paths", file=sys.stderr)


def pcsx2():
    """Root = PCSX2 memcards folder holding a *folder* memory card."""
    serial = None
    names = {}
    for line in fetch("ps2", SOURCES["ps2"]).splitlines():
        if line[:1] not in ("", " ", "#"):  # any top-level key starts a new entry
            m = re.match(r"^([A-Z]{4}-\d{5}):", line)
            serial = m.group(1) if m else None
            continue
        m = re.match(r'^  (name|name-en): "(.*)"\s*(?:#.*)?$', line)
        if m and serial and (m.group(1) == "name-en" or serial not in names):
            names[serial] = m.group(2).replace('\\"', '"')
    games = group(names, "PS2", lambda s: [f"<root>/*/B?{s}*"])
    games["PCSX2 (system)"].update({"<root>/*/BADATA-SYSTEM", "<root>/*/_pcsx2_superblock"})
    write("pcsx2", games, "Source: PCSX2 GameIndex.yaml")


def dolphin():
    """Root = Dolphin user folder (contains GC/, Wii/, StateSaves/). GCI-folder cards only."""
    games = defaultdict(set)
    entries = []
    for line in fetch("tdb", SOURCES["tdb"]).splitlines():
        m = re.match(r"^([A-Z0-9]{4})([A-Z0-9]{2})? = (.+)$", line)
        if m and not line.startswith("TITLES"):
            entries.append((m.group(1), m.group(2), clean(m.group(3))))
    # Wii saves are keyed by the 4-character code alone, which hacks and mods share with the
    # original game: give the folder to one owner, preferring Nintendo's own release (maker 01).
    wii_owner = {}
    for code, maker, name in sorted(entries, key=lambda e: e[1] != "01"):
        if maker is None:  # WiiWare / Virtual Console
            key = f"{name} (Wii)"
            games[key].add(f"<root>/Wii/title/00010001/{code.encode().hex()}")
            continue
        key = f"{name} ({'GameCube' if code[0] in 'GD' else 'Wii'})"
        games[key].add(f"<root>/StateSaves/{code}{maker}.*")
        if code[0] in "GDP":
            games[key].add(f"<root>/GC/*/*/{maker}-{code}-*.gci")
        if code[0] not in "GD" and wii_owner.setdefault(code, key) == key:
            games[key].add(f"<root>/Wii/title/00010000/{code.encode().hex()}")
    games["Dolphin (system)"].update({"<root>/GC/SRAM.raw", "<root>/Wii/shared2/sys/SYSCONF", "<root>/Wii/fst.bin"})
    write("dolphin", games, "Source: GameTDB via Dolphin wiitdb-en.txt")


def azahar():
    """Root = Azahar/Citra user folder (contains sdmc/, nand/)."""
    names = {}
    for region in ("US", "GB", "JP"):
        for x in json.loads(fetch(f"3ds_{region}", SOURCES[f"3ds_{region}"])):
            tid = x.get("TitleID", "").lower()
            if tid.startswith("00040000"):
                names.setdefault(tid[8:], x.get("Name", ""))
    games = group(names, "3DS", lambda low: [
        f"<root>/sdmc/Nintendo 3DS/*/*/title/00040000/{low}",
        f"<root>/sdmc/Nintendo 3DS/*/*/extdata/00000000/{int(low, 16) >> 8:08X}"])
    games["Azahar (system)"].update({"<root>/nand", "<root>/sysdata"})
    write("azahar", games, "Source: hax0kartik/3dsdb")


def ppsspp():
    """Root = PPSSPP's PSP folder (contains SAVEDATA/, PPSSPP_STATE/)."""
    names = {}
    for rel in PSP_DATS:
        for name, block in dat_games(rel):
            for a, b in set(re.findall(r'serial "[^"]*?([A-Z]{4})-?(\d{5})', block)):
                names.setdefault(a + b, strip_tags(name))
    games = group(names, "PSP", lambda s: [f"<root>/SAVEDATA/{s}*", f"<root>/PPSSPP_STATE/{s}_*"])
    write("ppsspp", games, "Source: libretro-database PSP DATs")


def retroarch(aliases):
    """Root = RetroArch config folder (contains saves/, states/), sorted by core or not."""
    titles = set()
    for rel in RETROARCH_DATS:
        for name, _block in dat_games(rel):
            title = strip_tags(name)
            if len(title) >= 2:
                titles.add(title)
    # "Donkey.*" would also claim saves of a game titled "Donkey.GG": skip the dotted pattern there.
    dotted = {t[:i] for t in titles for i, c in enumerate(t) if c == "."}
    games = defaultdict(set)

    def add(key, stem):
        s = glob_escape(stem)
        for kind in ("saves", "states"):
            if stem not in dotted:
                games[key].add(f"<root>/{kind}/**/{s}.*")
            games[key].add(f"<root>/{kind}/**/{s} (*")

    for title in titles:
        add(f"{clean(title)} (RetroArch)", title)
    # aliases: file-name title -> canonical title (merge) or null (standalone entry)
    for stem, target in aliases.items():
        add(f"{clean(target or stem)} (RetroArch)", stem)
    write("retroarch", games, "Source: libretro-database No-Intro/Redump DATs + aliases.json")


def duckstation():
    """Root = DuckStation data folder (contains memcards/, savestates/), or the memcards or
    savestates folder itself when only that is synced. Per-game card modes only."""
    games = defaultdict(set)

    def card(title):
        # DuckStation replaces characters the host OS forbids with "_"; which ones depends on
        # the OS (as does a trailing "."), so match any single character in their place.
        t = re.sub(r'[\\/<>:"|?*]', "?", re.sub(r"([\[\]{}])", r"[\1]", title))
        return t[:-1] + "?" if t.endswith(".") else t

    def unquote(s):
        return s.replace('\\"', '"')

    sets = {}  # serial -> (set name, set save title)
    for block in re.split(r"\n(?=- name:)", fetch("ps1_sets", SOURCES["ps1_sets"])):
        name = re.search(r'^- name: "(.*)"\s*(?:#.*)?$', block, re.M)
        save = re.search(r'^  saveName: "(.*)"\s*(?:#.*)?$', block, re.M)
        if name:
            n = unquote(name.group(1))
            for serial in re.findall(r"^    - (\S+)\s*(?:#.*)?$", block, re.M):
                sets[serial] = (n, unquote(save.group(1)) if save else n)
    for block in re.split(r"\n(?=\S[^\n]*:\s*\n)", fetch("ps1", SOURCES["ps1"])):
        m = re.match(r"([A-Za-z0-9]+-[A-Za-z0-9]+):", block)
        name = re.search(r'^  name: "(.*)"\s*(?:#.*)?$', block, re.M)
        if not m or not name:
            continue
        serial, n = m.group(1), unquote(name.group(1))
        save = re.search(r'^  saveName: "(.*)"\s*(?:#.*)?$', block, re.M)
        titles = {unquote(save.group(1)) if save else n}
        if serial in sets:
            n = sets[serial][0]
            titles.add(sets[serial][1])
        else:
            n = re.sub(r"\s*\(Disc \d+\)$", "", n)
        key = f"{clean(n)} (PS1)"
        for sub in ("memcards/", ""):
            for t in titles:
                games[key].add(f"<root>/{sub}{card(t)}_?.mcd")
            games[key].add(f"<root>/{sub}{serial}_?.mcd")
        for sub in ("savestates/", ""):
            games[key].add(f"<root>/{sub}{serial}_*.sav")
    for sub in ("memcards/", ""):
        games["DuckStation (system)"].add(f"<root>/{sub}shared_card_?.mcd")
    for sub in ("savestates/", ""):
        games["DuckStation (system)"].update({f"<root>/{sub}savestate_*.sav", f"<root>/{sub}resume.sav"})
    write("duckstation", games, "Source: DuckStation gamedb.yaml + discsets.yaml")


def rpcs3():
    """Root = RPCS3 config folder (contains dev_hdd0/)."""
    names = {}
    try:
        first = None
        for page in range(1, 60):
            data = json.loads(fetch(f"ps3_api_{page}", SOURCES["ps3_api"].format(page=page)))["results"]
            if not data or next(iter(data)) == first:  # past the last page it wraps to page 1
                break
            first = first or next(iter(data))
            for serial, v in data.items():
                if v.get("title"):
                    names[serial] = v["title"]
    except Exception as e:  # courtesy endpoint: Redump alone still covers disc games
        print(f"rpcs3 API unavailable ({e}); using Redump only", file=sys.stderr)
    for name, block in dat_games("redump/Sony - PlayStation 3.dat"):
        for a, b in set(re.findall(r'serial "([A-Z]{4})-?(\d{5})', block)):
            names.setdefault(a + b, strip_tags(name))
    games = group(names, "PS3", lambda s: [f"<root>/dev_hdd0/home/*/savedata/{s}*", f"<root>/savestates/{s}",
                                           f"<root>/dev_hdd0/savedata/vmc/{s}_mc?.VM1"])
    write("rpcs3", games, "Source: RPCS3 compatibility API + libretro-database Redump PS3 DAT")


def shadps4():
    """Root = shadPS4 user folder. Covers the v0.16+ layout (home/<user>/savedata) and the older one."""
    names = {}
    rows = csv.reader(io.StringIO(fetch("ps4", SOURCES["ps4"])), delimiter="\t")
    head = next(rows)
    tid, name = head.index("titleId"), head.index("name")
    for cols in rows:
        m = re.match(r"^([A-Z]{4}\d{5})", cols[tid]) if len(cols) > max(tid, name) else None
        if m and cols[name].strip():
            names.setdefault(m.group(1), cols[name])
    games = group(names, "PS4", lambda s: [f"<root>/home/*/savedata/{s}", f"<root>/savedata/*/{s}"])
    write("shadps4", games, "Source: andshrew/PlayStation-Titles")


def vita3k():
    """Root = Vita3K pref-path (contains ux0/)."""
    names = {x["titleId"]: x["name"] for x in json.loads(fetch("vita", SOURCES["vita"]))["list"]
             if x.get("titleId") and x.get("name")}
    for name, block in dat_games("no-intro/Sony - PlayStation Vita.dat"):
        for a, b in set(re.findall(r'serial "([A-Z]{4})-?(\d{5})', block)):
            names.setdefault(a + b, strip_tags(name))
    games = group(names, "Vita", lambda t: [f"<root>/ux0/user/*/savedata/{t}"])
    write("vita3k", games, "Source: Vita3K compatibility list + libretro-database Vita DAT")


def switch():
    """Root = user folder of a yuzu-family emulator (Eden, Citron, Suyu, yuzu...; contains nand/)."""
    names = {}
    for region in ("US", "GB"):
        for v in json.loads(fetch(f"switch_{region}", SOURCES[f"switch_{region}"])).values():
            tid = (v.get("id") or "").upper()
            if re.fullmatch(r"[0-9A-F]{13}000", tid) and v.get("name"):  # base applications only
                names.setdefault(tid, v["name"])
    games = group(names, "Switch", lambda t: [f"<root>/nand/user/save/0000000000000000/*/{t}",
                                              f"<root>/nand/user/save/cache/{t}"])
    games["Switch emulator (system)"].add("<root>/nand/system/save/8000000000000010")
    write("switch", games, "Source: blawar/titledb. For yuzu-family emulators, not Ryujinx.")


def ryujinx():
    """Root = Ryujinx data folder. Saves sit in numbered folders, so they cannot be split per game."""
    games = {"Ryujinx (all saves)": {"<root>/bis/user/save", "<root>/bis/user/saveMeta", "<root>/bis/system/save",
                                     "<root>/system/Profiles.json"}}
    write("ryujinx", games, "Static: Ryujinx save folders carry no title ID.")


def cemu():
    """Root = Cemu's mlc01 folder."""
    text = fetch("wiiu", SOURCES["wiiu"])
    start = text.index("== 00050000: Game Application Titles ==")
    section = text[start:text.index("\n==", start + 10)]

    def tidy(name):
        name = clean(re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", name))
        # "Japanese name (English name)": prefer the trailing bracketed Latin name
        if name.endswith(")") and not name.isascii():
            depth = 0
            for i in range(len(name) - 1, -1, -1):
                depth += (name[i] == ")") - (name[i] == "(")
                if depth == 0:
                    inner = name[i + 1:-1].strip()
                    if inner.isascii() and len(inner) >= 2 and not name[:i].isascii():
                        name = inner
                    break
        return name

    def junk(name):  # placeholder and test rows on the wiki
        return len(name) < 3 or name in ("TODO", "???") or name.startswith("'") or "(getOsVersion.rpx)" in name

    names = {}
    for tid, raw in re.findall(r"^\| 00050000-([0-9A-Fa-f]{8})\s*\n\| ?(.*)$", section, re.M):
        tid, name = tid.lower(), tidy(raw)
        if tid not in names or (junk(names[tid]) and not junk(name)):
            names[tid] = name
    games = group({t: ("" if junk(n) else n) for t, n in names.items()}, "Wii U",
                  lambda t: [f"<root>/usr/save/00050000/{t}"])
    games["Cemu (system)"].add("<root>/usr/save/system/act")
    write("cemu", games, "Source: WiiUBrew title database")


def xenia():
    """Root = Xenia content folder. Covers master (<id>/...) and Canary (<xuid>/<id>/...)."""
    names = {}
    for key in ("x360_stable", "x360_canary"):
        for x in json.loads(fetch(key, SOURCES[key])):
            if re.fullmatch(r"[0-9A-Fa-f]{8}", x.get("id") or "") and x.get("title"):
                names.setdefault(x["id"].upper(), x["title"])
    rows = csv.reader(io.StringIO(fetch("x360_list", SOURCES["x360_list"]).lstrip("﻿")))
    head = next(rows)
    tid, name = head.index("Title ID"), head.index("Game Name")
    for cols in rows:
        if len(cols) > max(tid, name) and re.fullmatch(r"[0-9A-Fa-f]{8}", cols[tid]) and cols[name].strip():
            names.setdefault(cols[tid].upper(), cols[name])
    games = group(names, "Xbox 360", lambda t: [f"<root>/{t}/00000001", f"<root>/{t}/profile",
                                                f"<root>/*/{t}/00000001", f"<root>/*/{t}/Headers/00000001"])
    games["Xenia (profiles)"].add("<root>/*/FFFE07D1")
    write("xenia", games, "Source: xenia-manager/database + IronRingX/xbox360-gamelist")


def scummvm():
    """Root = ScummVM save folder. Matches default target names (game ID plus variant suffix)."""
    entries = {}  # game id -> (full id, name); games sharing a game ID share save names
    for block in re.split(r"\n-\s*\n", "\n" + fetch("scummvm", SOURCES["scummvm"])):
        full = re.search(r"^\s+id: '?([^:'\n]+:[^'\n]+)'?\s*$", block, re.M)
        name = re.search(r"^\s+name: (.*)$", block, re.M)
        if not full or not name:
            continue
        n = name.group(1).strip()
        n = n[1:-1].replace("''", "'") if n[:1] == "'" else n[1:-1] if n[:1] == '"' else n
        entries.setdefault(full.group(1).split(":", 1)[1], (full.group(1), n))
    games = defaultdict(set)
    for name, patterns in SCUMMVM_ENGINE_FIXED.values():
        games[f"{name} (ScummVM)"].update(f"<root>/{p}" for p in patterns)
    for gid, (full, name) in entries.items():
        if full.split(":")[0] in SCUMMVM_ENGINE_FIXED:
            continue
        patterns = SCUMMVM_GAME_FIXED.get(full)
        if patterns is None:
            patterns = [f"{glob_escape(gid)}.*"] + SCUMMVM_GAME_EXTRA.get(full, [])
            # "sci-*.*" would also claim saves of the game "sci-fanmade": leave the variant pattern out
            if not any(other.startswith(gid + "-") for other in entries):
                patterns.append(f"{glob_escape(gid)}-*.*")
        games[f"{clean(name)} (ScummVM)"].update(f"<root>/{p}" for p in patterns)
    write("scummvm", games, "Source: scummvm-web games.yaml")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    aliases = json.load(open(os.path.join(HERE, "aliases.json"), encoding="utf-8"))
    builders = [pcsx2, dolphin, azahar, ppsspp, lambda: retroarch(aliases.get("retroarch", {})), duckstation,
                rpcs3, shadps4, vita3k, switch, ryujinx, cemu, xenia, scummvm]
    failed = 0
    for build in builders:
        try:
            build()
        except Exception as e:  # keep the other manifests; the previous file for this one stays in place
            failed += 1
            print(f"ERROR {getattr(build, '__name__', 'retroarch')}: {e}", file=sys.stderr)
    sys.exit(1 if failed else 0)
