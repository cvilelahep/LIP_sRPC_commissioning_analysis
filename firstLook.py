import argparse
import os

import numpy as np
import ROOT
import matplotlib.pyplot as plt

import houghTransform

hough = houghTransform.hough(17*4, (0, 17), 120, (-np.pi*0.441, np.pi*0.441), 0, "normal", 1., -1)

try :
    from tqdm import tqdm 
except ImportError :
    print("Could not import tqdm. No progress bar :( Fix by installing tqdm: 'pip install tqdm'.")
    def tqdm(iterable) :
        return iterable

# Argument parser
parser = argparse.ArgumentParser(prog = "firstLook",
                                 description = "First look at sRPC data.")
parser.add_argument("input_file", help = "Input ROOT file name. Use dataConverter.py to convert ASCII format to ROOT.")

args = parser.parse_args()

f = ROOT.TFile(args.input_file)

# Arrays to store data for histograms. One array for each trigger type.
all_q = [[], []]
all_t = [[], []]
all_t_diff = [[], []]

hits = [[], []]
hits_FB = [[], []]

hit_planes = [[], []]

# Event display plot counter. Let's not plot all events...
i_plot = 0

# Hit threshold
q_hit_threshold = 50

# Event loop
for i_event, event in tqdm(enumerate(f.sRPCdata)) :
    
    trigger_index = event.trigger - 1

    hits_per_event = 0
    
    FB_hits_per_event = 0
    planes_hit_per_event = []

    for i_hit in range(event.n_hits) :
        
        if event.QF[i_hit] > q_hit_threshold or event.QB[i_hit] > q_hit_threshold :
            hits_per_event += 1
        else :
            continue

        if event.plane[i_hit] not in planes_hit_per_event :
            planes_hit_per_event.append(event.plane[i_hit])

        all_q[trigger_index].append(event.QF[i_hit])
        all_q[trigger_index].append(event.QB[i_hit])

        all_t[trigger_index].append(event.TF[i_hit])
        all_t[trigger_index].append(event.TB[i_hit])

        if event.QF[i_hit] > q_hit_threshold and event.QB[i_hit] > q_hit_threshold :
            all_t_diff[trigger_index].append(event.TF[i_hit] - event.TB[i_hit])
            FB_hits_per_event += 1

    hit_planes[trigger_index].append(len(planes_hit_per_event))
    hits[trigger_index].append(hits_per_event)
    hits_FB[trigger_index].append(FB_hits_per_event)

    # Make a few event displays
    os.makedirs("Plots/EventDisplays", exist_ok = True)
    if event.trigger == 1. and i_plot < 100 :
        i_plot += 1
        
        strip = []
        plane = []
        charge = []
        t_diff = []

        for i_hit in range(event.n_hits) :
            if event.QF[i_hit] > q_hit_threshold and event.QB[i_hit] > q_hit_threshold :
                strip.append(event.strip[i_hit])
                plane.append(event.plane[i_hit])
                charge.append(event.QF[i_hit] + event.QB[i_hit])
                t_diff.append(event.TF[i_hit] - event.TB[i_hit])

        hough_res = hough.fit(zip(strip, plane), False, False, charge)
        
        fig = plt.figure()

        plt.subplot(2, 2, 1)
        plt.scatter(strip, plane, c = charge)
        plt.plot([-0.5, 16.5], [-0.5*hough_res[0] + hough_res[1], 16.5*hough_res[0] + hough_res[1]])
        plt.xlabel("Strip")
        plt.xlim(-0.5, 16.5)
        plt.ylabel("Plane")
        plt.ylim(-0.5, 3.5)
        plt.colorbar()
        
        plt.subplot(2, 2, 2)
        plt.scatter(t_diff, plane, c = charge)
        plt.xlabel(r"$t_F - t_B$")
        plt.xlim(-5, 15)
        plt.ylabel("Plane")
        plt.ylim(-0.5, 3.5)
        plt.colorbar()

        plt.subplot(2, 2, 3)
        plt.scatter(strip, t_diff, c = charge)
        plt.xlabel("Strip")
        plt.xlim(-0.5, 16.5)
        plt.ylabel(r"$t_F - t_B$")
        plt.ylim(-5, 15)
        plt.colorbar()

        ax = plt.subplot(2, 2, 4, projection = "3d")
        ax.scatter(strip, t_diff, plane, c = charge)
        ax.set_xlabel("Strip")
        ax.set_ylabel(r"$t_F - t_B$")
        ax.set_zlabel("Plane")

        ax.set_xlim(-0.5, 16.5)
        ax.set_ylim(-5, 15)
        ax.set_zlim(-0.5, 3.5)

        plt.tight_layout()
        plt.savefig("Plots/EventDisplays/event_{}_3d_plot.png".format(i_event))
        plt.close()

def makeplot(array, bins, range, xlabel, fname) :
    plt.figure()
    plt.hist(array[0], histtype = "step", bins = bins, range = range, label = "Physics trigger")
    plt.hist(array[1], histtype = "step", bins = bins, range = range, label = "Self trigger")
    plt.xlabel(xlabel)
    plt.yscale('log')
    plt.legend()
    plt.savefig("Plots/"+fname)
    plt.close()

makeplot(hit_planes, 5, (-0.5, 4.5), "Number of planes hit", "nplaneshit.png")
makeplot(hits, 100, (-0.5, 99.5), "Hit multiplicity", "hit_mult.png")
makeplot(hits_FB, 50, (-0.5, 49.5), "Multiplicity of strips with FB coincindence", "strip_mult_coinc.png")
makeplot(all_q, 100, (0, 1000), "Q", "hit_q.png")
makeplot(all_t, 100, (-300, 700), "T", "hit_t.png")
makeplot(all_t_diff, 60, (-30, 30), "TF - TB", "strip_tdiff.png")
