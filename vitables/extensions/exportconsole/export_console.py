import os.path
import logging
import tables
import numpy
from qtpy import QtCore, QtGui, QtWidgets

import vitables
from vitables.extensions.aboutpage import AboutPage
from vitables.vtutils.dbdoc_helper import importData

__docformat__ = 'restructuredtext'
__version__ = '1.0'
ext_name = 'Export to script console'
comment = ('Export array to script console '
           '')

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

translate = QtWidgets.QApplication.translate

_EXTENSIONS_FOLDER = os.path.join(os.path.dirname(__file__))

class ExtExportConsole(QtCore.QObject):
    """The class which defines the plugin for export to console
    """

    UID = __name__
    NAME = ext_name
    COMMENT = comment

    def __init__(self, parent=None):
        """Class constructor.

        Dynamically finds new instances of
        :meth:`vitables.vttables.leaf_model.LeafModel` and customizes them if
        they are arrays that can be grouped in a unique view.
        """

        super(ExtExportConsole, self).__init__(parent)
        self.vtapp = vitables.utils.getVTApp()
        self.vtgui = self.vtapp.gui
        # An specialized object will deal with the Node menu changes
        #self.menu_updater = MenuUpdater()
        self.addEntry()

        # Connect convenience signal defined in the vtapp module to slot
        #self.vtapp.leaf_model_created.connect(self.customizeView)
        # Connect signals to slots
        self.vtgui.dataset_menu.aboutToShow.connect(self.updateDatasetMenu)
        self.vtgui.leaf_node_cm.aboutToShow.connect(self.updateDatasetMenu)
        
        self.vtgui.add_locals({'import_data': self.import_data})

    def addEntry(self):
        """Add the `Export to Console..`. entry to `Dataset` menu.
        """

        self.export_console_action = QtWidgets.QAction(
            translate('ExportToConsole', "Export numpy array to Console...",
                      "Save dataset to script console"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey, triggered=lambda: self.export(),
            #icon=vitables.utils.getIcons()['document-export'],
            statusTip=translate(
                'ExportToConsole',
                "Save the dataset to script console",
                "Status bar text for the Dataset -> Export to console... action"))
        self.export_console_action.setObjectName('export_console')

        self.export_ref_console_action = QtWidgets.QAction(
            translate('ExportToConsole', "Export to Console...",
                      "Save reference dataset to script console"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey, triggered=lambda: self.export(False),
            #icon=vitables.utils.getIcons()['document-export'],
            statusTip=translate(
                'ExportToConsole',
                "Save the reference dataset to script console",
                "Status bar text for the Dataset -> Export to console... action"))
        self.export_console_action.setObjectName('export_ref_console')

        # Add the action to the Dataset menu
        vitables.utils.addToMenu(self.vtgui.dataset_menu, self.export_console_action, False)
        vitables.utils.addToMenu(self.vtgui.dataset_menu, self.export_ref_console_action, False)

        # Add the action to the leaf context menu
        vitables.utils.addToLeafContextMenu(self.export_console_action, self.updateDatasetMenu, False)
        vitables.utils.addToLeafContextMenu(self.export_ref_console_action, self.updateDatasetMenu, False)
        vitables.utils.addToGroupContextMenu(self.export_ref_console_action, self.updateDatasetMenu)
        vitables.utils.addToRootGroupContextMenu(self.export_ref_console_action, self.updateDatasetMenu)
        
    def updateDatasetMenu(self):
        """Update the `export` QAction when the Dataset menu is pulled down.

        This method is a slot. See class ctor for details.
        """

        enabled = True
        current = self.vtgui.dbs_tree_view.currentIndex()
        if current:
            leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current)
            if leaf.node_kind in ('group', 'root group'):
                enabled = False

        self.export_console_action.setEnabled(enabled)
        group_enabled = leaf.node._v_file.filename != self.vtgui.dbs_tree_model.tmp_filepath
        self.export_ref_console_action.setEnabled(group_enabled)
       
    def export(self, export_conv = True):
        """Export a given dataset to a `CSV` file.

        This method is a slot connected to the `export` QAction. See the
        :meth:`addEntry` method for details.
        """

        # The PyTables node tied to the current leaf of the databases tree
        current = self.vtgui.dbs_tree_view.currentIndex()
        leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current).node
        name = ''
        if not isinstance(leaf, tables.group.Group):
            # Empty datasets aren't saved to console
            if leaf.nrows == 0:
                log.info(translate(
                    'ExportToConsole', 'Empty dataset. Nothing to export.'))
                return

            # Scalar arrays aren't saved to console
            if leaf.shape == ():
                log.info(translate(
                    'ExportToConsole', 'Scalar array. Nothing to export.'))
                return
            
            if export_conv:
                match(leaf):
                    case tables.array.Array():
                        self.vtgui.add_locals({leaf.name + '_nd': leaf.read()})
                        self.vtgui.logger.write(f'Converted data exported to script console. name: {leaf.name}->{leaf.name}_nd')
                    case _:
                        self.vtgui.logger.write(f'Warning: not a supported conversion type ({type(leaf)}). Skip data conversion')
            self.vtgui.add_locals({leaf.name: leaf})
            name = leaf.name
        else:
            name = leaf._v_name if not isinstance(leaf, tables.group.RootGroup) else 'root'
            self.vtgui.add_locals({name: leaf})                
        self.vtgui.logger.write(f'Reference object exported to script console. name: {name}')

    def import_data(self, file_path: str, name: str, data: numpy.ndarray):
        dbt_model = self.vtgui.dbs_tree_model
        dbt_view = self.vtgui.dbs_tree_view
        importData(file_path, dbt_view, dbt_model, name, data)

    def helpAbout(self, parent):
        """Full description of the plugin.

        This is a convenience method which works as expected by
        :meth:preferences.preferences.Preferences.aboutPluginPage i.e.
        build a page which contains the full description of the plugin
        and, optionally, allows for its configuration.

        :Parameter about_page: the container widget for the page
        """
        # Extension full description
        desc = {'version': __version__,
                'module_name': os.path.join(os.path.basename(__file__)),
                'folder': os.path.join(os.path.dirname(__file__)),
                'author': 'Dalong Liu <liudalong0200@gmail.com>',
                'comment': translate('ExportToConsole',
                                     """
                 <qt><p>Extension that add support to export array to script console <p>
                 <p></qt>
                 """,
                 'Text of an About extension message box')}
        about_page = AboutPage(desc, parent)
        return about_page