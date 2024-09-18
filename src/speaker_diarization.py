import csv
import torch
import logging
import argparse
import operator
import torchaudio

from pathlib import Path
from collections import defaultdict

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
    logger.info(
        f'Export path for speaker diarization timestamps created: {export_folder_csv}')
    return export_folder_csv


def setup_pipeline(logger):
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1", use_auth_token="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")
    pipeline.to(torch.device("cuda"))
    logger.info('Model loaded for speaker diarization')
    return pipeline


def get_speaker_diarization(pipeline, audio, sample_rate, logger):
    logger.info('Starting speaker diarization')
    output = pipeline(
        {"waveform": audio, "sample_rate": sample_rate}, min_speakers=1, max_speakers=3)
    logger.info('Completed speaker diarization')
    logger.debug(f'Speaker diarization output {output}')
    return output


def build_speaker_map(audio, sample_rate, demanding_event, logger):
    pipeline = setup_pipeline(logger)
    diarization = get_speaker_diarization(pipeline, audio, sample_rate, logger)
    speaker_times = defaultdict(float)
    speaker_map = defaultdict(list)
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        start = turn.start * 1000
        end = turn.end * 1000
        duration = end - start
        speaker_times[speaker] += duration
        speaker_map[speaker].append((start, end))
    sorted_speakers = sorted(speaker_times.items(),
                             key=operator.itemgetter(1), reverse=True)
    labels = ["trainee", "trainer", "helmsman"]
    speaker_labels = {}
    for i, (speaker, _) in enumerate(sorted_speakers):
        speaker_labels[speaker] = labels[i]
    speaker_map_with_labels = {}
    for speaker, _ in speaker_map.items():
        speaker_map_with_labels[speaker_labels[speaker]] = speaker_map[speaker]
    logger.debug(f'Speaker map with timestamps {speaker_map_with_labels}')
    export_path = create_export_path(demanding_event, logger)
    with open(f"{export_path}/speaker_diarization_timestamps.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(['speaker', 'start', 'end'])
        for speaker, segments in speaker_map_with_labels.items():
            for start, end in segments:
                writer.writerow([speaker, start, end])
    logger.info(f'Speaker map saved to {export_path}')
    return speaker_map_with_labels


def identify_speakers_in_segment(segment_start, segment_end, demanding_event, logger, speaker_map=None):
    if not speaker_map:
        logger.info('Speaker map not found, loading from file')
        speaker_map_path = create_export_path(
            demanding_event, logger) / 'speaker_diarization_timestamps.csv'
        speaker_map = {}
        with open(speaker_map_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                speaker, start, end = row[0], float(row[1]), float(row[2])
                if speaker not in speaker_map:
                    speaker_map[speaker] = []
                speaker_map[speaker].append((start, end))
    sorted_speaker_map = dict(
        sorted(speaker_map.items(), key=lambda item: item[1][0]))
    segments = []
    for speaker, intervals in sorted_speaker_map.items():
        for start, end in intervals:
            if start >= segment_end:
                break
            if end <= segment_start:
                continue
            adjusted_start = max(start, segment_start)
            adjusted_end = min(end, segment_end)
            segments.append((adjusted_start, adjusted_end, speaker))
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
    build_speaker_map(audio, sample_rate, args.name, logger)
    print(identify_speakers_in_segment(326168, 328831, "collision", logger))
