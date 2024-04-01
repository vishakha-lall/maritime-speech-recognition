from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import itertools
from pathlib import Path
import argparse
import logging
import csv

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

def split_into_chunks(audio, logger):
    logger.info(f"Splitting audio by silence")
    chunks, timestamps = split_on_silence (
        audio, 
        min_silence_len = 10000,
        silence_thresh = -35,
        keep_silence = 4000
    )
    export_path = create_export_path(logger)
    for i, chunk in enumerate(chunks):
        chunk.export(f'{export_path}/chunk_{i}.mp3', format="mp3")
    logger.info(f"Audio chunks saved to {export_path}")
    f = open(f'{export_path}/timestamps.csv', 'w')
    writer = csv.writer(f)
    writer.writerow(['chunk_id', 'start', 'end'])
    for i, timestamp in enumerate(timestamps):
        writer.writerow([i, timestamp[0], timestamp[1]])
    f.close()
    logger.info(f"Chunk timestamps saved to {export_path}")

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

