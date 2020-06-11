SparkFun Artemis Firmware Uploader GUI
========================================

![Artemis Firmware Uploader GUI](https://cdn.sparkfun.com/assets/home_page_posts/3/2/4/5/Artemis_Firmware_Uploader_GUI.jpg)

The Artemis Firmware Uploader (AFU) is a simple to use GUI for updating firmware and the bootloader on Artemis based products.

To use:

* Download the [repo ZIP](https://github.com/sparkfun/Artemis-Firmware-Upload-GUI/archive/master.zip)
* Run the artemis_firmware_uploader_gui executable for your platform
  * **/Windows** contains the Windows .exe
  * **/OSX** contains an executable for macOS X
  * **/Linux** contains an executable built on Ubuntu
  * **/Raspberry_Pi__Debian** contains an executable for Raspberry Pi 4 (Debian Buster)
* Select the firmware file you'd like to upload (should end in *.bin*)
* Attach the Artemis target board over USB
* Select the COM port (hit Refresh to refresh the list of USB devices)
* Press Upload

The GUI does take a few seconds to load and run. _**Don't Panic**_ if the GUI does not start right away.

Be sure you are loading firmware for your board or product. While it's unlikely to damage Artemis by loading incorrect firmware it will erase the pre-existing firmware and may lead to the peripherals being controlled incorrectly.

An example *Blink.bin* firmware file is included in the repo. This firmware will cause these LEDs to blink at 1Hz:
* the D5 LED on the [SparkFun RedBoard Artemis ATP](https://www.sparkfun.com/products/15442)
* the D13 LED on the [SparkFun RedBoard Artemis](https://www.sparkfun.com/products/15444)
* the D18 LED on the [SparkFun Thing Plus - Artemis](https://www.sparkfun.com/products/15574)
* the D19 LED on the [SparkFun RedBoard Artemis Nano](https://www.sparkfun.com/products/15443)
* the Green LED on the [SparkFun Edge Development Board - Apollo3 Blue](https://www.sparkfun.com/products/15170)
* the STAT LED on the [OpenLog Artemis](https://www.sparkfun.com/products/15846)
* the D19 and GNSS LEDs on the [Artemis Global Tracker](https://www.sparkfun.com/products/16469)

Pressing the 'Update Bootloader' button will erase all firmware on the Artemis and load the latest bootloader firmware. This is handy when SparkFun releases updates to the [SVL](https://github.com/sparkfun/SparkFun_Apollo3_AmbiqSuite_BSPs/blob/master/common/examples/artemis_svl/src/main.c).

SparkFun labored with love to create this code. Feel like supporting open source hardware?
Buy a [breakout board](https://www.sparkfun.com/products/15444) from SparkFun!

Repository Contents
-------------------

* **/tools** contains the python source files and SVL binary
* **/Windows** contains the Windows .exe
* **/OSX** contains an executable for macOS X
* **/Linux** contains an executable built on Ubuntu
* **/Raspberry_Pi__Debian** contains an executable for Raspberry Pi 4 (Debian Buster)
* **LICENSE.md** contains the licence information

Building Your Own Executable
----------------------------

We use Python3 and [pyinstaller](http://www.pyinstaller.org/) to create the executables. You can create your own executable if you want to, so long as you have PyQt5 and the other prerequisites installed.

The **/tools** folder contains the python source code, icons and the latest SVL bootloader binary. You can run the python code directly by calling:

```python3 artemis_firmware_uploader_gui.py```

On Windows platforms, you can create an executable by calling:

```pyinstaller --onefile --noconsole --distpath=. --icon=artemis_firmware_uploader_gui.ico --add-data="artemis_svl.bin;." --add-data="Artemis-Logo-Rounded.png;." artemis_firmware_uploader_gui.py```

On Linux platforms, you need to replace the semicolons with colons:

```pyinstaller --onefile --noconsole --distpath=. --icon=artemis_firmware_uploader_gui.ico --add-data="artemis_svl.bin:." --add-data="Artemis-Logo-Rounded.png:." artemis_firmware_uploader_gui.py```

This will create a single file executable which has the SVL binary bundled into it. You can then distribute it and run it on the same platform without needing Python3.

License Information
-------------------

This product is _**open source**_!

If you have any questions or concerns on licensing, please contact techsupport@sparkfun.com.

Please use, reuse, and modify these files as you see fit. Please maintain attribution to SparkFun Electronics and release any derivative under the same license.

Distributed as-is; no warranty is given.

- Your friends at SparkFun.
