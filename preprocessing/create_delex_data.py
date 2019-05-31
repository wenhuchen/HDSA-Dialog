# -*- coding: utf-8 -*-
import copy
import json
import os
import re
import shutil
import urllib
from collections import OrderedDict
from io import BytesIO
from zipfile import ZipFile
import numpy as np
from utils import delexicalize
from utils.nlp import normalize
import sqlite3
import numpy as np
from nltk.tokenize import word_tokenize

domains = ['restaurant', 'hotel', 'attraction', 'train', 'taxi', 'hospital', 'police', 'bus']

np.set_printoptions(precision=3)

np.random.seed(2)

# GLOBAL VARIABLES
DICT_SIZE = 400
MAX_LENGTH = 50

db = 'db/whole.db'
conn = sqlite3.connect(db)
dbs = conn.cursor()
    
def is_ascii(s):
    return all(ord(c) < 128 for c in s)

def delexicaliseReferenceNumber(sent, turn):
    """Based on the belief state, we can find reference number that
    during data gathering was created randomly."""
    if turn['metadata']:
        for domain in turn['metadata']:
            if turn['metadata'][domain]['book']['booked']:
                for slot in turn['metadata'][domain]['book']['booked'][0]:
                    if slot == 'reference':
                        val = '[' + domain + '_' + slot + ']'
                    else:
                        val = '[' + domain + '_' + slot + ']'
                    key = normalize(turn['metadata'][domain]['book']['booked'][0][slot])
                    sent = (' ' + sent + ' ').replace(' ' + key + ' ', ' ' + val + ' ')

                    # try reference with hashtag
                    key = normalize("#" + turn['metadata'][domain]['book']['booked'][0][slot])
                    sent = (' ' + sent + ' ').replace(' ' + key + ' ', ' ' + val + ' ')

                    # try reference with ref#
                    key = normalize("ref#" + turn['metadata'][domain]['book']['booked'][0][slot])
                    sent = (' ' + sent + ' ').replace(' ' + key + ' ', ' ' + val + ' ')
    return sent

def clean(string):
    return string.lower().replace("'", "''").strip()

def queryResultVenues(constraints, return_dict=False, bs=True):
    #results = []
    assert len(constraints) == 1
    for domain in constraints:
        sql_query = "select * from {}".format(domain)
        flag = True
        for key, val in constraints[domain]:
            if val == "" or val == "dont care" or val == 'not mentioned' or val == "don't care" or val == "dontcare" or val == "do n't care":
                pass
            else:
                if flag:
                    sql_query += " where "
                    val2 = clean(val)
                    if key == 'leaveat' and bs:
                        sql_query += r" " + key + " > " + r"'" + val2 + r"'"
                    elif key == 'arriveby' and bs:
                        sql_query += r" " +key + " < " + r"'" + val2 + r"'"
                    else:
                        sql_query += r" " + key + "=" + r"'" + val2 + r"'"
                    flag = False
                else:
                    val2 = clean(val)
                    if key == 'leaveat' and bs:
                        sql_query += r" and " + key + " > " + r"'" + val2 + r"'"
                    elif key == 'arriveby' and bs:
                        sql_query += r" and " + key + " < " + r"'" + val2 + r"'"
                    else:
                        sql_query += r" and " + key + "=" + r"'" + val2 + r"'"

        cursor = dbs.execute(sql_query)
        result = cursor.fetchall()
        
        if result:
            if return_dict:
                header = list(map(lambda x: x[0], cursor.description))
                result = {k:v for k,v in zip(header, result[0])}
            else:
                result = [tuple(map(lambda x: x[0], cursor.description))] + result           
            return result
        else:
            if return_dict:
                return {}
            else:
                return []

def createDelexData(sent, sent_act, bs, dic, turn, option):
    # normalization, split and delexicalization of the sentence
    sent = normalize(sent)
    words = sent.split()
    sent = delexicalize.delexicalise(' '.join(words), dic) 
    # parsing reference number GIVEN belief state
    sent = delexicaliseReferenceNumber(sent, turn)
    # changes to numbers only here  
    digitpat = re.compile('\d+')
    sent = re.sub(digitpat, '[value_count]', sent)
    if option == 'user':
        sent = fixDelex(sent, None, bs)
    if option == 'sys':
        sent = fixDelex(sent, sent_act, None)
    
    return sent.strip()

def lower(dictionary):
    new_dictionary = {}
    for k in dictionary:
        for key, val in dictionary[k]:
            if key != "none":
                if k.lower().split('-')[0] in domains:
                    new_dictionary["domain-{}-{}".format(k.lower(), key.lower())] = val.lower().strip()
                else:
                    new_dictionary["{}-{}".format(k.lower(), key.lower())] = val.lower().strip()
            else:
                if k.lower().split('-')[0] in domains:
                    new_dictionary["domain-{}".format(k.lower())] = val.lower().strip()
                else:
                    new_dictionary["{}".format(k.lower())] = val.lower().strip()
    return new_dictionary

def tok(string):
    tokens = " ".join(word_tokenize(string.lower()))
    return tokens

def print_data(data, act_data, dic):
    infos = []
    mentioned = []
    for i in range(0, len(data), 2):
        tmp_info = {}
        tmp_info['user_orig'] = tok(data[i]['text'])
        tmp_info['sys_orig'] = tok(data[i+1]['text'])
        query_result = []
        if str(i // 2 + 1) not in act_data:
            tmp_info['user'] = createDelexData(data[i]['text'], None, None, dic, data[i+1], "user")
            tmp_info["sys"] = createDelexData(data[i + 1]['text'], None, None, dic, data[i+1], "sys")
            
            tmp_info["act"] = {}
            tmp_info['BS'] = {}
            tmp_info['KB'] = len(query_result)
            tmp_info['source'] = {}
        else:
            local_act = act_data[str(i // 2 + 1)]
            
            if isinstance(act_data[str(i // 2 + 1)], dict):
                tmp_info["act"] = lower(local_act)
            else:
                tmp_info["act"] = {}
                local_act = {}
            
            meta = data[i + 1]['metadata']
            constraints = {}
            for domain in meta:
                if domain not in domains:
                    print("exception, domain", domain)
                    continue
                for k in meta[domain]['semi']:
                    if meta[domain]['semi'][k] != "" and "mentioned" not in meta[domain]['semi'][k] and "care" not in meta[domain]['semi'][k]:
                        if domain not in mentioned:
                            mentioned.append(domain)
                        if domain in constraints:
                            constraints[domain].append([k, meta[domain]['semi'][k]])
                        else:
                            constraints[domain] = [[k, meta[domain]['semi'][k]]]          

            tmp_info['BS'] = constraints
            if len(constraints):
                if len(constraints) > 1:
                    for j in range(len(mentioned) - 1, -1, -1):
                        if mentioned[j] in constraints:
                            constraints = {mentioned[j]: constraints[mentioned[j]]}
                            break
                if 'taxi' in constraints:
                    tmp_info["KB"] = len(query_result)
                else:
                    query_result = queryResultVenues(constraints, bs=True)
                    tmp_info["KB"] = len(query_result)
            else:
                tmp_info["KB"] = len(query_result)
            
            source = act2language(tmp_info['act'], query_result)
            tmp_info['source'] = source
            tmp_info['user'] = createDelexData(data[i]['text'], None, constraints, dic ,data[i+1], "user")
            tmp_info["sys"] = createDelexData(data[i + 1]['text'], local_act, None, dic, data[i+1], "sys")
            
        infos.append(tmp_info)
    return infos

def in_list(key, lis):
    for l in lis:
        if key in l:
            return True
    return False

def fixDelex(sent, dialog_act, bs):
    """Given system dialogue acts fix automatic delexicalization."""
    back_sent = copy.copy(sent)
    if dialog_act is not None:
        keys = dialog_act.keys()
        done = False
        #for k, act in dialog_act.items():
        if in_list("Attraction", keys):
            if 'restaurant_' in sent and not in_list("Restaurant", keys):
                sent = sent.replace("restaurant_", "attraction_")
                done = True
            if 'hotel_' in sent and not in_list("Hotel", keys):
                sent = sent.replace("hotel_", "attraction_")
                done = True
        if in_list("Hotel", keys):
            if 'attraction_' in sent and not in_list("Attraction", keys):
                sent = sent.replace("attraction_", "hotel_")
                done = True
            if 'restaurant_' in sent and not in_list("Restaurant", keys):
                sent = sent.replace("restaurant_", "hotel_")
                done = True
        if in_list('Restaurant', keys):
            if 'attraction_' in sent and not in_list("Attraction", keys):
                sent = sent.replace("attraction_", "restaurant_")
                done = True
            if 'hotel_' in sent and not in_list("Hotel", keys):
                sent = sent.replace("hotel_", "restaurant_")
                done = True   
    
        if in_list("Train", keys):
            words = sent.split(' ')
            tmp_time, tmp_place = None, None
            for i, word in enumerate(words):
                if "leav" in word or "depart" in word or "from" in word:
                    tmp_time = "[train_leaveat]"
                    tmp_place = "[train_departure]"
                if "arriv" in word or "get" in word or "go" in word or "to" in word or "desti" in word:
                    tmp_time = "[train_arriveby]"
                    tmp_place = "[train_destination]"
                if word == "[value_time]":
                    if tmp_time is not None:
                        words[i] = tmp_time
                    else:
                        words[i] = "[train_leaveat]"
                if word == "[value_place]":
                    if tmp_place is not None:
                        words[i] = tmp_place
                    else:
                        words[i] = "[train_departure]"
                if word == "[value_day]":
                    words[i] = "[train_day]"
            sent = " ".join(words)
    
    if bs is not None:
        keys = bs.keys()
        done = False
        #for k, act in dialog_act.items():
        if "attraction" in keys:
            if 'restaurant_' in sent and "restaurant" not in keys:
                sent = sent.replace("restaurant_", "attraction_")
                done = True
            if 'hotel_' in sent and "hotel" not in keys:
                sent = sent.replace("hotel_", "attraction_")
                done = True
        if "hotel" in keys:
            if 'attraction_' in sent and "attraction" not in keys:
                sent = sent.replace("attraction_", "hotel_")
                done = True            
            if 'restaurant_' in sent and "restaurant" not in keys:
                sent = sent.replace("restaurant_", "hotel_")
                done = True        
        if 'restaurant' in keys:
            if 'attraction_' in sent and "attraction" not in keys:
                sent = sent.replace("attraction_", "restaurant_")
                done = True                
            if 'hotel_' in sent and "hotel" not in keys:
                sent = sent.replace("hotel_", "restaurant_")
                done = True
        
        if "train" in keys:
            words = sent.split(' ')
            tmp_time, tmp_place = None, None            
            for i, word in enumerate(words):
                if "leav" in word or "depart" in word or "from" in word:
                    tmp_time = "[train_leaveat]"
                    tmp_place = "[train_departure]"
                if "arriv" in word or "get" in word or "go" in word or "to" in word or "desti" in word:
                    tmp_time = "[train_arriveby]"
                    tmp_place = "[train_destination]"
                if word == "[value_time]":
                    if tmp_time is not None:
                        words[i] = tmp_time
                    else:
                        words[i] = "[train_leaveat]"
                if word == "[value_place]":
                    if tmp_place is not None:
                        words[i] = tmp_place
                    else:
                        words[i] = "[train_departure]"
                if word == "[value_day]":
                    words[i] = "[train_day]"  
            sent = " ".join(words)
    
    sent = sent.replace("hotel_food", "restaurant_food")
    sent = sent.replace("hotel_food", "restaurant_food")
    
    return sent

def create_vocab():    
    with open('../data/train.json') as f:
        data = json.load(f)
    with open('../data/val.json') as f:
        data_val = json.load(f)
    with open('../data/test.json') as f:
        data_test = json.load(f)
    
    act_ontology = []
    words = []
    for dialog in data + data_val + data_test:
        dialog = dialog['info']
        if not isinstance(dialog, list):
            raise ValueError
        for turn in dialog:
            for word in turn['sys'].split():
                words.append(word)
            for word in turn['user'].split():
                words.append(word)
            for key in turn['act']:
                #words.append(key)
                #elems = key.split('-')
                #for i in range(len(elems)):
                #    words.append('-'.join(elems[:i+1]))
                if key not in act_ontology:
                    act_ontology.append(key)
    
    from collections import Counter
    
    counter = Counter(words).most_common()
    
    import re
    word_dict = {"[PAD]": 0, "[EOS]": 1, "[SOS]": 2, "[UNK]": 3, "[CLS]": 4, "[SEP]": 5}
    
    for word, app in counter:
        if app >= 2:
            if "[value_count]" in word and len(word) != len("[value_count]"):
                pass
            else:
                word_dict[word] = len(word_dict)
            
    print(len(word_dict))
    iword_dict = {y:x for x,y in word_dict.items()}
    
    vocab = {'vocab': word_dict, 'rev': iword_dict}
    
    with open("../data/vocab.json", "w") as f:
        json.dump(vocab, f, indent=2)
    
    act_ontology = sorted(act_ontology)
    with open('../data/act_ontology.json', 'w') as f:
        json.dump(act_ontology, f, indent=2)    

def act2language(act, query_results):
    constraint = {}
    ref = None
    source = {}
    domain = None
    for key in act:
        if len(key.split('-')) == 4:
            _, domain, action, slot = key.split('-')
            if domain not in constraint:
                constraint[domain] = []
            if action in ['inform', 'recommend', 'select', 'offerbooked']:
                if slot in ['choice', 'fee', 'people', 'open', 'ticket', 'time']:
                    continue
                elif slot == "addr":
                    slot = 'address'
                elif slot == "post":
                    slot = 'postcode'
                elif slot == "ref":
                    ref = act[key]
                    continue
                elif slot == "car":
                    slot = "type"
                elif slot == 'dest':
                    slot = 'destination'
                elif domain == 'train' and slot == 'id':
                    slot = 'trainid'
                elif slot == 'leave':
                    slot = 'leaveat'
                elif slot == 'arrive':
                    slot = 'arriveby'
                elif slot == 'price':
                    slot = 'pricerange'
                elif slot == 'depart':
                    slot = 'departure'
                elif slot == 'name':
                    slot = 'name'
                elif slot == 'type':
                    slot = 'type'
                elif slot == 'area':
                    slot = 'area'
                elif slot == 'parking':
                    slot = 'parking'
                elif slot == 'internet':
                    slot = 'internet'
                elif slot == 'stars':
                    slot = 'stars'
                elif slot == 'food':
                    slot = 'food'
                elif slot == 'phone':
                    slot = 'phone'
                elif slot == 'day':
                    slot = 'day'
                else:
                    print(key)
                    continue
                constraint[domain].append((slot, act[key].strip()))
        elif "ref" in key:
            for domain in domains:
                source['[{}_reference]'.format(domain)] = act[key]
    if len(constraint) == 1:        
        result = queryResultVenues(constraint, bs=False, return_dict=True)
        domain = list(constraint.keys())[0]
        if result:
            if ref is not None:
                result['reference'] = ref
            else:
                result['reference'] = "xxxxxxxx"
            source = {"[{}_{}]".format(domain, k):v for k, v in result.items()}
    
    if not source:
        if query_results and domain is not None:
            source = {"[{}_{}]".format(domain, k):v for k, v in zip(query_results[0], query_results[1])}
                
    return source
    
def process_db():
    sfiles = ["attraction_db_orig.json", "bus_db_orig.json", "hospital_db_orig.json", "police_db_orig.json", 
             "hotel_db_orig.json", "restaurant_db_orig.json", "train_db_orig.json", "taxi_db_orig.json"]
    
    wfiles = ["attraction_db.json", "bus_db.json", "hospital_db.json", "police_db.json", 
             "hotel_db.json", "restaurant_db.json", "train_db.json", "taxi_db.json"]
    
    exceptions = ["introduction", "single", "signature", "takesbookings", "location", "openhours"]
    with open('/tmp/db.sql', 'w') as f:
        for sfile, wfile in zip(sfiles, wfiles):
            data = json.load(open("db/" + sfile))
            output = []
            for i, item in enumerate(data):
                if i == 0:
                    header = "CREATE TABLE IF NOT EXISTS {} (\n".format(sfile.split("_")[0])
                    col_names = [k for k in item.keys() if k not in exceptions and (isinstance(item[k], str) or 
                                                                                    isinstance(item[k], int))]
                    if "hospital" in sfile:
                        col_names.append("name")
                        col_names.append("postcode")
                        col_names.append("address")
                    
                    if "police" in sfile:
                        col_names.append("postcode")
                         
                    if "id" not in col_names:
                        col_names.append("id")
                    col_length = {k:0 for k in col_names}
                    content_part = ""                    
                
                if "hospital" in sfile:
                    item["name"] = "Addenbrookes Hospital"
                    item["postcode"] = "CB20QQ"
                    item["address"] = "Hills Rd"
                
                if "police" in sfile:
                    item["postcode"] = "CB11JG"
                     
                item['id'] = str(i)
                for col_name in col_names:
                    if col_name not in item:
                        item[col_name] = "unkown"
                
                output.append({k.lower():item[k].lower() for k in col_names})
                tmp = tuple(item[k] for k in col_names)
                tmp = json.dumps(tmp)
                tmp = "(" + tmp[1:-1] + ")"
                
                if i != 0:
                    content_part += ",\n" + tmp
                else:
                    content_part += tmp
                    
                for col_name in col_names:
                    if len(str(item[col_name])) > col_length[col_name]:
                        col_length[col_name] = len(item[col_name])
                        
            content_part += ";"
                
            for i, col_name in enumerate(col_names):
                if i != len(col_names) - 1:
                    header += "{} VARCHAR({}) NULL,\n".format(col_name.lower(), col_length[col_name])
                else:
                    header += "{} VARCHAR({}) NULL);".format(col_name.lower(), col_length[col_name])
            
            print(header, file=f)
            print("", file=f)
            print("INSERT INTO {} VALUES".format(sfile.split("_")[0]), file=f)
            print(content_part.lower(), file=f)
            print("", file=f)
    
            with open("db/" + wfile, 'w') as fw:
                json.dump(output, fw, indent=2)
 
def main():
    with open('data.json') as f:
        whole_data = json.load(f)
        
    with open('dialogue_acts.json') as f:
        whole_act_data = json.load(f)       
    
    dic = delexicalize.prepareSlotValuesIndependent()
    
    testListFile = []
    fin = open('testListFile.json')
    for line in fin:
        testListFile.append(line[:-1])
    fin.close()
    
    valListFile = []
    fin = open('valListFile.json')
    for line in fin:
        valListFile.append(line[:-1])
    fin.close()    
    
    with open('../data/train.json', 'w') as f_train:
        with open('../data/val.json', 'w') as f_val:
            with open('../data/test.json', 'w') as f_test:    
                train_turns = []
                val_turns = []
                test_turns = []
                num = 0
                for k in whole_data:
                    data = whole_data[k]['log']
                    turn = k.split('.')[0]
                    act_data = whole_act_data[turn]
    
                    if k in testListFile:
                        test_turns.append({"file":turn, "info":print_data(data, act_data, dic)})
                    elif k in valListFile:
                        val_turns.append({"file":turn, "info":print_data(data, act_data, dic)})
                    else:
                        train_turns.append({"file":turn, "info":print_data(data, act_data, dic)})
                    num += 1
                    print("Finished {}/{}".format(num, len(whole_data)))
                
                json.dump(train_turns, f_train, indent=2)
                json.dump(val_turns, f_val, indent=2)
                json.dump(test_turns, f_test, indent=2)

  
if __name__ == "__main__":
    main()
    create_vocab()
    #process_db()
    #add_source('data/val.json')
    #add_source('data/test.json')
