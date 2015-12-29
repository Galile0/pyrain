import json
import pickle
import traceback
import sys
import logging

from os import path
from queue import Queue
from threading import Thread, Event
from collections import OrderedDict
from io import StringIO
from time import sleep

import math
from PyQt5.QtCore import QSize, Qt, QRect, QThread, pyqtSignal
from PyQt5.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit,
                             QGridLayout, QListWidget, QSpacerItem, QHBoxLayout, QScrollArea,
                             QLayout, QToolBar, QLabel, QComboBox, QPushButton, QMenuBar, QMenu,
                             QAction, QGroupBox, QFrame, QSlider, QCheckBox, QDialog, QApplication,
                             QProgressBar, QMessageBox, QFileDialog, QMainWindow, QAbstractItemView)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import plotter
from analyser import Analyser, AnalyserUtils
from pyrope import Replay


class PyRainGui(QMainWindow):

    def __init__(self):
        super().__init__()
        self.replay = None
        self.analyser = None
        self.datasets = {}
        self.drawn_plots = {}
        self.setup_ui()
        handler = QtHandler(self.txt_log)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info('Setup Completed. Welcome to PyRain')

    def setup_ui(self):
        self.resize(1100, 560)
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

        self.meta_tab = QWidget()
        self.meta_tab.setEnabled(False)
        tabview.addTab(self.meta_tab, "MetaData")
        self.setup_metaview(self.meta_tab)

        self.heatmap_tab = QWidget()
        self.heatmap_tab.setEnabled(False)
        self.heatmap_tab.setMinimumSize(QSize(0, 290))
        tabview.addTab(self.heatmap_tab, "Heatmaps")
        self.setup_heatmapview(self.heatmap_tab)

        self.txt_log = QPlainTextEdit(self.centralwidget)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        size_policy.setHeightForWidth(self.txt_log.sizePolicy().hasHeightForWidth())
        self.txt_log.setSizePolicy(size_policy)
        self.txt_log.setMaximumSize(QSize(16777215, 100))

        vl_centralw.addWidget(tabview)
        vl_centralw.addWidget(self.txt_log)
        self.setCentralWidget(self.centralwidget)

        self.setup_menu()
        self.setup_toolbar()
        self.setup_signals()

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
        self.hm_sa = QScrollArea(tab)
        self.hm_sa.setMinimumWidth(330)
        self.hm_sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.hm_sa.setWidgetResizable(True)

        hm_sac = QWidget()
        self.hm_sacl = FlowLayout(hm_sac, container=self.hm_sa, resize_threshold=(-20, -10))
        self.hm_sa.setWidget(hm_sac)
        hzl_1.addWidget(self.hm_sa)

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

        action_import = QAction(self)
        action_import.setText('Import...')
        menu_file.addAction(action_import)

        action_export = QAction(self)
        action_export.setText('Export...')
        menu_file.addAction(action_export)

        action_exit = QAction(self)
        action_exit.setText('Exit')
        menu_file.addAction(action_exit)

        menu_view = QMenu(menubar)
        menu_view.setTitle('View')
        menubar.addAction(menu_view.menuAction())

        action_toggle_log = QAction(self)
        action_toggle_log.setText('Debug Log')
        menu_view.addAction(action_toggle_log)

        action_import.triggered.connect(self.import_data)
        action_exit.triggered.connect(self.close)
        action_toggle_log.triggered.connect(self.toggle_log)
        action_export.triggered.connect(self.export_data)
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

        gl_controls = QGridLayout(box_controls)
        gl_controls.setHorizontalSpacing(0)

        frm_settings = self.setup_settings(box_controls)
        gl_controls.addWidget(frm_settings, 1, 0, 1, 6)

        lbl_plots = QLabel(box_controls)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        size_policy.setHeightForWidth(lbl_plots.sizePolicy().hasHeightForWidth())
        lbl_plots.setSizePolicy(size_policy)
        lbl_plots.setText('Available Plots:')
        gl_controls.addWidget(lbl_plots, 2, 0, 1, 6)

        self.lst_plots = QListWidget(box_controls)
        self.lst_plots.setSelectionMode(QAbstractItemView.ExtendedSelection)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        self.lst_plots.setSizePolicy(size_policy)
        self.lst_plots.setMinimumSize(QSize(0, 50))
        self.lst_plots.setMaximumSize(QSize(16777215, 200))
        gl_controls.addWidget(self.lst_plots, 3, 0, 1, 6)

        self.btn_addplot = QPushButton(box_controls)
        self.btn_addplot.setText('Add')
        self.btn_addplot.setEnabled(False)
        gl_controls.addWidget(self.btn_addplot, 4, 0, 1, 2)

        self.btn_removeplot = QPushButton(box_controls)
        self.btn_removeplot.setText('Delete')
        self.btn_removeplot.setEnabled(False)
        gl_controls.addWidget(self.btn_removeplot, 4, 2, 1, 2)

        self.btn_updateplot = QPushButton(box_controls)
        self.btn_updateplot.setText('Update')
        self.btn_updateplot.setEnabled(False)
        gl_controls.addWidget(self.btn_updateplot, 4, 4, 1, 2)

        btn_clearplot = QPushButton(box_controls)
        btn_clearplot.setText('Clear')
        gl_controls.addWidget(btn_clearplot, 5, 0, 1, 3)

        btn_popout = QPushButton(box_controls)
        btn_popout.setText('Popout')
        gl_controls.addWidget(btn_popout, 5, 3, 1, 3)

        btn_saveimage = QPushButton(box_controls)
        btn_saveimage.setText('Save as image')
        gl_controls.addWidget(btn_saveimage, 6, 0, 1, 6)

        spc_5 = QSpacerItem(20, 2, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        gl_controls.addItem(spc_5)

        self.btn_removeplot.clicked.connect(self.remove_plots)
        self.btn_addplot.clicked.connect(self.create_plots)
        self.btn_updateplot.clicked.connect(self.update_plots)
        btn_popout.clicked.connect(self.popout_plots)
        btn_clearplot.clicked.connect(self.clear_plots)
        btn_saveimage.clicked.connect(self.save_plots)
        return box_controls

    def setup_settings(self, box_controls):
        frm_settings = QFrame(box_controls)
        frm_settings.setMinimumSize(QSize(0, 100))
        frm_settings.setFrameShape(QFrame.Box)
        frm_settings.setFrameShadow(QFrame.Sunken)

        gl_settings = QGridLayout(frm_settings)
        gl_settings.setContentsMargins(-1, -1, -1, 2)

        lbl_style = QLabel(frm_settings)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(lbl_style.sizePolicy().hasHeightForWidth())
        lbl_style.setSizePolicy(size_policy)
        lbl_style.setText('Style:')
        gl_settings.addWidget(lbl_style, 0, 0, 1, 1)

        self.cmb_style = QComboBox(frm_settings)
        self.cmb_style.setAutoFillBackground(False)
        self.cmb_style.setEditable(False)
        self.cmb_style.insertItems(0, ['Hexbin', 'Histogram - Blur', 'Histogram - Clear'])
        self.cmb_style.setCurrentIndex(0)
        gl_settings.addWidget(self.cmb_style, 0, 1, 1, 3)

        self.chk_logscale = QCheckBox(frm_settings)
        self.chk_logscale.setText('Logarithmic Scaling')
        gl_settings.addWidget(self.chk_logscale, 1, 0, 1, 4)

        lbl_res = QLabel(frm_settings)
        lbl_res.setText('Resolution:')
        gl_settings.addWidget(lbl_res, 2, 0, 1, 4)

        self.sld_res = QSlider(frm_settings)
        self.sld_res.setOrientation(Qt.Horizontal)
        self.sld_res.setMinimum(1)
        self.sld_res.setMaximum(50)
        self.sld_res.setValue(10)
        gl_settings.addWidget(self.sld_res, 3, 0, 1, 4)

        return frm_settings

    def setup_signals(self):
        self.lst_meta.itemSelectionChanged.connect(self.show_meta)
        self.btn_calc.clicked.connect(self.extract_data)
        self.lst_plots.itemSelectionChanged.connect(self.highlight_plots)

    def clear_plots(self):
        count = self.lst_plots.count()
        for i in range(count):
            item_name = self.lst_plots.item(i).text()
            if item_name in self.drawn_plots:
                self.drawn_plots[item_name].deleteLater()
                del self.drawn_plots[item_name]

    def remove_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items]
        for item in items_text:
            if item in self.drawn_plots:
                self.drawn_plots[item].deleteLater()
                del self.drawn_plots[item]
        self.highlight_plots()

    def update_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() in self.drawn_plots]
        for plot in items_text:
            old_widget = self.drawn_plots[plot]
            index = self.hm_sacl.indexOf(old_widget)
            self.hm_sacl.removeWidget(old_widget)
            new_widget = self.generate_plot_widget(plot)
            self.hm_sacl.insertWidgetAt(index, new_widget)
        self.highlight_plots()

    def create_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() not in self.drawn_plots]
        for item in items_text:
            self.hm_sacl.addWidget(self.generate_plot_widget(item))
        self.highlight_plots()

    def popout_plots(self):
        # plotter.graph_2d(self.analyser.calc_dist_to_zero(self.cmb_player.currentText(),
        #                                                  reference='Ball'))
        # return
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() in self.drawn_plots]
        self.popouts = []
        for plot in items_text:
            figure = self.drawn_plots[plot].findChild(FigureCanvas).figure
            popout = PopoutDialog(FigureCanvas(figure), plot)
            popout.show()
            self.popouts.append(popout)

    def save_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() in self.drawn_plots]
        for plot in items_text:
            folder = path.dirname(path.realpath(__file__))
            ext = 'Plot (*.png)'
            filename = QFileDialog.getSaveFileName(self, 'Save Image', folder, ext)
            if filename[0]:
                fig = self.drawn_plots[plot].findChild(FigureCanvas).figure
                fig.savefig(filename[0])

    def generate_plot_widget(self, datasetname):
        plt_type = self.cmb_style.currentText()
        hexbin = False
        interpolate = False
        if plt_type == 'Hexbin':
            hexbin = True
        if 'Blur' in plt_type:
            interpolate = True
        scale = self.sld_res.value()/10
        bins = (math.ceil(scale*15), math.ceil(scale*12))
        log = self.chk_logscale.isChecked()
        plot = plotter.generate_figure(self.datasets[datasetname],
                                       bins=bins,
                                       norm=log,
                                       interpolate=interpolate,
                                       hexbin=hexbin)
        frm = QFrame()
        frm.setContentsMargins(0, 0, 0, 0)
        frm.setMinimumSize(QSize(300, 240))
        frm.setMaximumSize(QSize(515, 412))
        frm.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        frm.setLineWidth(3)
        frml = QVBoxLayout(frm)
        frml.setContentsMargins(0, 0, 0, 0)
        fig = FigureCanvas(plot)
        fig.mpl_connect('scroll_event', lambda evt: self.hm_sa.verticalScrollBar().setValue(
                self.hm_sa.verticalScrollBar().value()+int(evt.step)*-60))  # TODO Well, it works
        fig.setContentsMargins(0, 0, 0, 0)
        frml.addWidget(fig)
        self.drawn_plots[datasetname] = frm
        return frm

    def highlight_plots(self):
        selected_plots = self.lst_plots.selectedItems()
        if selected_plots:
            plot_names = [plot.text() for plot in selected_plots]
        else:
            return
        enable_btn_mod = False
        enable_add = False
        for name, widget in self.drawn_plots.items():
            if name in plot_names:
                widget.setFrameStyle(0x11)
                enable_btn_mod = True
                plot_names.remove(name)
            else:
                widget.setFrameStyle(0x00)
        self.btn_removeplot.setEnabled(enable_btn_mod)
        self.btn_updateplot.setEnabled(enable_btn_mod)
        if plot_names:
            enable_add=True
        self.btn_addplot.setEnabled(enable_add)

    def export_data(self):
        if not self.replay:
            return  # TODO LOG ERROR
        folder = path.dirname(path.realpath(__file__))
        ext = 'Replay (*.pyrope);;MetaData (*.json);;Header (*.json);;Netstream (*.json)'
        filename = QFileDialog.getSaveFileName(self, 'Export Replay', folder, ext)
        if filename[0]:
            if 'Replay' in filename[1]:
                pickle.dump(self.replay, open(filename[0], 'wb'))
            elif 'MetaData' in filename[1]:
                with open(filename[0], 'w', encoding='utf-8') as outfile:
                    outfile.write(self.replay.metadata_to_json())
            elif 'Header' in filename[1]:
                with open(filename[0], 'w', encoding='utf-8') as outfile:
                    json.dump(self.replay.header, outfile, indent=2, ensure_ascii=False)
            elif 'Netstream' in filename[1]:
                if not self.replay.netstream:
                    return  # TODO LOG ERROR
                with open(filename[0], 'w', encoding='utf-8') as outfile:
                    outfile.write(self.replay.netstream_to_json())

    def toggle_log(self):
        self.txt_log.setVisible(not self.txt_log.isVisible())

    def extract_data(self):
        if not self.analyser:
            logger.error('Netstream not parsed yet.'
                         'Please import replay file and parse the Netstream')
            return
        self.heatmap_tab.setEnabled(True)
        player = self.cmb_player.currentText()
        slicing = True
        if self.cmb_slicing.currentText() == 'None':
            slicing = False
        if player == 'Ball':
            data = self.analyser.get_ball_pos(slicing)
        else:
            data = self.analyser.get_player_pos(player, slicing)
        new_datasets = AnalyserUtils.filter_coords(data)
        for entry in new_datasets:
            if entry['title_short'] in self.datasets:
                logger.debug("Dataset already in Plotlist")
                continue
            self.lst_plots.addItem(entry['title_short'])
            self.datasets[entry['title_short']] = entry

    def import_data(self):
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
                logger.info('Rocket League Replay File loaded and Validated')
                msg = 'Header Parsed. Decode Netstream now?\n(This might take a while)'
                question = QMessageBox().question(self, 'Proceed', msg,
                                                  QMessageBox.Yes, QMessageBox.No)
                if question == QMessageBox.Yes:
                    self.show_progress()
                else:
                    logger.warn('Netstream not Parsed. Only Metadata for view available')
            elif ext == 'pyrope':
                self.replay = pickle.load(open(fname[0], 'rb'))
                logger.info('pyrain Parsed Replay File sucessfully loaded')
                self.netstream_loaded()
            self.meta_attributes = OrderedDict([('CRC', self.replay.crc),
                                                ('Version', self.replay.version),
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
            self.lst_meta.clear()
            self.lst_meta.addItems(self.meta_attributes.keys())
            self.meta_tab.setEnabled(True)

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
        logger.info('Netstream Parsed. No Errors found')
        self.analyser = Analyser(self.replay)
        self.cmb_player.clear()
        self.cmb_player.insertItems(0, [k for k in self.analyser.player.keys()])
        self.cmb_player.addItem('Ball')


class PopoutDialog(QDialog):

    def __init__(self, widget, title):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(300, 240)
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)


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


class FlowLayout(QLayout):
    # TODO SHIT GETS LAGGY WITH LOTS OF MPL Figures
    # TODO ASPECT RATIO IS HARDCODED. BETTER TAKE IT FROM WIDGETS WidthForHeight
    def __init__(self, parent=None, container=None, resize_threshold=(0, 0), margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []
        self.container = parent
        if container:
            self.container = container
        self.resize_threshold = resize_threshold

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def insertWidgetAt(self, index, widget):
        self.addWidget(widget)
        self.itemList.insert(index, self.itemList.pop(-1))

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def do_layout(self, rect, testonly):
        x = rect.x()
        y = rect.y()
        line_height = 0

        for item in self.itemList:
            wid = item.widget()
            space_x = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton,
                                                                 QSizePolicy.PushButton,
                                                                 Qt.Horizontal)
            space_y = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton,
                                                                 QSizePolicy.PushButton,
                                                                 Qt.Vertical)
            next_x = x + item.geometry().width() + space_x
            cont_width = self.container.geometry().width()+self.resize_threshold[0]
            cont_height = self.container.geometry().height()+self.resize_threshold[1]
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.geometry().width() + space_x
                line_height = 0
            adjust_height = False
            max_height = item.maximumSize().height()
            max_width = item.maximumSize().width()
            if cont_width*0.8 >= cont_height:
                adjust_height = True
            if cont_width >= max_width and cont_height >= max_height:
                item.setGeometry(QRect(x, y, max_width, max_height))
            elif adjust_height and cont_height <= max_height:
                item.setGeometry(QRect(x, y, 1.25*cont_height, cont_height))
            else:
                item.setGeometry(QRect(x, y, cont_width, 0.8*cont_width))
            x = next_x
            line_height = max(line_height, item.geometry().height())
        return y + line_height - rect.y()


class QtHandler(logging.Handler):

    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        # record = self.format(record)
        self.widget.appendPlainText(record.msg)


def excepthook(exc_type, exc_value, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param exc_type exception type
    @param exc_value exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    notice = "Exception encountered\n"  # TODO MORE INFOS
    tbinfofile = StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(exc_type), str(exc_value))
    sections = [separator, errmsg, separator, tbinfo]
    msg = '\n'.join(sections)
    errorbox = QMessageBox()
    errorbox.setText(str(notice)+str(msg))
    errorbox.exec_()

sys.excepthook = excepthook
logger = logging.getLogger('pyrain')
app = QApplication(sys.argv)
ui = PyRainGui()
ui.show()
sys.exit(app.exec_())
