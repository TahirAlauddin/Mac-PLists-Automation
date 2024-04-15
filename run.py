from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from main import compare_ccdoc
from design import Ui_MainWindow
from threading import Thread


class MainWindow(QMainWindow):
    oldPlist = newPlist = None

    def __init__(self) -> None:
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.show()
        self.ui.selectOldPlistButton.clicked.connect(self.openOldPlistFileDialog)
        self.ui.selectNewPlistButton.clicked.connect(self.openNewPlistFileDialog)
        self.ui.runButton.clicked.connect(self.run)
        self.ui.consumerRadioButton.setChecked(True)

        
    def openOldPlistFileDialog(self):
        """Open a window so the user can select a document file
        It sets `oldPlist` variable to the path of docs."""
        options = QFileDialog.Options()
        self.oldPlist, _ = QFileDialog.getOpenFileName(
            self, "Documents File", "", "CCDOC (*.ccdoc) ;; PList(*.plist)", options=options)
        if self.oldPlist:
            self.ui.oldLineEdit.setText(self.oldPlist)

    def openNewPlistFileDialog(self):
        """Open a window so the user can select a document file
        It sets `newPlist` variable to the path of docs."""
        options = QFileDialog.Options()
        self.newPlist, _ = QFileDialog.getOpenFileName(
            self, "Documents File", "", "CCDOC (*.ccdoc) ;; PList(*.plist)", options=options)
        if self.newPlist:
            self.ui.newLineEdit.setText(self.newPlist)

    def run(self):
        if self.ui.fullDevRadioButton.isChecked():
            selection = '1'
        else:
            selection = '2'
        if self.oldPlist and self.newPlist:
            thread = Thread(target=compare_ccdoc, args=(self.oldPlist, self.newPlist), 
                            kwargs={'selection': selection}
                            )
            thread.start()
            thread.join()
        else:
            print("Please provide old and new ccodoc/plist")



if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    window  = MainWindow()
    sys.exit(app.exec_())

