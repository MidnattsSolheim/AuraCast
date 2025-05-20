import json
import argparse

with open("config.json") as f:
    _raw_config = json.load(f)

parser = argparse.ArgumentParser(description="Auracast Network Monitor")
parser.add_argument('--test', action='store_true', help='Enable testing mode')
args = parser.parse_args()

# Exported config
IS_TESTING = args.test
PCAP_FILE_PATH = _raw_config["PCAP_FILE_PATH"]
OUTPUT_DIR = _raw_config["OUTPUT_DIR"]
PHUE_IP_ADDRESS = _raw_config["PHUE_IP_ADDRESS"]
LIGHT_NAMES = _raw_config["LIGHT_NAMES"]
BASE_DIR = _raw_config["BASE_DIR_TEST"] if IS_TESTING else _raw_config["BASE_DIR_PROD"]
