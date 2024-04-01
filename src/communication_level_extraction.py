from pathlib import Path
import argparse
import logging
import spacy
from spaczz.matcher import FuzzyMatcher
nlp = spacy.blank("en")

def read_text_file(path, logger):
    logger.info(f"Reading text file: {path}")
    text_path = Path(path)
    f = open(text_path, "r")
    text = f.read()
    logger.info(f"Text: {text}")
    return text

def load_all_external_internal_keywords(external_path, internal_path, logger):
    logger.info(f"Reading external keywords file: {external_path}")
    external_path = Path(external_path)
    all_external_keywords = open(external_path).readlines()
    all_external_keywords = list(set([keyword.strip() for keyword in all_external_keywords]))
    logger.debug(f"Extracted external keywords: {all_external_keywords}")
    logger.info(f"Reading internal keywords file: {internal_path}")
    internal_path = Path(internal_path)
    all_internal_keywords = open(internal_path).readlines()
    all_internal_keywords = list(set([keyword.strip() for keyword in all_internal_keywords]))
    logger.debug(f"Extracted internal keywords: {all_internal_keywords}")
    return all_external_keywords, all_internal_keywords

def create_matcher(external_path, internal_path, logger):
    all_external_keywords, all_internal_keywords = load_all_external_internal_keywords(external_path, internal_path, logger)
    matcher = FuzzyMatcher(nlp.vocab)
    for internal_communication in all_internal_keywords:
        matcher.add("INT_COMM", [nlp(internal_communication)])
    for external_communication in all_external_keywords:
        matcher.add("EXT_COMM", [nlp(external_communication)])
    return matcher

def find_matches(text, matcher, logger):
    doc = nlp(text)
    matches = matcher(doc)
    communication_levels = {'internal':[], 'external':[]}
    for match_id, start, end, ratio, pattern in matches:
        logger.debug(f"Match found for entity {match_id} {doc[start:end]} as {pattern} with match confidence {ratio}")
        if ratio > 90:
            if match_id == "INT_COMM":
                communication_levels['internal'].append(pattern)
            else:
                communication_levels['external'].append(pattern)
    communication_levels['internal'] = list(set(communication_levels['internal']))
    communication_levels['external'] = list(set(communication_levels['external']))
    logger.info(f"Found communication {communication_levels}")
    return communication_levels

def find_communication_level(communication_levels, logger):
    logger.debug(f"Extracted communication {communication_levels}")
    if len(communication_levels['external']) > len(communication_levels['internal']):
        logger.info(f"External Communication with the following entities {communication_levels['external']}")
    else:
        logger.info(f"Internal Communication with the following entities {communication_levels['internal']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--textpath', type=str, required=True)
    parser.add_argument('--internalpath', type=str, required=True)
    parser.add_argument('--externalpath', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    text = read_text_file(args.textpath, logger)
    matcher = create_matcher(args.externalpath, args.internalpath, logger)
    communication_levels = find_matches(text, matcher, logger)
    find_communication_level(communication_levels, logger)
    

