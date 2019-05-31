from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import csv
import os
import time
import json
import numpy as np
import torch
import logging
from transformer import Constants
import copy
import json

logger = logging.getLogger(__name__)

def get_batch(data_dir, option, max_seq_length):
    examples = []
    prev_sys = None
    num = 0
    
    if option == 'train':
        with open('{}/train.json'.format(data_dir)) as f:
            source = json.load(f)
    elif option == 'dev':
        with open('{}/val.json'.format(data_dir)) as f:
            source = json.load(f)
    else:
        with open('{}/test.json'.format(data_dir)) as f:
            source = json.load(f)
    
    fw = open('data/{}.tsv'.format(option), 'w')
    logger.info("Loading total {} dialogs".format(len(source)))
    for num_dial, dialog_info in enumerate(source):
        hist = []
        hist_segment = []
        dialog_file = dialog_info['file']
        dialog = dialog_info['info']
        sys = "conversation start"
        for turn_num, turn in enumerate(dialog):
            #user = [vocab[w] if w in vocab else vocab['<UNK>'] for w in turn['user'].split()]
            user = turn['user_orig']
            hierarchical_act_vecs = [0 for _ in range(Constants.act_len)]
            source = []
            for k, v in turn['source'].items():
                source.extend([k.split('_')[1][:-1], 'is', v])
            source = " ".join(source)
            if len(source) == 0:
                source = "no information"
            if turn['act'] != "None":
                for w in turn['act']:
                    d, f, s = w.split('-')
                    hierarchical_act_vecs[Constants.domains.index(d)] = 1
                    #for _ in Constants.function_imapping[w]:
                    hierarchical_act_vecs[len(Constants.domains) + Constants.functions.index(f)] = 1                        
                    #for _ in Constants.arguments_imapping[w]:
                    hierarchical_act_vecs[len(Constants.domains) + len(Constants.functions) + Constants.arguments.index(s)] = 1
            print("{}\t{}\t{}\t{}\t{}\t{}".format(dialog_file, str(turn_num), source, sys, user, json.dumps(hierarchical_act_vecs)), file=fw)
            sys = turn['sys_orig']
            

    fw.close()
if __name__ == "__main__":
    get_batch('data/', 'train', 60)
    get_batch('data/', 'dev', 60)
    get_batch('data/', 'test', 60)

