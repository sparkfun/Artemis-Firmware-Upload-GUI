#!/usr/bin/env python3
#-----------------------------------------------------------------------------
# artemis_upload.py
#
#------------------------------------------------------------------------
#
# Written/Update by  SparkFun Electronics, Fall 2022
#
# This python package implements a GUI Qt application that supports
# firmware and boot loader uploading to the SparkFun Artemis module
#
# This file is part of the job dispatch system, which runs "jobs"
# in a background thread for the artemis_uploader package/application.
#
# This file is the main command line entry point, which calls into
# the 'artemis_uploader' package to launch the application
#
# More information on qwiic is at https://www.sparkfun.com/artemis
#
# Do you like this library? Help support SparkFun. Buy a board!
#
#==================================================================================
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
#==================================================================================
#
# pylint: disable=old-style-class, missing-docstring, wrong-import-position
#
#-----------------------------------------------------------------------------
import artemis_uploader

# Call the app entry point in the package
artemis_uploader.startArtemisUploader()

