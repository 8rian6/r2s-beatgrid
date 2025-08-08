
[简体中文](README_zh.md) | English

# r2s‑beatgrid (MP3 Only)

**Python script that writes beat information from Rekordbox XML into Serato BeatGrid**

Serato and Rekordbox share the DJ‑software market.  
Serato is favoured by DJs who perform with turntables and “battle”‑style controllers, especially in styles that emphasise groove and live expression—Hip‑Hop, Funk, R&B, Reggae, etc.  
But precisely those classic genres (old‑school Hip‑Hop, Funk, Soul, Blues, classic Rock…) often feature natural tempo drift, and **Serato’s native BeatGrid does not support variable tempo**.  
DJs therefore spend a lot of time manually fixing grids.

Rekordbox, on the other hand, excels at variable‑tempo analysis: its Dynamic BeatGrid reliably locks to tempo changes with little or no tweaking.  
With **this script (`r2s.py`)** you can automatically convert Rekordbox’s per‑track beat anchors and write them back into the corresponding **MP3** files, so Serato can read the same high‑precision variable grid.

> Commercial tools already exist, but they are complex, require access to all of your DJ databases, and often need an Internet connection—plus a monthly fee of ~ USD 7.  
> This script is free, offline, and open source.

> ⚠️ **MP3 ONLY.** Grids for WAV / AIFF / FLAC / ALAC stay in `_Serato_/Database V2`; the script will not touch them.  
> 🔄 **BACK UP all MP3s before you start!**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎯 Accurate grids | Writes Rekordbox’s down‑beats as Serato red‑line BeatGrid |
| 🔄 Batch support | Works on XML files containing many `<TRACK>` entries |
| 🛡️ Offline & safe | Edits only MP3 tags—never touches the Serato database |

---

## 🖥️ Requirements

| Component | Version / note |
|-----------|----------------|
| OS | Windows 10+, macOS 10.15+, or Linux |
| Python | 3.7 or newer |
| Dependencies | `serato-tools`, `mutagen` |

---

## 🚀 Quick‑start guide

### 0 · Back‑up

> **Strongly recommended:** copy all MP3s you intend to process to a safe place.

### 1 · Rekordbox — analyse & export XML

1. **Preferences ▸ Analysis**  
   - Mode **Dynamic BeatGrid**  
   - Tick **High‑Resolution BeatGrid** if available.  
2. Drag the target MP3s into your Rekordbox collection.  
3. Select them ▸ right‑click **Analyse Track** (or use the top‑bar Analyse button).  
4. When analysis is finished, choose **File ▸ Export Collection in XML Format…**  
   - Tick **BeatGrid / Tempo information**.  
   - Save as `rekordbox_export.xml`.

### 2 · Serato — write “initialisation” tags

1. Launch Serato ▸ in the left panel press **+** to create a new Crate, e.g. `GridPrep`.  
2. Drag the same MP3s into this crate.  
3. Click **Analyse Files** and **tick only** **Key** & **Waveform** — **untick Beatgrid**.  
4. Wait until analysis finishes; Serato now writes gain, overview, etc. (the *initialisation* tags) into every MP3.

### 3 · Install the script & dependencies

```bash
git clone https://github.com/<your‑username>/r2s-beatgrid.git
cd r2s-beatgrid

# optional virtual‑env
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# install dependencies
pip install -r requirements.txt
```

`requirements.txt` contains:
```
serato-tools>=0.4.0
mutagen>=1.47
```

### 4 · Run the script

```bash
python r2s.py /full/path/to/rekordbox_export.xml
```

Example output:
```
--> Reading XML: /Users/me/exports/rb.xml
→  Processing: Superstition (Superstition.mp3) , 112 bars
✅  BeatGrid & BPM=99.99 written to 'Superstition.mp3'
```

### 5 · Verify in Serato

Reload the processed tracks (remove then drag in again).  
You should see red grid lines at every bar‑one, and BPM changes follow the Rekordbox grid.

---

Happy mixing! 🎧
