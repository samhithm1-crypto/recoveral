# RecoverAI 🔵 — AI-Powered Forensic Data Recovery

> **CalmStacks 24H Hackathon 2026** · MCE Hassan · ₹50,000 Prize Pool

---

## 🚀 Quick Start (Run in 60 seconds)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate demo corrupted files
python generate_demo.py

# 3. Start the backend
python app.py

# 4. Open browser
# → http://localhost:5000
```

---

## 🧠 Problem Statement

> Design and develop an AI-assisted data recovery solution that can **identify, reconstruct, classify, and prioritize** recoverable digital information from damaged, deleted, or partially corrupted storage data.

---

## ✅ Features Implemented

| Feature | Status |
|---------|--------|
| File signature detection (15+ types) | ✅ |
| Fragment reconstruction from raw binary | ✅ |
| AI integrity scoring (Shannon Entropy) | ✅ |
| Recovery priority ranking | ✅ |
| Fragment relationship analysis | ✅ |
| Interactive forensic dashboard | ✅ |
| Export forensic report (JSON) | ✅ |
| Demo mode (no file needed) | ✅ |

---

## 🏗️ Architecture

```
User uploads corrupted file / disk image
          ↓
    Flask Backend (app.py)
          ↓
    Analyzer Engine (analyzer.py)
    ├── Magic Byte Scanner     → Detects file types from raw bytes
    ├── Fragment Extractor     → Identifies embedded file fragments
    ├── Entropy Scorer         → Shannon entropy-based integrity score
    ├── Priority Ranker        → Ranks fragments by recovery value
    └── Relationship Mapper    → Links related fragments
          ↓
    REST API (/api/scan, /api/demo, /api/report)
          ↓
    React-like Dashboard (frontend/)
    ├── Recovery rate gauge
    ├── Fragment map table
    ├── Category breakdown
    ├── Relationship graph
    └── AI-generated summary
```

---

## 🛠️ Tech Stack

- **Backend:** Python 3.14, Flask, Flask-CORS
- **AI Engine:** Shannon Entropy Analysis, Magic Byte Heuristics
- **Frontend:** Vanilla HTML/CSS/JS (zero dependencies)
- **Fonts:** JetBrains Mono + Inter (Google Fonts)

---

## 📁 Project Structure

```
hack project/
├── app.py              ← Flask server + API endpoints
├── analyzer.py         ← Core AI recovery engine
├── generate_demo.py    ← Demo file generator
├── requirements.txt    ← Python dependencies
├── frontend/
│   ├── index.html      ← Dashboard UI
│   ├── style.css       ← Dark forensic theme
│   └── app.js          ← Frontend logic
└── demo_files/         ← Generated test files
```

---

## 🔬 How the AI Works

1. **Magic Byte Scanning** — Reads raw binary and detects file signatures (JPEG=`FFD8FF`, PDF=`%PDF`, etc.)
2. **Fragment Extraction** — Extracts up to 64KB chunks starting at each signature
3. **Entropy Analysis** — Calculates Shannon entropy per fragment. High entropy (>7.5) = encrypted/compressed. Low (<3) = plain text.
4. **Integrity Scoring** — Combines: size score + entropy fitness + null-byte corruption ratio → 0–100% score
5. **Priority Ranking** — Documents score higher than media, databases higher than archives
6. **Relationship Detection** — Groups fragments by category and offset proximity

---

## 👤 Team

Built solo at CalmStacks 24H Hackathon 2026 — MCE Hassan

---

*RecoverAI v1.0 · Built with ❤️ for Agamya Cyber Tech Challenge*
