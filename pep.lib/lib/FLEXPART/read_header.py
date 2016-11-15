#!/usr/bin/env python
"""

D. Arnold 
D. Morton

This is taken froma version of Don Morton of pflexible
For original pflexible contact J. Bukhardt 

and adapted so that we only have the reading of the header
for FLEXPART version 8.X and further. Some other things have
been modified. Classes and helper functions also from pflexible
"""
# builtin imports
import pdb
import sys
import os

import struct
import re
import optparse
import time
import datetime
import itertools
from math import pi, sqrt, cos
import traceback



# Dependencies:
# Numpy
import numpy as np

#### Functions for reading FLEXPART output ##### 

def gridarea(H):
    """returns an array of area corresponding to each nx,ny,nz

    Usage::

        > area = gridarea(H)


    Returns
        OUT = array area corresponding to nx,ny,nz

    Arguments
        H  = :class:`Header` object from readheader function.

    """


    pih = pi / 180.
    r_earth = 6.371e6
    cosfunc = lambda y : cos(y * pih) * r_earth
    
    nx = H['numxgrid']
    ny = H['numygrid']
    outlat0 = H['outlat0']
    dyout = H['dyout']
    dxout = H['dxout']
    area = np.zeros((nx, ny))

    for iy in range(ny):
        ylata = outlat0 + (float(iy) + 0.5) * dyout  # NEED TO Check this, iy since arrays are 0-index
        ylatp = ylata + 0.5 * dyout
        ylatm = ylata - 0.5 * dyout
        if (ylatm < 0 and ylatp > 0): hzone = dyout * r_earth * pih
        else:
            # cosfact = cosfunc(ylata)
            cosfactp = cosfunc(ylatp)
            cosfactm = cosfunc(ylatm)
            if cosfactp < cosfactm:
                hzone = sqrt(r_earth ** 2 - cosfactp ** 2) - sqrt(r_earth ** 2 - cosfactm ** 2)
            else:
                hzone = sqrt(r_earth ** 2 - cosfactm ** 2) - sqrt(r_earth ** 2 - cosfactp ** 2)

        gridarea = 2.*pi * r_earth * hzone * dxout / 360.
        for ix in range(nx):
            area[ix, iy] = gridarea

    return area

def _get_header_version(bf):
    """
    Open and read the binary file (bf) header only to the point of 
    the Flexpart version string, return the string, seek to the
    start of the file.

    """
    try:
        bf = BinaryFile(bf)
    except:
        bf = bf
    
    ret = bf.tell()
    bf.seek(12)  # start of version string
    version = bf.read('13S')
    bf.seek(ret)
    
    return version

def read_header(pathname, **kwargs):
    """
    The readheader function returns a special class (Structure) which behaves
    like a dictionary. It contains all the metadata from the simulation which
    is contained in the "header" or "header_nest" binary files from the model 
    output.
    
    .. warning::
        It is recommended to use the :class:`Header` class: H = pf.Header(path)

    This version is using the BinaryFile class rather than FortFlex. 

    Usage::

        > H = read_header(pathname) #Don't include header filename

    Returns a dictionary

        H = dictionary like object with all the run metadata.
    Arguments

      .. tabularcolumns::  |l|L|

      =============       ========================================
      keyword             Description [default]
      =============       ========================================
      pathname            FLEXPART run output directory
      readp               read release points 0=no, [1]=y
      nested              nested output [False] or True
      headerfile          provide custom name for header file
      datefile            provide a custom name for the date file
      verbose             print information while loading header
      =============       ========================================

    .. note::
        **This function is in development**

        Please report any bugs found.

    .. TODO::

        probably a lot of things, among which ... 
        
       [] choose skip/getbin or direct seek/read 
       [] define output keys in docstring
       
       
    .. note::
        The user is no longer required to indicate which version of FLEXPART
        the header is from. Checks are made, and the header is read accordingly.
        Please report any problems...
        
    """

    OPS = Structure()
    OPS.readp = True
    OPS.nested = False
    OPS.ltopo = 1  # 1 for AGL, 0 for ASL
    OPS.verbose = False
    OPS.headerfile = None
    OPS.datefile = None
    
    # # add keyword overides and options to header
    for k in kwargs.keys():
        if k not in OPS.keys():
            print("WARNING: {0} not a valid input option.".format(k))
    
    # BW compat fixes
    if 'nest' in kwargs.keys():
        raise IOError("nest is no longer a valid keyword, see docs. \n Now use nested=True or nested=False")

    
    if 'nested' in kwargs.keys():
        if kwargs['nested'] is 1:
            print("WARNING, use of nested=1, deprecated converting to nested=True")
            kwargs['nested'] = True
    
    if 'nested' in kwargs.keys():
        if kwargs['nested'] is 0:
            print("WARNING, use of nested=0, deprecated converting to nested=False")
            kwargs['nested'] = False
       
    OPS.update(kwargs)
    
    if OPS.verbose:
        print "Reading Header with:\n"
        
        for o in OPS:
            print "%s ==> %s" % (o, OPS[o])
    
    # Define utility functions for reading binary file
    skip = lambda n = 8 : bf.seek(n, 1)
    getbin = lambda dtype, n = 1 : bf.read(dtype, (n,))


    h = Structure()

    
    if OPS.headerfile:
        filename = os.path.join(pathname, OPS.headerfile);
    
    elif OPS.nested is True:
        filename = os.path.join(pathname, 'header_nest')
        h['nested'] = True;
    else:
        filename = os.path.join(pathname, 'header')
        h['nested'] = False;
    
    # Open header file in binary format
    if not os.path.exists(filename):
        raise IOError#("No such file: {0}".format(filename))
    else:
        try:
            bf = BinaryFile(filename, order="fortran")
        except:
            raise IOError("Error opening: {0} with BinaryFile class".format(filename))
    
    # Get available_dates from dates file in same directory as header
    if OPS.datefile:
        datefile = os.path.join(pathname, OPS.datefile)
    else:
        datefile = os.path.join(pathname, 'dates')
    
    if not os.path.exists(datefile):
        raise IOError("No DATEFILE: {0}".format(datefile))
    else:
        try:
            fd = file(datefile, 'r').readlines()
        except:
            raise IOError("Could not read datefile: {0}".format(datefile))
    
    # get rid of any duplicate dates (a fix for the forecast system)
    fd = sorted(list(set(fd)))
    h['available_dates'] = [d.strip('\n') for d in fd]
    
    
    # which version format is header file:
    version = _get_header_version(bf)
    

    # required containers
    junk = []  # for catching unused output
    h['nz_list'] = []
    h['species'] = []
    h['wetdep'] = [] 
    h['drydep'] = [] 
    h['ireleasestart'] = []
    h['ireleaseend'] = []
    h['compoint'] = []
    
    # Define Header format and create Dictionary Keys
    I = {0:'_0', 1:'ibdate', 2:'ibtime', 3:'flexpart', \
         4:'_1', 5:'loutstep', 6:'loutaver', 7:'loutsample', \
         8:'_2', 9:'outlon0', 10:'outlat0', 11:'numxgrid', \
         12:'numygrid', 13:'dxout', 14:'dyout', 15:'_3', 16:'numzgrid', \
         }
    # format for binary reading first part of the header file   
    Dfmt = ['i', 'i', 'i', '13S', '2i', 'i', 'i', 'i', '2i', 'f', 'f', 'i', 'i', 'f', 'f', '2i', 'i']
    if bf:
        a = [bf.read(fmt) for fmt in Dfmt]
        for j in range(len(a)):
            h[I[j]] = a[j]

        h['outheight'] = np.array([bf.read('f') for i in range(h['numzgrid'])])
        junk.append(bf.read('2i'))
        h['jjjjmmdd'] = bf.read('i')
        h['hhmmss'] = bf.read('i')
        junk.append(bf.read('2i'))
        h['nspec'] = bf.read('i') / 3  # why!?
        h['numpointspec'] = bf.read('i')
        junk.append(bf.read('2i'))
        
        # Read in the species names and levels for each nspec
        # temp dictionaries
        for i in range(h['nspec']):
            if 'V6' in version:

                h['wetdep'].append(''.join([bf.read('c') for i in range(10)]).strip())
                junk.append(bf.read('2i'))
                junk.append(bf.read('i'))
                h['drydep'].append(''.join([bf.read('c') for i in range(10)]).strip())
                junk.append(bf.read('2i'))
                h['nz_list'].append(getbin('i'))
                h['species'].append(''.join([getbin('c') for i in range(10)]).strip())
            
            else:
            
                junk.append(bf.read('i'))
                h['wetdep'].append(''.join([bf.read('c') for i in range(10)]).strip())
                junk.append(bf.read('2i'))
                junk.append(bf.read('i'))
                h['drydep'].append(''.join([bf.read('c') for i in range(10)]).strip())
                junk.append(bf.read('2i'))
                h['nz_list'].append(bf.read('i'))
                h['species'].append(''.join([bf.read('c') for i in range(10)]).strip())
                junk.append(bf.read('2i'))

        if 'V6' in version:
            bf.seek(8, 1)
        # pdb.set_trace()
        h['numpoint'] = bf.read('i')
        
        # read release info if requested
        # if OPS.readp pass has changed, we cycle through once,
        # then break the loop if OPS.readp is false. This is done
        # in order to get some of the information into the header.
        before_readp = bf.tell()

        # initialise release fields
        I = {2:'kindz', 3:'xp1', 4:'yp1', 5:'xp2', \
           6:'yp2', 7:'zpoint1', 8:'zpoint2', 9:'npart', 10:'mpart'}

        for k, v in I.iteritems():
            h[v] = np.zeros(h['numpoint'])  # create zero-filled lists in H dict

        h['xmass'] = np.zeros((h['numpoint'], h['nspec']))

                
        if 'V6' in version:
            skip()
            _readV6(bf, h)
        else:
            junk.append(bf.read('i'))
            for i in range(h['numpoint']):
                junk.append(bf.read('i'))
    
                h['ireleasestart'].append(bf.read('i'))
                h['ireleaseend'].append(bf.read('i'))
                h['kindz'][i] = bf.read('h')  # This is an int16, might need to to change something
                junk.append(bf.read('2i'))
    
                h['xp1'][i] = bf.read('f')
                h['yp1'][i] = bf.read('f')
                h['xp2'][i] = bf.read('f')
                h['yp2'][i] = bf.read('f')
                h['zpoint1'][i] = bf.read('f')
                h['zpoint2'][i] = bf.read('f')
    
                junk.append(bf.read('2i'))
                h['npart'][i] = bf.read('i')
                h['mpart'][i] = bf.read('i')
    
                junk.append(bf.read('i'))
                # initialise release fields
    
                l = bf.read('i')  # get compoint length?
                gt = bf.tell() + l  # create 'goto' point
                sp = ''
                while re.search("\w", bf.read('c')):  # collect the characters for the compoint
                    bf.seek(-1, 1)
                    sp = sp + bf.read('c')
    
                bf.seek(gt)  # skip ahead to gt point
    
                h['compoint'].append(sp)  # species names in dictionary for each nspec
                # h['compoint'].append(''.join([bf.read('c') for i in range(45)]))
                
                junk.append(bf.read('i'))
                # now loop for nspec to get xmass
                for v in range(h['nspec']):
                    Dfmt = ['i', 'f', '2i', 'f', '2i', 'f', 'i']
                    a = [bf.read(fmt) for fmt in Dfmt]
                    h['xmass'][i, v] = a[1]
    
                if OPS.readp is False:
                    """
                    We get the first set of release points here in order
                    to get some information, but skip reading the rest
                    """
                    bf.seek(before_readp)
                    if 'V6' in version:
                        bf.seek(157 * h['numpoint'], 1);
                    else:
                        bf.seek(119 * h['numpoint'] + (h['nspec'] * 36) * h['numpoint'] + 4, 1)
                    break

        
        
        if 'V6' in version:
            h['method'] = bf.read('i')
        
        else:
            junk.append(bf.read('i'))
            junk.append(bf.read('i'))
        
        h['lsubgrid'] = bf.read('i')
        h['lconvection'] = bf.read('i')
        h['ind_source'] = bf.read('i')
        h['ind_receptor'] = bf.read('i')
        
        if 'V6' in version:
            pass
        else:
            junk.append(bf.read('2i'))
        
        h['nageclass'] = bf.read('i')
        
        Lage_fmt = ['i'] * h.nageclass
        h['lage'] = [bf.read(fmt) for fmt in Lage_fmt]
        
        # Orography
        nx = h['numxgrid']
        ny = h['numygrid']
        Dfmt = ['f'] * nx
        h['oro'] = np.zeros((nx, ny), np.float)
        junk.append(bf.read('2i'))
        
        for ix in range(nx):
            h['oro'][ix] = bf.read('f', ny)
            bf.seek(8, 1)
        
        # Why was this? / deprecated.
        # if h['loutstep'] < 0:
            # h['nspec'] = h['numpoint']
        
        bf.close()


        

    #############  ADDITIONS ###########
    # attributes to header that can be added after reading below here
    h['pathname'] = pathname
    h['decayconstant'] = 0
    h.path = pathname


    # Calculate Height (outheight + topography)
    # There is an offset issue here related to the 0-indexing. Be careful.
    oro = h['oro']  # z is a numpy array
    nx = h['numxgrid']
    ny = h['numygrid']
    nz = h['numzgrid']
    
    Heightnn = np.zeros((nx, ny, nz), np.float)
    for ix in range(nx):
        if OPS.ltopo == 1:
            Heightnn[ix, :, 0] = oro[ix, :]
        else:
            Heightnn[ix, :, 0] = np.zeros(ny)

        for iz in range(nz):
            if OPS.ltopo == 1:
                Heightnn[ix, :, iz] = [h['outheight'][iz] + oro[ix, y] for y in range(ny)]
            else:
                Heightnn[ix, :, iz] = h['outheight'][iz]

    h['Area'] = gridarea(h)
    h['Heightnn'] = Heightnn
    h['nx'] = nx
    h['ny'] = ny
    h['nz'] = nz
    
    # Convert ireleasestart and ireleaseend to datetimes, fix issue #10
    start_day = datetime.datetime.strptime(str(h['ibdate']), '%Y%m%d')
    H, M, S , = [int(str(h['ibtime']).zfill(6)[i:i + 2]) for i in range(0, 6, 2)] 
    start_time = datetime.timedelta(hours=H, minutes=M, seconds=S)
    h['simulationstart'] = start_day + start_time
   
    if OPS.readp:
        releasestart, releaseend = [], []
        for i in range(h.numpointspec):
            releasestart.append(h.simulationstart + \
                                 datetime.timedelta(seconds=int(h.ireleasestart[i])))
            releaseend.append(h.simulationstart + \
                               datetime.timedelta(seconds=int(h.ireleaseend[i])))
        h.releasestart = releasestart
        h.releaseend = releaseend[:h.numpointspec]
        h.releasetimes = [b - ((b - a) / 2) for a, b in zip(h.releasestart, h.releaseend)]

    # Add datetime objects for dates
    available_dates_dt = []
    for i in h.available_dates:
        available_dates_dt.append(datetime.datetime(
            int(i[:4]), int(i[4:6]), int(i[6:8]), int(i[8:10]), int(i[10:12]), int(i[12:])))
    h.available_dates_dt = available_dates_dt
    h.first_date = available_dates_dt[0]
    h.last_date = available_dates_dt[-1]
    h.ageclasses = np.array([act - h.simulationstart for act in h.available_dates_dt])
    h.numageclasses = len(h.ageclasses)

    # Add other helpful attributes
    h.nxmax = h.numxgrid
    h.nymax = h.numygrid
    h.nzmax = h.numzgrid
    h.maxspec = h.nspec
    h.maxpoint = h.numpoint
    h.maxageclass = h.numageclasses

    h.area = h.Area  # fix an annoyance
    
    if OPS.readp:
        h.xpoint = h.xp1
        h.ypoint = h.yp1

    # Add release unit derived from kindz
    if 'kindz' not in h.keys():
        h.kindz = [0]
        h.alt_unit = 'unkn.'
    if 3 in h.kindz:
        h.alt_unit = 'hPa'
    elif 2 in h.kindz:
        h.alt_unit = 'm.a.s.l.'
    elif 1 in h.kindz:
        h.alt_unit = 'm.a.g.l.'

    # 
    if h.loutstep > 0:
        h.direction = 'forward'
        h.unit = 'conc'  # could be pptv
        h.plot_unit = 'ppb'
    else:
        h.direction = 'backward'
        h.unit = 'time'
        h.plot_unit = 'ns / kg'  # Not sure about this

    # Units based on Table 1, ACP 2005
    if h.direction == 'forward':
        if h.ind_source == 1:
            if h.ind_receptor == 1:
                h.output_unit = 'ng m-3'
            if h.ind_receptor == 2:
                h.output_unit = 'pptm'
        if h.ind_source == 2:
            if h.ind_receptor == 1:
                h.output_unit = 'ng m-3'
            if h.ind_receptor == 2:
                h.output_unit = 'pptm'
    if h.direction == 'backward':
        if h.ind_source == 1:
            if h.ind_receptor == 1:
                h.output_unit = 's'
            if h.ind_receptor == 2:
                h.output_unit = 's m^3 kg-1'
        if h.ind_source == 2:
            if h.ind_receptor == 1:
                h.output_unit = 's kg m-3'
            if h.ind_receptor == 2:
                h.output_unit = 's'
    
                

    # Add layer thickness
    layerthickness = [h.outheight[0]]
    for i, lh in enumerate(h.outheight[1:]):
        layerthickness.append(lh - h.outheight[i])
    h.layerthickness = layerthickness

    h.options = OPS
    h.fp_version = h.flexpart
    h.junk = junk  # the extra bits that were read... more for debugging


    #print('Read {0} Header: {1}'.format(h.fp_version, filename))

    return h

# BW Compatability
readheader = read_header
readheaderV8 = read_header
readheaderV6 = read_header




########### HELPER FUNCTIONS ##########
class BinaryFile(object):

    """
    
    BinaryFile: A class for accessing data to/from large binary files
   

    The data is meant to be read/write sequentially from/to a binary file.
    One can request to read a piece of data with a specific type and shape
    from it.  Also, it supports the notion of Fortran and C ordered data,
    so that the returned data is always well-behaved (C-contiguous and
    aligned).

    This class is seeking capable.

    :Author:   Francesc Alted
    :Contact:  faltet@pytables.org
    :Created:  2010-03-18
    :Acknowledgment: Funding for the development of this code is provided
         through the Norwegian Research Council VAUUAV project #184724, 2010

    """


    # Common types whose conversion can be accelerated via the struct
    # module
    structtypes = {
        'i1': 'b', 'i2': 'h', 'i4': 'i',
        'f4': 'f', 'f8': 'd',
        }

    def __init__(self, filename, mode="r", order="fortran"):
        """Open the `filename` for write/read binary files.

        The `mode` can be 'r', 'w' or 'a' for reading (default),
        writing or appending.  The file will be created if it doesn't
        exist when opened for writing or appending; it will be
        truncated when opened for writing.  Add a '+' to the mode to
        allow simultaneous reading and writing.

        `order` specifies whether the file is is written in 'fortran'
        or 'c' order.
        """
        self.mode = mode + "b"
        self.file = open(filename, mode=self.mode, buffering=1)
        """The file handler."""
        if order not in ['fortran', 'c']:
            raise ValueError, "order should be either 'fortran' or 'c'."
        self.order = order
        """The order for file ('c' or 'fortran')."""


    def read(self, dtype, shape=(1,)):
        """Read an array of `dtype` and `shape` from current position.

        `shape` must be any tuple made of integers or even () for scalars.

        The current position will be updated to point to the end of
        read data.
        """
        if not isinstance(dtype, np.dtype):
            dtype = np.dtype(dtype)
        if type(shape) is int:
            shape = (shape,)
        if type(shape) is not tuple:
            raise ValueError, "shape must be a tuple"
        length = dtype.itemsize
        rank = len(shape)
        if rank == 1:
            length *= shape[0]
        elif rank > 1:
            length *= np.array(shape).prod()

        # Correct the shape in case dtype is multi-dimensional
        if shape != (1,):
            shape = shape + dtype.shape
        else:
            shape = dtype.shape
        rank = len(shape)

        if shape in (1, (1,)):
            order = "c"
        else:
            order = self.order

        # Read the data from file
        data = self.file.read(length)
        if len(data) < length:
            raise EOFError, "Asking for more data than available in file."

        # Convert read string into a regular array, or scalar
        dts = dtype.base.str[1:]
        if rank == 0:
            if dts[1] == "S":
                data = str(data)
            elif dts in self.structtypes:
                data = struct.unpack(self.structtypes[dts], data)[0]
        else:
            data = np.ndarray(shape=shape, buffer=data, dtype=dtype.base)
            if rank == 0:
                # Retrieve the scalar out of the 0-dim array
                data = data[()]

        if rank > 1:
            # If original data file is in fortran mode, reverse the
            # shape first
            if order == "fortran":
                shape = [i for i in shape[::-1]]
            data = data.reshape(shape)
            # If original data file is in fortran mode, do a transpose.
            # As the shape was reversed previously, we get the original
            # shape again.
            if self.order == "fortran":
                data = data.transpose().copy()
            # Do an additional copy just in case the array is not
            # well-behaved (i.e., it is not aligned or not contiguous).
            elif not data.flags.behaved:
                data = data.copy()
        return data


    def write(self, arr):
        """Write an `arr` to current position.

        The current position will be updated to point to the end of
        written data.
        """
        # Transpose data if case we need to
        if (self.order == "fortran") != (arr.flags.fortran):
            arr = arr.transpose().copy()
        # Write the data to file
        self.file.write(arr.data)


    def seek(self, offset, whence=0):
        """Move to new file position.

        Argument offset is a byte count.  Optional argument whence
        defaults to 0 (offset from start of file, offset should be >=
        0); other values are 1 (move relative to current position,
        positive or negative), and 2 (move relative to end of file,
        usually negative, although many platforms allow seeking beyond
        the end of a file).  If the file is opened in text mode, only
        offsets returned by tell() are legal.  Use of other offsets
        causes undefined behavior.
        """
        self.file.seek(offset, whence)


    def tell(self):
        "Returns current file position, an integer (may be a long integer)."
        return self.file.tell()


    def flush(self):
        "Flush buffers to file."
        self.file.flush()


    def close(self):
        "End access to file."
        self.file.close()


def closest(num, numlist):
    """ returns the index of the *closest* value in a list """
    # check if we're using datetimes
    dates = False
    if isinstance(num, datetime.datetime):
        dates = True
    if dates:
        num = date2num(num)
        assert isinstance(numlist[0], datetime.datetime), \
               "num is date, numlist must be a list of dates"
        numlist = date2num(numlist)

    return (np.abs(numlist - num)).argmin()



class Structure(dict, object):
    """ A 'fancy' dictionary that provides 'MatLab' structure-like
    referencing. 

    .. warning::
        may be replaced with a pure dict in future release.
        
    """
    def __getattr__(self, attr):
        # Fake a __getstate__ method that returns None
        if attr == "__getstate__":
            return lambda: None
        return self[attr]

    def __setattr__(self, attr, value):
        self[attr] = value

    def __dir__(self):
        """ necessary for Ipython tab-completion """
        return self.keys()

    def set_with_dict(self, D):
        """ set attributes with a dict """
        for k in D.keys():
            self.__setattr__(k, D[k])
    
    def __dir__(self):
        return self.keys()

class Header(Structure):
    """This is the primary starting point for processing FLEXPART output.
    The Header class ( :class:`Structure` ) behaves like a dictionary. 
    It contains all the metadata from the simulation run as read from the
    "header" or "header_nest" binary files from the model output.

    This version is using the BinaryFile class rather than FortFlex. 

    Usage::

        > H = pf.Header(inputpath)
        > H.keys() #provides a list of keys available

    Returns a dictionary

        H = dictionary like object with all the run metadata. TODO: Fill in keys.

        
    Arguments

      .. tabularcolumns::  |l|L|

      ==============        ========================================
      keyword               Description [default]
      ==============        ========================================
      path                  path to the run directory
      headerfile            name of the header file if non standard
      readheader_ops        optional dictionary to pass readheader
      ==============        ========================================

    Arguments for readheader_ops

      .. tabularcolumns::  |l|L|

      =============       ========================================
      keyword             Description [default]
      =============       ========================================
      pathname            FLEXPART run output directory
      readp               read release points 0=no, [1]=y
      nested              nested output True or [False]
      version             version of FLEXPART, default = 'V8'
      =============       ========================================
  
    
    .. note::
        **This function is in development**

        This function is being developed so that there is no dependence on
        using f2py to compile the FortFlex module. It is working using the
        :class:`BinaryFile`, but is notably slower than :class:`FortFlex`. 
        Please report any bugs found.

  
    """


    def __init__(self, path=None, headerfile=None, version='V8', **readheader_ops):
        """

        
        """
        try:
            h = read_header(path, **readheader_ops)
            self.set_with_dict(h)
            self.lonlat()
            self.version = 'V8'
        except:
            traceback.print_exc()
            raise IOError('''
            Could not set header variables.
            Does the `header` file exist in path?\n{0}'''.format(path))
            
        


    def lonlat(self):
        """ Add longitude and latitude attributes using data from header """
        lons = np.arange(self.outlon0, self.outlon0 + (self.dxout * self.numxgrid), self.dxout)
        lats = np.arange(self.outlat0, self.outlat0 + (self.dyout * self.numygrid), self.dyout)
        self.longitude = lons
        self.latitude = lats

    def read_grid(self, **kwargs):
        """ see :func:`read_grid` """
        self.FD = read_grid(self, **kwargs)

    def fill_backward(self, **kwargs):
        """ see :func:`fill_backward` """
        fill_grids(self, add_attributes=True, **kwargs)

    def add_trajectory(self, **kwargs):
        """ see :func:`read_trajectories` """
        self.trajectory = read_trajectories(self)

    def add_fires(self, **kwargs):
        """ uses the :mod:`emissions` module to read the MODIS hotspot data and
        add it to the header class as a 'fires' attribute.
        
        **This function is only available within NILU.**
        
        """

        from nilu.pflexpart import emissions as em
        self.fires = None
        for day in self.available_dates_dt:
            # day = day[:8]
            firedata = em.MODIS_hotspot(day)
            daily = firedata.daily
            # pdb.set_trace()
            if daily is None:
                continue
            else:
                if self.fires == None:
                    self.fires = daily
                else:

                    self.fires = np.hstack((self.fires, daily)).view(np.recarray)

    def closest_dates(self, dateval, fmt=None, take_set=False):
        """ given an iterable of datetimes, finds the closest dates.
            if passed a list, assumes it is a list of datetimes
            
            if take_set=True, then a set of unique values will be returned.
            This can be used with H.read_grid as the value for time_ret to 
            return only the grids matching the array of times.
            See (e.g. `extract_curtain`).
        """

        try:
            vals = [closest(d, self['available_dates_dt']) for d in dateval]
            if take_set:
                return list(set(vals))
            else:
                return vals

        except IOError:
            print('If dateval is iterable, must contain datetimes')


    def closest_date(self, dateval, fmt=None):
        """ given a datestring or datetime, tries to find the closest date.
            if passed a list, assumes it is a list of datetimes
            
        """

        if isinstance(dateval, str):
            if not fmt:
                if len(dateval) == 8:
                    fmt = '%Y%m%d'
                if len(dateval) == 14:
                    fmt = '%Y%m%d%H%M%S'
                else:
                    raise IOError("no format provided for datestring")
            print("Assuming date format: {0}".format(fmt))
            dateval = datetime.datetime.strptime(dateval, fmt)

        return closest(dateval, self['available_dates_dt'])

