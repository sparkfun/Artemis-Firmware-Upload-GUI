# -----------------------------------------------------------------------------
# artemis_uploader.py
#
# ------------------------------------------------------------------------
#
# Written/Update by  SparkFun Electronics, Fall 2022
#
# This python package implements a GUI Qt application that supports
# firmware and bootloader uploading to the SparkFun Artemis module
#
# This file is the main application implementation - creating the pyQt
# interface and event handlers.
#
# More information on qwiic is at https://www.sparkfun.com/artemis
#
# Do you like this library? Help support SparkFun. Buy a board!
#
# ==================================================================================
# Copyright (c) 2022 SparkFun Electronics
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==================================================================================
#
# pylint: disable=missing-docstring, wrong-import-position, no-name-in-module, syntax-error, invalid-name, global-statement
# pylint: disable=unused-variable, too-few-public-methods, too-many-instance-attributes, too-many-locals, too-many-statements
# -----------------------------------------------------------------------------

from .au_worker import AUxWorker
from .au_act_artfrmw import AUxArtemisUploadFirmware
from .au_act_artasb import AUxArtemisBurnBootloader
from .au_action import AxJob

import darkdetect
import sys
import os
import os.path
import platform

from typing import Iterator, Tuple
from PyQt5.QtCore import QSettings, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit, \
    QAction, QActionGroup, QMainWindow, QMessageBox
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon, QFont, QPixmap
from PyQt5.QtSerialPort import QSerialPortInfo


_APP_NAME = "Artemis Firmware Uploader"

# sub folder for our resource files
_RESOURCE_DIRECTORY = "resource"
# ---------------------------------------------------------------------------------------
# resource_path()
#
# Get the runtime path of app resources. This changes depending on how the app is
# run -> locally, or via pyInstaller
#
# https://stackoverflow.com/a/50914550

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, _RESOURCE_DIRECTORY, relative_path)

def get_version(rel_path: str) -> str:
    try: 
        with open(resource_path(rel_path), encoding='utf-8') as fp:
            for line in fp.read().splitlines():
                if line.startswith("__version__"):
                    delim = '"' if '"' in line else "'"
                    return line.split(delim)[1]
            raise RuntimeError("Unable to find version string.")
    except:
        raise RuntimeError("Unable to find _version.py.")

_APP_VERSION = get_version("_version.py")

# determine the current GUI style

# import action things - the .syntax is used since these are part of the package

# ----------------------------------------------------------------
# hack to know when a combobox menu is being shown. Helpful if contents
# of list are dynamic -- like serial ports.

class AUxComboBox(QComboBox):

    popupAboutToBeShown = pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super().showPopup()


# ----------------------------------------------------------------
# ux_is_darkmode()
#
# Helpful function used during setup to determine if the Ux is in
# dark mode
_is_darkmode = None


def ux_is_darkmode() -> bool:
    global _is_darkmode

    if _is_darkmode is not None:
        return _is_darkmode

    osName = platform.system()

    if osName == "Darwin":
        _is_darkmode = darkdetect.isDark()

    elif osName == "Windows":
        # it appears that the Qt interface on Windows doesn't apply DarkMode
        # So, just keep it light
        _is_darkmode = False
    elif osName == "Linux":
        # Need to check this on Linux at some pont
        _is_darkmod = False

    else:
        _is_darkmode = False

    return _is_darkmode

# --------------------------------------------------------------------------------------


BOOTLOADER_VERSION = 5  # << Change this to match the version of artemis_svl.bin

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_FILE_LOCATION = 'file_location'
SETTING_BAUD_RATE = 'baud'
SETTING_ARTEMIS = 'artemis'


def gen_serial_ports() -> Iterator[Tuple[str, str, str]]:
    """Return all available serial ports."""
    ports = QSerialPortInfo.availablePorts()
    return ((p.description(), p.portName(), p.systemLocation()) for p in ports)

# noinspection PyArgumentList

# ---------------------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """Main Window"""

    sig_message = pyqtSignal(str)
    sig_finished = pyqtSignal(int, str, int)

    def __init__(self, parent: QMainWindow = None) -> None:
        super().__init__(parent)

        self.installed_bootloader = -1  # Use this to record the bootloader version

        #
        self.appFile = 'artemis_svl.bin'    # --bin Bootloader binary file
        # --load-address-wired  dest=loadaddress_blob   default=0x60000
        self.load_address_blob = 0xC000
        # --load-address-blob   dest=loadaddress_image
        #           default=AM_SECBOOT_DEFAULT_NONSECURE_MAIN=0xC000
        self.load_address_image = 0x20000
        # --magic-num   Magic Num (AM_IMAGE_MAGIC_NONSECURE)
        self.magic_num = 0xCB

        # File location line edit
        msg_label = QLabel(self.tr('Firmware File:'))
        self.fileLocation_lineedit = QLineEdit()
        msg_label.setBuddy(self.fileLocation_lineedit)
        self.fileLocation_lineedit.setEnabled(False)
        self.fileLocation_lineedit.returnPressed.connect(
            self.on_browse_btn_pressed)

        # Browse for new file button
        browse_btn = QPushButton(self.tr('Browse'))
        browse_btn.setEnabled(True)
        browse_btn.pressed.connect(self.on_browse_btn_pressed)

        # Port Combobox
        port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = AUxComboBox()
        port_label.setBuddy(self.port_combobox)
        self.update_com_ports()
        self.port_combobox.popupAboutToBeShown.connect(self.on_port_combobox)

        # Baudrate Combobox
        baud_label = QLabel(self.tr('Baud Rate:'))
        self.baud_combobox = QComboBox()
        baud_label.setBuddy(self.baud_combobox)
        self.update_baud_rates()

        # Upload Button
        myFont = QFont()
        myFont.setBold(True)
        self.upload_btn = QPushButton(self.tr('  Upload Firmware  '))
        self.upload_btn.setFont(myFont)
        self.upload_btn.pressed.connect(self.on_upload_btn_pressed)

        # Upload Button
        self.updateBootloader_btn = QPushButton(self.tr(' Update Bootloader '))
        self.updateBootloader_btn.pressed.connect(
            self.on_update_bootloader_btn_pressed)

        # Messages Bar
        messages_label = QLabel(self.tr('Status / Warnings:'))

        # Messages/Console Window
        self.messages = QPlainTextEdit()
        color = "C0C0C0" if ux_is_darkmode() else "424242"
        self.messages.setStyleSheet("QPlainTextEdit { color: #" + color + ";}")

        # Attempting to reduce window size
        #self.messages.setMinimumSize(1, 2)
        #self.messages.resize(1, 2)

        # Menu Bar
        menubar = self.menuBar()
        boardMenu = menubar.addMenu('Board Type')

        boardGroup = QActionGroup(self)

        self.artemis = QAction('Artemis', self, checkable=True)
        self.artemis.setStatusTip(
            'Artemis-based boards including the OLA and AGT')
        self.artemis.setChecked(True)  # Default to artemis. _load_settings will override this
        a = boardGroup.addAction(self.artemis)
        boardMenu.addAction(a)

        self.apollo3 = QAction('Apollo3', self, checkable=True)
        self.apollo3.setStatusTip(
            'Apollo3 Blue development boards including the SparkFun Edge')
        self.apollo3.setChecked(False)  # Default to artemis. _load_settings will override this
        a = boardGroup.addAction(self.apollo3)
        boardMenu.addAction(a)

        # Add an artemis logo to the user interface
        logo = QLabel(self)
        icon = "artemis-icon.png" if ux_is_darkmode() else "artemis-icon-blk.png"
        pixmap = QPixmap(resource_path(icon))
        logo.setPixmap(pixmap)

        # Arrange Layout
        layout = QGridLayout()

        layout.addWidget(msg_label, 1, 0)
        layout.addWidget(self.fileLocation_lineedit, 1, 1)
        layout.addWidget(browse_btn, 1, 2)

        layout.addWidget(port_label, 2, 0)
        layout.addWidget(self.port_combobox, 2, 1)

        layout.addWidget(logo, 2, 2, 2, 3, alignment=Qt.AlignCenter)

        layout.addWidget(baud_label, 3, 0)
        layout.addWidget(self.baud_combobox, 3, 1)

        layout.addWidget(messages_label, 4, 0)
        layout.addWidget(self.messages, 5, 0, 5, 3)

        layout.addWidget(self.upload_btn, 15, 2)
        layout.addWidget(self.updateBootloader_btn, 15, 0)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.settings = QSettings()
        self._load_settings()

        # Make the text edit window read-only
        self.messages.setReadOnly(True)
        self.messages.clear()  # Clear the message window

        self.setWindowTitle(_APP_NAME + " - " + _APP_VERSION)

        # Initial Status Bar
        self.statusBar().showMessage(_APP_NAME + " - " + _APP_VERSION, 10000)

        # setup our background worker thread ...

        # connect the signals from the background processor to callback
        # methods/slots. This makes it thread safe
        self.sig_message.connect(self.log_message)
        self.sig_finished.connect(self.on_finished)

        # Create our background worker object, which also will do work in it's
        # own thread.
        self._worker = AUxWorker(self.on_worker_callback)

        # add the actions/commands for this app to the background processing thread.
        # These actions are passed jobs to execute.
        self._worker.add_action(
            AUxArtemisUploadFirmware(), AUxArtemisBurnBootloader())

    # --------------------------------------------------------------
    # callback function for the background worker.
    #
    # It is assumed that this method is called by the background thread
    # so signals and used to relay the call to the GUI running on the
    # main thread

    def on_worker_callback(self, *args): #msg_type, arg):

        # need a min of 2 args (id, arg)
        if len(args) < 2:
            self.log_message("Invalid parameters from the uploader.")
            return

        msg_type = args[0]
        if msg_type == AUxWorker.TYPE_MESSAGE:
            self.sig_message.emit(args[1])
        elif msg_type == AUxWorker.TYPE_FINISHED:
            # finished takes 3 args - status, job type, and job id
            if len(args) < 4:
                self.log_message("Invalid parameters from the uploader.");
                return;

            self.sig_finished.emit(args[1], args[2], args[3])

    # --------------------------------------------------------------
    @pyqtSlot(str)
    def log_message(self, msg: str) -> None:
        """Add msg to the messages window, ensuring that it is visible"""

        # The passed in text is inserted *raw* at the end of the console
        # text area. The insert method doesn't add any newlines. Most of the
        # text being recieved originates in a print() call, which adds newlines.

        self.messages.moveCursor(QTextCursor.End)

        # Backspace ("\b")??
        tmp = msg
        while len(tmp) > 2 and tmp.startswith('\b'):

            # remove the "\b" from the input string, and delete the
            # previous character from the cursor in the text console
            tmp = tmp[1:]
            self.messages.textCursor().deletePreviousChar()
            self.messages.moveCursor(QTextCursor.End)

        # insert the new text at the end of the console
        self.messages.insertPlainText(tmp)

        # make sure cursor is at end of text and it's visible
        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.repaint()  # Update/refresh the message window

    # --------------------------------------------------------------
    # on_finished()
    #
    #  Slot for sending the "on finished" signal from the background thread
    #
    #  Called when the backgroudn job is finished and includes a status value
    @pyqtSlot(int, str, int)
    def on_finished(self, status, action_type, job_id) -> None:

        # re-enable the UX
        self.disable_interface(False)

        # update the status message
        msg = "successfully" if status == 0 else "with an error"
        self.statusBar().showMessage("The upload process finished " + msg, 2000)

    # --------------------------------------------------------------
    # on_port_combobox()
    #
    # Called when the combobox pop-up menu is about to be shown
    #
    # Use this event to dynamically update the displayed ports
    #
    @pyqtSlot()
    def on_port_combobox(self):
        self.statusBar().showMessage("Updating ports...", 500)
        self.update_com_ports()

    # ---------------------------------------------------------------

    def _load_settings(self) -> None:
        """Load settings on startup."""

        port_name = self.settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        lastFile = self.settings.value(SETTING_FILE_LOCATION)
        if lastFile is not None:
            self.fileLocation_lineedit.setText(lastFile)

        baud = self.settings.value(SETTING_BAUD_RATE)
        if baud is not None:
            index = self.baud_combobox.findData(baud)
            if index > -1:
                self.baud_combobox.setCurrentIndex(index)

        checked = self.settings.value(SETTING_ARTEMIS)
        if checked is not None:
            if checked == 'True':
                self.artemis.setChecked(True)
                self.apollo3.setChecked(False)
            else:
                self.artemis.setChecked(False)
                self.apollo3.setChecked(True)

    # --------------------------------------------------------------
    def _save_settings(self) -> None:
        """Save settings on shutdown."""

        self.settings.setValue(SETTING_PORT_NAME, self.port)
        self.settings.setValue(SETTING_FILE_LOCATION, self.theFileName)
        self.settings.setValue(SETTING_BAUD_RATE, self.baudRate)
        if self.artemis.isChecked():  # Convert isChecked to str
            checkedStr = 'True'
        else:
            checkedStr = 'False'
        self.settings.setValue(SETTING_ARTEMIS, checkedStr)

    # --------------------------------------------------------------
    def _clean_settings(self) -> None:
        """Clean (remove) all existing settings."""
        settings = QSettings()
        settings.clear()

    # --------------------------------------------------------------
    def show_error_message(self, msg: str) -> None:
        """Show a Message Box with the error message."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    # --------------------------------------------------------------
    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""
        previousPort = self.port  # Record the previous port before we clear the combobox

        self.port_combobox.clear()

        index = 0
        indexOfCH340 = -1
        indexOfPrevious = -1
        for desc, name, nsys in gen_serial_ports():

            longname = desc + " (" + name + ")"
            self.port_combobox.addItem(longname, nsys)
            if "CH340" in longname:
                # Select the first available CH340
                # This is likely to only work on Windows. Linux port names are different.
                if indexOfCH340 == -1:
                    indexOfCH340 = index
                    # it could be too early to call
                    #self.log_message("CH340 found at index " + str(indexOfCH340))
                    # as the GUI might not exist yet
            if nsys == previousPort:  # Previous port still exists so record it
                indexOfPrevious = index
            index = index + 1

        if indexOfPrevious > -1:  # Restore the previous port if it still exists
            self.port_combobox.setCurrentIndex(indexOfPrevious)
        if indexOfCH340 > -1:  # If we found a CH340, let that take priority
            self.port_combobox.setCurrentIndex(indexOfCH340)

    # --------------------------------------------------------------
    # Is a port still valid?

    def verify_port(self, port) -> bool:

        # Valid inputs - Check the port
        for desc, name, nsys in gen_serial_ports():
            if nsys == port:
                return True

        return False
    # --------------------------------------------------------------

    def update_baud_rates(self) -> None:
        """Update baud rate list in GUI."""
        # Lowest speed first so code defaults to that
        # if settings.value(SETTING_BAUD_RATE) is None
        self.baud_combobox.clear()
        self.baud_combobox.addItem("115200", 115200)
        self.baud_combobox.addItem("460800", 460800)
        self.baud_combobox.addItem("921600", 921600)

    # --------------------------------------------------------------
    @property
    def port(self) -> str:
        """Return the current serial port."""
        return self.port_combobox.currentData()

    # --------------------------------------------------------------
    @property
    def baudRate(self) -> str:
        """Return the current baud rate."""
        return self.baud_combobox.currentData()
    
    # --------------------------------------------------------------
    @property
    def theFileName(self) -> str:
        """Return the current file location."""
        return self.fileLocation_lineedit.text()

    # --------------------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        self._save_settings()

        # shutdown the background worker/stop it so the app exits correctly
        self._worker.shutdown()

        event.accept()

    # --------------------------------------------------------------
    # disable_interface()
    #
    # Enable/Disable portions of the ux - often used when a job is running
    #
    def disable_interface(self, bDisable=False):

        self.upload_btn.setDisabled(bDisable)
        self.updateBootloader_btn.setDisabled(bDisable)

    # --------------------------------------------------------------
    # on_upload_btn_pressed()
    #

    def on_upload_btn_pressed(self) -> None:

        # Valid inputs - Check the port
        if not self.verify_port(self.port):
            self.log_message("Port No Longer Available")
            return

        # Does the upload file exist?
        fmwFile = self.fileLocation_lineedit.text()
        if not os.path.exists(fmwFile):
            self.log_message("The firmware file was not found: " + fmwFile)
            return

        # Create a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        #
        # Note - the job is defined with the ID of the target action
        theJob = AxJob(AUxArtemisUploadFirmware.ACTION_ID,
                       {"port": self.port, "baud": self.baudRate, "file": fmwFile})

        # Send the job to the worker to process
        job_id = self._worker.add_job(theJob)

        self.disable_interface(True)

    # --------------------------------------------------------------
    def on_update_bootloader_btn_pressed(self) -> None:

        # Valid inputs - Check the port
        if not self.verify_port(self.port):
            self.log_message("Port No Longer Available")
            return

        # Does the bootloader file exist?
        blFile = resource_path(self.appFile)
        if not os.path.exists(blFile):
            self.log_message("The bootloader file was not found: " + blFile)
            return

        # Make up a job and add it to the job queue. The worker thread will pick this up and
        # process the job. Can set job values using dictionary syntax, or attribute assignments
        theJob = AxJob(AUxArtemisBurnBootloader.ACTION_ID,
                       {"port": self.port, "baud": self.baudRate, "file": blFile})

        # Send the job to the worker to process
        job_id = self._worker.add_job(theJob)

        self.disable_interface(True)

    # --------------------------------------------------------------
    def on_browse_btn_pressed(self) -> None:
        """Open dialog to select bin file."""

        self.statusBar().showMessage("Select firmware file for upload...", 4000)
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Select Firmware to Upload",
            "",
            "Firmware Files (*.bin);;All Files (*)",
            options=options)
        if fileName:
            self.fileLocation_lineedit.setText(fileName)

# ------------------------------------------------------------------
# startArtemisUploader()
#
# This is the main entry point function to start the application GUI
#
# This is called from the command line script that launches the application
#


def startArtemisUploader():

    app = QApplication([])
    app.setOrganizationName('SparkFun Electronics')
    app.setApplicationName(_APP_NAME + ' - ' + _APP_VERSION)
    app.setWindowIcon(QIcon(resource_path("artemis-logo-rounded.png")))
    app.setApplicationVersion(_APP_VERSION)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


# ------------------------------------------------------------------
# This is probably not needed/working now that this is file is part of a package,
# but leaving here anyway ...
if __name__ == '__main__':
    startArtemisUploader()
