import logging
import argparse
import torchaudio
import pandas as pd

from pathlib import Path


def read_audio_file(path, logger):
    logger.info(f'Reading audio file: {path}')
    audio_path = Path(path)
    audio, sample_rate = torchaudio.load(audio_path)
    if audio.shape[0] > 1:
        audio = audio.mean(dim=0, keepdim=True)
    return audio, sample_rate


def split_on_demanding_event(audio_path, demanding_event_timestamps_path, logger):
    audio, sample_rate = read_audio_file(audio_path, logger)
    demanding_event_timestamps = pd.read_csv(demanding_event_timestamps_path)
    exported_de_audios = []
    for index in demanding_event_timestamps.index:
        de_audio = audio[:, int(demanding_event_timestamps['timestamp_start'][index] * sample_rate):
                         int(demanding_event_timestamps['timestamp_end'][index] * sample_rate)]
        exported_de_audios.append((
            demanding_event_timestamps['demanding_event'][index], de_audio, sample_rate))
        logger.info(
            f"Audio segment for demanding event {demanding_event_timestamps['demanding_event'][index]} extracted")
        logger.debug(
            f'Extracted tensor shape {de_audio.shape}, approximate audio segment length {de_audio.shape[1]/sample_rate/60} mins')
    return exported_de_audios


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audiopath', type=str, required=True)
    parser.add_argument('--csvpath', type=str, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f'Log level: {args.loglevel}')
    logger = logging.getLogger(__name__)

    split_on_demanding_event(args.audiopath, args.csvpath, logger)
