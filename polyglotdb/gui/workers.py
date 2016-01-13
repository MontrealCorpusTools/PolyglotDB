
from PyQt5 import QtGui, QtCore, QtWidgets

class FunctionWorker(QtCore.QThread):
    updateProgress = QtCore.pyqtSignal(object)
    updateProgressText = QtCore.pyqtSignal(str)
    errorEncountered = QtCore.pyqtSignal(object)
    finishedCancelling = QtCore.pyqtSignal()

    dataReady = QtCore.pyqtSignal(object)

    def __init__(self):
        super(FunctionWorker, self).__init__()
        self.stopped = False

    def setParams(self, kwargs):
        self.kwargs = kwargs
        self.kwargs['call_back'] = self.emitProgress
        self.kwargs['stop_check'] = self.stopCheck
        self.stopped = False
        self.total = None

    def stop(self):
        self.stopped = True

    def stopCheck(self):
        return self.stopped

    def emitProgress(self,*args):
        if isinstance(args[0],str):
            self.updateProgressText.emit(args[0])
            return
        elif isinstance(args[0],dict):
            self.updateProgressText.emit(args[0]['status'])
            return
        else:
            progress = args[0]
            if len(args) > 1:
                self.total = args[1]
        if self.total:
            self.updateProgress.emit((progress/self.total))


class ImportCorpusWorker(FunctionWorker):
    def run(self):
        time.sleep(0.1)
        textType = self.kwargs.pop('text_type')
        isDirectory = self.kwargs.pop('isDirectory')
        logging.info('Importing {} corpus named {}'.format(textType, self.kwargs['corpus_name']))
        logging.info('Path: '.format(self.kwargs['path']))
        log_annotation_types(self.kwargs['annotation_types'])
        try:
            if textType == 'spelling':

                if isDirectory:
                    corpus = load_directory_spelling(**self.kwargs)
                else:
                    corpus = load_discourse_spelling(**self.kwargs)
            elif textType == 'transcription':

                if isDirectory:
                    corpus = load_directory_transcription(**self.kwargs)
                else:
                    corpus = load_discourse_transcription(**self.kwargs)
            elif textType == 'ilg':

                if isDirectory:
                    corpus = load_directory_ilg(**self.kwargs)
                else:
                    corpus = load_discourse_ilg(**self.kwargs)
            elif textType == 'textgrid':
                if isDirectory:
                    corpus = load_directory_textgrid(**self.kwargs)
                else:
                    corpus = load_discourse_textgrid(**self.kwargs)
            elif textType == 'csv':
                corpus = load_corpus_csv(**self.kwargs)
            elif textType in ['buckeye', 'timit']:
                self.kwargs['dialect'] = textType
                if isDirectory:
                    corpus = load_directory_multiple_files(**self.kwargs)
                else:
                    corpus = load_discourse_multiple_files(**self.kwargs)
        except PCTError as e:
            self.errorEncountered.emit(e)
            return
        except Exception as e:
            e = PCTPythonError(e)
            self.errorEncountered.emit(e)
            return
        if self.stopped:
            time.sleep(0.1)
            self.finishedCancelling.emit()
            return
        self.dataReady.emit(corpus)
