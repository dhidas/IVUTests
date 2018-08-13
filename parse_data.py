from __future__ import print_function
from __future__ import division
import sys
import os
import glob

import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline




def twos_complement(input_value, num_bits=48):
    '''Calculates a two's complement integer from the given input value's bits'''
    value = int(input_value, 16)
    mask = 2**(num_bits - 1)
    return -(value & mask) + (value & ~mask)


def single16_word_int (v):
    value_low = int(v, 16)
    if value_low >= 65536/2:
        value_low = value_low - 65536
    return value_low



def read_file (filename, linear_offset = [0, 0, 0, 0], rotary_offset=[0, 0, 0, 0], scale_rotary=0, delta_t = 1, odfile = ''):
    """
    Parse a list gat file from pmac test runs
    """

    print('linear_offset:', linear_offset)

    # Data list for all processed data
    dall = []

    fi = open(filename)

    for i in range(20):
        fi.readline()
    data = fi.read().split()
    fi.close()
    ndata = len(data)//14

    for d in data:
        if len(d) != 12:
            print('ERROR: data format is incorrect.  bye bye')
            return

    scaling_done = False
    time = -delta_t
    for i in range(ndata):
        time += delta_t

        # In case of bad data mark bad and skip or not
        good_data = True

        # Data format hex words
        dSum23     = data.pop(0)
        dSub23     = data.pop(0)
        dSum45     = data.pop(0)
        dSub45     = data.pop(0)
        dLinearDSU = data.pop(0)
        dLinearUSU = data.pop(0)
        dLinearDSL = data.pop(0)
        dLinearUSL = data.pop(0)
        dRotaryDSU = data.pop(0)
        dRotaryUSU = data.pop(0)
        dRotaryDSL = data.pop(0)
        dRotaryUSL = data.pop(0)
        dUpperDACs = data.pop(0)
        dLowerDACs = data.pop(0)


        # Decipher hex words to meaningful data and correct
        Sum23 = twos_complement(dSum23) / 32 / 96
        Sub23 = twos_complement(dSub23) / 32 / 96
        Sum45 = twos_complement(dSum45) / 32 / 96
        Sub45 = twos_complement(dSub45) / 32 / 96

        LinearDSU = linear_offset[0] - int(dLinearDSU[4:], 16)
        LinearUSU = linear_offset[1] - int(dLinearUSU[4:], 16)
        LinearDSL = linear_offset[2] - int(dLinearDSL[4:], 16)
        LinearUSL = linear_offset[3] - int(dLinearUSL[4:], 16)

        # Check for bad linear encoder data
        if int(dLinearDSU[3], 16) + int(dLinearUSU[3], 16) + int(dLinearDSL[3], 16) + int(dLinearUSL[3], 16) != 0:
            good_data = False



        RotaryDSU_raw = twos_complement(dRotaryDSU) / 32
        RotaryUSU_raw = twos_complement(dRotaryUSU) / 32
        RotaryDSL_raw = twos_complement(dRotaryDSL) / 32
        RotaryUSL_raw = twos_complement(dRotaryUSL) / 32

        DACDSU = single16_word_int(dUpperDACs[6:10])
        DACUSU = single16_word_int(dUpperDACs[0:4])
        DACDSL = single16_word_int(dLowerDACs[6:10])
        DACUSL = single16_word_int(dLowerDACs[0:4])


        # Scaling and offset for rotary encoders set here
        if scaling_done is not True and good_data:
            scaling_done = True
            zero_LinearDSU = LinearDSU
            zero_LinearUSU = LinearUSU
            zero_LinearDSL = LinearDSL
            zero_LinearUSL = LinearUSL
            zero_RotaryDSU = RotaryDSU_raw
            zero_RotaryUSU = RotaryUSU_raw
            zero_RotaryDSL = RotaryDSL_raw
            zero_RotaryUSL = RotaryUSL_raw

        # Correct rotary numbers (local offset)
        RotaryDSU = (RotaryDSU_raw - zero_RotaryDSU)*scale_rotary + zero_LinearDSU
        RotaryUSU = (RotaryUSU_raw - zero_RotaryUSU)*scale_rotary + zero_LinearUSU
        RotaryDSL = (RotaryDSL_raw - zero_RotaryDSL)*scale_rotary + zero_LinearDSL
        RotaryUSL = (RotaryUSL_raw - zero_RotaryUSL)*scale_rotary + zero_LinearUSL


        if False:
                print( [-zero_LinearDSU / scale_rotary + RotaryDSU_raw,
                        -zero_LinearUSU / scale_rotary + RotaryUSU_raw,
                        -zero_LinearDSL / scale_rotary + RotaryDSL_raw,
                        -zero_LinearUSL / scale_rotary + RotaryUSL_raw] )
                exit(0)

        # Correct rotary numbers (local offset)
        RotaryDSU_abs = (RotaryDSU_raw - rotary_offset[0])*scale_rotary / 1000
        RotaryUSU_abs = (RotaryUSU_raw - rotary_offset[1])*scale_rotary / 1000
        RotaryDSL_abs = (RotaryDSL_raw - rotary_offset[2])*scale_rotary / 1000
        RotaryUSL_abs = (RotaryUSL_raw - rotary_offset[3])*scale_rotary / 1000

        # Scale Linear and Rotary to microns
        LinearDSU /= 1000
        LinearUSU /= 1000
        LinearDSL /= 1000
        LinearUSL /= 1000
        RotaryDSU /= 1000
        RotaryUSU /= 1000
        RotaryDSL /= 1000
        RotaryUSL /= 1000

        # Rotary Linear Differences
        RmLDSU = RotaryDSU - LinearDSU
        RmLUSU = RotaryUSU - LinearUSU
        RmLDSL = RotaryDSL - LinearDSL
        RmLUSL = RotaryUSL - LinearUSL

        # Rotary abs Linear Differences
        RmLDSU_abs = RotaryDSU_abs - LinearDSU
        RmLUSU_abs = RotaryUSU_abs - LinearUSU
        RmLDSL_abs = RotaryDSL_abs - LinearDSL
        RmLUSL_abs = RotaryUSL_abs - LinearUSL

        # Gap Calculation from Linear encoders
        LinearGapUS = LinearUSU + LinearUSL
        LinearGapDS = LinearDSU + LinearDSL
        LinearGap = (LinearGapUS + LinearGapDS) / 2
        LinearGap /= 1000

        # Girder Tilts and Elevations
        LinearTiltU = LinearDSU - LinearUSU
        LinearTiltL = LinearDSL - LinearUSL
        LinearElevationU = (LinearUSU + LinearDSU) / 2
        LinearElevationL = -(LinearUSL + LinearDSL) / 2

        # Gap Taper, Tilt, Elevation
        LinearGapTaper = LinearGapDS - LinearGapUS
        LinearGapTilt  = (LinearTiltU + LinearTiltL) / 2
        LinearGapElevation = LinearElevationU + LinearElevationL


        # Collect useful data in a list
        dout = [time,
                Sum23, Sub23, Sum45, Sub45,
                LinearDSU, LinearUSU, LinearDSL, LinearUSL,
                RotaryDSU, RotaryUSU, RotaryDSL, RotaryUSL,
                DACDSU, DACUSU, DACDSL, DACUSL,

                RmLDSU, RmLUSU, RmLDSL, RmLUSL,
                LinearGapUS, LinearGapDS, LinearGap,
                LinearTiltU, LinearTiltL, LinearElevationU, LinearElevationL,
                LinearGapTaper, LinearGapTilt, LinearGapElevation,
                RotaryDSU_raw, RotaryUSU_raw, RotaryDSL_raw, RotaryUSL_raw,
                RotaryDSU_abs, RotaryUSU_abs, RotaryDSL_abs, RotaryUSL_abs,
                RmLDSU_abs, RmLUSU_abs, RmLDSL_abs, RmLUSL_abs,
               ]
        if good_data:
            dall.append(dout)


    labs = ['Time [s]',
            '#2 DSU+USU', '#3 DSU-USU', '#4 DSL+USL', '#5 DSL-USL',
            'Linear DSU [um]', 'Linear USU [um]', 'Linear DSL [um]', 'Linear USL [um]',
            'Rotary DSU [um]', 'Rotary USU [um]', 'Rotary DSL [um]', 'Rotary USL [um]',
            'DAC DSU', 'DAC USU', 'DAC DSL', 'DAC USL',

            'Rotary - Linear DSU [um]', 'Rotary - Linear USU [um]', 'Rotary - Linear DSL [um]', 'Rotary - Linear USL [um]',
            'LinearGapUS [um]', 'LinearGapDS [um]', 'LinearGap [mm]',
            'LinearTiltU [um]', 'LinearTiltL [um]', 'LinearElevationU [um]', 'LinearElevationL [um]',
            'LinearGapTaper [um]', 'LinearGapTilt [um]', 'LinearGapElevation [um]',
            'RotaryDSU raw [cts]', 'RotaryUSU raw [cts]', 'RotaryDSL raw [cts]', 'RotaryUSL raw [cts]',
            'RotaryDSU abs [um]', 'RotaryUSU abs [um]', 'RotaryDSL abs [um]', 'RotaryUSL abs [um]',
            'Rotary abs - Linear DSU [um]', 'Rotary abs - Linear USU [um]', 'Rotary abs - Linear DSL [um]', 'Rotary abs - Linear USL [um]',
            ]

    if odfile != '':
        with open(odfile, 'w') as fo:
            fo.write('\t'.join(labs) + '\n')
 
            for d in dall:
                fo.write('\t'.join(list(map(str, d))) + '\n')

    return dall




def plot_data (dall, run, datadir='.', name=''):

    # Use same colors and labels for each axis on all plots
    c = ['r', 'b', 'g', 'm']
    l = ['DSU', 'USU', 'DSL', 'USL']

    base_outdir = os.path.join(datadir, 'plots', 'ana', run)
    os.makedirs(base_outdir, exist_ok=True)

    if name != '':
        name += ' '

    fig, ax1 = plt.subplots()
    plt.title(name + 'Linear and Rotary (Absolute) Encoder Positions')
    ax1.set_xlabel('Time [s]')
    lines = []
    for i in range(4):
        lines += ax1.plot([v[0] for v in dall], [v[i+5]/1000 for v in dall], color=c[i], linewidth=1, linestyle='-.', label='Linear '+l[i])
    for i in range(4):
        lines += ax1.plot([v[0] for v in dall], [v[i+35]/1000 for v in dall], color=c[i], linewidth=1, linestyle='--', label='Rotary '+l[i])
    ax1.set_ylabel('Encoder Position [mm]')
    ax2 = ax1.twinx()
    for i in range(4):
        lines += ax2.plot([v[0] for v in dall], [v[i+39] for v in dall], color=c[i], linewidth=0.5, linestyle='-', label='Linear-Rotary '+l[i])
    ax2.set_ylabel('Rotary - Linear Difference [$\mu$m]')
    labs = [ll.get_label() for ll in lines]
    plt.legend(lines, labs, fancybox=True, framealpha=0.5)
    plt.tight_layout()
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_1.png') )
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_1.pdf') )
    plt.close()


    fig, ax1 = plt.subplots()
    plt.title(name + 'Linear and Rotary (Relative) Encoder Positions')
    ax1.set_xlabel('Time [s]')
    lines = []
    for i in range(4):
        lines += ax1.plot([v[0] for v in dall], [v[i+5]/1000 for v in dall], color=c[i], linewidth=1, linestyle='-.', label='Linear '+l[i])
    for i in range(4):
        lines += ax1.plot([v[0] for v in dall], [v[i+9]/1000 for v in dall], color=c[i], linewidth=1, linestyle='--', label='Rotary '+l[i])
    ax1.set_ylabel('Encoder Position [mm]')
    ax2 = ax1.twinx()
    for i in range(4):
        lines += ax2.plot([v[0] for v in dall], [v[i+17] for v in dall], color=c[i], linewidth=0.5, linestyle='-', label='Linear-Rotary '+l[i])
    ax2.set_ylabel('Rotary - Linear Difference [$\mu$m]')
    labs = [ll.get_label() for ll in lines]
    plt.legend(lines, labs, fancybox=True, framealpha=0.5)
    plt.tight_layout()
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_2.png') )
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_2.pdf') )
    plt.close()

    fig, ax1 = plt.subplots()
    plt.title(name + 'Gap Coordinate System')
    ax1.set_xlabel('Time [s]')
    lines = []
    lines += ax1.plot([v[0] for v in dall], [v[23] for v in dall], color='black', label='Gap')
    ax1.set_ylabel('Linear Encoder Gap [mm]')
    ax2 = ax1.twinx()
    lines += ax2.plot([v[0] for v in dall], [v[28] for v in dall], label='Taper')
    lines += ax2.plot([v[0] for v in dall], [v[29] for v in dall], label='Tilt')
    lines += ax2.plot([v[0] for v in dall], [v[30] for v in dall], label='Elevation')
    ax2.set_ylabel('Linear Encoder Taper/Tilt/Elevation [$\mu$m]')
    labs = [ll.get_label() for ll in lines]
    plt.legend(lines, labs, fancybox=True, framealpha=0.5)
    plt.tight_layout()
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_3.png') )
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_3.pdf') )
    plt.close()


    fig, ax1 = plt.subplots()
    plt.title(name + 'DAC Output to Amp')
    ax1.set_xlabel('Time [s]')
    lines = []
    lines += ax1.plot([v[0] for v in dall], [v[23] for v in dall], color='black', label='Gap')
    ax1.set_ylabel('Linear Encoder Gap [mm]')
    ax2 = ax1.twinx()
    for i in range(4):
        lines += ax2.plot([v[0] for v in dall], [v[13+i] for v in dall], color=c[i], linewidth=1, label=l[i])
    ax2.set_ylabel('DAC Output')
    labs = [ll.get_label() for ll in lines]
    plt.legend(lines, labs, fancybox=True, framealpha=0.5)
    plt.tight_layout()
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_4.png') )
    plt.savefig( os.path.join(base_outdir, 'fig_' + run + '_4.pdf') )
    plt.close()


    with open(os.path.join(datadir, 'Ana_'+run+'.html'), 'w') as htmlfo:
        htmlfo.write(f"""
        <html><body>
        <h1>{device} - {run}</h1>
        <ol>
          <li>Linear and Rotary (Absolute) Encoder Positions - Rotary offset taken to be at initial positions at open gap</li>
          <li>Linear and Rotary (Absolute) Encoder Positions - Rotary offset taken to be beginning of *this* gap move</li>
          <li>Gap Coordinate System - Linear encoder values transformed into "gap" basis</li>
          <li>DAC Output to Amp - PMAC DAC output to amp (torque mode)</li>
        </ol>
        <a href="plots/ana/{run}/fig_{run}_1.pdf"><img src="plots/ana/{run}/fig_{run}_1.png"></a>
        <a href="plots/ana/{run}/fig_{run}_2.pdf"><img src="plots/ana/{run}/fig_{run}_2.png"></a>
        <a href="plots/ana/{run}/fig_{run}_3.pdf"><img src="plots/ana/{run}/fig_{run}_3.png"></a>
        <a href="plots/ana/{run}/fig_{run}_4.pdf"><img src="plots/ana/{run}/fig_{run}_4.png"></a>
        </body></html>
        """)

    
    return




def parse_metadeta_file (filename):
    """
    Parse the metadeta_ file for gather period and linear encoder offsets.

    Returns
    =======
    gather_period, linear_offsets[4]
    """

    with open(filename) as fi:
        gather_period = int(float(fi.readline().split()[-1]))

        fi.readline()
        fi.readline()
        lenc_line = fi.readline()
        linear_offsets = list(map(float, lenc_line[lenc_line.find('[')+1:lenc_line.find(']')-1].split(',')))

        fi.readline()
        fi.readline()
        fi.readline()
        fi.readline()
        
        start = float(fi.readline().split(':')[-1])
        end   = float(fi.readline().split(':')[-1])

    return gather_period, linear_offsets, start, end




def get_scale_rotary (device):
    # Rotary scaling from counts to nm

    if device == 'SRX' or device == 'AMX' or device == 'FMX':
        return 1/(1000000/1048576)/(1000/8)
    elif device == 'SMI' or device == 'ISR' or device == 'LIX':
        return 1/(1000000/1048576)/(800/8)

    return 0



def get_rotary_offset (device):

    if device == 'SRX':
        return [-2395854835.2929688, -2395919453.1121216, -2445716487.2940674, -2446270659.524109]
    elif device == 'AMX':
        return [-1943103140.900757, -1942963208.7803957, -1942980430.7344973, -1942898559.5010378]
    elif device == 'FMX':
        return [-835464624.0891726, -835239329.4262698, -835678154.3574221, -835625395.7142947]
    elif device == 'SMI':
        return [-1997446816.9587402, -1997467701.461914, -1997683801.2573242, -1997643883.451416]
    elif device == 'ISR':
        return [-2249166527.413574, -2249186875.5561523, -2249079324.890381, -2249071331.5612793]
    elif device == 'LIX':
        return [-588114327.2414551, -588116289.8979492, -588090331.3095703, -587886454.1208496]
        
    return



datadir = sys.argv[1]

device = datadir[-10:-7]

data_files = glob.glob(os.path.join(datadir, 'data_*.dat'))
runs = [os.path.basename(df)[5:5+8+1+6] for df in data_files]
runs.sort()

htmlfo = open(os.path.join(datadir, '..', 'index.html'), 'w')
htmlfo.write(f"""
             <html><body>
             <h1>{device}</h1>
             <table>
             <tr>
             <td width="250">Summary</td><td width="250">date.time</td><td width="200">Starting gap</td><td width="200">Ending gap</td><td>Text Data</td><td>Raw Data</td>
             </tr>
             """)

for run in runs:
    #if run != '20180808.144858':
    #    continue

    print(run)

    ifile = os.path.join(datadir, 'data_' + run + '.dat')
    odfile = os.path.join(datadir, 'data_' + run + '.txt')
    mdfilename = os.path.join(os.path.dirname(ifile), 'metadata_' + run + '.txt')
    gather_period, linear_offset, start, end = parse_metadeta_file(mdfilename)

    rotary_offset = get_rotary_offset(device)
    scale_rotary = get_scale_rotary(device)
    dall = read_file(ifile, linear_offset=linear_offset, rotary_offset=rotary_offset, scale_rotary=scale_rotary, delta_t=gather_period*442.74/1000/1000, odfile=odfile)
    plot_data(dall, run, datadir, device)

    htmlfo.write('<tr>')
    htmlfo.write('<td><a href="tests/Ana_'+run+'.html">Ana_'+run+'</a></td>')
    htmlfo.write('<td><a href="tests/ASummary_'+run+'.html">'+run+'</a></td>')
    htmlfo.write('<td>'+str(round(start, 1))+'</td>')
    htmlfo.write('<td>'+str(round(end, 1))+'</td>')
    htmlfo.write('<td><a href="tests/data_'+run+'.txt">data_'+run+'.txt</a></td>')
    htmlfo.write('<td><a href="tests/data_'+run+'.dat">data_'+run+'.dat</a></td>')
    htmlfo.write('</tr>\n')


htmlfo.write('</table>')
htmlfo.write('</body></html>')
