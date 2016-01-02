import json
from collections import OrderedDict

from PyQt5.QtWidgets import (QWidget, QListWidget, QPlainTextEdit, QGridLayout, QSizePolicy,
                             QSpacerItem)
from PyQt5.QtCore import QSize


class MetadataWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEnabled(False)
        self.lst_meta = None  # Attribute List
        self.txt_meta = None  # TextWidget for Attribute Display
        self.meta_attributes = None
        self._generate_widget()

    def set_replay(self, replay):
        self.replay = replay
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
        self.setEnabled(True)

    def _generate_widget(self):
        metaview_grid = QGridLayout(self)

        self.lst_meta = QListWidget(self)
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

        self.txt_meta = QPlainTextEdit(self)
        self.txt_meta.setMinimumWidth(356)
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)
        self.txt_meta.setSizePolicy(size_policy)
        metaview_grid.addWidget(self.txt_meta, 0, 2, 2, 1)

        self.lst_meta.itemSelectionChanged.connect(self._show_meta)

    def _show_meta(self):
        item = self.lst_meta.currentItem()
        data = self.meta_attributes[item.text()]
        if not data:
            data = "Empty Attribute"
        else:
            data = json.dumps(data, sort_keys=True, indent=4, separators=(',', ': '))
        self.txt_meta.setPlainText(data)
