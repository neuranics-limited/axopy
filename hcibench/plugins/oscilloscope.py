import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets

from hcibench import pipeline
from hcibench.base import Plugin


class OscilloscopeWidget(pg.GraphicsLayoutWidget):
    """
    Scrolling oscilloscope-like widget for displaying real-time signals.

    Intended for multi-channel viewing, each channel gets its own row in the
    widget, and all channels share y-axis zoom.
    """

    def __init__(self, parent=None):
        super(OscilloscopeWidget, self).__init__(parent=parent)

        self.plot_items = []
        self.plot_data_items = []

        self.n_channels = 0

        self.setBackground(None)

    def add_window(self, data):
        """
        Adds a window of data to the widget.

        Previous windows are scrolled to the left, and the new data is added to
        the end.

        Parameters
        ----------
        data : ndarray, shape = (n_channels, n_samples)
            Window of data to add to the end of the currently-shown data.
        """
        nch, nsamp = data.shape
        if nch != self.n_channels:
            self.n_channels = nch
            self._update_num_channels()

        for i, pdi in enumerate(self.plot_data_items):
            pdi.setData(data[i])

    def _update_num_channels(self):
        self.clear()

        self.plot_items = []
        self.plot_data_items = []
        pen = _MultiPen(self.n_channels)
        for i in range(self.n_channels):
            plot_item = self.addPlot(row=i, col=0)
            plot_data_item = plot_item.plot(pen=pen.get_pen(i), antialias=True)

            plot_item.showAxis('bottom', False)
            plot_item.showGrid(y=True, alpha=0.5)
            plot_item.setMouseEnabled(x=False)

            if self.n_channels > 1:
                label = "ch {}".format(i)
                plot_item.setLabels(left=label)

            if i > 0:
                plot_item.setYLink(self.plot_items[0])

            self.plot_items.append(plot_item)
            self.plot_data_items.append(plot_data_item)

        self.plot_items[0].disableAutoRange(pg.ViewBox.YAxis)
        self.plot_items[0].setYRange(-1, 1)


class Oscilloscope(Plugin):

    def __init__(self, name=None):
        super(Oscilloscope, self).__init__(name=name)

        self.widget = OscilloscopeWidget()
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.widget)
        self.setLayout(layout)

    def setup_recorder(self):
        # just want raw data
        self.recorder.remove_pipeline()
        self.recorder.updated.connect(self.on_recorder_update)

    def dispose_recorder(self):
        self.recorder.updated.connect(self.on_recorder_update)

    def on_recorder_update(self, data):
        self.widget.add_window(data)


class _MultiPen(object):

    MIN_HUE = 160
    HUE_INC = 20
    VAL = 200

    def __init__(self, n_colors):
        self.n_colors = n_colors
        self.max_hue = self.MIN_HUE + n_colors*self.HUE_INC

    def get_pen(self, index):
        return pg.intColor(
            index, hues=self.n_colors,
            minHue=self.MIN_HUE, maxHue=self.max_hue,
            minValue=self.VAL, maxValue=self.VAL)