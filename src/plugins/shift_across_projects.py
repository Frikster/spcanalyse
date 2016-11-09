#!/usr/bin/env python3

import os
from os.path import isfile, join
from os import listdir
import sys
import traceback
import time
import numpy as np
from shutil import copyfile
import matplotlib.pyplot as plt

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui

sys.path.append('..')
import qtutil
from project import Project
import tifffile as tiff

from .util.mygraphicsview import MyGraphicsView
from .util import mse_ui_elements as mue
from .util import project_functions as pfs

class NotConvertedError(Exception):
  pass

class FileAlreadyInProjectError(Exception):
  def __init__(self, filename):
    self.filename = filename

class Widget(QWidget):
  def __init__(self, project, parent=None):
    super(Widget, self).__init__(parent)

    if not project:
      return

    self.project = project

    # define ui components and global data
    self.view = MyGraphicsView(self.project)
    self.project_list = []
    self.video_list = QListView()
    self.list_shifted = QListView()
    self.origin_label = QLabel('Origin:')
    self.left = QFrame()
    self.right = QFrame()
    self.setup_ui()

    self.video_list.setModel(QStandardItemModel())
    self.video_list.selectionModel().selectionChanged[QItemSelection,
                                                      QItemSelection].connect(self.selected_video_changed)
    self.list_shifted.setModel(QStandardItemModel())
    for f in self.project.files:
      if f['type'] == 'shifted':
        self.video_list.model().appendRow(QStandardItem(f['path']))

  def setup_ui(self):
    vbox_view = QVBoxLayout()
    vbox_view.addWidget(self.view)
    self.view.vb.setCursor(Qt.CrossCursor)
    self.left.setLayout(vbox_view)

    vbox = QVBoxLayout()
    vbox.addWidget(QLabel('Data from other projects'))
    pb = QPushButton('Load JSON files from other projects')
    pb.clicked.connect(self.new_json)
    vbox.addWidget(pb)
    self.video_list.setStyleSheet('QListView::item { height: 26px; }')
    self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
    vbox.addWidget(self.video_list)
    vbox.addWidget(qtutil.separator())
    pb = QPushButton('Align selected data to this project')
    pb.clicked.connect(self.new_json)
    vbox.addWidget(pb)
    vbox.addWidget(QLabel('Shifted Data from other projects'))
    self.list_shifted.setStyleSheet('QListView::item { height: 26px; }')
    self.list_shifted.setSelectionMode(QAbstractItemView.NoSelection)
    vbox.addWidget(self.list_shifted)
    self.right.setLayout(vbox)
    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(3)
    splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
    splitter.addWidget(self.left)
    splitter.addWidget(self.right)
    hbox_global = QHBoxLayout()
    hbox_global.addWidget(splitter)
    self.setLayout(hbox_global)

  def refresh_video_list_via_combo_box(self, trigger_item=None):
    pfs.refresh_video_list_via_combo_box(self, trigger_item)

  def selected_video_changed(self, selected, deselected):
    pfs.selected_video_changed_multi(self, selected, deselected)

  def new_json(self):
    fd = FileDialog()
    fd.exec_()
    fd.show()
    dirnames = fd.selectedFiles()

    if not dirnames or dirnames[0] == fd.directory():
        return
    for project_dir in dirnames:
        only_files = [join(project_dir, f) for f in listdir(project_dir) if isfile(join(project_dir, f))]
        json_paths = [f for f in only_files if f[-5:] == '.json']
        if not json_paths:
            qtutil.critical("Not a project directory. No JSON file found in " + project_dir + ". Skipping.")
            continue
        self.project_list = self.project_list + [Project(project_dir)]
        for project in self.project_list:
            pfs.refresh_video_list(project, self.video_list)
            # for f in project.files:
            #     if f['type'] == 'video':
            #         self.video_list.model().appendRow(QStandardItem(f['path']))
        # self.import_files(filenames)

  def import_files(self, filenames):
    for filename in filenames:
        if filename in [f['path'] for f in self.project.files]:
            continue
        try:
            filename = self.import_file(filename)
        except NotConvertedError:
            qtutil.warning('Skipping file \'{}\' since not converted.'.format(filename))
        except FileAlreadyInProjectError as e:
            qtutil.warning('Skipping file \'{}\' since already in project.'.format(e.filename))
        except:
            qtutil.critical('Import of \'{}\' failed:\n'.format(filename) + \
                            traceback.format_exc())
        else:
            self.listview.model().appendRow(QStandardItem(filename))

class FileDialog(QtGui.QFileDialog):
    def __init__(self, *args):
        QtGui.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        for view in self.findChildren((QtGui.QListView, QtGui.QTreeView)):
            if isinstance(view.model(), QtGui.QFileSystemModel):
                view.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    #     self.filesSelected.connect(self.handleStop)
    #     self._running = True
    #     # while self._running:
    #     #     QtGui.qApp.processEvents()
    #     #     time.sleep(0.05)
    #
    # def handleStop(self):
    #     self._running = False


class MyPlugin:
    def __init__(self, project):
        self.name = 'Shift Across Projects'
        self.widget = Widget(project)
    def run(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)
    w = QMainWindow()
    w.setCentralWidget(Widget(None))
    w.show()
    app.exec_()
    sys.exit()
