import pandas as pd
import json
import argparse
import logging
import os
from pathlib import Path
import spacy
from spaczz.matcher import FuzzyMatcher
nlp = spacy.blank("en")

def find_nearest_chunk(timestamp_in_seconds, logger):
    chunks_timestamps = pd.read_csv('temp/extracted_timestamps/timestamps.csv')
    greatest_smaller_than_timestamp = chunks_timestamps['start'][chunks_timestamps['start'] <= timestamp_in_seconds].max()
    nearest_chunk = chunks_timestamps[chunks_timestamps['start'] == greatest_smaller_than_timestamp].index[0]
    logger.debug(f'Found nearest chunk to timestamp {nearest_chunk}')
    return nearest_chunk

def get_expected_response_tokens(demanding_event, logger):
    de_checklist = json.load(open('data/de_checklist.json'))
    expected_tokens = [token for token in de_checklist[demanding_event]['expected_tokens']]
    logger.debug(f'Found expected tokens {expected_tokens}')
    return expected_tokens

def create_matcher(tokens):
    matcher = FuzzyMatcher(nlp.vocab)
    for token in tokens:
        matcher.add("DE", [nlp(token)])
    return matcher

def is_match(text, matcher, logger):
    doc = nlp(text)
    matches = matcher(doc)
    if len(matches) == 0:
        return False
    for match_id, start, end, ratio, pattern in matches:
        logger.debug(f"Match found for entity {match_id} {doc[start:end]} as {pattern} with match confidence {ratio}")
        if ratio > 90:
            return True
    return False

def find_response_time(demanding_event, demanding_event_timestamp, logger):
    nearest_chunk = find_nearest_chunk(demanding_event_timestamp, logger)
    expected_tokens = get_expected_response_tokens(demanding_event, logger)
    matcher = create_matcher(expected_tokens)
    chunks_path = Path('temp/extracted_chunks')
    total_chunks = len(os.listdir(chunks_path))
    extracted_chunks_path = Path('temp/extracted_text')
    for chunk in range(nearest_chunk, total_chunks):
        chunk_transcripts = pd.read_csv(extracted_chunks_path / f'chunk_{chunk}.csv')
        for ind in chunk_transcripts.index:
            if is_match(chunk_transcripts['transcript'][ind], matcher, logger):
                logger.debug(f"First match for {demanding_event} found in chunk {chunk} at segment {chunk_transcripts['transcript'][ind]}")
                logger.info(f"Response time for {demanding_event} : {chunk_transcripts['start'][ind]}")
    logger.info(f'Response time could not be conclusively identified')

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
        response_time = find_response_time(demanding_event_timestamps['demanding_event'][index], demanding_event_timestamps['timestamp_start'][index], logger)
