import os
from PyQt5 import QtGui, QtCore, QtWidgets

class AnnotationTypeWidget(QtWidgets.QGroupBox):
    def __init__(self, annotation_type, parent = None,
                ignorable = True):
        #if title is None:
        #    title = 'Annotation type details'
        super(AnnotationTypeWidget, self).__init__(annotation_type.name, parent)
        return
        main = QtWidgets.QHBoxLayout()

        #main.addWidget(QLabel(annotation_type.name))

        self.annotation_type = annotation_type

        proplayout = QtWidgets.QFormLayout()

        self.nameWidget = QtWidgets.QLineEdit()

        proplayout.addRow('Name',self.nameWidget)

        self.typeWidget = NonScrollingComboBox()
        self.typeWidget.addItem('Orthography')
        self.typeWidget.addItem('Transcription')
        self.typeWidget.addItem('Other (numeric)')
        self.typeWidget.addItem('Other (character)')
        if ignorable:
            self.typeWidget.addItem('Notes (ignored)')
        self.typeWidget.setCurrentIndex(3)
        proplayout.addRow('Annotation type',self.typeWidget)
        self.typeWidget.currentIndexChanged.connect(self.typeChanged)

        self.associationWidget = RadioSelectWidget('Word association',
                                            OrderedDict([
                                            ('Associate this with the lexical item','type'),
                                            ('Allow this property to vary within lexical items','token'),]))

        proplayout.addRow(self.associationWidget)

        self.delimiterLabel = QtWidgets.QLabel('None')
        if self.annotation_type.delimiter is not None:
            self.delimiterLabel.setText(self.annotation_type.delimiter)
        self.morphDelimiterLabel = QtWidgets.QLabel('None')

        self.ignoreLabel = QtWidgets.QLabel('None')

        self.digraphLabel = QtWidgets.QLabel('None')

        self.numberLabel = QtWidgets.QLabel('None')

        parselayout = QtWidgets.QFormLayout()

        self.editButton = QtWidgets.QPushButton('Edit parsing settings')
        self.editButton.clicked.connect(self.editParsingProperties)

        parselayout.addRow('Transcription delimiter', self.delimiterLabel)
        parselayout.addRow('Morpheme delimiter', self.morphDelimiterLabel)
        parselayout.addRow('Number parsing', self.numberLabel)
        parselayout.addRow('Ignored characters', self.ignoreLabel)
        parselayout.addRow('Multicharacter segments',self.digraphLabel)
        parselayout.addRow(self.editButton)

        main.addLayout(proplayout)
        main.addLayout(parselayout)


        if self.annotation_type.token:
            self.associationWidget.click(1)
        if self.annotation_type.anchor:
            self.typeWidget.setCurrentIndex(0)
        elif self.annotation_type.base or self.annotation_type.delimiter is not None:
            self.typeWidget.setCurrentIndex(1)
        elif self.annotation_type.attribute.att_type == 'numeric':
            self.typeWidget.setCurrentIndex(2)
        #self.attributeWidget = AttributeWidget(attribute = self.annotation_type.attribute)

        self.nameWidget.setText(self.annotation_type.attribute.display_name)
        #if show_attribute:
        #    main.addWidget(self.attributeWidget)

        self.setLayout(main)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)


        self.typeChanged()

    def typeChanged(self):
        if self.typeWidget.currentIndex() in [0, 1]:
            self.editButton.setEnabled(True)
            self.updateParsingLabels()
        else:
            self.editButton.setEnabled(False)
        self.suggestName()

    def suggestName(self):
        if self.typeWidget.currentText() == 'Orthography':
            self.nameWidget.setText('Spelling')
        elif self.typeWidget.currentText() == 'Transcription':
            self.nameWidget.setText('Transcription')
        elif self.typeWidget.currentText() == 'Other (numeric)':
            self.nameWidget.setText(self.annotation_type.attribute.display_name)
        elif self.typeWidget.currentText() == 'Other (character)':
            self.nameWidget.setText(self.annotation_type.attribute.display_name)
        elif self.typeWidget.currentText() == 'Notes (ignored)':
            self.nameWidget.setText('Ignored')


    def updateParsingLabels(self):
        if self.typeWidget.currentIndex() == 0:
            self.digraphLabel.setText('N/A')
            self.numberLabel.setText('N/A')
            self.delimiterLabel.setText('N/A')
            self.morphDelimiterLabel.setText('N/A')
        elif self.typeWidget.currentIndex() == 1:
            if self.annotation_type.digraphs:
                self.digraphLabel.setText(truncate_string(' '.join(self.annotation_type.digraphs)))
            else:
                self.digraphLabel.setText('None')
            if self.annotation_type.morph_delimiters:
                self.morphDelimiterLabel.setText(
                        truncate_string(' '.join(
                            self.annotation_type.morph_delimiters
                            )
                        ))
            else:
                self.morphDelimiterLabel.setText('None')
            if self.annotation_type.trans_delimiter:
                self.delimiterLabel.setText(truncate_string(' '.join(self.annotation_type.trans_delimiter)))
            else:
                self.delimiterLabel.setText('None')
            if self.annotation_type.number_behavior:
                self.numberLabel.setText(str(self.annotation_type.number_behavior))
            else:
                self.numberLabel.setText('None')
        if self.annotation_type.ignored_characters:
            self.ignoreLabel.setText(truncate_string(' '.join(self.annotation_type.ignored_characters)))
        else:
            self.ignoreLabel.setText('None')

    def editParsingProperties(self):
        if self.typeWidget.currentText() == 'Orthography':
            atype = 'spelling'
        elif self.typeWidget.currentText() == 'Transcription':
            atype = 'tier'
        else:
            return
        dialog = ParsingDialog(self, self.annotation_type, atype)
        if dialog.exec_():
            self.annotation_type.ignored_characters = dialog.ignored()
            self.annotation_type.digraphs = dialog.digraphs()
            self.annotation_type.morph_delimiters = dialog.morphDelimiters()
            d = dialog.transDelimiter()
            if d == '':
                self.annotation_type.trans_delimiter = None
            else:
                self.annotation_type.trans_delimiter = d
            self.annotation_type.number_behavior = dialog.numberBehavior()
            self.updateParsingLabels()

    def value(self):
        a = self.annotation_type
        a.token = self.associationWidget.value() == 'token'
        display_name = self.nameWidget.text()
        a.anchor = False
        a.base = False
        name = Attribute.sanitize_name(display_name)
        if self.typeWidget.currentText() == 'Orthography':
            a.anchor = True
            a.base = False
            name = 'spelling'
            atype = 'spelling'
        elif self.typeWidget.currentText() == 'Transcription':
            a.anchor = False
            a.base = True
            atype = 'tier'
        elif self.typeWidget.currentText() == 'Other (numeric)':
            atype = 'numeric'
        elif self.typeWidget.currentText() == 'Other (character)':
            atype = 'factor'
        elif self.typeWidget.currentText() == 'Notes (ignored)':
            a.ignored = True
        if not a.ignored:
            a.attribute = Attribute(name, atype, display_name)
        return a

class AttributeWidget(QtWidgets.QGroupBox):
    def __init__(self, attribute = None, exclude_tier = False,
                disable_name = False, parent = None):
        super(AttributeWidget, self).__init__('Column details', parent)
        return
        main = QtWidgets.QFormLayout()

        self.nameWidget = QtWidgets.QLineEdit()

        main.addRow('Name of column',self.nameWidget)

        if attribute is not None:
            self.attribute = attribute
            self.nameWidget.setText(attribute.display_name)
        else:
            self.attribute = None

        if disable_name:
            self.nameWidget.setEnabled(False)

        self.typeWidget = NonScrollingComboBox()
        for at in Attribute.ATT_TYPES:
            if exclude_tier and at == 'tier':
                continue
            self.typeWidget.addItem(at.title())

        main.addRow('Type of column',self.typeWidget)

        self.useAs = NonScrollingComboBox()
        self.useAs.addItem('Custom column')
        self.useAs.addItem('Spelling')
        self.useAs.addItem('Transcription')
        self.useAs.addItem('Frequency')
        self.useAs.currentIndexChanged.connect(self.updateUseAs)

        for i in range(self.useAs.count()):
            if attribute is not None and self.useAs.itemText(i).lower() == attribute.name:
                self.useAs.setCurrentIndex(i)
                if attribute.name == 'transcription' and attribute.att_type != 'tier':
                    attribute.att_type = 'tier'

        for i in range(self.typeWidget.count()):
            if attribute is not None and self.typeWidget.itemText(i) == attribute.att_type.title():
                self.typeWidget.setCurrentIndex(i)

        main.addRow('Use column as', self.useAs)

        self.setLayout(main)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    def type(self):
        return self.typeWidget.currentText().lower()

    def updateUseAs(self):
        t = self.useAs.currentText().lower()
        if t == 'custom column':
            self.typeWidget.setEnabled(True)
        else:
            for i in range(self.typeWidget.count()):
                if t == 'spelling' and self.typeWidget.itemText(i) == 'Spelling':
                    self.typeWidget.setCurrentIndex(i)
                elif t == 'transcription' and self.typeWidget.itemText(i) == 'Tier':
                    self.typeWidget.setCurrentIndex(i)
                elif t == 'frequency' and self.typeWidget.itemText(i) == 'Numeric':
                    self.typeWidget.setCurrentIndex(i)
            self.typeWidget.setEnabled(False)

    def use(self):
        return self.useAs.currentText().lower()

    def value(self):
        display = self.nameWidget.text()
        cat = self.type()
        use = self.use()
        if use.startswith('custom'):
            name = Attribute.sanitize_name(display)
        else:
            name = use
        att = Attribute(name, cat, display)
        return att

class ParsingDialog(QtWidgets.QDialog):
    def __init__(self, parent, annotation_type, att_type):
        super(ParsingDialog, self).__init__(parent)
        self.characters = annotation_type.characters
        self.setWindowTitle('Parsing {}'.format(annotation_type.name))

        layout = QtWidgets.QFormLayout()
        self.example = QtWidgets.QLabel(' '.join(annotation_type[:5]))
        self.example.setWordWrap(True)
        layout.addRow('Example:', self.example)

        self.punctuationWidget = PunctuationWidget(annotation_type.punctuation)
        self.punctuationWidget.setPunctuation(annotation_type.ignored_characters)
        self.delimiterWidget = QtWidgets.QLineEdit()
        self.morphDelimiterWidget = PunctuationWidget(annotation_type.punctuation & set('-='),
                                                        'Morpheme delimiter')
        self.morphDelimiterWidget.setPunctuation(annotation_type.morph_delimiters)
        self.digraphWidget = DigraphWidget()
        self.numberBehaviorSelect = QtWidgets.QComboBox()
        self.numberBehaviorSelect.addItem('Same as other characters')
        self.numberBehaviorSelect.addItem('Tone')
        self.numberBehaviorSelect.addItem('Stress')
        self.numberBehaviorSelect.currentIndexChanged.connect(self.updatePunctuation)

        self.digraphWidget.characters = annotation_type.characters
        self.digraphWidget.setDigraphs(annotation_type.digraphs)

        self.punctuationWidget.selectionChanged.connect(self.punctuationChanged)
        delimiter = annotation_type.delimiter
        if delimiter is not None:
            self.delimiterWidget.setText(delimiter)
            self.punctuationWidget.updateButtons([delimiter])
        self.delimiterWidget.textChanged.connect(self.updatePunctuation)
        if att_type == 'tier':
            layout.addRow('Transcription delimiter',self.delimiterWidget)
        layout.addRow(self.morphDelimiterWidget)
        self.morphDelimiterWidget.selectionChanged.connect(self.updatePunctuation)

        if att_type == 'tier':
            if len(self.characters & set(['0','1','2'])):
                layout.addRow('Number parsing', self.numberBehaviorSelect)
            else:
                layout.addRow('Number parsing', QtWidgets.QLabel('No numbers'))
        layout.addRow(self.punctuationWidget)
        if att_type == 'tier':
            layout.addRow(self.digraphWidget)

        self.acceptButton = QtWidgets.QPushButton('Ok')
        self.cancelButton = QtWidgets.QPushButton('Cancel')
        acLayout = QtWidgets.QHBoxLayout()
        acLayout.addWidget(self.acceptButton)
        acLayout.addWidget(self.cancelButton)
        self.acceptButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        acFrame = QtWidgets.QFrame()
        acFrame.setLayout(acLayout)

        layout.addRow(acFrame)

        self.setLayout(layout)

    def ignored(self):
        return self.punctuationWidget.value()

    def morphDelimiters(self):
        return self.morphDelimiterWidget.value()

    def transDelimiter(self):
        return self.delimiterWidget.text()

    def numberBehavior(self):
        if self.numberBehaviorSelect.currentIndex() == 0:
            return None
        return self.numberBehaviorSelect.currentText().lower()

    def digraphs(self):
        return self.digraphWidget.value()

    def updatePunctuation(self):
        delimiter = self.delimiterWidget.text()
        if delimiter == '':
            delimiter = []
        else:
            delimiter = [delimiter]
        self.morphDelimiterWidget.updateButtons(delimiter, emit = False)

        delimiter += self.morphDelimiterWidget.value()
        self.punctuationWidget.updateButtons(delimiter)

    def punctuationChanged(self):
        self.digraphWidget.characters = self.characters - \
                                        self.punctuationWidget.value() - \
                                        self.morphDelimiterWidget.value()
        if self.numberBehaviorSelect.currentIndex() != 0:
            self.digraphWidget.characters -= NUMBER_CHARACTERS
        delimiter = self.delimiterWidget.text()
        if delimiter != '':
            self.digraphWidget.characters -= set([delimiter])

class CorpusSourceWidget(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(CorpusSourceWidget, self).__init__(parent)
        return
        self.filefilter = 'Text files (*.txt *.csv *.TextGrid *.words *.wrds)'
        self.relevent_files = None
        self.suggested_type = None

        layout = QtWidgets.QHBoxLayout()
        pathLayout = QtWidgets.QVBoxLayout()
        buttonLayout = QtWidgets.QVBoxLayout()

        self.pathEdit = QtWidgets.QLineEdit()
        pathLayout.addWidget(self.pathEdit)

        self.pathButton = QtWidgets.QPushButton('Choose file...')
        self.pathButton.setAutoDefault(False)
        self.pathButton.setDefault(False)
        self.pathButton.clicked.connect(self.pickFile)
        buttonLayout.addWidget(self.pathButton)

        self.directoryButton = QtWidgets.QPushButton('Choose directory...')
        self.directoryButton.setAutoDefault(False)
        self.directoryButton.setDefault(False)
        self.directoryButton.clicked.connect(self.pickDirectory)
        buttonLayout.addWidget(self.directoryButton)

        self.mouseover = QtWidgets.QLabel('Mouseover for included files')
        self.mouseover.setFrameShape(QtWidgets.QFrame.Box)
        self.mouseover.setToolTip('No included files')
        pathLayout.addWidget(self.mouseover)

        layout.addLayout(pathLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)

        self.textChanged = self.pathEdit.textChanged

    def pickDirectory(self):
        filename = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose a directory")
        if filename:

            self.suggested_type, self.relevent_files = inspect_directory(filename)
            self.updateType(self.suggested_type)
            self.pathEdit.setText(filename)
        else:
            self.relevent_files = None
            self.suggested_type = None

    def updateType(self, type):
        if self.relevent_files is None or type is None:
            self.mouseover.setToolTip('No included files')
        else:
            self.mouseover.setToolTip('\n'.join(self.relevent_files[type]))

    def pickFile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file',
                                                filter=self.filefilter)
        if filename:
            self.pathEdit.setText(filename[0])

    def value(self):
        return self.pathEdit.text()


class PunctuationWidget(QtWidgets.QGroupBox):
    selectionChanged = QtCore.pyqtSignal()
    def __init__(self, punctuation, title = 'Punctuation to ignore', parent = None):

        super(PunctuationWidget, self).__init__(title, parent)

        self.btnGroup = QtWidgets.QButtonGroup()
        self.btnGroup.setExclusive(False)
        layout = QtWidgets.QVBoxLayout()
        self.warning = QLabel('None detected (other than any transcription delimiters)')
        if len(punctuation) > 0:
            self.warning.hide()
        layout.addWidget(self.warning)
        box = QtWidgets.QGridLayout()

        row = 0
        col = 0
        for s in punctuation:
            btn = QtWidgets.QPushButton(s)
            btn.clicked.connect(self.selectionChanged.emit)
            btn.setAutoDefault(False)
            btn.setCheckable(True)
            btn.setAutoExclusive(False)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
            btn.setMaximumWidth(btn.fontMetrics().boundingRect(s).width() + 14)
            btn.setFocusPolicy(Qt.NoFocus)

            box.addWidget(btn,row,col)
            self.btnGroup.addButton(btn)
            col += 1
            if col > 11:
                col = 0
                row += 1
        boxFrame = QtWidgets.QFrame()
        boxFrame.setLayout(box)
        layout.addWidget(boxFrame)

        buttonlayout = QtWidgets.QHBoxLayout()
        self.checkAll = QtWidgets.QPushButton('Check all')
        self.checkAll.setAutoDefault(False)
        self.checkAll.clicked.connect(self.check)
        self.uncheckAll = QtWidgets.QPushButton('Uncheck all')
        self.uncheckAll.setAutoDefault(False)
        self.uncheckAll.clicked.connect(self.uncheck)

        if len(punctuation) < 2:
            self.checkAll.hide()
            self.uncheckAll.hide()
        buttonlayout.addWidget(self.checkAll, alignment = Qt.AlignLeft)
        buttonlayout.addWidget(self.uncheckAll, alignment = Qt.AlignLeft)
        buttonframe = QtWidgets.QFrame()
        buttonframe.setLayout(buttonlayout)

        layout.addWidget(buttonframe)
        self.setLayout(layout)

    def updateButtons(self, to_ignore, emit = True):
        count_visible = 0
        for b in self.btnGroup.buttons():
            if b.text() in to_ignore:
                b.setChecked(False)
                b.hide()
            else:
                b.show()
            if not b.isHidden():
                count_visible += 1
        if count_visible == 0:
            self.warning.show()
        else:
            self.warning.hide()
        if count_visible < 2:
            self.checkAll.hide()
            self.uncheckAll.hide()
        else:
            self.checkAll.show()
            self.uncheckAll.show()
        if emit:
            self.selectionChanged.emit()

    def setPunctuation(self, punc):
        for b in self.btnGroup.buttons():
            if b.text() in punc:
                b.setChecked(True)
        self.selectionChanged.emit()

    def check(self):
        for b in self.btnGroup.buttons():
            b.setChecked(True)
        self.selectionChanged.emit()

    def uncheck(self):
        for b in self.btnGroup.buttons():
            b.setChecked(False)
        self.selectionChanged.emit()

    def value(self):
        value = []
        for b in self.btnGroup.buttons():
            if b.isChecked():
                t = b.text()
                value.append(t)
        return set(value)

class DigraphDialog(QtWidgets.QDialog):
    def __init__(self, characters, parent = None):
        super(DigraphDialog, self).__init__(parent)
        layout = QtWidgets.QFormLayout()
        self.digraphLine = QtWidgets.QLineEdit()
        layout.addRow(QtWidgets.QLabel('Multicharacter segment'),self.digraphLine)
        symbolframe = QtWidgets.QGroupBox('Characters')
        box = QtWidgets.QGridLayout()

        row = 0
        col = 0
        self.buttons = list()
        for s in characters:
            btn = QtWidgets.QPushButton(s)
            btn.clicked.connect(self.addCharacter)
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
            btn.setMaximumWidth(btn.fontMetrics().boundingRect(s).width() + 14)
            self.buttons.append(btn)
            box.addWidget(btn,row,col)
            col += 1
            if col > 11:
                col = 0
                row += 1
        symbolframe.setLayout(box)
        layout.addRow(symbolframe)
        self.oneButton = QPushButton('Add')
        self.anotherButton = QPushButton('Add and create another')
        self.cancelButton = QPushButton('Cancel')
        acLayout = QtWidgets.QHBoxLayout()
        acLayout.addWidget(self.oneButton, alignment = QtCore.Qt.AlignLeft)
        acLayout.addWidget(self.anotherButton, alignment = Qt.AlignLeft)
        acLayout.addWidget(self.cancelButton, alignment = Qt.AlignLeft)
        self.oneButton.clicked.connect(self.one)
        self.anotherButton.clicked.connect(self.another)
        self.cancelButton.clicked.connect(self.reject)

        acFrame = QtWidgets.QFrame()
        acFrame.setLayout(acLayout)

        layout.addRow(acFrame)
        self.setLayout(layout)
        self.setFixedSize(self.sizeHint())
        self.setWindowTitle('Construct segment')

    def addCharacter(self):
        self.digraphLine.setText(self.digraphLine.text()+self.sender().text())

    def one(self):
        self.addOneMore = False
        self.accept()

    def another(self):
        self.addOneMore = True
        self.accept()

    def value(self):
        return self.digraphLine.text()

    def reject(self):
        self.addOneMore = False
        super(DigraphDialog, self).reject()

class DigraphWidget(QtWidgets.QGroupBox):
    def __init__(self,parent = None):
        self._parent = parent
        super(DigraphWidget, self).__init__('Multicharacter segments', parent)
        layout = QtWidgets.QVBoxLayout()

        self.editField = QtWidgets.QLineEdit()
        layout.addWidget(self.editField)
        self.button = QtWidgets.QPushButton('Construct a segment')
        self.button.setAutoDefault(False)
        self.button.clicked.connect(self.construct)
        layout.addWidget(self.button)
        self.setLayout(layout)
        self.characters = list()

    def setDigraphs(self, digraphs):
        self.editField.setText(','.join(digraphs))

    def construct(self):
        if len(self.characters) == 0:
            return
        possible = sorted(self.characters, key = lambda x: x.lower())
        dialog = DigraphDialog(possible,self)
        addOneMore = True
        while addOneMore:
            if dialog.exec_():
                v = dialog.value()
                if v != '' and v not in self.value():
                    val = self.value() + [v]
                    self.editField.setText(','.join(val))
            dialog.digraphLine.setText('')
            addOneMore = dialog.addOneMore

    def value(self):
        text = self.editField.text()
        values = [x.strip() for x in text.split(',') if x.strip() != '']
        if len(values) == 0:
            return []
        return values
