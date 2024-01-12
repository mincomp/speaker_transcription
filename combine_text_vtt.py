import os
import re
import sys
from datetime import datetime

import opencc

from filename_util import append_suffix_to_filename


def combine_files_to_text_for_dir(input_folder, output_file_path):
    combine_files_to_text(sorted(os.listdir(input_folder)), output_file_path)


def combine_files_to_text(input_files, output_file_path):
    print(f"Combining {input_files} to {output_file_path}")
    # Clear the output file if it already exists
    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    for file_path in input_files:
        text_content = ""
        if file_path.endswith(".text") or file_path.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as text_file:
                text_content = text_file.read()
        elif file_path.endswith(".vtt"):
            # Read text from the VTT file (ignoring timestamps)
            with open(file_path, 'r', encoding='utf-8') as vtt_file:
                vtt_content = vtt_file.readlines()
                text_content = ' '.join(
                    line.strip() for line in vtt_content
                    if not line.startswith("WEBVTT") and line.strip()
                    and not "-->" in line.strip())

        if text_content:
            converter = opencc.OpenCC('t2s')
            text_content = converter.convert(
                text_content)  # Enforce simplified Chinese

            with open(output_file_path, 'a', encoding='utf-8') as output_file:
                output_file.write(text_content)


def shift_vtt_timestamps(vtt_file_path, start_timestamp: datetime):
    with open(vtt_file_path, 'r', encoding='utf-8') as vtt_file:
        vtt_content = vtt_file.read()

    # Convert the start timestamp to seconds
    start_time_seconds = start_timestamp.hour * 3600 + start_timestamp.minute * 60 + start_timestamp.second + start_timestamp.microsecond / 1000000

    # Define a regular expression pattern to match timestamps
    timestamp_pattern = re.compile(
        r'(\d+:\d+:\d+\.\d+) --> (\d+:\d+:\d+\.\d+)')

    # Function to shift a single timestamp
    def shift_single_timestamp(match):
        start_time = match.group(1)
        end_time = match.group(2)

        # Convert timestamp strings to seconds
        start_seconds = sum(
            x * float(t) for x, t in zip([3600, 60, 1], start_time.split(':')))
        end_seconds = sum(x * float(t)
                          for x, t in zip([3600, 60, 1], end_time.split(':')))

        # Shift timestamps by the specified duration
        new_start_seconds = start_seconds + start_time_seconds
        new_end_seconds = end_seconds + start_time_seconds

        # Format the shifted timestamps back to HH:MM:SS.SSS
        new_start_time = '{:02d}:{:02d}:{:.3f}'.format(
            int(new_start_seconds // 3600),
            int((new_start_seconds % 3600) // 60), new_start_seconds % 60)
        new_end_time = '{:02d}:{:02d}:{:.3f}'.format(
            int(new_end_seconds // 3600), int((new_end_seconds % 3600) // 60),
            new_end_seconds % 60)

        # Replace the original timestamps with the shifted timestamps
        return f'{new_start_time} --> {new_end_time}'

    # Use the re.sub function to apply the shift to all timestamps in the VTT content
    shifted_content = timestamp_pattern.sub(shift_single_timestamp,
                                            vtt_content)

    output_file_path = append_suffix_to_filename(vtt_file_path, "shifted")
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(shifted_content)

    return output_file_path


def combine_vtt_files(vtt_file_tuples, combined_vtt_file_path):
    print(
        f"Combining {[tuple[0] for tuple in vtt_file_tuples]} to {combined_vtt_file_path}"
    )
    # Shift timestamps for each segment's vtt file, then combine them into a single vtt file
    shifted_vtt_file_paths = []
    for vtt_file_tuple in vtt_file_tuples:
        vtt_file_path = vtt_file_tuple[0]
        start_timestamp = vtt_file_tuple[1]
        output_file_name = shift_vtt_timestamps(vtt_file_path, start_timestamp)
        shifted_vtt_file_paths.append(output_file_name)

    with open(combined_vtt_file_path, 'w', encoding='utf-8') as output:
        # Iterate through each input file
        for i, input_file in enumerate(shifted_vtt_file_paths):
            # Open each input file in read mode
            with open(input_file, 'r', encoding='utf-8') as input_content:
                # Read the content of the input file
                vtt_content = input_content.read()

                # Skip "WEBVTT" line for all files except the first one
                if i > 0:
                    vtt_content = '\n'.join(vtt_content.splitlines()[1:])

                # Write the content to the output file
                output.write(vtt_content)


if __name__ == "__main__":
    # Check if the correct number of command-line arguments is provided
    if len(sys.argv) != 3:
        print(
            "Usage: python script.py <input_folder> <output_file_name>(in input_folder)"
        )
        sys.exit(1)

    input_folder = sys.argv[1]
    output_file_name = sys.argv[2]

    combine_files_to_text_for_dir(input_folder, output_file_name)
