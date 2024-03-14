from pathlib import Path
import torch
import whisper
import argparse
import logging

def read_audio_file(path, logger):
    logger.info(f"Reading audio file: {path}")
    audio_path = Path(path)
    audio = whisper.pad_or_trim(whisper.load_audio(audio_path))
    logger.debug(f"Audio file: {audio}")
    return audio

def create_export_path(logger):
    export_folder = Path.cwd() / 'temp'
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    return export_folder

def extract_mel_features(audio, logger):
    mel = whisper.log_mel_spectrogram(audio)
    export_folder = create_export_path(logger)
    mel_dump_path = export_folder / 'audio.pt'
    torch.save(mel, mel_dump_path)
    logger.debug(f'Extracted audio features dumped to path: {mel_dump_path}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    audio = read_audio_file(args.path, logger)
    extract_mel_features(audio, logger)

