# -*- coding: utf-8 -*-

"""
Created on Tue Aug 23 11:03:57 2016

@author: Sam Schott  (ss2151@cam.ac.uk)

(c) Sam Schott; This work is licensed under a Creative Commons
Attribution-NonCommercial-NoDerivs 2.0 UK: England & Wales License.

"""

# system imports
from __future__ import division, print_function, absolute_import
import sys
import os
import platform
import subprocess
import pkg_resources as pkgr
import time
from qtpy import QtGui, QtCore, QtWidgets, uic
import matplotlib as mpl
from matplotlib.figure import Figure
import numpy as np
import logging
from math import ceil, floor
from matplotlib.backends.backend_qt5agg import (FigureCanvasQTAgg
                                                as FigureCanvas,
                                                NavigationToolbar2QT as
                                                NavigationToolbar)

# loacl imports
from mercurygui.feed import MercuryFeed
from mercurygui.connection_dialog import ConnectionDialog
from mercurygui.utils.led_indicator_widget import LedIndicator
from mercurygui.config.main import CONF

MPL_STYLE_PATH = pkgr.resource_filename('mercurygui', 'figure_style.mplstyle')
MAIN_UI_PATH = pkgr.resource_filename('mercurygui', 'main.ui')

logger = logging.getLogger(__name__)


class MercuryPlotCanvas(FigureCanvas):
    """
    Matplotlib FigureCanvas for plotting the temperature, gasflow, and
    heater level vs time.
    """

    GREEN = np.array([0, 204, 153]) / 255
    BLUE = np.array([100, 171, 246]) / 255
    RED = np.array([221, 61, 53]) / 255

    LIGHT_BLUE = np.append(BLUE, 0.2)  # add alpha value of 0.2
    LIGHT_RED = np.append(RED, 0.2)  # add alpha value of 0.2

    def __init__(self, parent=None):

        # create figure and set axis labels
        with mpl.style.context(['default', MPL_STYLE_PATH]):
            figure = Figure(facecolor='None')

        FigureCanvas.__init__(self, figure)

        with mpl.style.context(['default', MPL_STYLE_PATH]):
            d = {'height_ratios': [5, 1], 'hspace': 0, 'bottom': 0.07,
                 'top': 0.97, 'left': 0.08, 'right': 0.95}
            self.ax1, self.ax2 = self.figure.subplots(2, sharex=True, gridspec_kw=d)

        self.ax1.tick_params(axis='both', which='major', direction='out',
                             labelcolor='black', color='gray', labelsize=9)
        self.ax2.tick_params(axis='both', which='major', direction='out',
                             labelcolor='black', color='gray', labelsize=9)

        self.ax2.spines['top'].set_alpha(0.4)

        self.ax1.xaxis.set_visible(False)
        self.ax2.xaxis.set_visible(True)
        self.ax2.yaxis.set_visible(False)

        self.x_pad = 0.7/100
        self.xLim = [-1 - self.x_pad, 0 + self.x_pad]
        self.yLim = [0, 300]
        self.ax1.axis(self.xLim + self.yLim)
        self.ax2.axis(self.xLim + [-0.08, 1.08])

        self.line_t, = self.ax1.plot(0, 295, '-', linewidth=1.1,
                                     color=self.GREEN)

        self.fill1 = self.ax2.fill_between([0, ], [0, ],
                                           facecolor=self.LIGHT_BLUE,
                                           edgecolor=self.BLUE)
        self.fill2 = self.ax2.fill_between([0, ], [0, ],
                                           facecolor=self.LIGHT_RED,
                                           edgecolor=self.RED)

        self.dpts = 1000  # maximum number of data points to plot

        self.setParent(parent)
        self.setStyleSheet("background-color:transparent;")

        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)

        FigureCanvas.updateGeometry(self)

    def update_plot(self, x_data, y_data_t, y_data_g, y_data_h, x_min):

        # slice to reduce number of points to self.dpts
        step_size = max([x_data.shape[0]/self.dpts, 1])
        step_size = int(step_size)
        self.CurrentXData = x_data[::step_size]
        self.CurrentYDataT = y_data_t[::step_size]
        self.CurrentYDataG = y_data_g[::step_size]
        self.CurrentYDataH = y_data_h[::step_size]

        # set smallest displayed datapoint to slider value
        # interpolate if necessary
        if self.CurrentXData[0] < x_min:
            self.CurrentXData[0] = x_min
            self.CurrentYDataT[0] = np.interp(x_min, self.CurrentXData[0:1],
                                              self.CurrentYDataT[0:1])

        # update axis limits
        if not self.CurrentXData.size == 0:
            x_pad_abs = max(self.x_pad * abs(x_min), 1/10000)  # add padding
            xLimNew = [x_min - x_pad_abs, x_pad_abs]

            yLimNew = [floor(self.CurrentYDataT.min())-2.2,
                       ceil(self.CurrentYDataT.max())+3.2]
        else:
            xLimNew, yLimNew = self.xLim, self.yLim

        self.line_t.set_data(self.CurrentXData, self.CurrentYDataT)

        self.fill1.remove()
        self.fill2.remove()

        self.fill1 = self.ax2.fill_between(self.CurrentXData,
                                           self.CurrentYDataG, 0,
                                           facecolor=self.LIGHT_BLUE,
                                           edgecolor=self.BLUE)
        self.fill2 = self.ax2.fill_between(self.CurrentXData,
                                           self.CurrentYDataH, 0,
                                           facecolor=self.LIGHT_RED,
                                           edgecolor=self.RED)

        if xLimNew + yLimNew == self.xLim + self.yLim:
            # redraw only lines

            for ax in self.figure.axes:
                # redraw plot backgrounds (to remove old lines)
                ax.draw_artist(ax.patch)
                # redraw spines
                for spine in ax.spines.values():
                    ax.draw_artist(spine)

            self.ax1.draw_artist(self.line_t)
            self.ax2.draw_artist(self.fill1)
            self.ax2.draw_artist(self.fill2)

            self.update()
        else:
            # redraw the whole plot
            self.ax1.axis(xLimNew + yLimNew)
            self.ax2.axis(xLimNew + [-0.08, 1.08])
            self.draw()

        # cache axis limits
        self.xLim = xLimNew
        self.yLim = yLimNew


class MercuryMonitorApp(QtWidgets.QMainWindow):

    # signals carrying converted data to GUI
    heater_volt_Signal = QtCore.Signal(str)
    heater_percent_Signal = QtCore.Signal(float)
    heater_auto_Signal = QtCore.Signal(bool)

    flow_auto_Signal = QtCore.Signal(bool)
    flow_Signal = QtCore.Signal(float)
    flow_min_Signal = QtCore.Signal(str)

    t_Signal = QtCore.Signal(str)
    t_setpoint_Signal = QtCore.Signal(float)
    t_ramp_Signal = QtCore.Signal(float)
    t_ramp_enable_Signal = QtCore.Signal(bool)

    def __init__(self, feed):
        super(self.__class__, self).__init__()
        uic.loadUi(MAIN_UI_PATH, self)

        self.feed = feed

        # create popup Widgets
        self.connectionDialog = ConnectionDialog(self, feed.mercury)
        self.readingsWindow = None

        # create LED indicator
        self.led = LedIndicator(self)
        self.led.setDisabled(True)  # Make the led non clickable
        self.statusbar.addPermanentWidget(self.led)
        self.led.setChecked(False)

        # Set up figure for data plotting
        self.canvas = MercuryPlotCanvas(self)
        self.gridLayoutCanvas.addWidget(self.canvas)
        self.canvas.draw()

        # adapt text edit colors to graoh colors
        self.t1_reading.setStyleSheet('color:rgb%s' % str(tuple(self.canvas.GREEN*255)))
        self.gf1_edit.setStyleSheet('color:rgb%s' % str(tuple(self.canvas.BLUE*255)))
        self.h1_edit.setStyleSheet('color:rgb%s' % str(tuple(self.canvas.RED*255)))
        self.gf1_unit.setStyleSheet('color:rgb%s' % str(tuple(self.canvas.BLUE*255)))
        self.h1_unit.setStyleSheet('color:rgb%s' % str(tuple(self.canvas.RED*255)))

        # allow panning by user
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.hide()
        self.toolbar.pan()

        # set up data vectors for plot
        self.xData = np.array([])
        self.xDataZeroMin = np.array([])
        self.yDataT = np.array([])
        self.yDataG = np.array([])
        self.yDataH = np.array([])

        # restore previous window geometry
        self.restoreGeometry()
        # Connect menu bar actions
        self.set_up_menubar()
        # accept only numbers as input for fields
        self.set_input_validators()

        # Check if mercury is connected, connect slots
        self.display_message('Looking for Mercury at %s...'
                             % self.feed.visa_address)
        if self.feed.mercury.connected:
            self.update_GUI_connection(connected=True)

        # start (stop) updates of GUI when mercury is connected (disconnected)
        # adjust clickable buttons upon connect / disconnect
        self.feed.connectedSignal.connect(self.update_GUI_connection)

        # get new readings when available, send as out signals
        self.feed.newReadingsSignal.connect(self.fetch_readings)
        # update plot when new data arrives
        self.feed.newReadingsSignal.connect(self.update_plot_data)
        # check for overheating when new data arrives
        self.feed.newReadingsSignal.connect(self._check_overheat)

        # set up logging to file
        self.setup_logging()

# =================== BASIC UI SETUP ==========================================

    def restoreGeometry(self):
        x = CONF.get('Window', 'x')
        y = CONF.get('Window', 'y')
        w = CONF.get('Window', 'width')
        h = CONF.get('Window', 'height')

        self.setGeometry(x, y, w, h)

    def saveGeometry(self):
        geo = self.geometry()
        CONF.set('Window', 'height', geo.height())
        CONF.set('Window', 'width', geo.width())
        CONF.set('Window', 'x', geo.x())
        CONF.set('Window', 'y', geo.y())

    def exit_(self):
        self.feed.exit_()
        self.saveGeometry()
        self.deleteLater()

    def closeEvent(self, event):
        self.exit_()

    def set_up_menubar(self):
        """
        Connects menu bar items to functions, sets the initialactivated status.
        """
        # connect to callbacks
        self.showLogAction.triggered.connect(self.on_log_clicked)
        self.exitAction.triggered.connect(self.exit_)
        self.readingsAction.triggered.connect(self._on_readings_clicked)
        self.connectAction.triggered.connect(self.feed.connect)
        self.disconnectAction.triggered.connect(self.feed.disconnect)
        self.updateAddressAction.triggered.connect(self.connectionDialog.open)

        # initially disable menu bar items, will be enabled later individually
        self.connectAction.setEnabled(True)
        self.disconnectAction.setEnabled(False)
        self.modulesAction.setEnabled(False)
        self.readingsAction.setEnabled(False)

    @QtCore.Slot(bool)
    def update_GUI_connection(self, connected):
        if connected:
            self.display_message('Connection established.')
            logger.info('Connection to MercuryiTC established.')
            self.connect_slots()
            self.connectAction.setEnabled(False)
            self.disconnectAction.setEnabled(True)
            self.modulesAction.setEnabled(True)
            self.readingsAction.setEnabled(True)

            self.led.setChecked(True)

            self.show()

        elif not connected:
            self.display_error('Connection lost.')
            logger.info('Connection to MercuryiTC lost.')

            self.disconnect_slots()

            self.connectAction.setEnabled(True)
            self.disconnectAction.setEnabled(False)
            self.modulesAction.setEnabled(False)
            self.readingsAction.setEnabled(False)

            self.led.setChecked(False)

    def set_input_validators(self):
        """ Sets validators for input fields"""
        self.t2_edit.setValidator(QtGui.QDoubleValidator())
        self.r1_edit.setValidator(QtGui.QDoubleValidator())
        self.gf1_edit.setValidator(QtGui.QDoubleValidator())
        self.h1_edit.setValidator(QtGui.QDoubleValidator())

    def connect_slots(self):

        self.display_message('Connection established.')

        self.connectAction.setEnabled(False)
        self.disconnectAction.setEnabled(True)
        self.modulesAction.setEnabled(True)
        self.readingsAction.setEnabled(True)

        # connect GUI slots to emitted data from worker
        self.heater_volt_Signal.connect(self.h1_label.setText)
        self.heater_auto_Signal.connect(self.h2_checkbox.setChecked)
        self.heater_auto_Signal.connect(lambda b: self.h1_edit.setEnabled(not b))
        self.heater_auto_Signal.connect(self.h1_edit.setReadOnly)
        self.heater_percent_Signal.connect(self.h1_edit.updateValue)

        self.flow_auto_Signal.connect(self.gf2_checkbox.setChecked)
        self.flow_auto_Signal.connect(lambda b: self.gf1_edit.setEnabled(not b))
        self.flow_auto_Signal.connect(self.gf1_edit.setReadOnly)
        self.flow_Signal.connect(self.gf1_edit.updateValue)
        self.flow_min_Signal.connect(self.gf1_label.setText)

        self.t_Signal.connect(self.t1_reading.setText)
        self.t_setpoint_Signal.connect(self.t2_edit.updateValue)
        self.t_ramp_Signal.connect(self.r1_edit.updateValue)
        self.t_ramp_enable_Signal.connect(self.r2_checkbox.setChecked)

        # connect user input to change mercury settings
        self.t2_edit.returnPressed.connect(self.change_t_setpoint)
        self.r1_edit.returnPressed.connect(self.change_ramp)
        self.r2_checkbox.clicked.connect(self.change_ramp_auto)
        self.gf1_edit.returnPressed.connect(self.change_flow)
        self.gf2_checkbox.clicked.connect(self.change_flow_auto)
        self.h1_edit.returnPressed.connect(self.change_heater)
        self.h2_checkbox.clicked.connect(self.change_heater_auto)

        # conect menu bar item to show module dialog if mercury is running
        self.modulesAction.triggered.connect(self.feed.dialog.show)

        # set update_plot to be executed every time the slider position changes
        self.horizontalSlider.valueChanged.connect(self.update_plot)

    def disconnect_slots(self):
        self.display_error('Disconnected.')

        self.connectAction.setEnabled(True)
        self.disconnectAction.setEnabled(False)
        self.modulesAction.setEnabled(False)
        self.readingsAction.setEnabled(False)

        # disconnect GUI slots from worker
        self.heater_volt_Signal.disconnect(self.h1_label.setText)
        self.heater_auto_Signal.disconnect(self.h2_checkbox.setChecked)
        self.heater_auto_Signal.disconnect(self.h1_edit.setReadOnly)
        self.heater_percent_Signal.disconnect(self.h1_edit.updateValue)

        self.flow_auto_Signal.disconnect(self.gf2_checkbox.setChecked)
        self.flow_auto_Signal.disconnect(self.gf1_edit.setReadOnly)
        self.flow_Signal.disconnect(self.gf1_edit.updateValue)
        self.flow_min_Signal.disconnect(self.gf1_label.setText)

        self.t_Signal.disconnect(self.t1_reading.setText)
        self.t_setpoint_Signal.disconnect(self.t2_edit.updateValue)
        self.t_ramp_Signal.disconnect(self.r1_edit.updateValue)
        self.t_ramp_enable_Signal.disconnect(self.r2_checkbox.setChecked)

        # disconnect user input from mercury
        self.t2_edit.returnPressed.disconnect(self.change_t_setpoint)
        self.r1_edit.returnPressed.disconnect(self.change_ramp)
        self.r2_checkbox.clicked.disconnect(self.change_ramp_auto)
        self.gf1_edit.returnPressed.disconnect(self.change_flow)
        self.gf2_checkbox.clicked.disconnect(self.change_flow_auto)
        self.h1_edit.returnPressed.disconnect(self.change_heater)
        self.h2_checkbox.clicked.disconnect(self.change_heater_auto)

        # disconnect update_plo
        self.horizontalSlider.valueChanged.disconnect(self.update_plot)

    def display_message(self, text):
        self.statusbar.showMessage('%s' % text, 5000)

    def display_error(self, text):
        self.statusbar.showMessage('%s' % text)

    @QtCore.Slot(object)
    def fetch_readings(self, readings):
        """
        Parses readings for the MercuryMonitorApp and emits resulting
        strings as signals.
        """
        # emit heater signals
        self.heater_volt_Signal.emit('Heater, %s V:' % readings['HeaterVolt'])
        self.heater_auto_Signal.emit(readings['HeaterAuto'] == 'ON')
        self.heater_percent_Signal.emit(readings['HeaterPercent'])

        # emit gas flow signals
        self.flow_auto_Signal.emit(readings['FlowAuto'] == 'ON')
        self.flow_Signal.emit(readings['FlowPercent'])
        self.flow_min_Signal.emit('Gas flow (min = %s%%):' % readings['FlowMin'])

        # emit temperature signals
        self.t_Signal.emit('%s K' % str(round(readings['Temp'], 3)))
        self.t_setpoint_Signal.emit(readings['TempSetpoint'])
        self.t_ramp_Signal.emit(readings['TempRamp'])
        self.t_ramp_enable_Signal.emit(readings['TempRampEnable'] == 'ON')

    @QtCore.Slot(object)
    def update_plot_data(self, readings):
        # append data for plotting
        self.xData = np.append(self.xData, time.time())
        self.yDataT = np.append(self.yDataT, readings['Temp'])
        self.yDataG = np.append(self.yDataG, readings['FlowPercent']/100)
        self.yDataH = np.append(self.yDataH, readings['HeaterPercent']/100)

        # prevent data vector from exceeding 86400 entries
        self.xData = self.xData[-86400:]
        self.yDataT = self.yDataT[-86400:]
        self.yDataG = self.yDataG[-86400:]
        self.yDataH = self.yDataH[-86400:]

        # convert xData to minutes and set current time to t = 0
        self.xDataZeroMin = (self.xData - max(self.xData))/60

        self.update_plot()

    @QtCore.Slot()
    def update_plot(self):

        # select data to be plotted
        x_slice = self.xDataZeroMin >= -self.horizontalSlider.value()
        self.CurrentXData = self.xDataZeroMin[x_slice]
        self.CurrentYDataT = self.yDataT[x_slice]
        self.CurrentYDataG = self.yDataG[x_slice]
        self.CurrentYDataH = self.yDataH[x_slice]

        # determine first plotted datapoint
        if not self.CurrentXData.size == 0:
            x_min = max(-self.horizontalSlider.value(), self.CurrentXData[0])

        # update plot
        self.canvas.update_plot(self.CurrentXData, self.CurrentYDataT,
                                self.CurrentYDataG, self.CurrentYDataH, x_min)

        # update label
        self.timeLabel.setText('Show last %s min' % self.horizontalSlider.value())

# =================== LOGGING DATA ============================================

    def setup_logging(self):
        """
        Set up logging of temperature history to files.
        Save temperature history to log file at '~/.CustomXepr/LOG_FILES/'
        after every 10 min.
        """
        # find user home directory
        homePath = os.path.expanduser('~')
        self.loggingPath = os.path.join(homePath, '.mercurygui', 'LOG_FILES')

        # create folder '~/.CustomXepr/LOG_FILES' if not present
        if not os.path.exists(self.loggingPath):
            os.makedirs(self.loggingPath)
        # set logging file path
        self.logFile = os.path.join(self.loggingPath, 'temperature_log ' +
                                    time.strftime("%Y-%m-%d_%H-%M-%S"))

        t_save = 10  # time interval to save temperature data in min
        self.newFile = True  # create new log file for every new start
        self.save_timer = QtCore.QTimer()
        self.save_timer.setInterval(t_save*60*1000)
        self.save_timer.setSingleShot(False)  # set to reoccur
        self.save_timer.timeout.connect(self.log_temperature_data)
        self.save_timer.start()

    def save_temperature_data(self, filePath=None):
        # promt user for file path if not given
        if filePath is None:
            text = 'Select path for temperature data file:'
            filePath = QtWidgets.QFileDialog.getSaveFileName(caption=text)
            filePath = filePath[0]

        if filePath[-4:] is not '.txt':
            filePath.join('.txt')

        title = '# temperature trace, saved on '+time.strftime('%d/%m/%Y')+'\n'
        heater_vlim = self.feed.heater.vlim
        header = '\t'.join(['Time (sec)', 'Temperature (K)',
                            'Heater (%% of %sV)' % heater_vlim, 'Gas flow (%)'])

        data_matrix = np.concatenate((self.xData[:, np.newaxis],
                                      self.yDataT[:, np.newaxis],
                                      self.yDataH[:, np.newaxis],
                                      self.yDataG[:, np.newaxis]), axis=1)

        np.savetxt(filePath, data_matrix, fmt='%.5E', delimiter='\t',
                   newline='\n', header=header, comments=title)

    def log_temperature_data(self):
        # save temperature data to log file
        if self.feed.mercury.connected:
            self.save_temperature_data(self.logFile)

# =================== CALLBACKS FOR SETTING CHANGES ===========================

    @QtCore.Slot()
    def change_t_setpoint(self):
        newT = self.t2_edit.value()

        if newT < 310 and newT > 3.5:
            self.display_message('T_setpoint = %s K' % newT)
            self.feed.control.t_setpoint = newT
        else:
            self.display_error('Error: Only temperature setpoints between ' +
                               '3.5 K and 300 K allowed.')

    @QtCore.Slot()
    def change_ramp(self):
        self.feed.control.ramp = self.r1_edit.value()
        self.display_message('Ramp = %s K/min' % self.r1_edit.value())

    @QtCore.Slot(bool)
    def change_ramp_auto(self, checked):
        if checked:
            self.feed.control.ramp_enable = 'ON'
            self.display_message('Ramp is turned ON')
        else:
            self.feed.control.ramp_enable = 'OFF'
            self.display_message('Ramp is turned OFF')

    @QtCore.Slot()
    def change_flow(self):
        self.feed.control.flow = self.gf1_edit.value()
        self.display_message('Gas flow  = %s%%' % self.gf1_edit.value())

    @QtCore.Slot(bool)
    def change_flow_auto(self, checked):
        if checked:
            self.feed.control.flow_auto = 'ON'
            self.display_message('Gas flow is automatically controlled.')
            self.gf1_edit.setReadOnly(True)
            self.gf1_edit.setEnabled(False)
        else:
            self.feed.control.flow_auto = 'OFF'
            self.display_message('Gas flow is manually controlled.')
            self.gf1_edit.setReadOnly(False)
            self.gf1_edit.setEnabled(True)

    @QtCore.Slot()
    def change_heater(self):
        self.feed.control.heater = self.h1_edit.value()
        self.display_message('Heater power  = %s%%' % self.h1_edit.value())

    @QtCore.Slot(bool)
    def change_heater_auto(self, checked):
        if checked:
            self.feed.control.heater_auto = 'ON'
            self.display_message('Heater is automatically controlled.')
            self.h1_edit.setReadOnly(True)
            self.h1_edit.setEnabled(False)
        else:
            self.feed.control.heater_auto = 'OFF'
            self.display_message('Heater is manually controlled.')
            self.h1_edit.setReadOnly(False)
            self.h1_edit.setEnabled(True)

    @QtCore.Slot(object)
    def _check_overheat(self, readings):
        if readings['Temp'] > 310:
            self.display_error('Over temperature!')
            self.feed.control.heater_auto = 'OFF'
            self.feed.control.heater = 0

# ========================== CALLBACKS FOR MENU BAR ===========================

    @QtCore.Slot()
    def _on_readings_clicked(self):
        # create readings overview window if not present
        if self.readingsWindow is None:
            self.readingsWindow = ReadingsOverview(self.feed.mercury)
        # show it
        self.readingsWindow.show()

    @QtCore.Slot()
    def on_log_clicked(self):
        """
        Opens directory with log files with current log file selected.
        """

        if platform.system() == 'Windows':
            os.startfile(self.loggingPath)
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', self.loggingPath])
        else:
            subprocess.Popen(['xdg-open', self.loggingPath])


class ReadingsTab(QtWidgets.QWidget):

    EXEPT = ['read', 'write', 'query', 'CAL_INT', 'EXCT_TYPES',
             'TYPES', 'clear_cache']

    def __init__(self, mercury, module):
        super(self.__class__, self).__init__()

        self.module = module
        self.mercury = mercury

        self.name = module.nick
        self.attr = dir(module)

        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName('gridLayout_%s' % self.name)

        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName('label_%s' % self.name)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 2)

        self.comboBox = QtWidgets.QComboBox(self)
        self.comboBox.setObjectName('comboBox_%s' % self.name)
        self.gridLayout.addWidget(self.comboBox, 1, 0, 1, 1)

        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setObjectName('lineEdit_%s' % self.name)
        self.gridLayout.addWidget(self.lineEdit, 1, 1, 1, 1)

        readings = [x for x in self.attr if not (x.startswith('_') or x in self.EXEPT)]
        self.comboBox.addItems(readings)

        self.comboBox.currentIndexChanged.connect(self.get_reading)
        self.comboBox.currentIndexChanged.connect(self.get_alarms)

        self.get_reading()
        self.get_alarms()

    def get_reading(self):
        """ Gets readings of selected variable in combobox."""

        reading = getattr(self.module, self.comboBox.currentText())
        if isinstance(reading, tuple):
            reading = ''.join(map(str, reading))
        reading = str(reading)
        self.lineEdit.setText(reading)

    def get_alarms(self):
        """Gets alarms of associated module."""

        # get alarms for all modules
        address = self.module.address.split(':')
        short_address = address[1]
        if self.module.nick == 'LOOP':
            short_address = short_address.split('.')
            short_address = short_address[0] + '.loop1'
        try:
            alarm = self.mercury.alarms[short_address]
        except KeyError:
            alarm = '--'

        self.label.setText('Alarms: %s' % alarm)


class ReadingsOverview(QtWidgets.QDialog):

    def __init__(self, mercury):
        super(self.__class__, self).__init__()
        self.mercury = mercury
        self.setupUi(self)

        # refresh readings every 3 sec
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.get_readings)
        self.timer.start(3000)

    def setupUi(self, Form):
        Form.setObjectName('Mercury ITC Readings Overview')
        Form.resize(500, 142)
        self.masterGrid = QtWidgets.QGridLayout(Form)
        self.masterGrid.setObjectName('gridLayout')

        # create main tab widget
        self.tabWidget = QtWidgets.QTabWidget(Form)
        self.tabWidget.setObjectName('tabWidget')

        # create a tab with combobox and text box for each module
        self.readings_tabs = []

        for module in self.mercury.modules:
            new_tab = ReadingsTab(self.mercury, module)
            self.readings_tabs.append(new_tab)
            self.tabWidget.addTab(new_tab, module.nick)

        # add tab widget to main grid
        self.masterGrid.addWidget(self.tabWidget, 0, 0, 1, 1)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def get_readings(self):
        """
        Getting alarams of selected tab and update its selected reading, only
        if QWidget is not hidden.
        """
        if self.isVisible():
            self.tabWidget.currentWidget().get_reading()
            self.tabWidget.currentWidget().get_alarms()


def run():

    from mercuryitc import MercuryITC
    from mercurygui.config.main import CONF

    MERCURY_ADDRESS = CONF.get('Connection', 'VISA_ADDRESS')
    VISA_LIBRARY = CONF.get('Connection', 'VISA_LIBRARY')

    mercury = MercuryITC('', VISA_LIBRARY)

    app = QtWidgets.QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    feed = MercuryFeed(mercury)
    mercuryGUI = MercuryMonitorApp(feed)
    mercuryGUI.show()

    app.exec_()


if __name__ == '__main__':
    run()
