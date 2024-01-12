import argparse
import os
import subprocess

from filename_util import append_suffix_to_filename, update_extension


def video_to_audio(input: str, format: str):
    output_file = append_suffix_to_filename(input, "audio")
    output_file = update_extension(output_file, format)
    return subprocess.run(["ffmpeg", "-i", input, "-vn", output_file])


def extract_audio_for_dir(dir: str, video_format: str, audio_format: str):
    for filename in os.listdir(dir):
        file_path = os.path.join(dir, filename)

        if os.path.isfile(file_path) and video_format in filename:
            print(f"Extracting audio from {file_path}")
            video_to_audio(file_path, audio_format)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract audio from video files")

    parser.add_argument("folder", help="Path to the folder containing files.")
    parser.add_argument("video_ext",
                        help="Video file extension (e.g., '.mp4').")
    parser.add_argument("audio_ext",
                        help="Audio file extension (e.g., '.mp3').")
    args = parser.parse_args()

    extract_audio_for_dir(args.folder, args.video_ext, args.audio_ext)
