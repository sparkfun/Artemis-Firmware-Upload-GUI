#-----------------------------------------------------------------------------
# au_action.py
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
# This file defines key data types for the background processing system.
# A "Job" type and a "Action" type are defined in this file.
#
#    Job - has a type and a list of parameter values for the Job to execute
#
#    Action - defines a process type that runs a job
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
# "actions" - commands that execute a command for the application
# 
#--------------------------------------------------------------------------
# simple job class - list of parameters and an ID string. 
#
# Sub-classes a dictionary (dict), and stores parameters in the dictionary. 
# Parameters can also be accessed as attributes. 
#
# Example:
#
#  myJob = AxJob('my-job-id')
#
#  myJob['data'] = 1
#
#  print(myJob.data)
#
#  myJob.data=2
#
#  print(myJob['data'])
#
# And can init the job using dictionary syntax
#
#  myJob = AxJob('my-job-id', {"data":1, "sensor":"spectra1", "flight":33.3})
#
#  print(myJob.data)
#  print(myJob.sensor)
#  print(myJob.flight)
#

class AxJob(dict):

	# class variable for job ids
	_next_job_id =1

	def __init__(self, action_id:str, indict=None):

		if indict is None:
			indict = {}

		self.action_id = action_id

		self.job_id = AxJob._next_job_id;
		AxJob._next_job_id = AxJob._next_job_id+1;

		# super
		dict.__init__(self, indict)

		# flag
		self.__initialized = True

	def __getattr__(self, item):

		try:
			return self.__getitem__(item)
		except KeyError:
			raise AttributeError(item)

	def __setattr__(self, item, value):

		if '_AxJob__initialized' not in  self.__dict__:  # this test allows attributes to be set in the __init__ method
			return dict.__setattr__(self, item, value)

		else:
			self.__setitem__(item, value)

	#def __str__(self):
	#	return "\"" + self.action_id + "\" :" + str(self._args)

#--------------------------------------------------------------------------
# Base action class - defines method
#
# Sub-class this class to create a action

class AxAction(object):

	def __init__(self, action_id:str, name="") -> None:
		object.__init__(self)
		self.action_id = action_id
		self.name = name

	def run_job(self, job:AxJob) -> int:
		return 1 # error
