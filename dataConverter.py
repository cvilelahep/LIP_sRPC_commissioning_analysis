import argparse
import tarfile
import os
import time
import datetime

import numpy as np
import ROOT
from array import array

try :
    from tqdm import tqdm 
except ImportError :
    print("Could not import tqdm. No progress bar :( Fix by installing tqdm: 'pip install tqdm'.")
    def tqdm(iterable) :
        return iterable
    
# Useful indices
I_TRIGGER = 6

I_F = 0
I_B = 1

I_T = 0
I_Q = 1

L_EVENT_HEADER = 7
N_STRIPS = 16
N_PLANES = 4

N_MAX_CHANNELS = N_STRIPS*N_PLANES*2

# Function to map data to array index
# plane: [0, 4]
# strip: [0, 15]
# end: 0 for F, 1 for B
# tq: 0 for t, 1 for q
def channelMap(plane, strip, end, tq) :
    return L_EVENT_HEADER + strip + end*N_STRIPS + tq*2*N_STRIPS + plane*2*2*N_STRIPS

# Argument parser
parser = argparse.ArgumentParser(prog = "dataConverter",
                                 description = "Converts LIP sRPC telescope ASCII data format to ROOT file")
parser.add_argument("input_file", help = "Input file name. Runs on .tar.gz or ASCII files.")

args = parser.parse_args()

# Function to convert ASCII file to ROOT
def convertFile(f) :

    # Set up output TTree
    out_file_name = "{}.root".format(os.path.splitext(f)[0])
    f_out = ROOT.TFile(out_file_name, "RECREATE")
    tree_out = ROOT.TTree("sRPCdata", "LIP sRPC telescope commissioning data")

    # Date and time
    year = array("I", [0])
    tree_out.Branch("year", year, "year/i")

    month = array("I", [0])
    tree_out.Branch("month", month, "month/i")

    day = array("I", [0])
    tree_out.Branch("day", day, "day/i")

    hour = array("I", [0])
    tree_out.Branch("hour", hour, "hour/i")

    minute = array("I", [0])
    tree_out.Branch("minute", minute, "minute/i")

    second = array("I", [0])
    tree_out.Branch("second", second, "second/i")

    # Unix timestamp
    unix_time = array("f", [0])
    tree_out.Branch("unix_time", unix_time, "unix_time/F")
    
    # Trigger
    trigger = array("I", [0])
    tree_out.Branch("trigger", trigger, "trigger/i")
    
    # Hit multiplicity
    n_hits = array('I', [0])
    tree_out.Branch("n_hits", n_hits, "n_hits/i")

    n_hits_per_plane = array('I', [0]*4)
    tree_out.Branch('n_hits_per_plane', n_hits_per_plane, 'n_hits_per_plane[4]/i')

    # Hits
    plane = array('I', [0]*N_MAX_CHANNELS)
    tree_out.Branch('plane', plane, 'plane[n_hits]/i')

    strip = array('I', [0]*N_MAX_CHANNELS)
    tree_out.Branch('strip', strip, 'strip[n_hits]/i')

    QF = array('f', [0]*N_MAX_CHANNELS)
    tree_out.Branch('QF', QF, 'QF[n_hits]/F')

    QB = array('f', [0]*N_MAX_CHANNELS)
    tree_out.Branch('QB', QB, 'QB[n_hits]/F')

    TF = array('f', [0]*N_MAX_CHANNELS)
    tree_out.Branch('TF', TF, 'TF[n_hits]/F')

    TB = array('f', [0]*N_MAX_CHANNELS)
    tree_out.Branch('TB', TB, 'TB[n_hits]/F')

    # Read data
    data = np.loadtxt(f)

    for event in tqdm(data) :

        # Date and time
        year[0], month[0], day[0], hour[0], minute[0], second[0] = [int(i) for i in event[:6]]
        unix_time[0] = time.mktime(datetime.datetime(year[0], month[0], day[0], hour[0], minute[0], second[0]).timetuple())

        # Trigger
        trigger[0] = int(event[I_TRIGGER])
        
        # Reset hit arrays
        n_hits[0] = 0
        for i in range(4) :
            n_hits_per_plane[i] = 0

        for i_plane in range(N_PLANES) :
            for i_strip in range(N_STRIPS) :
                # Hit condition: any of QF, QB, TF, TB different from zero
                is_hit = False
                for i in range(4) :
                    if event[channelMap(i_plane, i_strip, i//2, i%2)] != 0. :
                        is_hit = True
                        break
                if is_hit :
                    plane[n_hits[0]] = i_plane
                    strip[n_hits[0]] = i_strip

                    QF[n_hits[0]] = event[channelMap(i_plane, i_strip, I_F, I_Q)]
                    TF[n_hits[0]] = event[channelMap(i_plane, i_strip, I_F, I_T)]
                    QB[n_hits[0]] = event[channelMap(i_plane, i_strip, I_B, I_Q)]
                    TB[n_hits[0]] = event[channelMap(i_plane, i_strip, I_B, I_T)]

                    n_hits[0] += 1
                    n_hits_per_plane[i_plane] += 1
        tree_out.Fill()
    tree_out.Write()
    f_out.Close()

# Untar first and then delete decompressed file at the end
if tarfile.is_tarfile(args.input_file) :
    with tarfile.open(args.input_file) as tar :
        for member in tar.getmembers() :
            tar.extract(member, path = os.path.dirname(args.input_file))
            convertFile(os.path.dirname(args.input_file)+os.sep+member.name)
            os.remove(os.path.dirname(args.input_file)+os.sep+member.name)
else :
    convertFile(args.input_file)
