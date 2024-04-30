from pathlib import Path
import shutil
import ffmpeg
import argparse
import logging

def read_video_file(path, logger):
    logger.info(f"Reading video file: {path}")
    video_path = Path(path)
    video = ffmpeg.input(video_path)
    logger.debug(f"Video file: {video}")
    return video

def create_export_path(logger):
    export_folder = Path.cwd() / 'temp/extracted_audio'
    if export_folder.exists() and export_folder.is_dir():
        shutil.rmtree(export_folder)
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    return export_folder

def extract_audio(video, logger):
    export_folder = create_export_path(logger)
    video.output(str(export_folder / 'extracted_audio.mp3'), acodec='mp3').run()
    logger.info(f'Audio extracted and saved to {export_folder}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='INFO')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    video = read_video_file(args.path, logger)
    extract_audio(video, logger)
