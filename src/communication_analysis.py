import re
import csv
import json
import copy
import spacy
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

from checklist_item_adherence_orm_crud import create_checklist_item_adherence
from checklist_item_orm_crud import get_checklist_item_by_demanding_event_id
from checklist_prompt_orm_crud import get_checklist_prompt_by_client_id_demanding_event_id
from extracted_entity_orm_crud import create_extracted_entities


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
    logger.debug(
        'Fuzzy matcher for internal and external classification created')
    return matcher


def find_communication_level(text, matcher, logger):
    nlp = spacy.blank("en")
    doc = nlp(text)
    matches = matcher(doc)
    if len(matches) > 0:
        logger.debug(f'Fuzzy matching for {text} is {matches[0]}')
        match_id, _, _, ratio, entity = matches[0]
        if ratio > 90:
            if match_id == "INT_COMM":
                return entity, "internal"
            else:
                return entity, "external"


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
            communication_entity, communication_level = find_communication_level(
                addressee, matcher, logger)
            return communication_entity, communication_level
        except json.JSONDecodeError as e:
            logger.debug(f"Error decoding JSON {json_str}: {e}")
        except Exception as e:
            logger.debug(f'Exception encountered, skipping {e}')
    return None, None


def get_communication_entities(session_id, demanding_event_id, transcript, path, model, tokenizer, logger):
    matcher = create_matcher('data/external_labels',
                             'data/internal_labels', logger)
    inputs = [
        {"role": "system", "content": f"""You are an assistant tasked with analyzing maritime communication during a simulated exercise involving a trainee pilot and a trainer who takes on multiple roles based on the situation. In this scenario, the trainee's own vessel is named Cosulich Adventurer. You will be given dialogue spoken by the trainee. Your job is to identify, in that dialogue, who the trainee is communicating with, if it is specified.
Additional Instructions:
1. If the trainee is communicating with someone explicitly mentioned (e.g., 'Control', 'Keppel', 'Engineer'), identify that person or group.
2. If it is not explicitly mentioned but can be inferred based on context (e.g., engine room, bridge team), provide the best inference along with reasoning.
3. If it is unclear who the trainee is communicating with, state 'Trainer' and do not guess. Give your response in the following json schema: {Entity.schema_json()}."""}
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
    create_extracted_entities(session_id, demanding_event_id, entity_df['segment_id'].to_list(
    ), entity_df['addressee'].to_list(), entity_df['communication_level'].to_list())
    logger.info(f'Extracted entities stored to {path}')


def generate_formatted_transcript(transcript, logger):
    formatted_transcript = ', '.join(
        f"{record['start']}-{record['end']}:{record['text']}"
        for record in transcript
        if record['speaker'] == "trainee"
    )
    logger.debug(f'Generated transcipt - {formatted_transcript}')
    return formatted_transcript


def get_prompt_for_demanding_event(session, demanding_event):
    de_prompt = get_checklist_prompt_by_client_id_demanding_event_id(
        session.client_id, demanding_event.id)
    formatted_de_prompt = f'{de_prompt}{Checklist.schema_json()}.'
    return formatted_de_prompt


def create_matcher_for_tokens(tokens, logger):
    nlp = spacy.blank("en")
    matcher = FuzzyMatcher(nlp.vocab)
    for token in tokens:
        matcher.add("MATCH", [nlp(token)])
    logger.debug(f'Matcher created for tokens {tokens}')
    return matcher


def find_match_in_expected_checklist(session_id, extracted_items, demanding_event, logger):
    nlp = spacy.blank("en")
    expected_checklist = get_checklist_item_by_demanding_event_id(
        demanding_event.id)
    checklist_adherance = []
    for item in expected_checklist:
        item_matched = False
        matcher = create_matcher_for_tokens(item.tokens, logger)
        for extracted_item in extracted_items:
            matches = matcher(nlp(extracted_item["item"]))
            if len(matches) > 0:
                logger.debug(f'Checklist item {item.description} completed')
                is_completed = True if extracted_item["completed_by_trainee"].lower(
                ) == "yes" else False
                completion_time = extracted_item["start_time"] if extracted_item["completed_by_trainee"].lower(
                ) == "yes" else None
                checklist_adherance.append(
                    {"checklist_item": item.description, "completed": is_completed, "importance": item.importance, "completion_time": completion_time})
                create_checklist_item_adherence(
                    session_id, demanding_event.id, item.id, is_completed, completion_time)
                item_matched = True
        if not item_matched:
            checklist_adherance.append(
                {"checklist_item": item.description, "completed": False, "importance": item.importance, "completion_time": None})
            create_checklist_item_adherence(
                session_id, demanding_event.id, item.id, False, None)
    return checklist_adherance


class ChecklistItem(BaseModel):
    item: str
    completed_by_trainee: str
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


def load_incomplete_json_array(json_array_str):
    while True:
        if not json_array_str:
            return None
        try:
            data = json.loads(json_array_str)
            return data
        except json.decoder.JSONDecodeError:
            json_array_str = json_array_str[:-1]
            json_array_str = json_array_str + "]}"


def extract_from_model_response(response, logger):
    start_index = response.find('[')
    end_index = response.find(']', start_index) + 1
    json_array_str = response[start_index:end_index]
    try:
        return load_incomplete_json_array(json_array_str)

    except json.JSONDecodeError as e:
        logger.info(f"Error decoding JSON {json_array_str}: {e}")
    except Exception as e:
        logger.info(f'Exception encountered, skipping {e}')
    return None


def split_transcript(transcript, split_size=50):
    for i in range(0, len(transcript), split_size):
        yield transcript[i:i + split_size]


def get_communication_adherance(transcript, session, demanding_event, path, model, tokenizer, logger):
    all_responses_for_demanding_event = []
    for partial_transcript in split_transcript(transcript):
        inputs = [{"role": "system", "content": get_prompt_for_demanding_event(session, demanding_event)}, {
            "role": "user", "content": f"Transcript - {generate_formatted_transcript(partial_transcript, logger)}"}]
        parser = JsonSchemaParser(Checklist.schema())
        prefix_function = build_transformers_prefix_allowed_tokens_fn(
            tokenizer, parser)
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
        responses = extract_from_model_response(decoded_output, logger)
        if responses:
            all_responses_for_demanding_event.extend(responses)
    checklist_items = all_responses_for_demanding_event
    if checklist_items:
        print(checklist_items)
        checklist_adherance = find_match_in_expected_checklist(
            session.id, checklist_items, demanding_event, logger)
        with open(f'{path}/checklist_adherance.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(
                file, fieldnames=['checklist_item', 'completed', 'importance', 'completion_time'])
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
    get_communication_adherance(
        transcript, "main_engine_failure", args.path, model, tokenizer, logger)
