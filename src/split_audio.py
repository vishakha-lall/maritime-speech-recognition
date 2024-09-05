import logging
import argparse
import torchaudio
import pandas as pd

from pathlib import Path
from demanding_event_orm_crud import get_demanding_event_by_id
from demanding_event_session_mapping_orm_crud import get_demanding_event_session_mapping_by_session_id


def read_audio_file(path, logger):
    logger.info(f'Reading audio file: {path}')
    audio_path = Path(path)
    audio, sample_rate = torchaudio.load(audio_path)
    if audio.shape[0] > 1:
        audio = audio.mean(dim=0, keepdim=True)
    return audio, sample_rate


def split_on_demanding_event(audio_path, demanding_event_session_mappings, logger):
    audio, sample_rate = read_audio_file(audio_path, logger)
    exported_de_audios = []
    for demanding_event_session_mapping in demanding_event_session_mappings:
        de_audio = audio[:, int(demanding_event_session_mapping.time_start * sample_rate):
                         int(demanding_event_session_mapping.time_end * sample_rate)]
        demanding_event = get_demanding_event_by_id(
            demanding_event_session_mapping.demanding_event_id)
        exported_de_audios.append(
            (demanding_event, de_audio, sample_rate))
        logger.info(
            f"Audio segment for demanding event {demanding_event.type} extracted")
        logger.debug(
            f'Extracted tensor shape {de_audio.shape}, approximate audio segment length {de_audio.shape[1]/sample_rate/60} mins')
    return exported_de_audios


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--audiopath', type=str, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f'Log level: {args.loglevel}')
    logger = logging.getLogger(__name__)

    demanding_event_session_mappings = get_demanding_event_session_mapping_by_session_id(
        1)
    split_on_demanding_event(
        args.audiopath, demanding_event_session_mappings, logger)
