import json
import os
import pprint
import pickle
from pyrope.frame import FrameParsingError
from pyrope.netstream_property_parsing import PropertyParsingError
from pyrope.replay import Replay
import time

if __name__ == '__main__':
    # filename = "91D6"
    # filename = "FD1D"
    filename = "3BF9"
    # filename = "C51C0"
    # filename = "C747"
    replay = Replay("testfiles/"+filename+".replay")

    try:
        start = time.time()
        replay.parse(parse_header=True, parse_netstream=True)
        delta = time.time() - start
        print("Shit Took:", delta)
    except (PropertyParsingError, FrameParsingError) as e:
        print('\n')
        for arg in e.args:
            pprint.pprint(arg)
    os.makedirs(filename, exist_ok=True)
    pickle.dump(replay.netstream, open(filename+'/netstream.pickle', 'wb'))
    with open(filename+'/keyframes.json', 'w', encoding='utf-8') as outfile:
        json.dump(replay.keyframes, outfile, indent=2, ensure_ascii=False)
    with open(filename+'/header.json', 'w', encoding='utf-8') as outfile:
        json.dump(replay.header.parsed, outfile, indent=2, ensure_ascii=False)
    with open(filename+'/netstream.json', 'w', encoding='utf-8') as outfile:
        outfile.write(replay.netstream.to_json())