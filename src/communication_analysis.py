import re
import csv
import json
import copy
import spacy
import torch
import logging
import argparse
import pandas as pd

from typing import List
from pathlib import Path
from pydantic import BaseModel, Field
from lmformatenforcer import JsonSchemaParser
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from spaczz.matcher import FuzzyMatcher
from lmformatenforcer.integrations.transformers import \
    build_transformers_prefix_allowed_tokens_fn


def setup_pipeline(logger):
    quantization_config = BitsAndBytesConfig(load_in_4bit=True)
    model = AutoModelForCausalLM.from_pretrained(
        './models/llm_model', device_map="auto", quantization_config=quantization_config)
    tokenizer = AutoTokenizer.from_pretrained('./models/llm_model')
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


class Entity(BaseModel):
    addressee: str


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
        except Exception as e:
            logger.debug(f'Exception encountered, skipping {e}')
    return None, None


def get_communication_entities(transcript, path, model, tokenizer, logger):
    matcher = create_matcher('data/external_labels',
                             'data/internal_labels', logger)
    inputs = [
        {"role": "system", "content": f"You are an asistant to understand the maritime communication done by a trainee pilot during a simulated exercise with the trainer who takes multiple roles based on the situation. You will be given a dialogue spoken by the trainee. Your job is to identify in that dialogue, who the trainee is communicating with if it is specified. Note that the addressee should be a word from the dialogue. Give your response in the following json schema: {Entity.schema_json()}."}
    ]
    logger.debug(f'Prompt for Large Language Model - {inputs}')
    parser = JsonSchemaParser(Entity.schema())
    prefix_function = build_transformers_prefix_allowed_tokens_fn(
        tokenizer, parser)
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
                **tokenized_inputs, max_new_tokens=512, temperature=0.1, prefix_allowed_tokens_fn=prefix_function)
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
    logger.info(f'Extracted entities stored to {path}')


def generate_formatted_transcript(transcript, logger):
    formatted_transcript = ', '.join(
        f"{record['start']}-{record['end']}:<{record['text']}>"
        for record in transcript
        if record['speaker'] == "trainee"
    )
    logger.debug(f'Generated transcipt - {formatted_transcript}')
    return formatted_transcript


def get_prompt_for_demanding_event(demanding_event):
    de_prompts = json.load(open('data/de_prompts.json'))
    if demanding_event == "collision":
        formatted_de_prompt = f'{de_prompts[demanding_event]}{Vessels.schema_json()}.'
    if demanding_event == "main_engine_failure" or demanding_event == "squall":
        formatted_de_prompt = f'{de_prompts[demanding_event]}{Checklist.schema_json()}.'
    return formatted_de_prompt


def create_matcher_for_tokens(tokens, logger):
    nlp = spacy.blank("en")
    matcher = FuzzyMatcher(nlp.vocab)
    for token in tokens:
        matcher.add("MATCH", [nlp(token)])
    logger.debug(f'Matcher created for tokens {tokens}')
    return matcher


def find_match_in_expected_checklist(extracted_items, demanding_event, logger):
    nlp = spacy.blank("en")
    expected_checklist = json.load(
        open('data/de_checklist.json'))[demanding_event]["checklist_items"]
    checklist_adherance = []
    for item in expected_checklist:
        item_matched = False
        matcher = create_matcher_for_tokens(item["tokens"], logger)
        for extracted_item in extracted_items:
            matches = matcher(nlp(extracted_item))
            if len(matches) > 0:
                logger.debug(f'Checklist item {item["item"]} completed')
                checklist_adherance.append(
                    {"checklist_item": item["item"], "completed": True})
                item_matched = True
                break
        if not item_matched:
            checklist_adherance.append(
                {"checklist_item": item["item"], "completed": False})
    response_correctness = (sum(
        1 for item in checklist_adherance if item["completed"] is True) / len(checklist_adherance)) * 100
    return response_correctness, checklist_adherance


class Vessel(BaseModel):
    vessel_name: str
    start_time: float = Field(..., multipleOfPrecision=0.01)

    class Config:
        schema_extra = {
            "properties": {
                "start_time": {
                    "multipleOfPrecision": 0.01
                }
            }
        }


class Vessels(BaseModel):
    vessels: List["Vessel"] = Field(max_items=10)


class ChecklistItem(BaseModel):
    item: str
    start_time: float = Field(..., multipleOfPrecision=0.01)

    class Config:
        schema_extra = {
            "properties": {
                "start_time": {
                    "multipleOfPrecision": 0.01
                }
            }
        }


class Checklist(BaseModel):
    checklist_items: List["ChecklistItem"] = Field(max_items=10)


def extract_analysis(response, demanding_event, logger):
    start_index = response.find('[')
    end_index = response.find(']', start_index) + 1
    json_array_str = response[start_index:end_index]
    try:
        if demanding_event == "collision":
            vessels = json.loads(json_array_str)
            response_correctness = len(vessels)/6
            if response_correctness > 1:
                response_correctness = 1
            response_time_in_minutes = float(vessels[0]["start_time"])/1000/60
            return response_correctness, response_time_in_minutes
        if demanding_event == "main_engine_failure" or demanding_event == "squall":
            checklist_items = json.loads(json_array_str)
            completed_checklist_items = list(
                set([record['item'] for record in checklist_items]))
            response_correctness, checklist_adherance = find_match_in_expected_checklist(
                completed_checklist_items, demanding_event, logger)
            response_time_in_minutes = float(
                checklist_items[0]["start_time"])/1000/60
            return response_correctness, response_time_in_minutes, checklist_adherance
    except json.JSONDecodeError as e:
        logger.debug(f"Error decoding JSON {json_array_str}: {e}")
    except Exception as e:
        logger.debug(f'Exception encountered, skipping {e}')
    return None


def get_communication_adherance(transcript, demanding_event, path, model, tokenizer, logger):
    inputs = [{"role": "system", "content": get_prompt_for_demanding_event(demanding_event)}, {
        "role": "user", "content": f"Transcript - {generate_formatted_transcript(transcript, logger)}"}]
    if demanding_event == "collision":
        parser = JsonSchemaParser(Vessels.schema())
        prefix_function = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)
    if demanding_event == "main_engine_failure" or demanding_event == "squall":
        parser = JsonSchemaParser(Checklist.schema())
        prefix_function = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)
    tokenized_inputs = tokenizer.apply_chat_template(
        inputs, tokenize=False, add_generation_prompt=True)
    tokenized_inputs = tokenizer(
        tokenized_inputs, return_tensors="pt", add_special_tokens=False)
    tokenized_inputs = {key: tensor.to(
        model.device) for key, tensor in tokenized_inputs.items()}
    outputs = model.generate(
        **tokenized_inputs, max_new_tokens=1000, temperature=0.1, prefix_allowed_tokens_fn=prefix_function)
    decoded_output = tokenizer.decode(
        outputs[0][tokenized_inputs['input_ids'].size(1):], skip_special_tokens=True)
    logger.debug(f'Output of Large Language Model {decoded_output}')
    analysis = extract_analysis(
        decoded_output, demanding_event, logger)
    if analysis:
        response_correctness = analysis[0]
        response_time_in_minutes = analysis[1]
        if response_correctness is not None and response_time_in_minutes is not None:
            with open(f'{path}/response_analysis.csv', mode='w', newline='') as file:
                writer = csv.DictWriter(
                    file, fieldnames=['response_correctness', 'response_time_in_minutes'])
                writer.writeheader()
                writer.writerow({'response_correctness': response_correctness,
                                'response_time_in_minutes': response_time_in_minutes})
            logger.info(f'Extracted analysis stored to {path}')
        if demanding_event == "main_engine_failure" or demanding_event == "squall":
            checklist_adherance = analysis[2]
            with open(f'{path}/checklist_adherance.csv', mode='w', newline='') as file:
                writer = csv.DictWriter(
                    file, fieldnames=['checklist_item', 'completed'])
                writer.writeheader()
                for item in checklist_adherance:
                    writer.writerow(item)
            logger.info(f'Extracted checklist completion stored to {path}')


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
    model, tokenizer = setup_pipeline(logger)
    # get_communication_entities(transcript, args.path, model, tokenizer, logger)
    get_communication_adherance(transcript, "main_engine_failure", args.path, model, tokenizer, logger)
