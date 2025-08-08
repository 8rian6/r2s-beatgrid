#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据 Rekordbox 导出的 XML（任意包含多条 <TRACK> 节点的文件）
生成 Serato BeatGrid，并把平均 BPM 写入 MP3 的 ID3v2 TBPM 帧。

使用流程建议：
1. 先把目标 MP3 批量导入 Serato，让 Serato 做一次“仅调号/波形分析”，
   这样文件会生成所有 Serato 专用 GEOB 帧（含初始 BeatGrid）。
2. 运行本脚本：它只会覆盖同名 GEOB("Serato BeatGrid") 并写入 TBPM，
   不会触碰 Markers2、Overview 等其它帧。

依赖：
    pip install serato-tools mutagen
"""

import os
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from statistics import mean

from serato_tools.track_beatgrid import TrackBeatgrid
from mutagen.id3 import ID3, TBPM

# ──────────────────────────────────────────────────────────────
# Rekordbox XML 解析辅助
# ──────────────────────────────────────────────────────────────

def parse_tempos_from_track_elem(track_elem):
    """提取 <TEMPO> 锚点。返回 [(time, bpm, beats_per_bar, beat_in_bar), ...]"""
    points = []
    for tp in track_elem.findall("TEMPO"):
        t = float(tp.get("Inizio", "0"))
        bpm = float(tp.get("Bpm", "0"))
        metro = tp.get("Metro", "4/4")
        beats_per_bar = int(metro.split("/")[0])
        battito = int(tp.get("Battito", "1"))
        points.append((t, bpm, beats_per_bar, battito))
    points.sort(key=lambda x: x[0])
    return points


def build_full_beats(points):
    """把锚点扩展成逐拍列表 [(time, beat_in_bar), ...]"""
    full_beats = []
    n = len(points)
    for i, (t, bpm, beats_per_bar, battito) in enumerate(points):
        full_beats.append((t, battito))
        if i < n - 1:
            next_t = points[i + 1][0]
            quarter = 60.0 / bpm
            curr_time, curr_beat = t, battito
            while True:
                cand_time = curr_time + quarter
                cand_beat = curr_beat + 1
                if cand_beat > beats_per_bar:
                    cand_beat = 1
                if cand_time < next_t - quarter / 2:
                    full_beats.append((cand_time, cand_beat))
                    curr_time, curr_beat = cand_time, cand_beat
                else:
                    break
    full_beats.sort(key=lambda x: x[0])
    return full_beats


def extract_downbeats(full_beats):
    """筛选出每小节第一拍 (beat==1)"""
    return [t for t, beat in full_beats if beat == 1]


def resolve_mp3_path(location_attr):
    if not location_attr:
        return None
    for prefix in ("file://localhost", "file://"):
        if location_attr.startswith(prefix):
            path = location_attr[len(prefix):]
            break
    else:
        path = location_attr
    return urllib.parse.unquote(path)


def process_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    results = []
    for track in root.findall(".//TRACK"):
        name = track.get("Name", "<unknown>")
        loc = track.get("Location") or track.findtext("LOCATION")
        mp3_path = resolve_mp3_path(loc)
        if not mp3_path:
            print(f"⚠️ [{name}] 未指定 Location，跳过")
            continue
        if not os.path.isfile(mp3_path):
            print(f"⚠️ 找不到文件: {mp3_path!r} （TRACK Name={name}）")
            continue
        points = parse_tempos_from_track_elem(track)
        if not points:
            print(f"⚠️ [{name}] 未找到任何 TEMPO 锚点，跳过")
            continue
        full_beats = build_full_beats(points)
        downbeats = extract_downbeats(full_beats)
        avg_bpm = mean([bpm for _, bpm, _, _ in points])
        results.append((mp3_path, downbeats, avg_bpm, name))
    return results

# ──────────────────────────────────────────────────────────────
# 写入 BeatGrid & BPM
# ──────────────────────────────────────────────────────────────

def write_tbpm(mp3_path: str, bpm: float):
    """把平均 BPM 写入 ID3v2 TBPM 帧（v2.3）。只覆盖 TBPM，不动其它帧"""
    try:
        id3 = ID3(mp3_path)
    except Exception:
        id3 = ID3()

    id3.delall("TBPM")
    # Serato 读文本 BPM 时接受整数或带小数，这里保留 2 位。
    bpm_text = f"{bpm:.2f}".rstrip("0").rstrip(".")
    id3.add(TBPM(encoding=0, text=bpm_text))  # encoding=0 → ISO-8859‑1 (v2.3 safe)
    id3.save(mp3_path, v2_version=3)


def write_serato_beatgrids(tracks_data):
    for mp3_path, downbeats, avg_bpm, name in tracks_data:
        if not downbeats:
            print(f"⚠️ [{name}] 没有提取到任何小节第一拍，已跳过")
            continue

        print(f"→ 处理: {name} ({mp3_path}) ，共 {len(downbeats)} 个小节")
        # ① 重写 BeatGrid
        tb = TrackBeatgrid(mp3_path)
        entries = []
        for t in downbeats[:-1]:
            entries.append(tb.NonTerminalBeatgridMarker(t, 4))  # 每小节 4 拍
        entries.append(tb.TerminalBeatgridMarker(downbeats[-1], avg_bpm))
        entries.append(tb.Footer(0))
        tb.entries = entries
        tb._dump()
        tb.save()  # 仅替换 "Serato BeatGrid" GEOB

        # ② 写入 TBPM (ID3 Text)
        write_tbpm(mp3_path, avg_bpm)
        print(f"✅ 已写入 BeatGrid & BPM={avg_bpm:.2f} 到 '{os.path.basename(mp3_path)}'")

# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 2:
        print(f"用法: {os.path.basename(sys.argv[0])} Rekordbox导出列表.xml")
        sys.exit(1)
    xml_path = sys.argv[1]
    if not os.path.isfile(xml_path):
        print(f"✖️ 未找到 XML 文件: {xml_path!r}")
        sys.exit(1)

    print(f"--> 读取 XML：{xml_path}")
    tracks = process_xml(xml_path)
    if not tracks:
        print("⚠️ 未处理到任何有效 TRACK。")
        sys.exit(0)
    write_serato_beatgrids(tracks)


if __name__ == "__main__":
    main()
