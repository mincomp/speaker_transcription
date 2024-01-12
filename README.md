# speaker_transcription
Transcribe text from audio for a certain speaker

This repo is consisted of a few scripts that could be used in combination to transcribe a certain speaker (for whom we have some sample audio) from a given audio.

The main idea is to use Pyannote to do speaker diarization, then match a speaker by comparing embedding similarity with the sample audio. Transcription is done with OpenAI Whisper API.

## Set up

Some set up is needed before using these scripts.
- Prepare a [Huggingface auth token](https://huggingface.co/settings/tokens) (for pyannote) and an [OpenAI API key](https://platform.openai.com/api-keys) (for Whisper transcription), and set them as environment variables `HUGGINGFACE_AUTH_TOKEN` and `OPENAI_API_KEY`.
- Make sure [`ffpmeg`](https://www.ffmpeg.org/download.html) is installed can be invoked from commandline.
- In a Python virtual environment, `pip install -r requirements.txt`

## Scripts

- audio_transcription.py: the main script. Given an input audio file, a sample audio file for target speaker, and output format (text for vtt), extract target speaker audio segments from input audio, and transcribe according to the format.
- extract_audio_with_target_speaker.py: speaker diarization, target speaker matching and extraction from input audio.
- video_to_audio.py: extra audio from video file(s).
- combine_text_vtt.py: combine text / vtt files into one.

## Example

- Transcribe two audio files to two vtt files
```
OPENAI_API_KEY=<> HUGGINGFACE_AUTH_TOKEN=<> python audio_transcription.py data/input1.mp3,data/input2.mp3 data/sample.mp3 vtt --language zh --prompt 以下，是普通话的句子。
```

## Acceleration

Running speaker diarization with CPU can be slow, so set environment variable `DEVICE` to `cuda` to use Nvidia GPU, and `mps` if running on Mac.

## License
[MIT License](./LICENSE)