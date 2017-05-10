#!/usr/bin/env python2.7

# Copyright 2013 Virantha Ekanayake All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



"""
    Wrap ghostscript calls.  Yes, this is ugly.
"""

import subprocess
import sys, os
import logging
import glob
import shutil
import tempfile

def error(text):
    print("ERROR: %s" % text)
    exit(-1)


def warn(self, msg):
    print("WARNING: %s" % msg)

class PyRawImages(object):
    """Class to wrap all the pdfimages calls"""

    def __init__(self):
        pass

    def _get_dpi(self, pdf_filename):
        output_dpi = 300
        cmd = 'pdfimages -list "%s"' % pdf_filename
        logging.info("Running pdfimages to figure out DPI...")
        logging.debug(cmd)
        try:
            out = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            warn ("Could not execute pdfimages to calculate DPI (try installing xpdf or poppler?), so defaulting to %sdpi" % self.output_dpi) 
            return output_dpi

        # Need the second line of output
        # Make sure it exists (in case this is an empty pdf)
        results = out.splitlines()
        if len(results)<3:
            warn("Empty pdf, cannot determine dpi using pdfimages")
            return output_dpi
        results = results[2]
        logging.debug(results)
        results = results.split()
        if(results[2] != 'image'):
            warn("Could not understand output of pdfimages, please rerun with -d option and file an issue at http://github.com/virantha/pypdfocr/issues") 
            return output_dpi
        x_pt, y_pt = int(results[3]), int(results[4])

        # Now, run imagemagick identify to get pdf width/height/density
        cmd = 'identify -format "%%w %%x %%h %%y\n" "%s"' % pdf_filename
        try:
            out = subprocess.check_output(cmd, shell=True)
            results = out.splitlines()[0]
            results = results.replace("Undefined", "")
            width, xdensity, height, ydensity = [float(x) for x in results.split()]
            xdpi = round(x_pt/width*xdensity)
            ydpi = round(y_pt/height*ydensity)
            output_dpi = xdpi
            if ydpi>xdpi: output_dpi = ydpi
            if output_dpi < 300: output_dpi = 300
            if abs(xdpi-ydpi) > xdpi*.05:  # Make sure the two dpi's are within 5%
                warn("X-dpi is %d, Y-dpi is %d, defaulting to %d" % (xdpi, ydpi, output_dpi))
            else:
                print("Using %d DPI" % output_dpi)


        except Exception as e:
            logging.debug(str(e))
            warn ("Could not execute identify to calculate DPI (try installing imagemagick?), so defaulting to %sdpi" % output_dpi) 
        return output_dpi

    def extract_raw_images(self, pdf_filename, prefix):
        try:
            cmd = ['pdfimages', '-all', pdf_filename, prefix]
            logging.info(cmd)
            subprocess.check_call(cmd, shell=False)
        except subprocess.CalledProcessError as e:
            error(e)

    def make_img_from_pdf(self, pdf_filename):
        if not os.path.exists(pdf_filename):
            error('Could not find input PDF: %s' % pdf_filename)

        filename, _ = os.path.splitext(pdf_filename)

        # The possible output files glob
        globable_filename = filename + '_raw_images_*'
        # Delete any img files already existing
        for fn in glob.glob(globable_filename):
            os.remove(fn)

        output_dpi = self._get_dpi(pdf_filename)
        self.extract_raw_images(pdf_filename, filename + "_raw_images_")

        for fn in glob.glob(globable_filename):
            logging.info("Created image %s" % fn)
        return (output_dpi, globable_filename)

