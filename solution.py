import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def safe_import(module_name, package_name=None):
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
    if input_type == "unknown" or not output_ext:
        return False
    supported_conversions = {
        "document": [".pdf", ".docx", ".doc", ".txt", ".md", ".epub", ".pptx", ".html", ".tex", ".xml", ".bib", ".json", ".rst", ".rtf", ".odt", ".org", ".ipynb", ".fb2", ".icml", ".opml", ".texi", ".textile", ".typ", ".muse", ".hs", ".1", ".adoc", ".dj", ".ms"],
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
    input_abs = Path(input_path).resolve()
    output_abs = Path(output_path).resolve()
    if not input_abs.exists():
        raise FileNotFoundError(f"Input file {input_abs} does not exist.")
    if output_abs.exists():
        response = input(f"Output file {output_abs} exists. Overwrite? (y/N): ")
        if response.lower() != "y":
            sys.exit("Operation cancelled.")
    output_abs.parent.mkdir(parents=True, exist_ok=True)
    return str(input_abs), str(output_abs)


def convert_media(input_path: str, output_path: str):
    ffmpeg_exe = safe_import("imageio_ffmpeg").get_ffmpeg_exe()
    output_ext = Path(output_path).suffix.lower()
    Path(output_path).unlink(missing_ok=True)
    if output_ext == ".gif":
        palette_path = Path(output_path).with_suffix(".palette.png")
        try:
            subprocess.run([ffmpeg_exe, "-y", "-i", input_path, "-vf", "fps=10,scale=480:-1:flags=lanczos,palettegen=stats_mode=diff", str(palette_path)], check=True)
            subprocess.run([ffmpeg_exe, "-y", "-i", input_path, "-i", str(palette_path), "-filter_complex", "[0:v]fps=10,scale=480:-1:flags=lanczos[s];[s][1:v]paletteuse=dither=bayer:bayer_scale=5", "-r", "10", output_path], check=True)
        finally:
            palette_path.unlink(missing_ok=True)
    elif output_ext in (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"):
        codec_map = {".mp3": ("libmp3lame", "192k"), ".m4a": ("aac", "192k"), ".aac": ("aac", "192k"), ".wav": ("pcm_s16le", None), ".ogg": ("libvorbis", "192k"), ".flac": ("flac", None)}
        codec, bitrate = codec_map.get(output_ext, ("aac", "192k"))
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-vn", "-c:a", codec]
        if bitrate:
            cmd += ["-b:a", bitrate]
        cmd.append(output_path)
        subprocess.run(cmd, check=True)
    else:
        format_codec_map = {
            ".webm": {"video_codec": "libvpx-vp9", "video_params": ["-crf", "30", "-b:v", "0", "-deadline", "realtime", "-cpu-used", "5"], "audio_codec": "libopus", "audio_params": ["-b:a", "128k"], "format_params": []},
            ".mp4": {"video_codec": "libx264", "video_params": ["-crf", "23", "-preset", "ultrafast"], "audio_codec": "aac", "audio_params": ["-b:a", "128k"], "format_params": ["-movflags", "+faststart"]},
            ".mkv": {"video_codec": "libx264", "video_params": ["-crf", "23", "-preset", "ultrafast"], "audio_codec": "aac", "audio_params": ["-b:a", "128k"], "format_params": []},
            ".avi": {"video_codec": "libx264", "video_params": ["-crf", "23", "-preset", "ultrafast"], "audio_codec": "aac", "audio_params": ["-b:a", "128k"], "format_params": []},
            ".mov": {"video_codec": "libx264", "video_params": ["-crf", "23", "-preset", "ultrafast"], "audio_codec": "aac", "audio_params": ["-b:a", "128k"], "format_params": ["-movflags", "+faststart"]},
            ".flv": {"video_codec": "libx264", "video_params": ["-crf", "23", "-preset", "ultrafast"], "audio_codec": "aac", "audio_params": ["-b:a", "128k"], "format_params": []},
        }
        config = format_codec_map.get(output_ext, format_codec_map[".mp4"])
        cmd = [ffmpeg_exe, "-y", "-i", input_path, "-c:v", config["video_codec"]]
        cmd.extend(config["video_params"])
        cmd.extend(config["format_params"])
        cmd.extend(["-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:a", config["audio_codec"]])
        cmd.extend(config["audio_params"])
        cmd.append(output_path)
        subprocess.run(cmd, check=True)


def batch_convert(input_dir, output_dir, input_ext, output_ext):
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory {input_path} does not exist.")
    if not input_path.is_dir():
        raise ValueError(f"Input path {input_path} is not a directory.")
    if not input_ext.startswith('.'):
        input_ext = '.' + input_ext
    if not output_ext.startswith('.'):
        output_ext = '.' + output_ext
    output_path.mkdir(parents=True, exist_ok=True)
    input_files = list(input_path.glob(f"*{input_ext}"))
    if not input_files:
        print(f"No files with extension {input_ext} found in {input_path}")
        return
    print(f"Found {len(input_files)} files with extension {input_ext}\nConverting from {input_path} to {output_path}\nConverting {input_ext} → {output_ext}")
    successful_conversions = 0
    failed_conversions = 0
    for input_file in input_files:
        try:
            output_filename = input_file.stem + output_ext
            output_file = output_path / output_filename
            print(f"Converting: {input_file.name} → {output_filename}")
            convert_file(str(input_file), str(output_file), preserve_original=True)
            successful_conversions += 1
        except Exception as e:
            print(f"✗ Failed to convert {input_file.name}: {e}")
            failed_conversions += 1
            continue
    print("-" * 50)
    print(f"Batch conversion completed:\n✓ Successful: {successful_conversions}\n✗ Failed: {failed_conversions}\n📁 Output directory: {output_path}")


def convert_file(input_path, output_path, preserve_original=False, password=None):
    start_time = time.time()
    temp_file_path = None
    try:
        input_abs, output_abs = validate_files(input_path, output_path)
        input_type = detect_file_type(input_abs)
        output_ext = Path(output_abs).suffix.lower()
        if input_type == "unknown":
            raise ValueError(f"Unsupported input file type: {input_abs}")
        if not is_conversion_supported(input_type, output_ext):
            raise ValueError(f"Cannot convert {input_type} to {output_ext}")
        print(f"Converting {input_abs} to {output_abs}")
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
                pypandoc.convert_text(content, to=output_ext.lstrip("."), outputfile=output_abs, format="markdown", extra_args=["--pdf-engine=xelatex"] if output_ext == ".pdf" else [])
            else:
                pypandoc.convert_file(work_path, to=output_ext.lstrip("."), outputfile=output_abs, format=Path(work_path).suffix.lstrip("."), extra_args=["--pdf-engine=xelatex"] if output_ext == ".pdf" else [])
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
        elif input_type in ("audio", "video"):
            convert_media(work_path, output_abs)
            print(f"{input_type.capitalize()} conversion successful: {output_abs}")
        elif input_type == "archive":
            patoolib = safe_import("patoolib")
            temp_extract_dir = tempfile.mkdtemp()
            try:
                patoolib.extract_archive(work_path, outdir=temp_extract_dir, verbosity=1 if password else 0, interactive=False)
                if password:
                    print(f"Extracting password-protected archive: {work_path}")
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
    parser = argparse.ArgumentParser(prog="swissknife", usage="swissknife [options]", description="A Swiss Army Knife of command-line tools. Use -h for help.", epilog=("Examples:\n  %(prog)s convert input.docx output.pdf\n  %(prog)s batch-convert ./docs ./output .docx .pdf\n"), formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="command", description="Available commands")
    convert_parser = subparsers.add_parser("convert", help="Convert files between formats")
    convert_parser.add_argument("input", help="Input file path")
    convert_parser.add_argument("output", help="Output file path")
    convert_parser.add_argument("--preserve-original", action="store_true", help="Preserve original file")
    convert_parser.add_argument("--password", help="Password for encrypted documents or password-protected archives")
    batch_parser = subparsers.add_parser("batch-convert", help="Batch convert files of one format from one directory to another directory of another format")
    batch_parser.add_argument("input_dir", help="Input directory path")
    batch_parser.add_argument("output_dir", help="Output directory path")
    batch_parser.add_argument("input_ext", help="Input file extension (e.g., .txt or txt)")
    batch_parser.add_argument("output_ext", help="Output file extension (e.g., .pdf or pdf)")
    return parser


def main():
    parser = setup_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()
    try:
        if args.command == "convert":
            convert_file(args.input, args.output, preserve_original=getattr(args, "preserve_original", False), password=getattr(args, "password", None))
        elif args.command == "batch-convert":
            batch_convert(args.input_dir, args.output_dir, args.input_ext, args.output_ext)
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
