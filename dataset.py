import cPickle as pickle
import os
import numpy as np
import torch
from torch.utils.serialization import load_lua
from collections import namedtuple
from nltk import word_tokenize

def get_file_list(folder):
    file_list = []
    for root, dirs, files in os.walk(folder):
        for ff in files:
            file_list.append(ff)
    return file_list


class Dataset(object):
    def __init__(self, data_folder, buffer_size=10000):
        self.data_folder = data_folder
        self.buffer_size = buffer_size
        self.captions = pickle.load(open(os.path.join(data_folder, 'captions.pkl'), 'rb'))
        self.train_files = get_file_list(os.path.join(data_folder, 'train'))
        self.val_files = get_file_list(os.path.join(data_folder, 'val'))
        self.test_files = get_file_list(os.path.join(data_folder, 'test'))

    def examples(self, file_list, folder, shuffle=False):
        _file_list = list(file_list)
        if shuffle:
            np.random.shuffle(_file_list)

        for f_name in _file_list:
            captions = self.captions[f_name.split('.')[0]]
            captions = [['<s>'] + word_tokenize(caption) + ['</s>'] for caption in captions]
            img_encoding = load_lua(os.path.join(self.data_folder, folder, f_name))

            yield img_encoding, captions

    def train_examples(self, shuffle=False):
        return self.examples(self.train_files, 'train/', shuffle=shuffle)

    def valid_examples(self, shuffle=False):
        return self.examples(self.val_files, 'val/', shuffle=shuffle)

    def test_examples(self, shuffle=False):
        return self.examples(self.test_files, 'test/', shuffle=shuffle)

    def batch_iter(self, category, batch_size, shuffle=False):
        if category == 'train':
            exg_iter = self.train_examples(shuffle=shuffle)
        elif category == 'val':
            exg_iter = self.valid_examples(shuffle=shuffle)
        else:
            exg_iter = self.test_examples(shuffle=shuffle)
        examples_buffer = []

        while True:
            for i in xrange(self.buffer_size):
                try:
                    item = next(exg_iter)
                    examples_buffer.append(item)
                except StopIteration:
                    pass

            batch_num = int(np.ceil(len(examples_buffer) / float(batch_size)))
            for batch_id in xrange(batch_num):
                batch_items = examples_buffer[batch_id * batch_size: (batch_id + 1) * batch_size]
                yield batch_items

            del examples_buffer[:]