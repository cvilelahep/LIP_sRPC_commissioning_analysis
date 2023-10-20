import numpy as np

data = np.genfromtxt("dabc23292080012.dat")

# Useful indices
I_TRIGGER = 6

I_F = 0
I_B = 1
I_T = 0
I_Q = 1

n_event_header = 7
n_strips = 16
n_planes = 4

q_hit_threshold = 50.

# Function to map data to array index
# plane: [0, 4]
# strip: [0, 15]
# end: 0 for F, 1 for B
# tq: 0 for t, 1 for q
def channelMap(plane, strip, end, tq) :
    return n_event_header + strip + end*n_strips + tq*2*n_strips + plane*2*2*n_strips

import matplotlib.pyplot as plt

# Arrays to store data for histograms. One array for each trigger type.
all_q = [[], []]
all_t = [[], []]
all_t_diff = [[], []]

hits = [[], []]
hits_FB = [[], []]

hit_planes = [[], []]

# Event display plot counter. Let's not plot all events...
i_plot = 0

# Event loop
for i_event, event in enumerate(data) :

    trigger_index = int(event[I_TRIGGER]-1)
    
    hits_per_event = 0
    FB_hits_per_event = 0
    planes_hit_per_event = []
    for i_plane in range(n_planes) :
        for i_strip in range(n_strips) :
            for end in range(2) :
                # Check if hit is above threshold
                if event[channelMap(i_plane, i_strip, end, 1)] > q_hit_threshold :
                    hits_per_event += 1
                    if i_plane not in planes_hit_per_event :
                        planes_hit_per_event.append(i_plane)
                    all_q[trigger_index].append(event[channelMap(i_plane, i_strip, end, I_Q)])
                    all_t[trigger_index].append(event[channelMap(i_plane, i_strip, end, I_T)])

            # Check if both ends of the strip are above threshold
            if event[channelMap(i_plane, i_strip, I_F, I_Q)] > q_hit_threshold and event[channelMap(i_plane, i_strip, I_B, I_Q)] > q_hit_threshold:
                all_t_diff[trigger_index].append(event[channelMap(i_plane, i_strip, I_F, I_T)] - event[channelMap(i_plane, i_strip, I_B, I_T)])
                FB_hits_per_event += 1
                
    hit_planes[trigger_index].append(len(planes_hit_per_event))
    hits[trigger_index].append(hits_per_event)
    hits_FB[trigger_index].append(FB_hits_per_event)

    # Make a few event displays
    if event[I_TRIGGER] == 1. and i_plot < 100 :
        i_plot += 1
        
        strip = []
        plane = []
        charge = []
        t_diff = []

        for i_strip in range(n_strips) :
            for i_plane in range(n_planes) :
                if event[channelMap(i_plane, i_strip, 0, 1)] > q_hit_threshold and event[channelMap(i_plane, i_strip, 1, 1)] > q_hit_threshold :
                    strip.append(i_strip)
                    plane.append(i_plane)
                    charge.append(event[channelMap(i_plane, i_strip, 0, 1)] + event[channelMap(i_plane, i_strip, 1, 1)])
                    t_diff.append(event[channelMap(i_plane, i_strip, 0, 0)] - event[channelMap(i_plane, i_strip, 1, 0)])

        fig = plt.figure()
        ax = fig.add_subplot(projection = '3d')
        ax.scatter(strip, t_diff, plane, c = charge)
        ax.set_xlabel("Strip")
        ax.set_ylabel(r"$t_F - t_B$")
        ax.set_zlabel("Plane")

        ax.set_xlim(0, 16)
        ax.set_ylim(-5, 15)
        ax.set_zlim(0, 3)
        plt.savefig("event_{}_3d_plot.png".format(i_event))
        plt.close()

def makeplot(array, bins, range, xlabel, fname) :
    plt.figure()
    plt.hist(array[0], histtype = "step", bins = bins, range = range, label = "Physics trigger")
    plt.hist(array[1], histtype = "step", bins = bins, range = range, label = "Self trigger")
    plt.xlabel(xlabel)
    plt.yscale('log')
    plt.legend()
    plt.savefig(fname)
    plt.close()

makeplot(hit_planes, 5, (-0.5, 4.5), "Number of planes hit", "nplaneshit.png")
makeplot(hits, 100, (-0.5, 99.5), "Hit multiplicity", "hit_mult.png")
makeplot(hits_FB, 50, (-0.5, 49.5), "Multiplicity of strips with FB coincindence", "strip_mult_coinc.png")
makeplot(all_q, 100, (0, 1000), "Q", "hit_q.png")
makeplot(all_t, 100, (-300, 700), "T", "hit_t.png")
makeplot(all_t_diff, 60, (-30, 30), "TF - TB", "strip_tdiff.png")

# Print some event data
for i_event in range(10) :
    print("EVENT {} ================================================================================".format(i_event))
    print(data[i_event][0:6])
    for i_line in range(16) : 
        print(data[i_event][7+i_line*2*2*4:7+(i_line+1)*2*2*4])
    
    print("CHARGES FRONT")
    for i_plane in range(n_planes) :
        for i_strip in range(n_strips) :
            print(data[i_event][channelMap(i_plane, i_strip, 0, 1)], end = "\t")
        print("")
    print("TIMES FRONT")
    for i_plane in range(n_planes) :
        for i_strip in range(n_strips) :
            print(data[i_event][channelMap(i_plane, i_strip, 0, 0)], end = "\t")
        print("")
    print("CHARGES BACK")
    for i_plane in range(n_planes) :
        for i_strip in range(n_strips) :
            print(data[i_event][channelMap(i_plane, i_strip, 1, 1)], end = "\t")
        print("")
    print("TIMES BACK")
    for i_plane in range(n_planes) :
        for i_strip in range(n_strips) :
            print(data[i_event][channelMap(i_plane, i_strip, 1, 0)], end = "\t")
        print("")

