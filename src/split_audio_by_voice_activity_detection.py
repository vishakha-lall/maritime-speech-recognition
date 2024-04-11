from pydub import AudioSegment
from pyannote.audio import Pipeline
import torch
from pathlib import Path
import argparse
import logging
import csv
import shutil

def read_audio_file(path, logger):
    logger.info(f"Reading audio file: {path}")
    audio_path = Path(path)
    audio = AudioSegment.from_mp3(audio_path)
    logger.debug(f"Audio file: {audio}")
    return audio

def create_export_path(logger):
    export_folder = Path.cwd() / 'temp/extracted_chunks'
    if export_folder.exists() and export_folder.is_dir():
        shutil.rmtree(export_folder)
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    export_folder_csv = Path.cwd() / 'temp/extracted_timestamps'
    Path(export_folder_csv).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path for timestamps created: {export_folder_csv}')
    return export_folder,export_folder_csv

def setup_pipeline(logger):
    pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection", use_auth_token="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")
    pipeline.to(torch.device("cuda"))
    logger.debug("Model loaded for voice activity detection")
    return pipeline

def get_voice_activity_detection(pipeline, audio_path, logger):
    output = pipeline(audio_path)
    logger.debug(f"Voice activity detection output {list(output.itertracks(yield_label=True))}")
    return output

def get_segments(pipeline, audio_path, logger):
    output = get_voice_activity_detection(pipeline, audio_path, logger)
    previous_segment_start = 0
    previous_segment_end = 0
    segments = []
    for segment, _, _ in output.itertracks(yield_label=True):
        if segment.start - previous_segment_end > 10:
            segments.append((previous_segment_start, previous_segment_end))
            previous_segment_start = segment.start
            previous_segment_end = segment.end
        else:
            previous_segment_end = segment.end
    if segment.start - previous_segment_end > 10:
        segments.append((previous_segment_start, previous_segment_end))
    return segments

def split_into_chunks(pipeline, audio_path, logger):
    audio = read_audio_file(audio_path, logger)
    logger.info(f"Splitting audio by voice activity detection")
    segments = get_segments(pipeline, audio_path, logger)
    export_path, export_folder_csv = create_export_path(logger)
    f = open(f'{export_folder_csv}/chunk_timestamps.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['chunk_id', 'start', 'end'])
    for i, segment in enumerate(segments):
        print(segment)
        audio_chunk=audio[segment[0]*1000:segment[1]*1000]
        audio_chunk.export(f'{export_path}/chunk_{i}.mp3', format="mp3")
        writer.writerow([i, segment[0], segment[1]])
    f.close()
    logger.info(f"Audio chunks saved to {export_path}")
    logger.info(f"Chunk timestamps saved to {export_folder_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    pipeline = setup_pipeline(logger)
    split_into_chunks(pipeline, args.path, logger)

