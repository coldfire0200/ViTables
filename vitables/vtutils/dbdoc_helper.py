import os
import logging
import vitables
import numpy
import tables
from qtpy import QtWidgets, QtCore
log = logging.getLogger(__name__)

translate = QtWidgets.QApplication.translate

def isValidFilepath(filepath):
    """Check the filepath of the destination file.

    :Parameter filepath: the filepath where the imported dataset will live
    """
    valid = True
    if os.path.exists(filepath):
        log.error(translate(
            'ImportCSV',
            'CSV import failed because destination file already exists.',
            'A file creation error'))
        valid = False

    elif os.path.isdir(filepath):
        log.error(translate(
            'ImportCSV',
            'CSV import failed because destination container is a directory.',
            'A file creation error'))
        valid = False

    return valid

def findNodeIndex(dbt_model, root_index: QtCore.QModelIndex, target_node: tables.node.Node):
    if not root_index.isValid():
        return None
    node = dbt_model.nodeFromIndex(root_index).node
    if node is target_node:
        return root_index
    for row in range(dbt_model.rowCount(root_index)):
        child_index = dbt_model.index(row, 0, root_index)
        result = findNodeIndex(dbt_model, child_index, target_node)
        if result is not None:
            return result
    return None

def updateTree(dbt_view, dbt_model, filepath, group_node = None):
    """Update the databases tree once the `CSV` file has been imported.

    When the destination h5 file is created and added to the databases tree
    it has no nodes. Once the `CSV` file has been imported into a
    `PyTables` container we update the representation of the h5 file in the
    tree so that users can see that the file has a leaf. Eventually, the
    root node of the imported file is selected so that users can locate it
    immediately.

    :Parameter filepath: the filepath of the destination h5 file
    """
    for row, child in enumerate(dbt_model.root.children):
        if child.filepath == filepath:
            index = dbt_model.index(row, 0, QtCore.QModelIndex())
            if group_node:
                index = findNodeIndex(dbt_model, index, group_node)
                if index is None:
                    return
            dbt_model.lazyAddChildren(index)
            dbt_view.setCurrentIndex(index)

def createDestFile(dbt_model, filepath):
    """Create the `PyTables` file where the `CSV` file will be imported.

    :Parameter filepath: the `PyTables` file filepath
    """

    dbdoc = None
    try:
        dirname, filename = os.path.split(filepath)
        root = os.path.splitext(filename)[0]
        dest_filepath = vitables.utils.forwardPath(os.path.join(dirname,
                                                                f'{root}.h5'))
        if isValidFilepath(dest_filepath):
            dbdoc = dbt_model.createDBDoc(dest_filepath)
    except:
        log.error(
            translate('ImportCSV', 'Import failed because destination '
                        'file cannot be created.',
                        'A file creation error'))
        vitables.utils.formatExceptionInfo()

    return dbdoc

def importData(filepath: str, dbt_view, dbt_model, array_name: str, data: numpy.ndarray):
    # Import the data
    try:
        QtWidgets.QApplication.processEvents()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # The dtypes are determined by the contents of each column
        # Multidimensional columns will have string datatype
    except TypeError:
        data = None
        dbdoc = None
        log.error("Import type error")
    else:
        try:
            # Create the array
            dbdoc = createDestFile(dbt_model, filepath)
            if dbdoc is None:
                return
            title = f'Imported from file {os.path.basename(filepath)}'
            dbdoc.h5file.create_array('/', array_name, data, title=title)
            dbdoc.h5file.flush()
            updateTree(dbt_view, dbt_model, dbdoc.filepath)
        except TypeError:
            log.error("Import type error")
        except tables.NodeError:
            vitables.utils.formatExceptionInfo()
    finally:
        del data
        QtWidgets.QApplication.restoreOverrideCursor()