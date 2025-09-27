import argparse
import os
import sys
import shutil
import tempfile
import time
import threading
import psutil
import signal
from pathlib import Path
import subprocess


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


class MemoryMonitor:
    """Monitor memory usage during video processing."""

    def __init__(self, max_memory_gb=4.0):
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.monitoring = False
        self.process = psutil.Process()

    def start_monitoring(self):
        """Start monitoring memory usage."""
        self.monitoring = True

    def stop_monitoring(self):
        """Stop monitoring memory usage."""
        self.monitoring = False

    def check_memory(self):
        """Check current memory usage and raise exception if limit exceeded."""
        if not self.monitoring:
            return

        try:
            memory_info = self.process.memory_info()
            current_memory = memory_info.rss  # Resident Set Size

            if current_memory > self.max_memory_bytes:
                memory_gb = current_memory / (1024 * 1024 * 1024)
                max_gb = self.max_memory_bytes / (1024 * 1024 * 1024)
                raise MemoryError(
                    f"Memory limit exceeded: {memory_gb:.1f}GB > {max_gb:.1f}GB limit. "
                    "Consider using a smaller input file or increasing memory limit."
                )
        except psutil.NoSuchProcess:
            pass  # Process may have ended


class VideoProgressMonitor:
    """Monitor video conversion progress and provide feedback."""

    def __init__(self, duration, timeout_seconds=300):
        self.duration = duration
        self.timeout_seconds = timeout_seconds
        self.start_time = None
        self.last_progress = 0
        self.timed_out = False

    def start(self):
        """Start progress monitoring."""
        self.start_time = time.time()

        # Set up timeout handler
        def timeout_handler():
            time.sleep(self.timeout_seconds)
            if (
                self.start_time
                and (time.time() - self.start_time) > self.timeout_seconds
            ):
                self.timed_out = True
                print(
                    f"\n⚠️  Warning: Processing taking longer than {self.timeout_seconds}s"
                )

        timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
        timeout_thread.start()

    def update_progress(self, current_time):
        """Update progress based on current processing time."""
        if self.duration > 0:
            progress = min(100, (current_time / self.duration) * 100)
            if progress - self.last_progress >= 10:  # Update every 10%
                print(
                    f"Progress: {progress:.0f}% ({current_time:.1f}s/{self.duration:.1f}s)"
                )
                self.last_progress = progress

    def is_timed_out(self):
        """Check if processing has timed out."""
        return self.timed_out


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


def convert_video_pure(input_path: str, output_path: str):
    ffmpeg_exe = safe_import("imageio_ffmpeg").get_ffmpeg_exe()
    ext = output_path.rsplit(".", 1)[-1].lower()
    if ext == "gif":
        p = output_path.rsplit(".", 1)[0] + ".palette.png"
        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-i",
                input_path,
                "-vf",
                "fps=10,scale=320:-1:flags=lanczos,palettegen=stats_mode=diff",
                p,
            ],
            check=True,
        )
        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-i",
                input_path,
                "-i",
                p,
                "-filter_complex",
                "[0:v]fps=10,scale=320:-1:flags=lanczos[s];[s][1:v]paletteuse=dither=bayer:bayer_scale=5",
                "-r",
                "10",
                output_path,
            ],
            check=True,
        )
        Path(p).unlink(missing_ok=True)
    else:
        codec_args = {
            "mp4": [
                "-c:v",
                "libx264",
                "-crf",
                "28",
                "-preset",
                "ultrafast",
                "-c:a",
                "aac",
                "-b:a",
                "64k",
            ],
            "webm": [
                "-c:v",
                "libvpx-vp9",
                "-crf",
                "40",
                "-b:v",
                "0",
                "-c:a",
                "libopus",
                "-cpu-used",
                "4",
            ],
            "mkv": ["-c", "copy"],
        }.get(ext, ["-c", "copy"])
        subprocess.run(
            [
                ffmpeg_exe,
                "-y",
                "-i",
                input_path,
                *codec_args,
                "-vf",
                "scale=640:trunc(640*ih/iw/2)*2",
                "-r",
                "24",
                output_path,
            ],
            check=True,
        )


def convert_file(input_path, output_path, preserve_original=False, password=None):
    """Convert files between formats with proper error handling."""
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
                    format="plain",
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
            AudioSegment = safe_import("AudioSegment", "pydub")
            audio = AudioSegment.from_file(work_path)
            audio.export(output_abs, format=output_ext[1:])
            print(f"Audio conversion successful: {output_abs}")
        elif input_type == "video":
            convert_video_pure(work_path, output_abs)
            print(f"Video conversion successful: {output_abs}")
        elif input_type == "archive":
            # Archive extraction/compression using Patool
            patoolib = safe_import("patoolib")
            temp_extract_dir = tempfile.mkdtemp()
            try:
                # Extract the input archive
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
        help="Password for encrypted files (if applicable)",
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
