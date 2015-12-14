import json
import os
import pprint
import pickle
import sys
from pyrope.frame import FrameParsingError
from pyrope.netstream_property_parsing import PropertyParsingError
from pyrope.replay import Replay


if __name__ == '__main__':
    # filename = "FD1D"
    filename = "3BF9"
    # filename = "C51C0"
    replay = Replay("testfiles/"+filename+".replay")

    # try:
    #     replay.parse(parse_header=True, parse_netstream=True)
    #     # pprint.pprint(replay.car_id_to_player())
    # except (PropertyParsingError, FrameParsingError) as e:
    #     print('\n')
    #     for arg in e.args:
    #         pprint.pprint(arg)
    # os.makedirs(filename, exist_ok=True)
    # pickle.dump(replay.netstream, open(filename+'/netstream.pickle', 'wb'))
    # with open(filename+'/keyframes.json', 'w', encoding='utf-8') as outfile:
    #     json.dump(replay.keyframes, outfile, indent=2, ensure_ascii=False)
    # with open(filename+'/header.json', 'w', encoding='utf-8') as outfile:
    #     json.dump(replay.header.parsed, outfile, indent=2, ensure_ascii=False)
    # with open(filename+'/netstream.json', 'w', encoding='utf-8') as outfile:
    #     # json.dump(replay.netstream.frames, outfile, indent=2, ensure_ascii=False)
    #     outfile.write(replay.netstream.to_json())

    replay.netstream = pickle.load(open(filename+'/netstream.pickle', 'rb'))
    pprint.pprint(replay.get_player())
    positions = replay.get_pos_of_player(5)
    print(positions)
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(positions[6]['x'], positions[6]['y'], positions[6]['z'], c='r', marker='o')

    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.show()