#!/usr/bin/env python3

import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import gui

app = QtWidgets.QApplication(sys.argv)

my_mainWindow = gui.AccountDialog()
# my_mainWindow = gui.Contact()
# my_mainWindow = gui.MainWindow()

my_mainWindow.show()

sys.exit(app.exec_())


