import re
import json
import copy
import spacy
import logging
import argparse
import pandas as pd

from pathlib import Path
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from spaczz.matcher import FuzzyMatcher


def setup_pipeline(logger):
    access_token = "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"
    model_name = "meta-llama/Llama-2-7b-chat-hf"
    quantization_config = BitsAndBytesConfig(load_in_4bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, device_map="auto", quantization_config=quantization_config)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer


def load_all_external_internal_keywords(external_path, internal_path, logger):
    logger.info(f"Reading external keywords file: {external_path}")
    external_path = Path(external_path)
    all_external_keywords = open(external_path).readlines()
    all_external_keywords = list(
        set([keyword.strip() for keyword in all_external_keywords]))
    logger.debug(f"Extracted external keywords: {all_external_keywords}")
    logger.info(f"Reading internal keywords file: {internal_path}")
    internal_path = Path(internal_path)
    all_internal_keywords = open(internal_path).readlines()
    all_internal_keywords = list(
        set([keyword.strip() for keyword in all_internal_keywords]))
    logger.debug(f"Extracted internal keywords: {all_internal_keywords}")
    return all_external_keywords, all_internal_keywords


def create_matcher(external_path, internal_path, logger):
    nlp = spacy.blank("en")
    all_external_keywords, all_internal_keywords = load_all_external_internal_keywords(
        external_path, internal_path, logger)
    matcher = FuzzyMatcher(nlp.vocab)
    for internal_communication in all_internal_keywords:
        matcher.add("INT_COMM", [nlp(internal_communication)])
    for external_communication in all_external_keywords:
        matcher.add("EXT_COMM", [nlp(external_communication)])
    return matcher


def find_communication_level(text, matcher, logger):
    nlp = spacy.blank("en")
    doc = nlp(text)
    matches = matcher(doc)
    if len(matches) > 0:
        logger.debug(f'Fuzzy matching for {text} is {matches}')
        match_id, _, _, ratio, _ = matches[0]
        if ratio > 90:
            if match_id == "INT_COMM":
                return "internal"
            else:
                return "external"


def generate_input(text, logger):
    generated_input = {"role": "user",
                       "content": f"The trainee's dialogue is - '{text}'"}
    logger.debug(
        f'Input generated for Large Language Model - {generated_input}')
    return generated_input


def extract_entity(text, matcher, logger):
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        json_str = json_match.group()
        try:
            json_obj = json.loads(json_str)
            addressee = json_obj["addressee"]
            communication_level = find_communication_level(
                addressee, matcher, logger)
            return addressee, communication_level
        except json.JSONDecodeError as e:
            logger.debug(f"Error decoding JSON {json_str}: {e}")
    return None, None


def get_communication_entities(transcript, path, logger):
    model, tokenizer = setup_pipeline(logger)
    matcher = create_matcher('data/external_labels',
                             'data/internal_labels', logger)
    inputs = [
        {"role": "system", "content": f"You are an asistant to understand the maritime communication done by a trainee pilot during a simulated exercise with the trainer who takes multiple roles based on the situation. You will be given a dialogue spoken by the trainee. Your job is to identify in that dialogue, who the trainee is communicating with if it is specified. Note that the addressee should be a word from the dialogue. Your response should be as a json object with key - addessee. Remember, if no addressee is found return an empty json object."}
    ]
    logger.debug(f'Prompt for Large Language Model - {inputs}')
    segment_entity = {}
    for communication in transcript:
        if communication['speaker'] == 'trainee':
            if communication['segment_id'] not in segment_entity:
                segment_entity[communication['segment_id']] = {
                    'addressee': 'helmsman'.title(), 'communication_level': 'internal'.title()}
            current_inputs = copy.deepcopy(inputs)
            current_inputs.append(generate_input(
                communication['text'], logger))
            tokenized_inputs = tokenizer.apply_chat_template(
                current_inputs, tokenize=False, add_generation_prompt=True)
            tokenized_inputs = tokenizer(
                tokenized_inputs, return_tensors="pt", add_special_tokens=False)
            tokenized_inputs = {key: tensor.to(
                model.device) for key, tensor in tokenized_inputs.items()}
            outputs = model.generate(
                **tokenized_inputs, max_new_tokens=512, temperature=0.1)
            decoded_output = tokenizer.decode(
                outputs[0][tokenized_inputs['input_ids'].size(1):], skip_special_tokens=True)
            logger.debug(f'Output of Large Language Model {decoded_output}')
            addressee, communication_level = extract_entity(
                decoded_output, matcher, logger)
            if addressee is not None and communication_level is not None:
                segment_entity[communication['segment_id']] = {
                    'addressee': addressee.title(), 'communication_level': communication_level.title()}
    entity_df = pd.DataFrame.from_dict(
        segment_entity, orient='index').reset_index()
    entity_df.columns = ['segment_id', 'addressee', 'communication_level']
    entity_df.to_csv(f'{path}/extracted_entities.csv')
    logger.info(f'Extracted entities stored to {entity_df}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='DEBUG')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f'Log level: {args.loglevel}')
    logger = logging.getLogger(__name__)

    transcript = pd.read_csv(f'{args.path}/transcript.csv').to_dict('records')
    get_communication_entities(transcript, args.path, logger)
