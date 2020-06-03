"""
This is a simple firmware upload GUI designed for the Artemis platform.
Very handy for updating devices in the field without the need for compiling
and uploading through Arduino.

Based on gist by Stefan Lehmann: https://gist.github.com/stlehmann/bea49796ad47b1e7f658ddde9620dff1

Also based on Srikanth Anantharam's SerialTerminal example
https://github.com/sria91/SerialTerminal

MIT license

Pyinstaller:

pyinstaller --onefile --icon=artemis_firmware_uploader_gui.ico --add-binary=artemis_svl.bin --add-binary=Artemis-Logo-Rounded.png artemis_firmware_uploader_gui.py 

TODO:

Push user to upgrade bootloader as needed
Bootloader from CLI:
ambiq_bin2board.exe --bin "artemis_svl.bin" --load-address-blob 0x20000 --magic-num 0xCB --version 0x0 --load-address-wired 0xC000 -i 6 --options 0x1 -b 115200 -port "COM3" -r 2 -v

"""

# Immediately upon reset the Artemis module will search for the timing character
#   to auto-detect the baud rate. If a valid baud rate is found the Artemis will 
#   respond with the bootloader version packet
# If the computer receives a well-formatted version number packet at the desired
#   baud rate it will send a command to begin bootloading. The Artemis shall then 
#   respond with the a command asking for the next frame. 
# The host will then send a frame packet. If the CRC is OK the Artemis will write 
#   that to memory and request the next frame. If the CRC fails the Artemis will
#   discard that data and send a request to re-send the previous frame.
# This cycle repeats until the Artemis receives a done command in place of the
#   requested frame data command.
# The initial baud rate determination must occur within some small timeout. Once 
#   baud rate detection has completed all additional communication will have a 
#   universal timeout value. Once the Artemis has begun requesting data it may no
#   no longer exit the bootloader. If the host detects a timeout at any point it 
#   will stop bootloading. 

# Notes about PySerial timeout:
# The timeout operates on whole functions - that is to say that a call to 
#   ser.read(10) will return after ser.timeout, just as will ser.read(1) (assuming 
#   that the necessary bytes were not found)
# If there are no incoming bytes (on the line or in the buffer) then two calls to 
#   ser.read(n) will time out after 2*ser.timeout
# Incoming UART data is buffered behind the scenes, probably by the OS.

from typing import Iterator, Tuple
from PyQt5.QtCore import QSettings, QProcess, QTimer
from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout, \
    QPushButton, QApplication, QLineEdit, QFileDialog, QPlainTextEdit
from PyQt5.QtGui import QCloseEvent, QTextCursor, QIcon
from PyQt5.QtSerialPort import QSerialPortInfo
import sys
import time
import math
import os
import serial

# Setting constants
SETTING_PORT_NAME = 'port_name'
SETTING_FILE_LOCATION = 'message'
SETTING_BAUD_RATE = '115200' # Default to 115200 for upload

guiVersion = 'v1.0_integrated'


def gen_serial_ports() -> Iterator[Tuple[str, str, str]]:
    """Return all available serial ports."""
    ports = QSerialPortInfo.availablePorts()
    return ((p.description(), p.portName(), p.systemLocation()) for p in ports)

#https://stackoverflow.com/a/50914550
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# noinspection PyArgumentList

class RemoteWidget(QWidget):
    """Main Widget."""

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        # ///// START of code taken from artemis_svl.py

        # ***********************************************************************************
        #
        # Commands
        #
        # ***********************************************************************************
        self.SVL_CMD_VER     = 0x01  # version
        self.SVL_CMD_BL      = 0x02  # enter bootload mode
        self.SVL_CMD_NEXT    = 0x03  # request next chunk
        self.SVL_CMD_FRAME   = 0x04  # indicate app data frame
        self.SVL_CMD_RETRY   = 0x05  # request re-send frame
        self.SVL_CMD_DONE    = 0x06  # finished - all data sent

        self.barWidthInCharacters = 50  # Width of progress bar, ie [###### % complete

        self.crcTable = (
            0x0000, 0x8005, 0x800F, 0x000A, 0x801B, 0x001E, 0x0014, 0x8011,
            0x8033, 0x0036, 0x003C, 0x8039, 0x0028, 0x802D, 0x8027, 0x0022,
            0x8063, 0x0066, 0x006C, 0x8069, 0x0078, 0x807D, 0x8077, 0x0072,
            0x0050, 0x8055, 0x805F, 0x005A, 0x804B, 0x004E, 0x0044, 0x8041,
            0x80C3, 0x00C6, 0x00CC, 0x80C9, 0x00D8, 0x80DD, 0x80D7, 0x00D2,
            0x00F0, 0x80F5, 0x80FF, 0x00FA, 0x80EB, 0x00EE, 0x00E4, 0x80E1,
            0x00A0, 0x80A5, 0x80AF, 0x00AA, 0x80BB, 0x00BE, 0x00B4, 0x80B1,
            0x8093, 0x0096, 0x009C, 0x8099, 0x0088, 0x808D, 0x8087, 0x0082,
            0x8183, 0x0186, 0x018C, 0x8189, 0x0198, 0x819D, 0x8197, 0x0192,
            0x01B0, 0x81B5, 0x81BF, 0x01BA, 0x81AB, 0x01AE, 0x01A4, 0x81A1,
            0x01E0, 0x81E5, 0x81EF, 0x01EA, 0x81FB, 0x01FE, 0x01F4, 0x81F1,
            0x81D3, 0x01D6, 0x01DC, 0x81D9, 0x01C8, 0x81CD, 0x81C7, 0x01C2,
            0x0140, 0x8145, 0x814F, 0x014A, 0x815B, 0x015E, 0x0154, 0x8151,
            0x8173, 0x0176, 0x017C, 0x8179, 0x0168, 0x816D, 0x8167, 0x0162,
            0x8123, 0x0126, 0x012C, 0x8129, 0x0138, 0x813D, 0x8137, 0x0132,
            0x0110, 0x8115, 0x811F, 0x011A, 0x810B, 0x010E, 0x0104, 0x8101,
            0x8303, 0x0306, 0x030C, 0x8309, 0x0318, 0x831D, 0x8317, 0x0312,
            0x0330, 0x8335, 0x833F, 0x033A, 0x832B, 0x032E, 0x0324, 0x8321,
            0x0360, 0x8365, 0x836F, 0x036A, 0x837B, 0x037E, 0x0374, 0x8371,
            0x8353, 0x0356, 0x035C, 0x8359, 0x0348, 0x834D, 0x8347, 0x0342,
            0x03C0, 0x83C5, 0x83CF, 0x03CA, 0x83DB, 0x03DE, 0x03D4, 0x83D1,
            0x83F3, 0x03F6, 0x03FC, 0x83F9, 0x03E8, 0x83ED, 0x83E7, 0x03E2,
            0x83A3, 0x03A6, 0x03AC, 0x83A9, 0x03B8, 0x83BD, 0x83B7, 0x03B2,
            0x0390, 0x8395, 0x839F, 0x039A, 0x838B, 0x038E, 0x0384, 0x8381,
            0x0280, 0x8285, 0x828F, 0x028A, 0x829B, 0x029E, 0x0294, 0x8291,
            0x82B3, 0x02B6, 0x02BC, 0x82B9, 0x02A8, 0x82AD, 0x82A7, 0x02A2,
            0x82E3, 0x02E6, 0x02EC, 0x82E9, 0x02F8, 0x82FD, 0x82F7, 0x02F2,
            0x02D0, 0x82D5, 0x82DF, 0x02DA, 0x82CB, 0x02CE, 0x02C4, 0x82C1,
            0x8243, 0x0246, 0x024C, 0x8249, 0x0258, 0x825D, 0x8257, 0x0252,
            0x0270, 0x8275, 0x827F, 0x027A, 0x826B, 0x026E, 0x0264, 0x8261,
            0x0220, 0x8225, 0x822F, 0x022A, 0x823B, 0x023E, 0x0234, 0x8231,
            0x8213, 0x0216, 0x021C, 0x8219, 0x0208, 0x820D, 0x8207, 0x0202)

        # ///// END of code taken from artemis_svl.py

        # File location line edit
        self.msg_label = QLabel(self.tr('Firmware File:'))
        self.fileLocation_lineedit = QLineEdit()
        self.msg_label.setBuddy(self.msg_label)
        self.fileLocation_lineedit.setEnabled(False)
        self.fileLocation_lineedit.returnPressed.connect(
            self.on_browse_btn_pressed)

        # Browse for new file button
        self.browse_btn = QPushButton(self.tr('Browse'))
        self.browse_btn.setEnabled(True)
        self.browse_btn.pressed.connect(self.on_browse_btn_pressed)

        # Port Combobox
        self.port_label = QLabel(self.tr('COM Port:'))
        self.port_combobox = QComboBox()
        self.port_label.setBuddy(self.port_combobox)
        self.update_com_ports()

        # Refresh Button
        self.refresh_btn = QPushButton(self.tr('Refresh'))
        self.refresh_btn.pressed.connect(self.on_refresh_btn_pressed)

        # Baudrate Combobox
        self.baud_label = QLabel(self.tr('Baud Rate:'))
        self.baud_combobox = QComboBox()
        self.baud_label.setBuddy(self.baud_combobox)
        self.update_baud_rates()

        # Upload Button
        self.upload_btn = QPushButton(self.tr('Upload'))
        self.upload_btn.pressed.connect(self.on_upload_btn_pressed)

        # Upload Button
        self.updateBootloader_btn = QPushButton(self.tr('Update Bootloader'))
        self.updateBootloader_btn.pressed.connect(
            self.on_update_bootloader_btn_pressed)

        # Status bar
        self.status_label = QLabel(self.tr('Status:'))
        self.status = QLabel(self.tr(' '))

        # Messages Bar
        self.messages_label = QLabel(self.tr('Status / Warnings:'))

        # Messages Window
        self.messages = QPlainTextEdit()
        # Attempting to reduce window size
        #self.messages.setMinimumSize(1, 2)
        #self.messages.resize(1, 2)

        # Arrange Layout
        layout = QGridLayout()
        layout.addWidget(self.msg_label, 0, 0)
        layout.addWidget(self.fileLocation_lineedit, 0, 1)
        layout.addWidget(self.browse_btn, 0, 2)

        layout.addWidget(self.port_label, 1, 0)
        layout.addWidget(self.port_combobox, 1, 1)
        layout.addWidget(self.refresh_btn, 1, 2)

        layout.addWidget(self.baud_label, 2, 0)
        layout.addWidget(self.baud_combobox, 2, 1)

        #layout.addWidget(self.status_label, 3, 0)
        #layout.addWidget(self.status, 3, 1)

        layout.addWidget(self.messages_label, 3, 0)
        layout.addWidget(self.messages, 4, 0, 4, 3)

        layout.addWidget(self.upload_btn, 15, 2)
##        layout.addWidget(self.updateBootloader_btn, 15, 1)

        self.setLayout(layout)

        self._load_settings()

        # Make the text edit window read-only
        self.messages.setReadOnly(True)
        self.messages.clear()  # Clear the message window

    def addMessage(self, msg: str) -> None:
        """Add msg to the messages window, ensuring that it is visible"""
        self.messages.moveCursor(QTextCursor.End)
        self.messages.ensureCursorVisible()
        self.messages.appendPlainText(msg)
        self.messages.ensureCursorVisible()
        self.repaint()

    def _load_settings(self) -> None:
        """Load settings on startup."""
        settings = QSettings()

        # port name
        port_name = settings.value(SETTING_PORT_NAME)
        if port_name is not None:
            index = self.port_combobox.findData(port_name)
            if index > -1:
                self.port_combobox.setCurrentIndex(index)

        # last message
        msg = settings.value(SETTING_FILE_LOCATION)
        if msg is not None:
            self.fileLocation_lineedit.setText(msg)

        baud = settings.value(SETTING_BAUD_RATE)
        if baud is not None:
            index = self.baud_combobox.findData(baud)
            if index > -1:
                self.baud_combobox.setCurrentIndex(index)

    def _save_settings(self) -> None:
        """Save settings on shutdown."""
        settings = QSettings()
        settings.setValue(SETTING_PORT_NAME, self.port)
        settings.setValue(SETTING_FILE_LOCATION, self.fileLocation_lineedit.text())
        settings.setValue(SETTING_BAUD_RATE, self.baudRate)

    def show_error_message(self, msg: str) -> None:
        """Show a Message Box with the error message."""
        QMessageBox.critical(self, QApplication.applicationName(), str(msg))

    def update_com_ports(self) -> None:
        """Update COM Port list in GUI."""
        self.port_combobox.clear()

        settings = QSettings()
        port_name = settings.value(SETTING_PORT_NAME)

        index = 0
        indexOfCH340 = -1
        for desc, name, sys in gen_serial_ports():
            longname = desc + " (" + name + ")"
            self.port_combobox.addItem(longname, sys)
            if("CH340" in longname):
                if port_name is not None: # Allow SETTING_PORT_NAME to take priority
                    if(sys == port_name):
                        indexOfCH340 = index
                elif (indexOfCH340 == -1):  # Otherwise select the first available CH340
                    indexOfCH340 = index
                    # it could be too early to call self.addMessage("CH340 found at index " + str(indexOfCH340))
            index = index + 1

        if indexOfCH340 > -1:
            self.port_combobox.setCurrentIndex(indexOfCH340)

    def update_baud_rates(self) -> None:
        """Update baud rate list in GUI."""
        self.baud_combobox.addItem("921600", 921600)
        self.baud_combobox.addItem("460800", 460800)
        self.baud_combobox.addItem("115200", 115200)

    @property
    def port(self) -> str:
        """Return the current serial port."""
        return self.port_combobox.currentData()

    @property
    def baudRate(self) -> str:
        """Return the current baud rate."""
        return self.baud_combobox.currentData()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle Close event of the Widget."""
        self._save_settings()

        event.accept()

    def on_refresh_btn_pressed(self) -> None:
        self.update_com_ports()
        self.addMessage("Ports Refreshed")

    def on_upload_btn_pressed(self) -> None:
        """Check if port is available"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.addMessage("Port No Longer Available")
            return

        """Check if file exists"""
        fileExists = False
        try:
            f = open(self.fileLocation_lineedit.text())
            fileExists = True
        except IOError:
            fileExists = False
        finally:
            if (fileExists == False):
                self.addMessage("File Not Found")
                return
            f.close()

        self.addMessage("Uploading")

        self.upload_main() # Call artemis_svl.py (previously this spawned a QProcess)

    def on_update_bootloader_btn_pressed(self) -> None:
        """Check if port is available"""
        portAvailable = False
        for desc, name, sys in gen_serial_ports():
            if (sys == self.port):
                portAvailable = True
        if (portAvailable == False):
            self.addMessage("Port No Longer Available")
            return

        self.addMessage("Updating bootloader")

        self.process = QProcess()
        self.process.readyReadStandardError.connect(
            self.onReadyReadStandardError)
        self.process.readyReadStandardOutput.connect(
            self.onReadyReadStandardOutput)

        self.process.start("tools/ambiq_bin2board.exe --bin tools/artemis_svl.bin --load-address-blob 0x20000 --magic-num 0xCB --version 0x0 --load-address-wired 0xC000 -i 6 --options 0x1 -b 115200 -port " + str(self.port) +
                           " -r 2 -v")

    def onReadyReadStandardError(self):
        error = self.process.readAllStandardError().data().decode()
        # print(error)
        self.addMessage(error)

    def onReadyReadStandardOutput(self):
        """Parse the output from the process. Update our status as we go."""
        result = self.process.readAllStandardOutput().data().decode()
        # print(result)
        self.addMessage(result)
        if ("complete" in result):
            self.addMessage("Complete")
        elif ("failed" in result):
            self.addMessage("Upload Failed")
        elif ("open" in result):
            self.addMessage("Port In Use / Please Close")

    def on_browse_btn_pressed(self) -> None:
        """Open dialog to select bin file."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(
            None,
            "Select Firmware to Upload",
            "",
            "Firmware Files (*.bin);;All Files (*)",
            options=options)
        if fileName:
            self.fileLocation_lineedit.setText(fileName)

    # ///// START of code taken from artemis_svl.py

    def get_crc16(self, data) -> int:
        """Compute CRC on a byte array"""

        #Table and code ported from Artemis SVL bootloader
        crc = 0x0000
        data = bytearray(data)
        for ch in data:
            tableAddr = ch ^ (crc >> 8)
            CRCH = (self.crcTable[tableAddr] >> 8) ^ (crc & 0xFF)
            CRCL = self.crcTable[tableAddr] & 0x00FF
            crc = CRCH << 8 | CRCL
        #self.addMessage("\tcrc is " + str(crc))
        return crc


    def wait_for_packet(self) -> dict:
        """Wait for a packet"""

        packet = {'len':0, 'cmd':0, 'data':0, 'crc':1, 'timeout':1}

        n = self.ser.read(2) # get the length bytes
        if(len(n) < 2):
            #self.addMessage("\tpacket length < 2")
            return packet

        packet['len'] = int.from_bytes(n, byteorder='big', signed=False)
        #self.addMessage("\tpacket length " + str(packet['len']))

        if(packet['len'] == 0): # Check for an empty packet
            return packet

        payload = self.ser.read(packet['len']) #read bytes (or timeout)

        if(len(payload) != packet['len']):
            #self.addMessage("\tincorrect payload length")
            return packet
        
        packet['timeout'] = 0                           # all bytes received, so timeout is not true
        packet['cmd'] = payload[0]                      # cmd is the first byte of the payload
        packet['data'] = payload[1:packet['len']-2]     # the data is the part of the payload that is not cmd or crc
        packet['crc'] = self.get_crc16(payload)         # performing the crc on the whole payload should return 0

        return packet


    def send_packet(self, cmd, data) -> None:
        """Send a packet"""
        
        data = bytearray(data)
        num_bytes = 3 + len(data)
        #self.addMessage("\tsending packet length " + str(num_bytes))
        payload = bytearray(cmd.to_bytes(1,'big'))
        payload.extend(data)
        crc = self.get_crc16(payload)
        payload.extend(bytearray(crc.to_bytes(2,'big')))
        #self.addMessage("\tsending packet crc " + str(crc))

        self.ser.write(num_bytes.to_bytes(2,'big'))
        #self.addMessage("\t" + str(num_bytes.to_bytes(2,'big')))
        self.ser.write(bytes(payload))
        #self.addMessage("\t" + str(bytes(payload)))

    def phase_setup(self) -> None:
        """Setup: signal baud rate, get version, and command BL enter"""

        baud_detect_byte = b'U'

        self.addMessage("Phase:\tSetup")
        
        self.ser.reset_input_buffer()                        # Handle the serial startup blip
        self.addMessage("\tCleared startup blip")

        self.ser.write(baud_detect_byte)            # send the baud detection character
        #self.addMessage("\tsent baud_detect_byte")

        packet = self.wait_for_packet()
        #self.addMessage("\twait_for_packet complete")
        if(packet['timeout']):
            #self.addMessage("\twait_for_packet timeout")
            return
        if(packet['crc']):
            #self.addMessage("\twait_for_packet crc error")
            return
        
        self.addMessage("\tGot SVL Bootloader Version: " + str(int.from_bytes(packet['data'], 'big')))
        self.addMessage("\tSending \'enter bootloader\' command")

        self.send_packet(self.SVL_CMD_BL, b'')
        #self.addMessage("\tfinished send_packet")

        # Now enter the bootload phase


    def phase_bootload(self) -> bool:
        """Bootloader phase (Artemis is locked in)"""

        startTime = time.time()
        frame_size = 512*4

        resend_max = 4
        resend_count = 0

        self.addMessage("Phase:\tBootload")

        with open(self.fileLocation_lineedit.text(), mode='rb') as binfile:
            application = binfile.read()
            total_len = len(application)

            total_frames = math.ceil(total_len/frame_size)
            curr_frame = 0
            progressChars = 0

            self.addMessage("\tSending " + str(total_len) +
                         " bytes in " + str(total_frames) + " frames")

            bl_done = False
            bl_failed = False
            while((not bl_done) and (not bl_failed)):
                    
                packet = self.wait_for_packet()               # wait for indication by Artemis

                if(packet['timeout'] or packet['crc']):
                    self.addMessage("\tError receiving packet")
                    bl_failed = True
                    bl_done = True

                if( packet['cmd'] == self.SVL_CMD_NEXT ):
                    self.addMessage("\tGot frame request")
                    curr_frame += 1
                    resend_count = 0
                elif( packet['cmd'] == self.SVL_CMD_RETRY ):
                    self.addMessage("\tRetrying...")
                    resend_count += 1
                    if( resend_count >= resend_max ):
                        bl_failed = True
                        bl_done = True
                else:
                    self.addMessage("\tUnknown error")
                    bl_failed = True
                    bl_done = True

                if( curr_frame <= total_frames ):
                    frame_data = application[((curr_frame-1)*frame_size):((curr_frame-1+1)*frame_size)]
                    self.addMessage("\tSending frame #" + str(curr_frame) + ", length: " + str(len(frame_data)))
                    self.send_packet(self.SVL_CMD_FRAME, frame_data)
                else:
                    self.send_packet(self.SVL_CMD_DONE, b'')
                    bl_done = True

            if( bl_failed == False ):
                self.addMessage("Upload complete!")
                endTime = time.time()
                bps = total_len / (endTime - startTime)
                self.addMessage("Nominal bootload " + str(round(bps, 2)) + " bytes/sec\n")
            else:
                self.addMessage("Upload failed!\n")

            return bl_failed


    def upload_main(self) -> None:
        """SparkFun Variable Loader (Variable baud rate bootloader for Artemis Apollo3 modules)"""
        try:
            num_tries = 3

            self.messages.clear() # Clear the message window

            self.addMessage("Artemis SVL Bootloader")

            for _ in range(num_tries):

                bl_failed = False

                # Open the serial port
                #self.addMessage("Opening " + str(self.port) + " at " + str(self.baudRate) + " Baud")
                with serial.Serial(self.port, self.baudRate, timeout=0.5) as self.ser:

                    t_su = 0.15             # startup time for Artemis bootloader   (experimentally determined - 0.095 sec min delay)

                    time.sleep(t_su)        # Allow Artemis to come out of reset
                    self.phase_setup()      # Perform baud rate negotiation

                    bl_failed = self.phase_bootload()     # Bootload

                if( bl_failed == False ):
                    break

        except:
            self.addMessage("Could not communicate with board!\n")

        try:
            self.ser.close()
        except:
            pass
            

    # ///// END of code taken from artemis_svl.py

if __name__ == '__main__':
    import sys
    app = QApplication([])
    app.setOrganizationName('SparkFun')
    app.setApplicationName('Artemis Firmware Uploader ' + guiVersion)
    app.setWindowIcon(QIcon("Artemis-Logo-Rounded.png"))
    w = RemoteWidget()
    w.show()
    sys.exit(app.exec_())
