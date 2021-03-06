#!/usr/bin/env python
''' Analysis script for TTG selection (g bbllnunu or g bbjjlnu)
'''
#
# Standard imports and batch mode
#
import ROOT
ROOT.gROOT.SetBatch(True)

from math import sqrt, cos, sin, pi
from RootTools.core.standard import *
from StopsDilepton.tools.user import plot_directory
from StopsDilepton.tools.helpers import deltaPhi


#
# Arguments
# 
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',      nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], help="Log level for logging")
argParser.add_argument('--overwrite',      action='store_true', default=True,        help='overwrite?')
argParser.add_argument('--plot_directory', action='store',      default='TTG')
argParser.add_argument('--selection',      action='store',      default=None)
argParser.add_argument('--isChild',        action='store_true', default=False)
args = argParser.parse_args()


#
# Logger
#
import StopsDilepton.tools.logger as logger
import RootTools.core.logger as logger_rt
logger    = logger.get_logger(   args.logLevel, logFile = None)
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None)

#
# Selections (two leptons with pt > 20 GeV, photon)
#
from StopsDilepton.tools.objectSelection import looseMuIDString,looseEleIDString
def getLooseLeptonString(nMu, nE):
  return looseMuIDString(ptCut=10) + "==" + str(nMu) + "&&" + looseEleIDString(ptCut=10, absEtaCut=2.5) + "==" + str(nE)

def getLeptonString(nMu, nE):
#  return getLooseLeptonString(nMu, nE)
  return "nGoodMuons==" + str(nMu) + "&&nGoodElectrons==" + str(nE)


jetSelection    = "(Sum$(JetGood_pt>30&&abs(JetGood_eta)<2.4&&JetGood_id))>="
bJetSelectionM  = "(Sum$(JetGood_pt>30&&abs(JetGood_eta)<2.4&&JetGood_id&&JetGood_btagCSV>0.890))>="
bJetSelectionL  = "(Sum$(JetGood_pt>30&&abs(JetGood_eta)<2.4&&JetGood_id&&JetGood_btagCSV>0.605))>="
filterCut       = "(Flag_HBHENoiseIsoFilter&&Flag_HBHENoiseFilter&&Flag_CSCTightHaloFilter&&Flag_goodVertices&&Flag_eeBadScFilter&&vetoPassed&&jsonPassed&&weight>0)"

#
# Cuts to iterate over
#
cuts = [
    ("njet2",             jetSelection+"2"),
    ("photon30",          "(1)"),
    ("photon50",          "(1)"),
    ("llgNoZ",            "(1)"),			# Cut implemented in lepton selection
    ("gJetdR",            "(1)"),			# Implenented in otherSelections() method
    ("gLepdR",            "(1)"),			# Implemented in otherSelections() method
    ("btagL",             bJetSelectionL+"1"),
    ("btagM",             bJetSelectionM+"1"),
    ("mll20",             "dl_mass>20"),
    ("met80",             "met_pt_photonEstimated>80"),
    ("metSig5",           "metSig_photonEstimated>5"),
    ("dPhiJet0-dPhiJet1", "cos(met_phi_photonEstimated-JetGood_phi[0])<cos(0.25)&&cos(met_phi_photonEstimated-JetGood_phi[1])<cos(0.25)"),
  ]


#
# Construct prefixes and selectionstring and filter on possible cut combinations
#
import itertools
selectionStrings = {}
for i_comb in reversed( range( len(cuts)+1 ) ):
    for comb in itertools.combinations( cuts, i_comb ):
        presel = [] 
        presel.extend( comb )
        selection = '-'.join([p[0] for p in presel])
        if selection.count("btag") > 1:    continue
        if selection.count("photon") != 1: continue
        if selection.count("njet") != 1:   continue

        if selection.count("dPhiJet0-dPhiJet1") and not selection.count("metSig5"):  continue
        if selection.count("metSig5")           and not selection.count("met80"):    continue
        if selection.count("met80")             and not selection.count("mll20"):    continue
        if selection.count("mll20")             and not selection.count("btag"):     continue
        if selection.count("mll20")             and not selection.count("llgNoZ"):   continue
#        if selection.count("mll20")             and not selection.count("gJetdR"):   continue
#        if selection.count("mll20")             and not selection.count("gLepdR"):   continue

        selectionStrings[selection] = "&&".join( [p[1] for p in presel])

#
# If this is the mother process, launch the childs and exit (I know, this could potententially be dangereous if the --isChild and --selection commands are not given...)
#
if not args.isChild and args.selection is None:
  import os
  os.system("mkdir -p log")
  for selection in selectionStrings:
    command = "./ttG.py --selection=" + selection
    logfile = "log/" + selection + ".log"
    logger.info("Launching " + selection + " on cream02 with child command: " + command)
    os.system("qsub -v command=\"" + command + " --isChild\" -q localgrid@cream02 -o " + logfile + " -e " + logfile + " -l walltime=03:00:00 runPlotsOnCream02.sh")
  logger.info("All jobs launched")
  exit(0)



#
# Make samples, will be searched for in the postProcessing directory
#
#postProcessing_directory = "postProcessed_Fall15_mAODv2/dilepTiny_may2"
from StopsDilepton.samples.cmgTuples_Fall15_mAODv2_25ns_postProcessed import *
from StopsDilepton.samples.cmgTuples_Fall15_mAODv2_25ns_postProcessed_photonSamples import *
from StopsDilepton.samples.cmgTuples_Data25ns_mAODv2_postProcessed import *


#
# Text on the plots
#
def drawObjects( dataMCScale, lumi_scale ):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(11) # align right
    lines = [
      (0.15, 0.95, 'CMS Preliminary'), 
      (0.45, 0.95, 'L=%3.2f fb{}^{-1} (13 TeV) Scale %3.2f'% ( int(lumi_scale*100)/100., dataMCScale ) )
    ]
    return [tex.DrawLatex(*l) for l in lines] 


#
# Read variables and sequences
#
read_variables = ["weight/F" , "l1_eta/F" , "l1_phi/F", "l2_eta/F", "l2_phi/F", "JetGood[pt/F,eta/F,phi/F,btagCSV/F]", "dl_mass/F", "dl_eta/F", "dl_mt2ll_photonEstimated/F", "dl_mt2bb_photonEstimated/F", "dl_mt2blbl_photonEstimated/F",
                  "met_pt_photonEstimated/F", "met_phi_photonEstimated/F",
                  "metSig_photonEstimated/F", "ht/F", "nBTag/I", "nJetGood/I", "mt_photonEstimated/F", "photon_pt/F", "photon_eta/F",  "photon_phi/F", "photonJetdR/F", "photonLepdR/F"]

# Variables only to be read/available for specific samples (i.e. variables only in MC)
TTG.read_variables         = ["photon_genPt/F", "photon_genEta/F"]
TTLep_pow.read_variables   = ["photon_genPt/F"]
TTZtoLLNuNu.read_variables = ["zBoson_genPt/F", "zBoson_genEta/F", "dl_mt2ll/F"]

def photonDeltaR(data, eta, phi):
  return sqrt(deltaPhi(data.photon_phi, phi)**2 + (data.photon_eta - eta)**2)

def makeDeltaR(data):
  data.photonLep1DeltaR     = photonDeltaR(data, data.l1_eta, data.l1_phi)
  data.photonLep2DeltaR     = photonDeltaR(data, data.l2_eta, data.l2_phi)
  data.JetGood_photonDeltaR = [photonDeltaR(data, data.JetGood_eta[i], data.JetGood_phi[i]) for i in range(data.nJetGood)]

# Filter on dR jets and recalculate jet var
def filterJets(data):
  if args.selection.count("gJetdR"): data.goodJetIndices = [i for i in range(data.nJetGood) if data.JetGood_photonDeltaR[i] > 0.3]
  else:                              data.goodJetIndices = [i for i in range(data.nJetGood)]
  data.nJetGood               = len(data.goodJetIndices)
  data.ht                     = sum([data.JetGood_pt[j] for j in data.goodJetIndices])
  data.metSig_photonEstimated = data.met_pt_photonEstimated/sqrt(data.ht) if data.ht !=0 else float('nan')
  data.nBTag                  = len([j for j in data.goodJetIndices if data.JetGood_btagCSV[j] > 0.890])
  data.nBTagLoose             = len([j for j in data.goodJetIndices if data.JetGood_btagCSV[j] > 0.605])
  data.dPhiMetJet             = [cos(data.met_phi_photonEstimated - data.JetGood_phi[j]) for j in data.goodJetIndices]

# Make photonLepdR selection or re-evaluate jet selection after photonJetdR
def otherSelections(data, sample):
  data.passed = True
  if args.selection.count("gLepdR"):
    data.passed = (data.passed and data.photonLep1DeltaR > 0.3 and data.photonLep2DeltaR > 0.3)
  if args.selection.count("gJetdR"):
    if args.selection.count("njet2"):             data.passed = (data.passed and data.nJetGood > 1)
    if args.selection.count("btagL"):             data.passed = (data.passed and data.nBTagLoose > 0)
    if args.selection.count("btagM"):             data.passed = (data.passed and data.nBTag > 0)
    if args.selection.count("metSig5"):           data.passed = (data.passed and data.metSig_photonEstimated > 5)
    if args.selection.count("dPhiJet0-dPhiJet1"): data.passed = (data.passed and max(data.dPhiMetJet[0], data.dPhiMetJet[1]) < cos(0.25))

# Compare different variable types for TTZ vs TTG
def makeCompareVariables(data, sample):
  if sample == TTZtoLLNuNu: 
    data.boson_genPt  = data.zBoson_genPt
    data.boson_genEta = data.zBoson_genEta
    data.mt2ll        = data.dl_mt2ll
  elif sample == TTG:
    data.boson_genPt  = data.photon_genPt
    data.boson_genEta = data.photon_genEta
    data.mt2ll        = data.dl_mt2ll_photonEstimated

sequence = [makeDeltaR, filterJets, otherSelections, makeCompareVariables]


offZ            = "abs(dl_mass-91.1876)>15"
offZ_dlg        = "abs(dlg_mass-91.1876)>15"
mumuSelection   = getLeptonString(2, 0) + "&&isOS&&isMuMu&&HLT_mumuIso&&" + offZ 
mueSelection    = getLeptonString(1, 1) + "&&isOS&&isEMu&&HLT_mue"
eeSelection     = getLeptonString(0, 2) + "&&isOS&&isEE&&HLT_ee_DZ&&" + offZ
photonSelection = "nPhotonGood>0&&photon_eta<2.5&&photon_idCutBased>2&&photon_pt>" + args.selection.split('photon')[1].split('-')[0]

#
# Loop over channels
#
yields     = {}
allPlots   = {}
allModes   = ['mumu','mue','ee']
for index, mode in enumerate(allModes):
  yields[mode] = {}
  if mode=="mumu":
    data_sample     = DoubleMuon_Run2015D
    qcd_sample      = QCD_Mu5 #FIXME
    leptonSelection = mumuSelection + "&&" + offZ_dlg
    leptonSelection_nollg = mumuSelection
  elif mode=="ee":
    data_sample     = DoubleEG_Run2015D
    qcd_sample      = QCD_EMbcToE
    leptonSelection = eeSelection + "&&" + offZ_dlg
    leptonSelection_nollg = eeSelection
  elif mode=="mue":
    data_sample     = MuonEG_Run2015D
    qcd_sample      = QCD_Mu5EMbcToE
    leptonSelection = mueSelection
    leptonSelection_nollg = mueSelection

  if not args.selection.count('llgNoZ'):
    leptonSelection = leptonSelection_nollg

  qcd_sample.name  = "QCD"  # Give same name in all modes such that it combines easily
  data_sample.name = "data"

  data_sample.style = styles.errorStyle( ROOT.kBlack )
  lumi_scale = data_sample.lumi/1000

#  mc = [ diBoson, WJetsToLNu, WZZ, DY_HT_LO, qcd_sample, singleTop, TTLep_pow, TTX, TTG ]
#  mc = [ diBoson, DY_HT_LO, singleTop, TTLep_pow, TTX, TTG ]
  mc = [ WG, ZG, WWG, diBoson, DY_HT_LO, singleTop, TTLep_pow, TTX, TTG ]
  for sample in mc:
    sample.scale = lumi_scale
    sample.style = styles.fillStyle(sample.color)


  stack = Stack(mc, [data_sample])
  data_sample.setSelectionString([filterCut, leptonSelection, photonSelection])
  for sample in mc:
    sample.setSelectionString([leptonSelection, photonSelection])

  # For TTJets, do TTGJets overlap events removal
 # TTJets.setSelectionString(   ["TTGJetsEventType<4", leptonSelection, photonSelection])
  TTLep_pow.setSelectionString(["TTGJetsEventType<4", leptonSelection, photonSelection])
  DY_HT_LO.setSelectionString(["TTGJetsEventType<4", leptonSelection, photonSelection])

  # For comparisons with TTZ, do not use photonSelection, but use leptonSelection such that we probe the neutrino decay component
  TTZtoLLNuNu.setSelectionString([leptonSelection_nollg])


  # Use some defaults
  Plot.setDefaults(stack = stack, weight = (lambda data:data.weight if data.passed else 0), selectionString = selectionStrings[args.selection])
  
  plots = []

  plots.append(Plot(
    name = 'yield', texX = 'yield', texY = 'Number of Events',
    variable = Variable.fromString( "yield/F" ).addFiller(lambda data: 0.5 + index),
    binning=[3, 0, 3],
  ))

  plots.append(Plot(
    texX = 'm(ll) of leading dilepton (GeV)', texY = 'Number of Events / 4 GeV',
    variable = Variable.fromString( "dl_mass/F" ),
    binning=[200/4,0,200],
  ))

  plots.append(Plot(
    texX = 'm(ll#gamma) of leading dilepton and photon (GeV)', texY = 'Number of Events / 4 GeV',
    variable = Variable.fromString( "dlg_mass/F" ),
    binning=[300/4,50,350],
  ))

  plots.append(Plot(
    texX = 'm(ll#gamma) of leading dilepton and photon (GeV)', texY = 'Number of Events / GeV',
    variable = Variable.fromString( "dlg_mass/F" ),
    name = "dlg_mass_zoomed",
    binning=[80, 50, 130],
  ))

  plots.append(Plot(
    texX = 'MT_{2}^{ll} (including #gamma) (GeV)', texY = 'Number of Events / 20 GeV',
    variable = Variable.fromString( "dl_mt2ll_photonEstimated/F" ),
    binning=[300/20,0,300],
  ))

  plots.append(Plot(
    texX = 'MT_{2}^{bb} (including #gamma) (GeV)', texY = 'Number of Events / 20 GeV',
    variable = Variable.fromString( "dl_mt2bb_photonEstimated/F" ),
    binning=[300/20,0,300],
  ))

  plots.append(Plot(
    texX = 'MT_{2}^{blbl} (including #gamma) (GeV)', texY = 'Number of Events / 20 GeV',
    variable = Variable.fromString( "dl_mt2blbl_photonEstimated/F" ),
    binning=[300/20,0,300],
  ))

  plots.append(Plot(
    texX = '#slash{E}_{T} (including #gamma) (GeV)', texY = 'Number of Events / 50 GeV',
    variable = Variable.fromString( "met_pt_photonEstimated/F" ),
    binning=[300/50,0,300],
  ))

  plots.append(Plot(
    texX = '#slash{E}_{T}/#sqrt(H_{T}) (including #gamma) (GeV^{1/2})', texY = 'Number of Events',
    variable = Variable.fromString('metSig_photonEstimated/F').addFiller(lambda data: data.met_pt_photonEstimated/sqrt(data.ht)),
    binning=[15,0,15],
  ))

  plots.append(Plot(
    texX = 'H_{T} (GeV)', texY = 'Number of Events / 30 GeV',
    variable = Variable.fromString( "ht/F" ).addFiller(lambda data: data.ht),
    binning=[510/30,90,600],
  ))

  plots.append(Plot(
    texX = 'Cos(#phi(#slash{E}_{T}, Jet[0]))', texY = 'Number of Events',
    variable = Variable.fromString('cosMetJet0phi/F').addFiller(lambda data: data.dPhiMetJet[0] if data.nJetGood > 0 else -1),
    binning = [10,-1,1], 
  ))

  plots.append(Plot(
    texX = 'Cos(#phi(#slash{E}_{T}, Jet[1]))', texY = 'Number of Events',
    variable = Variable.fromString('cosMetJet1phi/F').addFiller(lambda data: data.dPhiMetJet[1] if data.nJetGood > 1 else -1),
    binning = [10,-1,1], 
  ))

  plots.append(Plot(
    texX = 'p_{T}(leading jet) (GeV)', texY = 'Number of Events / 20 GeV',
    variable = Variable.fromString('jet1pt/F').addFiller(lambda data: data.JetGood_pt[data.goodJetIndices[0]] if data.nJetGood > 0 else -1),
    binning=[500/20,30,530],
  ))

  plots.append(Plot(
    texX = 'p_{T}(2^{nd.} leading jet) (GeV)', texY = 'Number of Events / 20 GeV',
    variable = Variable.fromString('jet2pt/F').addFiller(lambda data: data.JetGood_pt[data.goodJetIndices[1]] if data.nJetGood > 1 else -1),
    binning=[400/20,30,430],
  ))

  plots.append(Plot(
    texX = 'number of medium b-tags (CSVM)', texY = 'Number of Events',
    variable = Variable.fromString('nBTag/I').addFiller(lambda data: data.nBTag),
    binning=[8,0,8],
  ))

  plots.append(Plot(
    texX = 'number of loose b-tags (CSVM)', texY = 'Number of Events',
    variable = Variable.fromString('nBTagLoose/I').addFiller(lambda data: data.nBTagLoose),
    binning=[8,0,8],
  ))

  plots.append(Plot(
    texX = 'number of jets', texY = 'Number of Events',
    variable = Variable.fromString('nJetGood/I').addFiller(lambda data : data.nJetGood),
    binning=[14,0,14],
  ))

  plots.append(Plot(
    texX = '#eta(#gamma)', texY = 'Number of Events',
    variable = Variable.fromString( "photon_eta/F" ).addFiller(lambda data: abs(data.photon_eta)),
    binning=[10, 0, 2.4],
  ))

  plots.append(Plot(
    texX = 'p_{T}(#gamma)', texY = 'Number of Events / 20 GeV',
    variable = Variable.fromString( "photon_pt/F" ),
    binning=[10, 50,250],
  ))

  plots.append(Plot(
    texX = '#phi(#gamma)', texY = 'Number of Events',
    variable = Variable.fromString( "photon_phi/F" ),
    binning=[15,-pi,pi],
  ))

  plots.append(Plot(
    texX = '#Delta R(#gamma, l)', texY = 'Number of Events',
    variable = Variable.fromString( "photonLepdR/F" ),
    binning=[20, 0, 5],
  ))

  plots.append(Plot(
    texX = '#Delta R(#gamma, j)', texY = 'Number of Events',
    variable = Variable.fromString( "photonJetdR/F" ),
    binning=[20, 0, 5],
  ))

  plots.append(Plot(
    texX     = '#Delta R(#gamma, l_{1})', texY = 'Number of Events',
    variable = Variable.fromString("photonLep1DeltaR/F").addFiller(lambda data : data.photonLep1DeltaR),
    binning  = [20, 0, 5]
  ))

  plots.append(Plot(
    texX     = '#Delta R(#gamma, l_{2})', texY = 'Number of Events',
    variable = Variable.fromString("photonLep2DeltaR/F").addFiller(lambda data : data.photonLep2DeltaR),
    binning  = [20, 0, 5]
  ))

  plots.append(Plot(
    texX     = '#Delta R(#gamma, j_{1})', texY = 'Number of Events',
    variable = Variable.fromString("photonJet1DeltaR/F").addFiller(lambda data : data.JetGood_photonDeltaR[data.goodJetIndices[0]] if data.nJetGood > 0 else -1),
    name     = "photonJet1DeltaR",
    binning  = [20, 0, 5]
  ))

  plots.append(Plot(
    texX     = '#Delta R(#gamma, j_{2})', texY = 'Number of Events',
    variable = Variable.fromString("photonJet2DeltaR/F").addFiller(lambda data : data.JetGood_photonDeltaR[data.goodJetIndices[1]] if data.nJetGood > 1 else -1),
    name     = "photonJet2DeltaR",
    binning  = [20, 0, 5]
  ))

  # Some MC only plots, unfortunately this still loops two times over the samples...
  Plot.setDefaults(stack = Stack(TTLep_pow, TTG), weight = (lambda data:data.weight if data.passed else 0), selectionString = selectionStrings[args.selection])

  try:
    os.makedirs(os.path.join(plot_directory, args.plot_directory, mode, args.selection, 'comp'))
  except:
    pass

  plots.append(Plot(
    texX     = '#slash{E}_{T} resolution', texY = 'Normalized units',
    variable = Variable.fromString("met_res/F").addFiller(helpers.uses(lambda data : data.met_pt/data.met_genPt if data.met_pt > 30 else -1, ["met_pt/F","met_genPt/F"])),
    name     = "comp/TTJets_vs_TTGJets-met_res",
    binning  = [20, 0, 2]
  ))

  plots.append(Plot(
    texX     = 'p_{T}(#gamma) resolution', texY = 'Normalized units',
    variable = Variable.fromString("photon_res/F").addFiller(lambda data: data.photon_pt/data.photon_genPt if data.photon_genPt > 0 else -1),
    name     = "comp/TTJets_vs_TTGJets-photon_res",
    binning  = [40, 0.8, 1.2]
  ))
 
  plots.append(Plot(
    texX     = 'MT_{2}^{ll} (including #gamma) (GeV)', texY = 'Normalized units',
    variable = Variable.fromString( "dl_mt2ll_photonEstimated/F" ),
    name     = "comp/TTJets_vs_TTGJets-dl_mt2ll_photonEstimated",
    binning  = [300/20,0,300],
  ))

  plots.append(Plot(
    texX     = 'p_{T}(#gamma)', texY = 'Normalized units',
    variable = Variable.fromString( "photon_pt/F" ),
    name     = "comp/TTJets_vs_TTGJets-photon_pt",
    binning  = [10, 50,250],
  ))

  plots.append(Plot(
    texX     = 'event type', texY = 'Normalized units',
    variable = Variable.fromString( "TTGJetsEventType/I" ),
    name     = "comp/TTJets_vs_TTGJets-eventType",
    binning  = [5, 0, 5],
  ))

  plotting.fill(plots, read_variables = read_variables, sequence = sequence)

  # Get normalization yields from yield histogram
  for plot in plots:
    if plot.name == "yield":
      for i, l in enumerate(plot.histos):
        for j, h in enumerate(l):
          yields[mode][plot.stack[i][j].name] = h.GetBinContent(h.FindBin(0.5+index))
          h.GetXaxis().SetBinLabel(1, "#mu#mu")
          h.GetXaxis().SetBinLabel(2, "e#mu")
          h.GetXaxis().SetBinLabel(3, "ee")

  yields[mode]["MC"] = sum(yields[mode][s.name] for s in mc)
  dataMCScale = yields[mode]["data"]/yields[mode]["MC"] if yields[mode]["MC"] != 0 else float('nan')
  logger.info( "Data/MC Scale: %4.4f Yield MC %4.4f Yield Data %4.4f Lumi-scale %4.4f", dataMCScale, yields[mode]["MC"], yields[mode]["data"], lumi_scale )

  # Some different layout settings for the MC comparison plots
  for plot in plots:
    if plot.name.startswith("comp"):
      for i, l in enumerate(plot.histos):
        for j, h in enumerate(l):
          h.style = styles.lineStyle(plot.stack[i][j].color, 2)

    if plot.name == "comp/TTG_vs_TTZ-boson_genPt_highPt":
      yieldTTZ  = plot.histos[0][0].Integral()
      yieldTTG  = plot.histos[1][0].Integral()
      TTG_scale = yieldTTG/yieldTTZ if yieldTTZ > 0 else 1
      print "yield TTZ: " + str(yieldTTZ)
      print "yield TTG: " + str(yieldTTG)
      print "TTG scale: " + str(TTG_scale)

  for plot in plots:
    if plot.name.startswith("comp/TTG_vs_TTZ"):
      plot.histos[1][0].Scale(1/TTG_scale)

  for plot in plots:
    if not max(l[0].GetMaximum() for l in plot.histos): continue # Empty plot
    plotting.draw(plot, 
        plot_directory = os.path.join(plot_directory, args.plot_directory, mode, args.selection),
        ratio = {'yRange':(0.1,1.9)}, 
        logX = False, logY = False, sorting = False, 
        yRange = (0.003, "auto"),
        scaling = {0:1} if plot.name.startswith("comp/TTJets_vs_TTGJets") else {},
        drawObjects = drawObjects( dataMCScale, lumi_scale ) if not plot.name.startswith("comp/TTG_vs_TTZ") else drawObjects( TTG_scale, lumi_scale),
    )
  allPlots[mode] = plots



# Add yields in channels
yields["all"] = {}
for y in yields[allModes[0]]:
  try:
    yields["all"][y] = sum(yields[mode][y] for mode in allModes)
  except:
    yields["all"][y] = 0
dataMCScale = yields["all"]["data"]/(yields["all"]["MC"])


# Write to tex file
columns = [i.name for i in mc] + ["MC", "data"]
texdir = "tex"
try:
  os.makedirs("./" + texdir)
except:
  pass
with open("./" + texdir + "/" + args.selection + ".tex", "w") as f:
  f.write("&" + " & ".join(columns) + "\\\\ \n")
  for mode in allModes + ["all"]:
    f.write(mode + " & " + " & ".join([ " %12.1f" % yields[mode][i] for i in columns]) + "\\\\ \n")


try:
  os.makedirs(os.path.join(plot_directory, args.plot_directory, "all", args.selection, 'comp'))
except:
  pass
# Add the different channels and plot the sums
for plot in allPlots[allModes[0]]:
  logger.info("Adding " + plot.name + " for mode " + allModes[0] + " to all")
  for mode in allModes[1:]:
    for plot2 in (p for p in allPlots[mode] if p.name == plot.name):
      logger.info("Adding " + plot.name + " for mode " + mode + " to all")
      for i, j in enumerate(list(itertools.chain.from_iterable(plot.histos))):
        for k, l in enumerate(list(itertools.chain.from_iterable(plot2.histos))):
          if i==k:
            j.Add(l)

  if plot.name == "comp/TTG_vs_TTZ-boson_genPt_highPt":
      yieldTTZ  = plot.histos[0][0].Integral()
      yieldTTG  = plot.histos[1][0].Integral()
      TTG_scale = yieldTTG/yieldTTZ if yieldTTZ > 0 else 1
      print "TTG scale: " + str(TTG_scale)


for plot in allPlots[allModes[0]]:
  if plot.name.startswith("comp/TTG_vs_TTZ"):
      plot.histos[1][0].Scale(1/TTG_scale)
  if not plot.name.startswith("comp"): plot.histos[1][0].legendText = "Data 2015 (all channels)"
  plotting.draw(plot,
        plot_directory = os.path.join(plot_directory, args.plot_directory, "all", args.selection),
        ratio = {'yRange':(0.1,1.9)},
        logX = False, logY = False, sorting = False,
        yRange = (0.003, "auto"),
        scaling = {0:1} if plot.name.startswith("comp/TTJets_vs_TTGJets") else {},
        drawObjects = drawObjects( dataMCScale, lumi_scale ) if not plot.name.startswith("comp/TTG_vs_TTZ") else drawObjects( TTG_scale, lumi_scale),
  )

logger.info( "Done with prefix %s and selectionString %s", args.selection, selectionStrings[args.selection] )
