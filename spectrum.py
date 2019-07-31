import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import struct

from scipy.fftpack import fft

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.ptime import time
from time import sleep
import csv
from os import path


# backend selection of matplot lib
#%matplotlib tk
#%matplotlib TkAgg

CHUNK = 1024 * 4
FORMAT = pyaudio.paInt16
CHANNELS =  1
RATE = 44100

Npts = 500
wait_sec = 2
sample_time_sec = 0.50 # estimate of time taken by server to return value
rescale = True

dt8852_params={'IntegrationTime_micros':100000}


pa = pyaudio.PyAudio()

stream = pa.open(
    format=FORMAT,
    channels = CHANNELS,
    rate = RATE,
    input = True,
    output = True,
    frames_per_buffer = CHUNK
)
audio_data = np.zeros(CHUNK//2)
def read_audio():
    data = stream.read(CHUNK)
    #data_int = np.array(struct.unpack(str(2*CHUNK)+'B', data), dtype='b')[::2]+127
    data_int = np.array(struct.unpack(str(2*CHUNK)+'B', data), dtype='b')[::2]

    return data_int

#fig, ax = plt.subplots()
#ax.plot(data_int, '-')
#plt.show()




app = QtGui.QApplication([])

## Define a top-level widget to hold everything
w = QtGui.QWidget()

## Create some widgets to be placed inside
btn_save = QtGui.QPushButton('Start Saving')

edit_intTime = QtGui.QLineEdit('{:f}'.format(sample_time_sec))
btn_setparam = QtGui.QPushButton('Set Sampling time [sec]')
btn_setdirec = QtGui.QPushButton('Set Data Directory')

statusbar = QtGui.QStatusBar()

pt = pg.PlotWidget()
xlabel = pt.setLabel('bottom',text='Sample',units='Arb. Unit')
ylabel = pt.setLabel('left',text='Counts',units='Arb. Unit')

pf = pg.PlotWidget()
xlabel = pf.setLabel('bottom',text='Frequency',units='Hz')
ylabel = pf.setLabel('left',text='Counts',units='Arb. Unit')


## Create a grid layout to manage the widgets size and position
layout = QtGui.QGridLayout()
w.setLayout(layout)

## Add widgets to the layout in their proper positions
layout.addWidget(btn_save, 1, 0) # save spectra button

layout.addWidget(QtGui.QLabel('Integration Time [usec]'), 2,0)
layout.addWidget(edit_intTime, 2, 1)
layout.addWidget(btn_setparam, 3, 0) # Set parameters button
layout.addWidget(btn_setdirec, 4, 0) # Set parameters button

layout.addWidget(statusbar, 11,0, 1,10)

layout.addWidget(pf, 0, 2, 4, 8) # Plot on right spans 8x8
layout.addWidget(pt, 6, 2, 4, 8) # Plot on right spans 8x8




# Timer function
def refresh_audio_data():
    global audio_data

    # print('Refreshing plot')
    audio_data = read_audio()
    audio_spectra = np.abs(fft(audio_data))

    pt.plot(x, audio_data, clear=True)
    pf.plot(xf, audio_spectra, clear=True)

## Start timer
timer_factor = 1.0e-3
timer = QtCore.QTimer()
timer.timeout.connect(refresh_audio_data)


def set_directory():
    global data_dir

    timer.stop()
    data_dir = QtGui.QFileDialog.getExistingDirectory()

    timer.start(sample_time_sec*timer_factor) # in msec

    statusbar.showMessage('Set data director to {}'.format(data_dir), 5000)
btn_setdirec.clicked.connect(set_directory)

def exitHandler():
    global timer
    
    print('Exiting script')
    timer.stop()

app.aboutToQuit.connect(exitHandler)


x = np.arange(0, 2*CHUNK, 2)
pt.setYRange(-128,128, padding=0)
xf = np.linspace(0, RATE, CHUNK)
pf.setXRange(0, RATE/2)





timer.start(sample_time_sec*timer_factor) # in msec

## Display the widget as a new window
w.show()

## Start the Qt event loop
app.exec_()
