# coding:utf-8
'''Get all questions, annotated actions, entities, relations, types together in JSON format.
'''
from itertools import islice
from Preprocess.load_qadata import load_qadata, getQA_by_state_py3
import sys
import json
#Python codes to read the binary files.
import numpy as np
import random
SEED = 1987
LINE_SIZE = 100000
from random import shuffle

special_counting_characters = {'-','|','&'}
special_characters = {'(',')','-','|','&'}

# Get items_wikidata_n.json.
# This json contains a dict with keys as the ids of wikidata entities and values as their string labels.
def getEntitiyID2Label():
    with open("../../data/official_downloaded_data/items_wikidata_n.json", 'r', encoding="UTF-8") as load_f:
        load_dict = json.load(load_f)
    print ('Reading items_wikidata_n.json is done!')
    return load_dict

# Get all questions and answers in CQA-10K data-set for REINFORCEMENT learning by using denotations.
# Also treat the JSON as the file of training set used for REINFORCEMENT learning with denotations.
def getAllQustionsAndAnswers():
    fw = open('../../data/auto_QA_data/CSQA_DENOTATIONS_full.json', 'w', encoding="UTF-8")
    qa_set = load_qadata("../../data/official_downloaded_data/10k/train_10k")
    qa_map = getQA_by_state_py3(qa_set)
    load_dict = getEntitiyID2Label()
    question_dict = {}
    totality = 0
    fwQuestionDic = open('../../data/auto_QA_data/mask/dic_rl_tr.question', 'w', encoding="UTF-8")
    questionSet = set()
    for qafile_key, qafile_value in qa_map.items():
        id_prefix = qafile_key
        count = 0
        for qa in qafile_value:
            # context = qa['context'].replace("\n", "").strip()
            context_utterance = qa['context_utterance'].replace("\n", "").strip()
            if(len(context_utterance)==0):
                continue
            count += 1
            id = id_prefix.replace("\n", "").strip() + '_' + str(count)
            context_entities = [] if(len(qa['context_entities'].replace("\n", "").strip())==0) else qa['context_entities'].replace("\n", "").strip().split("|")
            context_relations = [] if(len(qa['context_relations'].replace("\n", "").strip())==0) else qa['context_relations'].replace("\n", "").strip().split("|")
            context_types = [] if (len(qa['context_types'].replace("\n", "").strip())==0) else qa['context_types'].replace("\n", "").strip().split("|")
            context_ints = qa['context_ints'].replace("\n", "").strip()
            # Get reverse relation: has_child and -has_child.
            # context_relations.extend(['-' + r for r in context_relations])
            response_entities = []  if (len(qa['response_entities'].replace("\n", "").strip())==0) else qa['response_entities'].replace("\n", "").strip().split("|")
            orig_response = qa['orig_response'].replace("\n", "").strip()
            response_bools = [] if (len(qa['response_bools'].replace("\n", "").strip())==0) else qa['response_bools'].replace("\n", "").strip().split("|")
            # response_ints = qa['response_ints'].replace("\n", "").split("|")
            question_info = {}
            question_info.update({'question': context_utterance,
                                  'entity': context_entities, 'relation': context_relations,
                                  'type': context_types,'context_ints': context_ints,
                                  'response_entities': response_entities,'orig_response': orig_response,
                                  'response_bools': response_bools})
            # Get masked entity.
            entity_maskID = {}
            if len(context_entities)!=0:
                context_utterance_low = context_utterance.lower()
                entity_index_dict = {}
                for entity in context_entities:
                    if(entity in load_dict):
                        entity_name = load_dict.get(entity).lower()
                        entity_index_dict[entity] = entity_name
                    else:
                        entity_index_dict[entity] = entity
                for key, value in entity_index_dict.items():
                    if(value in context_utterance_low):
                        entity_index_dict[key] = context_utterance_low.index(value)
                    else:
                        entity_index_dict[key] = LINE_SIZE
                temp_count = 0
                # To sort a dict by value.
                for key, value in sorted(entity_index_dict.items(), key=lambda item: item[1]):
                    entity_maskID[key] = 'ENTITY' + str(temp_count + 1)
                    temp_count+=1
            question_info['entity_mask'] = entity_maskID

            # Get masked relation.
            relation_maskID = {}
            if len(context_relations) != 0:
                relation_index = 0
                for relation in context_relations:
                    relation = relation.replace('-', '')
                    if relation not in relation_maskID:
                        relation_index += 1
                        relation_maskID[relation] = 'RELATION' + str(relation_index)
            question_info['relation_mask'] = relation_maskID

            # Get masked type.
            type_maskID = {}
            if len(context_types) != 0:
                for i, type in enumerate(context_types):
                    type_maskID[type] = 'TYPE' + str(i + 1)
            question_info['type_mask'] = type_maskID

            question_string = '<E> '
            if len(entity_maskID) > 0:
                for entity_key, entity_value in entity_maskID.items():
                    if str(entity_value) != '':
                        question_string += str(entity_value) + ' '
            question_string += '</E> <R> '
            if len(relation_maskID) > 0:
                for relation_key, relation_value in relation_maskID.items():
                    if str(relation_value) != '':
                        question_string += str(relation_value) + ' '
            question_string += '</R> <T> '
            if len(type_maskID) > 0:
                for type_key, type_value in type_maskID.items():
                    if str(type_value) != '':
                        question_string += str(type_value) + ' '
            question_string += '</T> '

            question_token = str(context_utterance).lower().replace('?', '')
            question_token = question_token.replace(',', ' ')
            question_token = question_token.replace(':', ' ')
            question_token = question_token.replace('(', ' ')
            question_token = question_token.replace(')', ' ')
            question_token = question_token.replace('"', ' ')
            question_token = question_token.strip()
            question_string += question_token
            question_string = question_string.strip()
            question_tokens = question_string.strip().split(' ')
            question_tokens_set = set(question_tokens)
            questionSet = questionSet.union(question_tokens_set)
            question_info['input'] = question_string
            question_dict[id] = question_info
            totality += 1
            if(totality%1000==0):
                print(totality)
    fw.writelines(json.dumps(question_dict, indent=1, ensure_ascii=False))
    fw.close()
    questionList = list()
    for item in questionSet:
        temp = str(item) + '\n'
        if temp != '\n':
            questionList.append(temp)
    fwQuestionDic.writelines(questionList)
    fwQuestionDic.close()
    print("Writing CSQA_DENOTATIONS_full.JSON is done!")

def getAllQuestionsAndActions():
    fw = open('../../data/auto_QA_data/CSQA_ANNOTATIONS_full.json', 'w', encoding="UTF-8")
    '''dictMerged2 = dict( dict1, **dict2 ) is :
        dictMerged2 = dict1.copy()
        dictMerged2.update( dict2 )'''
    question_dicts = dict(
        getQuestionsAndActions('../../data/annotation_logs/simple_auto.log', '../../data/annotation_logs/simple_orig.log'),
    **(getQuestionsAndActions('../../data/annotation_logs/quantative_auto.log','../../data/annotation_logs/quantative_orig.log')))
    question_dicts = dict(question_dicts,
        **(getQuestionsAndActions('../../data/annotation_logs/logical_auto.log','../../data/annotation_logs/logical_orig.log')))
    question_dicts = dict(question_dicts,
                          **(getQuestionsAndActions('../../data/annotation_logs/count_auto.log',
                                                    '../../data/annotation_logs/count_orig.log')))
    question_dicts = dict(question_dicts,
                          **(getQuestionsAndActions('../../data/annotation_logs/bool_auto.log',
                                                    '../../data/annotation_logs/bool_orig.log')))
    question_dicts = dict(question_dicts,
                          **(getQuestionsAndActions('../../data/annotation_logs/comp_auto.log',
                                                    '../../data/annotation_logs/comp_orig.log')))
    question_dicts = dict(question_dicts,
                          **(getQuestionsAndActions('../../data/annotation_logs/compcount_auto.log',
                                                    '../../data/annotation_logs/compcount_orig.log')))
    question_dicts = dict(question_dicts,
                          **(getQuestionsAndActions('../../data/annotation_logs/compappro_auto.log',
                                                    '../../data/annotation_logs/compappro_orig.log')))
    question_dicts = dict(question_dicts,
                          **(getQuestionsAndActions('../../data/annotation_logs/compcountappro_auto.log',
                                                    '../../data/annotation_logs/compcountappro_orig.log')))
    fw.writelines(json.dumps(question_dicts, indent=1, ensure_ascii=False))
    fw.close()
    print ("Writing JSON is done!")

def getQuestionsAndActions(annotationPath, origPath):
    annotation_list = list()
    orig_list = list()
    question_dict = {}
    with open(annotationPath, 'r', encoding="UTF-8") as infile:
        count = 0
        while True:
            lines_gen = list(islice(infile, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                annotation_list.append(line.strip())
            count = count + 1
            print(count)
    with open(origPath, 'r', encoding="UTF-8") as infile:
        count = 0
        while True:
            lines_gen = list(islice(infile, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                orig_list.append(line.strip())
            count = count + 1
            print(count)
    count = 0
    # Each question is corresponding to one action sequence.
    while count < len(annotation_list):
        line_string = str(annotation_list[count]).strip()
        if str(line_string).startswith('['):
            count += 1
        else:
            string_list = str(line_string).split(' ')
            if 'simple_' in str(annotationPath):
                ID_string = 'simple_' + string_list[0]
            elif 'logical_' in str(annotationPath):
                ID_string = 'logical_' + string_list[0]
            elif 'quantative_' in str(annotationPath):
                ID_string = 'quantative_' + string_list[0]
            elif 'count_' in str(annotationPath) and 'compcount_' not in str(annotationPath):
                ID_string = 'count_' + string_list[0]
            elif 'bool_' in str(annotationPath):
                ID_string = 'bool_' + string_list[0]
            elif 'comp_' in str(annotationPath):
                ID_string = 'comp_' + string_list[0]
            elif 'compcount_' in str(annotationPath):
                ID_string = 'compcount_' + string_list[0]
            elif 'compcountappro_' in str(annotationPath):
                ID_string = 'compcountappro_' + string_list[0]
            elif 'compappro_' in str(annotationPath):
                ID_string = 'compappro_' + string_list[0]
            question_string = ' '.join(string_list[1:])
            actionSequenceList = list()
            count += 1
            while count < len(annotation_list) and str(annotation_list[count]).strip().startswith('[') :
                actionSequence = eval(str(annotation_list[count]).strip())
                actionSequenceList.append(actionSequence)
                count += 1
            question_info = {}
            # Original annotation information.
            question_info.setdefault('question', question_string)
            question_info.setdefault('action_sequence_list', actionSequenceList)
            question_dict.setdefault(ID_string, question_info)

    count = 0
    while count < len(orig_list):
        if 'simple_' in str(origPath):
            ID_string = 'simple_' + str(orig_list[count]).strip()
        elif 'logical_' in str(origPath):
            ID_string = 'logical_' + str(orig_list[count]).strip()
        elif 'quantative_' in str(origPath):
            ID_string = 'quantative_' + str(orig_list[count]).strip()
        elif 'count_' in str(origPath) and 'compcount_' not in str(origPath):
            ID_string = 'count_' + str(orig_list[count]).strip()
        elif 'bool_' in str(origPath):
            ID_string = 'bool_' + str(orig_list[count]).strip()
        elif 'comp_' in str(origPath):
            ID_string = 'comp_' + str(orig_list[count]).strip()
        elif 'compcount_' in str(origPath):
            ID_string = 'compcount_' + str(orig_list[count]).strip()
        elif 'compcountappro_' in str(origPath):
            ID_string = 'compcountappro_' + str(orig_list[count]).strip()
        elif 'compappro_' in str(annotationPath):
            ID_string = 'compappro_' + str(orig_list[count]).strip()
        if ID_string in question_dict:
            question_info_new = question_dict.get(ID_string)
            entity_list = list()
            relation_list = list()
            type_list = list()
            if count+2 < len(orig_list) and str(orig_list[count+2]).startswith('context_entities'):
                entity_string = str(orig_list[count+2]).strip()
                entity_string = entity_string.replace('context_entities:','').strip()
                if len(entity_string) > 0:
                    entity_list = entity_string.split(',')
            if count+3 < len(orig_list) and str(orig_list[count+3]).startswith('context_relations'):
                relation_string = str(orig_list[count+3]).strip()
                relation_string = relation_string.replace('context_relations:','').strip()
                if len(relation_string) > 0:
                    relation_list = relation_string.split(',')
            if count+4 < len(orig_list) and str(orig_list[count+4]).startswith('context_types'):
                type_string = str(orig_list[count+4]).strip()
                type_string = type_string.replace('context_types:','').strip()
                if len(type_string) > 0:
                    type_list = type_string.split(',')
            question_info_new.setdefault('entity', entity_list)
            question_info_new.setdefault('relation', relation_list)
            question_info_new.setdefault('type', type_list)
            entity_maskID = {}
            if len(entity_list) !=0:
                for i, entity in enumerate(entity_list):
                    entity_maskID.setdefault(entity, 'ENTITY'+str(i+1))
            question_info_new.setdefault('entity_mask', entity_maskID)
            relation_maskID = {}
            if len(relation_list) != 0:
                relation_index = 0
                for relation in relation_list:
                    relation = relation.replace('-','')
                    if relation not in relation_maskID:
                        relation_index += 1
                        relation_maskID.setdefault(relation, 'RELATION' + str(relation_index))
            question_info_new.setdefault('relation_mask', relation_maskID)
            type_maskID = {}
            if len(type_list) != 0:
                for i, type in enumerate(type_list):
                    type_maskID.setdefault(type, 'TYPE' + str(i + 1))
            question_info_new.setdefault('type_mask', type_maskID)
            actions = question_info_new.get('action_sequence_list')
            MASK_actions = list()
            if len(actions) > 0:
                for action in actions:
                    MASK_action = list()
                    for dict in action:
                        MASK_dict = {}
                        for temp_key, temp_value in dict.items():
                            MASK_key = temp_key
                            MASK_value = list()
                            for token in temp_value:
                                if '-' in token and token != '-':
                                    token_new = token.replace('-','')
                                    if token_new in relation_maskID:
                                        MASK_value.append('-' + str(relation_maskID.get(token_new)))
                                else:
                                    if token in entity_maskID:
                                        MASK_value.append(entity_maskID.get(token))
                                    elif token in relation_maskID:
                                        MASK_value.append(relation_maskID.get(token))
                                    elif token in type_maskID:
                                        MASK_value.append(type_maskID.get(token))
                                    elif token in special_counting_characters:
                                        MASK_value.append(token)
                            MASK_dict.setdefault(MASK_key, MASK_value)
                        MASK_action.append(MASK_dict)
                    MASK_actions.append(MASK_action)
            question_info_new.setdefault('mask_action_sequence_list', MASK_actions)
            question_dict.setdefault(ID_string, question_info_new)
        count += 5
    return question_dict

# Get training data for sequence2sequence.
def getTrainingDatasetForPytorch():
    fwTrainQ = open('../../data/auto_QA_data/mask/PT_train.question', 'w', encoding="UTF-8")
    fwTrainA = open('../../data/auto_QA_data/mask/PT_train.action', 'w', encoding="UTF-8")
    fwTestQ = open('../../data/auto_QA_data/mask/PT_test.question', 'w', encoding="UTF-8")
    fwTestA = open('../../data/auto_QA_data/mask/PT_test.action', 'w', encoding="UTF-8")
    fwQuestionDic = open('../../data/auto_QA_data/mask/dic_py.question', 'w', encoding="UTF-8")
    fwActionDic = open('../../data/auto_QA_data/mask/dic_py.action', 'w', encoding="UTF-8")
    questionSet = set()
    actionSet = set()
    with open("../../data/auto_QA_data/CSQA_ANNOTATIONS_full.json", 'r', encoding="UTF-8") as load_f:
        count = 1
        train_action_string_list, test_action_string_list, train_question_string_list, test_question_string_list = list(), list(), list(), list()
        dict_list = list()
        load_dict = json.load(load_f)
        for key, value in load_dict.items():
            try:
                actions = eval(str(value['mask_action_sequence_list']))
            except SyntaxError:
                pass
            if len(actions) > 0:
                count += 1
                action_string = ''
                action = actions[0]
                for dict in action:
                    for temp_key, temp_value in dict.items():
                        action_string += temp_key + ' ( '
                        for token in temp_value:
                            if '-' in token:
                                token = '- ' + token.replace('-','')
                            action_string += str(token) + ' '
                        action_string += ') '
                question_string = '<E> '
                entities = value['entity_mask']
                if len(entities) > 0:
                    for entity_key, entity_value in entities.items():
                        if str(entity_value) != '':
                            question_string += str(entity_value) + ' '
                question_string += '</E> <R> '
                relations = value['relation_mask']
                if len(relations) > 0:
                    for relation_key, relation_value in relations.items():
                        if str(relation_value) !='':
                            question_string += str(relation_value) + ' '
                question_string += '</R> <T> '
                types = value['type_mask']
                if len(types) > 0:
                    for type_key, type_value in types.items():
                        if str(type_value) !='':
                            question_string += str(type_value) + ' '
                question_string += '</T> '
                question_token = str(value['question']).lower().replace('?', '')
                question_token = question_token.replace(',', ' ')
                question_token = question_token.replace(':', ' ')
                question_token = question_token.replace('(', ' ')
                question_token = question_token.replace(')', ' ')
                question_token = question_token.replace('"', ' ')
                question_token = question_token.strip()
                question_string += question_token
                question_string = question_string.strip() + '\n'

                action_string = action_string.strip() + '\n'
                action_tokens = action_string.strip().split(' ')
                action_tokens_set = set(action_tokens)
                actionSet = actionSet.union(action_tokens_set)

                question_tokens = question_string.strip().split(' ')
                question_tokens_set = set(question_tokens)
                questionSet = questionSet.union(question_tokens_set)

                dict_temp = {}
                dict_temp.setdefault('q', str(key) + ' ' + question_string)
                dict_temp.setdefault('a', str(key) + ' ' + action_string)
                dict_list.append(dict_temp)

    random.seed(SEED)
    random.shuffle(dict_list)
    # train_size = int(len(dict_list) * 0.95)
    train_size = int(len(dict_list))
    for i, item in enumerate(dict_list):
        if i < train_size:
            train_action_string_list.append(item.get('a'))
            train_question_string_list.append(item.get('q'))
        elif train_size <= i:
            test_action_string_list.append(item.get('a'))
            test_question_string_list.append(item.get('q'))
    fwTrainQ.writelines(train_question_string_list)
    fwTrainA.writelines(train_action_string_list)
    fwTestQ.writelines(test_question_string_list)
    fwTestA.writelines(test_action_string_list)
    fwTrainQ.close()
    fwTrainA.close()
    fwTestQ.close()
    fwTestA.close()

    questionList = list()
    for item in questionSet:
        temp = str(item) + '\n'
        if temp != '\n':
            questionList.append(temp)
    actionList = list()
    for item in actionSet:
        temp = str(item) + '\n'
        if temp != '\n':
            actionList.append(temp)
    fwQuestionDic.writelines(questionList)
    fwActionDic.writelines(actionList)
    print ("Getting SEQUENCE2SEQUENCE processDataset is done!")

# Get training data for REINFORCE (using annotation instead of denotation as reward).
def getTrainingDatasetForRl():
    fwTrainQ = open('../../data/auto_QA_data/mask/RL_train.question', 'w', encoding="UTF-8")
    fwTrainA = open('../../data/auto_QA_data/mask/RL_train.action', 'w', encoding="UTF-8")
    fwTestQ = open('../../data/auto_QA_data/mask/RL_test.question', 'w', encoding="UTF-8")
    fwTestA = open('../../data/auto_QA_data/mask/RL_test.action', 'w', encoding="UTF-8")
    fwQuestionDic = open('../../data/auto_QA_data/mask/dic_rl.question', 'w', encoding="UTF-8")
    fwActionDic = open('../../data/auto_QA_data/mask/dic_rl.action', 'w', encoding="UTF-8")
    fwNoaction = open('../../data/auto_QA_data/mask/no_action_question.txt', 'w', encoding="UTF-8")
    no_action_question_list = list()
    questionSet = set()
    actionSet = set()
    with open("../../data/auto_QA_data/CSQA_ANNOTATIONS_full.json", 'r', encoding="UTF-8") as load_f:
        count = 1
        train_action_string_list, test_action_string_list, train_question_string_list, test_question_string_list = list(), list(), list(), list()
        dict_list = list()
        load_dict = json.load(load_f)
        for key, value in load_dict.items():
            try:
                actions = eval(str(value['mask_action_sequence_list']))
            except SyntaxError:
                pass
            if len(actions) > 0:
                action_string_list = list()
                count += 1
                for action in actions:
                    action_string = ''
                    for dict in action:
                        for temp_key, temp_value in dict.items():
                            action_string += temp_key + ' ( '
                            for token in temp_value:
                                if '-' in token:
                                    token = '- ' + token.replace('-','')
                                action_string += str(token) + ' '
                            action_string += ') '
                    action_string = action_string.strip() + '\n'
                    action_string_list.append(action_string)
                question_string = '<E> '
                entities = value['entity_mask']
                if len(entities) > 0:
                    for entity_key, entity_value in entities.items():
                        if str(entity_value) != '':
                            question_string += str(entity_value) + ' '
                question_string += '</E> <R> '
                relations = value['relation_mask']
                if len(relations) > 0:
                    for relation_key, relation_value in relations.items():
                        if str(relation_value) !='':
                            question_string += str(relation_value) + ' '
                question_string += '</R> <T> '
                types = value['type_mask']
                if len(types) > 0:
                    for type_key, type_value in types.items():
                        if str(type_value) !='':
                            question_string += str(type_value) + ' '
                question_string += '</T> '
                question_token = str(value['question']).lower().replace('?', '')
                question_token = question_token.replace(',', ' ')
                question_token = question_token.replace(':', ' ')
                question_token = question_token.replace('(', ' ')
                question_token = question_token.replace(')', ' ')
                question_token = question_token.replace('"', ' ')
                question_token = question_token.strip()
                question_string += question_token
                question_string = question_string.strip() + '\n'

                question_tokens = question_string.strip().split(' ')
                question_tokens_set = set(question_tokens)
                questionSet = questionSet.union(question_tokens_set)

                action_withkey_list = list()
                if len(action_string_list) > 0:
                    for action_string in action_string_list:
                        action_tokens = action_string.strip().split(' ')
                        action_tokens_set = set(action_tokens)
                        actionSet = actionSet.union(action_tokens_set)
                        action_withkey_list.append(str(key) + ' ' + action_string)

                dict_temp = {}
                dict_temp.setdefault('q', str(key) + ' ' + question_string)
                dict_temp.setdefault('a', action_withkey_list)
                dict_list.append(dict_temp)
            elif len(actions) == 0:
                no_action_question_list.append(str(key) + ' ' + str(value['question']).lower().replace('?', '').strip() + '\n')

    random.seed(SEED)
    random.shuffle(dict_list)
    train_size = int(len(dict_list))
    # train_size = int(len(dict_list) * 0.95)
    for i, item in enumerate(dict_list):
        if i < train_size:
            for action_string in item.get('a'):
                train_action_string_list.append(action_string)
            train_question_string_list.append(item.get('q'))
        elif train_size <= i:
            for action_string in item.get('a'):
                test_action_string_list.append(action_string)
            test_question_string_list.append(item.get('q'))
    fwTrainQ.writelines(train_question_string_list)
    fwTrainA.writelines(train_action_string_list)
    fwTestQ.writelines(test_question_string_list)
    fwTestA.writelines(test_action_string_list)
    questionList = list()
    for item in questionSet:
        temp = str(item) + '\n'
        if temp != '\n':
            questionList.append(temp)
    actionList = list()
    for item in actionSet:
        temp = str(item) + '\n'
        if temp != '\n':
            actionList.append(temp)
    fwQuestionDic.writelines(questionList)
    fwActionDic.writelines(actionList)
    fwNoaction.writelines(no_action_question_list)
    fwTrainQ.close()
    fwTrainA.close()
    fwTestQ.close()
    fwTestA.close()
    fwQuestionDic.close()
    fwActionDic.close()
    fwNoaction.close()
    print ("Getting RL processDataset is done!")

def getShareVocabulary():
    questionVocab = set()
    actionVocab = set()
    actionVocab_list = list()
    with open('../../data/auto_QA_data/mask/dic_py.question', 'r', encoding="UTF-8") as infile1, open('../../data/auto_QA_data/mask/dic_rl.question', 'r', encoding="UTF-8") as infile2, open('../../data/auto_QA_data/mask/dic_rl_tr.question', 'r', encoding="UTF-8") as infile3:
        count = 0
        while True:
            lines_gen = list(islice(infile1, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                token = line.strip()
                questionVocab.add(token)
            count = count + 1
            print(count)
        count = 0
        while True:
            lines_gen = list(islice(infile2, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                token = line.strip()
                questionVocab.add(token)
            count = count + 1
            print(count)
        count = 0
        while True:
            lines_gen = list(islice(infile3, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                token = line.strip()
                questionVocab.add(token)
            count = count + 1
            print(count)
    with open('../../data/auto_QA_data/mask/dic_py.action', 'r', encoding="UTF-8") as infile1, open('../../data/auto_QA_data/mask/dic_rl.action', 'r', encoding="UTF-8") as infile2:
        count = 0
        while True:
            lines_gen = list(islice(infile1, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                token = line.strip()
                actionVocab.add(token)
            count = count + 1
            print(count)
        count = 0
        while True:
            lines_gen = list(islice(infile2, LINE_SIZE))
            if not lines_gen:
                break
            for line in lines_gen:
                token = line.strip()
                actionVocab.add(token)
            count = count + 1
            print(count)
    action_size = 0
    for word in actionVocab:
        if word not in questionVocab and word not in special_characters:
            actionVocab_list.append(word)
            action_size += 1
        elif word in special_characters:
            actionVocab_list.append(word)
            action_size += 1
            if word in questionVocab:
                questionVocab.remove(word)
    questionVocab_list = list(questionVocab)
    share_vocab_list = actionVocab_list + questionVocab_list
    for i in range(len(share_vocab_list)):
        share_vocab_list[i] = share_vocab_list[i] + '\n'
    fw = open('../../data/auto_QA_data/share.question', 'w', encoding="UTF-8")
    fw.writelines(share_vocab_list)
    fw.close()
    print("Writing SHARE VOCAB is done!")
    return action_size

# Run getAllQuestionsAndActions to get the JSON file which contains all information related to questions.
# Run getAllQustionsAndAnswers() to get the JSON file which contains all information and answers related to questions.
# Run getTrainingDatasetForPytorch() to get training and test processDataset for seq2seq model training.
# Run getTrainingDatasetForRl() to get training and test processDataset for REINFORCE-seq2seq model training.
# Run getShareVocabulary() to get vocabulary in all training processDataset.
if __name__ == "__main__":
    # getAllQuestionsAndActions()
    # getTrainingDatasetForPytorch()
    # getTrainingDatasetForRl()
    getAllQustionsAndAnswers()
    print(getShareVocabulary())


