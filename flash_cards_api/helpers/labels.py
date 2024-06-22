import json
from sklearn.preprocessing import LabelEncoder


def write_label_file(labels):
    with open('labels.json', 'w') as file:
        file.write(json.dumps(labels))

def read_label_file():
    with open('labels.json', 'r') as file:
        labels = (json.loads(file.read()))
    return labels


def get_label_encoder():
    labels = read_label_file()
    le = LabelEncoder()
    le.fit(labels)
    return le
