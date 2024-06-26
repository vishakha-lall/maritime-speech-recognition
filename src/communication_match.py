import json
import logging
import argparse
import pandas as pd
import spacy
import os
from pathlib import Path
nlp = spacy.blank("en")

def get_expected_response_text(demanding_event, logger):
    de_checklist = json.load(open('data/de_checklist.json'))
    expected_response = de_checklist[demanding_event]['expected_response']
    logger.debug(f'Found expected response {expected_response}')
    return expected_response

def find_nearest_chunk(timestamp_in_seconds, demanding_event, logger):
    chunks_timestamps = pd.read_csv(f'temp/extracted_timestamps/{demanding_event}/timestamps.csv')
    greatest_smaller_than_timestamp = chunks_timestamps['start'][chunks_timestamps['start'] <= timestamp_in_seconds].max()
    nearest_chunk = chunks_timestamps[chunks_timestamps['start'] == greatest_smaller_than_timestamp].index[0]
    logger.debug(f'Found nearest chunk to timestamp {nearest_chunk}')
    return nearest_chunk

def find_match_score(de_start_timestamp, de_end_timestamp, demanding_event, logger):
    expected_response = get_expected_response_text(demanding_event, logger)
    start_chunk = find_nearest_chunk(de_start_timestamp, demanding_event, logger)
    end_chunk = find_nearest_chunk(de_end_timestamp, demanding_event, logger)
    extracted_chunks_path = Path(f'temp/extracted_text/{demanding_event}')
    true_response = ""
    for chunk in range(start_chunk, end_chunk):
        chunk_transcripts = pd.read_csv(extracted_chunks_path / f'chunk_{chunk}.csv')
        for ind in chunk_transcripts.index:
            true_response += chunk_transcripts['transcript'][ind]
    logger.info(f"Match score for demanding event {demanding_event} is {nlp(true_response).similarity(nlp(expected_response))}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    demanding_event_timestamps = pd.read_csv(args.path)
    for index in demanding_event_timestamps.index:
        print(find_match_score(demanding_event_timestamps['timestamp_start'][index], demanding_event_timestamps['timestamp_end'][index], demanding_event_timestamps['demanding_event'][index], logger))