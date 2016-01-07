import json
import pickle
import traceback
import sys
import logging

from os import path
from queue import Queue
from threading import Thread, Event
from io import StringIO
from time import sleep, time

from PyQt5.QtCore import QSize, Qt, QRect, QThread, pyqtSignal
from PyQt5.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit,
                             QLayout, QPushButton, QMenuBar, QMenu, QAction, QDialog, QApplication,
                             QProgressBar, QMessageBox, QFileDialog, QMainWindow)

from analyser import Analyser
from distance_widget import DistanceWidget
from qt_ext import QtHandler
from heatmap_widget import HeatmapWidget
from metadata_widget import MetadataWidget
from pyrope import Replay


class PyRainGui(QMainWindow):

    def __init__(self):
        super().__init__()
        self.replay = None
        self.analyser = None
        self.setup_ui()
        handler = QtHandler(self.txt_log)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.info('Setup Completed. Welcome to PyRain')

    def setup_ui(self):
        self.resize(1280, 530)
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
        layout = QVBoxLayout(self.centralwidget)
        # layout.setContentsMargins(-1, 9, -1, -1)

        tabview = QTabWidget(self.centralwidget)
        tabview.setTabPosition(QTabWidget.North)

        self.meta_tab = MetadataWidget(parent=tabview)
        tabview.addTab(self.meta_tab, "MetaData")

        self.heatmap_tab = HeatmapWidget(parent=tabview)
        self.heatmap_tab.setMinimumSize(QSize(0, 380))
        tabview.addTab(self.heatmap_tab, "Heatmaps")

        self.distance_tab = DistanceWidget(parent=tabview)
        tabview.addTab(self.distance_tab, "Distances")

        self.txt_log = QPlainTextEdit(self.centralwidget)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        size_policy.setHeightForWidth(self.txt_log.sizePolicy().hasHeightForWidth())
        self.txt_log.setSizePolicy(size_policy)
        self.txt_log.setMaximumSize(QSize(16777215, 100))
        self.txt_log.hide()

        layout.addWidget(tabview)
        layout.addWidget(self.txt_log)
        self.setCentralWidget(self.centralwidget)

        self.setup_menu()

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

    def export_data(self):
        if not self.replay:
            logger.error("Nothing to Export")
            return
        folder = path.dirname(path.realpath(__file__))
        ext = 'Replay (*.pyrope);;MetaData (*.json);;Header (*.json);;Netstream (*.json)'
        filename = QFileDialog.getSaveFileName(self, 'Export Replay', folder, ext)
        if filename[0]:
            if 'Replay' in filename[1]:
                pickle.dump(self.replay, open(filename[0], 'wb'), protocol=-1)
            elif 'MetaData' in filename[1]:
                with open(filename[0], 'w', encoding='utf-8') as outfile:
                    outfile.write(self.replay.metadata_to_json())
            elif 'Header' in filename[1]:
                with open(filename[0], 'w', encoding='utf-8') as outfile:
                    json.dump(self.replay.header, outfile, indent=2, ensure_ascii=False)
            elif 'Netstream' in filename[1]:
                if not self.replay.netstream:
                    logger.error('Netstream not parsed')
                    return
                with open(filename[0], 'w', encoding='utf-8') as outfile:
                    outfile.write(self.replay.netstream_to_json())

    def toggle_log(self):
        self.txt_log.setVisible(not self.txt_log.isVisible())

    def import_data(self):
        home = path.expanduser('~')
        replay_folder = home+'\\Documents\\My Games\\\Rocket League\\TAGame\\Demos'
        # replay_folder = path.dirname(path.realpath(__file__))+'\\testfiles'
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
                # start = time()
                self.replay = pickle.load(open(fname[0], 'rb'))
                # print("UNPICKLING: %f" % (time()-start))
                logger.info('pyrain Parsed Replay File sucessfully loaded')
                self.netstream_loaded()
            self.meta_tab.set_replay(self.replay)

    def show_progress(self):
        num_frames = self.replay.header['NumFrames']-1
        progress = ProgressDialog(self, num_frames)
        ti = ThreadedImport(self, self.replay)
        ti.progress.connect(progress.set_value)
        ti.done.connect(self.netstream_loaded)
        ti.exception.connect(lambda e: [progress.close(), self.netstream_error(e)])
        progress.btn_cancel.clicked.connect(ti.setstop)
        progress.show()
        ti.start()

    def netstream_error(self, exc):
        raise exc

    def netstream_loaded(self):
        # start = time()
        analyser = Analyser(self.replay)
        # print("analyser: %f" % (time()-start))
        # start = time()
        self.heatmap_tab.set_analyser(analyser)
        # print("heatmap: %f" % (time()-start))
        # start = time()
        self.distance_tab.set_analyser(analyser)
        # print("distance: %f" % (time()-start))
        logger.info('Netstream Parsed. No Errors found')


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
    exception = pyqtSignal(Exception)

    def __init__(self, parent, replay):
        QThread.__init__(self, parent)
        self.replay = replay
        self.stop = Event()

    def run(self):
        qout = Queue()
        parse_thread = Thread(target=self.replay.parse_netstream, args=(qout, self.stop))
        parse_thread.start()
        while not self.stop.isSet():
            if qout.empty():
                sleep(0.1)
                continue
            msg = qout.get()
            if msg == 'done':
                self.done.emit()
                return
            elif msg == 'exception':
                exc = qout.get()
                self.exception.emit(exc)
                return
            else:
                self.progress.emit(msg)

    def setstop(self):
        self.stop.set()


def excepthook(exc_type, exc_value, tracebackobj):
    """
    Global function to catch unhandled exceptions.

    @param exc_type exception type
    @param exc_value exception value
    @param tracebackobj traceback object
    """
    separator = '-' * 80
    notice = "Error\n"
    tbinfofile = StringIO()
    traceback.print_tb(tracebackobj, None, tbinfofile)
    tbinfofile.seek(0)
    tbinfo = tbinfofile.read()
    errmsg = '%s: \n%s' % (str(exc_type), str(exc_value))
    sections = [separator, errmsg, separator, tbinfo]
    with open('error.log', mode='w', encoding='utf-8') as outfile:
        json.dump(exc_value.args, outfile, indent=2, ensure_ascii=False)
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
