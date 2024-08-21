import csv
import torch
import logging
import argparse
import torchaudio

from pathlib import Path

from pyannote.audio import Pipeline


def read_audio_file(path, logger):
    logger.info(f'Reading audio file: {path}')
    audio_path = Path(path)
    audio, sample_rate = torchaudio.load(audio_path)
    return audio, sample_rate


def create_export_path(demanding_event, logger):
    export_folder_csv = Path.cwd(
    ) / f'temp/extracted_timestamps/{demanding_event}'
    Path(export_folder_csv).mkdir(parents=True, exist_ok=True)
    logger.info(f'Export path for timestamps created: {export_folder_csv}')
    return export_folder_csv


def setup_pipeline(logger):
    pipeline = Pipeline.from_pretrained(
        "pyannote/voice-activity-detection", use_auth_token="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")
    pipeline.to(torch.device("cuda"))
    logger.info('Model loaded for voice activity detection')
    return pipeline


def get_voice_activity_detection(pipeline, audio, sample_rate, logger):
    logger.info('Starting voice activity detection')
    output = pipeline({"waveform": audio, "sample_rate": sample_rate})
    logger.info('Completed voice activity detection')
    logger.debug(f'Voice activity detection output {output}')
    return output


def get_segments(pipeline, audio, sample_rate, logger):
    output = get_voice_activity_detection(pipeline, audio, sample_rate, logger)
    segments = []
    max_length = 10 * 1000
    for speech in output.get_timeline().support():
        start = int(speech.start * 1000)
        end = int(speech.end * 1000)
        while start < end:
            segment_end = min(start + max_length, end)
            segments.append((start, segment_end))
            start = segment_end
    logger.debug(
        f'Number of segments detected by voice activity detection {len(segments)}')
    return segments


def split_into_chunks(audio, sample_rate, demanding_event, logger):
    pipeline = setup_pipeline(logger)
    segments = get_segments(pipeline, audio, sample_rate, logger)
    export_path = create_export_path(demanding_event, logger)
    f = open(f'{export_path}/chunk_timestamps.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['chunk_id', 'start', 'end'])
    for i, segment in enumerate(segments):
        writer.writerow([i, segment[0], segment[1]])
    f.close()
    logger.info(f'Chunk timestamps saved to {export_path}')
    return segments


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--name', type=str, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f'Log level: {args.loglevel}')
    logger = logging.getLogger(__name__)

    audio, sample_rate = read_audio_file(args.path, logger)
    split_into_chunks(audio, sample_rate, args.name, logger)
