import copy
import json
import pickle
import traceback
from collections import OrderedDict
from io import StringIO

import math
from PyQt5.QtCore import QSize, Qt, QRect, QThread, pyqtSignal
import sys
from os import path
from queue import Queue
from threading import Thread, Event

from PyQt5.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit, QGridLayout, QListWidget,
    QSpacerItem, QHBoxLayout, QScrollArea, QLayout, QToolBar, QLabel, QComboBox, QPushButton, QMenuBar, QMenu, QAction,
    QGroupBox, QFrame, QSlider, QCheckBox, QDialog, QApplication, QProgressBar, QMessageBox, QFileDialog, QMainWindow)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import LogNorm
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from pyrope.analyser import Analyser
from pyrope.replay import Replay
from time import sleep, time, strftime

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


class PyRainGui(QMainWindow):

    def __init__(self):
        super().__init__()
        self.replay = None
        self.centralwidget = None
        self.mpl_widget = None
        self.cmb_player = None
        self.cmb_style = None
        self.action_exit = None
        self.action_open = None
        self.btn_popout = None
        self.btn_saveimage = None
        self.txt_log = None
        self.lst_plots = None
        self.chk_logscale = None
        self.sld_res = None
        self.cmb_slicing = None
        self.btn_calc = None
        self.analyser = None

    def setup_ui(self):
        self.resize(720, 552)
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setWindowTitle('PyRain - Replay Analysis Interface')

        self.centralwidget = QWidget(self)
        size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        size_policy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(size_policy)
        vl_centralw = QVBoxLayout(self.centralwidget)
        vl_centralw.setContentsMargins(-1, 9, -1, -1)

        tabview = QTabWidget(self.centralwidget)
        tabview.setTabPosition(QTabWidget.North)

        self.metaview = QWidget()
        self.metaview.setEnabled(False)
        tabview.addTab(self.metaview, "MetaData")
        self.setup_metaview(self.metaview)

        self.heatmapview = QWidget()
        self.heatmapview.setEnabled(False)
        tabview.addTab(self.heatmapview, "Heatmaps")
        self.setup_heatmapview(self.heatmapview)

        self.txt_log = QPlainTextEdit(self.centralwidget)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        size_policy.setHeightForWidth(self.txt_log.sizePolicy().hasHeightForWidth())
        self.txt_log.setSizePolicy(size_policy)
        self.txt_log.setMaximumSize(QSize(16777215, 100))

        vl_centralw.addWidget(tabview)
        vl_centralw.addWidget(self.txt_log)
        self.vl_centralw = vl_centralw
        self.setCentralWidget(self.centralwidget)

        self.setup_menu()
        self.setup_toolbar()
        self.setup_signals()

        self.txt_log.appendPlainText('Setup Completed. Welcome to PyRain')

    def setup_metaview(self, tab):
        metaview_grid = QGridLayout(tab)

        self.lst_meta = QListWidget(tab)
        size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        size_policy.setVerticalStretch(1)
        size_policy.setHorizontalStretch(1)
        size_policy.setHeightForWidth(self.lst_meta.sizePolicy().hasHeightForWidth())
        self.lst_meta.setSizePolicy(size_policy)
        self.lst_meta.setMinimumSize(QSize(100, 235))
        self.lst_meta.setMaximumSize(QSize(200, 400))
        metaview_grid.addWidget(self.lst_meta, 0, 1, 1, 1)

        spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        metaview_grid.addItem(spacer, 1, 1, 1, 1)

        self.txt_meta = QPlainTextEdit(tab)
        self.txt_meta.setMinimumWidth(356)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.txt_meta.setSizePolicy(size_policy)
        metaview_grid.addWidget(self.txt_meta, 0, 2, 2, 1)

    def setup_heatmapview(self, tab):
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        tab.setSizePolicy(size_policy)
        hzl_1 = QHBoxLayout(tab)  # Main Container (Controls | Figure)

        # CONTROLS
        box_controls = self.setup_heatmap_controls()
        hzl_1.addWidget(box_controls)

        # PLOTTING AREA
        mpl_scrollarea = QScrollArea(self.heatmapview)
        mpl_scrollarea.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,
                                                 QSizePolicy.MinimumExpanding))
        mpl_scrollarea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        mpl_scrollarea.setWidgetResizable(True)
        mpl_content = QWidget()

        size_policy = QSizePolicy(QSizePolicy.MinimumExpanding,
                                  QSizePolicy.MinimumExpanding)
        mpl_content.setSizePolicy(size_policy)

        self.mpl_l = QVBoxLayout(mpl_content)
        self.mpl_l.setSizeConstraint(QLayout.SetMinimumSize)

        mpl_scrollarea.setWidget(mpl_content)
        hzl_1.addWidget(mpl_scrollarea)

    def setup_toolbar(self):
        toolbar = QToolBar(self)
        toolbar.setStyleSheet('QToolBar{spacing:10px;}')
        toolbar.layout().setContentsMargins(7, 7, 7, 7)

        lbl_player = QLabel()
        lbl_player.setText("Player:")
        toolbar.addWidget(lbl_player)
        self.cmb_player = QComboBox()
        self.cmb_player.insertItems(0, ['No Replay Present'])
        toolbar.addWidget(self.cmb_player)

        toolbar.addSeparator()

        lbl_slicing = QLabel()
        lbl_slicing.setText('Slicing:')
        toolbar.addWidget(lbl_slicing)
        self.cmb_slicing = QComboBox()
        self.cmb_slicing.insertItems(0, ['None', 'Goal'])
        self.cmb_slicing.setMinimumSize(QSize(100, 0))
        toolbar.addWidget(self.cmb_slicing)

        toolbar.addSeparator()

        self.btn_calc = QPushButton()
        self.btn_calc.setText("Extract Data")
        toolbar.addWidget(self.btn_calc)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

    def setup_menu(self):
        menubar = QMenuBar(self)
        menubar.setGeometry(QRect(0, 0, 868, 21))
        menu_file = QMenu(menubar)
        menu_file.setTitle('File')
        menubar.addAction(menu_file.menuAction())

        action_open = QAction(self)
        action_open.setText('Open...')
        menu_file.addAction(action_open)

        menu_save = QMenu(self)
        menu_save.setTitle('Save')
        menu_file.addAction(menu_save.menuAction())

        action_save_replay = QAction(self)
        action_save_replay.setText('Save Parsed Replay')
        menu_save.addAction(action_save_replay)

        action_exit = QAction(self)
        action_exit.setText('Exit')
        menu_file.addAction(action_exit)

        menu_view = QMenu(menubar)
        menu_view.setTitle('View')
        menubar.addAction(menu_view.menuAction())

        action_toggle_log = QAction(self)
        action_toggle_log.setText('Debug Log')
        menu_view.addAction(action_toggle_log)

        action_open.triggered.connect(self.show_open_file)
        action_exit.triggered.connect(self.close)
        action_toggle_log.triggered.connect(self.toggle_log)
        action_save_replay.triggered.connect(self.save_replay)
        self.setMenuBar(menubar)

    def setup_heatmap_controls(self):
        box_controls = QGroupBox(self.centralwidget)
        size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        size_policy.setHorizontalStretch(1)
        size_policy.setHeightForWidth(box_controls.sizePolicy().hasHeightForWidth())
        box_controls.setSizePolicy(size_policy)
        box_controls.setMinimumSize(QSize(150, 250))
        box_controls.setMaximumSize(QSize(200, 16777215))
        box_controls.setAutoFillBackground(True)

        vl_controls = QVBoxLayout(box_controls)

        frm_settings = self.setup_settings(box_controls)
        vl_controls.addWidget(frm_settings)

        lbl_plots = QLabel(box_controls)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        size_policy.setHeightForWidth(lbl_plots.sizePolicy().hasHeightForWidth())
        lbl_plots.setSizePolicy(size_policy)
        lbl_plots.setText('Available Plots:')
        vl_controls.addWidget(lbl_plots)

        self.lst_plots = QListWidget(box_controls)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        size_policy.setHeightForWidth(self.lst_plots.sizePolicy().hasHeightForWidth())
        self.lst_plots.setSizePolicy(size_policy)
        self.lst_plots.setMinimumSize(QSize(0, 50))
        self.lst_plots.setMaximumSize(QSize(16777215, 200))
        self.lst_plots.setFrameShape(QFrame.Box)
        self.lst_plots.setFrameShadow(QFrame.Sunken)
        vl_controls.addWidget(self.lst_plots)

        self.btn_popout = QPushButton(box_controls)
        self.btn_popout.setText('Popout to new window')
        vl_controls.addWidget(self.btn_popout)

        self.btn_saveimage = QPushButton(box_controls)
        self.btn_saveimage.setText('Save as image')
        vl_controls.addWidget(self.btn_saveimage)

        spc_5 = QSpacerItem(20, 2, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        vl_controls.addItem(spc_5)

        return box_controls

    def setup_settings(self, box_controls):
        frm_settings = QFrame(box_controls)
        frm_settings.setMinimumSize(QSize(0, 100))
        frm_settings.setFrameShape(QFrame.Box)
        frm_settings.setFrameShadow(QFrame.Sunken)

        grl_settings = QGridLayout(frm_settings)
        grl_settings.setContentsMargins(-1, -1, -1, 2)

        lbl_style = QLabel(frm_settings)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(lbl_style.sizePolicy().hasHeightForWidth())
        lbl_style.setSizePolicy(size_policy)
        lbl_style.setText('Style:')
        grl_settings.addWidget(lbl_style, 0, 0, 1, 1)

        self.cmb_style = QComboBox(frm_settings)
        self.cmb_style.setAutoFillBackground(False)
        self.cmb_style.setEditable(False)
        self.cmb_style.insertItems(0, ['Hexbin', 'Histogram - Blur', 'Histogram - Clear'])
        self.cmb_style.setCurrentIndex(0)
        grl_settings.addWidget(self.cmb_style, 0, 1, 1, 3)

        self.chk_logscale = QCheckBox(frm_settings)
        self.chk_logscale.setText('Logarithmic Scaling')
        grl_settings.addWidget(self.chk_logscale, 1, 0, 1, 4)

        lbl_res = QLabel(frm_settings)
        lbl_res.setText('Resolution:')
        grl_settings.addWidget(lbl_res, 2, 0, 1, 4)

        self.sld_res = QSlider(frm_settings)
        self.sld_res.setOrientation(Qt.Horizontal)
        grl_settings.addWidget(self.sld_res, 3, 0, 1, 4)

        return frm_settings

    def setup_signals(self):
        self.lst_meta.itemSelectionChanged.connect(self.show_meta)
        self.btn_calc.clicked.connect(self.show_figure)

    def save_replay(self):
        folder = path.dirname(path.realpath(__file__))
        ext = 'Replay (*.pyrope)'
        filename = QFileDialog.getSaveFileName(self, 'Load Replay', folder, ext)
        pickle.dump(self.replay, open(filename[0], 'wb'))

    def toggle_log(self):
        self.txt_log.setVisible(not self.txt_log.isVisible())

    def show_figure(self):
        if not self.analyser:
            self.txt_log.appendPlainText('Netstream not parsed yet. Please reimport replay file')
            # return TODO REENABLE
        player = self.cmb_player.currentText()
        slicing = True
        if self.cmb_slicing.currentText() == 'None':
            slicing = False
        coords = self.analyser.get_player_pos(player, slicing)
        hm_list = self.generate_figures(coords)
        for hm in hm_list:
            fig = FigureCanvas(hm)
            fig.setMinimumSize(QSize(400, 320))
            fig.setMaximumSize(QSize(600, 480))
            fig.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.mpl_l.addWidget(fig)
        # self.mpl_scrollarea.setWidget(self.mpl_content)

    def show_open_file(self):
        home = path.expanduser('~')
        # replay_folder = home+'\\My Games\\\Rocket League\\TAGame\\Demos'
        replay_folder = path.dirname(path.realpath(__file__))+'\\testfiles'  # TODO DEV ONLY
        if not path.isdir(replay_folder):
            replay_folder = home
        ext = 'Replay (*.pyrope *.replay)'
        fname = QFileDialog.getOpenFileName(self, 'Load Replay', replay_folder, ext)
        if fname[0]:
            ext = fname[0].split('.')[-1]
            if ext == 'replay':
                self.replay = Replay(path=fname[0])
                self.txt_log.appendPlainText('Rocket League Replay File loaded and Validated')
                msg = 'Header Parsed. Decode Netstream now?\n(This might take a while)'
                question = QMessageBox().question(self, 'Proceed', msg,  QMessageBox.Yes, QMessageBox.No)
                if question == QMessageBox.Yes:
                    self.show_progress()
                    self.heatmapview.setEnabled(True)
                else:
                    self.txt_log.appendPlainText('Netstream not Parsed. Only Metadata for view available')
            elif ext == 'pyrope':
                self.replay = pickle.load(open(fname[0], 'rb'))
                self.txt_log.appendPlainText('pyrain Parsed Replay File sucessfully loaded')
                self.netstream_loaded()
                self.heatmapview.setEnabled(True)
            # self.meta_attributes = {k:v for (k,v) in self.replay.__dict__.items() if not k.startswith('_')}
            self.meta_attributes = OrderedDict([('CRC', self.replay.crc),  # TODO search better way than hardcoding
                                                ('Version', self.replay.version),  # while preserving order
                                                ('Header', self.replay.header),
                                                ('Maps', self.replay.maps),
                                                ('KeyFrames', self.replay.keyframes),
                                                ('Debug Log', self.replay.dbg_log),
                                                ('Goal Frames', self.replay.goal_frames),
                                                ('Packages', self.replay.packages),
                                                ('Objects', self.replay.objects),
                                                ('Names', self.replay.names),
                                                ('Class Map', self.replay.class_index_map),
                                                ('Netcache Tree', self.replay.netcache)])
            for k in self.meta_attributes.keys():
                self.lst_meta.addItem(k)
            self.metaview.setEnabled(True)

    def show_meta(self):
        item = self.lst_meta.currentItem()
        data = self.meta_attributes[item.text()]
        if not data:
            data = "Empty Attribute"
        else:
            data = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        self.txt_meta.setPlainText(data)

    def show_progress(self):
        num_frames = self.replay.header['NumFrames']-1
        progress = ProgressDialog(self, num_frames)

        ti = ThreadedImport(self, self.replay)
        ti.progress.connect(progress.set_value)
        ti.done.connect(self.netstream_loaded)
        progress.btn_cancel.clicked.connect(ti.setstop)
        progress.show()
        ti.start()

    def netstream_loaded(self):
        self.txt_log.appendPlainText('Netstream Parsed. No Errors found')
        self.analyser = Analyser(self.replay)
        self.cmb_player.clear()
        self.cmb_player.insertItems(0, [k for k in self.analyser.get_player().keys()])

    def generate_figures(self, coords, draw_map=True, bins=(13, 10), hexbin=True):
        all_data = 0
        figures = []
        for i, coord in enumerate(coords):
            fig = Figure()
            ax = fig.add_subplot(111)
            y = [x for x, y, z in coord if z > 15 and -5120 <= y <= 5120 and -4096 <= x <= 4096]
            x = [y for x, y, z in coord if z > 15 and -5120 <= y <= 5120 and -4096 <= x <= 4096]
            if not x and not y:
                continue
            all_data += len(x)
            print("Building Heatmap %d with %d Data Points" % (i, len(x)))
            ax.set_ylim((4596, -4596))
            ax.set_xlim((5520, -5520))
            if not hexbin:
                heatmap, xedges, yedges = np.histogram2d(y, x, bins=bins, range=[(-5520, 5520), (-4596, 4596)])
                extent = [yedges[0], yedges[-1], xedges[-1], xedges[0]]
                my_cmap = copy.copy(plt.cm.get_cmap('jet')) # copy the default cmap
                my_cmap.set_bad((0, 0, 1))
                cax = ax.imshow(heatmap, extent=extent, aspect=0.8, norm=LogNorm(), cmap=my_cmap)  # Draw heatmap
                # self.fig.colorbar(cax)
                # ax.hist2d(x, y, bins=(26, 20), normed=LogNorm, range=[(-4596,4596),(-5520,5520)])
                # ax.set_aspect(0.8)
            else:
                y.extend([-4596, 4596, 4596, -4596])
                x.extend([5520, 5520, -5520, -5520])
                ax.hexbin(x, y, cmap=plt.cm.jet, gridsize=bins, norm=LogNorm()) #oder bins='log'?
                ax.set_aspect(0.8)
                # self.axes.plot()
                # self.fig.colorbar(cax)
            if draw_map:
                x = [y for x, y in stadium]
                y = [x for x, y in stadium]
                ax.plot(x, y, c='r')
            # ax.axis('off')
            # fig.subplots_adjust(hspace=0, wspace=0, right=0.99, left=0.1)
            figures.append(fig)
        print("OVERALL POINTS", all_data)
        return figures


class ProgressDialog(QDialog):

    def __init__(self, parent, limit):
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Parsing Replay')
        self.setMinimumSize(QSize(400, 75))
        self.setMaximumSize(QSize(400, 75))
        vlayout = QVBoxLayout(self)
        vlayout.setSizeConstraint(QLayout.SetMinAndMaxSize)

        self.pbar = QProgressBar(self)
        self.pbar.setRange(0, limit)
        self.pbar.setAlignment(Qt.AlignCenter)
        self.pbar.setFormat("Parsing Netstream %p%")
        self.pbar.setMinimumSize(QSize(380, 20))
        self.pbar.setMaximumSize(QSize(380, 20))
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.pbar.setSizePolicy(size_policy)
        vlayout.addWidget(self.pbar)

        self.btn_cancel = QPushButton(self)
        self.btn_cancel.setSizePolicy(size_policy)
        self.btn_cancel.setMinimumSize(QSize(120, 23))
        self.btn_cancel.setMaximumSize(QSize(120, 23))
        self.btn_cancel.setText("MISSION ABORT!")
        size_policy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_cancel.setSizePolicy(size_policy)
        vlayout.addWidget(self.btn_cancel)

        self.btn_cancel.clicked.connect(self.close)

    def set_value(self, value):
        self.pbar.setProperty("value", value)
        if value == self.pbar.maximum():
            self.close()


class ThreadedImport(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal()

    def __init__(self, parent, replay):
        QThread.__init__(self, parent)
        self.replay = replay
        self.stop = Event()

    def run(self):
        qout = Queue()
        parse_thread = Thread(target=self.replay.parse_netstream, args=(qout, self.stop))
        parse_thread.start()
        while True:
            if qout.empty():
                sleep(0.1)
                continue
            msg = qout.get()
            if msg == 'done':
                self.done.emit()
                break
            elif msg == 'exception':
                exc = qout.get()
                raise exc
            elif msg == 'abort':
                return
            else:
                self.progress.emit(msg)

    def setstop(self):
        self.stop.set()


def excepthook(excType, excValue, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param excType exception type
    @param excValue exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    notice = "Exception encountered\n"  # TODO MORE INFOS
    tbinfofile = StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(excType), str(excValue))
    sections = [separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    errorbox = QMessageBox()
    errorbox.setText(str(notice)+str(msg))
    errorbox.exec_()
sys.excepthook = excepthook
app = QApplication(sys.argv)
ui = PyRainGui()
ui.setup_ui()
ui.show()
sys.exit(app.exec_())