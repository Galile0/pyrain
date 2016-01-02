import logging
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger('pyrain')
ARENA_OUTLINE = {'file': 'resources/arena_outline.png',
                 'alpha': 0.8}
ARENA_FIELDLINE = {'file': 'resources/arena_fieldlines.png',
                   'alpha': 0.3}
ARENA_BOOST = {'file': 'resources/arena_boost.png',
               'alpha': 0.8}

# avg car size ~118x82x32 ; Field Size(Excluding Wasteland: 10240x8192*(2000?);
# -5120 - 5120; -4096,4096; 19, 2000
# Goals are roughly 650units deep
# Field length with goals: ~11540 aspect ratio: 0.71
# bins for ~1:1 mapping:87x100x62


def graph_2d(values, mean=True):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(values['xs'], values['ys'])
    if mean:
        y_mean = [np.mean(values['ys']) for i in values['xs']]
        ax.plot(values['xs'], y_mean, linestyle='--')
    plt.show()


def generate_figure(data, draw_map=None, bins=(25, 12), hexbin=False, interpolate=True, norm=False):
    fig = Figure()
    ax = fig.add_subplot(111)
    x = data['x']
    y = data['y']
    logger.info("Building Heatmap %s with %d Data Points" % (data['title_short'], len(x)))
    cmap = plt.cm.get_cmap('jet')
    cmap.set_bad((0, 0, 0.5))
    norm = LogNorm() if norm else None
    if hexbin:
        ax.hexbin(x, y, cmap=cmap, gridsize=bins, norm=norm, extent=[-5770, 5770, -4096, 4096])
        # Zorder = 1
    else:
        interpolate = 'bilinear' if interpolate else 'none'
        bins = (bins[1], bins[0])
        heatmap, xedges, yedges = np.histogram2d(y, x, bins=bins,
                                                 range=[(-4096, 4096), (-5770, 5770)])
        extent = [yedges[0], yedges[-1], xedges[0], xedges[-1]]
        ax.imshow(heatmap, extent=extent, norm=norm, cmap=cmap, interpolation=interpolate,
                  origin='lower', aspect='auto')
        ax.autoscale(False)
    if draw_map:
        for drawing in draw_map:
            im = plt.imread(drawing['file'])
            axim = ax.imshow(im, extent=[-5770, 5770, -4096, 4096], origin='lower', aspect='auto',
                             alpha=drawing['alpha'])
            axim.set_zorder(2)
    ax.text(0.1, 0, 'Team 0',
            transform=ax.transAxes,
            bbox=dict(facecolor='white'))
    ax.text(0.9, 0, 'Team 1',
            horizontalalignment='right',
            transform=ax.transAxes,
            bbox=dict(facecolor='white'))
    ax.set_xlim(-5880, 5880)
    ax.set_ylim(-4200, 4200)
    ax.set_title(data['title'], bbox=dict(facecolor='white'))
    ax.axis('off')
    fig.subplots_adjust(hspace=0, wspace=0, right=1, top=0.9, bottom=0.05, left=0)
    fig.patch.set_facecolor((0, 0, .5))
    return fig
