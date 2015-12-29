import logging
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger('pyrain')
stadium = [(x + 100 if x > 0 else x - 100, y + 100 if y > 0 else y - 100) for x, y in
           [(2646, 5097), (2576, 5101), (-2512, 5101), (-2571, 5100), (-2641, 5097), (-2711, 5089),
            (-2837, 5060), (-2957, 5014), (-3068, 4949), (-3176, 4860), (-3359, 4678),
            (-3549, 4489), (-3729, 4309), (-3865, 4169), (-3941, 4066), (-4007, 3943),
            (-4048, 3821), (-4070, 3695), (-4076, 3625), (-4078, 3496), (-4077, 3367),
            (-4077, -3586), (-4073, -3659), (-4063, -3747), (-4024, -3902), (-3955, -4045),
            (-3853, -4183), (-3743, -4296), (-3631, -4407), (-3520, -4518), (-3399, -4639),
            (-3288, -4750), (-3176, -4860), (-3043, -4965), (-2907, -5036), (-2841, -5060),
            (-2761, -5081), (-2679, -5094), (-2611, -5101), (2551, -5101), (2616, -5099),
            (2693, -5092), (2757, -5081), (2904, -5037), (3029, -4975), (3140, -4893),
            (3249, -4790), (3345, -4692), (3442, -4596), (3538, -4499), (3643, -4394),
            (3739, -4298), (3834, -4202), (3920, -4099), (3994, -3974), (4040, -3851),
            (4057, -3781), (4068, -3722), (4077, -3592), (4077, 3562), (4074, 3652), (4063, 3750),
            (4043, 3838), (4017, 3919), (3989, 3984), (3900, 4127), (3796, 4243), (3685, 4353),
            (3574, 4464), (3453, 4585), (3342, 4695), (3232, 4805), (3108, 4918), (2981, 5001),
            (2906, 5036), (2842, 5060), (2763, 5081), (2646, 5097)]]
# TODO Hardcode stadium size extension and make something for wasteland


# avg car size ~118x82x32 ; Field Size(Excluding Wasteland: 10240x8192*(2000?);
# -5120 - 5120; -4096,4096; 19, 2000
# bins for ~1:1 mapping:87x100x62


def graph_2d(values, mean=True):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(values['xs'], values['ys'])
    if mean:
        y_mean = [np.mean(values['ys']) for i in values['xs']]
        ax.plot(values['xs'], y_mean, linestyle='--')
    plt.show()


def heat_3d():
    # Stadium Borders 3D
    fig = plt.figure()
    plot = fig.add_subplot(111, projection='3d')
    points_h = []
    for h in range(10):
        points_h.extend([(y, x, h * 200) for x, y in stadium])
    x, y, z = zip(*points_h)
    plot.plot(y, x, z)
    plt.show()


def generate_figure(data, draw_map=True, bins=(15, 12), hexbin=False, interpolate=True, norm=False):
    fig = Figure()
    ax = fig.add_subplot(111)
    x = data['x']
    y = data['y']
    logger.info("Building Heatmap %s with %d Data Points" % (data['title_short'], len(x)))
    cmap = plt.cm.get_cmap('jet')
    cmap.set_bad((0, 0, 1))
    # cmap = plt.cm.get_cmap('OrRd')
    norm = LogNorm() if norm else None
    if hexbin:
        ax.hexbin(x, y, cmap=cmap, gridsize=bins, norm=norm, extent=[-5520, 5520, 4416, -4416])
    else:
        interpolate = 'bilinear' if interpolate else 'none'
        bins = (bins[1], bins[0])
        heatmap, xedges, yedges = np.histogram2d(y, x, bins=bins,
                                                 range=[(-4416, 4416), (-5520, 5520)])
        extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]
        ax.imshow(heatmap, extent=extent, norm=norm, cmap=cmap, interpolation=interpolate,
                  origin='lower', aspect='auto')
        ax.autoscale(False)
    if draw_map:
        x = [y for x, y in stadium]
        y = [x for x, y in stadium]
        ax.plot(x, y, c='r')
    ax.text(0.1, 0, 'Team 0',
            transform=ax.transAxes,
            bbox=dict(facecolor='white'))
    ax.text(0.9, 0, 'Team 1',
            horizontalalignment='right',
            transform=ax.transAxes,
            bbox=dict(facecolor='white'))
    ax.set_title(data['title'], bbox=dict(facecolor='white'))
    ax.axis('off')
    fig.subplots_adjust(hspace=0, wspace=0, right=1, top=0.9, bottom=0.05, left=0)
    fig.patch.set_visible(False)
    return fig
