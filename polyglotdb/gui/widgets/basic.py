import os
from PyQt5 import QtGui, QtCore, QtWidgets

class FileWidget(QtWidgets.QFrame):
    def __init__(self, title, filefilter, parent=None):
        super(FileWidget, self).__init__(parent)

        self.title = title

        self.filefilter = filefilter

        pathLayout = QtWidgets.QHBoxLayout()
        self.pathEdit = QLineEdit()
        pathButton = QtWidgets.QPushButton('Choose file...')
        pathButton.setAutoDefault(False)
        pathButton.setDefault(False)
        pathButton.clicked.connect(self.pathSet)
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(pathButton)
        self.setLayout(pathLayout)

        self.textChanged = self.pathEdit.textChanged

    def pathSet(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self,self.title, filter=self.filefilter)
        if filename:
            self.pathEdit.setText(filename[0])

    def value(self):
        return self.pathEdit.text()

class SaveFileWidget(QtWidgets.QFrame):
    def __init__(self,title,filefilter,parent=None):
        super(SaveFileWidget, self).__init__(parent)

        self.title = title

        self.filefilter = filefilter

        pathLayout = QtWidgets.QHBoxLayout()
        self.pathEdit = QtWidgets.QLineEdit()
        pathButton = QtWidgets.QPushButton('Choose file...')
        pathButton.setAutoDefault(False)
        pathButton.setDefault(False)
        pathButton.clicked.connect(self.pathSet)
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(pathButton)
        self.setLayout(pathLayout)

        self.textChanged = self.pathEdit.textChanged

    def pathSet(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self,self.title, filter=self.filefilter)
        if filename:
            self.pathEdit.setText(filename[0])

    def value(self):
        return self.pathEdit.text()

class DirectoryWidget(QtWidgets.QFrame):
    def __init__(self,parent=None):
        super(DirectoryWidget, self).__init__(parent)

        pathLayout = QtWidgets.QHBoxLayout()
        self.pathEdit = QtWidgets.QLineEdit()
        pathButton = QtWidgets.QPushButton('Choose directory...')
        pathButton.setAutoDefault(False)
        pathButton.setDefault(False)
        pathButton.clicked.connect(self.pathSet)
        pathLayout.addWidget(self.pathEdit)
        pathLayout.addWidget(pathButton)
        self.setLayout(pathLayout)

        self.textChanged = self.pathEdit.textChanged

    def setPath(self,path):
        self.pathEdit.setText(path)

    def pathSet(self):
        filename = QtWidgets.QFileDialog.getExistingDirectory(self,"Choose a directory")
        if filename:
            self.pathEdit.setText(filename)

    def value(self):
        return self.pathEdit.text()

class SegmentButton(QtWidgets.QPushButton):
    def sizeHint(self):
        sh = super(SegmentButton, self).sizeHint()

        sh.setHeight(self.fontMetrics().boundingRect(self.text()).height()+14)
        sh.setWidth(self.fontMetrics().boundingRect(self.text()).width()+14)
        return sh

class NonScrollingComboBox(QtWidgets.QComboBox):
    def __init__(self, parent = None):
        super(NonScrollingComboBox, self).__init__(parent)
        self.setFocusPolicy(QtCode.Qt.StrongFocus)

    def wheelEvent(self, e):
        e.ignore()

class HorizontalTabBar(QtWidgets.QTabBar):

    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        option = QtWidgets.QStyleOptionTab()

        for index in range(self.count()):
            self.initStyleOption(option, index)
            tabRect = self.tabRect(index)
            tabRect.moveLeft(10)
            painter.drawControl(QtWidgets.QStyle.CE_TabBarTabShape, option)
            painter.drawText(tabRect, QtCore.Qt.AlignVCenter | QtCore.Qt.TextDontClip,
                             self.tabText(index))
        painter.end()

    def tabSizeHint(self,index):
        sh = super(HorizontalTabBar, self).tabSizeHint(index)

        sh.setHeight(self.fontMetrics().boundingRect(self.tabText(index)).height()+14)
        sh.setWidth(self.fontMetrics().boundingRect(self.tabText(index)).width()+14)
        #sh.setHeight(500)
        #sh.setWidth(500)
        return sh

class HorizontalTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent, *args):
        super(HorizontalTabWidget, self).__init__(parent, *args)
        self.setTabBar(HorizontalTabBar(self))
        self.setTabPosition(QtWidgets.QTabWidget.West)


class SafeWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(SafeWidget, self).__init__(parent)

        self.progressDialog = ProgressDialog(self)

    def handleError(self, error):
        if isinstance(error, PGError):
            if hasattr(error, 'main'):
                reply = QtWidgets.QMessageBox()
                reply.setWindowTitle('Error encountered')
                reply.setIcon(QtWidgets.QMessageBox.Critical)
                reply.setText(error.main)
                reply.setInformativeText(error.information)
                reply.setDetailedText(error.details)

                if hasattr(error,'print_to_file'):
                    error.print_to_file(self.parent().settings.error_directory())
                    reply.addButton('Open errors directory', QtWidgets.QMessageBox.AcceptRole)
                reply.setStandardButtons(QMessageBox.Close)
                ret = reply.exec_()
                if ret == QtWidgets.QMessageBox.AcceptRole:
                    error_dir = self.parent().settings.error_directory()
                    if sys.platform == 'win32':
                        args = ['{}'.format(error_dir)]
                        program = 'explorer'
                        #subprocess.call('explorer "{0}"'.format(self.parent().settings.error_directory()),shell=True)
                    elif sys.platform == 'darwin':
                        program = 'open'
                        args = ['{}'.format(error_dir)]
                    else:
                        program = 'xdg-open'
                        args = ['{}'.format(error_dir)]
                    #subprocess.call([program]+args,shell=True)
                    proc = QtCore.QProcess(self.parent())
                    t = proc.startDetached(program,args)
            else:
                reply = QtWidgets.QMessageBox.critical(self,
                        "Error encountered", str(error))
        else:
            reply = QtWidgets.QMessageBox.critical(self,
                    "Error encountered", str(error))
        self.progressDialog.reject()
        return None

class ProgressDialog(QtWidgets.QProgressDialog):
    beginCancel = QtCore.pyqtSignal()
    def __init__(self, parent):
        super(ProgressDialog, self).__init__(parent)
        self.setMinimumWidth(500)
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        self.setAutoClose(False)
        self.setAutoReset(False)
        self.setCancelButton(self.cancelButton)

        self.information = ''
        self.startTime = None

        self.rates = list()
        self.eta = None

        self.beginCancel.connect(self.updateForCancel)
        b = self.findChildren(QtWidgets.QPushButton)[0]
        b.clicked.disconnect()
        b.clicked.connect(self.cancel)
        self.hide()

    def cancel(self):
        self.beginCancel.emit()

    def updateForCancel(self):
        self.show()
        self.setMaximum(0)
        self.cancelButton.setEnabled(False)
        self.cancelButton.setText('Canceling...')
        self.setLabelText('Canceling...')

    def reject(self):
        QtWidgets.QProgressDialog.cancel(self)

    def updateText(self,text):
        if self.wasCanceled():
            return
        self.information = text
        eta = 'Unknown'

        self.setLabelText('{}\nTime left: {}'.format(self.information,eta))

    def updateProgress(self, progress):
        if self.wasCanceled():
            return
        if progress == 0:
            self.setMaximum(100)
            self.cancelButton.setText('Cancel')
            self.cancelButton.setEnabled(True)
            self.startTime = time.time()

            self.eta = None
        else:
            elapsed = time.time() - self.startTime
            self.rates.append(elapsed / progress)
            self.rates = self.rates[-20:]
            if len(self.rates) > 18:

                rate = sum(self.rates)/len(self.rates)
                eta = int((1 - progress) * rate)
                if self.eta is None:
                    self.eta = eta
                if eta < self.eta or eta > self.eta + 10:
                    self.eta = eta
        self.setValue(progress*100)
        if self.eta is None:
            eta = 'Unknown'

        else:
            if self.eta < 0:
                self.eta = 0
            eta = str(datetime.timedelta(seconds = self.eta))
        self.setLabelText('{}\nEstimated time left: {}'.format(self.information,eta))

