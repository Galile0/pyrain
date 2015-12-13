import json
import pprint
import pickle

from pyrope.frame import FrameParsingError
from pyrope.netstream_property_parsing import PropertyParsingError
from pyrope.replay import Replay


if __name__ == '__main__':
    # replay = Replay("testfiles/FD1D.replay")
    replay = Replay("testfiles/3BF9.replay")
    # replay = Replay("testfiles/C51C0.replay") # Thats a special one T_T
    try:
        replay.parse(parse_header=True, parse_netstream=True)
    except (PropertyParsingError, FrameParsingError) as e:
        print('\n')
        for arg in e.args:
            pprint.pprint(arg)
    # else:
    #     print(replay.get_actor_list())
    with open('header.json', 'w', encoding='utf-8') as outfile:
        json.dump(replay.header.parsed, outfile, indent=2, ensure_ascii=False)
    with open('netstream.json', 'w', encoding='utf-8') as outfile:
        # json.dump(replay.netstream.frames, outfile, indent=2, ensure_ascii=False)
        outfile.write(replay.netstream.to_json())
