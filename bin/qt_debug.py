import os
import sys
base = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,base)
from polyglotdb.gui.main import MainWindow, QtWidgets

if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow(app)

    app.setActiveWindow(main)
    main.show()
    sys.exit(app.exec_())
