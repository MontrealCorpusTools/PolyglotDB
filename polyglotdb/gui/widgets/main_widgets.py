import os

from PyQt5 import QtGui, QtCore, QtWidgets


from polyglotdb.config import CorpusConfig, is_valid_ipv4_address
from polyglotdb.corpus import CorpusContext, get_corpora_list
from polyglotdb.exceptions import (ConnectionError, PGError,
                            AuthorizationError,NetworkAddressError)

from polyglotdb.gui.workers import ImportCorpusWorker

from .basic import SafeWidget

from .io_widgets import CorpusSourceWidget

class ImportWidget(SafeWidget):
    supported_types = [(None, ''),('csv', 'Column-delimited file'),
                        ('running', 'Running text'),
                        ('ilg', 'Interlinear text'),
                        ('textgrid', 'TextGrid'),
                        ('multiple', 'Other standards'),]
    def __init__(self, parent):
        self._parent = parent
        super(ImportWidget, self).__init__(parent)
        return
        self.textType = None
        self.isDirectory = False

        self.createWidgets()

        layout = QtWidgets.QVBoxLayout()
        mainlayout = QtWidgets.QHBoxLayout()
        iolayout = QtWidgets.QFormLayout()
        pathlayout = QtWidgets.QHBoxLayout()

        self.pathWidget = CorpusSourceWidget()
        self.pathWidget.pathEdit.textChanged.connect(self.updateName)

        pathlayout.addWidget(QtWidgets.QLabel('Corpus source'))
        pathlayout.addWidget(self.pathWidget)

        self.nameEdit = QtWidgets.QLineEdit()
        pathlayout.addWidget(QtWidgets.QLabel('Corpus name'))
        pathlayout.addWidget(self.nameEdit)

        pathframe = QtWidgets.QWidget()
        pathframe.setLayout(pathlayout)
        iolayout.addRow(pathframe)

        ioframe = QtWidgets.QWidget()
        ioframe.setLayout(iolayout)

        mainlayout.addWidget(ioframe)

        self.tabWidget = QtWidgets.QTabWidget()

        optionlayout = QtWidgets.QFormLayout()

        csvFrame = QtWidgets.QWidget()
        csvlayout = QtWidgets.QFormLayout()
        csvlayout.addRow('Column delimiter (auto-detected)',self.columnDelimiterEdit)
        csvlayout.addRow(self.csvForceInspectButton)

        csvFrame.setLayout(csvlayout)
        self.tabWidget.addTab(csvFrame,'Column-delimited file')

        runningFrame = QtWidgets.QWidget()
        runninglayout = QtWidgets.QFormLayout()
        runninglayout.addRow('Text type', self.runningSelect)
        runningFrame.setLayout(runninglayout)
        self.tabWidget.addTab(runningFrame,'Running text')

        ilgFrame = QtWidgets.QWidget()
        ilglayout = QtWidgets.QFormLayout()
        ilglayout.addRow('Number of lines per gloss (auto-detected)', self.lineNumberEdit)
        ilglayout.addRow(self.ilgForceInspectButton)
        ilgFrame.setLayout(ilglayout)
        self.tabWidget.addTab(ilgFrame,'Interlinear text')

        tgFrame = QtWidgets.QWidget()
        tglayout = QtWidgets.QFormLayout()
        tgFrame.setLayout(tglayout)
        self.tabWidget.addTab(tgFrame,'TextGrid')

        multFrame = QtWidgets.QFrame()
        multlayout = QtWidgets.QFormLayout()
        multlayout.addRow('File format', self.multSelect)
        multFrame.setLayout(multlayout)
        self.tabWidget.addTab(multFrame,'Other standards')

        self.tabWidget.currentChanged.connect(self.typeChanged)

        mainframe = QtWidgets.QFrame()
        mainframe.setLayout(mainlayout)
        layout.addWidget(mainframe)

        iolayout.addWidget(self.tabWidget)
        previewlayout = QtWidgets.QVBoxLayout()
        previewlayout.addWidget(QtWidgets.QLabel('Parsing preview'))
        scroll = QtWidgets.QScrollArea()
        self.columnFrame = QtWidgets.QWidget()
        self.columns = []
        lay = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom)
        lay.addStretch()
        self.columnFrame.setLayout(lay)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.columnFrame)
        scroll.setMinimumWidth(140)
        policy = scroll.sizePolicy()
        policy.setVerticalStretch(1)
        scroll.setSizePolicy(policy)
        previewlayout.addWidget(scroll)
        mainlayout.addLayout(previewlayout)

        self.acceptButton = QtWidgets.QPushButton('Ok')
        self.acceptButton.setDefault(True)
        self.helpButton = QtWidgets.QPushButton('Help')
        acLayout = QtWidgets.QHBoxLayout()
        acLayout.addWidget(self.acceptButton)
        acLayout.addWidget(self.helpButton)
        self.acceptButton.clicked.connect(self.accept)
        self.helpButton.clicked.connect(self.help)

        acFrame = QtWidgets.QWidget()
        acFrame.setLayout(acLayout)

        layout.addWidget(acFrame)

        self.setLayout(layout)

        self.thread = ImportCorpusWorker()
        self.thread.errorEncountered.connect(self.handleError)

        self.progressDialog.setWindowTitle('Importing corpus...')
        self.progressDialog.beginCancel.connect(self.thread.stop)
        self.thread.updateProgress.connect(self.progressDialog.updateProgress)
        self.thread.updateProgressText.connect(self.progressDialog.updateText)
        self.thread.dataReady.connect(self.setResults)
        self.thread.dataReady.connect(self.progressDialog.accept)
        self.thread.finishedCancelling.connect(self.progressDialog.reject)

        self.typeChanged()
        print(self.progressDialog.isHidden())

    def createWidgets(self):
        self.columnDelimiterEdit = QtWidgets.QLineEdit()

        self.lineNumberEdit = QtWidgets.QLineEdit()

        self.csvForceInspectButton = QtWidgets.QPushButton('Reinspect')
        self.csvForceInspectButton.clicked.connect(self.forceInspect)

        self.ilgForceInspectButton = QtWidgets.QPushButton('Reinspect')
        self.ilgForceInspectButton.clicked.connect(self.forceInspect)

        self.csvForceInspectButton.setAutoDefault(False)
        self.ilgForceInspectButton.setAutoDefault(False)

        self.multSelect = QtWidgets.QComboBox()
        self.multSelect.addItem('Buckeye')
        self.multSelect.addItem('Timit')
        self.multSelect.currentIndexChanged.connect(self.typeChanged)

        self.runningSelect = QtWidgets.QComboBox()
        self.runningSelect.addItem('Orthography')
        self.runningSelect.addItem('Transcribed')
        self.runningSelect.currentIndexChanged.connect(self.typeChanged)


    def updateType(self, type):
        curIndex = self.tabWidget.currentIndex()
        if type == 'text':
            if not self.isDirectory and curIndex > 2:
                self.tabWidget.setTabEnabled(0,True)
                self.tabWidget.setCurrentIndex(0)
            elif self.isDirectory:
                self.tabWidget.setTabEnabled(1,True)
                self.tabWidget.setCurrentIndex(1)
                self.tabWidget.setTabEnabled(0,False)
            else:
                self.inspect()
        elif type == 'textgrid':
            if curIndex != 3:
                self.tabWidget.setTabEnabled(3,True)
                self.tabWidget.setCurrentIndex(3)
            else:
                self.inspect()
        elif type == 'multiple':
            if curIndex != 4:
                self.tabWidget.setTabEnabled(4,True)
                self.tabWidget.setCurrentIndex(4)
            else:
                self.inspect()
        elif type == 'csv':
            if curIndex != 0:
                self.tabWidget.setTabEnabled(0,True)
                self.tabWidget.setCurrentIndex(0)
            else:
                self.inspect()
        for i in range(self.tabWidget.count()):
            if type == 'text':
                if self.supported_types[i + 1][0] in ['csv', 'running','ilg']:
                    if self.isDirectory and self.supported_types[i + 1][0] == 'csv':
                        continue
                    self.tabWidget.setTabEnabled(i, True)
                else:
                    self.tabWidget.setTabEnabled(i, False)
            elif type == self.supported_types[i + 1][0]:
                self.tabWidget.setTabEnabled(i, True)
            else:
                self.tabWidget.setTabEnabled(i, False)

    def typeChanged(self):
        type = self.supported_types[self.tabWidget.currentIndex() + 1][0]
        if type == 'running':
            if self.runningSelect.currentText() == 'Orthography':
                type = 'spelling'
            else:
                type = 'transcription'
        elif type == 'multiple':
            if self.multSelect.currentText() == 'Buckeye':
                type = 'buckeye'
            else:
                type = 'timit'
        self.textType = type
        if self.isDirectory:
            t = 'text'
            if type == 'textgrid':
                t = type
            elif type in ['buckeye','timit']:
                t = 'multiple'
            self.pathWidget.updateType(t)
        self.inspect()

    def help(self):
        self.helpDialog = HelpDialog(self,name = 'loading corpora',
                                    section = 'using-a-custom-corpus')
        self.helpDialog.exec_()

    def setResults(self, results):
        self.corpus = results

    def delimiters(self):
        wordDelim = None
        colDelim = codecs.getdecoder("unicode_escape")(self.columnDelimiterEdit.text())[0]
        return wordDelim, colDelim

    def inspect(self):
        if self.textType is not None and os.path.exists(self.pathWidget.value()):
            if self.textType == 'csv':
                try:
                    atts, coldelim = inspect_csv(self.pathWidget.value())
                except PCTError:
                    self.updateColumnFrame([])
                    return
                self.columnDelimiterEdit.setText(coldelim.encode('unicode_escape').decode('utf-8'))
                self.updateColumnFrame(atts)
            else:
                if self.textType == 'textgrid':
                    anno_types = inspect_discourse_textgrid(self.pathWidget.value())
                elif self.textType == 'ilg':
                    anno_types = inspect_discourse_ilg(self.pathWidget.value())
                    self.lineNumberEdit.setText(str(len(anno_types)))
                elif self.textType == 'transcription':
                    anno_types = inspect_discourse_transcription(self.pathWidget.value())
                elif self.textType == 'spelling':
                    anno_types = inspect_discourse_spelling(self.pathWidget.value())
                elif self.textType in ['buckeye','timit']:

                    anno_types = inspect_discourse_multiple_files(self.pathWidget.value(), self.textType)
                self.updateColumnFrame(anno_types)

        else:
            self.updateColumnFrame([])

    def forceInspect(self, b):
        if os.path.exists(self.pathWidget.value()):
            if self.textType == 'csv':
                colDelim = codecs.getdecoder("unicode_escape")(self.columnDelimiterEdit.text())[0]
                if not colDelim:
                    colDelim = None
                atts, coldelim = inspect_csv(self.pathWidget.value(),
                        coldelim = colDelim)
                self.updateColumnFrame(atts)
            elif self.textType == 'ilg':
                number = self.lineNumberEdit.text()
                if number == '':
                    number = None
                else:
                    try:
                        number = int(number)
                    except:
                        number = None
                annotation_types = inspect_discourse_ilg(self.pathWidget.value(), number = number)
                self.updateColumnFrame(annotation_types)

    def updateColumnFrame(self, atts):
        for i in reversed(range(self.columnFrame.layout().count()-1)):
            w = self.columnFrame.layout().itemAt(i).widget()
            if w is None:
                del w
                continue
            w.setParent(None)
            w.deleteLater()
        self.columns = list()
        for a in reversed(atts):
            ignorable = self.textType not in ['spelling','transcription']
            c = AnnotationTypeWidget(a, ignorable = ignorable)
            self.columns.append(c)
            self.columnFrame.layout().insertWidget(0, c)

    def generateKwargs(self):
        path = self.pathWidget.value()
        if path == '':
            reply = QtWidgets.QMessageBox.critical(self,
                    "Missing information", "Please specify a file or directory.")
            return
        if not os.path.exists(path):
            reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information", "The specified path does not exist.")
            return
        name = self.nameEdit.text()
        if name == '':
            reply = QtWidgets.QMessageBox.critical(self,
                    "Missing information", "Please specify a name for the corpus.")
            return
        kwargs = {'corpus_name': name,
                    'path': path,
                    'isDirectory':self.isDirectory,
                    'text_type': self.textType}
        kwargs['annotation_types'] = [x.value() for x in reversed(self.columns)]
        if self.textType == 'csv':
            kwargs['delimiter'] = codecs.getdecoder("unicode_escape")(
                                        self.columnDelimiterEdit.text()
                                        )[0]
        elif self.textType in ['buckeye', 'timit']:
            if not self.isDirectory:
                base, ext = os.path.splitext(path)
                if ext == '.words':
                    phone_path = base +'.phones'
                elif ext == '.wrd':
                    phone_path = base + '.phn'
                if not os.path.exists(phone_path):
                    reply = QtWidgets.QMessageBox.critical(self,
                            "Invalid information", "The phone file for the specifie words file does not exist.")
                    return
                kwargs['word_path'] = kwargs.pop('path')
                kwargs['phone_path'] = phone_path
        if name in get_corpora_list(self.settings['storage']):
            msgBox = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, "Duplicate name",
                    "A corpus named '{}' already exists.  Overwrite?".format(name), QMessageBox.NoButton, self)
            msgBox.addButton("Overwrite", QtWidgets.QMessageBox.AcceptRole)
            msgBox.addButton("Abort", QtWidgets.QMessageBox.RejectRole)
            if msgBox.exec_() != QtWidgets.QMessageBox.AcceptRole:
                return None

        return kwargs

    def accept(self, b):
        kwargs = self.generateKwargs()
        if kwargs is None:
            return
        self.thread.setParams(kwargs)

        self.thread.start()
        result = self.progressDialog.exec_()

        self.progressDialog.reset()
        if result:
            pass

    def updateName(self):
        path = self.pathWidget.value()
        filename = os.path.split(path)[1]
        if os.path.isdir(path):
            self.isDirectory = True
            self.nameEdit.setText(filename)
            self.updateType(self.pathWidget.suggested_type)
            return
        name, ext = os.path.splitext(filename)
        ext = ext.lower()
        self.nameEdit.setText(name)
        self.isDirectory = False
        if ext == '.textgrid':
            self.updateType('textgrid')
        elif ext == '.csv':
            self.updateType('csv')
        elif ext in ['.words','.wrds']:
            self.updateType('multiple')
        elif ext == '.txt':
            self.updateType('text')

class ViewWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(ViewWidget, self).__init__(parent)

class CorporaList(QtWidgets.QGroupBox):
    selectionChanged = QtCore.pyqtSignal(object)
    def __init__(self, parent = None):
        super(CorporaList, self).__init__('Available corpora', parent)
        layout = QtWidgets.QVBoxLayout()

        self.corporaList = QtWidgets.QListWidget()
        self.corporaList.itemSelectionChanged.connect(self.changed)
        layout.addWidget(self.corporaList)
        self.setLayout(layout)

    def clear(self):
        self.corporaList.clear()

    def add(self, items):
        for i in items:
            self.corporaList.addItem(i)

    def changed(self):
        c = self.text()
        if c is None:
            c = ''
        self.selectionChanged.emit(c)

    def text(self):
        sel = self.corporaList.selectedItems()
        if not sel:
            return None
        return sel[0].text()


class ConnectWidget(QtWidgets.QWidget):
    configChanged = QtCore.pyqtSignal(object)
    def __init__(self, config = None, parent = None):
        super(ConnectWidget, self).__init__(parent)

        layout = QtWidgets.QHBoxLayout()
        self.formlayout = QtWidgets.QFormLayout()

        self.hostEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.hostEdit.setText(config.graph_host)
        else:
            self.hostEdit.setText('localhost')
        self.portEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.portEdit.setText(str(config.graph_port))
        else:
            self.portEdit.setText('7474')
        self.userEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.userEdit.setText(config.graph_user)
        self.passwordEdit = QtWidgets.QLineEdit()
        if config is not None:
            self.passwordEdit.setText(config.graph_password)
        self.passwordEdit.setEchoMode(QtWidgets.QLineEdit.Password)

        self.formlayout.addRow('IP address (or localhost)', self.hostEdit)
        self.formlayout.addRow('Port', self.portEdit)
        self.formlayout.addRow('Username (optional)', self.userEdit)
        self.formlayout.addRow('Password (optional)', self.passwordEdit)

        connectButton = QtWidgets.QPushButton('Connect')
        connectButton.clicked.connect(self.connectToServer)

        self.hostEdit.returnPressed.connect(connectButton.click)
        self.portEdit.returnPressed.connect(connectButton.click)
        self.userEdit.returnPressed.connect(connectButton.click)
        self.passwordEdit.returnPressed.connect(connectButton.click)
        self.formlayout.addRow(connectButton)

        layout.addLayout(self.formlayout)

        self.corporaList = CorporaList()
        self.corporaList.selectionChanged.connect(self.changeConfig)
        layout.addWidget(self.corporaList)

        self.setLayout(layout)
        if config is not None:
            self.connectToServer()

    def connectToServer(self, ignore = False):
        host = self.hostEdit.text()
        if host == '':
            if not ignore:
                reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information", "IP address must be specified or named 'localhost'.")
            return
        #elif host != 'localhost':
            #if not is_valid_ipv4_address(host):
            #    reply = QtWidgets.QMessageBox.critical(self,
            #            "Invalid information", "IP address must be properly specified.")
            #    return
        port = self.portEdit.text()
        try:
            port = int(port)
        except ValueError:
            if not ignore:
                reply = QtWidgets.QMessageBox.critical(self,
                    "Invalid information", "Port must be an integer.")
            return
        user = self.userEdit.text()
        if not user:
            user = None
        password = self.passwordEdit.text()
        if not password:
            password = None
        config = CorpusConfig('', graph_host = host, graph_port = port,
                        graph_user = user, graph_password = password)
        self.corporaList.clear()
        try:
            corpora = get_corpora_list(config)
            self.corporaList.add(corpora)
            self.configChanged.emit(config)
        except (ConnectionError, AuthorizationError, NetworkAddressError) as e:
            self.configChanged.emit(None)
            if not ignore:
                reply = QtWidgets.QMessageBox.critical(self,
                    "Could not connect to server", str(e))
            return

    def changeConfig(self, name):
        host = self.hostEdit.text()
        port = self.portEdit.text()
        user = self.userEdit.text()
        password = self.passwordEdit.text()
        config = CorpusConfig(name, graph_host = host, graph_port = port,
                        graph_user = user, graph_password = password)
        self.configChanged.emit(config)



class ExportWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(ExportWidget, self).__init__(parent)
