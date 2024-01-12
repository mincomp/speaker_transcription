import argparse
import os

import numpy as np
import torch
from pyannote.audio import Audio, Pipeline
from pyannote.audio.pipelines.speaker_verification import PretrainedSpeakerEmbedding
from pyannote.audio.pipelines.utils.hook import ProgressHook
from pydub import AudioSegment
from scipy.spatial.distance import cdist

from filename_util import update_extension

DEVICE = os.getenv("DEVICE",
                   "cpu")  # use `cuda` for Nvidia GPU, `mps` if running on Mac
AUTH_TOKEN = os.getenv("HUGGINGFACE_AUTH_TOKEN")


def extract_audio_from_sample(input, sample, output):
    if os.path.exists(output):
        print(f"{output} already exists, not extracting audio")
        return
    model = PretrainedSpeakerEmbedding(
        "pyannote/wespeaker-voxceleb-resnet34-LM",  # Must match the embedding model used for diarization. Check config file from Huggingface (e.g. https://huggingface.co/pyannote/speaker-diarization-3.1/blob/main/config.yaml).
        device=torch.device(DEVICE))

    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1",
                                        use_auth_token=AUTH_TOKEN)
    assert model.embedding == pipeline.embedding

    audio = Audio(sample_rate=16000, mono='downmix')
    waveform, _ = audio({"audio": sample})
    embedding_sample = model(waveform[None])

    pipeline.to(torch.device(DEVICE))
    print("Performing speaker diarization...")
    with ProgressHook() as hook:
        diarization, embeddings = pipeline(input,
                                           hook=hook,
                                           return_embeddings=True)

    # Uncomment when Pyannote has a way to read from rttm files.
    # diarization_file = update_extension(input, "lab")
    # print(f"Writing diarization result to {diarization_file}")
    # diarization.write_rttm(diarization_file)

    distance = cdist(embeddings, embedding_sample, metric="cosine")
    ranked_idx = np.argsort(distance[:, 0])
    target_speaker = diarization.labels()[ranked_idx[0]]

    print("Collecting target speaker segments...")
    all_target_segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if speaker == target_speaker:
            if all_target_segments and turn.start - all_target_segments[-1][
                    1] < 2:  # Merge segments that are less than 2 seconds apart
                all_target_segments[-1][1] = turn.end
            else:
                all_target_segments.append([turn.start, turn.end])

    audio_data = AudioSegment.from_mp3(input)
    all_target_audio_segments = []
    for segment in all_target_segments:
        all_target_audio_segments.append(audio_data[segment[0] *
                                                    1000:segment[1] * 1000])
    concatenated_audio = sum(all_target_audio_segments)

    print("Exporting the concatenated speaker audio to a new file")
    concatenated_audio.export(output, format="mp3")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=
        "Extract certain speaker's audio from source audio file with given sample audio"
    )

    parser.add_argument("input", help="Input audio file.")
    parser.add_argument("sample", help="Sample audio file.")
    parser.add_argument("output", help="Output audio file.")
    args = parser.parse_args()

    extract_audio_from_sample(args.input, args.sample, args.output)
