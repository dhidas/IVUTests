# Import used libraries
import matplotlib.pyplot as plt
import numpy as np
import os, copy, glob


offset_isr = [71579707, 70510314, 71171829, 72673077]
offset_smi = [71577492, 68852577, 69667985, 72502298]
offset_lix = [71251126, 70582604, 71941200, 73154733]


def combine_data_files (ifiles, ofile=None):
    """
    Put different files together in the order given.  Time will add.  The first entry
    of files after the first file will be skipped for simplicity.
    
    Parameters
    ----------
    ifiles : list
        List of filenames to combine
        
    ofile : str
        Name of output file.  Default is None
    """
    
    with open(ofile, 'w') as fo:
        tadd = 0
        for i in range(len(ifiles)):
            with open(ifiles[i]) as fi:
                l0 = fi.readline()
                l1 = fi.readline()
                if i == 0:
                    fo.write(l0)
                    fo.write(l1)
                    
                # Loop over all data
                for line in fi:
                    V = list(map(float, line.strip().split('\t')))
                    V[0] = V[0] + tadd
                    tlast = V[0]

                    fo.write('\t'.join(list(map(str, V))) + '\n')
                
                tadd = tlast
            
    return


                    
        





def make_plots_one_file (filename, time=[-1, 1e99], odir = '.'):
    """
    Make basic plots for one input file
    
    Parameters
    ----------
    filename : str
        Name of the input file
    """

    # Base output name
    outprefix = os.path.join(odir, os.path.basename(filename)[0:-4])
    
    # For the data
    D = []
    
    # Is this the first entry (will be subtracted off)
    first = True
    
    # Open file and read contents to D
    with open(filename) as fi:
        print('running file', filename)
        # Grab field names fro header, print them to see them
        fields = fi.readline().strip().split('\t')
        nfields = len(fields)
            
        # Loop over all data
        for line in fi:
            V = list(map(float, line.strip().split('\t')))
            
            if len(V) != nfields:
                raise IndexError('not the same number of fields')

            # Rescale rotary encoder counts to linear encoder scale
            for i in range(5, 9):
                V[i] = -V[i]
            for i in range(9, 13):
                V[i] = V[i]/(1000000./1048576.)/100.

            for i in range(1, 13):
                V[i] = V[i] / 1000.

            # Subtract off first entry from all others
            if first:
                a = copy.deepcopy(V[:])
                first = False
            if V[0] < time[0] or V[0] > time[1]:
                continue

                
            # Append this data line to data D
            D.append([V[i] - a[i] for i in range(len(V))])

            
    # Plot Readings vs time
    fig, ax1 = plt.subplots()
    p0 = ax1.plot([v[0] for v in D], [v[1] for v in D], label=fields[1])
    p1 = ax1.plot([v[0] for v in D], [v[3] for v in D], label=fields[3])
    plt.xlabel(fields[0])
    ax1.set_ylabel('Summation [$\mu$m]')
    ax2 = ax1.twinx()
    p2 = ax2.plot([v[0] for v in D], [v[2] for v in D], '--', label=fields[2])
    p3 = ax2.plot([v[0] for v in D], [v[4] for v in D], '--', label=fields[4])
    lns = p0+p1+p2+p3
    labs = [l.get_label() for l in lns]
    ax2.legend(lns, labs)
    ax2.set_ylabel('Subtraction [$\mu$m]')
    plt.title('ID16: ' + os.path.basename(filename))
    plt.tight_layout()
    plt.savefig(outprefix+'_1.png')
    plt.savefig(outprefix+'_1.pdf')
    plt.close()

    # Plot Readings vs time
    plt.figure()
    for i in range(5, 9):
        plt.plot([v[0] for v in D], [v[i] for v in D], label=fields[i])
    for i in range(9, 13):
        plt.plot([v[0] for v in D], [v[i] for v in D], linestyle='dashed', label=fields[i])
    plt.legend()
    plt.xlabel(fields[0])
    plt.ylabel('Encoder position [$\mu$m]')
    plt.title('ID16: ' + os.path.basename(filename))
    plt.tight_layout()
    plt.savefig(outprefix+'_2.png')
    plt.savefig(outprefix+'_2.pdf')
    plt.close()
    
    # Plot Readings vs time
    plt.figure()
    plt.plot([v[0] for v in D], [(v[9]-v[5]) for v in D], label=fields[9]+'-'+fields[5])
    plt.plot([v[0] for v in D], [(v[10]-v[6]) for v in D], label=fields[10]+'-'+fields[6])
    plt.plot([v[0] for v in D], [(v[11]-v[7]) for v in D], label=fields[11]+'-'+fields[7])
    plt.plot([v[0] for v in D], [(v[12]-v[8]) for v in D], label=fields[12]+'-'+fields[8])
    plt.legend()
    plt.xlabel(fields[0])
    plt.ylabel('Rotary - Linear Position [$\mu$m]')
    plt.title('ID16: ' + os.path.basename(filename))
    plt.tight_layout()
    plt.savefig(outprefix+'_3.png')
    plt.savefig(outprefix+'_3.pdf')
    plt.close()
    
    # Plot Readings vs time
    plt.figure()
    plt.plot([v[0] for v in D], [(v[9]-v[10]) for v in D], linestyle='dashed', label=fields[9]+'-'+fields[10])
    plt.plot([v[0] for v in D], [(v[5]-v[6]) for v in D], label=fields[5]+'-'+fields[6])
    plt.plot([v[0] for v in D], [(v[11]-v[12]) for v in D], linestyle='dashed', label=fields[11]+'-'+fields[12])
    plt.plot([v[0] for v in D], [(v[7]-v[8]) for v in D], label=fields[7]+'-'+fields[8])
    plt.legend()
    plt.xlabel(fields[0])
    plt.ylabel('DS - US [$\mu$m]')
    plt.title('ID16: ' + os.path.basename(filename))
    plt.tight_layout()
    plt.savefig(outprefix+'_4.png')
    plt.savefig(outprefix+'_4.pdf')
    plt.close()
    
    return






# data: tests/data_20180711.055625.txt
# plot: tests/plots/20180711.055625/
# html: Ana_20180711.055625.html
# index: index.html

def make_all_in_dir (idir):
    datafiles = glob.glob(idir + '/tests/data_*.txt')
    runs = [os.path.basename(datafile)[5:-4] for datafile in datafiles]
    
    for run in runs:
        # Create plots/ana/run
        os.makedirs(idir + '/tests/plots/ana/'+run)
        
        # Create html file Ana_run.html
        with open('tests/Ana_'+run+'.html', 'w') as fo:
            fo.write('<html><body>\n')
            for i in range(1, 5):
                fo.write('<a href=plots/ana/'+run+'/data_'+run+'_'+str(i)+'.png>\n')
                fo.write('<img src=plots/ana/'+run+'/data_'+run+'_'+str(i)+'.png>\n')
                fo.write('</a>\n')
            fo.write('</body></html>\n')
            
        make_plots_one_file ('tests/data_'+run+'.txt', time=[-1, 1e99], odir = 'tests/plots/ana/'+run+'/')




if __name__ == "__main__":
    filename = sys.argv[1]
    odir = os.path.dirname(filename)
    make_plots_one_file (filename, time=[-1, 1e99], odir = idir)
