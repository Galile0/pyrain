from PyQt5.QtCore import QSize, Qt, QRect, QThread, pyqtSignal, QPoint
from PyQt5.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QTabWidget, QPlainTextEdit, QGridLayout, QListWidget,
    QSpacerItem, QHBoxLayout, QScrollArea, QLayout, QToolBar, QLabel, QComboBox, QPushButton, QMenuBar, QMenu, QAction,
    QGroupBox, QFrame, QSlider, QCheckBox, QDialog, QApplication, QProgressBar, QMessageBox, QFileDialog, QMainWindow,
    QStatusBar)
import sys


class PyRainGui(QMainWindow):

    def __init__(self):
        super().__init__()
        
    def setup_ui(self):
        self.resize(720, 552)
        size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self.setSizePolicy(size_policy)
        self.setWindowTitle('PyRain - Replay Analysis Interface')
        
        self.centralwidget = QWidget(self)
        size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.centralwidget.setSizePolicy(size_policy)
        self.centralwidget.setMinimumSize(QSize(150, 50))
        central_grid = QGridLayout(self.centralwidget)
        central_grid.setSizeConstraint(QLayout.SetMinAndMaxSize)
        # self.listWidget = QListWidget(self.centralwidget)
        # self.listWidget.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        # self.listWidget.setMinimumSize(QSize(0, 0))
        # self.listWidget.setMaximumSize(QSize(200, 16777215))
        # central_grid.addWidget(self.listWidget, 0, 0, 1, 1)
        
        self.sa = QScrollArea(self.centralwidget)
        self.sa.setWidgetResizable(True)
        self.sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.sac = QWidget()
        self.sacl = FlowLayout(self.sac, container=self.sa, resize_threshold=(-20,-5))
        self.sa.setWidget(self.sac)
        central_grid.addWidget(self.sa, 0, 1, 1, 1)
        
        self.plainTextEdit = QPlainTextEdit(self.centralwidget)
        self.plainTextEdit.setMaximumSize(QSize(16777215, 100))
        central_grid.addWidget(self.plainTextEdit, 1, 0, 1, 2)

        self.setCentralWidget(self.centralwidget)
        self.plainTextEdit.textChanged.connect(self.dbg)
    def dbg(self):
        print(self.sa.sizeHint())
        print(self.sa.minimumSize())
        print(self.sa.minimumSizeHint())
        print(self.centralwidget.sizeHint())

        print('==================')
    def addLabels(self):
        lbl_list = []
        for i in range(10):
            lbl = QLabel(self.sac)
            lbl.setText("LABEL")
            lbl.setFrameShape(QFrame.Box)
            lbl.setLineWidth(5)
            lbl.setMinimumSize(50, 40)
            lbl.setMaximumSize(400, 320)
            size_policy = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            lbl.setSizePolicy(size_policy)
            self.sacl.addWidget(lbl)
            lbl_list.append(lbl)
        

class FlowLayout(QLayout):
    """
    BEHAVIOR:
        Takes elements with min and max size in. As long as its own width is smaller than what the child widget could do
        it resizes the child widget while keeping the aspect ratio. When the layouts width is bigger than the maximum of
        the child widget it stops the upscaling and instead kicks in when it finds enough space to place a second
        maximimized child widget next to it. Thats the flow part.
        TL;DR: Regular resizing from WidgetMin to WidgetMax. When max is reached freeflow takes control
    """
    def __init__(self, parent=None, container=None, resize_threshold=(0,0), margin=0, spacing=-1):
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

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.geometry().width() + spaceX
            cont_width = self.container.geometry().width()+self.resize_threshold[0]
            cont_height = self.container.geometry().height()+self.resize_threshold[1]
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.geometry().width() + spaceX
                lineHeight = 0
            adjust_height = False
            if cont_width*0.8 >= cont_height: adjust_height=True
            if cont_width >= item.maximumSize().width() and cont_height >= item.maximumSize().height():
                # Set widget width to maximum
                item.setGeometry(QRect(x, y, item.maximumSize().width(), item.maximumSize().height()))
            elif adjust_height and cont_height <= item.maximumSize().height():
                # Set widget height to fit layout height
                item.setGeometry(QRect(x, y, 1.25*cont_height, cont_height))
            else:
                # Set widget size to parent size
                item.setGeometry(QRect(x, y, cont_width, 0.8*cont_width))
            x = nextX
            lineHeight = max(lineHeight, item.geometry().height())
        return y + lineHeight - rect.y()

def excepthook(excType, excValue, tracebackobj):
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
ui.addLabels()
ui.show()
sys.exit(app.exec_())
