import pickle
import pprint
from analyser import Analyser
from plotter import heat_2d
cloud = False
# filename = "FD1D"
# filename = "91D6"
# filename = "3BF9"
# filename = "C51C0"
# filename = "C747"
filename = "0FCD"


if __name__ == '__main__':
    replay = pickle.load(open(filename + '/replay.pickle', 'rb'))
    analyser = Analyser(replay)

    print("Please select PlayerID from following List:")
    pprint.pprint(analyser.get_player())
    # player_id = int(input("Enter ID:"))
    player_id = 17
    player_pos = analyser.get_player_pos(player_id, sep=False)
    # ball_pos = replay.get_ball_pos()
    plots = []
    if cloud:
        # heat_3d()
        pass
    else:
        # graph_2d(player_pos)
        heat_2d(player_pos, hexbin=True)
        # heat_2d(player_pos, hexbin=False)
