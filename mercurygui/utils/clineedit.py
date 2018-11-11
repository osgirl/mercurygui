# -*- coding: utf-8 -*-

from qtpy import QtWidgets


class CLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(CLineEdit, self).__init__(parent)

    def updateText(self, text):
        if not self.hasFocus():
            self.setText(text)
        else:
            pass

    def updateValue(self, value):
        if not self.hasFocus():
            self.setText(str(round(value, 1)))
        else:
            pass
