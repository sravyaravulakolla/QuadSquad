from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QFileDialog, QLabel, QMessageBox, QWidget, QVBoxLayout
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QMovie
import requests
import sys
import threading
import time
import zipfile
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSpacerItem, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIcon, QPixmap


class UploadThread(QtCore.QThread):
    upload_started = pyqtSignal()
    upload_finished = pyqtSignal(bool)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        self.upload_started.emit()
        zip_file_path = os.path.splitext(self.file_path)[0] + ".zip"
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(self.file_path, os.path.basename(self.file_path))
        url = "/upload"  # Replace with your server URL
        files1 = {"file": open(self.file_path, "rb")}
        files2 = {"file": open(zip_file_path,"rb")}
        try:
            response = requests.post(url, files=files2)
            print(response)
            if response.status_code == 200:
                print("File uploaded successfully")
                self.upload_finished.emit(True)
            elif response.status_code == 400:
                print("No file selected")
                self.upload_finished.emit(False)
        except requests.exceptions.RequestException as e:
            print(f"Error uploading file: {e}")
            self.upload_finished.emit(False)


class BackendThread(QtCore.QThread):
    result_check = pyqtSignal()
    result_found = pyqtSignal(str)

    def run(self):
        self.result_check.emit()

        response = requests.get("http://divyareddy.pythonanywhere.com/check_result")
        print(response.status_code)
        result = response.text

        self.result_found.emit(result)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("MALWARE FINDER")
        self.setMinimumSize(QtCore.QSize(600, 400))

        # Set the application icon (Windows and Linux)
        app_icon = QIcon("D:\\vscodeprograms\\pyqtcodes\\icon.png")
        self.setWindowIcon(app_icon)

        # Set the window icon (macOS)
        self.setWindowIcon(QIcon("D:\\vscodeprograms\\pyqtcodes\\icon.png"))
        

        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.gif_label = QLabel(self)
        # self.layout.addWidget(self.gif_label)
        self.gif = QMovie(self)

        

        self.upload_button = QPushButton("UPLOAD", self.central_widget)
        self.upload_button.setStyleSheet(
            "background-color: #F5C3EC;border-radius: 10px;font-family: Helvetica;font-size: 20px;"
        )
        self.upload_button.setGeometry(QtCore.QRect(1000, 350, 120, 50))
        self.upload_button.clicked.connect(self.upload_file)

        self.upload_label = QLabel(self.central_widget)
        self.upload_label.setGeometry(QtCore.QRect(580, 420, 120, 50))
        self.upload_label.setStyleSheet("color:white;font-size:25px")

        self.layout.addStretch(1)

        self.gif_path = "D:\\vscodeprograms\\pyqtcodes\\l-unscreen.gif"


    def resizeEvent(self, event):
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        # Update the position of gif_label when the window is resized
        self.gif_label.setGeometry(QtCore.QRect(600, 280, 120, 100))

    def closeEvent(self, event):
        # Call the function to stop the EC2 instance
        self.stop_ec2()
        event.accept()

    def set_background_image(self, file_path):

        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                print("Failed to load the image:", file_path)
            else:
                scaled_pixmap = pixmap.scaled(self.bg_label.size(), QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)
                self.bg_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print("Error loading the image:", str(e))

    def upload_file(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)  # Set file mode to select an existing file
        file_dialog.setAcceptMode(QFileDialog.AcceptOpen)  # Set accept mode to open files

        # Set the custom filter for .vmem and .mem extensions
        file_dialog.setNameFilter("VMEM , MEM Files , DMP files and RAW files (*.vmem *.mem *.dmp *.raw)")
        if file_dialog.exec_() == QFileDialog.Accepted:
            file_path = file_dialog.selectedFiles()[0]

            self.upload_label.setText("File uploading...")
            self.upload_label.adjustSize()

            self.upload_thread = UploadThread(file_path)
            self.upload_thread.upload_started.connect(self.start_gif)
            self.upload_thread.upload_finished.connect(self.upload_finished)
            self.upload_thread.start()

    @pyqtSlot(bool)
    def upload_finished(self, success):
        self.upload_thread = None

        if success:
            self.gif_label.hide()
            self.upload_label.setText("File uploaded successfully!")
            self.upload_label.adjustSize()

            # Use QTimer to change the message to "Analyzing..." after 5 seconds
            QTimer.singleShot(5000, self.start_analyzing)
        else:
            self.gif_label.hide()
            self.upload_label.setText("Error uploading file")
            self.upload_label.adjustSize()


    def start_analyzing(self):
        self.gif_label.show()
        self.upload_label.setText("Analyzing...")
        self.upload_label.adjustSize()

        self.backend_thread = BackendThread()
        self.backend_thread.result_check.connect(self.handle_result_check)
        self.backend_thread.result_found.connect(self.handle_result)
        self.backend_thread.start()


    def start_gif(self):
        self.gif = QMovie(self.gif_path)
        self.gif_label.setMovie(self.gif)
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif.start()
        self.gif_label.show()

    def handle_result_check(self):
        # Perform any necessary actions before checking the result
        pass

    def handle_result(self, result):
        self.gif_label.hide()
        self.upload_label.setText("")
        self.upload_label.adjustSize()
        if "Benign" in result:
            QMessageBox.information(self, "Result", "Your system is safe.")
        elif "Malware" in result:
            QMessageBox.warning(self, "Result", "Your system contains malware.")
        elif "" in result:
            QMessageBox.critical(self, "Error", "Error in analyzing the file.")

        self.delete_file()

    def delete_file(self):
        url = '/delete_files'
        try:
            response = requests.post(url)
            if response.status_code == 200:
                print("File deleted successfully")
            else:
                print("Failed to delete")
        except requests.exceptions.RequestException as e:
            print("Error", f"Request failed: {str(e)}")

    def stop_ec2(self):
        url = '/stop_ec2_inst'
        try:
            response = requests.post(url)
            if response.status_code == 200:
                print("Successfully stopped")
            else:
                print("Couldn't stop successfully")
        except Exception as e:
            print("Error is", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.set_background_image("D:\\vscodeprograms\\pyqtcodes\\ff.png")
    window.show()
    sys.exit(app.exec_())
