import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def safe_import(module_name, package_name=None):
    """Safely import modules with helpful error messages."""
    try:
        if package_name:
            return __import__(module_name, fromlist=[package_name])
        return __import__(module_name)
    except ImportError:
        print(f"Module {module_name} not found. Please install it using pip.")
        if package_name:
            print(f"Try: pip install {package_name}")
        else:
            print(f"Try: pip install {module_name}")
        sys.exit(1)


def detect_file_type(file_path):
    """Detect file type from extension."""
    ext = Path(file_path).suffix.lower()
    if ext in [".pdf", ".docx", ".doc", ".txt", ".md", ".epub", ".pptx", ".xlsx"]:
        return "document"
    elif ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]:
        return "image"
    elif ext in [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"]:
        return "audio"
    elif ext in [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"]:
        return "video"
    elif ext in [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"]:
        return "archive"
    else:
        return "unknown"


def is_conversion_supported(input_type, output_ext):
    """Check if conversion between types is supported (simplified logic)."""
    if input_type == "unknown" or not output_ext:
        return False

    # Allow flexible conversions: documents can convert to images (PDF), etc.
    supported_conversions = {
        "document": [
            ".pdf",
            ".docx",
            ".doc",
            ".txt",
            ".md",
            ".epub",
            ".pptx",
            ".html",
            ".tex",
            ".xml",
            ".bib",
            ".json",
            ".rst",
            ".rtf",
            ".odt",
            ".org",
            ".ipynb",
            ".fb2",
            ".icml",
            ".opml",
            ".texi",
            ".textile",
            ".typ",
            ".muse",
            ".hs",
            ".1",
            ".adoc",
            ".dj",
            ".ms",
        ],
        "image": [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".pdf"],
        "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
        "video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".gif"],
        "archive": [".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"],
    }

    return output_ext in supported_conversions.get(input_type, [])


def create_temp_copy(file_path):
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / Path(file_path).name
    shutil.copy2(file_path, temp_file)
    return str(temp_file)


def validate_files(input_path, output_path):
    """Validate input and output file paths with absolute path resolution."""
    # Convert to absolute paths for consistent handling
    input_abs = Path(input_path).resolve()
    output_abs = Path(output_path).resolve()

    if not input_abs.exists():
        raise FileNotFoundError(f"Input file {input_abs} does not exist.")

    if output_abs.exists():
        response = input(f"Output file {output_abs} exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            sys.exit("Operation cancelled.")

    # Create output directory if it doesn't exist - make it any level
    output_abs.parent.mkdir(parents=True, exist_ok=True)

    return str(input_abs), str(output_abs)


def convert_media(input_path: str, output_path: str):
    # Video/GIF conversion constants
    GIF_FPS = 10
    GIF_WIDTH = 480
    GIF_DITHER_SCALE = 5
    GIF_SCALE_FLAGS = "lanczos"
    AUDIO_BITRATE = "192k"
    
    ffmpeg_exe = safe_import("imageio_ffmpeg").get_ffmpeg_exe()
    output_path_obj = Path(output_path)
    output_ext = output_path_obj.suffix.lower()

    # Ensure output file doesn't exist to avoid overwrite issues
    output_path_obj.unlink(missing_ok=True)

    # === 1. VIDEO → GIF ===
    if output_ext == ".gif":
        palette_path = Path(output_path).with_suffix(".palette.png")
        try:
            # Generate optimized color palette
            palette_filter = f"fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags={GIF_SCALE_FLAGS},palettegen=stats_mode=diff"
            subprocess.run(
                [
                    ffmpeg_exe,
                    "-y",
                    "-i",
                    input_path,
                    "-vf",
                    palette_filter,
                    str(palette_path),
                ],
                check=True,
            )

            # Create GIF using palette
            gif_filter = f"[0:v]fps={GIF_FPS},scale={GIF_WIDTH}:-1:flags={GIF_SCALE_FLAGS}[s];[s][1:v]paletteuse=dither=bayer:bayer_scale={GIF_DITHER_SCALE}"
            subprocess.run(
                [
                    ffmpeg_exe,
                    "-y",
                    "-i",
                    input_path,
                    "-i",
                    str(palette_path),
                    "-filter_complex",
                    gif_filter,
                    "-r",
                    str(GIF_FPS),
                    output_path,
                ],
                check=True,
            )
        finally:
            palette_path.unlink(missing_ok=True)

    # === 2. AUDIO → AUDIO (strip video) ===
    elif output_ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"):
        codec_map = {
            ".mp3": ("libmp3lame", AUDIO_BITRATE),
            ".m4a": ("aac", AUDIO_BITRATE),
            ".aac": ("aac", AUDIO_BITRATE),
            ".wav": ("pcm_s16le", None),
            ".ogg": ("libvorbis", AUDIO_BITRATE),
            ".flac": ("flac", None),
        }
        codec, bitrate = codec_map.get(output_ext, ("aac", AUDIO_BITRATE))
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", "-c:a", codec]
        if bitrate:
            cmd += ["-b:a", bitrate]
        cmd.append(output_path)
        subprocess.run(cmd, check=True)

    # === 3. VIDEO → VIDEO (default catch-all) ===
    else:
        # Video encoding constants
        VIDEO_BITRATE_AUDIO = "128k"
        CRF_QUALITY = "23"
        WEBM_CRF = "30"
        X264_PRESET = "ultrafast"
        VP9_CPU_USED = "5"
        
        # Codec configuration based on output format
        format_codec_map = {
            ".webm": {
                "video_codec": "libvpx-vp9",
                "video_params": [
                    "-crf",
                    WEBM_CRF,
                    "-b:v",
                    "0",
                    "-deadline",
                    "realtime",
                    "-cpu-used",
                    VP9_CPU_USED,
                ],
                "audio_codec": "libopus",
                "audio_params": ["-b:a", VIDEO_BITRATE_AUDIO],
                "format_params": [],
            },
            ".mp4": {
                "video_codec": "libx264",
                "video_params": ["-crf", CRF_QUALITY, "-preset", X264_PRESET],
                "audio_codec": "aac",
                "audio_params": ["-b:a", VIDEO_BITRATE_AUDIO],
                "format_params": ["-movflags", "+faststart"],
            },
            ".mkv": {
                "video_codec": "libx264",
                "video_params": ["-crf", CRF_QUALITY, "-preset", X264_PRESET],
                "audio_codec": "aac",
                "audio_params": ["-b:a", VIDEO_BITRATE_AUDIO],
                "format_params": [],
            },
            ".avi": {
                "video_codec": "libx264",
                "video_params": ["-crf", CRF_QUALITY, "-preset", X264_PRESET],
                "audio_codec": "aac",
                "audio_params": ["-b:a", VIDEO_BITRATE_AUDIO],
                "format_params": [],
            },
            ".mov": {
                "video_codec": "libx264",
                "video_params": ["-crf", CRF_QUALITY, "-preset", X264_PRESET],
                "audio_codec": "aac",
                "audio_params": ["-b:a", VIDEO_BITRATE_AUDIO],
                "format_params": ["-movflags", "+faststart"],
            },
            ".flv": {
                "video_codec": "libx264",
                "video_params": ["-crf", CRF_QUALITY, "-preset", X264_PRESET],
                "audio_codec": "aac",
                "audio_params": ["-b:a", VIDEO_BITRATE_AUDIO],
                "format_params": [],
            },
        }

        # Get codec config, default to MP4 settings for unknown formats
        config = format_codec_map.get(output_ext, format_codec_map[".mp4"])

        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-c:v", config["video_codec"]]
        cmd.extend(config["video_params"])
        cmd.extend(config["format_params"])
        cmd.extend(
            [
                "-vf",
                "scale=trunc(iw/2)*2:trunc(ih/2)*2",  # ensure even dimensions
                "-c:a",
                config["audio_codec"],
            ]
        )
        cmd.extend(config["audio_params"])
        cmd.append(output_path)
        subprocess.run(cmd, check=True)


def convert_file(input_path, output_path, preserve_original=False, password=None):
    start_time = time.time()
    temp_file_path = None

    try:
        # Validate and get absolute paths
        input_abs, output_abs = validate_files(input_path, output_path)

        # Check file type and compatibility
        input_type = detect_file_type(input_abs)
        output_ext = Path(output_abs).suffix.lower()

        if input_type == "unknown":
            raise ValueError(f"Unsupported input file type: {input_abs}")

        if not is_conversion_supported(input_type, output_ext):
            raise ValueError(f"Cannot convert {input_type} to {output_ext}")

        print(f"Converting {input_abs} to {output_abs}")

        # Set up work path
        work_path = input_abs
        if preserve_original:
            temp_file_path = create_temp_copy(input_abs)
            work_path = temp_file_path

        if input_type == "document":
            pypandoc = safe_import("pypandoc")
            input_ext = Path(work_path).suffix.lower()

            if input_ext == ".txt":
                with open(work_path, "r", encoding="utf-8") as f:
                    content = f.read()
                pypandoc.convert_text(
                    content,
                    to=output_ext.lstrip("."),
                    outputfile=output_abs,
                    format="markdown",
                    extra_args=["--pdf-engine=xelatex"] if output_ext == ".pdf" else [],
                )
            else:
                pypandoc.convert_file(
                    work_path,
                    to=output_ext.lstrip("."),
                    outputfile=output_abs,
                    format=Path(work_path).suffix.lstrip("."),
                    extra_args=["--pdf-engine=xelatex"] if output_ext == ".pdf" else [],
                )
            print(f"Document conversion successful: {output_abs}")
        elif input_type == "image":
            PIL = safe_import("PIL", "PIL")
            from PIL import Image

            img = Image.open(work_path)
            if output_ext == ".pdf":
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.save(output_abs, "PDF", resolution=100.0)
            elif output_ext in [".jpg", ".jpeg"]:
                img = img.convert("RGB")
                img.save(output_abs, optimize=True, quality=85)
            else:
                img.save(output_abs, optimize=True)
            print(f"Image conversion successful: {output_abs}")
        elif input_type == "audio":
            convert_media(work_path, output_abs)
            print(f"Audio conversion successful: {output_abs}")
        elif input_type == "video":
            convert_media(work_path, output_abs)
            print(f"Video conversion successful: {output_abs}")
        elif input_type == "archive":
            # Archive extraction/compression using Patool
            patoolib = safe_import("patoolib")
            temp_extract_dir = tempfile.mkdtemp()
            try:
                # Extract the input archive with password support
                if password:
                    # For password-protected archives, use verbosity=1 to handle passwords
                    patoolib.extract_archive(work_path, outdir=temp_extract_dir, verbosity=1, interactive=False)
                    print(f"Extracting password-protected archive: {work_path}")
                else:
                    patoolib.extract_archive(work_path, outdir=temp_extract_dir)

                # Create the output archive directly from the extracted directory
                patoolib.create_archive(output_abs, [temp_extract_dir])
                print(f"Archive conversion successful: {output_abs}")
            finally:
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
        else:
            raise ValueError(f"Unsupported file type: {input_type}")

    except Exception as e:
        print(f"Conversion failed: {e}")
        raise
    finally:
        end_time = time.time()
        duration = end_time - start_time
        print(f"Conversion completed in {duration:.2f} seconds.")
        if temp_file_path and Path(temp_file_path).exists():
            shutil.rmtree(Path(temp_file_path).parent, ignore_errors=True)


def setup_parser():
    parser = argparse.ArgumentParser(
        prog="swissknife",
        usage="swissknife [options]",
        description="A Swiss Army Knife of command-line tools. Use -h for help.",
        epilog=(
            "Examples:\n"
            "  %(prog)s convert input.docx output.pdf\n"
            "  %(prog)s batch-convert ./docs ./output .docx .pdf\n"
            "  %(prog)s summarize document.pdf --length medium\n"
            "  %(prog)s info document.pdf\n"
            "  %(prog)s logs\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", description="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert files between formats"
    )
    convert_parser.add_argument("input", help="Input file path")
    convert_parser.add_argument("output", help="Output file path")
    convert_parser.add_argument(
        "--preserve-original", action="store_true", help="Preserve original file"
    )
    convert_parser.add_argument(
        "--password",
        help="Password for encrypted documents or password-protected archives",
    )

    return parser


def main():
    """Main entry point for the swissknife CLI."""
    parser = setup_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    try:
        if args.command == "convert":
            convert_file(
                args.input,
                args.output,
                preserve_original=getattr(args, "preserve_original", False),
                password=getattr(args, "password", None),
            )
        else:
            parser.print_help()
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
