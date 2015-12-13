import json
from pyrope.replay import Replay


if __name__ == '__main__':
    replay = Replay("testfiles/FD1D.replay")
    replay.parse(parse_header=True, parse_netstream=True)
    # with open('parsed.json', 'w', encoding='utf-8') as outfile:
    #     json.dump(header, outfile, indent=4, ensure_ascii=False)
    print("That shit's just to much")
