'''
Created on 19 Jan 2013

@author: kreczko
'''
from rootpy.logger import logging
from rootpy.io import File
from ROOT import gROOT
gcd = gROOT.cd
from config.summations_common import b_tag_bins_inclusive, b_tag_summations
from config.summations_common import b_tag_bins_exclusive

def get_histogram_from_file( histogram_path, input_file ):
    current_btag, found_btag = find_btag(histogram_path)
    
    root_file = File( input_file )
    get_histogram = root_file.Get
    
    
    if not found_btag or not current_btag in b_tag_summations.keys():
        root_histogram = get_histogram( histogram_path )
        if not is_valid_histogram( root_histogram, histogram_path, input_file ):
            return
    else:
        listOfExclusiveBins = b_tag_summations[current_btag]
        exclhists = []
        
        for excbin in listOfExclusiveBins:
            hist = get_histogram( histogram_path.replace( current_btag, excbin ) )
            if not is_valid_histogram( hist, histogram_path.replace( current_btag, excbin ), input_file ):
                return
            exclhists.append( hist )
        root_histogram = exclhists[0].Clone()
        
        for hist in exclhists[1:]:
            root_histogram.Add( hist )
    
    gcd()
    histogram = None
    # change from float to double
    if root_histogram.TYPE == 'F':
        histogram = root_histogram.empty_clone(type='D')
        histogram.Add(root_histogram)
    else:
        histogram = root_histogram.Clone()
    root_file.Close()
    return histogram 
    
def is_valid_histogram( histogram, histogram_name, file_name ):
    if not histogram:
        logging.error( 'Histogram \n"%s" \ncould not be found in root_file:\n%s' % ( histogram_name, file_name ) )
        return False
    return True

# Reads a single histogram from each given rootFile
# and returns a dictionary with the same naming as 'files'
def get_histogram_dictionary( histogram_path, files = {} ):
    hists = {}
    for sample, file_name in files.iteritems():
        hists[sample] = get_histogram_from_file( histogram_path, file_name )
    return hists

# Reads a list of histograms from each given file
def get_histograms_from_files( histogram_paths = [], files = {}, verbose = False ):
    histograms = {}
    nHistograms = 0
    for sample, input_file in files.iteritems():
        root_file = File( input_file )
        get_histogram = root_file.Get
        histograms[sample] = {}
        
        for histogram_path in histogram_paths:
            current_btag, found_btag = find_btag(histogram_path)
            
            root_histogram = None
            if not found_btag or not current_btag in b_tag_summations.keys():
                root_histogram = get_histogram( histogram_path )
                if not is_valid_histogram( root_histogram, histogram_path, input_file ):
                    return
            else:
                listOfExclusiveBins = b_tag_summations[current_btag]
                exclhists = []
                
                for excbin in listOfExclusiveBins:
                    hist = get_histogram( histogram_path.replace( current_btag, excbin ) )
                    if not is_valid_histogram( hist, histogram_path.replace( current_btag, excbin ), input_file ):
                        return
                    exclhists.append( hist )
                root_histogram = exclhists[0].Clone()
                
                for hist in exclhists[1:]:
                    root_histogram.Add( hist )
            
            gcd()
            nHistograms += 1
            histograms[sample][histogram_path] = root_histogram.Clone()
            if verbose and nHistograms % 5000 == 0:
                print 'Read', nHistograms, 'histograms'
        root_file.Close()
    return histograms

def get_histogram_info_tuple( histogram_in_path ):
    histogram_name = histogram_in_path.split( '/' )[-1]
    directory = ''.join( histogram_in_path.rsplit( histogram_name, 1 )[:-1] )
    b_tag_bin = histogram_name.split( '_' )[-1]
    
    return directory, histogram_name, b_tag_bin    
        
def set_root_defaults( set_batch = True, msg_ignore_level = 1001 ):
    # set to batch mode (or not)
    gROOT.SetBatch( set_batch )
    # ignore warnings
    gROOT.ProcessLine( 'gErrorIgnoreLevel = %d;' % msg_ignore_level )

def root_mkdir(file_handle, path):
    '''
        Equivalent to mkdir -p but for ROOT files.
        Will create all the directories necessary to complete the given path
        @param file_handle: file handle to an open ROOT file with write acccess
        @param path: the path to be written to the ROOT file
    '''
    file_handle.cd()

    directories = []
    if '/' in path:
        directories = path.split('/')
    else:
        directories = [path]

    current_dir = ''
    for directory in directories:
        if current_dir == '':
            current_dir = directory
        else:
            current_dir = current_dir + '/' + directory
        if root_exists(file_handle, current_dir):
            continue
        file_handle.mkdir(current_dir)

def root_exists(file_handle, path):
    pointer_to_directory = None
    try:
        pointer_to_directory = file_handle.GetDirectory( path )
    except:
        return False
    return not (pointer_to_directory is None)

def find_btag( histogram_path ):
    '''
        function to determine if the histogram path contains a valid b-tag
        multiplicity identifier (as specified in config.summations_common)
        Returns (found b-tag, True) or (default b-tag, False)
    '''
    for b_tag in b_tag_bins_inclusive:
        if b_tag in histogram_path:
            return b_tag, True
    for b_tag in b_tag_bins_exclusive:
        if b_tag in histogram_path:
            return b_tag, True
    return b_tag_bins_inclusive[0], False
