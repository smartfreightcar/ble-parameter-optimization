import random
import statistics

class DiscoverySimulation:
    def __init__(self, T, Ts, Ta, advlength, blength, rndslots, rngloss = 0.85):
        """
        Initializes a Discovery Simulation instance for calculating the mean discovery time (in slots)

        @param T    scanning interval in slots
        @param Ts   scanning window in slots
        @param Ta   advertising interval in slots
        @param advlength    advertising length (pdu) in slots
        @param blength  inter-advertising delay in slots
        @param rndslots random slotcount between advertisements        
        """

        self.T = round(T)
        self.Ts = round(Ts)
        self.Ta = round(Ta)
        
        self.blength = round(blength)
        self.rndslots = round(rndslots)
        self.advlength = round(advlength)

        self.rngloss = rngloss

        self.T_slots = self.T
        self.Ts_slots = self.Ts
        self.Ta_slots = self.Ta

        self.count_scaninterval_reset = self.T_slots
        self.count_scanwindow_reset = self.Ts_slots
        self.count_advinterval_reset = self.Ta_slots

        self.count_adv_a_reset = self.advlength
        self.count_adv_b_reset = self.blength 

        self.scan_channels = [37, 38, 39]
        self.adv_channels = [37, 38, 39]

        #print(f"Initialized simulation with T:{self.T}, Ts:{self.Ts}, Ta:{self.Ta}, PDU:{self.advlength}, B:{self.blength}, RNG:{self.rndslots}")

    def reset(self):
        """
        Resets the simulation to start at zero
        """
        self.count_scaninterval = 0
        self.count_scanwindow = 0
        self.count_advinterval = 0
        
        self.count_adv_a = 0
        self.count_adv_b = 0
        self.count_adv_idx = 0

        self.count_matched = 0

        self.channel_scan = 0
        self.channel_adv = 0

        self.channel_scan_idx = 0
        self.channel_adv_idx = 0

    
        self.count_total = 0

    def _next_event(self):
        times = []
        if self.channel_adv != 0:
            times.append(self.count_adv_a)

        if not self.count_adv_b < 0 and self.count_adv_a < 0 and self.channel_adv_idx != 0:
            times.append(self.count_adv_b)

        if self.count_advinterval >= 0:
            times.append(self.count_advinterval)

        if self.count_scaninterval >= 0:
            times.append(self.count_scaninterval)

        if self.count_scanwindow >= 0:
            times.append(self.count_scanwindow)

        return max(1, min(times))



    def sample(self):
        """
        perform one simulation for calculating the time it takes until a whole pdu is scanned and sent at the same channel at the same time

        @return slotcount until discovery
        """
        self.reset()
        self.count_advinterval = random.randint(0, self.count_advinterval_reset)

        foundmatch = False
        while not foundmatch:

            stepsize = self._next_event()
            self.count_total += stepsize
            self.count_scaninterval -= stepsize
            self.count_advinterval -= stepsize

            if self.channel_adv != 0 and self.channel_adv == self.channel_scan:
                self.count_matched += stepsize
                if self.count_matched == self.advlength:
                    if random.random() < self.rngloss:
                        return self.count_total
                    else:
                        self.count_matched = 0
            else:
                self.count_matched = 0

            if self.channel_scan != 0:
                self.count_scanwindow -= stepsize
                if self.count_scanwindow < 0:
                    self.channel_scan = 0

            if self.count_scaninterval < 0:
                #print("Scan Event")
                self.count_scaninterval = self.count_scaninterval_reset
                self.channel_scan = self.scan_channels[self.channel_scan_idx]
                self.channel_scan_idx = (self.channel_scan_idx + 1 ) % len(self.scan_channels)
                self.count_scanwindow = self.count_scanwindow_reset

            if self.channel_adv != 0:
                self.count_adv_a -= stepsize

                if self.count_adv_a < 0:
                    self.count_adv_b = self.count_adv_b_reset
                    self.channel_adv = 0

            if not self.count_adv_b < 0 and self.count_adv_a < 0 and self.channel_adv_idx != 0:
                self.count_adv_b -= stepsize
                if self.count_adv_b < 0:
                    self.count_adv_a = self.count_adv_a_reset
                    self.channel_adv = self.adv_channels[self.channel_adv_idx]
                    self.channel_adv_idx = (self.channel_adv_idx + 1) % len(self.adv_channels)
            

            if self.count_advinterval < 0:
                #print("Adv Event")
                self.count_advinterval = self.count_advinterval_reset + random.randint(0, self.rndslots)

                self.channel_adv = self.adv_channels[self.channel_adv_idx]
                self.channel_adv_idx = (self.channel_adv_idx + 1) % len(self.adv_channels)
                self.count_adv_a = self.count_adv_a_reset

    def mean(self, samples=100000):
        """
        calculate a mean value for discovery performing n samples

        @param samples  the number of samples performed to calculate mean time

        @return (mean number of slots until discovery happens, standard deviation)
        ‚
        """

        results = []

        for x in range(samples):
            mean = self.sample()
            results.append(mean)
            #print("Sample: ", mean)

        return (statistics.mean(results), statistics.stdev(results), results)

    def print_state(self):
        print(f"{self.count_total}: SCAN {self.count_scaninterval} | ADV {self.count_advinterval} | SCANCHANNEL {self.channel_scan} | ADVCHANNEL {self.channel_adv}")

SECONDS_PER_SLOT = 0.625 * 10**(-6)

def calc_mean_for_paramset(paramset, samples=10000, rngloss=0.85):
    (T, Ts, Ta) = paramset

    Tslots = T/SECONDS_PER_SLOT
    Tsslots = Ts/SECONDS_PER_SLOT
    Taslots = Ta/SECONDS_PER_SLOT

    # 20 Bytes / 1MBit/s
    advlength = (20*8) / 1000000
    advlengthslots = advlength/SECONDS_PER_SLOT
    blengthslots = (0.01 - advlength)/SECONDS_PER_SLOT

    randomslots = 0.01/SECONDS_PER_SLOT

    sim = DiscoverySimulation(Tslots, Tsslots, Taslots, advlengthslots, blengthslots, randomslots, rngloss)
    mean = sim.mean(samples=samples)

    return ((T, Ts, Ta), (mean[0] * SECONDS_PER_SLOT, mean[1] * SECONDS_PER_SLOT), mean[2])



    







