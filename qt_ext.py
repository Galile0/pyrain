import logging
from PyQt5.QtWidgets import QLayout, QSizePolicy
from PyQt5.QtCore import Qt, QRect, QSize


class FlowLayout(QLayout):
    # TODO SHIT GETS LAGGY WITH LOTS OF MPL Figures
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
            if not testonly:
                adjust_height = cont_width*0.8 >= cont_height
                max_height = item.maximumSize().height()
                max_width = item.maximumSize().width()
                scale_width = max_width/max_height
                scale_height = max_height/max_width
                if cont_width >= max_width and cont_height >= max_height:
                    item.setGeometry(QRect(x, y, max_width, max_height))
                elif adjust_height and cont_height <= max_height:
                    item.setGeometry(QRect(x, y, scale_width*cont_height, cont_height))
                else:
                    item.setGeometry(QRect(x, y, cont_width, scale_height*cont_width))
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