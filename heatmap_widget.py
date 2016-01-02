from os import path
import math
import logging

from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import (QGridLayout, QSizePolicy, QScrollArea, QWidget, QLabel, QComboBox,
                             QPushButton, QGroupBox, QSpacerItem, QListWidget, QAbstractItemView,
                             QFrame, QSlider, QCheckBox, QDialog, QVBoxLayout, QFileDialog)
from PyQt5.QtCore import Qt, QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from qt_ext import FlowLayout
from analyser import Analyser, AnalyserUtils
import plotter


class HeatmapWidget(QWidget):

    def __init__(self, replay=None, parent=None):
        super().__init__(parent)
        self.setEnabled(False)
        self.logger = logging.getLogger('pyrain')
        self.datasets = {}
        self.drawn_plots = {}
        self.scroll_area = None  # Scrollarea with figures
        self.flowlayout = None  # FLowlayout containing figures
        self.cmb_player = None  # Player Selection for data extraction
        self.cmb_slicing = None  # Splitting Datapoints selection
        self.lst_plots = None  # List with Datasets
        self.btn_removeplot = None
        self.btn_addplot = None
        self.btn_updateplot = None
        self.cmb_style = None  # Plot style
        self.chk_logscale = None  # Scale Logarithmic
        self.sld_res = None  # Bin Scaling for plots
        self._generate_widget()
        if replay:
            self.set_replay(replay)

    def set_replay(self, replay):
        self.replay = replay
        self.analyser = Analyser(self.replay)
        self.frm_extraction.setEnabled(True)
        self.cmb_player.clear()
        self.cmb_player.insertItems(0, [k for k in self.analyser.player.keys()])
        self.cmb_player.addItem('Ball')
        self.setEnabled(True)

    def _generate_widget(self):
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Ignored)
        self.setSizePolicy(size_policy)
        grid = QGridLayout(self)

        # CONTROLS
        box_controls = self._setup_controls()
        grid.addWidget(box_controls, 0, 0, 1, 1)

        # PLOTTING AREA
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setMinimumWidth(330)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        scrollarea_content = QWidget()
        self.flowlayout = FlowLayout(scrollarea_content,
                                     container=self.scroll_area,
                                     resize_threshold=(-20, -10))
        self.scroll_area.setWidget(scrollarea_content)
        grid.addWidget(self.scroll_area, 0, 1, 1, 1)

    def _setup_controls(self):
        groupbox = QGroupBox(self)
        size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        size_policy.setHorizontalStretch(1)
        size_policy.setHeightForWidth(groupbox.sizePolicy().hasHeightForWidth())
        groupbox.setSizePolicy(size_policy)
        groupbox.setMinimumSize(QSize(150, 372))
        groupbox.setMaximumSize(QSize(200, 16777215))
        groupbox.setAutoFillBackground(True)

        grid = QGridLayout(groupbox)
        grid.setHorizontalSpacing(0)

        self.frm_extraction = self._setup_extraction(groupbox)
        self.frm_extraction.setEnabled(False)
        grid.addWidget(self.frm_extraction, 1, 0, 1, 1)

        self.frm_settings = self._setup_settings(groupbox)
        self.frm_settings.setEnabled(False)
        grid.addWidget(self.frm_settings, 2, 0, 1, 1)

        self.frm_plots = self._setup_plots(groupbox)
        self.frm_plots.setEnabled(False)
        grid.addWidget(self.frm_plots, 3, 0, 1, 1)

        spacer = QSpacerItem(20, 2, QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        grid.addItem(spacer)

        return groupbox

    def _setup_extraction(self, parent):
        frame = QFrame(parent)
        frame.setMinimumSize(QSize(0, 100))
        frame.setFrameShape(QFrame.Box)
        frame.setFrameShadow(QFrame.Sunken)

        grid = QGridLayout(frame)
        grid.setContentsMargins(-1, -1, -1, 2)

        lbl_player = QLabel(frame)
        lbl_player.setText("Player:")
        grid.addWidget(lbl_player, 0, 0, 1, 1)
        self.cmb_player = QComboBox(frame)
        self.cmb_player.insertItems(0, ['No Replay Present'])
        grid.addWidget(self.cmb_player, 0, 1, 1, 1)

        lbl_slicing = QLabel(frame)
        lbl_slicing.setText('Slicing:')
        grid.addWidget(lbl_slicing, 1, 0, 1, 1)
        self.cmb_slicing = QComboBox(frame)
        self.cmb_slicing.insertItems(0, ['None', 'Goal'])
        grid.addWidget(self.cmb_slicing, 1, 1, 1, 1)

        btn_extract = QPushButton(frame)
        btn_extract.setText("Extract Data")
        grid.addWidget(btn_extract, 2, 0, 1, 2)

        btn_extract.clicked.connect(self._extract_data)

        return frame

    def _setup_settings(self, parent):
        frame = QFrame(parent)
        frame.setMinimumSize(QSize(0, 100))
        frame.setFrameShape(QFrame.Box)
        frame.setFrameShadow(QFrame.Sunken)

        grid = QGridLayout(frame)
        grid.setContentsMargins(-1, -1, -1, 2)

        lbl_style = QLabel(frame)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(lbl_style.sizePolicy().hasHeightForWidth())
        lbl_style.setSizePolicy(size_policy)
        lbl_style.setText('Style:')
        grid.addWidget(lbl_style, 0, 0, 1, 1)

        self.cmb_style = QComboBox(frame)
        self.cmb_style.setAutoFillBackground(False)
        self.cmb_style.setEditable(False)
        self.cmb_style.insertItems(0, ['Hexbin', 'Histogram - Blur', 'Histogram - Clear'])
        self.cmb_style.setCurrentIndex(0)
        grid.addWidget(self.cmb_style, 0, 1, 1, 3)

        self.chk_logscale = QCheckBox(frame)
        self.chk_logscale.setText('Logarithmic Scaling')
        grid.addWidget(self.chk_logscale, 1, 0, 1, 4)

        lbl_res = QLabel(frame)
        lbl_res.setText('Resolution:')
        grid.addWidget(lbl_res, 2, 0, 1, 4)

        self.sld_res = QSlider(frame)
        self.sld_res.setOrientation(Qt.Horizontal)
        self.sld_res.setMinimum(1)
        self.sld_res.setMaximum(50)
        self.sld_res.setValue(10)
        grid.addWidget(self.sld_res, 3, 0, 1, 4)

        return frame

    def _setup_plots(self, parent):
        # frame = QFrame(parent)
        frame = QWidget(parent)
        # frame.setFrameShape(QFrame.Box)
        # frame.setFrameShadow(QFrame.Sunken)

        grid = QGridLayout(frame)
        grid.setContentsMargins(1, 1, 1, 1)

        lbl_plots = QLabel(frame)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        size_policy.setHeightForWidth(lbl_plots.sizePolicy().hasHeightForWidth())
        lbl_plots.setSizePolicy(size_policy)
        lbl_plots.setText('Available Plots:')
        grid.addWidget(lbl_plots, 1, 0, 1, 6)

        self.lst_plots = QListWidget(frame)
        self.lst_plots.setSelectionMode(QAbstractItemView.ExtendedSelection)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        self.lst_plots.setSizePolicy(size_policy)
        self.lst_plots.setMinimumSize(QSize(0, 30))
        self.lst_plots.setMaximumSize(QSize(16777215, 200))
        grid.addWidget(self.lst_plots, 2, 0, 1, 6)

        self.btn_addplot = QPushButton(frame)
        self.btn_addplot.setText('Add')
        self.btn_addplot.setEnabled(False)
        grid.addWidget(self.btn_addplot, 3, 0, 1, 2)

        self.btn_removeplot = QPushButton(frame)
        self.btn_removeplot.setText('Delete')
        self.btn_removeplot.setEnabled(False)
        grid.addWidget(self.btn_removeplot, 3, 2, 1, 2)

        self.btn_updateplot = QPushButton(frame)
        self.btn_updateplot.setText('Update')
        self.btn_updateplot.setEnabled(False)
        grid.addWidget(self.btn_updateplot, 3, 4, 1, 2)

        btn_clearplot = QPushButton(frame)
        btn_clearplot.setText('Clear')
        grid.addWidget(btn_clearplot, 4, 0, 1, 3)

        btn_popout = QPushButton(frame)
        btn_popout.setText('Popout')
        grid.addWidget(btn_popout, 4, 3, 1, 3)

        btn_saveimage = QPushButton(frame)
        btn_saveimage.setText('Save as image')
        grid.addWidget(btn_saveimage, 5, 0, 1, 6)

        self.lst_plots.itemSelectionChanged.connect(self._highlight_plots)
        self.btn_removeplot.clicked.connect(self._remove_plots)
        self.btn_addplot.clicked.connect(self._create_plots)
        self.btn_updateplot.clicked.connect(self._update_plots)
        btn_popout.clicked.connect(self._popout_plots)
        btn_clearplot.clicked.connect(self._clear_plots)
        btn_saveimage.clicked.connect(self._save_plots)

        return frame

    def _extract_data(self):
        if not self.analyser:
            self.logger.error('Netstream not parsed yet.'
                              'Please import replay file and parse the Netstream')
            return
        self.frm_settings.setEnabled(True)
        self.frm_plots.setEnabled(True)
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
                self.logger.debug("Dataset already in Plotlist")
                continue
            self.lst_plots.addItem(entry['title_short'])
            self.datasets[entry['title_short']] = entry

    def _clear_plots(self):
        count = self.lst_plots.count()
        print(count)
        for i in range(count):
            item_name = self.lst_plots.item(i).text()
            if item_name in self.drawn_plots:
                self.drawn_plots[item_name].deleteLater()
                del self.drawn_plots[item_name]

    def _remove_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items]
        for item in items_text:
            if item in self.drawn_plots:
                self.drawn_plots[item].deleteLater()
                del self.drawn_plots[item]
        self._highlight_plots()

    def _update_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() in self.drawn_plots]
        for plot in items_text:
            old_widget = self.drawn_plots[plot]
            index = self.flowlayout.indexOf(old_widget)
            self.flowlayout.removeWidget(old_widget)
            new_widget = self._generate_plot_widget(plot)
            self.flowlayout.insertWidgetAt(index, new_widget)
            self.drawn_plots[plot] = new_widget
            old_widget.deleteLater()
        self._highlight_plots()

    def _create_plots(self):
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() not in self.drawn_plots]
        for item in items_text:
            self.flowlayout.addWidget(self._generate_plot_widget(item))
        self._highlight_plots()

    def _popout_plots(self):
        # plotter.graph_2d(self.analyser.calc_dist_to_zero(self.cmb_player.currentText(),
        #                                                  reference='Ball'))
        # return
        items = self.lst_plots.selectedItems()
        if not items:
            return
        items_text = [item.text() for item in items if item.text() in self.drawn_plots]
        self.popouts = []  # Reference so the dialogs wont get garbage collected
        for plot in items_text:
            figure = self.drawn_plots[plot].findChild(FigureCanvas).figure
            popout = PopoutDialog(FigureCanvas(figure), plot)
            popout.show()
            self.popouts.append(popout)

    def _save_plots(self):
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

    def _generate_plot_widget(self, datasetname):
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
                                       draw_map=[plotter.ARENA_OUTLINE,
                                                 plotter.ARENA_FIELDLINE,
                                                 plotter.ARENA_BOOST],
                                       bins=bins,
                                       norm=log,
                                       interpolate=interpolate,
                                       hexbin=hexbin)
        frm = QFrame()
        frm.setContentsMargins(0, 0, 0, 0)
        frm.setMinimumSize(QSize(280, 199))
        frm.setMaximumSize(QSize(650, 462))
        frm.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        frm.setLineWidth(3)
        palette = QPalette()
        palette.setColor(QPalette.Foreground, QColor(Qt.green))
        frm.setPalette(palette)
        frml = QVBoxLayout(frm)
        frml.setContentsMargins(0, 0, 0, 0)
        fig = FigureCanvas(plot)
        fig.mpl_connect('scroll_event', lambda evt: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().value()+int(evt.step)*-60))
        fig.setContentsMargins(0, 0, 0, 0)
        frml.addWidget(fig)
        self.drawn_plots[datasetname] = frm
        return frm

    def _highlight_plots(self):
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


class PopoutDialog(QDialog):

    def __init__(self, widget, title):
        super().__init__()
        self.setWindowTitle(title)
        self.setMinimumSize(300, 240)
        layout = QVBoxLayout(self)
        layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)