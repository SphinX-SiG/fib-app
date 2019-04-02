import os
import pathlib

import yaml

CONFIG_PATH = pathlib.Path(__file__).parent / 'fibonacci.yaml'


def get_config(path):
    with open(path) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    return config


config = get_config(CONFIG_PATH).get(os.environ.get('FIBAPP_ENV'))
