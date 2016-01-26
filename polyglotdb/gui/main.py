
from PyQt5 import QtGui, QtCore, QtWidgets

from .widgets import (ConnectWidget, ViewWidget, ImportWidget, ExportWidget,
                        HorizontalTabWidget)

class MainWindow(QtWidgets.QMainWindow):
    configUpdated = QtCore.pyqtSignal(object)
    def __init__(self, app):
        super(MainWindow, self).__init__()

        self.corpusConfig = None

        self.connectWidget = ConnectWidget(parent = self)
        self.connectWidget.configChanged.connect(self.updateConfig)
        self.viewWidget = ViewWidget(self)
        self.importWidget = ImportWidget(self)
        self.exportWidget = ExportWidget(self)
        self.mainWidget = HorizontalTabWidget(self)
        self.mainWidget.addTab(self.viewWidget, 'Current corpus')
        self.mainWidget.addTab(self.importWidget, 'Import a corpus')
        self.mainWidget.addTab(self.exportWidget, 'Export a corpus')
        self.mainWidget.addTab(self.connectWidget, 'Connection')
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.mainWidget)
        splitter.setStretchFactor(0, 1)
        self.wrapper = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(splitter)
        self.wrapper.setLayout(layout)
        self.setCentralWidget(self.wrapper)

        self.status = QtWidgets.QLabel()
        self.statusBar().addWidget(self.status, stretch=1)
        self.setWindowTitle("PolyglotDB")
        self.createActions()
        self.createMenus()

        self.updateStatus()

    def updateConfig(self, config):
        self.corpusConfig = config
        self.updateStatus()
        self.configUpdated.emit(self.corpusConfig)

    def updateStatus(self):
        if self.corpusConfig is None:
            self.status.setText('No connection')
        else:
            c_name = self.corpusConfig.corpus_name
            if not c_name:
                c_name = 'No corpus selected'
            self.status.setText('Connected to {} ({})'.format(self.corpusConfig.graph_hostname, c_name))


    def createActions(self):

        self.connectAct = QtWidgets.QAction( "Connect to corpus...",
                self,
                statusTip="Connect to a corpus", triggered=self.connect)

        self.importAct = QtWidgets.QAction( "Import a  corpus...",
                self,
                statusTip="Import a corpus", triggered=self.importCorpus)

        self.specifyAct = QtWidgets.QAction( "Add phonological features...",
                self,
                statusTip="Specify a corpus", triggered=self.specifyCorpus)

        self.exportAct = QtWidgets.QAction( "Export a  corpus...",
                self,
                statusTip="Export a corpus", triggered=self.exportCorpus)

    def createMenus(self):
        self.corpusMenu = self.menuBar().addMenu("Corpus")
        self.corpusMenu.addAction(self.connectAct)

        self.corpusMenu.addSeparator()
        self.corpusMenu.addAction(self.importAct)
        self.corpusMenu.addAction(self.specifyAct)
        self.corpusMenu.addAction(self.exportAct)

    def connect(self):
        pass

    def importCorpus(self):
        pass

    def specifyCorpus(self):
        pass

    def exportCorpus(self):
        pass
