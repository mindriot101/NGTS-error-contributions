#!/usr/bin/env python

'''
With data measured from PlotErrors.py, this script
plots the saturating magnitude as a function of exposure 
time and makes an empirical fit to the data at bright 
and dark times.

For the bright time a 4th order polynomial is fitted, 
and a 2nd order is fitted to the dark time.

The two fits are then dumped into a cPickle file 
on disk for usage later.
'''

from ppgplot import *
import argparse
import numpy as np
import cPickle

class App(object):
    ''' 
    Main application object
    '''
    def __init__(self, args):
        '''
        Constructor, sets up the data and performs the fits
        '''
        super(App, self).__init__()
        self.args = args

        self.ydata = np.array([9, 9.25, 9.5, 10, 10.5, 11, 11.5, 
            12, 12.5, 13, 9.75, 10.25, 10.75, 11.25, 11.75, 12.25, 
            12.75, 8.75, 8.5, 8.25,
            ])

        self.brightxdata = np.log10([11.1, 13.55, 17.67, 26.33, 36.71, 
            54.70, 71.36, 93.09, 113.63, 129.78, 21.57, 32.14, 44.81,
            62.48, 81.5, 99.48, 121.43, 9.09, 7.45, 5.71,
            ])


        self.darkxdata = np.log10([11.86, 14.48, 18.89, 28.14, 44.81,
            66.77, 99.48, 138.70, 193.36, 269.58, 23.06, 36.71, 54.7,
            81.5, 121.43, 169.30, 236.03, 9.72, 7.45, 6.1,
            ])

        assert self.ydata.size == self.brightxdata.size
        assert self.ydata.size == self.darkxdata.size





        self.brightFit = np.poly1d(np.polyfit(self.brightxdata, self.ydata, 4))
        self.darkFit = np.poly1d(np.polyfit(self.darkxdata, self.ydata, 2))

        pgopen(self.args.device)

    def __del__(self):
        '''
        Destructor, dumps the data and closes the plot when the class
        is destroyed
        '''
        cPickle.dump({'bright': self.brightFit, 'dark': self.darkFit}, open("fits.cpickle", "w"), protocol=2)
        pgclos()

    def plotLine(self, xdata, fit, colour=1):
        '''
        Utility function - plot a best fit line
        '''
        newxdata = np.linspace(xdata.min(), xdata.max(), 100)
        pgsci(colour)
        pgline(newxdata, fit(newxdata))
        pgsci(1)

    def run(self):
        '''
        Main function - sets up the plot nicely
        and plots points, lines and legend
        '''
        pgenv(0.9*self.brightxdata.min(), 1.1*self.brightxdata.max(), 0.9*self.ydata.min(), 1.1*self.ydata.max(), 0, 10)
        pgpt(self.brightxdata, self.ydata, 6)
        pgpt(self.darkxdata, self.ydata[:self.darkxdata.size], 7)

        self.plotLine(self.brightxdata, self.brightFit, colour=2)
        self.plotLine(self.darkxdata, self.darkFit, colour=3)

        # legend
        xpt = 6
        ypt = 13.5
        pgsci(2)
        pgline(np.log10([xpt, 1.1 * xpt]), np.array([ypt, ypt]))
        pgsci(3)
        pgline(np.log10([xpt, 1.1 * xpt]), np.array([ypt - 0.5, ypt - 0.5]))
        pgsci(1)

        pgtext(np.log10(1.15 * xpt), ypt, r"Bright %.3f t\de\u\u4\d +"
                "%.3f t\de\u\u3\d + %.3f t\de\u\u4\d + %.3f  t\de\u +"
                "%.3f" % (
                self.brightFit[0], self.brightFit[1],
                    self.brightFit[2], self.brightFit[3],
                    self.brightFit[4]))
        pgtext(np.log10(1.15 * xpt), ypt - 0.5, r"Dark %.3f t\de\u\u2\d + %.3f t\de\u + %.3f" % (self.darkFit[0], self.darkFit[1], self.darkFit[2]))

        pglab(r"Exposure time (t\de\u)", r"Saturation magnitude", "")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="PGPLOT device",
            default="1/xs", required=False)
    args = parser.parse_args()
    app = App(args)
    app.run()
