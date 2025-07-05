from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.pyplot import Figure

class MplCanvas(FigureCanvas):

    def __init__(self, parent = None):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)
        self.axes.set_xlabel('', color='#e0e0e0')
        self.axes.set_ylabel('', color='#e0e0e0')
        self.axes.set_facecolor('#31363b')
        self.axes.tick_params(colors='#d0d0d0')
        for spine in self.axes.spines.values():
            spine.set_edgecolor('#a0a0a0')
        self.axes.set_aspect('auto')

    def set_facecolor(self, color):
        self.fig.patch.set_facecolor(color)

    def clear(self):
        self.axes.cla()