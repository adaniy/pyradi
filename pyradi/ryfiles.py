#  $Id$
#  $HeadURL$

################################################################
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/

# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.

# The Original Code is part of the PyRadi toolkit.

# The Initial Developer of the Original Code is CJ Willers,
# Portions created by CJ Willers are Copyright (C) 2006-2012
# All Rights Reserved.

# Contributor(s): MS Willers.
################################################################
"""
This module provides functions for file input/output. These are all wrapper
functions, based on existing functions in other Python classes. Functions are 
provided to save a two-dimensional array to a text file, load selected columns 
of data from a text file, load a column header line, compact strings to include 
only legal filename characters, and a function from the Python Cookbook to 
recursively match filename patterns.

See the __main__ function for examples of use.

This package was partly developed to provide additional material in support of students 
and readers of the book Electro-Optical System Analysis and Design: A Radiometry 
Perspective,  Cornelius J. Willers, ISBN 9780819495693, SPIE Monograph Volume
PM236, SPIE Press, 2013.  http://spie.org/x648.html?product_id=2021423&origin_id=x646
"""

#prepare so long for Python 3
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

__version__= "$Revision$"
__author__='pyradi team'
__all__=['saveHeaderArrayTextFile', 'loadColumnTextFile', 'loadHeaderTextFile', 'cleanFilename',
         'listFiles','readRawFrames','arrayToLaTex','epsLaTexFigure','read2DLookupTable']

import sys
if sys.version_info[0] > 2:
    print("pyradi is not yet ported to Python 3, because imported modules are not yet ported")
    exit(-1)


from scipy.interpolate import interp1d
import numpy
import os.path, fnmatch
import csv

################################################################
def saveHeaderArrayTextFile(filename,dataArray, header=None,
        comment=None, delimiter=None):
    """Save a numpy array to a file, included header lines.

    This function saves a two-dimensional array to a text file, with
    an optional user-defined header. This functionality will be part of
    numpy 1.7, when released.

    Args:
        | filename (string): name of the output ASCII flatfile.
        | dataArray (np.array[N,M]): a two-dimensional array.
        | header (string): the optional header.
        | comment (string): the symbol used to comment out lines, default value is None.
        | delimiter (string): delimiter used to separate columns, default is whitespace.

    Returns:
        | Nothing.

    Raises:
        | No exception is raised.
    """
    #open required file
    file=open(filename, 'wt')

    #write the header info to the output file
    if (header is not None):
        for line in header.split('\n'):
            file.write(comment+line+'\n')

    #then write the array, using the file handle (and not filename)
    numpy.savetxt(file, dataArray, delimiter=delimiter)
    #neatly close the file
    file.close()


################################################################
def loadColumnTextFile(filename, loadCol=[1],  \
        comment=None, normalize=0, skiprows=0, delimiter=None,\
        abscissaScale=1,ordinateScale=1, abscissaOut=None):
    """Load selected column data from a text file, processing as specified.

    This function loads column data from a text file,
    manipulating the data read in. The individual vector data
    must be given in columns in the file, with the
    abscissa (x-value) in first column (col 0 in Python)
    and any number of ordinate (y-value) vectors in second and
    later columns.

    Note: leave only single separators (e.g. spaces) between columns!
    Also watch out for a single sapce at the start of line.

    Args:
        | filename (string): name of the input ASCII flatfile.
        | loadCol ([int]): the M =len([]) column(s) to be loaded as the ordinate, default value is column 1
        | comment (string): string, the symbol used to comment out lines, default value is None
        | normalize (int): integer, flag to indicate if data must be normalized.
        | skiprows (int): integer, the number of rows to be skipped at the start of the file (e.g. headers)
        | delimiter (string): string, the delimiter used to separate columns, default is whitespace.
        | abscissaScale (float): scale by which abscissa (column 0) must be multiplied
        | ordinateScale (float): scale by which ordinate (column >0) must be multiplied
        | abscissaOut (np.array[N,] or [N,1]): abscissa vector on which output variables are interpolated.

    Returns:
        | (np.array[N,M]): The interpolated, M columns of N rows, processed array.

    Raises:
        | No exception is raised.
    """

    #numpy.loadtxt(fname, dtype=<type 'float'>, comments='#', \
    #   delimiter=None, converters=None, skiprows=0, \
    #   usecols=None, unpack=False, ndmin=0)

    #load first column as well as user-specified column from the
    # given file, scale as prescribed
    abscissa=abscissaScale*numpy.loadtxt(filename, usecols=[0],\
            comments=comment,  skiprows=skiprows, \
            delimiter=delimiter,  unpack=True)
    ordinate = ordinateScale*numpy.loadtxt(filename, \
            usecols=loadCol,comments=comment,skiprows=skiprows,\
            delimiter=delimiter, unpack=True)

    if  abscissaOut is not None:
        #convert to [N, ] array
        abscissaOut=abscissaOut.reshape(-1,)
        #inpterpolate read values with the given inut vec
        f=interp1d(abscissa,  ordinate)
        interpValue=f(abscissaOut)
    else:
        interpValue=ordinate

    # read more than one column, get back into required shape.
    if interpValue.ndim > 2:
        interpValue = interpValue.squeeze().T

    #if read-in values must be normalised.
    if normalize != 0:
        interpValue /= numpy.max(interpValue,axis=0)

    #return in a form similar to input
    return interpValue.reshape(len(loadCol),  -1 ).T


################################################################################
def loadHeaderTextFile(filename, loadCol=[1], comment=None):
    """Loads column data from a text file, using the csv package.

    Using the csv package, loads column header data from a file, from the firstrow.
    Headers must be delimited by commas. The function [LoadColumnTextFile] provides
    more comprehensive capabilties.

    Args:
        | filename (string): the name of the input ASCII flatfile.
        | loadCol ([int]): list of numbers, the column headers to be loaded , default value is column 1
        | comment (string): the symbol to comment out lines

    Returns:
        | [string]: a list with selected column header entries

    Raises:
        | No exception is raised.
    """

    with open(filename, 'rb') as infile:
        #read from CVS file, must be comma delimited
        lstHeader = csv.reader(infile,quoting=csv.QUOTE_ALL)
        #get rid of leading and trailing whitespace
        list=[x.strip() for x in lstHeader.next()]
        #select only those required
        rtnList =[list[i] for i in loadCol ]
        infile.close()

    return rtnList


################################################################
def cleanFilename(sourcestring,  removestring =" %:/,.\\[]"):
    """Clean a string by removing selected characters.

    Creates a legal and 'clean' sourcestring from a string by removing some clutter and illegals.
    A default set is given but the user can override the default string.

    Args:
        | sourcestring (string): the string to be cleaned.
        | removestring (string): remove all these characters from the source.

    Returns:
        | (string): A cleaned-up string.

    Raises:
        | No exception is raised.
    """
    #remove spaces,comma, ":.%/\[]"
    return filter(lambda c: c not in removestring, sourcestring)


################################################################
#lists the files in a directory and subdirectories
#this code is adapted from a recipe in the Python Cookbook
def listFiles(root, patterns='*', recurse=1, return_folders=0, useRegex=False):
    """Lists the files/directories meeting specific requirement

    Searches a directory structure along the specified path, looking
    for files that matches the glob pattern. If specified, the search will
    continue into sub-directories.  A list of matching names is returned.

    Args:
        | root (string): root directory from where the search must take place
        | patterns (string): glob pattern for filename matching
        | recurse (unt): should the search extend to subdirs of root?
        | return_folders (int): should foldernames also be returned?
        | useRegex (bool): should regular expression evaluation be used?

    Returns:
        | A list with matching file/directory names

    Raises:
        | No exception is raised.
    """
    if useRegex:
        import re

    # Expand patterns from semicolon-separated string to list
    pattern_list = patterns.split(';')
    # Collect input and output arguments into one bunch
    class Bunch:
        def __init__(self, **kwds): self.__dict__.update(kwds)
    arg = Bunch(recurse=recurse, pattern_list=pattern_list,
        return_folders=return_folders, results=[])

    def visit(arg, dirname, files):
        # Append to arg.results all relevant files (and perhaps folders)
        for name in files:
            fullname = os.path.normpath(os.path.join(dirname, name))
            if arg.return_folders or os.path.isfile(fullname):
                for pattern in arg.pattern_list:
                    if useRegex:
                        regex = re.compile(pattern)
                        #search returns None is pattern not found
                        if regex.search(name):
                            arg.results.append(fullname)
                            break
                    else:
                        if fnmatch.fnmatch(name, pattern):
                            arg.results.append(fullname)
                            break
        # Block recursion if recursion was disallowed
        if not arg.recurse: files[:]=[]
    os.path.walk(root, visit, arg)
    return arg.results

################################################################
##
def rawFrameToImageFile(image, filename):
    """Writes a single raw image frame to image file.
    The file type must be given, e.g. png or jpg.
    The image need not be scaled beforehand, it is done prior 
    to writing out the image. File types tested with are
    'png','jpg','tiff','eps'.

    Args:
        | image (numpy.ndarray): two-dimensional array representing an image
        | filename (string): name of file to be written to, with extension

    Returns:
        | Nothing

    Raises:
        | No exception is raised.
    """
    #normalise input image (img) data to between 0 and 1
    from scipy import ndimage
    image = image - ndimage.minimum(image)
    image =  image/ndimage.maximum(image)

    # http://scikit-image.org/docs/dev/api/skimage.io.html#imread
    import skimage.io as io
    io.imsave(filename, image) 


################################################################
##
def readRawFrames(fname, rows, cols, vartype, loadFrames=[]):
    """ Constructs a numpy array from data in a binary file with known data-type.

    Args:
        | fname (string): path and filename
        | rows (int): number of rows in frames
        | cols (int): number of columns in frames
        | vartype (numpy.dtype): numpy data type of data to be read
        |                                      int8, int16, int32, int64
        |                                      uint8, uint16, uint32, uint64
        |                                      float16, float32, float64
        | loadFrames ([int]): optional list of frames to load, zero-based , empty list (default) loads all frames

    Returns:
        | frames (int) : number of frames in the returned data set,
        |                      0 if error occurred
        | rawShaped (numpy.ndarray): vartype numpy array of dimensions (frames,rows,cols),
        |                                              None if error occurred

    Raises:
        | No exception is raised.
    """

    frames = 0
    rawShaped = None

    # load all frames in the file

    if not loadFrames:
        try:
            with open(fname, 'rb') as fin:
                data = numpy.fromfile(fin, vartype,-1)

        except IOError:
            #print('  File not found, returning {0} frames'.format(frames))
            return int(frames), rawShaped

    # load only frames requested

    else:
        try:
            framesize = rows * cols;
            lastframe = max(loadFrames)
            data = None

            with open(fname, 'rb') as fin:
                for frame in range(0, lastframe+1, 1):
                    dataframe = numpy.fromfile(fin, vartype,framesize)
                    if frame in loadFrames:
                        if data == None:
                            data = dataframe
                        else:
                            data = numpy.concatenate((data, dataframe))

        except IOError:
            #print('  File not found, returning {0} frames'.format(frames))
            return int(frames), rawShaped

    frames = data.size / (rows * cols)
    sizeCheck = frames * rows * cols

    if sizeCheck == data.size:
        rawShaped = data.reshape(frames, rows ,cols)
        #print('  Returning {0} frames of size {1} x {2} and data type {3} '.format(  \
        #rawShaped.shape[0],rawShaped.shape[1],rawShaped.shape[2],rawShaped.dtype))
    else:
        #print('  Calculated size = {0}, actual size = {1}, returning  {3} frames '.format(sizeCheck,data.size,frames) )
        pass

    return int(frames), rawShaped


################################################################
##
def epsLaTexFigure(filename, epsname, caption, scale, filemode='a'):
    """ Write the code to include an eps graphic as a latex figure.
        The text is added to an existing file.

    Args:
        | fname (string): output path and filename
        | epsname (string): filename/path to eps file
        | caption (string): figure caption
        | scale (double): scale to textwidth [0..1]
        | filemode (string): file open mode (a=append, w=new file)

    Returns:
        | None, writes a file to disk

    Raises:
        | No exception is raised.
    """

    with open(filename, filemode) as outfile:
        outfile.write('\\begin{figure}[tb]\n')
        outfile.write('\\centering\n')
        outfile.write('\\resizebox{{{0}\\textwidth}}{{!}}{{\includegraphics{{eps/{1}}}}}\n'.\
            format(scale,epsname))
        outfile.write('\\caption{{{0}. \label{{fig:{1}}}}}\n'.format(caption,epsname.split('.')[0]))
        outfile.write('\\end{figure}\n')
        outfile.write('\n')
        outfile.write('\n')

################################################################
##
def arrayToLaTex(filename, arr, header=None, leftCol=None,formatstring='%1.4e', filemode='wt'):
    """ Write a numpy array to latex table format in output file.

        The table can contain only the array data (no top header or
        left column side-header), or you can add either or both of the
        top row or side column headers. Leave 'header' or 'leftcol' as
        None is you don't want these.

        The output format of the array data can be specified, i.e.
        scientific notation or fixed decimal point.

    Args:
        | fname (string): output path and filename
        | arr (np.array[N,M]): array with table data
        | header (string): column header in final latex format
        | leftCol ([string]): left column each row, in final latex format
        | formatstring (string): output format precision for array data (see numpy.savetxt)
        | filemode (string): file open mode (a=append, w=new file)

    Returns:
        | None, writes a file to disk

    Raises:
        | No exception is raised.
    """

    #is seems that savetxt does not like unicode strings
    formatstring = formatstring.encode('ascii')

    if leftCol is None:
        numcols = arr.shape[1]
    else:
        numcols = arr.shape[1] + 1

    file=open(filename, filemode)
    file.write('\\begin{{tabular}}{{ {0} }}\n\hline\n'.format('|'+ numcols*'c|'))

    #write the header
    if header is not None:
        # first column for header
        if leftCol is not None:
            file.write('{0} & '.format(leftCol[0]))
        #rest of the header
        file.write('{0}\\\\\hline\n'.format(header))

    #write the array data
    if leftCol is None:
        #then write the array, using the file handle (and not filename)
        numpy.savetxt(file, arr, fmt=formatstring,  delimiter='&',newline='\\\\\n')
    else:
        # first write left col for each row, then array data for that row
        for i,entry in enumerate(leftCol[1:]):
            file.write(entry+'&')
            numpy.savetxt(file, arr[i].reshape(1,-1), fmt=formatstring, delimiter='&',newline='\\\\\n')

    file.write('\hline\n\end{tabular}')
    file.close()


################################################################
##
def read2DLookupTable(filename):
    """ Read a 2D lookup table and extract the data.

        The table has the following format: ::

            line 1: xlabel ylabel title
            line 2: 0 (vector of y (col) abscissa)
            lines 3 and following: (element of x (row) abscissa), followed
            by table data.

        From line/row 3 onwards the first element is the x abscissa value
        followed by the row of data, one point for each y abscissa value.
        The format can depicted as follows: ::

            x-name y-name ordinates-name
            0 y1 y2 y3 y4
            x1 v11 v12 v13 v14
            x2 v21 v22 v23 v24
            x3 v31 v32 v33 v34
            x4 v41 v42 v43 v44
            x5 v51 v52 v53 v54
            x6 v61 v62 v63 v64

        This function reads the file and returns the individual data items.

    Args:
        | fname (string): input path and filename

    Returns:
        | xVec ((np.array[N])): x abscissae
        | yVec ((np.array[M])): y abscissae
        | data ((np.array[N,M])): data corresponding the x,y
        | xlabel (string): x abscissa label
        | ylabel (string): y abscissa label
        | title (string): dataset title

    Raises:
        | No exception is raised.
    """
    import numpy 

    with open(filename,'r') as f:
        lines = f.readlines()
        xlabel, ylabel, title = lines[0].split()
    aArray = numpy.loadtxt(filename, skiprows=1, dtype=float)
    xVec = aArray[1:, 0]
    yVec = aArray[0, 1:] 
    data = aArray[1:, 1:]
    return(xVec, yVec, data, xlabel, ylabel, title)


################################################################
################################################################
##
##

if __name__ == '__init__':
    pass

if __name__ == '__main__':

    import ryplot
    import ryutils

    xVec,yVec,data,xlabel, ylabel, title = read2DLookupTable('data/OTBMLSNavMar15Nov4_10-C1E.txt')
  
    p = ryplot.Plotter(1)
    for azim in [0,18,36]:
        p.plot(1,yVec,data[azim,:],xlabel='Zenith [rad]',ylabel='Irradiance [W/m$^2$]',
            ptitle='3-5 {}m, Altitude 10 m'.format(ryutils.upMu(False)),
            label=['Azim={0:.0f} deg'.format(yVec[azim])])
    p.saveFig('OTBMLSNavMar15Nov4_10-C1E.png')

    print ('Test writing latex format arrays:')
    arr = numpy.asarray([[1.0,2,3],[4,5,6],[7,8,9]])
    arrayToLaTex('arr0.txt', arr)
    arrayToLaTex('arr1.txt', arr, formatstring='%.1f')
    headeronly = 'Col1 & Col2 & Col3'
    arrayToLaTex('arr2.txt', arr, headeronly, formatstring='%.3f')
    header = 'Col 1 & Col 2 & Col 3'
    leftcol = ['XX','Row 1','Row 2','Row 3']
    #with \usepackage{siunitx} you can even do this:
    arrayToLaTex('arr3.txt', arr, header, leftcol, formatstring=r'\num{%.6e}')

    print ('Test writing eps file figure latex fragments:')
    epsLaTexFigure('eps.txt', 'picture.eps', 'This is the caption', 0.75)

    print ('Test writing and reading numpy array to text file, with header:')
    #create a two-dimensional array of 25 rows and 7 columns as an outer product
    twodA=numpy.outer(numpy.arange(0, 5, .2),numpy.arange(1, 8))
    #write this out as a test file
    filename='ryfilestesttempfile.txt'
    saveHeaderArrayTextFile(filename,twodA, header="line 1 header\nline 2 header", \
                       delimiter=' ', comment='%')

    #create a new range to be used for interpolation
    tim=numpy.arange(1, 3, .3).reshape(-1, 1)
    #read the test file and interpolate the selected columns on the new range tim
    # the comment parameter is superfluous, since there are no comments in this file

    print(loadColumnTextFile(filename, [0,  1,  2,  4],abscissaOut=tim,  comment='%').shape)
    print(loadColumnTextFile(filename, [0,  1,  2,  4],abscissaOut=tim,  comment='%'))
    os.remove(filename)

    ##------------------------- samples ----------------------------------------
    # read space separated file containing wavelength in um, then samples.
    # select the samples to be read in and then load all in one call!
    # first line in file contains labels for columns.
    wavelength=numpy.linspace(0.38, 0.72, 350).reshape(-1, 1)
    samplesSelect = [1,2,3,8,10,11]
    samples = loadColumnTextFile('data/colourcoordinates/samples.txt', abscissaOut=wavelength, \
                loadCol=samplesSelect,  comment='%')
    samplesTxt=loadHeaderTextFile('data/colourcoordinates/samples.txt',\
                loadCol=samplesSelect, comment='%')
    #print(samples)
    print(samplesTxt)
    print(samples.shape)
    print(wavelength.shape)

    ##------------------------- plot sample spectra ------------------------------
    smpleplt = ryplot.Plotter(1, 1, 1)
    smpleplt.plot(1, wavelength, samples, "Sample reflectance", r'Wavelength $\mu$m',\
                r'Reflectance', \
                ['r-', 'g-', 'y-','g--', 'b-', 'm-'],samplesTxt,0.5)
    smpleplt.saveFig('SampleReflectance'+'.png')

    ##===================================================
    print ('\nTest CleanFilename function:')
    inString="aa bb%cc:dd/ee,ff.gg\\hh[ii]jj"
    print('{0}\n{1}'.format(inString,cleanFilename(inString) ))
    inString="aa bb%cc:dd/ee,ff.gg\\hh[ii]jj"
    print('{0}\n{1}'.format(inString,cleanFilename(inString, "") ))

    print ('\nTest listFiles function:')
    print(listFiles('./', patterns='*.py', recurse=1, return_folders=1))

    ##------------------------- load frames from binary & show ---------------------------
    import matplotlib.pyplot as plt

    imagefile = 'data/sample.ulong'
    rows = 100
    cols = 100
    vartype = numpy.uint32
    framesToLoad =  [1, 3, 5, 7]
    frames, img = readRawFrames(imagefile, rows, cols, vartype, framesToLoad)

    if frames == len(framesToLoad):

        #first plot using ryplot, using matplotlib
        P = ryplot.Plotter(1, 2, 2,'Sample frames from binary file', figsize=(4, 4))
        P.showImage(1, img[0], 'frame {0}'.format(framesToLoad[0]))
        P.showImage(2, img[1], 'frame {0}'.format(framesToLoad[1]), cmap=plt.cm.autumn)
        P.showImage(3, img[2], 'frame {0}'.format(framesToLoad[2]), cmap=plt.cm. bone)
        P.showImage(4, img[3], 'frame {0}'.format(framesToLoad[3]), cmap=plt.cm.gist_rainbow)
        P.getPlot().show()
        P.saveFig('sample.png', dpi=300)
        print('\n{0} frames of size {1} x {2} and data type {3} read from binary file {4}'.format(  \
        img.shape[0],img.shape[1],img.shape[2],img.dtype, imagefile))

        #now write the raw frames to image files
        type = ['png','jpg','tiff','png']
        for i in range(frames):
            print(i)
            filename = 'rawIm{0}.{1}'.format(i,type[i])
            rawFrameToImageFile(img[i],filename)

    else:
        print('\nNot all frames read from file')

    #######################################################################
    print("Test the glob version of listFiles")
    filelist = listFiles('.', patterns=r"ry*.py", recurse=0, return_folders=0)
    for filename in filelist:
        print('  {0}'.format(filename))

    print("Test the regex version of listFiles")
    filelist = listFiles('.', patterns=r"[a-z]*p[a-z]*\.py[c]*", \
        recurse=0, return_folders=0, useRegex=True)
    for filename in filelist:
        print('  {0}'.format(filename))

    print('module ryfiles done!')