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

def load_all_locations(path, logger):
    logger.info(f"Reading locations file: {path}")
    locations_path = Path(path)
    all_locations = open(locations_path).readlines()
    all_locations = list(set([location.strip() for location in all_locations]))
    logger.debug(f"Extracted locations: {all_locations}")
    return all_locations

def create_matcher(path, logger):
    matcher_location = FuzzyMatcher(nlp.vocab)
    for location in load_all_locations(path, logger):
        matcher_location.add("ANCHORAGE", [nlp(location)])
    return matcher_location

def find_matches(text, matcher_location, logger):
    doc = nlp(text)
    matches = matcher_location(doc)
    locations = []
    for match_id, start, end, ratio, pattern in matches:
        logger.debug(f"Match found for entity {match_id} {doc[start:end]} as {pattern} with match confidence {ratio}")
        if ratio > 84:
            locations.append(pattern)
    locations = list(set(locations))
    logger.info(f"Found locations {locations}")
    return locations

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--textpath', type=str, required=True)
    parser.add_argument('--locationspath', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    text = read_text_file(args.textpath, logger)
    matcher = create_matcher(args.locationspath, logger)
    find_matches(text, matcher, logger)
    

