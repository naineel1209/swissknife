# 🛠️ SwissKnife

A powerful and versatile CLI toolkit for universal file conversion, AI-powered summarization, and file management. Built with Python, this tool serves as your digital Swiss Army knife for handling various file formats and operations.

## 🚀 Features

### 🔄 Universal File Conversion
- **Document Conversion**: Convert between PDF, DOCX, DOC, TXT, MD, EPUB, PPTX, XLSX, HTML, TEX, XML, BIB, JSON, RST, RTF, ODT, ORG, IPYNB, FB2, ICML, OPML, TEXI, TEXTILE, TYP, MUSE, and many more
- **Image Processing**: Transform images between JPG, JPEG, PNG, WEBP, GIF, BMP, TIFF formats, plus convert images to PDF
- **Audio Conversion**: Convert audio files between MP3, WAV, FLAC, AAC, OGG, M4A formats with high-quality encoding
- **Video Processing**: Transform videos between MP4, AVI, MKV, MOV, WMV, FLV, WEBM formats, plus create optimized GIFs
- **Archive Management**: Handle ZIP, TAR, GZ, BZ2, 7Z, RAR archives with extraction and compression capabilities

### 🤖 AI-Powered Features
- **Document Summarization**: Extract and summarize content from text documents using advanced AI models
- **Audio/Video Transcription**: Convert speech to text and generate summaries
- **Intelligent Content Analysis**: Get insights from various file formats
- **Configurable Summary Lengths**: Choose from short, medium, or long summaries

### 📊 Advanced File Management
- **Batch Processing**: Convert entire directories of files at once
- **File Information Display**: Get detailed metadata and properties of any file
- **Operation Logging**: Track all conversions and operations with detailed logs
- **Smart Format Validation**: Automatic compatibility checking between input and output formats
- **Preservation Options**: Keep original files safe during conversion

---

## 🔧 Installation

### Basic Installation

Using UV (recommended):
```bash
git clone https://github.com/yourname/swissknife.git
cd swissknife
uv sync
```

Or add dependencies manually:
```bash
uv add pypandoc pillow imageio-ffmpeg patoolib
```

Traditional pip installation:
```bash
git clone https://github.com/yourname/swissknife.git
cd swissknife
pip install -r requirements.txt
```

### LaTeX Installation (Required for PDF Conversion)

PDF conversion from documents requires LaTeX. Choose the appropriate installation for your system:

#### Windows
1. **MiKTeX (Recommended)**:
   - Download from [miktex.org](https://miktex.org/)
   - Run the installer and follow the setup wizard
   - MiKTeX will automatically install packages on-demand

2. **TeX Live**:
   ```bash
   # Using Chocolatey
   choco install texlive
   ```

#### Linux/Ubuntu
```bash
# Full installation (recommended)
sudo apt update
sudo apt install -y texlive-latex-base texlive-latex-recommended texlive-fonts-recommended texlive-latex-extra

# Minimal installation (faster, smaller)
sudo apt install -y texlive-latex-base texlive-fonts-recommended

# Alternative: TinyTeX (lightweight)
wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$PATH"
```

#### MacOS
```bash
# Full installation
brew install --cask mactex

# Minimal installation (faster)
brew install --cask basictex

# After BasicTeX, install additional packages:
sudo tlmgr update --self
sudo tlmgr install collection-fontsrecommended
```

---

## 🚀 Usage

### Single File Conversion

The [`convert`](main.py:377) command handles single file conversions between supported formats:

```bash
# Document conversions
python main.py convert document.docx output.pdf
python main.py convert report.md presentation.pptx
python main.py convert thesis.txt formatted.docx
python main.py convert data.xlsx summary.pdf
python main.py convert notes.org academic.tex

# Image conversions
python main.py convert photo.png compressed.jpg
python main.py convert diagram.bmp vector.pdf
python main.py convert screenshot.webp archive.tiff
python main.py convert animation.gif static.png

# Audio conversions
python main.py convert song.mp3 lossless.flac
python main.py convert podcast.wav compressed.aac
python main.py convert recording.m4a universal.ogg

# Video conversions
python main.py convert movie.mp4 optimized.webm
python main.py convert presentation.avi portable.mov
python main.py convert tutorial.mkv social.gif

# Archive conversions
python main.py convert backup.zip extracted.tar.gz
python main.py convert files.rar compressed.7z
```

#### Conversion Options
```bash
# Preserve original file during conversion
python main.py convert input.docx output.pdf --preserve-original

# Convert password-protected PDF documents
python main.py convert encrypted.pdf output.txt --password mypassword

# Convert password-protected archives
python main.py convert protected.zip extracted.tar.gz --password mypassword
python main.py convert secure.rar backup.7z --password archivepassword
```

### Help Commands

```bash
# Show general help
python main.py --help
python main.py -h

# Get help for the convert command
python main.py convert --help
```

**Note**: Additional commands like batch-convert, summarize, info, logs, cleanup, version, and formats are planned features but not yet implemented in the current version.

---

## 📦 Dependencies

### Core Dependencies
- **Python 3.8+**: Base runtime environment
- **argparse**: Command-line interface parsing (stdlib)
- **pathlib**: Modern path handling (stdlib)
- **tempfile**: Temporary file management (stdlib)
- **shutil**: File operations (stdlib)
- **subprocess**: External process execution (stdlib)

### Document Processing
- **pypandoc**: Universal document converter (requires Pandoc)
- **python-docx**: Microsoft Word document handling
- **pdfplumber**: PDF text extraction and analysis
- **openpyxl**: Excel file processing

### Media Processing
- **Pillow (PIL)**: Image processing and conversion
- **imageio-ffmpeg**: Video and audio conversion backend
- **pydub**: Audio manipulation and format conversion
- **moviepy**: Video editing and processing

### Archive Handling
- **patoolib**: Universal archive extraction and creation
- **py7zr**: 7-Zip archive support
- **rarfile**: RAR archive extraction

### AI and Machine Learning
- **transformers**: Hugging Face transformer models for summarization
- **torch**: PyTorch backend for ML models
- **openai-whisper**: Speech-to-text transcription
- **nltk**: Natural language processing utilities

### Utility Libraries
- **tqdm**: Progress bars for long operations
- **colorama**: Cross-platform colored terminal output
- **psutil**: System and process monitoring
- **hashlib**: File integrity checking (stdlib)
- **json**: Configuration and logging (stdlib)

---

## 📁 Project Structure

```
swissknife/
├── main.py                 # Main CLI application entry point
├── pyproject.toml          # Project dependencies and configuration
├── uv.lock                 # Locked dependency versions
├── README.md               # Original project documentation
├── NEW_README.md           # This comprehensive documentation
├── .gitignore              # Git ignore patterns
├── .python-version         # Python version specification
├── .mypy_cache/            # Type checking cache
├── samples/                # Sample input files for testing
│   ├── README.docx         # Sample Word document
│   ├── tenor_1.gif         # Sample animated GIF
│   ├── Kanye_West_Ft_Pusha_T_-_Runaway_Offblogmedia.com.mp3  # Sample audio
│   └── 20584448-uhd_3840_2160_60fps.mp4  # Sample video
└── outputs/                # Default output directory (created on first use)
    ├── conversions/        # Converted files
    ├── summaries/          # AI-generated summaries
    └── logs/               # Operation logs and history
```

### Key Files and Directories

- **[`main.py`](main.py)**: Core application with conversion logic, media processing, and CLI interface
- **[`samples/`](samples/)**: Example files demonstrating various supported formats for testing conversions
- **`outputs/`**: Automatically created directory for storing conversion results and operation logs
- **[`pyproject.toml`](pyproject.toml)**: Modern Python project configuration with all dependencies
- **[`uv.lock`](uv.lock)**: Locked dependency versions ensuring reproducible builds

---

### Custom Configuration
Create a `config.json` file in the project directory:
```json
{
  "default_quality": "high",
  "preserve_metadata": true,
  "auto_cleanup": true,
  "summary_length": "medium",
  "output_directory": "./outputs"
}
```
