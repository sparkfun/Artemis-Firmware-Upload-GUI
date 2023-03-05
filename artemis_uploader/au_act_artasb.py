
#-----------------------------------------------------------------------------
# au_act_astasb.py
#
#------------------------------------------------------------------------
#
# Written/Update by  SparkFun Electronics, Fall 2022
#
# This python package implements a GUI Qt application that supports
# firmware and bootloader uploading to the SparkFun Artemis module
#
# This file is part of the job dispatch system, which runs "jobs"
# in a background thread for the artemis_uploader package/application.
#
# This file defines a "Action", which manages the uploading of a
# bootloader to an artemis module
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
from .au_action import AxAction, AxJob
from .asb import main as asb_main
import tempfile
import sys
#--------------------------------------------------------------------------------------
# Artemis Boot loader burn action
class AUxArtemisBurnBootloader(AxAction):

    ACTION_ID = "artemis-burn-bootloader"
    NAME = "Artemis Bootloader Upload"

    def __init__(self) -> None:
        super().__init__(self.ACTION_ID, self.NAME)

    def run_job(self, job:AxJob):

        # fake command line args - since the apollo3 bootloader command will use
        # argparse 
        sys.argv = ['./asb/asb.py', \
                    "--bin", job.file, \
                    "-port", job.port, \
                    "-b", str(job.baud), \
                    "-o", tempfile.gettempdir(), \
                    "--load-address-blob", "0x20000", \
                    "--magic-num", "0xCB", \
                    "--version", "0x0", \
                    "--load-address-wired", "0xC000", \
                    "-i", "6", \
                    "-clean", "1" ]

        # Call the ambiq command
        asb_main()
