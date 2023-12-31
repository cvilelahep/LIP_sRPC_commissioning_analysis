import numpy as np
import matplotlib.pyplot as plt

def hit_finder(slope, intercept, box_centers, box_ds, tol = 0.) :
    """ Finds hits intersected by Hough line """

    # First check if track at center of box is within box limits
    d = np.abs(box_centers[0,:,1] - (box_centers[0,:,0]*slope + intercept))
    center_in_box = d < (box_ds[0,:,1]+tol)/2.

    # Now check if, assuming line is not in box at box center, the slope is large enough for line to clip the box at corner
    clips_corner = np.abs(slope) > np.abs((d - (box_ds[0,:,1]+tol)/2.)/(box_ds[0,:,0]+tol)/2.)
    
    # If either of these is true, line goes through hit:
    hit_mask = np.logical_or(center_in_box, clips_corner)

    # Return indices
    return np.where(hit_mask)[0]

class hough() :
    """ Hough transform implementation """

    def __init__(self, n_yH, yH_range, n_xH, xH_range, z_offset, Hformat, space_scale, det_Zlen, squaretheta = False, smooth = False) :

        self.n_yH = n_yH
        self.n_xH = n_xH

        self.yH_range = yH_range
        self.xH_range = xH_range

        self.z_offset = z_offset
        self.HoughSpace_format = Hformat
        self.space_scale = space_scale
        
        self.det_Zlen = det_Zlen

        self.smooth = smooth

        self.yH_bins = np.linspace(self.yH_range[0], self.yH_range[1], n_yH)
        if not squaretheta :
            self.xH_bins = np.linspace(self.xH_range[0], self.xH_range[1], n_xH)
        else :
            self.xH_bins = np.linspace(np.sign(self.xH_range[0])*(self.xH_range[0]**0.5), np.sign(self.xH_range[1])*(self.xH_range[1]**0.5), n_xH)
            self.xH_bins = np.sign(self.xH_bins)*np.square(self.xH_bins)

        self.cos_thetas = np.cos(self.xH_bins)
        self.sin_thetas = np.sin(self.xH_bins)
        
        self.xH_i = np.array(list(range(n_xH)))

        # A back-up Hough space designed to have more/less bins wrt the default one above.
        # It is useful when fitting some low-E muon tracks, which are curved due to mult. scattering.
        self.n_yH_scaled = int(n_yH*space_scale)
        self.n_xH_scaled = int(n_xH*space_scale)
        self.yH_bins_scaled = np.linspace(self.yH_range[0], self.yH_range[1], self.n_yH_scaled)
        if not squaretheta :
            self.xH_bins_scaled= np.linspace(self.xH_range[0], self.xH_range[1], self.n_xH_scaled)
        else :
            self.xH_bins_scaled = np.linspace(np.sign(self.xH_range[0])*(self.xH_range[0]**0.5), np.sign(self.xH_range[1])*(self.xH_range[1]**0.5), self.n_xH_scaled)
            self.xH_bins_scaled = np.sign(self.xH_bins_scaled)*np.square(self.xH_bins_scaled)

        self.cos_thetas_scaled = np.cos(self.xH_bins_scaled)
        self.sin_thetas_scaled = np.sin(self.xH_bins_scaled)

        self.xH_i_scaled = np.array(list(range(self.n_xH_scaled)))

    def fit(self, hit_collection, is_scaled, draw, weights = None) :

        if not is_scaled:
           n_xH = self.n_xH
           n_yH = self.n_yH
           cos_thetas = self.cos_thetas
           sin_thetas = self.sin_thetas
           xH_bins = self.xH_bins
           yH_bins = self.yH_bins
           xH_i = self.xH_i
#           res = self.res
        else:
           n_xH = self.n_xH_scaled
           n_yH = self.n_yH_scaled
           cos_thetas = self.cos_thetas_scaled
           sin_thetas = self.sin_thetas_scaled
           xH_bins = self.xH_bins_scaled
           yH_bins = self.yH_bins_scaled
           xH_i = self.xH_i_scaled
#           res = self.res*self.space_scale

        self.accumulator = np.zeros((n_yH, n_xH))
        for i_hit, hit in enumerate(hit_collection) :
            shifted_hitZ = hit[0] - self.z_offset
            if self.HoughSpace_format == 'normal':
                 hit_yH = shifted_hitZ*cos_thetas + hit[1]*sin_thetas
            elif self.HoughSpace_format == 'linearSlopeIntercept':
                 hit_yH = hit[1] - shifted_hitZ*xH_bins
            elif self.HoughSpace_format== 'linearIntercepts':
                 hit_yH = (self.det_Zlen*hit[1] - shifted_hitZ*xH_bins)/(self.det_Zlen - shifted_hitZ)
            out_of_range = np.logical_and(hit_yH > self.yH_range[0], hit_yH < self.yH_range[1]) 
            hit_yH_i = np.floor((hit_yH[out_of_range] - self.yH_range[0])/(self.yH_range[1] - self.yH_range[0])*n_yH).astype(np.int_)

            if weights is not None :
                self.accumulator[hit_yH_i, xH_i[out_of_range]] += weights[i_hit]
            else :
                self.accumulator[hit_yH_i, xH_i[out_of_range]] += 1

        # Smooth accumulator
        if self.smooth :
            self.accumulator = scipy.ndimage.gaussian_filter(self.accumulator, self.sigma, truncate=self.truncate)

        # This might be useful for debugging, but leave out for now.
        if draw :
            plt.figure()
            plt.imshow(self.accumulator, origin = "lower", extent = [self.xH_range[0], self.xH_range[-1], self.yH_range[0], self.yH_range[-1]], aspect = "auto")
            if self.HoughSpace_format == 'normal':
               plt.xlabel(r"$\theta$ [rad]")
               plt.ylabel("r [cm]")
            elif self.HoughSpace_format == 'linearSlopeIntercept':
               plt.xlabel("slope")
               plt.ylabel("intercept @ 1st plane [cm]")
            elif self.HoughSpace_format == 'linearIntercepts':
               plt.xlabel("intercept @ last plane [cm]")
               plt.ylabel("intercept @ 1st plane [cm]")
            plt.tight_layout()
            plt.show()
            
        i_max = np.unravel_index(self.accumulator.argmax(), self.accumulator.shape)

        found_yH = yH_bins[int(i_max[0])]
        found_xH = xH_bins[int(i_max[1])]
        
        if self.HoughSpace_format == 'normal':
           slope = -1./np.tan(found_xH)
           interceptShift = found_yH/np.sin(found_xH)
           intercept = (np.tan(found_xH)*interceptShift + self.z_offset)/np.tan(found_xH)
        elif self.HoughSpace_format == 'linearSlopeIntercept':
           slope = found_xH
           intercept = found_yH - slope*self.z_offset
        elif self.HoughSpace_format == 'linearIntercepts':
           slope = (found_xH - found_yH)/self.det_Zlen
           intercept = found_yH - slope*self.z_offset
        
        return (slope, intercept)

    def fit_randomize(self, hit_collection, hit_d, n_random, is_scaled, draw, weights = None) :
        success = True
        if not len(hit_collection) :
            return (-1, -1, [[],[]], [], False)

        # Randomize hits
        if (n_random > 0) :
            random_hit_collection = []
            for i_random in range(n_random) :
                random_hits = np.random.uniform(size = hit_collection.shape) - 0.5
                random_hits *= hit_d
                random_hits += hit_collection
                random_hit_collection.append(random_hits)

            random_hit_collection = np.concatenate(random_hit_collection)
            if weights is not None :
                weights = np.tile(weights, n_random)

            fit = self.fit(random_hit_collection, is_scaled, draw, weights)
        else :
            fit = self.fit(hit_collection, is_scaled, draw, weights)

        return fit
