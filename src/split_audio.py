from pydub import AudioSegment
from pydub.utils import make_chunks
from pathlib import Path
import argparse
import logging

def read_audio_file(path, logger):
    logger.info(f"Reading audio file: {path}")
    audio_path = Path(path)
    audio = AudioSegment.from_mp3(audio_path)
    logger.debug(f"Audio file: {audio}")
    return audio

def create_export_path(logger):
    export_folder = Path.cwd() / 'temp/extracted_chunks'
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    return export_folder

def split_into_chunks(audio, logger):
    logger.info(f"Splitting audio into 240s chunks")
    chunks = make_chunks(audio, 240000)
    export_path = create_export_path(logger)
    for i, chunk in enumerate(chunks):
        chunk.export(f'{export_path}/chunk_{i}.mp3', format="mp3")
    logger.info(f"Audio chunks saved to {export_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    audio = read_audio_file(args.path, logger)
    split_into_chunks(audio, logger)

