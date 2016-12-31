from PyQt5.QtCore import QThread,pyqtSignal
import time
import parameter as gl

#淡入淡出提示文字
class Trans(QThread):
    trigger = pyqtSignal()

    def __init__(self, parent=None):
        super(Trans, self).__init__(parent)

    def run(self):
        for i in range(gl.opacity, -1, -1):
            gl.opacity = i
            time.sleep(0.01)
            self.trigger.emit()
        time.sleep(2)
        gl.new_trans = False
        for i in range(gl.opacity, 101):
            if gl.new_trans == True:
                break
            gl.opacity = i
            time.sleep(0.01)
            self.trigger.emit()
        gl.new_trans = False

#淡入提示文字
class In(QThread):
    trigger = pyqtSignal()

    def __init__(self, parent=None):
        super(In, self).__init__(parent)

    def run(self):
        for i in range(gl.opacity, -1, -1):
            gl.opacity = i
            time.sleep(0.01)
            self.trigger.emit()
