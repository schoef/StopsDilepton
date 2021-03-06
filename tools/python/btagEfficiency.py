''' Implementation of b-tagging reweighting
'''

# Standard imports
import ROOT, pickle, itertools, os
from operator import mul

# Logging
import logging
logger = logging.getLogger(__name__)

#binning in pt and eta
ptBorders = [30, 40, 50, 60, 70, 80, 100, 120, 160, 210, 260, 320, 400, 500, 670]
ptBins = []
etaBins = [[0,0.8], [0.8,1.6], [ 1.6, 2.4]]
for i in range(len(ptBorders)-1):
    ptBins.append([ptBorders[i], ptBorders[i+1]])

ptBins.append([ptBorders[-1], -1])

def toFlavourKey(pdgId):
    if abs(pdgId)==5: return ROOT.BTagEntry.FLAV_B
    if abs(pdgId)==4: return ROOT.BTagEntry.FLAV_C
    return ROOT.BTagEntry.FLAV_UDSG

# get the combinatorical weights for jet efficiency list eff
#Method 1ab
effFile             = '$CMSSW_BASE/src/StopsDilepton/tools/data/btagEfficiencyData/TTJets_DiLepton_comb_2j_2l.pkl'
sfFile           = '$CMSSW_BASE/src/StopsDilepton/tools/data/btagEfficiencyData/CSVv2.csv'
sfFile_FastSim   = '$CMSSW_BASE/src/StopsDilepton/tools/data/btagEfficiencyData/CSV_13TEV_Combined_20_11_2015.csv'

class btagEfficiency:

    @staticmethod
    def getWeightDict_1b(effs, maxMultBTagWeight):
        '''Make Weight dictionary for jets
        '''
        zeroTagWeight = 1.

        for e in effs:
            zeroTagWeight*=(1-e)

        tagWeight={}
        for i in range(min(len(effs), maxMultBTagWeight)+1):
            tagWeight[i]=zeroTagWeight
            twfSum = 0.
            for tagged in itertools.combinations(effs, i):
                twf=1.
                for fac in [x/(1-x) for x in tagged]:
                    twf*=fac
                twfSum+=twf
            tagWeight[i]*=twfSum

        for i in range(maxMultBTagWeight+1):
            if not tagWeight.has_key(i):
                tagWeight[i] = 0.

        return tagWeight

    def getBTagSF_1a(self, var, bJets, nonBJets):
        if var not in self.btagWeightNames:
            raise ValueError( "Don't know what to do with b-tag variation %s" %var )
        if var != 'MC':
                ref = reduce(mul, [j['beff']['MC'] for j in bJets] + [1-j['beff']['MC'] for j in nonBJets], 1 )
                return reduce(mul, [j['beff'][var] for j in bJets] + [1-j['beff'][var] for j in nonBJets], 1 )/ref


    def __init__(self,  WP = ROOT.BTagEntry.OP_MEDIUM, fastSim = False):

        # Whether or not FS SF are to be used
        self.fastSim=fastSim

        # All btag weight names per jet
        self.btagWeightNames = ['MC', 'SF', 'SF_b_Down', 'SF_b_Up', 'SF_l_Down', 'SF_l_Up']
        if self.fastSim:
            self.btagWeightNames += [ 'SF_FS_Up', 'SF_FS_Down']

        # Input files
        self.scaleFactorFile = sfFile
        self.scaleFactorFileFS = sfFile_FastSim
        self.mcEfficiencyFile = effFile

        logger.info ( "Loading scale factors from %s", os.path.expandvars(self.scaleFactorFile) )
        self.calib = ROOT.BTagCalibration("csvv2", os.path.expandvars(self.scaleFactorFile) )

        # Get readers
        self.readerMuUp        = ROOT.BTagCalibrationReader(self.calib, WP, "mujets", "up")
        self.readerMuCentral   = ROOT.BTagCalibrationReader(self.calib, WP, "mujets", "central")
        self.readerMuDown      = ROOT.BTagCalibrationReader(self.calib, WP, "mujets", "down")
        self.readerCombUp      = ROOT.BTagCalibrationReader(self.calib, WP, "comb", "up")
        self.readerCombCentral = ROOT.BTagCalibrationReader(self.calib, WP, "comb", "central")
        self.readerCombDown    = ROOT.BTagCalibrationReader(self.calib, WP, "comb", "down")
        if fastSim:
            logger.info( "Loading FullSim/FastSim scale factors from %s", os.path.expandvars( self.scaleFactorFileFS ) )
            self.calibFS = ROOT.BTagCalibration("csv", os.path.expandvars( self.scaleFactorFileFS ) )
            self.readerFSCentral     = ROOT.BTagCalibrationReader(self.calibFS, WP, "fastsim", "central")
            self.readerFSUp          = ROOT.BTagCalibrationReader(self.calibFS, WP, "fastsim", "up")
            self.readerFSDown        = ROOT.BTagCalibrationReader(self.calibFS, WP, "fastsim", "down")

        # Load MC efficiency
        logger.info( "Loading MC efficiency %s", os.path.expandvars(self.mcEfficiencyFile) )
        self.mcEff = pickle.load(file(os.path.expandvars(self.mcEfficiencyFile)))

    def getMCEff(self, pdgId, pt, eta):
        ''' Get MC efficiency for jet
        '''
        for ptBin in ptBins:
            if pt>=ptBin[0] and (pt<ptBin[1] or ptBin[1]<0):
                aeta=abs(eta)
                for etaBin in etaBins:
                    if abs(aeta)>=etaBin[0] and abs(aeta)<etaBin[1]:
                        if abs(pdgId)==5:      return  self.mcEff[tuple(ptBin)][tuple(etaBin)]["b"]
                        elif abs(pdgId)==4:    return  self.mcEff[tuple(ptBin)][tuple(etaBin)]["c"]
                        else:                  return  self.mcEff[tuple(ptBin)][tuple(etaBin)]["other"]

        logger.debug( "No MC efficiency for pt %f eta %f pdgId %i", pt, eta, pdgId)
        return 1

    def getSF(self, pdgId, pt, eta):
        if pt<20: raise ValueError( "BTag SF Not implemented below 20 GeV. Got %f"%pt )
        doubleUnc = False
        pt_=pt
        if pt<30:
            pt_=30
            doubleUnc=True
        if pt>=670:
            pt_=669.9
            doubleUnc = True

        sf_fs   = 1 if not self.fastSim else self.readerFSCentral.eval(toFlavourKey(pdgId), eta, pt_)
        sf_fs_u = 1 if not self.fastSim else self.readerFSUp.eval(toFlavourKey(pdgId), eta, pt_)
        sf_fs_d = 1 if not self.fastSim else self.readerFSDown.eval(toFlavourKey(pdgId), eta, pt_)
        if sf_fs == 0:  # never actually happened...just for sanity
            sf_fs = 1
            sf_fs_u = 1
            sf_fs_d = 1
        if abs(pdgId)==5: #SF for b
            sf      = sf_fs*self.readerMuCentral.eval(ROOT.BTagEntry.FLAV_B, eta, pt_)
            sf_b_d  = sf_fs*self.readerMuDown   .eval(ROOT.BTagEntry.FLAV_B, eta, pt_)
            sf_b_u  = sf_fs*self.readerMuUp     .eval(ROOT.BTagEntry.FLAV_B, eta, pt_)
            sf_l_d  = 1.
            sf_l_u  = 1.
        elif abs(pdgId)==4: #SF for c
            sf     = sf_fs*self.readerMuCentral.eval(ROOT.BTagEntry.FLAV_C, eta, pt_)
            sf_b_d = sf_fs*self.readerMuDown .eval(ROOT.BTagEntry.FLAV_C, eta, pt_)
            sf_b_u = sf_fs*self.readerMuUp   .eval(ROOT.BTagEntry.FLAV_C, eta, pt_)
            sf_l_d = 1.
            sf_l_u = 1.
        else: #SF for light flavours
            sf     = sf_fs*self.readerCombCentral.eval(ROOT.BTagEntry.FLAV_UDSG, eta, pt_)
            sf_b_d = 1.
            sf_b_u = 1.
            sf_l_d = sf_fs*self.readerCombDown .eval(ROOT.BTagEntry.FLAV_UDSG, eta, pt_)
            sf_l_u = sf_fs*self.readerCombUp   .eval(ROOT.BTagEntry.FLAV_UDSG, eta, pt_)
        if doubleUnc:
            sf_b_d = sf + 2.*(sf_b_d - sf)
            sf_b_u = sf + 2.*(sf_b_u - sf)
            sf_l_d = sf + 2.*(sf_l_d - sf)
            sf_l_u = sf + 2.*(sf_l_u - sf)
        if self.fastSim:
            return (sf, sf_b_d, sf_b_u, sf_l_d, sf_l_u, sf*sf_fs_u/sf_fs, sf*sf_fs_d/sf_fs)
        else:
            return (sf, sf_b_d, sf_b_u, sf_l_d, sf_l_u)

    def addBTagEffToJet(self, j):
        mcEff = self.getMCEff(j['hadronFlavour'], j['pt'], j['eta'])
        sf =    self.getSF(j['hadronFlavour'], j['pt'], j['eta'])
        if self.fastSim:
            j['beff'] =  {'MC':mcEff, 'SF':mcEff*sf[0], 'SF_b_Down':mcEff*sf[1], 'SF_b_Up':mcEff*sf[2], 'SF_l_Down':mcEff*sf[3], 'SF_l_Up':mcEff*sf[4], 'SF_FS_Up':mcEff*sf[5], 'SF_FS_Down':mcEff*sf[6]}
        else:
            j['beff'] =  {'MC':mcEff, 'SF':mcEff*sf[0], 'SF_b_Down':mcEff*sf[1], 'SF_b_Up':mcEff*sf[2], 'SF_l_Down':mcEff*sf[3], 'SF_l_Up':mcEff*sf[4]}

#Method 1d
#https://twiki.cern.ch/twiki/bin/view/CMS/BTagShapeCalibration
#https://twiki.cern.ch/twiki/bin/view/CMS/BTagSFMethods
sfFile_1d = '$CMSSW_BASE/src/StopsDilepton/tools/data/btagEfficiencyData/ttH_BTV_CSVv2_13TeV_2015D_20151120.csv'
flavourSys_1d = {
    5:{'central', 'up_jes', 'down_jes', 'up_lf', 'down_lf', 'up_hfstats1', 'down_hfstats1', 'up_hfstats2', 'down_hfstats2'},
    4:{'central', 'up_cferr1', 'down_cferr1', 'up_cferr2', 'down_cferr2'},
    0:{'central', 'up_jes', 'down_jes', 'up_hf', 'down_hf', 'up_lfstats1', 'down_lfstats1', 'up_lfstats2', 'down_lfstats2'},
}
from operator import or_

class btagEfficiency_1d:

    def addBTagEffToJet(self, j):
        j['beff'] = {sys: 1. if sys not in flavourSys_1d[abs(j['hadronFlavour'])] else self.readers[sys].eval(toFlavourKey(j['hadronFlavour']), j['eta'], j['pt'], j['btagCSV']) for sys in self.btagWeightNames}

    def __init__(self,  WP = ROOT.BTagEntry.OP_MEDIUM):
        self.btagWeightNames = reduce(or_, flavourSys_1d.values())

        self.scaleFactorFile = sfFile_1d
        logger.info( "Loading scale factors from %s", os.path.expandvars(self.scaleFactorFile) )
        self.calib = ROOT.BTagCalibration("csvv2", os.path.expandvars(self.scaleFactorFile))
        self.readers = {sys: ROOT.BTagCalibrationReader(self.calib, ROOT.BTagEntry.OP_RESHAPING, "iterativefit", sys) for sys in self.btagWeightNames}
