import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta

from openai import OpenAI

from combine_text_vtt import combine_files_to_text, combine_vtt_files
from extract_audio_with_target_speaker import extract_audio_from_sample
from filename_util import append_suffix_to_filename, update_extension

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)
SPEAKER = "speaker"


def file_duration(input):
    duration = subprocess.run(
        f"ffmpeg -i {input} 2>&1 | grep Duration | awk '{{print $2}}'",
        shell=True,
        stdout=subprocess.PIPE,
        text=True).stdout[:-2]
    return duration.split(".")[0]


def cut_audio(input: str, start: str, end: str, max_segment_seconds: int):
    print(f"Cutting audio file {input} ({start}, {end})")

    start_time = datetime.strptime(start, '%H:%M:%S')
    end_time = datetime.strptime(end, '%H:%M:%S')
    idx = 0
    outputs = []
    while start_time < end_time:
        seg_end_time = min(end_time,
                           start_time + timedelta(seconds=max_segment_seconds))
        output_file = append_suffix_to_filename(
            input,
            f"{datetime.strftime(start_time, '%H_%M_%S')}_{datetime.strftime(seg_end_time, '%H_%M_%S')}"
        )
        if os.path.exists(output_file):
            print(f"{output_file} already exists, skipping")
        else:
            start_time_str = datetime.strftime(start_time, '%H:%M:%S')
            seg_end_time_str = datetime.strftime(seg_end_time, '%H:%M:%S')
            print(
                f"Cutting audio file ({start_time_str}, {seg_end_time_str}) to {output_file}"
            )
            subprocess.run([
                "ffmpeg", "-i", input, "-ss", start_time_str, "-to",
                seg_end_time_str, "-c", "copy", output_file
            ],
                           capture_output=True,
                           text=True,
                           check=True)
        outputs.append((output_file, start_time, seg_end_time))
        start_time += timedelta(minutes=10)
        idx += 1

    return outputs


def transcribe_with_whisper(file,
                            response_format="vtt",
                            language=None,
                            prompt=None):
    print(f"Transcribing {file}")
    audio_file = open(file, "rb")
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language=language,
        response_format=response_format,
        prompt=prompt
        # Tip: use "以下，是普通话的句子。" to enforce Simplified Chinese. See https://github.com/openai/whisper/discussions/277
    )
    return transcript


def transcribe_audio_with_target_speaker(input, sample, response_format,
                                         language, prompt):
    print(f"Processing input {input}")
    speaker_audio_file = append_suffix_to_filename(input, SPEAKER)
    extract_audio_from_sample(input, sample, speaker_audio_file)
    duration = file_duration(speaker_audio_file)
    segments = cut_audio(
        speaker_audio_file,
        "00:00:00",
        duration,
        60 * 10,
    )

    outputs = []
    for audio_segment_tuple in segments:
        audio_segment = audio_segment_tuple[0]
        output_file = update_extension(audio_segment, response_format)
        if os.path.exists(output_file):
            print(
                f"Transcription for {audio_segment} already exists, skipping")
        else:
            output = transcribe_with_whisper(audio_segment, response_format,
                                             language, prompt)
            with open(output_file, "w") as file:
                file.write(output)
        outputs.append(
            (output_file, audio_segment_tuple[1], audio_segment_tuple[2]))
    return outputs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Transcribe certain speaker's audio from source video")

    parser.add_argument(
        "input",
        help="Input video file. Multiple files are separated by comma.")
    parser.add_argument("sample", help="Sample audio file.")
    parser.add_argument(
        "response_format",
        help="Response format supported by Whipser API (e.g. json, text, vtt).",
        default="vtt")
    parser.add_argument("--language", help="Language of the input audio file.")
    parser.add_argument("--prompt", help="Prompt for Whisper model.")
    args = parser.parse_args()

    for input in args.input.split(","):
        outputs = transcribe_audio_with_target_speaker(input, args.sample,
                                                       args.response_format,
                                                       args.language,
                                                       args.prompt)

        # Output combined text file
        speaker_output_txt_file = update_extension(
            append_suffix_to_filename(input, SPEAKER), "txt")
        combine_files_to_text([output[0] for output in outputs],
                              speaker_output_txt_file)
        if args.response_format == "vtt":
            # Output combined vtt file
            speaker_output_vtt_file = update_extension(
                append_suffix_to_filename(input, SPEAKER), "vtt")
            combine_vtt_files(outputs, speaker_output_vtt_file)
