from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import itertools
from pathlib import Path
import argparse
import logging
import csv
import shutil
import pandas as pd

def read_audio_file(path, logger):
    logger.info(f"Reading audio file: {path}")
    audio_path = Path(path)
    audio = AudioSegment.from_mp3(audio_path)
    logger.debug(f"Audio file: {audio}")
    return audio

def create_export_path(demanding_event, logger):
    export_folder = Path.cwd() / f'temp/extracted_chunks/{demanding_event}' 
    if export_folder.exists() and export_folder.is_dir():
        shutil.rmtree(export_folder)
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    export_folder_csv = Path.cwd() / f'temp/extracted_timestamps/{demanding_event}'
    Path(export_folder_csv).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path for timestamps created: {export_folder_csv}')
    return export_folder,export_folder_csv

def create_export_path_demanding_events(logger):
    export_folder = Path.cwd() / 'temp/extracted_audio/demanding_events_audio'
    if export_folder.exists() and export_folder.is_dir():
        shutil.rmtree(export_folder)
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    return export_folder

def split_on_demanding_event(audio_segment, demanding_event_timestamps_path, logger):
    demanding_event_timestamps = pd.read_csv(demanding_event_timestamps_path)
    export_path = create_export_path_demanding_events(logger)
    exported_de_audio_paths = []
    for index in demanding_event_timestamps.index:
        de_audio_segment = audio_segment[demanding_event_timestamps['timestamp_start'][index]*1000:demanding_event_timestamps['timestamp_end'][index]*1000]
        de_audio_path = f'{export_path}/{demanding_event_timestamps['demanding_event'][index]}.mp3'
        de_audio_segment.export(de_audio_path, format='mp3')
        exported_de_audio_paths.append((demanding_event_timestamps['demanding_event'][index],de_audio_path))
        logger.info(f"Audio segment for demanding event {demanding_event_timestamps['demanding_event'][index]} saved as {de_audio_path}")
    return exported_de_audio_paths

def split_on_silence(audio_segment, min_silence_len=1000, silence_thresh=-16, keep_silence=100,
                     seek_step=1):
    def pairwise(iterable):
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)
    if isinstance(keep_silence, bool):
        keep_silence = len(audio_segment) if keep_silence else 0
    output_ranges = [
        [ start - keep_silence, end + keep_silence ]
        for (start,end)
            in detect_nonsilent(audio_segment, min_silence_len, silence_thresh, seek_step)
    ]
    for range_i, range_ii in pairwise(output_ranges):
        last_end = range_i[1]
        next_start = range_ii[0]
        if next_start < last_end:
            range_i[1] = (last_end+next_start)//2
            range_ii[0] = range_i[1]
    return [
        audio_segment[ max(start,0) : min(end,len(audio_segment)) ]
        for start,end in output_ranges
    ], output_ranges

def split_into_chunks(audio, demanding_event, logger):
    logger.info(f"Splitting audio by silence")
    chunks, timestamps = split_on_silence (
        audio, 
        min_silence_len = 10000,
        silence_thresh = -45,
        keep_silence = 4000
    )
    export_path, export_folder_csv = create_export_path(demanding_event, logger)
    for i, chunk in enumerate(chunks):
        chunk.export(f'{export_path}/chunk_{i}.mp3', format="mp3")
    logger.info(f"Audio chunks saved to {export_path}")
    f = open(f'{export_folder_csv}/timestamps.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['chunk_id', 'start', 'end'])
    for i, timestamp in enumerate(timestamps):
        writer.writerow([i, timestamp[0]/1000, timestamp[1]/1000])
    f.close()
    logger.info(f"Chunk timestamps saved to {export_folder_csv}")

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

