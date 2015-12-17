import pickle
import pprint
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from pyrope.replay import Replay
import numpy as np
import math

cloud = False
stadium = [(x + 100 if x > 0 else x - 100, y + 100 if y > 0 else y - 100) for x, y in
           [(2646, 5097), (2576, 5101), (-2512, 5101), (-2571, 5100), (-2641, 5097), (-2711, 5089), (-2837, 5060),
            (-2957, 5014), (-3068, 4949), (-3176, 4860), (-3359, 4678), (-3549, 4489), (-3729, 4309), (-3865, 4169),
            (-3941, 4066), (-4007, 3943), (-4048, 3821), (-4070, 3695), (-4076, 3625), (-4078, 3496), (-4077, 3367),
            (-4077, -3586), (-4073, -3659), (-4063, -3747), (-4024, -3902), (-3955, -4045), (-3853, -4183),
            (-3743, -4296), (-3631, -4407), (-3520, -4518), (-3399, -4639), (-3288, -4750), (-3176, -4860),
            (-3043, -4965), (-2907, -5036), (-2841, -5060), (-2761, -5081), (-2679, -5094), (-2611, -5101),
            (2551, -5101), (2616, -5099), (2693, -5092), (2757, -5081), (2904, -5037), (3029, -4975), (3140, -4893),
            (3249, -4790), (3345, -4692), (3442, -4596), (3538, -4499), (3643, -4394), (3739, -4298), (3834, -4202),
            (3920, -4099), (3994, -3974), (4040, -3851), (4057, -3781), (4068, -3722), (4077, -3592), (4077, 3562),
            (4074, 3652), (4063, 3750), (4043, 3838), (4017, 3919), (3989, 3984), (3900, 4127), (3796, 4243),
            (3685, 4353), (3574, 4464), (3453, 4585), (3342, 4695), (3232, 4805), (3108, 4918), (2981, 5001),
            (2906, 5036), (2842, 5060), (2763, 5081), (2646, 5097)]]  # TODO Hardcode stadium size extension

# avg car size ~118x82x32 ; Field Size: 10240x8192*2000?;
# bins for ~1:1 mapping:87x100x62


def heat_2d(coords, draw_map=True, bins=(10, 8)):
    fig = plt.figure()
    col = 1
    row = 1
    col_max = 6
    use_sq = False
    entrys = len(coords)
    if entrys > 12:
        use_sq = True
        sq = math.ceil(math.sqrt(len(coords)))
    elif entrys > col_max:
            row = 2
            col = 6
    elif entrys > col:
            col = entrys
    all_data = 0
    for i, coord in enumerate(coords):
        filtered = [(y, x) for x, y, z in coord if z > 15]
        if not filter:
            continue
        if use_sq:
            ax = plt.subplot(sq*100+sq*10+1+i)
        else:
            ax = plt.subplot(row*100+col*10+1+i)
        all_data += len(filtered)
        print("Building Heatmap %d with %d Data Points" % (i, len(filtered)))
        plt.xlim((4477, -4477))
        plt.ylim((5401, -5401))
        filtered.extend([(5477, 6401), (5477, -6401),
                        (-5477, 6401), (-5477, -6401)])  # Background Blur
        heatmap, xedges, yedges = np.histogram2d(*zip(*filtered), bins=bins)
        extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]
        ax.imshow(heatmap, extent=extent, aspect=1.206)  # Draw heatmap
        if draw_map:
            ax.plot(*zip(*stadium), c='r')
        ax.axis('off')
    # plt.tight_layout(rect=[0,0,1,1])
    print("OVERALL POINTS" ,all_data)
    fig.subplots_adjust(hspace=0.05, wspace=0.05, right=0.995, left=0.005, top=1, bottom=0)
    plt.show()


def graph_2d(coords):
    for i, actor in enumerate(coords.values()):
        fig = plt.figure()
        filtered = [(x, y) for x, y, z in actor if z > 15]
        if not filtered:
            continue
        ax = fig.add_subplot(111)
        ax.scatter(*zip(*filtered), c='b', marker='o', s=[10] * len(filtered))
        ax.plot(*zip(*stadium), c='r')
        plt.xlim((4477, -4477))
        plt.ylim((5401, -5401))
    plt.show()


def heat_3d():
    # Stadium Borders 3D
    fig = plt.figure()
    plot = fig.add_subplot(111, projection='3d')
    points_h = []
    for h in range(10):
        points_h.extend([(y,x,h*200) for x,y in stadium])
    x, y, z = zip(*points_h)
    plot.plot(y, x, z)
    plt.show()


if __name__ == '__main__':
    # filename = "FD1D"
    # filename = "91D6"
    # filename = "3BF9"
    filename = "C51C0"
    # filename = "C747"
    # filename = "0FCD"
    # replay = Replay("testfiles/" + filename + ".replay")
    replay = pickle.load(open(filename + '/replay.pickle', 'rb'))
    # replay.netstream = pickle.load(open(filename + '/replay.pickle', 'rb'))
    print("Please Enter PlayerID from following List:")
    pprint.pprint(replay.get_player())
    # player_id = int(input("Enter ID:"))
    player_id = 7
    player_pos = replay.get_player_pos(player_id, sep=True)
    # ball_pos = replay.get_ball_pos()
    plots = []
    if cloud:
        heat_3d()
    else:
        # graph_2d(player_pos)
        heat_2d(player_pos)
