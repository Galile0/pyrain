import json
from replay_parser import ReplayParser


if __name__ == '__main__':
    header = ReplayParser("testfiles/r1.replay").parse_file()
    with open('parsed.json', 'w') as outfile:
        json.dump(header, outfile, indent=4)