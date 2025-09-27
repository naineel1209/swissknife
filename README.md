# 🛠️ Swissknife

A lightweight CLI toolkit (**exactly 250 lines of Python**) for universal file conversion and AI-powered summarization.

## ⚡ Features

### 🔄 Convert Files

- **Documents** → PDF, DOCX, DOC, TXT, MD, EPUB, PPTX and, many more
- **Images** → JPG, JPEG, PNG, WEBP, GIF, BMP, TIFF, PDF
- **Audio** → MP3, WAV, FLAC, AAC, OGG, M4A
- **Video** → MP4, AVI, MKV, MOV, WMV, FLV, WEBM, GIF
- **Archives** → ZIP, TAR, GZ, BZ2, 7Z, RAR

### 🤖 AI-Powered Summarization

- **Text Documents** → Extract and summarize content using BART
- **Audio/Video** → Transcribe with Whisper → Summarize text
- **Images** → Basic image information display
- **Configurable lengths** → Short, Medium, Long summaries

### 📊 Advanced Features

- **Batch Processing** → Convert entire directories
- **Operation Logging** → JSON-based history tracking
- **File Information** → Detailed metadata display
- **Temp File Cleanup** → Automatic cleanup of old temporary files
- **Format Validation** → Smart format compatibility checking

---

## 🔧 Installation

### Basic Installation

```bash
git clone https://github.com/yourname/swissknife.git
cd swissknife
uv sync
```

### LaTeX Installation (Required for PDF Conversion)

For document-to-PDF conversion, you need to install LaTeX:

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install -y texlive-latex-base texlive-latex-recommended texlive-fonts-recommended
```

**Minimal Installation (Faster):**

```bash
sudo apt install -y texlive-latex-base
```

**Alternative - TinyTeX (Lightweight):**

```bash
wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
```

**macOS:**

```bash
brew install --cask basictex
export PATH=/Library/TeX/texbin:$PATH
```

**Windows:**
Download and install MiKTeX from [miktex.org](https://miktex.org/)

---

## 🚀 Usage

### Single File Conversion

```bash
python main.py convert input.docx output.pdf
python main.py convert document.txt output.docx
python main.py convert image.png image.jpg
python main.py convert image.jpg output.pdf
python main.py convert audio.mp3 audio.wav
python main.py convert video.mp4 video.gif
python main.py convert archive.zip output.tar.gz
```

### Batch Conversion

```bash
python main.py batch-convert ./docs ./output .docx .pdf
python main.py batch-convert ./images ./converted .png .jpg
python main.py batch-convert ./audio ./output .mp3 .wav
```

### AI Summarization

```bash
python main.py summarize document.pdf --length medium
python main.py summarize lecture.mp4 --length long
python main.py summarize report.docx --length short
```

### File Information & Management

```bash
python main.py info document.pdf
python main.py logs
python main.py cleanup
python main.py version
```

---

## 🧩 CLI Commands

| Command         | Description               | Example                               |
| --------------- | ------------------------- | ------------------------------------- |
| `convert`       | Convert single files      | `convert input.docx output.pdf`       |
| `batch-convert` | Batch convert directories | `batch-convert ./docs ./out .md .pdf` |
| `summarize`     | AI-powered summarization  | `summarize file.pdf --length medium`  |
| `info`          | Display file metadata     | `info document.pdf`                   |
| `logs`          | Show operation history    | `logs`                                |
| `cleanup`       | Clean temporary files     | `cleanup`                             |
| `version`       | Show version info         | `version`                             |

---

## 📦 Dependencies

- **CLI Framework:** `argparse` (stdlib)
- **Document Processing:** `pypandoc-binary`, `python-docx`, `pdfplumber`
- **Image Processing:** `Pillow`
- **Audio Processing:** `pydub`
- **Video Processing:** `moviepy`, `ffmpeg-python`
- **AI/ML:** `transformers`, `torch`, `openai-whisper`
- **Utilities:** `hashlib`, `json`, `pathlib` (stdlib)

---

## 🎯 Project Specifications

- **Line Budget:** Exactly 250 executable lines of Python
- **Architecture:** Modular functions with clear separation of concerns
- **Error Handling:** Comprehensive validation and user-friendly messages
- **Logging:** JSON-based operation tracking
- **Compatibility:** Python 3.8+ with cross-platform support

---

## 📁 Project Structure

```
swissknife/
├── main.py            # Main CLI application (250 lines)
├── pyproject.toml     # Dependencies and project config
└── README.md          # Documentation
```
