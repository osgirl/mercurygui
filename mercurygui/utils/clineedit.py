# -*- coding: utf-8 -*-

from qtpy import QtWidgets


class CLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(self.__class__, self).__init__(parent)

    def updateText(self, text):
        """Only update if widget is not in focus / beeing edited."""
        if not self.hasFocus():
            self.setText(text)
        else:
            pass

    def updateValue(self, value):
        """Only update if widget is not in focus / beeing edited."""
        if not self.hasFocus():
            self.setText(str(round(value, 1)))
        else:
            pass

    def value(self):
        """Convert text value to float."""
        return float(self.text())
