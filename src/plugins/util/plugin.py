import functools

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from . import project_functions as pfs
from .mygraphicsview import MyGraphicsView
from .qt import MyListView


class PrimaryFunctionMissing(Exception):
    def __init__(self, message):
        self.message = message


class WidgetDefault(object):
    class Labels(object):
        video_list_indices_label = 'video_list_indices'
        last_manips_to_display_label = 'last_manips_to_display'
        video_player_scaled_label = 'video_player_scaled'
        video_player_unscaled_label = 'video_player_unscaled'
        delete_signal_label = 'delete_signal'
        detatch_signal_label = 'detatch_signal'


    class Defaults(object):
        video_list_indices_default = [0]
        last_manips_to_display_default = ['All']
        list_display_type = ['video']

    def __init__(self, project, plugin_position):
        if not project or not isinstance(plugin_position, int):
            return
        self.plugin_position = plugin_position
        self.project = project

        # define ui components and global data
        self.view = MyGraphicsView(self.project)
        self.video_list = MyListView()
        self.video_list.setModel(QStandardItemModel())
        list_of_manips = pfs.get_list_of_project_manips(self.project)
        self.toolbutton = pfs.add_combo_dropdown(self, list_of_manips)
        self.left = QFrame()
        self.right = QFrame()
        self.vbox_view = QVBoxLayout()
        self.vbox = QVBoxLayout()
        self.video_list_indices = []
        self.toolbutton_values = []
        self.open_dialogs = []
        self.selected_videos = []
        self.shown_video_path = None

        self.setup_ui()
        self.setup_signals()
        if isinstance(plugin_position, int):
            self.params = project.pipeline[self.plugin_position]
            self.setup_param_signals()
            try:
                self.setup_params()
            except:
                self.setup_params(reset=True)
            pfs.refresh_list(self.project, self.video_list, self.video_list_indices,
                             self.Defaults.list_display_type, self.toolbutton_values)

    def video_triggered(self, index, scaling=True):
        pfs.video_triggered(self, index, scaling)

    def setup_ui(self):
        self.vbox_view.addWidget(self.view)
        self.left.setLayout(self.vbox_view)

        self.vbox.addWidget(self.toolbutton)
        self.vbox.addWidget(QLabel('Choose video:'))
        self.video_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.video_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.video_list.setStyleSheet('QListView::item { height: 26px; }')
        self.vbox.addWidget(self.video_list)

        self.right.setLayout(self.vbox)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setStyleSheet('QSplitter::handle {background: #cccccc;}')
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)
        hbox_global = QHBoxLayout()
        hbox_global.addWidget(splitter)
        self.setLayout(hbox_global)

    def setup_signals(self):
        self.video_list.selectionModel().selectionChanged.connect(self.selected_video_changed)
        self.video_list.doubleClicked.connect(self.video_triggered)
        self.toolbutton.activated.connect(self.refresh_video_list_via_combo_box)
        self.video_list.video_player_scaled_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.video_player_scaled_label))
        self.video_list.video_player_unscaled_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.video_player_unscaled_label))
        self.video_list.delete_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.delete_signal_label))
        self.video_list.detatch_signal.connect(functools.partial(
            self.prepare_context_menu_signal_for_action, self.Labels.detatch_signal_label))

    def prepare_context_menu_signal_for_action(self, key):
        if key == self.Labels.video_player_scaled_label:
            self.video_triggered(self.video_list.currentIndex())
        if key == self.Labels.video_player_unscaled_label:
            self.video_triggered(self.video_list.currentIndex(), False)
        if key == self.Labels.delete_signal_label:
            pass
        if key == self.Labels.detatch_signal_label:
            pass

    def setup_params(self, reset=False):
        if len(self.params) == 1 or reset:
            self.update_plugin_params(self.Labels.video_list_indices_label, self.Defaults.video_list_indices_default)
            self.update_plugin_params(self.Labels.last_manips_to_display_label, self.Defaults.last_manips_to_display_default)
        self.video_list_indices = self.params[self.Labels.video_list_indices_label]
        self.toolbutton_values = self.params[self.Labels.last_manips_to_display_label]
        manip_items = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
                                  if self.toolbutton.itemText(i) in self.params[self.Labels.last_manips_to_display_label]]
        for item in manip_items:
            item.setCheckState(Qt.Checked)
        not_checked = [self.toolbutton.model().item(i, 0) for i in range(self.toolbutton.count())
                       if self.toolbutton.itemText(i) not in self.params[self.Labels.last_manips_to_display_label]]
        for item in not_checked:
            item.setCheckState(Qt.Unchecked)

    def setup_param_signals(self):
        self.video_list.selectionModel().selectionChanged.connect(self.prepare_video_list_for_update)
        self.toolbutton.activated.connect(self.prepare_toolbutton_for_update)

    def prepare_video_list_for_update(self, selected, deselected):
        val = [v.row() for v in self.video_list.selectedIndexes()]
        self.update_plugin_params(self.Labels.video_list_indices_label, val)

    def prepare_toolbutton_for_update(self, trigger_item):
        val = self.params[self.Labels.last_manips_to_display_label]
        selected = self.toolbutton.itemText(trigger_item)
        if selected not in val:
            val = val + [selected]
            if trigger_item != 0:
                val = [manip for manip in val if manip not in self.Defaults.last_manips_to_display_default]
        else:
            val = [manip for manip in val if manip != selected]

        self.update_plugin_params(self.Labels.last_manips_to_display_label, val)

    def update_plugin_params(self, key, val):
        pfs.update_plugin_params(self, key, val)

    def refresh_video_list_via_combo_box(self, trigger_item=None):
        pfs.refresh_video_list_via_combo_box(self, self.Defaults.list_display_type, trigger_item)

    def selected_video_changed(self, selected, deselected):
        pfs.selected_video_changed_multi(self, selected, deselected)

    def execute_primary_function(self, input_paths=None):
        raise PrimaryFunctionMissing("Your custom plugin does not have a primary function."
                                     "Override this method")


class ListMenu(MyListView):
    pass


class PluginDefault:
    def __init__(self, widget, widget_labels_class, name):
        self.name = name
        self.widget = widget
        if hasattr(self.widget, 'project') and hasattr(self.widget, 'plugin_position'):
            self.widget.params = self.widget.project.pipeline[self.widget.plugin_position]
        self.widget_labels = widget_labels_class

    def run(self, input_paths=None):
        return self.widget.execute_primary_function(input_paths)

    def get_input_paths(self):
        fs = self.widget.project.files
        indices = self.widget.params[self.widget_labels.video_list_indices_label]
        fs_sub_types = [f for f in fs if f['type'] in self.widget.Defaults.list_display_type]
        return [fs_sub_types[i]['path'] for i in range(len(fs_sub_types)) if i in indices]

    def check_ready_for_automation(self):
        return False

    def automation_error_message(self):
        return "Plugin " + self.name + " is not suitable for automation."
