SparkFun Artemis Firmware Uploader GUI
========================================

![Artemis Firmware Uploader GUI](https://cdn.sparkfun.com/assets/home_page_posts/3/2/4/5/Artemis_Firmware_Uploader_GUI.jpg)

The Artemis Firmware Uploader (AFU) is a simple to use Windows GUI for updating firmware and the bootloader on Artemis based products.

To use:

* Download the repo ZIP
* Run artemis_firmware_uploader_gui.exe
* Select the firmware file you'd like to upload (should end in *.bin*)
* Attach the Artemis target board over USB
* Select the COM port (hit Refresh to refresh the list of USB devices)
* Press Upload

Be sure you are loading firmware for your board or product. While it's unlikely to damage Artemis by loading incorrect firmware it will erase the pre-existing firmware and may lead to the peripherals being controlled incorrectly.

A *Blink.bin* firmware file is included. This will cause pin 5 (the status LED on [ATP](https://www.sparkfun.com/products/15442)to blink at 1Hz.

Pressing the 'Update Bootloader' button will erase all firmware on the Artemis and load the latest bootloader firmware. This is handy when SparkFun releases updates to the [SVL](https://github.com/sparkfun/SparkFun_Apollo3_AmbiqSuite_BSPs/blob/master/common/examples/artemis_svl/src/main.c).

SparkFun labored with love to create this code. Feel like supporting open source hardware? 
Buy a [breakout board](https://www.sparkfun.com/products/15444) from SparkFun!

Repository Contents
-------------------

* **/tools** - The python source files and executables

License Information
-------------------

This product is _**open source**_! 

If you have any questions or concerns on licensing, please contact techsupport@sparkfun.com.

Please use, reuse, and modify these files as you see fit. Please maintain attribution to SparkFun Electronics and release any derivative under the same license.

Distributed as-is; no warranty is given.

- Your friends at SparkFun.