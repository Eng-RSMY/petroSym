# -*- coding: utf-8 -*-
"""
Created on Tue Aug 25 13:08:19 2015

@author: jgimenez
"""

from PyQt4 import QtGui, QtCore
from run_ui import Ui_runUI
from PyFoam.RunDictionary.ParsedParameterFile import ParsedParameterFile
import os
from reset import *
from time import localtime, strftime, struct_time
from logTab import *
from ExampleThread import *

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class runUI(QtGui.QScrollArea, Ui_runUI):
    def __init__(self, parent=None, f=QtCore.Qt.WindowFlags()):
        QtGui.QScrollArea.__init__(self, parent)
        self.setupUi(self)
        
class runWidget(runUI):
    
    def __init__(self, currentFolder, solvername):
        runUI.__init__(self)
        self.solvername = solvername
        self.currentFolder = currentFolder
        

    def setCurrentFolder(self, currentFolder, solvername):
        self.currentFolder = currentFolder
        self.solvername = solvername
        
        #Si abro la gui y hay un caso corriendo, desabilito estos botones
        if (self.window().runningpid!= -1):
            self.pushButton_run.setEnabled(False)
            self.pushButton_reset.setEnabled(False)
            
        
    def runCase(self):
        #modifico el control dict porque pude haber parado la simulacion        
        filename = '%s/system/controlDict'%self.currentFolder
        parsedData = ParsedParameterFile(filename,createZipped=False)
        parsedData['stopAt'] = 'endTime'
        parsedData.writeFile()
        
        self.window().removeFilesPostPro()
        
        #retraso un minuto la edicion del control dict
        tt = list(localtime())
        tt[4] = (tt[4]-1)%60 #Agrego el modulo porque cuando el min es 0, 0-1 = -1
        command = 'touch -d "%s" %s'%(strftime("%Y-%m-%d %H:%M:%S", struct_time(tuple(tt))),filename)
        os.system(command)
        
        filename = '%s/run.log'%self.currentFolder
        self.window().newLogTab('Run',filename)
        command = '%s -case %s > %s &'%(self.solvername,self.currentFolder,filename)
        os.system(command)
        
        command = 'pidof %s'%self.solvername
        import subprocess
        self.window().runningpid = subprocess.check_output(command, shell=True)
        self.window().runningpid.replace('\n','') #Me lo devuelve con un espacio al final
        self.window().runningpid = int(self.window().runningpid) #Y como string
        self.window().save_config()
        
        self.pushButton_run.setEnabled(False)
        self.pushButton_reset.setEnabled(False)
        self.window().findChild(logTab,'%s/run.log'%self.currentFolder).findChild(QtGui.QPushButton,'pushButton_3').setEnabled(True)
        self.window().updateLogFiles()
        
    def changeType(self):
        if self.type_serial.isChecked():
            self.num_proc.setEnabled(False)
            self.reconstruct.setEnabled(False)
            self.pushButton_decompose.setEnabled(False)
        else:
            self.num_proc.setEnabled(True)
            self.reconstruct.setEnabled(True)
            self.pushButton_decompose.setEnabled(True)

    def resetCase(self):
        w = reset()
        result = w.exec_()
        if result:
            command = 'pyFoamClearCase.py %s %s'%(w.getParams(), self.currentFolder)
            os.system(command)
            if w.deleteSnapshots():
                command = 'rm -rf %s/snapshots'%self.currentFolder                
                os.system(command)
            if w.resetFigures():
                self.window().resetFigures(w.deletePostpro(),w.deleteSnapshots())
            filename = '%s/system/controlDict'%self.currentFolder
            parsedData = ParsedParameterFile(filename,createZipped=False)
            parsedData['startFrom'] = 'startTime'            
            parsedData['startTime'] = '0'
            parsedData.writeFile()
            self.window().typeFile = {}
            self.window().pending_files = []
            self.window().pending_dirs = []
            self.window().updateLogFiles()
            self.window().save_config()

    def decomposeCase(self):
        return