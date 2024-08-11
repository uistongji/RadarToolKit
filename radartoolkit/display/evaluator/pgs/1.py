class PgImagePlot2d(AbstractInspector):
    """ Draws two image plots of two-dimensional arrays (slices) side by side.

        Plotting is done with the PyQtGraph package. See www.pyqtgraph.org.
    """

    def __init__(self, collector, parent=None):
        """ Constructor. See AbstractInspector constructor for parameters.
        """
        super(PgImagePlot2d, self).__init__(collector, parent=parent)

        # Ensure that only a white background is visible when self.graphicsLayoutWidget is hidden.
        self.contentsWidget.setStyleSheet('background: white;')

        # Initialize sliced arrays for the two images.
        self.slicedArray1 = None
        self.slicedArray2 = None

        # Initialize title labels for both plots
        self.titleLabel1 = pg.LabelItem('Title 1')
        self.titleLabel2 = pg.LabelItem('Title 2')

        # Initialize the image plot items
        self.imagePlotItem1 = RTKPgPlotItem()
        self.imagePlotItem2 = RTKPgPlotItem()

        self.viewBox1 = self.imagePlotItem1.getViewBox()
        self.viewBox2 = self.imagePlotItem2.getViewBox()

        # Initialize the ImageItems
        self.imageItem1 = pg.ImageItem()
        self.imageItem2 = pg.ImageItem()

        self.imageItem1.setPos(-0.5, -0.5)
        self.imageItem2.setPos(-0.5, -0.5)

        self.imagePlotItem1.addItem(self.imageItem1)
        self.imagePlotItem2.addItem(self.imageItem2)

        # Initialize color legends for both images
        self.colorLegendItem1 = RTKColorLegendItem(self.imageItem1)
        self.colorLegendItem2 = RTKColorLegendItem(self.imageItem2)

        # Cross plots for both images
        self.crossPlotRow1 = None
        self.crossPlotCol1 = None
        self.crossPlotRow2 = None
        self.crossPlotCol2 = None

        self.horCrossPlotItem1 = RTKPgPlotItem()
        self.verCrossPlotItem1 = RTKPgPlotItem()
        self.horCrossPlotItem2 = RTKPgPlotItem()
        self.verCrossPlotItem2 = RTKPgPlotItem()

        self.horCrossPlotItem1.setXLink(self.imagePlotItem1)
        self.verCrossPlotItem1.setYLink(self.imagePlotItem1)
        self.horCrossPlotItem2.setXLink(self.imagePlotItem2)
        self.verCrossPlotItem2.setYLink(self.imagePlotItem2)

        # Create crosshairs for both plots
        self._createCrosshairs()

        # Layout
        self.horPlotAdded1 = False
        self.verPlotAdded1 = False
        self.horPlotAdded2 = False
        self.verPlotAdded2 = False

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.contentsLayout.addWidget(self.graphicsLayoutWidget)

        # Add items to layout
        self._setupLayout()

        # Configuration tree
        self._config = PgImagePlot2dCti(pgImagePlot2d=self, nodeName='2D image plot')

        # Connect signals: re-implement the mouseMoved event for the crosshair
        self.imagePlotItem1.scene().sigMouseMoved.connect(lambda pos: self.mouseMoved(pos, 1))
        self.imagePlotItem2.scene().sigMouseMoved.connect(lambda pos: self.mouseMoved(pos, 2))

    def _createCrosshairs(self):
        """ Create crosshairs for both image plots. """
        self.crossPen = pg.mkPen("#BFBFBF")
        self.crossShadowPen = pg.mkPen([0, 0, 0, 100], width=3)

        # Crosshairs for the first plot
        self.crossLineHorShadow1 = pg.InfiniteLine(angle=0, movable=False, pen=self.crossShadowPen)
        self.crossLineVerShadow1 = pg.InfiniteLine(angle=90, movable=False, pen=self.crossShadowPen)
        self.crossLineHorizontal1 = pg.InfiniteLine(angle=0, movable=False, pen=self.crossPen)
        self.crossLineVertical1 = pg.InfiniteLine(angle=90, movable=False, pen=self.crossPen)

        self.imagePlotItem1.addItem(self.crossLineVerShadow1, ignoreBounds=True)
        self.imagePlotItem1.addItem(self.crossLineHorShadow1, ignoreBounds=True)
        self.imagePlotItem1.addItem(self.crossLineVertical1, ignoreBounds=True)
        self.imagePlotItem1.addItem(self.crossLineHorizontal1, ignoreBounds=True)

        # Crosshairs for the second plot
        self.crossLineHorShadow2 = pg.InfiniteLine(angle=0, movable=False, pen=self.crossShadowPen)
        self.crossLineVerShadow2 = pg.InfiniteLine(angle=90, movable=False, pen=self.crossShadowPen)
        self.crossLineHorizontal2 = pg.InfiniteLine(angle=0, movable=False, pen=self.crossPen)
        self.crossLineVertical2 = pg.InfiniteLine(angle=90, movable=False, pen=self.crossPen)

        self.imagePlotItem2.addItem(self.crossLineVerShadow2, ignoreBounds=True)
        self.imagePlotItem2.addItem(self.crossLineHorShadow2, ignoreBounds=True)
        self.imagePlotItem2.addItem(self.crossLineVertical2, ignoreBounds=True)
        self.imagePlotItem2.addItem(self.crossLineHorizontal2, ignoreBounds=True)

    def _setupLayout(self):
        """ Setup the layout to hold two image plots and associated widgets. """
        self.graphicsLayoutWidget.addItem(self.titleLabel1, ROW_TITLE, COL_TITLE, colspan=3)
        self.graphicsLayoutWidget.addItem(self.colorLegendItem1, ROW_COLOR, COL_COLOR, rowspan=2)
        self.graphicsLayoutWidget.addItem(self.imagePlotItem1, ROW_IMAGE, COL_IMAGE)

        self.graphicsLayoutWidget.addItem(self.titleLabel2, ROW_TITLE, COL_TITLE+4, colspan=3)
        self.graphicsLayoutWidget.addItem(self.colorLegendItem2, ROW_COLOR, COL_COLOR+4, rowspan=2)
        self.graphicsLayoutWidget.addItem(self.imagePlotItem2, ROW_IMAGE, COL_IMAGE+4)

        self.graphicsLayoutWidget.addItem(self.probeLabel1, ROW_PROBE, COL_PROBE, colspan=3)
        self.graphicsLayoutWidget.addItem(self.probeLabel2, ROW_PROBE, COL_PROBE+4, colspan=3)

        gridLayout = self.graphicsLayoutWidget.ci.layout # A QGraphicsGridLayout
        gridLayout.setHorizontalSpacing(10)
        gridLayout.setVerticalSpacing(10)

        gridLayout.setRowStretchFactor(ROW_HOR_LINE, 1)
        gridLayout.setRowStretchFactor(ROW_IMAGE, 2)
        gridLayout.setColumnStretchFactor(COL_IMAGE, 2)
        gridLayout.setColumnStretchFactor(COL_VER_LINE, 1)

    def _drawContents(self, reason=None, initiator=None):
        """ 
        Draws the plot contents from the sliced arrays of the collected repo tree item.
        """

        print(f"reason: {reason}, initiator: {initiator}")
        if self._resetRequired(reason, initiator):
            self.resetConfig()

        # Prepare the sliced arrays
        self.slicedArray1 = self.collector.getSlicedArray(index=1)
        self.slicedArray2 = self.collector.getSlicedArray(index=2)

        if self.slicedArray1 is None or self.slicedArray2 is None:
            self._clearContents()
            raise InvalidDataError("One of the sliced arrays is None.")

        self._updateImage(self.imageItem1, self.slicedArray1)
        self._updateImage(self.imageItem2, self.slicedArray2)

        self.titleLabel1.setText(self.configValue('title').format(**self.collector.rtiInfo1))
        self.titleLabel2.setText(self.configValue('title').format(**self.collector.rtiInfo2))

    def _updateImage(self, imageItem, slicedArray):
        """ Update the given ImageItem with the given sliced array. """
        imageArray = replaceMaskedValueWithFloat(slicedArray.data, slicedArray.mask, np.nan, copyOnReplace=True)
        imageArray = replaceMaskedValueWithFloat(imageArray, np.isinf(slicedArray.data), np.nan, copyOnReplace=True)
        imageArray = imageArray.transpose()

        imageItem.setImage(imageArray, autoLevels=False)

    @QtSlot(object)
    def mouseMoved(self, viewPos, plotIndex):
        """ Updates the probe text and crosshairs with the values under the cursor for the selected plot. """
        try:
            check_class(viewPos, QtCore.QPointF)

            if plotIndex == 1:
                self._updateCrosshairs(viewPos, self.imageItem1, self.viewBox1, self.crossLineHorizontal1, self.crossLineVertical1)
            else:
                self._updateCrosshairs(viewPos, self.imageItem2, self.viewBox2, self.crossLineHorizontal2, self.crossLineVertical2)

        except Exception as ex:
            logger.exception(ex)

    def _updateCrosshairs(self, viewPos, imageItem, viewBox, crossLineHorizontal, crossLineVertical):
        """ Updates the crosshairs for the selected plot based on cursor position. """
        if imageItem.image is not None and viewBox.sceneBoundingRect().contains(viewPos):
            scenePos = viewBox.mapSceneToView(viewPos)
            row, col = round(scenePos.y()), round(scenePos.x())
            if (0 <= row < imageItem.image.shape[0]) and (0 <= col < imageItem.image.shape[1]):
                viewBox.setCursor(QtCore.Qt.CrossCursor)

                crossLineHorizontal.setPos(row)
                crossLineVertical.setPos(col)

                crossLineHorizontal.setVisible(True)
                crossLineVertical.setVisible(True)
        else:
            crossLineHorizontal.setVisible(False)
            crossLineVertical.setVisible(False)

    def _clearContents(self):
        """ Clears the contents when no valid data is available """
        logger.debug("Clearing inspector contents")

        self.slicedArray1 = None
        self.slicedArray2 = None
        self.imageItem1.clear()
        self.imageItem2.clear()

        self.titleLabel1.setText('')
        self.titleLabel2.setText('')

        self.crossLineHorizontal1.setVisible(False)
        self.crossLineVertical1.setVisible(False)
        self.crossLineHorizontal2.setVisible(False)
        self.crossLineVertical2.setVisible(False)

        self.horCrossPlotItem1.clear()
        self.verCrossPlotItem1.clear()
        self.horCrossPlotItem2.clear()
        self.verCrossPlotItem2.clear()

        self.graphicsLayoutWidget.show()

    def finalize(self):
        """ Is called before destruction. Can be used to clean-up resources. """
        logger.debug("Finalizing: {}".format(self))
        self.colorLegendItem1.finalize()
        self.colorLegendItem2.finalize()

        self.imagePlotItem1.scene().sigMouseMoved.disconnect()
        self.imagePlotItem2.scene().sigMouseMoved.disconnect()

        self.imagePlotItem1.close()
        self.imagePlotItem2.close()
        self.graphicsLayoutWidget.close()



from PyQt5 import QtWidgets, QtGui
import pyqtgraph as pg

class BasePickItem(object):
    def __init__(self, position, dct={}):
        self._position = position
        self._data = dct
        self.status = "Status message"

        # setup the color picker and checkBox
        self._viewBtn = QtWidgets.QRadioButton()
        self._viewBtn.toggled.connect(self.contentsChanged)

        self._checkBox = QtWidgets.QCheckBox()
        self._checkBox.stateChanged.connect(self.contentsChanged)

        self._colorBtn = pg.ColorButton(color=self.color)
        self._colorBtn.setFlat(True)
        self._colorBtn.sigColorChanged.connect(self.contentsChanged)

        self._msgLabel = QtWidgets.QLabel("")
        self._msgLabel.setText(self._data['nodeName'])

        self._statusLabel = QtWidgets.QLabel("")
        self._statusLabel.setText(self.status)
        self._statusLabel.setStyleSheet("font-style: italic; color: gray;")

        # setup the layout for the widget
        self._widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(self._widget)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 0, 10, 0)  # 设置右边距

        layout.addWidget(self._viewBtn)
        layout.addWidget(self._checkBox)
        layout.addWidget(self._colorBtn)
        layout.addWidget(self._msgLabel)
        layout.addStretch(2)
        
        spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        layout.addItem(spacer)
        
        layout.addWidget(self._statusLabel)

    def contentsChanged(self, state):
        """ emits signal whenever contents changed. """
        self._data['color'] = self._colorBtn.color()
        print(f"Contents changed: {state}")

    @property
    def color(self):
        return self._data.get('color', QtGui.QColor(255, 160, 122))  # 默认颜色

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(window)
    
    item = BasePickItem(0, {'nodeName': 'Node 1'})
    layout.addWidget(item._widget)
    
    window.setLayout(layout)
    window.setWindowTitle("Example")
    window.resize(600, 100)
    window.show()
    sys.exit(app.exec_())




"""
This example demonstrates plotting with color gradients.
It also shows multiple plots with timed rolling updates
"""

import time

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, mkQApp


class DataSource(object):
    """ source of buffered demonstration data """
    def __init__(self, sample_rate=200., signal_period=0.55, negative_period=None, max_length=300):
        """ prepare, but don't start yet """
        self.rate = sample_rate
        self.period = signal_period
        self.neg_period = negative_period
        self.start_time = 0.
        self.sample_idx = 0 # number of next sample to be taken
        
    def start(self, timestamp):
        """ start acquiring simulated data """
        self.start_time = timestamp
        self.sample_idx = 0
        
    def get_data(self, timestamp, max_length=6000):
        """ return all data acquired since last get_data call """        
        next_idx = int( (timestamp - self.start_time) * self.rate )
        if next_idx - self.sample_idx > max_length:
            self.sample_idx = next_idx - max_length # catch up if needed
        # create some mildly intersting data:
        sample_phases = np.arange( self.sample_idx, next_idx, dtype=np.float64 )
        self.sample_idx = next_idx

        sample_phase_pos = sample_phases / (self.period*self.rate)
        sample_phase_pos %= 1.0
        if self.neg_period is None:
            return sample_phase_pos**4
        sample_phase_neg = sample_phases / (self.neg_period*self.rate)
        sample_phase_neg %= 1.0
        return sample_phase_pos**4 - sample_phase_neg**4

class MainWindow(pg.GraphicsLayoutWidget):
    """ example application main window """
    def __init__(self):
        super().__init__()
        self.setWindowTitle('pyqtgraph example: gradient plots')
        self.resize(800,800)
        self.show()
        
        layout = self # we are using a GraphicsLayoutWidget as main window for convenience
        cm = pg.colormap.get('CET-L17')
        cm.reverse()
        pen0 = cm.getPen( span=(0.0,1.0), width=5 )
        curve0 = pg.PlotDataItem(pen=pen0 )
        comment0 = 'Clipped color map applied to vertical axis'

        cm = pg.colormap.get('CET-D1')
        cm.setMappingMode('diverging')
        brush = cm.getBrush( span=(-1., 1.), orientation='vertical' ) 
        curve1 = pg.PlotDataItem(pen='w', brush=brush, fillLevel=0.0 )
        comment1 = 'Diverging vertical color map used as brush'
        
        cm = pg.colormap.get('CET-L17')
        cm.setMappingMode('mirror')
        pen2 = cm.getPen( span=(400.0,600.0), width=5, orientation='horizontal' )
        curve2 = pg.PlotDataItem(pen=pen2 )
        comment2 = 'Mirrored color map applied to horizontal axis'

        cm = pg.colormap.get('CET-C2')
        cm.setMappingMode('repeat')
        pen3 = cm.getPen( span=(100, 200), width=5, orientation='horizontal' )
        curve3 = pg.PlotDataItem(pen=pen3 ) # vertical diverging fill
        comment3 = 'Repeated color map applied to horizontal axis'

        curves = (curve0, curve1, curve2, curve3)
        comments = (comment0, comment1, comment2, comment3)

        length = int( 3.0 * 200. ) # length of display in samples
        self.top_plot = None
        for idx, (curve, comment) in enumerate( zip(curves,comments) ):
            plot = layout.addPlot(row=idx+1, col=0)
            text = pg.TextItem( comment, anchor=(0,1) )
            text.setPos(0.,1.)
            if self.top_plot is None:
                self.top_plot = plot
            else:
                plot.setXLink( self.top_plot )
            plot.addItem( curve )
            plot.addItem( text )
            plot.setXRange( 0, length )
            if idx != 1: plot.setYRange(  0. , 1.1 )
            else       : plot.setYRange( -1. , 1.2 ) # last plot include positive/negative data

        self.traces = (
            {'crv': curve0, 'buf': np.zeros( length ), 'ptr':0, 'ds': DataSource( signal_period=0.55 ) },
            {'crv': curve1, 'buf': np.zeros( length ), 'ptr':0, 'ds': DataSource( signal_period=0.61, negative_period=0.55 ) },
            {'crv': curve2, 'buf': np.zeros( length ), 'ptr':0, 'ds': DataSource( signal_period=0.65 ) },
            {'crv': curve3, 'buf': np.zeros( length ), 'ptr':0, 'ds': DataSource( signal_period=0.52 ) },
        )
        self.timer = QtCore.QTimer(timerType=QtCore.Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.update)
        timestamp = time.perf_counter()
        for dic in self.traces:
            dic['ds'].start( timestamp )
        self.last_update = time.perf_counter()
        self.mean_dt = None
        self.timer.start(33)
        
    def update(self):
        """ called by timer at 30 Hz """
        timestamp = time.perf_counter()
        # measure actual update rate:
        dt = timestamp - self.last_update
        if self.mean_dt is None:
            self.mean_dt = dt
        else:
            self.mean_dt = 0.95 * self.mean_dt + 0.05 * dt # average over fluctuating measurements
        self.top_plot.setTitle(
            'refresh: {:0.1f}ms -> {:0.1f} fps'.format( 1000*self.mean_dt, 1/self.mean_dt )
        )
        # handle rolling buffer:
        self.last_update = timestamp
        for dic in self.traces:
            new_data = dic['ds'].get_data( timestamp )
            idx_a = dic['ptr']
            idx_b = idx_a + len( new_data )
            len_buffer = dic['buf'].shape[0]
            if idx_b < len_buffer: # data does not cross buffer boundary
                dic['buf'][idx_a:idx_b] = new_data
            else: # part of the new data needs to roll over to beginning of buffer
                len_1 = len_buffer - idx_a # this many elements still fit
                dic['buf'][idx_a:idx_a+len_1] = new_data[:len_1] # first part of data at end
                idx_b = len(new_data) - len_1
                dic['buf'][0:idx_b] = new_data[len_1:] # second part of data at re-start
            dic['ptr'] = idx_b
            dic['crv'].setData( dic['buf'] )

mkQApp("Gradient plotting example")
main_window = MainWindow()

## Start Qt event loop
if __name__ == '__main__':
    pg.exec()
