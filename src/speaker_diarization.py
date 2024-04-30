from pyannote.audio import Pipeline
import torch
from pathlib import Path
import argparse
import logging
import csv
import shutil

def setup_pipeline(logger):
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token="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")
    pipeline.to(torch.device("cuda"))
    logger.debug("Model loaded for speaker diarization")
    return pipeline

def get_speaker_diarization(pipeline, audio_path, logger):
    output = pipeline(audio_path)
    logger.debug(f"Speaker diarization output {list(output.itertracks(yield_label=True))}")
    return output

def create_export_path(demanding_event, logger, audio_name):
    export_folder_csv = Path.cwd() / f'temp/extracted_timestamps/speaker_diarization/{demanding_event}' / audio_name
    if export_folder_csv.exists() and export_folder_csv.is_dir():
        shutil.rmtree(export_folder_csv)
    Path(export_folder_csv).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path for speaker diarization timestamps created: {export_folder_csv}')
    return export_folder_csv

def segment_audio_by_speakers(audio_path, audio_name, demanding_event, logger):
    pipeline = setup_pipeline(logger)
    output = get_speaker_diarization(pipeline, audio_path, logger)
    export_folder_csv = create_export_path(demanding_event, logger, audio_name)
    f = open(f'{export_folder_csv}/timestamps.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['speaker_id', 'start', 'end'])
    segments_by_speaker = {}
    for segment, _, speaker in output.itertracks(yield_label=True):
        if speaker in segments_by_speaker:
            segments_by_speaker[speaker].append(segment)
        else:
            segments_by_speaker[speaker] = [segment]
    for speaker, segments in segments_by_speaker.items():
        previous_segment_start = 0
        previous_segment_end = 0
        for segment in segments:
            if segment.start - previous_segment_end < 1:
                previous_segment_end = segment.end
            else:
                if previous_segment_end - previous_segment_start > 1:
                    writer.writerow([speaker, previous_segment_start, previous_segment_end])
                previous_segment_start = segment.start
                previous_segment_end = segment.end
        if previous_segment_end - previous_segment_start > 1:
            writer.writerow([speaker, previous_segment_start, previous_segment_end])
    logger.info(f"Speaker diarization timestamps saved to {export_folder_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--name', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    segment_audio_by_speakers(args.path, args.name, logger)
