from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QListWidget, QAbstractItemView,
                             QPushButton, QGridLayout, QLabel, QComboBox, QSizePolicy,
                             QSpacerItem, QGroupBox)
from PyQt5.QtCore import QSize
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import itertools

import plotter
from rangeslider import QRangeSlider

WHITE = QBrush(QColor(255, 255, 255))


class DistanceWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plots = {}
        self.overlaps = {}
        self.ax = None
        self.analyser = None
        self._generate_widget()
        self.setEnabled(False)

    def set_analyser(self, analyser):
        # Reset Internal Variables and remove plots
        self.plots = {}
        self.overlaps = {}
        self.lst_plots.clear()
        while self.ax.lines:
            self.ax.lines[-1].remove()
        self.ax.relim()
        self.canvas.setVisible(False)
        self.range.setMin(500)
        self.range.setMax(0)
        self.range.setRange(0, 500)
        self.range.setVisible(False)
        # Populate GUI
        self.analyser = analyser
        players = list(self.analyser.player_data.keys())
        self.overlaps = {player: [] for player in players}
        self.overlaps['Ball'] = players
        for pair in itertools.permutations(players, 2):
            if self._overlap(self.analyser.player_data[pair[0]],
                             self.analyser.player_data[pair[1]]):
                self.overlaps[pair[0]].append(pair[1])
        [x.extend(['Ball', '(0,0,0)']) for x in self.overlaps.values()]
        self.cmb_player.clear()
        self.cmb_player.insertItems(0, [k for k in analyser.player_data])
        self.cmb_player.addItem('Ball')
        self.setEnabled(True)

    def _overlap(self, player, reference):
        for actor in player:
            seperate = any(actor['join'] > cdata['left'] or
                           cdata['join'] > actor['left']
                           for cdata in reference)
            if seperate:
                return False
        return True

    def _update_ref(self, text):
        if text:
            self.cmb_ref.clear()
            self.cmb_ref.insertItems(0, self.overlaps[text])

    def _generate_widget(self):
        layout_main = QGridLayout(self)

        layout_main.addWidget(self._setup_controls(), 0, 0, 2, 1)

        frm_plot = QFrame(self)
        frm_plot.setFrameStyle(0x36)
        plot_layout = QHBoxLayout(frm_plot)
        frm_plot.setMinimumWidth(350)
        fig = Figure()
        self.ax = fig.add_subplot(111)
        plotter.set_colormap(self.ax)
        self.ax.hold(True)
        self.canvas = FigureCanvas(fig)
        self.canvas.setVisible(False)
        plot_layout.addWidget(self.canvas)
        layout_main.addWidget(frm_plot, 0, 1, 1, 1)

        self.range = QRangeSlider(self)
        self.range.setMin(500)
        self.range.setMax(0)
        self.range.startValueChanged.connect(self._set_xmin)
        self.range.endValueChanged.connect(self._set_xmax)
        self.range.setFixedHeight(30)
        self.range.setBackgroundStyle("""
                                         #Head {
                                             border: 2px #65737e;
                                             border-style: solid none solid solid;
                                         }
                                         #Tail {
                                             border: 2px #65737e;
                                             border-style: solid solid solid none;
                                         }
                                      """)
        self.range.setVisible(False)
        layout_main.addWidget(self.range, 1, 1, 1, 1)

    def _setup_controls(self):
        groupbox = QGroupBox(self)
        size_policy = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        size_policy.setHorizontalStretch(1)
        size_policy.setHeightForWidth(groupbox.sizePolicy().hasHeightForWidth())
        groupbox.setSizePolicy(size_policy)
        groupbox.setMinimumSize(QSize(150, 372))
        groupbox.setMaximumWidth(200)
        groupbox.setAutoFillBackground(True)

        grid = QGridLayout(groupbox)
        grid.setHorizontalSpacing(0)

        grid.addWidget(self._setup_extraction(groupbox), 0, 0, 1, 1)
        grid.addWidget(self._setup_plotctrl(groupbox), 1, 0, 1, 1)

        return groupbox

    def _setup_extraction(self, parent):
        frame = QFrame(parent)
        frame.setFrameShape(QFrame.Box)
        frame.setFrameShadow(QFrame.Sunken)
        frame.setMinimumSize(QSize(0, 100))

        grid = QGridLayout(frame)
        grid.setContentsMargins(-1, -1, -1, 2)

        lbl_headline = QLabel(frame)
        lbl_headline.setText("Distance between:")
        grid.addWidget(lbl_headline, 0, 0, 1, 2)

        lbl_player = QLabel(frame)
        lbl_player.setText("Player:")
        grid.addWidget(lbl_player, 1, 0, 1, 1)
        self.cmb_player = QComboBox(frame)
        self.cmb_player.insertItems(0, ['----'])
        self.cmb_player.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        self.cmb_player.currentTextChanged.connect(self._update_ref)
        grid.addWidget(self.cmb_player, 1, 1, 1, 1)

        lbl_ref = QLabel(frame)
        lbl_ref.setText("Reference:")
        grid.addWidget(lbl_ref, 2, 0, 1, 1)
        self.cmb_ref = QComboBox(frame)
        self.cmb_ref.insertItems(0, ['----'])
        grid.addWidget(self.cmb_ref, 2, 1, 1, 1)

        btn_add = QPushButton(frame)
        btn_add.setText('Add Plot')
        grid.addWidget(btn_add, 3, 0, 1, 2)
        btn_add.clicked.connect(self._add_plot)
        return frame

    def _setup_plotctrl(self, parent):
        frame = QWidget(parent)
        grid = QGridLayout(frame)
        grid.setContentsMargins(1, 1, 1, 1)

        self.lst_plots = QListWidget(frame)
        self.lst_plots.setSelectionMode(QAbstractItemView.ExtendedSelection)
        size_policy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.MinimumExpanding)
        size_policy.setVerticalStretch(1)
        self.lst_plots.setSizePolicy(size_policy)
        self.lst_plots.setMinimumSize(QSize(0, 30))
        self.lst_plots.setMaximumHeight(350)
        self.lst_plots.itemSelectionChanged.connect(self._toggle_buttons)
        self.lst_plots.itemDoubleClicked.connect(self._toggle_plot)
        grid.addWidget(self.lst_plots, 0, 0, 1, 2)

        btn_show = QPushButton(frame)
        btn_show.setText('Show')
        grid.addWidget(btn_show, 1, 0, 1, 1)
        btn_show.clicked.connect(self._show_plot)
        btn_show.setEnabled(False)
        btn_hide = QPushButton(frame)
        btn_hide.setText('Hide')
        btn_hide.setEnabled(False)
        grid.addWidget(btn_hide, 1, 1, 1, 1)
        btn_hide.clicked.connect(self._hide_plot)

        spacer = QSpacerItem(20, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        grid.addItem(spacer, 2, 0, 1, 2)

        self.buttons = {'show': btn_show,
                        'hide': btn_hide}
        return frame

    def _add_plot(self):
        player = self.cmb_player.currentText()
        reference = self.cmb_ref.currentText()
        label1 = player + ' - ' + reference
        label2 = reference + ' - ' + player
        if label1 not in self.plots and label2 not in self.plots: # create new lineplot
            reference = None if reference == '(0,0,0)' else reference
            dot = self.analyser.calc_dist(player, reference)
            lines = plotter.lines2d(dot['time'], dot['distance'], self.ax)
            [line.remove() for line in lines]
            self.plots[label1] = lines
            self.lst_plots.addItem(label1)
            item = self.lst_plots.item(self.lst_plots.count()-1)
            item.setBackground(WHITE)
            item.setToolTip('Average Distance: '+str(int(lines[1].get_ydata()[0])))

    def _show_plot(self):
        self.canvas.setVisible(True)
        self.range.setVisible(True)
        self.ax.autoscale(enable=True, axis='both', tight=True)
        for item in self.lst_plots.selectedItems():
            for plot in self.plots[item.text()]:
                if plot not in self.ax.lines:
                    self.ax.lines.append(plot)
            color = plotter.get_rgb(self.plots[item.text()][0])
            item.setBackground(QBrush(QColor(color)))
        self.canvas.draw()
        self.canvas.figure.tight_layout()
        self._update_range()
        self._toggle_buttons()

    def _hide_plot(self):
        for item in self.lst_plots.selectedItems():
            for plot in self.plots[item.text()]:
                if plot in self.ax.lines:
                    plot.remove()
            item.setBackground(WHITE)
        self.canvas.draw()
        self.canvas.figure.tight_layout()
        self._toggle_buttons()

    def _toggle_buttons(self):
        selected = [item.text() for item in self.lst_plots.selectedItems()]
        if not selected:
            for btn in self.buttons.values():
                btn.setEnabled(False)
        else:
            for item in selected:
                if self.plots[item][1] in self.ax.lines:
                    self.buttons['hide'].setEnabled(True)
                else:
                    self.buttons['show'].setEnabled(True)

    def _toggle_plot(self, item):
        if item.background().color().getRgb() == WHITE.color().getRgb():
            self._show_plot()
        else:
            self._hide_plot()

    def _set_xmin(self, val):
        self.ax.set_xlim(left=val)
        self.canvas.draw()

    def _set_xmax(self, val):
        self.ax.set_xlim(right=val)
        self.canvas.draw()

    def _update_range(self):
        xlim = self.ax.get_xlim()
        xlim = [int(xlim[0]), int(xlim[1])]
        if xlim[0] <= self.range.min():
            self.range.setMin(xlim[0])
            self.range.setStart(xlim[0])
        if xlim[1] >= self.range.max():
            self.range.setMax(xlim[1])
            self.range.setEnd(xlim[1])
        self.range.repaint()
