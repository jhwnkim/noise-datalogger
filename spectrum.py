# Modules for Audio stream and Spectrum analyzers
import matplotlib.pyplot as plt
import numpy as np
import pyaudio
import struct
from scipy.fftpack import fft

# Modules for GUI
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.exporters
from pyqtgraph.ptime import time
from time import sleep
import csv
from os import path

# Modules for webcam
import cv2
import utils

# Serial communication for DT8852
import serial


# backend selection of matplot lib
#%matplotlib tk
#%matplotlib TkAgg

CHUNK = 1024 * 32
FORMAT = pyaudio.paInt16
CHANNELS =  1
RATE = 44100
BUFFER_SIZE_SEC = 5

Npts = 500
wait_sec = 2
sample_time_sec = 0.20 # estimate of time taken by server to return value
rescale = True
sample_time_msec_dt8852 = 10 # sampling time for dt8852

dt8852_params={'IntegrationTime_micros':100000}

# Initialize audio
pa = pyaudio.PyAudio()

stream = pa.open(
    format=FORMAT,
    channels = CHANNELS,
    rate = RATE,
    input = True,
    output = True,
    frames_per_buffer = CHUNK,
    #stream_callback=read_audio
)
audio_data = np.zeros(CHUNK//2)
audio_data_buffer = np.int16(np.zeros(RATE*BUFFER_SIZE_SEC))

# define callback (2)
def read_audio():
    data = stream.read(CHUNK)
    data_int = np.array(struct.unpack(str(2*CHUNK)+'B', data), dtype='b')[::2]

    return np.int16(data_int)


# open stream using callback (3)
# stream = pa.open(format=p.get_format_from_width(wf.getsampwidth()),
#                 channels=wf.getnchannels(),
#                 rate=wf.getframerate(),
#                 output=True,
#                 frames_per_buffer = CHUNK)
stream = pa.open(
    format=FORMAT,
    channels = CHANNELS,
    rate = RATE,
    input = True,
    output = True,
    frames_per_buffer = CHUNK
)


# # Initialize start_camera
camera = cv2.VideoCapture(0)

# Setup serial for communications with dt8852_params
dt = serial.Serial('COM4', timeout=1.0, write_timeout=1.0)
dt.write(0x55) # Toggle recording

noise_data_buffer = []

# GUI section

app = QtGui.QApplication([])

## Define a top-level widget to hold everything
w = QtGui.QWidget()

## Create some widgets to be placed inside
btn_start = QtGui.QPushButton('Start Monitoring')

edit_intTime = QtGui.QLineEdit('{:f}'.format(sample_time_sec))
btn_setparam = QtGui.QPushButton('Set Sampling time [sec]')
btn_setdirec = QtGui.QPushButton('Set Data Directory')

statusbar = QtGui.QStatusBar()

# Audio display widgets
## Time domain
pt = pg.PlotWidget(title='Time Domain Audio')
xlabel = pt.setLabel('bottom',text='Sample',units='Arb. Unit')
ylabel = pt.setLabel('left',text='Counts',units='Arb. Unit')
pt.setYRange(-128,128, padding=0)
x = np.arange(0, 2*CHUNK, 2)
## Frequency Domain
pf = pg.PlotWidget(title='Frequency Domain Audio')
xlabel = pf.setLabel('bottom',text='Frequency',units='Hz')
ylabel = pf.setLabel('left',text='Counts',units='Arb. Unit')
pf.setYRange(0,np.iinfo('int16').max*5)
# pf.setXRange(0, RATE/2)
pf.setXRange(0, 100) # just up to 100 Hz
xf = np.linspace(0, RATE, CHUNK)

# Camera image view widget
imv = pg.ImageView()
imv.ui.histogram.hide()
imv.ui.roiBtn.hide()
imv.ui.menuBtn.hide()

# Sound Level meter Display
pdBA = pg.PlotWidget(title='Noise Level')
xlabel = pdBA.setLabel('bottom',text='Date/Time',units='Arb. Unit')
ylabel = pdBA.setLabel('left',text='Noise Level',units='dBA')
# pdBA.setYRange(0,130, padding=0)
pdBA.disableAutoRange()
pdBA.setYRange(30,80, padding=0)
dtime = np.arange(0, 2*CHUNK, 2)

dBLabel = QtGui.QLabel('Noise Level: ')
dBLabel.setFont(QtGui.QFont("Arial", 20, QtGui.QFont.Black))

## Create a grid layout to manage the widgets size and position
layout = QtGui.QGridLayout()
w.setLayout(layout)

## Add widgets to the layout in their proper positions
row_count = 0
layout.addWidget(btn_start, 0, 0) # start measurement button
row_count = row_count+1

#layout.addWidget(QtGui.QLabel('Integration Time [usec]'), 2,0)
#layout.addWidget(edit_intTime, 2, 1)
#layout.addWidget(btn_setparam, 3, 0) # Set parameters button
#layout.addWidget(btn_setdirec, 4, 0) # Set parameters button

#layout.addWidget(statusbar, 11,0, 1,10)

layout.addWidget(pdBA, row_count, 0, 4, 14)
layout.addWidget(dBLabel, row_count, 14, 4,2)

row_count = row_count+4


layout.addWidget(pf, row_count, 0, 4, 8) # Plot on right spans 4x8
row_count = row_count+4
layout.addWidget(pt, row_count, 0, 4, 8) # Plot on right spans 4x8
row_count = row_count -4

layout.addWidget(imv, row_count, 8, 8, 8) # Image view on right




# Timer function
def refresh_audio_data():
    global audio_data

    # print('Refreshing plot')
    try:
        audio_data = read_audio()
    except:
        print('Error while reading audio')
        return
    audio_spectra = np.abs(fft(audio_data))

    pt.plot(x, audio_data, clear=True)
    pf.plot(xf, audio_spectra, clear=True)

def refresh_camera_data():
    global imv

    try:
        ret, image = camera.read()
        #image = np.zeros([400,500])
    except:
        print('Error while reading camera')
        return

    # Error in setimage at night bug
    if ret:
        if np.sum(image) < 100000:
            image = cv2.imread('na.png')

        imv.setImage(image.T, autoHistogramRange=False)
    else:
        print('Error reading image')
    # # try:
    # #     imv.setImage(image.T)
    # # except Exception as e:
    # #     print('error while printing image')


def refresh_soundmeter_data():
    global sample_time_msec_dt8852
    global pdBA

    try:
        dt_data = dt.read()
    except Exception as e:

        print('Error while receiving data from sound meter: '+e)

        # Slow down timer
        if sample_time_msec_dt8852 == 10:
            print('slow down dt8852')
            sample_time_msec_dt8852 = 500
            timer3.stop()
            timer3.start(sample_time_msec_dt8852)
        return
    #print('DT8852 sent {}'.format(dt_data))

    if len(dt_data) > 0:

        if ord(dt_data) == 0xa5:
            token = dt.read()

            if ord(token) == 0x0d: # current measurement
                noise_data = dt.read(2)
                #print('Sound meter data received {}'.format(noise_data))
                noise_data_float = float(utils.bcdToInt(noise_data))/10.0
                # print('Sound meter data received : {} dBA'.format(noise_data_float))
                noise_data_buffer.append(noise_data_float)
                pdBA.plot(noise_data_buffer)
                pdBA.setXRange(max([0, len(noise_data_buffer)-60]), len(noise_data_buffer))

                dBLabel.setText('Noise Level:\n{} dB'.format(noise_data_float))
            elif ord(token) == 0x02: # Is in fast motion_detection
                print('Speed is fast mode')
                # dt.write(0x77) # Toggle to slow
            elif ord(token) == 0x30: # range is 30-80dB
                print('Range in 30-80 dB, toggling')
                dt.write(0x40) # Toggle to auto
            elif ord(token) == 0x4b: # range is 50-100dB
                dt.write(0x40) # Toggle to auto
            elif ord(token) == 0x4c: # range is 80-130dB
                dt.write(0x40) # Toggle to auto

        # Speed up timer
        if sample_time_msec_dt8852 ==500:
            print('speed up dt8852')
            sample_time_msec_dt8852 = 10
            timer3.stop()
            timer3.start(sample_time_msec_dt8852)
    else:
        dt.write(0x55)

        # Slow down timer
        if sample_time_msec_dt8852 == 10:
            print('slow down dt8852')
            sample_time_msec_dt8852 = 500
            timer3.stop()
            timer3.start(sample_time_msec_dt8852)



## Set timer
timer_factor = 1.0e3 # from seconds to msec
timer = QtCore.QTimer()
timer.timeout.connect(refresh_audio_data)

timer2 = QtCore.QTimer()
timer2.timeout.connect(refresh_camera_data)

timer3 = QtCore.QTimer()
timer3.timeout.connect(refresh_soundmeter_data)


def set_directory():
    global data_dir

    timer.stop()
    data_dir = QtGui.QFileDialog.getExistingDirectory()

    timer.start(sample_time_sec*timer_factor) # in msec

    statusbar.showMessage('Set data directory to {}'.format(data_dir), 5000)
btn_setdirec.clicked.connect(set_directory)

def exitHandler():
    global timer
    global stream, pa
    global camera

    # Timers
    timer.stop()
    timer2.stop()

    # Audio
    stream.stop_stream()
    stream.close()
    pa.terminate()

    # Camera
    camera.release()

    # Noise meter
    dt.close()

    print('Exiting script')


app.aboutToQuit.connect(exitHandler)


timer.start(sample_time_sec*timer_factor) # in msec
timer2.start(2*sample_time_sec*timer_factor) # in msec
timer3.start(sample_time_msec_dt8852) # in msec


## Display the widget as a new window
#w.show()
w.showMaximized()

## Start the Qt event loop
app.exec_()
