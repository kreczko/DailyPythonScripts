from rootpy.plotting import Hist, Hist2D
from rootpy.io import root_open
#from rootpy.interactive import wait
from argparse import ArgumentParser
from dps.config.xsection import XSectionConfig
from dps.config.variable_binning import bin_edges_vis, reco_bin_edges_vis
from dps.config.variableBranchNames import branchNames, genBranchNames_particle, genBranchNames_parton
from dps.utils.file_utilities import make_folder_if_not_exists
from math import trunc, exp, sqrt

import ROOT as ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine( 'gErrorIgnoreLevel = 2001;' )

class channel:
    def __init__(self, channelName, treeName, outputDirName):
        self.channelName = channelName
        self.treeName = treeName
        self.outputDirName = outputDirName
        pass
    pass

def calculateTopEtaWeight( lepTopRap, hadTopRap, whichWayToWeight = 1):
    if whichWayToWeight == -1 :
        return max ( (-0.24 * abs(lepTopRap) + 1.24) * (-0.24 * abs(hadTopRap) + 1.24), 0.1 )
    elif whichWayToWeight == 1 :
        return max ( ( 0.24 * abs(lepTopRap) + 0.76) * ( 0.24 * abs(hadTopRap) + 0.76), 0.1 )
    else :
        return 1

def calculateTopPtWeight( lepTopPt, hadTopPt, whichWayToWeight = 1 ):
    if whichWayToWeight == -1 :
        return max ( (-0.0005 * lepTopPt + 1.15 ) * (-0.0005 * hadTopPt + 1.15), 0.15 )
    elif whichWayToWeight == 1 :
        return max ( (0.0005 * lepTopPt + 0.95 ) * (0.0005 * hadTopPt + 0.95), 0.1 )
    else :
        return 1

def calculateTopPtSystematicWeight( lepTopPt, hadTopPt ):
    '''
    Calculating the top pt weight
         ______________            A + B.Pt
    W = / SF(t)SF(tbar) , SF(t) = e

    A = 0.0615
    B = -0.0005
    '''     
    lepTopWeight = ptWeight( lepTopPt )
    hadTopWeight = ptWeight( hadTopPt )
    return sqrt( lepTopWeight * hadTopWeight )
 
def ptWeight( pt ):
    return exp( 0.0615 - 0.0005 * pt ) 
 

def calculateTopPtSystematicWeight( lepTopPt, hadTopPt ):
    lepTopWeight = ptWeight( lepTopPt )
    hadTopWeight = ptWeight( hadTopPt )
    return sqrt( lepTopWeight * hadTopWeight )

def ptWeight( pt ):
    return exp( 0.0615 - 0.0005 * pt )

def getFileName( com, sample, measurementConfig ) :

    fileNames = {
        '13TeV' : {
            'central'           : measurementConfig.ttbar_trees['central'],

            'amcatnlo'          : measurementConfig.ttbar_amc_trees,
            'madgraph'          : measurementConfig.ttbar_madgraph_trees,
            'powhegherwigpp'    : measurementConfig.ttbar_powhegherwigpp_trees,


            'ueup'              : measurementConfig.ttbar_ueup_trees,
            'uedown'            : measurementConfig.ttbar_uedown_trees,
            'isrup'             : measurementConfig.ttbar_isrup_trees,
            'isrdown'           : measurementConfig.ttbar_isrdown_trees,
            'fsrup'             : measurementConfig.ttbar_fsrup_trees,
            'fsrdown'           : measurementConfig.ttbar_fsrdown_trees,

            'massdown'          : measurementConfig.ttbar_mtop1695_trees,
            'massup'            : measurementConfig.ttbar_mtop1755_trees,

            'jesdown'           : measurementConfig.ttbar_jesdown_trees,
            'jesup'             : measurementConfig.ttbar_jesup_trees,
            'jerdown'           : measurementConfig.ttbar_jerdown_trees,
            'jerup'             : measurementConfig.ttbar_jerup_trees,

            'bjetdown'          : measurementConfig.ttbar_trees['central'],
            'bjetup'            : measurementConfig.ttbar_trees['central'],
            'lightjetdown'      : measurementConfig.ttbar_trees['central'],
            'lightjetup'        : measurementConfig.ttbar_trees['central'],

            'leptondown'        : measurementConfig.ttbar_trees['central'],
            'leptonup'          : measurementConfig.ttbar_trees['central'],
            'pileupUp'          : measurementConfig.ttbar_trees['central'],
            'pileupDown'        : measurementConfig.ttbar_trees['central'],

            'ElectronEnUp'      : measurementConfig.ttbar_trees['central'],
            'ElectronEnDown'    : measurementConfig.ttbar_trees['central'],
            'MuonEnUp'          : measurementConfig.ttbar_trees['central'],
            'MuonEnDown'        : measurementConfig.ttbar_trees['central'],
            'TauEnUp'           : measurementConfig.ttbar_trees['central'],
            'TauEnDown'         : measurementConfig.ttbar_trees['central'],
            'UnclusteredEnUp'   : measurementConfig.ttbar_trees['central'],
            'UnclusteredEnDown' : measurementConfig.ttbar_trees['central'],

            'topPtSystematic'   : measurementConfig.ttbar_trees['central'],

        },
    }

    return fileNames[com][sample]

channels = [
    channel( 'ePlusJets', 'rootTupleTreeEPlusJets', 'electron'),
    channel( 'muPlusJets', 'rootTupleTreeMuPlusJets', 'muon'),
]



def parse_arguments():
    parser = ArgumentParser(__doc__)
    parser.add_argument('--topPtReweighting', 
        dest='applyTopPtReweighting', 
        type=int, 
        default=0 
    )
    parser.add_argument('--topEtaReweighting', 
        dest='applyTopEtaReweighting', 
        type=int, 
        default=0 
    )
    parser.add_argument('-c', '--centreOfMassEnergy', 
        dest='centreOfMassEnergy', 
        type=int, 
        default=13 
    )
    parser.add_argument('--pdfWeight', 
        type=int, 
        dest='pdfWeight', 
        default=-1 
    )
    parser.add_argument('--muFmuRWeight', 
        type=int, 
        dest='muFmuRWeight', 
        default=-1 
    )
    parser.add_argument('--alphaSWeight', 
        type=int, 
        dest='alphaSWeight', 
        default=-1 
    )
    parser.add_argument('--matchingWeight', 
        type=int, 
        dest='matchingWeight', 
        default=-1 
    )
    parser.add_argument('--nGeneratorWeights', 
        type=int, 
        dest='nGeneratorWeights', 
        default=1 
    )
    parser.add_argument('-s', '--sample', 
        dest='sample', 
        default='central'
    )
    parser.add_argument('-d', '--debug', 
        action='store_true', 
        dest='debug', 
        default=False
    )
    parser.add_argument('-n', 
        action='store_true', 
        dest='donothing', 
        default=False
    )
    parser.add_argument('-e', 
        action='store_true', 
        dest='extraHists', 
        default=False
    )
    parser.add_argument('-f',
        action='store_true', 
        dest='fineBinned', 
        default=False
    )
    args = parser.parse_args()
    return args

def main():
    args = parse_arguments()

    measurement_config = XSectionConfig( args.centreOfMassEnergy )

    # Input file name
    file_name = 'crap.root'
    if int(args.centreOfMassEnergy) == 13:
        file_name = getFileName('13TeV', args.sample, measurement_config)
    else:
        print "Error: Unrecognised centre of mass energy."

    pdfWeight    = args.pdfWeight
    muFmuRWeight = args.muFmuRWeight
    alphaSWeight = args.alphaSWeight
    matchingWeight = args.matchingWeight

    # Output file name
    outputFileName = 'crap.root'
    outputFileDir = 'unfolding/%sTeV/' % args.centreOfMassEnergy
    make_folder_if_not_exists(outputFileDir)
   
    energySuffix = '%sTeV' % ( args.centreOfMassEnergy )

    if args.applyTopEtaReweighting != 0:
        if args.applyTopEtaReweighting == 1:
            outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_withTopEtaReweighting_up.root' % energySuffix
        elif args.applyTopEtaReweighting == -1:
            outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_withTopEtaReweighting_down.root' % energySuffix
    elif args.applyTopPtReweighting:
        if args.applyTopPtReweighting == 1:
            outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_withTopPtReweighting_up.root' % energySuffix
        elif args.applyTopPtReweighting == -1:
            outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_withTopPtReweighting_down.root' % energySuffix
    elif muFmuRWeight == 1:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_1muR2muF.root' % ( energySuffix )
    elif muFmuRWeight == 2:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_1muR05muF.root' % ( energySuffix )
    elif muFmuRWeight == 3:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_2muR1muF.root' % ( energySuffix )
    elif muFmuRWeight == 4:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_2muR2muF.root' % ( energySuffix )
    elif muFmuRWeight == 6:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_05muR1muF.root' % ( energySuffix )
    elif muFmuRWeight == 8:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_05muR05muF.root' % ( energySuffix )

    elif matchingWeight == 9:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_matching_down.root' % ( energySuffix )
    elif matchingWeight == 18:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_matching_up.root' % ( energySuffix )
    elif matchingWeight >= 0:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_matchingWeight_%i.root' % ( energySuffix, matchingWeight )

    elif alphaSWeight == 0:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_alphaS_down.root' % ( energySuffix )
    elif alphaSWeight == 1:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_alphaS_up.root' % ( energySuffix )
    elif pdfWeight >= 0 and pdfWeight <= 99:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric_pdfWeight_%i.root' % ( energySuffix, pdfWeight )
    elif args.sample != 'central':
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_%s_asymmetric.root' % ( energySuffix, args.sample  )
    elif args.fineBinned :
        outputFileName = outputFileDir+'/unfolding_TTJets_%s.root' % ( energySuffix  )
    else:
        outputFileName = outputFileDir+'/unfolding_TTJets_%s_asymmetric.root' % energySuffix

    with root_open( file_name, 'read' ) as f, root_open( outputFileName, 'recreate') as out:

            # Get the tree
            treeName = "TTbar_plus_X_analysis/Unfolding/Unfolding"
            if args.sample == "jesup":
                treeName += "_JESUp"
            elif args.sample == "jesdown":
                treeName += "_JESDown"
            elif args.sample == "jerup":
                treeName += "_JERUp"
            elif args.sample == "jerdown":
                treeName += "_JERDown"

            tree = f.Get(treeName)
            nEntries = tree.GetEntries()

            # For variables where you want bins to be symmetric about 0, use abs(variable) (but also make plots for signed variable)
            allVariablesBins = bin_edges_vis.copy()
            for variable in bin_edges_vis:
                if 'Rap' in variable:
                    allVariablesBins['abs_%s' % variable] = [0,bin_edges_vis[variable][-1]]

            recoVariableNames = {}
            genVariable_particle_names = {}
            genVariable_parton_names = {}
            histograms = {}
            outputDirs = {}

            for variable in allVariablesBins:
                if args.debug and variable != 'HT' : continue
                if args.sample in measurement_config.met_specific_systematics \
                and variable in measurement_config.variables_no_met:
                    continue

                outputDirs[variable] = {}
                histograms[variable] = {}

                #
                # Variable names
                #
                recoVariableName = branchNames[variable]
                sysIndex = None
                if variable in ['MET', 'ST', 'WPT']:
                    if args.sample == "jerup":
                        recoVariableName += '_METUncertainties'
                        sysIndex = 0
                    elif args.sample == "jerdown":
                        recoVariableName+= '_METUncertainties'
                        sysIndex = 1
                    elif args.sample == "jesup":
                        recoVariableName += '_METUncertainties'
                        sysIndex = 2
                    elif args.sample == "jesdown":
                        recoVariableName += '_METUncertainties'
                        sysIndex = 3
                    # Dont need this?
                    elif args.sample in measurement_config.met_systematics:
                        recoVariableName += '_METUncertainties'
                        sysIndex = measurement_config.met_systematics[args.sample]

                genVariable_particle_name = None
                genVariable_parton_name = None
                if variable in genBranchNames_particle:
                    genVariable_particle_name = genBranchNames_particle[variable]
                if variable in genBranchNames_parton:
                    genVariable_parton_name = genBranchNames_parton[variable]

                recoVariableNames[variable] = recoVariableName
                genVariable_particle_names[variable] = genVariable_particle_name
                genVariable_parton_names[variable] = genVariable_parton_name 

                for channel in channels:
                    # Make dir in output file
                    outputDirName = variable+'_'+channel.outputDirName
                    outputDir = out.mkdir(outputDirName)
                    outputDirs[variable][channel.channelName] = outputDir

                    #
                    # Book histograms
                    #
                    # 1D histograms
                    histograms[variable][channel.channelName] = {}
                    h = histograms[variable][channel.channelName]
                    h['truth'] = Hist( allVariablesBins[variable], name='truth')
                    h['truthVis'] = Hist( allVariablesBins[variable], name='truthVis')
                    h['truth_parton'] = Hist( allVariablesBins[variable], name='truth_parton')                
                    h['measured'] = Hist( reco_bin_edges_vis[variable], name='measured')
                    h['measuredVis'] = Hist( reco_bin_edges_vis[variable], name='measuredVis')
                    h['measured_without_fakes'] = Hist( reco_bin_edges_vis[variable], name='measured_without_fakes')
                    h['measuredVis_without_fakes'] = Hist( reco_bin_edges_vis[variable], name='measuredVis_without_fakes')
                    h['fake'] = Hist( reco_bin_edges_vis[variable], name='fake')
                    h['fakeVis'] = Hist( reco_bin_edges_vis[variable], name='fakeVis')
                    # 2D histograms
                    h['response'] = Hist2D( reco_bin_edges_vis[variable], allVariablesBins[variable], name='response')
                    h['response_without_fakes'] = Hist2D( reco_bin_edges_vis[variable], allVariablesBins[variable], name='response_without_fakes')
                    h['responseVis_without_fakes'] = Hist2D( reco_bin_edges_vis[variable], allVariablesBins[variable], name='responseVis_without_fakes')
                    h['response_parton'] = Hist2D( reco_bin_edges_vis[variable], allVariablesBins[variable], name='response_parton')
                    h['response_without_fakes_parton'] = Hist2D( reco_bin_edges_vis[variable], allVariablesBins[variable], name='response_without_fakes_parton')

                    if args.fineBinned:
                        minVar = trunc( allVariablesBins[variable][0] )
                        maxVar = trunc( max( tree.GetMaximum(genVariable_particle_names[variable]), tree.GetMaximum( recoVariableNames[variable] ) ) * 1.2 )
                        nBins = int(maxVar - minVar)
                        if variable is 'lepton_eta' or variable is 'bjets_eta':
                            maxVar = 2.5
                            minVar = -2.5
                            nBins = 1000
                        elif 'abs' in variable and 'eta' in variable:
                            maxVar = 3.0
                            minVar = 0.
                            nBins = 1000
                        elif 'Rap' in variable:
                            maxVar = 3.0
                            minVar = -3.0
                            nBins = 1000
                        elif 'NJets' in variable:
                            maxVar = 20.5
                            minVar = 3.5
                            nBins = 17

                        h['truth'] = Hist( nBins, minVar, maxVar, name='truth')
                        h['truthVis'] = Hist( nBins, minVar, maxVar, name='truthVis')
                        h['truth_parton'] = Hist( nBins, minVar, maxVar, name='truth_parton')
                        h['measured'] = Hist( nBins, minVar, maxVar, name='measured')
                        h['measuredVis'] = Hist( nBins, minVar, maxVar, name='measuredVis')
                        h['measured_without_fakes'] = Hist( nBins, minVar, maxVar, name='measured_without_fakes')
                        h['measuredVis_without_fakes'] = Hist( nBins, minVar, maxVar, name='measuredVis_without_fakes')
                        h['fake'] = Hist( nBins, minVar, maxVar, name='fake')
                        h['fakeVis'] = Hist( nBins, minVar, maxVar, name='fakeVis')
                        h['response'] = Hist2D( nBins, minVar, maxVar, nBins, minVar, maxVar, name='response')
                        h['response_without_fakes'] = Hist2D( nBins, minVar, maxVar, nBins, minVar, maxVar, name='response_without_fakes')
                        h['responseVis_without_fakes'] = Hist2D( nBins, minVar, maxVar, nBins, minVar, maxVar, name='responseVis_without_fakes')

                        h['response_parton'] = Hist2D( nBins, minVar, maxVar, nBins, minVar, maxVar, name='response_parton')
                        h['response_without_fakes_parton'] = Hist2D( nBins, minVar, maxVar, nBins, minVar, maxVar, name='response_without_fakes_parton')

                    # Some interesting histograms
                    h['puOffline'] = Hist( 20, 0, 2, name='puWeights_offline')
                    h['eventWeightHist'] = Hist( 100, -2, 2, name='eventWeightHist')                    
                    h['genWeightHist'] = Hist( 100, -2, 2, name='genWeightHist')
                    h['offlineWeightHist'] = Hist( 100, -2, 2, name='offlineWeightHist')
 
                    h['phaseSpaceInfoHist'] = Hist( 10, 0, 1, name='phaseSpaceInfoHist')


            # Counters for studying phase space
            nVis            = {c.channelName : 0 for c in channels}
            nVisNotOffline  = {c.channelName : 0 for c in channels}
            nOffline        = {c.channelName : 0 for c in channels}
            nOfflineNotVis  = {c.channelName : 0 for c in channels}
            nFull           = {c.channelName : 0 for c in channels}
            nOfflineSL      = {c.channelName : 0 for c in channels}

            n=0
            # Event Loop
            # for event, weight in zip(tree,weightTree):
            for event in tree:
                branch = event.__getattr__
                n+=1
                if not n%100000: print 'Processing event %.0f Progress : %.2g %%' % ( n, float(n)/nEntries*100 )
                # if n == 10000: break
                # # #
                # # # Weights and selection
                # # #

                # Pileup weight
                # Don't apply if calculating systematic
                pileupWeight = event.PUWeight
                # print event.PUWeight,event.PUWeight_up,event.PUWeight_down
                if args.sample == "pileupUp":
                    pileupWeight = event.PUWeight_up
                elif args.sample == "pileupDown":
                    pileupWeight = event.PUWeight_down

                # Generator level weight
                genWeight = event.EventWeight * measurement_config.luminosity_scale

                # Lepton weight
                leptonWeight = event.LeptonEfficiencyCorrection

                if args.sample == 'leptonup':
                    leptonWeight = event.LeptonEfficiencyCorrectionUp
                elif args.sample == 'leptondown':
                    leptonWeight = event.LeptonEfficiencyCorrectionDown

                # B Jet Weight
                bjetWeight = event.BJetWeight
                if args.sample == "bjetup":
                    bjetWeight = event.BJetUpWeight
                elif args.sample == "bjetdown":
                    bjetWeight = event.BJetDownWeight
                elif args.sample == "lightjetup":
                    bjetWeight = event.LightJetUpWeight
                elif args.sample == "lightjetdown":
                    bjetWeight = event.LightJetDownWeight

                # Top pt systematic weight
                topPtSystematicWeight = 1
                if args.sample == 'topPtSystematic':
                    topPtSystematicWeight = calculateTopPtSystematicWeight( branch('lepTopPt_parton'), branch('hadTopPt_parton'))

                # Offline level weights
                offlineWeight = event.EventWeight * measurement_config.luminosity_scale
                offlineWeight *= pileupWeight
                offlineWeight *= bjetWeight
                # offlineWeight *= leptonWeight
                offlineWeight *= topPtSystematicWeight
                genWeight *= topPtSystematicWeight
                
                # Generator weight
                # Scale up/down, pdf
                if pdfWeight >= 0:
                    genWeight *= branch('pdfWeight_%i' % pdfWeight)
                    offlineWeight *= branch('pdfWeight_%i' % pdfWeight)
                    pass


                if muFmuRWeight >= 0:
                    genWeight *= branch('muFmuRWeight_%i' % muFmuRWeight)
                    offlineWeight *= branch('muFmuRWeight_%i' % muFmuRWeight)
                    pass

                if alphaSWeight == 0 or alphaSWeight == 1:
                    genWeight *= branch('alphaSWeight_%i' % alphaSWeight)
                    offlineWeight *= branch('alphaSWeight_%i' % alphaSWeight)
                    pass

                if matchingWeight >= 0:
                    genWeight *= branch('matchingWeight_%i' % matchingWeight)
                    offlineWeight *= branch('matchingWeight_%i' % matchingWeight)
                    pass

                if args.applyTopPtReweighting != 0:
                    ptWeight = calculateTopPtWeight( branch('lepTopPt_parton'), branch('hadTopPt_parton'), args.applyTopPtReweighting)
                    offlineWeight *= ptWeight
                    genWeight *= ptWeight
                
                if args.applyTopEtaReweighting != 0:
                    etaWeight = calculateTopEtaWeight( branch('lepTopRap_parton'), branch('hadTopRap_parton'), args.applyTopEtaReweighting)
                    offlineWeight *= etaWeight
                    genWeight *= etaWeight

                for channel in channels:
                    # Generator level selection
                    genSelection = ''
                    genSelectionVis = ''
                    if channel.channelName is 'muPlusJets' :
                        genSelection = event.isSemiLeptonicMuon == 1
                        genSelectionVis = event.passesGenEventSelection == 1
                    elif channel.channelName is 'ePlusJets' :
                        genSelection = event.isSemiLeptonicElectron == 1
                        genSelectionVis = event.passesGenEventSelection == 1

                    # Offline level selection
                    offlineSelection = 0

                    if channel.channelName is 'muPlusJets' :
                        offlineSelection = int(event.passSelection) == 1
                    elif channel.channelName is 'ePlusJets' :               
                        offlineSelection = int(event.passSelection) == 2

                    # Fake selection
                    fakeSelection = offlineSelection and not genSelection
                    fakeSelectionVis = offlineSelection and not genSelectionVis

                    # Phase space info
                    if genSelection:
                        nFull[channel.channelName] += genWeight
                        if offlineSelection:
                            nOfflineSL[channel.channelName] += genWeight
                    if genSelectionVis:
                        nVis[channel.channelName] += genWeight
                        if not offlineSelection:
                            nVisNotOffline[channel.channelName] += genWeight
                    if offlineSelection:
                        nOffline[channel.channelName] += offlineWeight
                        if not genSelectionVis:
                            nOfflineNotVis[channel.channelName] += offlineWeight

                    for variable in allVariablesBins:
                        if args.debug and variable != 'HT' : continue
                        if args.sample in measurement_config.met_specific_systematics and \
                        variable in measurement_config.variables_no_met:
                            continue

                        # # #
                        # # # Variable to plot
                        # # #
                        recoVariable = branch(recoVariableNames[variable])
                        if variable in ['MET', 'ST', 'WPT'] and \
                        sysIndex != None and ( offlineSelection or fakeSelection or fakeSelectionVis ) :
                            recoVariable = recoVariable[sysIndex]
                        
                        if 'abs' in variable:
                            recoVariable = abs(recoVariable)

                        # With TUnfold, reco variable never goes in the overflow (or underflow)
                        # if recoVariable > allVariablesBins[variable][-1]:
                        #     print 'Big reco variable : ',recoVariable
                        #     print 'Setting to :',min( recoVariable, allVariablesBins[variable][-1] - 0.000001 )
                        if not args.fineBinned:
                            recoVariable = min( recoVariable, allVariablesBins[variable][-1] - 0.000001 )
                        genVariable_particle = branch(genVariable_particle_names[variable])
                        if 'abs' in variable:
                            genVariable_particle = abs(genVariable_particle)
                        # #
                        # # Fill histograms
                        # #
                        histogramsToFill = histograms[variable][channel.channelName]
                        if not args.donothing:

                            if genSelection:
                                histogramsToFill['truth'].Fill( genVariable_particle, genWeight)
                            if genSelectionVis:
                                histogramsToFill['truthVis'].Fill( genVariable_particle, genWeight)
                            if offlineSelection:
                                histogramsToFill['measured'].Fill( recoVariable, offlineWeight)
                                histogramsToFill['measuredVis'].Fill( recoVariable, offlineWeight)
                                if genSelectionVis :
                                    histogramsToFill['measuredVis_without_fakes'].Fill( recoVariable, offlineWeight)
                                if genSelection:
                                    histogramsToFill['measured_without_fakes'].Fill( recoVariable, offlineWeight)
                                histogramsToFill['response'].Fill( recoVariable, genVariable_particle, offlineWeight )
                            if offlineSelection and genSelection:
                                histogramsToFill['response_without_fakes'].Fill( recoVariable, genVariable_particle, offlineWeight ) 
                            elif genSelection:
                                histogramsToFill['response_without_fakes'].Fill( allVariablesBins[variable][0]-1, genVariable_particle, genWeight )
                                # if genVariable_particle < 0 : print recoVariable, genVariable_particle
                                # if genVariable_particle < 0 : print genVariable_particle
                            if offlineSelection and genSelectionVis:
                                histogramsToFill['responseVis_without_fakes'].Fill( recoVariable, genVariable_particle, offlineWeight )
                            elif genSelectionVis:
                                histogramsToFill['responseVis_without_fakes'].Fill( allVariablesBins[variable][0]-1, genVariable_particle, genWeight )
                            if fakeSelection:
                                histogramsToFill['fake'].Fill( recoVariable, offlineWeight)
                            if fakeSelectionVis:
                                histogramsToFill['fakeVis'].Fill( recoVariable, offlineWeight)

                            if args.extraHists:
                                if genSelection:
                                    histogramsToFill['eventWeightHist'].Fill(event.EventWeight)
                                    histogramsToFill['genWeightHist'].Fill(genWeight)
                                    histogramsToFill['offlineWeightHist'].Fill(offlineWeight)

            #
            # Output histgorams to file
            #
            for variable in allVariablesBins:
                if args.debug and variable != 'HT' : continue
                if args.sample in measurement_config.met_systematics and variable not in ['MET', 'ST', 'WPT']:
                    continue
                for channel in channels:

                    if nOffline[channel.channelName] != 0 : 
                        # Fill phase space info
                        h = histograms[variable][channel.channelName]['phaseSpaceInfoHist']
                        h.SetBinContent(1, nVisNotOffline[channel.channelName] / nVis[channel.channelName])
                        # h.GetXaxis().SetBinLabel(1, "nVisNotOffline/nVis")

                        h.SetBinContent(2, nOfflineNotVis[channel.channelName] / nOffline[channel.channelName])
                        # h.GetXaxis().SetBinLabel(2, "nOfflineNotVis/nOffline")

                        h.SetBinContent(3, nVis[channel.channelName] / nFull[channel.channelName])
                        # h.GetXaxis().SetBinLabel(3, "nVis/nFull")

                        # Selection efficiency for SL ttbar
                        h.SetBinContent(4, nOfflineSL[channel.channelName] / nFull[channel.channelName])
                        # h.GetXaxis().SetBinLabel(4, "nOfflineSL/nFull")

                        # Fraction of offline that are SL
                        h.SetBinContent(5, nOfflineSL[channel.channelName] / nOffline[channel.channelName])
                        # h.GetXaxis().SetBinLabel(5, "nOfflineSL/nOffline")

                    outputDirs[variable][channel.channelName].cd()
                    for h in histograms[variable][channel.channelName]:
                        histograms[variable][channel.channelName][h].Write()


    with root_open( outputFileName, 'update') as out:
        # Done all channels, now combine the two channels, and output to the same file
        for path, dirs, objects in out.walk():
            if 'electron' in path:
                outputDir = out.mkdir(path.replace('electron','combined'))
                outputDir.cd()
                for h in objects:
                    h_e = out.Get(path+'/'+h)
                    h_mu = out.Get(path.replace('electron','muon')+'/'+h)
                    h_comb = (h_e + h_mu).Clone(h)
                    h_comb.Write()
                pass
            pass
        pass

if __name__ == '__main__':
    main()
