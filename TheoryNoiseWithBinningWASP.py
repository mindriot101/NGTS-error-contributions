#!/usr/bin/env python
# encoding: utf-8


import sys
import os
import os.path
import argparse
#from subprocess import Popen, call, PIPE, STDOUT
#import matplotlib.pyplot as plt
import numpy as np
import srw
#import pyfits
from ppgplot import *
import AstErrors as ae
import pickle
from srw import pghelpers as pgh
from ConfigWASP import *
from fits import Fits

COLOURS = {'sky': 4, 'source': 2, 'scin': 5, 'total': 1, 'read': 3}


class App(object):
    '''
    Main application object for the project
    '''
    source = []
    sky = []
    read = []
    scin = []
    total = []

    def __init__(self, args):
        '''
        Constructor
        '''
        super(App, self).__init__()
        self.args = args
        self.exptime = self.args.exptime

        self.fileDir = os.path.dirname(__file__)

        self.mag = np.linspace(7, 18., 1000)

        self.plotLimits = (16, 8, -5, 0)

        self.run()

    def plotWASPData(self):
        '''
        Overlays the wasp data from Joao
        '''
        waspdata = pickle.load(open(
            os.path.join(self.fileDir,
            "JoaoData", "data.cpickle")
            ))

        # Convert I to V
        #imagCorrection = 0.27
        pgsci(15)
        pgpt(waspdata['vmag'], np.log10(waspdata['binned']), 1)
        pgsci(1)

    def plotNGTSData(self):
        '''
        Overlays the NGTS data
        '''
        ngtsdata = pickle.load(open(
            os.path.join(self.fileDir,
                "NGTSData", "NGTSData.cpickle")
            ))

        pgsci(15)
        pgpt(ngtsdata['mag'], np.log10(ngtsdata['sd']), 1)
        pgsci(1)

    def saturationLimit(self):
        fits = Fits()
        self.brightLimit = fits['bright'](np.log10(self.exptime))
        self.darkLimit = fits['dark'](np.log10(self.exptime))

        # Get the plot limits
        pgsci(15)
        pgsls(4)
        pgline(np.array([self.brightLimit, self.brightLimit]),
                np.array([self.plotLimits[2], self.plotLimits[3]]))
        pgsls(1)
        pgline(np.array([self.darkLimit, self.darkLimit]),
                np.array([self.plotLimits[2], self.plotLimits[3]]))
        pgsci(1)



    def run(self):
        '''
        Main function
        '''
        radius = 3.5  # Radius of flux extraction aperture
        npix = np.pi * radius ** 2
        detector = ae.WASPDetector()
        extinction = 0.08
        targettime = self.args.totaltime
        height = 2400.
        apsize = 0.111
        airmass = 1.
        readnoise = ReadNoise
        #zp = srw.ZP(1.)
        #zp = 15  # from RGW
        zp = 18.545

        if self.args.skylevel == "dark": skypersecperpix = 18.
        elif self.args.skylevel == "bright": skypersecperpix = 18.


        for mag in self.mag:
            errob = ae.ErrorContribution(mag, npix, detector.readTime(),
                    extinction, targettime, height, apsize, zp, readnoise)
            self.source.append(errob.sourceError(airmass, self.exptime))
            self.sky.append(errob.skyError(airmass, self.exptime,
                skypersecperpix))
            self.read.append(errob.readError(airmass, self.exptime))
            self.scin.append(errob.scintillationError(airmass, self.exptime))
            self.total.append(errob.totalError(airmass, self.exptime,
                skypersecperpix))

        self.source = np.log10(self.source)
        self.sky = np.log10(self.sky)
        self.read = np.log10(self.read)
        self.scin = np.log10(self.scin)
        self.total = np.log10(self.total)

        pgopen(self.args.device)
        pgvstd()
        pgswin(self.plotLimits[0], self.plotLimits[1], self.plotLimits[2],
                self.plotLimits[3])

        if self.args.plotwasp: self.plotWASPData()
        if self.args.plotngts: self.plotNGTSData()

        #if self.args.satlimit: self.saturationLimit()

        # Draw the 1mmag line
        #pgsls(2)
        #pgsci(15)
        #pgline(np.array([self.mag.max(), self.mag.min()]),
                #np.array([-3., -3.]))
        #pgsci(1)
        #pgsls(1)


        # Plot a line at the point when the total error meets
        # the 1mmag line
        #distFrom1mmag = np.abs(self.total + 3.)
        #ind = distFrom1mmag==distFrom1mmag.min()
        #self.crossPoint = self.mag[ind][0]


        #pgsls(2)
        #pgsci(15)
        #pgline(np.array([self.crossPoint, self.crossPoint]),
                #np.array([-6, -1])
                #)
        #pgsci(1)
        #pgsls(1)



        #pglab(r"V magnitude", "Fractional error", r"t\de\u: %.1f s, "
                #"t\dI\u: %.1f hours, sky: %s, 1mmag @ %.3f mag" % (
                    #self.exptime, targettime/3600., self.args.skylevel,
                    #self.crossPoint))
        pglab(r'V magnitude', r'Fractional error', r'')

        # Draw the lines
        with pgh.change_colour(COLOURS['read']):
            pgline(self.mag, self.read)
        with pgh.change_colour(COLOURS['sky']):
            pgline(self.mag, self.sky)
        with pgh.change_colour(COLOURS['source']):
            pgline(self.mag, self.source)
        with pgh.change_colour(COLOURS['scin']):
            pgline(self.mag, self.scin)
        with pgh.change_colour(COLOURS['total']):
            pgline(self.mag, self.total)
        pgbox('bcnst', 0, 0, 'bcnstl', 0, 0)

        # Create the legend
        pgsvp(0.08, 0.35, 0.12, 0.32)
        pgswin(0, 1, 0, 1)
        #pgbox('bcnst', 0, 0, 'bcnst', 0, 0)
        yinc = 0.8 / 5.
        ylevel = 0.1
        line_data = np.array([0.2, 0.4])

        for i, (key, label) in enumerate([
            ('scin', 'Scintillation'),
            ('read', 'Read'),
            ('sky', 'Sky'),
            ('source', 'Source'),
            ('total', 'Total')]):
            with pgh.change_colour(COLOURS[key]):
                ylevel = 0.1 + i * yinc
                pgline(line_data,
                        np.array([ylevel, ylevel])
                        )
            pgtext(0.5, ylevel, label)

        pgclos()

        if self.args.verbose:
            if self.darkLimit:
                print("SATLEVEL DARK: %f" % self.darkLimit)

            if self.brightLimit:
                print("SATLEVEL BRIGHT: %f" % self.brightLimit)

            print("CROSSPOINT: %f" % self.crossPoint)









if __name__ == '__main__':
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", r'.*use PyArray_AsCArray.*')
        try:
            parser = argparse.ArgumentParser()
            parser.add_argument("-t", "--totaltime", help="Total integration time",
                    default=3600., type=float, required=False)
            parser.add_argument("-e", "--exptime", help="Science exposure time",
                    type=float, required=True)
            parser.add_argument("-s", "--skylevel", help="Sky type (bright "
                                "or dark", choices=["bright", "dark"],
                                type=lambda val: val.lower(),
                                required=False, default="dark")
            parser.add_argument("-d", "--device", help="PGPLOT device",
                    required=False, default="/xs")
            parser.add_argument("-w", "--plotwasp", help="Overlay some WASP staring data",
                    action="store_true", default=False)
            parser.add_argument("-n", "--plotngts", help="Overlay some NGTS prototype data",
                    action="store_true", default=False)
            parser.add_argument("-S", "--satlimit", help="Do not plot saturation limit",
                    action="store_false", default=True)
            parser.add_argument("-v", "--verbose", default=False, help="Print extra information",
                    action="store_true")
            args = parser.parse_args()
            app = App(args)
        except KeyboardInterrupt:
            print("Interrupt caught, exiting...", file=sys.stderr)
            sys.exit(0)
