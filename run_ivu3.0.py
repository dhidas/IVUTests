from __future__ import print_function

from epics import caget, caput, PV
import time, datetime, threading
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from analysis_28v2 import *

device = sys.argv[1]
new_gap = float(sys.argv[2])


nsamples = 20
sample_time = 5.
nrecord = 10



def command (request):
    with comm_lock:
        aout.put(request, wait=True)
        time.sleep(0.05)
        response = ainp.get()
    return response




file_datetime = datetime.datetime.now().strftime('%Y%m%d.%H%M%S')
print('file identifier:', file_datetime)

# Create any directories needed
BASEDIR = 'Tests_3.0m/' + device
os.makedirs(BASEDIR, exist_ok=True)

rawfo = open(BASEDIR + '/data_' + file_datetime + '.dat')

aout = PV('SR:C04-ID:G1{IVU:1}Asyn.AOUT')
ainp = PV('SR:C04-ID:G1{IVU:1}Asyn.AINP')
gap_set = PV(pvid+'-Mtr:2}Inp:Pos')
start = PV(pvid+'-Mtr:2}Sw:Go.PROC')




# Servo interrupt time (need for gather period)
i10 = float(command('I10'))
servo_interrupt_time = i10 / 8388608. / 1e3

gather_period = sample_time / nsamples / servo_interrupt_time
print('gather period', gather_period)

sample_period = int(gather_period) * servo_interrupt_time
total_time = sample_period * nsamples
print('total_time', total_time)
rawfo.write(str(sample_period) + '\n')


# Print current gap for info
starting_gap = caget(pvid+'-LEnc}Gap')
print('starting gap:', starting_gap)

# Linear encoder values and offsets
lenc_offset = []
lenc_offset.append(float(caget(pvid+'-LEnc:1}Offset:RB')))
lenc_offset.append(float(caget(pvid+'-LEnc:2}Offset:RB')))
lenc_offset.append(float(caget(pvid+'-LEnc:3}Offset:RB')))
lenc_offset.append(float(caget(pvid+'-LEnc:4}Offset:RB')))
lenc = []
lenc.append(float(caget(pvid+'-LEnc:1}Pos')))
lenc.append(float(caget(pvid+'-LEnc:2}Pos')))
lenc.append(float(caget(pvid+'-LEnc:1}Pos')))
lenc.append(float(caget(pvid+'-LEnc:2}Pos')))
print('lenc        ', lenc)
print('lenc offset ', lenc_offset)
print('actual (cts)', [(y-x) for x,y in zip(lenc, lenc_offset)])
print('actual  (mm)', [(y-x)/1.e6 for x,y in zip(lenc, lenc_offset)])
rawfo.write(str(lenc_offset) + '\n')



# Set a new gap
gap_set.put(new_gap, wait=True)




labels = [
    '#1 Ele Rotary',
    '#2 Gap Rotary',
    '#1 Ele Linear',
    '#2 Gal Linear',
    '#3 Ele Linear Secondary',
    '#4 Gal Linear Secondary',
    '#1 DAC',
    '#2 DAC',
]
names = [
    'Ele Rot',
    'Gap Rot',
    'Ele Lin',
    'Gap Lin',
    'Ele Lin2',
    'Gap Lin2',
    'Ele DAC',
    'Gap DAC',
]


# Setup the fake motors for watching the linear encoders
command('I2503=$351A')
command('I2603=$351C')
command('I2703=$351E')
command('I2803=$3520')
command('I2500=1')
command('I2600=1')
command('I2700=1')
command('I2800=1')

# Setup gather table
command('I5000=1')

# Motor 1,2 act position (twos-compliment 48-bit)
# Elevation
command('I5001=$80008B')
# Gap
command('I5002=$80010B')

# Linear
# Elevation
command('I5003=$80018B')
# Gap
command('I5004=$80020B')
# Elevation Secondary
command('I5005=$078B20')
# Gap Secondary
command('I5006=$078B21')

# DAC Outputs 1, 2
# Elevation
command('I5007=$078002')
# Gap
command('I5008=$07800A')

command('I5049={}'.format(int(gather_period)))
command('I5050=$ff')
command('I5051=$0')
command('END GATHER')
command('DELETE GATHER')
command('DEFINE GATHER')
command('GATHER')


# Start motion
start.put(1)

# Wait for data collection
time.sleep(total_time)
time.sleep(1)

command('END GATHER')




rawfo = open(DATADIR+'/data_'+file_datetime+'.dat', 'w')
rawfo.write(str(command('I5001'))+'\n')
rawfo.write(str(command('I5002'))+'\n')
rawfo.write(str(command('I5003'))+'\n')
rawfo.write(str(command('I5004'))+'\n')
rawfo.write(str(command('I5005'))+'\n')
rawfo.write(str(command('I5006'))+'\n')
rawfo.write(str(command('I5007'))+'\n')
rawfo.write(str(command('I5008'))+'\n')

i = 0
time_download_start = time.time()
while True:
    values = command('LIST GATHER {}, 3'.format(i)).split()
    if len(values) == 1 and 'ERR' in values[0]:
        print('found end of data')
        break

    rawfo.write(' '.join(values) + ' ')

    for v in values:
        i += 1

print('download time:', time.time() - time_download_start, '[s]')

command('DELETE GATHER')
# Remove fake motors
command('I2500,4,100=0')

rawfo.close()

