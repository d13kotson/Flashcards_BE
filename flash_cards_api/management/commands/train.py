from django.core.management.base import BaseCommand, CommandError

import numpy as np
import cv2
import os

from sklearn.utils import shuffle

from flash_cards_api.helpers.labels import write_label_file, get_label_encoder
from flash_cards_api.helpers.model import construct_model, train_model, save_model


def get_image(file):
    image = cv2.imread(file)
    image = cv2.resize(image, (64, 64))
    image = np.array(image, dtype=np.float32)
    image = image / 255
    return image


def get_files(path):
    data = []
    labels = []
    for subdir, dirs, files in os.walk(path):
        if subdir == path:
            continue
        label = int(subdir[-4:], 16)
        if len(files) > 20:
            for file in files:
                image = os.path.join(subdir, file)
                data.append(image)
                labels.append(label)

    write_label_file(labels)
    data_sh, labels_sh = shuffle(data, labels, random_state=42)

    return data_sh, labels_sh


def get_data(files, labels, start, size):
    data = list()
    for file in files[start:start+size]:
        data.append(get_image(file))
    data = np.array(data)
    labels = np.array(labels[start:start+size])

    le = get_label_encoder()
    labels = le.transform(labels)

    data_sh, labels_sh = shuffle(data, labels, random_state=42)
    return data_sh, labels_sh


class Command(BaseCommand):
    help = ''

    def add_arguments(self, parser):
        parser.add_argument('datapath', type=str)
        parser.add_argument('chunk-size', type=int)

    def handle(self, datapath, *args, **options):
        chunk_size = options.get('chunk-size', None)
        files, labels = get_files(datapath)

        model = construct_model()
        index = 0
        while index < len(labels):
            data, labels_set = get_data(files, labels, index, chunk_size)
            print(f'Training on {index + len(data)} items out of {len(labels)}.')
            history = train_model(model, data, labels_set)
            index += chunk_size
        save_model(model)
