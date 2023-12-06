"""
Widgets for plotting multi-channel signals.
"""
from mimetypes import init
import signal
import numpy as np
import pyqtgraph as pg
from PyQt5.QtGui import * #QFont,
from PyQt5 import QtWidgets, QtCore, QtGui
from .assets import resources


class SignalWidget(pg.GraphicsLayoutWidget):
    """
    Scrolling oscilloscope-like widget for displaying real-time signals.

    Intended for multi-channel viewing, each channel gets its own row in the
    widget, and all channels share y-axis zoom.

    Parameters
    ----------
    channel_names : list, optional
        List of channel names.
    bg_color : pyqtgraph color, optional
        Background color. Default is None (i.e., default background color).
    y_range : tuple, optional
        Y-axis range. Default is (-1, 1).
    show_bottom : boolean or str
        Whether to show x-axis in plots. If set to ``last``, x-axis will only
        be visible in the last row.
    """

    def __init__(self, channel_names=None, bg_color=None, yrange=(-1,1),
                 show_bottom=False, xlabel=None):
        super(SignalWidget, self).__init__()

        self.plot_items = []
        self.plot_data_items = []

        self.n_channels = 0
        self.channel_names = channel_names
        self.bg_color = bg_color
        self.yrange = yrange
        self.show_bottom = show_bottom
        self.xlabel = xlabel
        

        self.setBackground(self.bg_color)

    def plot(self, y, x=None):
        """
        Adds a window of data to the widget.

        Previous windows are scrolled to the left, and the new data is added to
        the end.

        Parameters
        ----------
        y : ndarray, shape = (n_channels, n_samples)
            Window of data to add to the end of the currently-shown data.
        x : array, shape = (n_samples,), optional (default: None)
            Independent variable values that will be displayed on x axis.
        """
        
        nch, nsamp = y.shape
        if nch != self.n_channels:
            self.n_channels = nch

            if self.channel_names is None:
                self.channel_names = range(self.n_channels)

            self._update_num_channels()

        for i, pdi in enumerate(self.plot_data_items):
            if x is not None:
                pdi.setData(x, y[i])
            else:
                pdi.setData(y[i])

    def _update_num_channels(self):
        self.clear()

        self.plot_items = []
        self.plot_data_items = []
        pen = _MultiPen(self.n_channels)
        for i, name in zip(range(self.n_channels), self.channel_names):
            plot_item = self.addPlot(row=i, col=0)
            plot_data_item = plot_item.plot(pen=pen.get_pen(i), antialias=True)

            if self.show_bottom is not True:
                plot_item.showAxis('bottom', False)
            plot_item.showGrid(y=True, alpha=0.5)
            plot_item.setMouseEnabled(x=False)
            plot_item.setMenuEnabled(False)

            if self.n_channels > 1:
                label = "{}".format(name)
                plot_item.setLabels(left=label)

            #if i > 0:
                #plot_item.setYLink(self.plot_items[0])
            #plot_item.disableAutoRange(pg.ViewBox.YAxis)
            #plot_item.setYRange(*self.yrange)
            self.plot_items.append(plot_item)
            self.plot_data_items.append(plot_data_item)

        #self.plot_items[0].disableAutoRange(pg.ViewBox.YAxis)
        #self.plot_items[0].setYRange(*self.yrange)
        
        if self.show_bottom == 'last':
            self.plot_items[-1].showAxis('bottom', True)

        if self.xlabel is not None:
            self.plot_items[-1].setLabels(bottom=self.xlabel)

class _LayoutSignalWidget(QtWidgets.QWidget):
    """ 
    This contains the common methods and fields that can be used by the different layouts containing the signal widget
    """

    def enable_record_button(self):
        self.recordButton.toggle()
        self.recordButton.setText("Record Data")
        #self.recordButton.setStyleSheet("""background-color: white;""")
        self.recordButton.setEnabled(True)
        
    def record_button_clicked(self):
        self.recordButton.toggle()
        self.recordButton.setText("Recording...")
        #self.recordButton.setStyleSheet("""background-color: red;""")
        self.recordButton.setEnabled(False)
        self.start_recording()
    
    def plot(self, y, x=None) -> None:
        """
        Adds a window of data to the signal widget.

        Previous windows are scrolled to the left, and the new data is added to
        the end.

        Parameters
        ----------
        y : ndarray, shape = (n_channels, n_samples)
            Window of data to add to the end of the currently-shown data.
        x : array, shape = (n_samples,), optional (default: None)
            Independent variable values that will be displayed on x axis.
        """
        self.signalWidget.plot(y, x)
        
    def change_y(self, newYScale: int = 1000, plotIndex: int = 0):
        self.signalWidget.plot_items[0].disableAutoRange(pg.ViewBox.YAxis)
        self.signalWidget.plot_items[0].setYRange(-newYScale, newYScale)
        
    def change_x(self, newXScale : int):
        self.change_window(newXScale)
        self.xAxisChanger.setToolTip(f"time window: {self.xAxisChanger.value()} sec")
        self.label.setText(f"Time Window: {self.xAxisChanger.value()} sec")

class GridSignalWidget(_LayoutSignalWidget):
    """
    A stacked layout widget to show multiple widget types over each other, in this case both the Signal widget which plots the signal and other features which should be visible.
    
    Widgets stacked in this (starting from the bottom most widget):
    - SignalWidget
    - X axis changing?
    - Recording button and indicator

    Arguments
    ---------
    connectedMethods: a dictionary containing the methods to connect the buttons. This should contain the methods 
        - "start_recording" which is connected to the recording button (opitonal)
        - "change_window" which is connected to the x axis plot scale
    """
    def __init__(self, connectedMethods: dict, channelNames: list = ["Signal 1", "Signal 2"]):
        super(GridSignalWidget, self).__init__()
        
        self.gridLayout = QtWidgets.QGridLayout()
        self.change_window = connectedMethods["change_window"]    
        
        
        

        self.signalWidget = SignalWidget(channel_names=channelNames,
                                         show_bottom=True, xlabel= "Time (s)",
                                         yrange=(-25000, 25000), #bg_color="black"
                                            )
        sliderRange = [1,20]
        self.xAxisChanger = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        #x axis changer works in seconds 
        # if we need more range it may be worth trying to make the scale nonlinear (eg logarithmic or exponential)
        #self.xAxisChanger.setGeometry(QtCore.QRect(10,10,10,10))
        self.xAxisChanger.setStyleSheet("""background-color: transparent;""")
        

        self.setStyleSheet("""
            QSlider::groove:horizontal {
            border: 1px solid #bbb;
            background: transparent;
            height: 10px;
            border-radius: 4px;
            }

            QSlider::sub-page:horizontal {
            background: transparent;
            background: transparent;
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
            }

            QSlider::add-page:horizontal {
            background: transparent;
            border: 1px solid #777;
            height: 10px;
            border-radius: 4px;
            }

            QSlider::handle:horizontal {
            background: grey;
            border: 1px solid #777;
            width: 13px;
            margin-top: -2px;
            margin-bottom: -2px;
            border-radius: 4px;
            }

            QSlider::handle:horizontal:hover {
            background: blue;
            border: 1px solid #444;
            margin-top: -10px;
            margin-bottom: -10px;               
            border-radius: 4px;
            }

            QSlider::sub-page:horizontal:disabled {
            background: #bbb;
            border-color: #999;
            }

            QSlider::add-page:horizontal:disabled {
            background: transparent;
            border-color: #999;
            }

            QSlider::handle:horizontal:disabled {
            background: transparent;
            border: 1px solid #aaa;
            border-radius: 4px;
            }""")
        
        self.xAxisChanger.setRange(sliderRange[0],sliderRange[1])
        self.xAxisChanger.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.xAxisChanger.setTickInterval(1)
        self.xAxisChanger.setValue(5)
        self.xAxisChanger.valueChanged.connect(self.change_x)

        self.xAxisChanger.setToolTip(f"time window: {self.xAxisChanger.value()} sec")
        #set up grid layout
        
        if "start_recording" in connectedMethods:
            self.start_recording = connectedMethods["start_recording"]
            
            self.recordButton = QtWidgets.QPushButton("Record Data")
            self.recordButton.setCheckable(True)
            self.recordButton.clicked.connect(self.record_button_clicked)
            self.recordButton.setIcon(QtGui.QIcon(':/icons/recording.png'))
            self.recordButton.setToolTip("Record and save 60 sec of data")
            #self.recordButton.setStyleSheet("""background-color: white;""")
            #this still needs the button position

            self.gridLayout.addWidget(self.recordButton, 0, 0)
        
        
        # addWidget ( QWidget * widget, int fromRow, int fromColumn, int rowSpan, int columnSpan, Qt::Alignment alignment = 0 )
        self.label = QtWidgets.QLabel(f"Time Window: {self.xAxisChanger.value()} sec")
        self.label.setAlignment(QtCore.Qt.AlignHCenter)
        self.gridLayout.addWidget(self.xAxisChanger, 2, 1, 1, 6)
        self.gridLayout.addWidget(self.label, 2,0)
        self.gridLayout.addWidget(self.signalWidget, 1, 0, 1, 8)
        
        self.logo = QtWidgets.QLabel()
        self.pixmap = QPixmap(':/icons/logo.png')
        #self.scaledPixmap = self.pixmap.scaled(50, 100, QtCore.Qt.KeepAspectRatio)
        self.logo.setPixmap(self.pixmap)
        #self.logo.setScaledContents(True)
        self.gridLayout.addWidget(self.logo, 0 , 7)
        
        
        self.setLayout(self.gridLayout)

class StackedSignalWidget(_LayoutSignalWidget):
    """
    A stacked layout widget to show multiple widget types over each other, in this case both the Signal widget which plots the signal and other features which should be visible.
    
    Widgets stacked in this (starting from the bottom most widget):
    - SignalWidget
    - X axis changing?
    - Recording button and indicator

    Arguments
    ---------
    connectedMethods: a dictionary containing the methods to connect the buttons. This should contain the methods 
        - "start_recording" which is connected to the recording button (opitonal)
        - "change_window" which is connected to the x axis plot scale
    """
    def __init__(self, connectedMethods: dict, channelNames: list = ["Signal 1", "Signal 2"]):
        super(StackedSignalWidget, self).__init__()
        
        self.stackLayout = QtWidgets.QStackedLayout()
        self.stackLayout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        
        self.gridLayout = QtWidgets.QGridLayout()
            
       
        self.change_window = connectedMethods["change_window"]
        self.xAxisChanger = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        #x axis changer works in seconds 
        # if we need more range it may be worth trying to make the scale nonlinear (eg logarithmic or exponential)
        #self.xAxisChanger.setGeometry(QtCore.QRect(10,10,10,10))
        self.xAxisChanger.setStyleSheet("""background-color: transparent;""")
        self.xAxisChanger.setRange(1,60)
        #self.xAxisChanger.setTickPosition(5)
        self.xAxisChanger.valueChanged.connect(self.change_window)
        #this still needs the position

        self.signalWidget = SignalWidget(channel_names=channelNames,
                                         show_bottom=True, xlabel= "Time (s)",
                                         yrange=(-25000, 25000)
                                            )

        #set up grid layout
        self.gridLayout.addWidget(self.xAxisChanger, 2,1)
        if "start_recording" in connectedMethods:
            self.start_recording = connectedMethods["start_recording"]
            
            self.recordButton = QtWidgets.QPushButton("Record Data")
            self.recordButton.setCheckable(True)
            self.recordButton.clicked.connect(self.record_button_clicked)
            self.recordButton.setStyleSheet("""background-color: transparent;""")
            #this still needs the button position

            self.gridLayout.addWidget(self.recordButton, 0, 0)
        
        self.gridWidget = QtWidgets.QWidget()
        self.gridWidget.setLayout(self.gridLayout)
            
        #set up stacked layout
        self.stackLayout.addWidget(self.signalWidget) 
        self.stackLayout.addWidget(self.gridWidget)
        #self.stackLayout.addWidget(self.xAxisChanger)
         
        self.stackLayout.setCurrentIndex(0)
        
        self.setLayout(self.stackLayout)

class NumberedQSlider(QtWidgets.QWidget):
    """ A standard Qslider with numbers on the ticks, but this does not quite work as it should """
    
    def __init__(self, connectedMethod, sliderRange: list = [1,20]) -> None:
        super(NumberedQSlider, self).__init__()
        
        self.stackLayout = QtWidgets.QStackedLayout()
        self.stackLayout.setStackingMode(QtWidgets.QStackedLayout.StackAll)
        
        self.xAxisChanger = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        #x axis changer works in seconds 
        # if we need more range it may be worth trying to make the scale nonlinear (eg logarithmic or exponential)
        #self.xAxisChanger.setGeometry(QtCore.QRect(10,10,10,10))
        self.xAxisChanger.setStyleSheet("""background-color: transparent;""")

        self.xAxisChanger.setRange(sliderRange[0],sliderRange[1])
        self.xAxisChanger.setTickPosition(QtWidgets.QSlider.TickPosition.TicksBelow)
        self.xAxisChanger.setTickInterval(1)
        self.xAxisChanger.setValue(5)
        self.xAxisChanger.valueChanged.connect(connectedMethod)

        self.xAxisChanger.setToolTip(f"time window: {self.xAxisChanger.value()} sec")
        
        #labels to show: 1, 5, 10, 15, 20 -> lowest, 25%, 50%, 75%, 100%
        self.gridLayout = QtWidgets.QGridLayout()
        
        self.label = {}
        self.label["0"] = QtWidgets.QLabel(str(sliderRange[0]))
        self.gridLayout.addWidget(self.label["0"], 1, 0)
        
        self.label["1"] = QtWidgets.QLabel(str(sliderRange[1]))
        self.label["1"].setAlignment(QtCore.Qt.AlignRight)
        self.gridLayout.addWidget(self.label["0"], 1, 1)
        
        """
        for number in range(1, sliderRange[1]+1):
            self.label[str(number)] = QtWidgets.QLabel(str(number)) #str(int(sliderRange[1]*fraction))
            if number > 2*sliderRange[1]/3:
                self.label[str(number)].setAlignment(QtCore.Qt.AlignHCenter)
            elif number > sliderRange[1]/3:
                self.label[str(number)].setAlignment(QtCore.Qt.AlignRight)
            self.gridLayout.addWidget(self.label[str(number)], 1, number)
            """
        
        gridWidget = QtWidgets.QWidget()
        gridWidget.setLayout(self.gridLayout)
        #assemble stack layout
        self.stackLayout.addWidget(gridWidget)
        self.stackLayout.addWidget(self.xAxisChanger)

        self.setLayout(self.stackLayout)
        
    def value(self):
        return self.xAxisChanger.value()
    
    def setToolTip(self, string: str):
        self.xAxisChanger.setToolTip(string)

class BarWidget(pg.PlotWidget):
    """
    Bar graph widget for displaying real-time signals.

    Intended for multi-group viewing, each group can optionally use a
    different color.

    Parameters
    ----------
    channel_names : list, optional
        List of channel names.
    group_colors : list, optional
        List of pyqtgraph colors. One for each group.
    bg_color : pyqtgraph color, optional
        Background color. Default is None (i.e., default background color).
    y_range : tuple, optional
        Y-axis range. Default is (-1, 1).
    font_size : int, optional
        Axes font size. Default is 12.
    """

    def __init__(self, channel_names=None, group_colors=None, bg_color=None,
                 yrange=(-1,1), font_size=12):
        super(BarWidget, self).__init__()

        self.channel_names = channel_names
        self.group_colors = group_colors
        self.bg_color = bg_color
        self.yrange = yrange
        self.font_size = font_size

        self.plot_items = None
        self.plot_data_items = None

        self.n_channels = 0
        self.n_groups = 0

        self.showGrid(y=True, alpha=0.5)
        self.setBackground(self.bg_color)
        self.setMouseEnabled(x=False)
        self.setMenuEnabled(False)

        font = QFont()
        font.setPixelSize(self.font_size)
        self.getAxis('bottom').tickFont = font
        self.getAxis('left').tickFont = font

    def plot(self, data):
        """
        Plots a data sample.

        Parameters
        ----------
        data : ndarray, shape = (n_channels, n_groups) or (n_channels,)
            Data sample to show on the graph.
        """
        # Handle both cases: (n_channels, n_groups) and (n_channels,)
        data = np.reshape(data, (data.shape[0], -1))
        nch, ngr = data.shape

        if nch != self.n_channels or ngr != self.n_groups:
            self.n_channels = nch
            self.n_groups = ngr

            if self.channel_names is None:
                self.channel_names = range(self.n_channels)

            if self.group_colors is None:
                self.group_colors = [0.5] * self.n_groups  # default gray

            self._update_num_channels()

        for i, pdi in enumerate(self.plot_items):
            pdi.setOpts(height=data[:, i])

    def _update_num_channels(self):
        self.clear()

        self.plot_items = []
        self.plot_data_items = []
        for i, color in zip(range(self.n_groups), self.group_colors):
            width = 1./(self.n_groups+1)
            x = np.arange(self.n_channels) + (i - self.n_groups/2 + 0.5)*width
            plot_item = pg.BarGraphItem(x=x, height=0, width=width,
                                        brush=color, pen='k')

            self.plot_items.append(plot_item)
            self.addItem(plot_item)

        self.disableAutoRange(pg.ViewBox.YAxis)
        self.setYRange(*self.yrange)

        ax = self.getAxis('bottom')
        x_ticks = [(i, name) for i, name in enumerate(self.channel_names)]
        ax.setTicks([x_ticks])


class PolarWidget(pg.GraphicsLayoutWidget):
    """
    Polar graph widget for displaying real-time polar data.

    Parameters
    ----------
    max_value : float, optional
        Expected maximum value of the data. Default is 1.
    fill : boolean, optional
        If True, fill the space between the origin and the plot. Default is
        True.
    color : pyqtgraph color, optional
        Line color. Default is 'k'.
    width : float, optional
        Line width. Default is 3.
    circle_color : pyqtgraph color, optional
        Circe color. Default is 'k'.
    circle_width : float, optional
        Circle width. Default is 0.2.
    n_circles : int, optional
        Number of circles to draw. Default is 30.
    bg_color : pyqtgraph color, optional
        Background color. Default is None (i.e., default background color).
    """

    def __init__(self, max_value=1., fill=True, color='k', width=3.,
                 circle_color='k', circle_width=0.2, n_circles=30,
                 bg_color=None):
        super(PolarWidget, self).__init__()

        self.max_value = max_value
        self.fill = fill
        self.color = color
        self.width = width
        self.circle_color = circle_color
        self.circle_width = circle_width
        self.n_circles = n_circles
        self.bg_color = bg_color

        self.n_channels = 0

        self.plot_item = None
        self.plot_data_item = None

        self.setBackground(self.bg_color)

    def plot(self, data, color=None):
        """
        Plots a data sample.

        Parameters
        ----------
        data : ndarray, shape = (n_channels,) or (n_channels, 1)
            Data sample to show on the graph.
        """
        # Handle both cases: (n_channels,) and (n_channels, 1)
        data = np.reshape(data, (-1,))
        nch = data.size

        if nch != self.n_channels:
            self.n_channels = nch

            self._update_num_channels()

        if color is not None:
            self.plot_data_item.setPen(
                pg.mkPen(pg.mkColor(color), width=self.width))
            self.plot_data_item.setBrush(pg.mkBrush(pg.mkColor(color)))

        x, y = self._transform_data(data)
        self.plot_data_item.setData(x, y)


    def _update_num_channels(self):
        self.clear()

        self.plot_item = self.addPlot(row=0, col=0)
        self.plot_data_item = pg.PlotCurveItem(
            pen=pg.mkPen(self.color, width=self.width), antialias=True)
        if self.fill:
            self.plot_data_item.setFillLevel(1)
            fill_color = self.color
            self.plot_data_item.setBrush(pg.mkBrush(pg.mkColor(fill_color)))

        self.plot_item.addItem(self.plot_data_item)

        # Add polar grid lines
        self.plot_item.addLine(x=0, pen=pg.mkPen(
            color=self.circle_color, width=self.circle_width))
        self.plot_item.addLine(y=0, pen=pg.mkPen(
            color=self.circle_color, width=self.circle_width))

        for r in np.linspace(0., 3 * self.max_value, self.n_circles):
            circle = pg.QtGui.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(
                color=self.circle_color, width=self.circle_width))
            self.plot_item.addItem(circle)

        self.theta = np.linspace(0, 2 * np.pi, self.n_channels + 1)

        self.plot_item.showAxis('bottom', False)
        self.plot_item.showAxis('left', False)
        self.plot_item.showGrid(y=False, x=False)
        self.plot_item.setMouseEnabled(x=False)
        self.plot_item.setMenuEnabled(False)

        self.plot_item.setYRange(-self.max_value / 2, self.max_value / 2)
        self.plot_item.setXRange(-self.max_value / 2, self.max_value / 2)
        self.plot_item.setAspectLocked()

    def _transform_data(self, data):
        "Performs polar transformation. "
        # Connect end to start to make a continuous plot
        data = np.hstack((data, data[0]))

        x = data * np.cos(self.theta)
        y = data * np.sin(self.theta)

        return (x, y)


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
