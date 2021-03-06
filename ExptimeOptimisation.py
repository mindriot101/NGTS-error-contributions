#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Usage:
    ExptimeOptimisation.py [options] --exp_fits <fits> --hprange <hprange>

Options:
    -h, --help                  Show this help
    -o, --output <output>       Output filename
    -t, --title <title>         Plot title
'''

import sys
import os
from BesanconParser import BesanconParser
import numpy as np
import matplotlib.pyplot as plt
from contextlib import contextmanager
from functools import partial
import pickle
import tables
from scipy.interpolate import interp1d
from docopt import docopt

BASE_DIR = os.path.dirname(__file__)


@contextmanager
def open_parser(cls):
    parser = cls()
    yield parser
    parser.close()

besancon_parser = partial(open_parser, cls=BesanconParser)



class Application(object):
    def __init__(self, args):
        self.args = args


    def saturated_objects(self, mags, exptime):
        with open(os.path.join(BASE_DIR, self.args['<fits>'])) as infile:
            data = pickle.load(infile)

        dark_fit = data['dark']
        bright_fit = data['bright']

        bright_out, dark_out = [], []
        for e in exptime:
            le = np.log10(e)
            dark_ind = mags < dark_fit(le)
            bright_ind = mags < bright_fit(le)

            dark_out.append(mags[dark_ind].size)
            bright_out.append(mags[bright_ind].size)

        return dark_out, bright_out

    def high_precision_objects(self, mags, exptime):
        with tables.open_file(os.path.join(BASE_DIR, self.args['<hprange>'])) as infile:
            ref_e = infile.root.exptimes[:]
            crosspoints = infile.root.crosspoints[:]

        interp_fn = interp1d(ref_e, crosspoints)

        out_x, out_y = [], []
        for e in exptime:
            try:
                thresh = interp_fn(e)
            except ValueError:
                continue
            else:
                ind = mags < thresh
                out_x.append(e)
                out_y.append(mags[ind].size)

        return list(map(np.array, [out_x, out_y]))


    def get_shutter_ops(self, exptimes, readout=1.5):
        # Assumed number of good hours per year for a particular coordinate
        nhours = 1200.
        nseconds = nhours * 3600
        nops = nseconds / (exptimes + readout)

        return nops / 1E3

    def run(self):
        fig = plt.figure()
        ax_top = fig.add_subplot(311)
        ax_mid = fig.add_subplot(312, sharex=ax_top)
        ax_bottom = fig.add_subplot(313, sharex=ax_top)

        exptimes = 10 ** np.linspace(np.log10(5), np.log10(50), 100)
        with besancon_parser() as parser:
            for i in range(1, 4):
                # Magnitude data
                catalogue_table = parser.getTable('/fields', 'field{:d}'.format(i))


                # Get the separate magnitude arrays
                mags_dwarfs = np.array([every['imagnitude'] for every in
                        catalogue_table.where('''(cl == 5) & (imagnitude > 0)''')])
                mags_giants = np.array([every['imagnitude'] for every in
                    catalogue_table.where('''(cl < 5) & (imagnitude > 0)''')])


                # Plot the high precision objects
                hp_exptime, high_precision = self.high_precision_objects(mags_dwarfs, 
                        exptimes)
                ax_top.plot(hp_exptime, high_precision, 'k-', color='k')

                # Plot the saturation points
                dark, bright = self.saturated_objects(mags_dwarfs, exptimes)
                dark, bright = list(map(np.array, [dark, bright]))

                # Prevent the zeros being plotted
                dark_ind = dark > 0
                bright_ind = bright > 0

                ax_bottom.plot(exptimes[dark_ind], dark[dark_ind], 'k-')
                ax_bottom.plot(exptimes[bright_ind], bright[bright_ind], 'k--')


                # Calculate the shutter operations
                shutter_ops = self.get_shutter_ops(exptimes)
                ax_mid.plot(exptimes, shutter_ops, 'k-')


        ticks = [5, 10, 20, 50]

        all_axes = [ax_top, ax_mid, ax_bottom]
        ylabels = ['High precision', 'Shutter operations / 1k', 'Saturated']

        for (ax, ylabel) in zip(all_axes, ylabels):
            ax.set_xscale('log')
            ax.set_xlim(min(ticks), max(ticks))

            ax.set_ylabel(ylabel)
            ax.set_ylim(ymin=0)

        xticklabels = ax_top.get_xticklabels() + ax_mid.get_xticklabels()
        plt.setp(xticklabels, visible=False)
        ax_bottom.set_xticks(ticks)
        ax_bottom.set_xticklabels(ticks)
        ax_bottom.set_xlim(5, 50)
        ax_bottom.set_xlabel(r'Exposure time / s')
        ax_bottom.set_ylim(ymax=100)

        # Set the grid on the top plot
        ax_top.grid()

        if args['--title']:
            ax_top.set_title(args['--title'])


        plt.tight_layout()


        if self.args['--output']:
            plt.savefig(args['--output'], bbox_inches='tight')
        else:
            plt.show()

if __name__ == '__main__':
    args = docopt(__doc__)
    app = Application(args)
    app.run()
