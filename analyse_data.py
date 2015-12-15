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
    # player_id = int(input("Enter ID:"))
    player_id = 4
    player_pos = replay.get_player_pos(player_id)
    ball_pos = replay.get_ball_pos()
    print(player_pos)
    plots = []

    for i, actor in player_pos.items():
        fig = plt.figure()
        x = np.array(actor['x'])
        y = np.array(actor['y'])
        z = np.array(actor['z'])
        ax = fig.add_subplot(111, projection='3d')
        # ax.plot(x,y,zs=0, zdir='z')
        # ax.scatter(x, y, z, c='r', marker='o')
        ax.plot_wireframe(x, y, z, rstride=1000, cstride=1000)
        # ax.scatter(ball_pos['x'], ball_pos['y'], ball_pos['z'], c='b', marker='o')
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plots.append(ax)
    plt.show()