import json
import os
import pprint
import pickle
from pyrope.frame import FrameParsingError
from pyrope.netstream_property_parsing import PropertyParsingError
from pyrope.replay import Replay
import time
from threading import Thread, Event
from queue import Queue

if __name__ == '__main__':
    # filename = "91D6"
    # filename = "FD1D"
    filename = "3BF9"
    # filename = "C51C0"
    # filename = "C747"
    # filename = "0FCD"
    replay = Replay("testfiles/"+filename+".replay")

    try:
        start = time.time()

        status = Queue()
        stop = Event()
        thread = Thread(target=replay.parse_netstream, args=(status, stop))
        thread.start()
        while True:
            if status.empty():
                time.sleep(0.1)
                continue
            i = status.get()
            if i=='done':
                break
            if i=='exception':
                exc = status.get()
                raise exc
            if i % 100 == 0:
                print(i)
        delta = time.time() - start
        print("Shit Took:", delta)
    except (PropertyParsingError, FrameParsingError) as e:
        print('\n')
        for arg in e.args:
            pprint.pprint(arg)

    os.makedirs(filename, exist_ok=True)
    pickle.dump(replay, open(filename+'/replay.pickle', 'wb'))
    with open(filename+'/keyframes.json', 'w', encoding='utf-8') as outfile:
        json.dump(replay.keyframes, outfile, indent=2, ensure_ascii=False)
    with open(filename+'/header.json', 'w', encoding='utf-8') as outfile:
        json.dump(replay.header, outfile, indent=2, ensure_ascii=False)
    with open(filename+'/netstream.json', 'w', encoding='utf-8') as outfile:
        outfile.write(replay.netstream_to_json())
