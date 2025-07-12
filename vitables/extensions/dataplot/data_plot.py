import os.path
import logging
import tables
import numpy
from qtpy import QtCore, QtGui, QtWidgets
from qtpy.QtCore import Property
import pyqtgraph as pg
import pyqtgraph.opengl as gl

import vitables
from vitables.extensions.aboutpage import AboutPage
from vitables.h5db.leafnode import LeafNode
import matplotlib
matplotlib.use('Qt5Agg')
from vitables.extensions.dataplot.mpl_canvas import MplCanvas

__docformat__ = 'restructuredtext'
__version__ = '1.0'
ext_name = 'Data plot'
comment = ('Data plot'
           '')
default_size = QtCore.QSize(420, 420)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

translate = QtWidgets.QApplication.translate

_EXTENSIONS_FOLDER = os.path.join(os.path.dirname(__file__))

class DataPlotWidget(QtWidgets.QWidget):

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setObjectName('Data Plot')
        self.vtgui = vitables.utils.getGui()
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        # self.canvas = MplCanvas(self)
        # self.canvas.set_facecolor('#31363b')
        # self.canvas.axes.xaxis.set_tick_params(labelbottom=False, bottom=False, top=False, which='both')
        # self.canvas.axes.yaxis.set_tick_params(labelleft=False, left=False, right=False, which='both')
        # self.canvas.axes.set_xticks([])
        # self.canvas.axes.set_yticks([])
        # self.canvas.fig.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)    
        # self.canvas.mpl_connect('motion_notify_event', self.canvas_move)
        # self.verticalLayout.addWidget(self.canvas)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.verticalLayout.addWidget(self.plot_widget)
        self.view = self.plot_widget.addViewBox()
        self.view.setAspectLocked(False)
        self.img = pg.ImageItem()
        self.view.addItem(self.img)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.slider.setValue(0)        
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.slider.setTickInterval(5)        
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.verticalLayout.addWidget(self.slider)
        self.data = None
        self._transpose = True
        self._name = ''
        self.colormaps = ['viridis', 'jet', 'gray', 'hsv', 'bone', 'hot', 'cool']
        self.colormap_name = 'viridis'
        self._frame = 0
        self._autoRange = True
        self._valueRange = []

    def draw(self, image_data, **kwargs):
        self.canvas.axes.imshow(image_data, aspect='auto', interpolation = 'bilinear', **kwargs)        
        self.canvas.fig.tight_layout(pad = 0.05)
        self.canvas.fig.canvas.draw()
        #self.img.setImage(image_data)

    def canvas_move(self, event):
        ...

    def update_image(self, *kargs):
        if not self.signalsBlocked():
            value = kargs[0] if kargs else self.slider.value()
            if(len(self.data.shape) == 3) and value < self.data.shape[0]:
                data_slice = self.data[value,:]
            elif len(self.data.shape) == 2:
                data_slice = self.data[:]
            else:
                self.vtgui.logger.write(f'Error: does not support {len(self.data.shape)} dimension array')                
                return
            # apply operations to image data
            ops = []
            if numpy.iscomplexobj(data_slice):
                ops.append(numpy.abs)
            if self._transpose:
                ops.append(numpy.transpose)
            for op in ops:
                data_slice = op(data_slice)
            if self._autoRange:
                self._valueRange = [numpy.min(data_slice), numpy.max(data_slice)]
            self.draw(data_slice, cmap=self.colormap_name, vmin=self._valueRange[0], vmax=self._valueRange[1])

    def slider_value_changed(self, value):
        self.update_image(value)
        self.vtgui.updatePropertyEditor([self])

    def set_data(self, data, **kwargs):
        if 'name' in kwargs:
            self._name = kwargs['name']
        if 'cmap' in kwargs:
            cmap = kwargs['cmap']
            if cmap in self.colormap_list:
                self.colormap_name = cmap
        if 'transpose' in kwargs:
            self._transpose = kwargs['transpose']
        self.data = data
        if data is None:
            self.canvas.clear()
            self.canvas.fig.canvas.draw()
            return
        if len(data.shape) == 3 and data.shape[0] > 1:
            self.slider.setMaximum(data.shape[0] - 1)
            self.slider.setValue(0)
            self.slider.setVisible(True)
        else:
            self.slider.setVisible(False)
        self.update_image()
        self.vtgui.updatePropertyEditor([self])

    @Property(str, designable=True, user=True)
    def name(self):
        return self._name
    QtCore.Q_CLASSINFO('name', 'display=Title')

    @Property(bool, designable=True, user=True)
    def transpose(self):
        return self._transpose
    @transpose.setter
    def transpose(self, value):
        self._transpose = value
        self.update_image()
    QtCore.Q_CLASSINFO('transpose', 'display=Tranpose')

    # colormap selection mechanism
    @Property(list, designable=False, user=True)
    def colormap_list(self):
        return self.colormaps
    @Property(int, designable=True, user=True)
    def colormap_sel(self):
        return self.colormap_list.index(self.colormap_name)
    @colormap_sel.setter
    def colormap_sel(self, value):
        self.colormap_name = self.colormap_list[value]
        self.update_image()
    QtCore.Q_CLASSINFO('colormap_sel', 'display=Color Map;emulate_enums=@colormap_list')

    @Property(bool, designable=True, user=True)
    def autoRange(self):
        return self._autoRange
    @autoRange.setter
    def autoRange(self, value):
        self._autoRange = value
        self.update_image()
        self.vtgui.updatePropertyEditor([self])
    QtCore.Q_CLASSINFO('autoRange', 'display=Auto Range')

    @Property(list, designable=True, user=True)
    def valueRange(self):
        return self._valueRange
    @valueRange.setter
    def valueRange(self, value):
        self._valueRange = value
        self.update_image()
    QtCore.Q_CLASSINFO('valueRange', 'display=Range;enabled=!autoRange')

    @Property(int, designable=True, user=True)
    def frame(self):
        return self.slider.value()
    @frame.setter
    def frame(self, value):
        if value != self.slider.value():
            if value <= self.slider.maximum():
                self.slider.setValue(value)
            else:
                self.vtgui.updatePropertyEditor([self])
    QtCore.Q_CLASSINFO('frame', 'display=Frame;minimum=0')

    @Property(list, designable=True, user = True)
    def shape(self):
        return list(self.data.shape) if self.data is not None else []
    QtCore.Q_CLASSINFO('shape', 'display=Data Shape')

class DataPlotSubWindow(QtWidgets.QMdiSubWindow):
    """A widget that contains a group of Arrays.
    """
    def __init__(self, data_in, parent=None, flags=QtCore.Qt.SubWindow):
        """The class constructor.
        """
        self.vtgui = vitables.utils.getGui()
        super(DataPlotSubWindow, self).__init__(self.vtgui.workspace, flags)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.plot_widget = DataPlotWidget(self)
        self.setWidget(self.plot_widget)
        name = 'No name'
        data = None
        self.dbt_leaf = None
        if isinstance(data_in, LeafNode):
            self.dbt_leaf = data_in        
            data = data_in.node
            name = data_in.node.name
        elif isinstance(data_in, numpy.ndarray):
            self.dbt_leaf = None
            data = data_in
        if data is not None:
            self.plot_widget.set_data(data, name = name)
        self.setWindowTitle(f'Figure: {name}')

    def set_data(self, data: numpy.ndarray | tables.array.Array, **kwargs):        
        self.plot_widget.set_data(data, **kwargs)

class ExtDataPlot(QtCore.QObject):
    """The class which defines the plugin for data plot
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

        super(ExtDataPlot, self).__init__(parent)
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

        self.vtgui.add_locals({'plot_data': self.plot_data, 'figure': self.figure})

    def addEntry(self):
        """Add the `data plot..`. entry to `Dataset` menu.
        """

        self.plot_data_action = QtWidgets.QAction(
            translate('DataPlot', "Open Plot",
                      "Plot data"),
            self,
            shortcut=QtGui.QKeySequence.UnknownKey, triggered=self.plot_current_data,
            #icon=vitables.utils.getIcons()['document-export'],
            statusTip=translate(
                'DataPlot',
                "Plot data",
                "Status bar text for the Dataset -> plot data... action"))
        self.plot_data_action.setObjectName('plot_data')

        # Add the action to the Dataset menu
        vitables.utils.addToMenu(self.vtgui.dataset_menu, self.plot_data_action, False)

        # Add the action to the leaf context menu
        vitables.utils.addToLeafContextMenu(self.plot_data_action, None, False)

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

        self.plot_data_action.setEnabled(enabled)
        
    def plot_current_data(self):
        """Export a given dataset to a `CSV` file.

        This method is a slot connected to the `export` QAction. See the
        :meth:`addEntry` method for details.
        """

        # The PyTables node tied to the current leaf of the databases tree
        current = self.vtgui.dbs_tree_view.currentIndex()
        dbt_leaf = self.vtgui.dbs_tree_model.nodeFromIndex(current)
        leaf = dbt_leaf.node

        # Empty datasets aren't saved to console
        if leaf.nrows == 0:
            log.info(translate(
                'DataPlot', 'Empty dataset. Nothing to export.'))
            return

        # Scalar arrays aren't saved to console
        if leaf.shape == ():
            log.info(translate(
                'DataPlot', 'Scalar array. Nothing to export.'))
            return
        
        if len(leaf.shape) not in (2, 3):
            self.vtgui.logger.write(f'Warning: only 2D/3D data is supported for now')
            return
        
        sub_window = DataPlotSubWindow(dbt_leaf)
        sub_window.show()
        # weird bug. need to cycle the visiblity to make it work. otherwise it will not redraw
        sub_window.hide()
        sub_window.show()
        sub_window.resize(default_size)

    def plot_data(self, ndarray: numpy.ndarray = None, **kwargs):
        window = self.vtgui.workspace.activeSubWindow()
        if window and isinstance(window, DataPlotSubWindow) and not window.dbt_leaf:
            window.set_data(ndarray, **kwargs)
        else:
            self.figure().set_data(ndarray, **kwargs)

    def figure(self):
        sub_window = DataPlotSubWindow(None)
        sub_window.show()
        # weird bug. need to cycle the visiblity to make it work. otherwise it will not redraw
        sub_window.hide()
        sub_window.show()
        sub_window.resize(default_size)

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
                'comment': translate('DataPlot',
                                     """
                 <qt><p>Extension that add support to plot data <p>
                 <p></qt>
                 """,
                 'Text of an About extension message box')}
        about_page = AboutPage(desc, parent)
        return about_page