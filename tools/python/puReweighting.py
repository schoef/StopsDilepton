''' PU reweighting function
'''
#Standard imports
import ROOT

# helpers
from StopsDilepton.tools.helpers import getObjFromFile

# Logging
import logging
logger = logging.getLogger(__name__)

def extendHistoTo(h, hc):
    "Extend histo h to nbins of hc"
    res = ROOT.TH1D(h.GetName()+"_extended",h.GetTitle(), hc.GetNbinsX(),hc.GetXaxis().GetXmin(),hc.GetXaxis().GetXmax())
    assert  hc.GetXaxis().GetXmin()==h.GetXaxis().GetXmin() \
            and hc.GetNbinsX()==hc.GetXaxis().GetXmax()-hc.GetXaxis().GetXmin() \
            and h.GetNbinsX()==h.GetXaxis().GetXmax()-h.GetXaxis().GetXmin(), \
            "Error extending histogram! Check axis ranges!"
    res.Reset()
    for i in range(min(hc.GetNbinsX(), h.GetNbinsX())):
        res.SetBinContent(i, h.GetBinContent(i))
    return res

#Define a functor that returns a reweighting-function according to the era
def getReweightingFunction(data="PU_2100_XSecCentral", mc="Spring15"):

    # Data
    fileNameData = "$CMSSW_BASE/src/StopsDilepton/tools/data/puReweightingData/%s.root" % data

    histoData = getObjFromFile(fileNameData, 'pileup')
    histoData.Scale(1./histoData.Integral())
    logger.info("Loaded 'pileup' from data file %s", fileNameData )

    # MC
    if mc=='Spring15':
        from StopsDilepton.tools.puProfiles import spring15 as mcProfile
        logger.info("Loaded Spring15 MC Profile" )
    elif mc=="Fall15":
        mcProfile = extendHistoTo(getObjFromFile("$CMSSW_BASE/src/StopsDilepton/tools/data/puReweightingData/MCProfile_Fall15.root", 'MC'), histoData)
    else:
        raise ValueError( "Don't know about MC PU profile %s" %mc )

    mcProfile.Scale(1./mcProfile.Integral())

    # Create reweighting histo
    reweightingHisto = histoData.Clone( '_'.join(['reweightingHisto', data, mc]) )
    reweightingHisto.Divide(mcProfile)

    # Define reweightingFunc
    def reweightingFunc(nvtx):
        return reweightingHisto.GetBinContent(reweightingHisto.FindBin(nvtx))

    return reweightingFunc
