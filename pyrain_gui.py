import pickle
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
from os import path
from pyrope.replay import Replay


# class ProgressModal(QtWidgets.QProgressDialog):
#
#     def __init__(self):
#         super().__init__(labelText="Parsing Replay")
#         self.resize(402, 59)
#         self.setWindowTitle("Parsing Replay")

class PyRainGui(QtWidgets.QMainWindow):

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

    def setup_ui(self):
        self.resize(868, 552)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                            QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(size_policy)
        self.setWindowTitle('PyRain - Replay Analysis Interface')

        self.centralwidget = QtWidgets.QWidget(self)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                            QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(size_policy)

        vl_centralw = QtWidgets.QVBoxLayout(self.centralwidget)
        vl_centralw.setContentsMargins(-1, 9, -1, -1)

        hzl_1 = QtWidgets.QHBoxLayout()  # Main Container (Controls | Figure)

        box_controls = self.setup_controls()
        hzl_1.addWidget(box_controls)

        self.mpl_widget = QtWidgets.QWidget(self.centralwidget)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                            QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.mpl_widget.sizePolicy().hasHeightForWidth())
        self.mpl_widget.setSizePolicy(size_policy)
        self.mpl_widget.setMinimumSize(QtCore.QSize(356, 0))
        hzl_1.addWidget(self.mpl_widget)
        vl_centralw.addLayout(hzl_1)

        self.txt_log = QtWidgets.QPlainTextEdit(self.centralwidget)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.txt_log.sizePolicy().hasHeightForWidth())
        self.txt_log.setSizePolicy(size_policy)
        self.txt_log.setMaximumSize(QtCore.QSize(16777215, 100))
        vl_centralw.addWidget(self.txt_log)

        self.setCentralWidget(self.centralwidget)
        self.centralwidget.setEnabled(False)

        self.setup_menu()
        self.setup_toolbar()
        self.setup_signals()

    def setup_toolbar(self):
        toolbar = QtWidgets.QToolBar(self)
        toolbar.setStyleSheet('QToolBar{spacing:10px;}')
        toolbar.layout().setContentsMargins(7, 7, 7, 7)

        lbl_player = QtWidgets.QLabel()
        lbl_player.setText("Player:")
        toolbar.addWidget(lbl_player)
        self.cmb_player = QtWidgets.QComboBox()
        self.cmb_player.insertItems(0, ['No Replay Present'])
        toolbar.addWidget(self.cmb_player)

        toolbar.addSeparator()

        lbl_slicing = QtWidgets.QLabel()
        lbl_slicing.setText('Slicing:')
        toolbar.addWidget(lbl_slicing)
        self.cmb_slicing = QtWidgets.QComboBox()
        self.cmb_slicing.insertItems(0, ['None', 'Goal'])
        self.cmb_slicing.setMinimumSize(QtCore.QSize(100, 0))
        toolbar.addWidget(self.cmb_slicing)

        toolbar.addSeparator()

        self.btn_calc = QtWidgets.QPushButton()
        self.btn_calc.setText("Extract Data")
        toolbar.addWidget(self.btn_calc)
        self.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

    def setup_menu(self):
        menubar = QtWidgets.QMenuBar(self)
        menubar.setGeometry(QtCore.QRect(0, 0, 868, 21))
        menu_file = QtWidgets.QMenu(menubar)
        menu_file.setTitle('File')
        menubar.addAction(menu_file.menuAction())

        self.action_open = QtWidgets.QAction(self)
        self.action_open.setText('Open...')
        menu_file.addAction(self.action_open)

        self.action_exit = QtWidgets.QAction(self)
        self.action_exit.setText('Exit')
        menu_file.addAction(self.action_exit)

        self.setMenuBar(menubar)

    def setup_controls(self):
        box_controls = QtWidgets.QGroupBox(self.centralwidget)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(1)
        size_policy.setHeightForWidth(box_controls.sizePolicy().hasHeightForWidth())
        box_controls.setSizePolicy(size_policy)
        box_controls.setMinimumSize(QtCore.QSize(0, 285))
        box_controls.setMaximumSize(QtCore.QSize(200, 16777215))
        box_controls.setAutoFillBackground(True)

        vl_controls = QtWidgets.QVBoxLayout(box_controls)

        frm_settings = self.setup_settings(box_controls)
        vl_controls.addWidget(frm_settings)

        lbl_plots = QtWidgets.QLabel(box_controls)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(lbl_plots.sizePolicy().hasHeightForWidth())
        lbl_plots.setSizePolicy(size_policy)
        lbl_plots.setMinimumSize(QtCore.QSize(0, 0))
        lbl_plots.setText('Available Plots:')
        vl_controls.addWidget(lbl_plots)

        self.lst_plots = QtWidgets.QListWidget(box_controls)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(1)
        size_policy.setHeightForWidth(self.lst_plots.sizePolicy().hasHeightForWidth())
        self.lst_plots.setSizePolicy(size_policy)
        self.lst_plots.setMinimumSize(QtCore.QSize(0, 60))
        self.lst_plots.setMaximumSize(QtCore.QSize(16777215, 200))
        self.lst_plots.setFrameShape(QtWidgets.QFrame.Box)
        self.lst_plots.setFrameShadow(QtWidgets.QFrame.Sunken)
        vl_controls.addWidget(self.lst_plots)

        self.btn_popout = QtWidgets.QPushButton(box_controls)
        self.btn_popout.setText('Popout to new window')
        vl_controls.addWidget(self.btn_popout)

        self.btn_saveimage = QtWidgets.QPushButton(box_controls)
        self.btn_saveimage.setText('Save as image')
        vl_controls.addWidget(self.btn_saveimage)

        spc_5 = QtWidgets.QSpacerItem(20, 2, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        vl_controls.addItem(spc_5)

        return box_controls

    def setup_settings(self, box_controls):
        frm_settings = QtWidgets.QFrame(box_controls)
        frm_settings.setMinimumSize(QtCore.QSize(0, 100))
        frm_settings.setFrameShape(QtWidgets.QFrame.Box)
        frm_settings.setFrameShadow(QtWidgets.QFrame.Sunken)

        grl_settings = QtWidgets.QGridLayout(frm_settings)
        grl_settings.setContentsMargins(-1, -1, -1, 2)

        lbl_style = QtWidgets.QLabel(frm_settings)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(lbl_style.sizePolicy().hasHeightForWidth())
        lbl_style.setSizePolicy(size_policy)
        lbl_style.setText('Style:')
        grl_settings.addWidget(lbl_style, 0, 0, 1, 1)

        self.cmb_style = QtWidgets.QComboBox(frm_settings)
        self.cmb_style.setAutoFillBackground(False)
        self.cmb_style.setEditable(False)
        self.cmb_style.insertItems(0, ['Hexbin', 'Histogram - Blur', 'Histogram - Clear'])
        self.cmb_style.setCurrentIndex(0)
        grl_settings.addWidget(self.cmb_style, 0, 1, 1, 3)

        self.chk_logscale = QtWidgets.QCheckBox(frm_settings)
        self.chk_logscale.setText('Logarithmic Scaling')
        grl_settings.addWidget(self.chk_logscale, 1, 0, 1, 4)

        lbl_res = QtWidgets.QLabel(frm_settings)
        lbl_res.setText('Resolution:')
        grl_settings.addWidget(lbl_res, 2, 0, 1, 4)

        self.sld_res = QtWidgets.QSlider(frm_settings)
        self.sld_res.setOrientation(QtCore.Qt.Horizontal)
        grl_settings.addWidget(self.sld_res, 3, 0, 1, 4)

        return frm_settings

    def setup_signals(self):
        self.action_open.triggered.connect(self.show_open_file)
        self.action_exit.triggered.connect(self.close)

    def show_open_file(self):
        home = path.expanduser('~')
        # replay_folder = home+'\\My Games\\\Rocket League\\TAGame\\Demos'
        replay_folder = path.dirname(path.realpath(__file__))  # TODO DEV ONLY
        if not path.isdir(replay_folder):
            replay_folder = home
        ext = 'Replay (*.pyrope *.replay)'
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Replay', replay_folder, ext)
        if fname[0]:
            ext = fname[0].split('.')[-1]
            if ext == 'replay':
                self.replay = Replay(path=fname[0])
                self.show_progress()
            elif ext == '.pyrope':
                self.replay = pickle.load(open(fname[0], 'rb'))

    def show_progress(self):
        progress = QtWidgets.QProgressDialog(self)
        progress.setCancelButton('Mission Abort!')
        progress.setWindowTitle('Parsing Replay')
app = QtWidgets.QApplication(sys.argv)
ui = PyRainGui()
ui.setup_ui()
ui.show()
sys.exit(app.exec_())
