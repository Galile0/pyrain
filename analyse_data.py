import pickle
import pprint
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from pyrope.replay import Replay
import numpy as np

if __name__ == '__main__':
    # filename = "FD1D"
    filename = "91D6"
    # filename = "3BF9"
    # filename = "C51C0"

    replay = Replay("testfiles/"+filename+".replay")
    replay.netstream = pickle.load(open(filename+'/netstream.pickle', 'rb'))
    print("Please Enter PlayerID from following List:")
    pprint.pprint(replay.get_player())
    player_id = int(input("Enter ID:"))
    # player_id = 3
    player_pos = replay.get_player_pos(player_id)
    ball_pos = replay.get_ball_pos()
    plots = []
    fig = plt.figure()
    for i, actor in enumerate(player_pos):
        x = np.array(player_pos[actor]['x'])
        y = np.array(player_pos[actor]['y'])
        z = np.array(player_pos[actor]['z'])
        ax = fig.add_subplot(331+i, projection='3d')
        ax.scatter(x, y, z, c='r', marker='o')
        # ax.scatter(ball_pos['x'], ball_pos['y'], ball_pos['z'], c='b', marker='o')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plots.append(ax)
    plt.show()