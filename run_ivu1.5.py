from __future__ import print_function

from epics import caget, caput, PV
import time, datetime, threading
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import sys
import os
from analysis_15 import *

device = sys.argv[1]
new_gap = float(sys.argv[2])

if device != 'SRX' and device != 'AMX' and device != 'FMX':
    raise ValueError('first argument must be SRX AMX or FMX')

pvid = 'SR:C5-ID:G1{IVU21:1'
if device == 'AMX':
    pvid = 'SR:C17-ID:G1{IVU21:1'
elif device == 'FMX':
    pvid = 'SR:C17-ID:G1{IVU21:2'

comm_lock = threading.Lock()

nsamples = 3000
sample_time = 50.
nrecord = 16

file_datetime = datetime.datetime.now().strftime('%Y%m%d.%H%M%S')
print('file identifier:', file_datetime)

# Create any directories needed
BASEDIR = 'Tests_1.5m_20180807/'+device
DATADIR = BASEDIR + '/tests'
PLOTDIR = BASEDIR + '/tests/plots/' + file_datetime
os.makedirs(PLOTDIR)


# open meta data file and summary file
mfo = open(DATADIR + '/metadata_{}.txt'.format(file_datetime), 'w')
sfo = open(DATADIR + '/ASummary_{}.html'.format(file_datetime), 'w')

# html headers
sfo.write('<html><body>\n')
sfo.write('<h1>'+file_datetime+'</h1><br><br>\n')

aout = PV(pvid+'}.AOUT')
ainp = PV(pvid+'}.AINP')
gap_set = PV(pvid+'-Mtr:2}Inp:Pos')
start = PV(pvid+'-Mtr:2}Sw:Go.PROC')

def command (request):
    with comm_lock:
        aout.put(request, wait=True)
        time.sleep(0.005)
        response = ainp.get()
    return response


def convert_48bit_hex2float (v):
    '''
    Convert 12 char hex representation of 48-bits to a float from DT format
    '''
    exponent = int(v[9:], 16) - 2047
    value_lo = int(v[8], 16)
    value_hi = int(v[0:8], 16)
    calc = ( (16*value_hi) + value_lo) / 34359738363.0
    calc = calc * (1 << exponent)
    return calc


def twos_complement(input_value, num_bits=48):
    '''Calculates a two's complement integer from the given input value's bits'''
    value = int(input_value, 16)
    mask = 2**(num_bits - 1)
    return -(value & mask) + (value & ~mask)

def single_word_int (v):
    value_low = int(v, 16)
    if value_low >= 838608:
        value_low = value_low - 16777216
    return value_low

def single16_word_int (v):
    value_low = int(v, 16)
    if value_low >= 65536/2:
        value_low = value_low - 65536
    return value_low



# Servo interrupt time (need for gather period)
i10 = float(command('I10'))
servo_interrupt_time = i10 / 8388608. / 1e3

gather_period = sample_time / nsamples / servo_interrupt_time
print('gather period', gather_period)
mfo.write('gather period ' + str(gather_period) + '\n')

sample_period = int(gather_period) * servo_interrupt_time
total_time = sample_period * nsamples
print('total_time', total_time)
mfo.write('total_time ' + str(total_time) + '\n')


# Print current gap for info
starting_gap = caget(pvid+'-LEnc}Gap')
print('starting gap:', starting_gap)

# Linear encoder values and offsets
lenc_offset = []
lenc_offset.append(float(caget(pvid+'-LEnc:2}Offset:RB')))
lenc_offset.append(float(caget(pvid+'-LEnc:3}Offset:RB')))
lenc_offset.append(float(caget(pvid+'-LEnc:4}Offset:RB')))
lenc_offset.append(float(caget(pvid+'-LEnc:5}Offset:RB')))
lenc = []
lenc.append(float(caget(pvid+'-LEnc:2}Pos')))
lenc.append(float(caget(pvid+'-LEnc:3}Pos')))
lenc.append(float(caget(pvid+'-LEnc:4}Pos')))
lenc.append(float(caget(pvid+'-LEnc:5}Pos')))
print('lenc        ', lenc)
print('lenc offset ', lenc_offset)
print('actual (cts)', [(y-x) for x,y in zip(lenc, lenc_offset)])
print('actual  (mm)', [(y-x)/1.e6 for x,y in zip(lenc, lenc_offset)])
mfo.write('lenc        ' + str(lenc) + '\n')
mfo.write('lenc offset ' + str(lenc_offset) + '\n')
mfo.write('actual (cts)' + str([(y-x) for x,y in zip(lenc, lenc_offset)]) + '\n')
mfo.write('actual  (mm)' + str([(y-x)/1.e6 for x,y in zip(lenc, lenc_offset)]) + '\n')



gap_set.put(new_gap, wait=True)




labels = [
    '#2:2+3 Rotary',
    '#3:2-3 Rotary',
    '#4:4+5 Rotary',
    '#5:4-5 Rotary',
    '#25:DSU Linear',
    '#26:USU Linear',
    '#27:DSL Linear',
    '#28:USL Linear',
    '#29:DSU Rotary',
    '#30:USU Rotary',
    '#31:DSL Rotary',
    '#32:USL Rotary',
    'DSU DAC',
    'USU DAC',
    'DSL DAC',
    'USL DAC',
]
names = [
    '2P3R',
    '2M3R',
    '4P5R',
    '4M5R',
    'DSUL',
    'USUL',
    'DSLL',
    'USLL',
    'DSUR',
    'USUR',
    'DSLR',
    'USLR',
    'DSUDAC',
    'USUDAC',
    'DSLDAC',
    'USLDAC',
]


# Setup the fake motors for watching the rotary encoders
command('I2903=$3502')
command('I3003=$3503')
command('I3103=$3504')
command('I3203=$3505')
command('I2900=1')
command('I3000=1')
command('I3100=1')
command('I3200=1')



command('I5000=1')


# Motor 2-5 act position (twos-compliment 48-bit)
command('I5001=$80010B')
command('I5002=$80018B')
command('I5003=$80020B')
command('I5004=$80028B')

# Linear encoders from motors 22-25
command('I5005=$078B24')
command('I5006=$078B25')
command('I5007=$078B28')
command('I5008=$078B29')
command('I5009=$078B2C')
command('I5010=$078B2D')
command('I5011=$078B30')
command('I5012=$078B31')


# Rotary encoders from motors 29-32
command('I5013=$800E8B')
command('I5014=$800F0B')
command('I5015=$800F8B')
command('I5016=$80100B')

# DAC output of motors 2-5 (y-registers)
command('I5017=$07800A')
command('I5018=$078012')
command('I5019=$07801A')
command('I5020=$078102')


command('I5049={}'.format(int(gather_period)))
command('I5050=$fffff')
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



result=[]
scaling=1.

rawfo = open(DATADIR+'/data_'+file_datetime+'.dat', 'w')
rawfo.write(str(command('I5001'))+'\n')
rawfo.write(str(command('I5002'))+'\n')
rawfo.write(str(command('I5003'))+'\n')
rawfo.write(str(command('I5004'))+'\n')
rawfo.write(str(command('I5005'))+'\n')
rawfo.write(str(command('I5006'))+'\n')
rawfo.write(str(command('I5007'))+'\n')
rawfo.write(str(command('I5008'))+'\n')
rawfo.write(str(command('I5009'))+'\n')
rawfo.write(str(command('I5010'))+'\n')
rawfo.write(str(command('I5011'))+'\n')
rawfo.write(str(command('I5012'))+'\n')
rawfo.write(str(command('I5013'))+'\n')
rawfo.write(str(command('I5014'))+'\n')
rawfo.write(str(command('I5015'))+'\n')
rawfo.write(str(command('I5016'))+'\n')
rawfo.write(str(command('I5017'))+'\n')
rawfo.write(str(command('I5018'))+'\n')
rawfo.write(str(command('I5019'))+'\n')
rawfo.write(str(command('I5020'))+'\n')

i = 0
iw = 0
t = []
this_time = 0
good_linears = True
temp_result = []
time_download_start = time.time()
while True:
    values = command('LIST GATHER {}, 3'.format(i)).split()
    if len(values) == 1 and 'ERR' in values[0]:
        print('found end of data')
        mfo.write('found end of data\n')
        break

    rawfo.write(' '.join(values) + ' ')

    for v in values:
        if iw % nrecord < 4:
            temp_result.append(twos_complement(v) / 32. / 96.)
            iw += 1
        elif iw % nrecord < 8:
            temp_result.append((lenc_offset[(iw%nrecord) -4] - int(v[4:], 16)))
            if int(v[3], 16) != 0x0:
                print(format(int(v[0:4], 16), '#018b'), (lenc_offset[(iw%nrecord) -4] - int(v[4:], 16)))
                good_linears = False
            iw += 1
        elif iw % nrecord < 12:
            temp_result.append(twos_complement(v) / 32.)
            iw += 1
        else:
            temp_result.append(single16_word_int(v[6:10]))
            temp_result.append(single16_word_int(v[0:4]))
            iw += 2
        if iw % nrecord == 0 and i != 0:
            if good_linears:
                result = result + temp_result
                t.append(this_time)
            else:
                good_linears = True
            temp_result = []
        i += 1
    this_time += sample_period

print('download time:', time.time() - time_download_start, '[s]')
mfo.write('download time: ' + str(time.time() - time_download_start) + ' [s]')

print('res:',result)
command('DELETE GATHER')
# Remove fake motors
command('I2900,4,100=0')



r = []
for i in range(nrecord):
    r.append( [ x for x in result[i::nrecord] ])

print('lens2', len(t), len(result)/nrecord)
time_write_start = time.time()
TXTDATAFILENAME = DATADIR+'/data_'+file_datetime+'.txt'
with open(TXTDATAFILENAME, 'w') as fo:
    fo.write('Time (s)\t' + '\t'.join(labels))
    fo.write('\n')
    for i in range(len(result)):
        if i % nrecord == 0:
            fo.write(str(t[i//nrecord]) + '\t')
        fo.write( str(result[i]) )
        if i % nrecord == nrecord-1:
            fo.write('\n')
        else:
            fo.write('\t')
print('file write time:', time.time() - time_write_start, '[s]')
mfo.write('file write time: ' + str(time.time() - time_write_start) + ' [s]' + '\n')




ending_gap = caget(pvid+'-LEnc}Gap')
sfo.write('<h3>starting gap:' + str(starting_gap) + '</h3>\n')
sfo.write('<h3>ending gap:  ' + str(ending_gap) + '</h3>\n')
mfo.write('starting gap:' + str(starting_gap) + '\n')
mfo.write('ending gap:  ' + str(ending_gap) + '\n')

with open(BASEDIR+'/index.html') as ifi:
    with open(BASEDIR+'/index.tmp', 'w') as tmpfo:
        for l in ifi:
            tmpfo.write(l)
        tmpfo.write('<tr><td><a href="tests/Ana_{0}.html">{0}</a></td>'.format(file_datetime)+'<td><a href="tests/ASummary_{0}.html">{0}</a></td><td>'.format(file_datetime)+str(starting_gap)+'</td><td>'+str(ending_gap)+'</td><td><a href="tests/data_{0}.txt">data_{0}.txt</a></td><td><a href="tests/metadata_{0}.txt">metadata_{0}.txt</a></td></tr>\n'.format(file_datetime))


os.rename(BASEDIR+'/index.html', BASEDIR+'/index.bak')
os.rename(BASEDIR+'/index.tmp', BASEDIR+'/index.html')
plt.figure()
plt.title('Linear Encoders')
for i in range(4, 8):
    print('lens', len(t), len(r[i]))
    plt.plot(t, r[i], label=labels[i])
    plt.xlabel('Time [s]')
    plt.ylabel('Position [cts]')
plt.legend()
plt.tight_layout()
plt.savefig(PLOTDIR+'/linear_{}.pdf'.format(file_datetime))
plt.savefig(PLOTDIR+'/linear_{}.png'.format(file_datetime))
sfo.write('<a href="plots/{0}/linear_{0}.pdf"><img src="plots/{0}/linear_{0}.png"></a>\n'.format(file_datetime))
plt.close()

plt.figure()
plt.title('Rotary Encoders')
for i in range(8, 12):
    plt.plot(t, r[i], label=labels[i])
    plt.xlabel('Time [s]')
    plt.ylabel('Position [cts]')
plt.legend()
plt.tight_layout()
plt.savefig(PLOTDIR+'/rotary_{}.pdf'.format(file_datetime))
plt.savefig(PLOTDIR+'/rotary_{}.png'.format(file_datetime))
sfo.write('<a href="plots/{0}/rotary_{0}.pdf"><img src="plots/{0}/rotary_{0}.png"></a>\n'.format(file_datetime))
plt.close()
sfo.write('<br><br>\n')

for i in range(nrecord):
    plt.figure(1)
    plt.plot(t, r[i])
    plt.title(labels[i])
    plt.xlabel('Time [s]')
    if i < 12:
        plt.ylabel('Position [cts]')
    else:
        plt.ylabel('DAC Output')
    plt.tight_layout()
    plt.savefig(PLOTDIR+'/single_{}_{}.pdf'.format(names[i], file_datetime))
    plt.savefig(PLOTDIR+'/single_{}_{}.png'.format(names[i], file_datetime))
    sfo.write('<a href="plots/{0}/single_{1}_{0}.pdf"><img src="plots/{0}/single_{1}_{0}.png"></a>\n'.format(file_datetime, names[i]))
    plt.close()


mfo.close()
mfo = open(DATADIR + '/metadata_{}.txt'.format(file_datetime))
sfo.write('<pre>\n')
sfo.write(mfo.read())
sfo.write('</pre>\n')
sfo.write('</body></html>')




runme(TXTDATAFILENAME)
