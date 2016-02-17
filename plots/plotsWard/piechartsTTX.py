import ROOT
ROOT.gROOT.LoadMacro("$CMSSW_BASE/src/StopsDilepton/tools/scripts/tdrstyle.C")
ROOT.setTDRStyle()
import numpy, sys
from pylab import *
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from math import *

from StopsDilepton.tools.helpers import getChain, getObjDict, getEList, getVarValue, deltaPhi
from StopsDilepton.tools.texHelpers import latexmaker_2
from StopsDilepton.tools.objectSelection import getLeptons, looseMuID, looseEleID, getJets, getGenParts, getGoodLeptons, getGoodElectrons, getGoodMuons
from StopsDilepton.tools.user import *
from StopsDilepton.tools.mt2Calculator import mt2Calculator
mt2Calc = mt2Calculator()



#######################################################
#        SELECT WHAT YOU WANT TO DO HERE              #
#######################################################
reduceStat         = 1 #recude the statistics, i.e. 10 is ten times less samples to look at
btagcoeff          = 0.89
metcut             = 80.
metsignifcut       = 8.
dphicut            = 0.25
mllcut             = 20
ngoodleptons       = 2
luminosity         = 10000


presel_met         = 'met_pt>'+str(metcut)
presel_nbjet       = 'Sum$(Jet_pt>30&&abs(Jet_eta)<2.4&&Jet_id&&Jet_btagCSV>'+str(btagcoeff)+')>=1'
presel_njet        = 'Sum$(Jet_pt>30&&abs(Jet_eta)<2.4&&Jet_id)>=2'
presel_metsig      = 'met_pt/sqrt(Sum$(Jet_pt*(Jet_pt>30&&abs(Jet_eta)<2.4&&Jet_id)))>'+str(metsignifcut)
presel_mll         = 'dl_mass>'+str(mllcut)
presel_ngoodlep    = '((nGoodMuons+nGoodElectrons)=='+str(ngoodleptons)+')'
presel_OS          = 'isOS'

#preselection: MET>40, njets>=2, n_bjets>=1, n_lep>=2
#See here for the Sum$ syntax: https://root.cern.ch/root/html/TTree.html#TTree:Draw@2
preselection = presel_met+'&&'+presel_nbjet+'&&'+presel_njet+'&&'+presel_metsig+'&&'+presel_mll+'&&'+presel_ngoodlep+'&&'+presel_OS

#######################################################
#                 load all the samples                #
#######################################################
from StopsDilepton.samples.cmgTuples_Spring15_mAODv2_25ns_1l_postProcessed import *
backgrounds = [TTH,TTW,TTZ,TZQ]

#######################################################
#            get the TChains for each sample          #
#######################################################
for s in backgrounds:
    s['chain'] = getChain(s,histname="")


#######################################################
#         Define piecharts you want to make           #
#######################################################
mt2llcuts = [0.,80.,100.,130.,150.,200.]
piechart = {}
for cut in mt2llcuts:
    piechart[str(cut)] = {\
        "OF":{\
            "(>=2,>=1)" :{},
        },
        "SF":{\
            "(>=2,>=1)" :{},
        }
}

#######################################################
#            Start filling in the histograms          #
#######################################################
for s in backgrounds:
    for cut in piechart.keys():
        for flavor in piechart[cut].keys():
            for piece in piechart[cut][flavor].keys():
                piechart[cut][flavor][piece][s["name"]] = 0
    chain = s["chain"]

    chain.SetBranchStatus("*",0)
    chain.SetBranchStatus("met_pt",1)
    chain.SetBranchStatus("met_phi",1)
    chain.SetBranchStatus("Jet_pt",1)
    chain.SetBranchStatus("Jet_eta",1)
    chain.SetBranchStatus("Jet_id",1)
    chain.SetBranchStatus("Jet_btagCSV",1)
    chain.SetBranchStatus("LepGood_pt",1)
    chain.SetBranchStatus("LepGood_eta",1)
    chain.SetBranchStatus("LepGood_phi",1)
    chain.SetBranchStatus("LepGood_charge",1)
    chain.SetBranchStatus("LepGood_dxy",1)
    chain.SetBranchStatus("LepGood_dz",1)
    chain.SetBranchStatus("LepGood_relIso03",1)
    chain.SetBranchStatus("LepGood_tightId",1)
    chain.SetBranchStatus("LepGood_pdgId",1)
    chain.SetBranchStatus("LepGood_mediumMuonId",1)
    chain.SetBranchStatus("LepGood_miniRelIso",1)
    chain.SetBranchStatus("LepGood_sip3d",1)
    chain.SetBranchStatus("LepGood_mvaIdPhys14",1)
    chain.SetBranchStatus("LepGood_convVeto",1)
    chain.SetBranchStatus("LepGood_lostHits",1)
    chain.SetBranchStatus("Jet_eta",1)
    chain.SetBranchStatus("Jet_pt",1)
    chain.SetBranchStatus("Jet_phi",1)
    chain.SetBranchStatus("Jet_btagCMVA",1)
    chain.SetBranchStatus("Jet_btagCSV",1)
    chain.SetBranchStatus("Jet_id",1)
    chain.SetBranchStatus("weight",1)
    chain.SetBranchStatus("l1_pt",1)
    chain.SetBranchStatus("l2_pt",1)
    chain.SetBranchStatus("dl_mass",1)
    chain.SetBranchStatus("dl_mt2ll",1)
    chain.SetBranchStatus("dl_mt2bb",1)
    chain.SetBranchStatus("dl_mt2blbl",1)
    chain.SetBranchStatus("dl_mass",1)
    chain.SetBranchStatus("nGoodMuons",1)
    chain.SetBranchStatus("nGoodElectrons",1)
    chain.SetBranchStatus("isOS",1)
    chain.SetBranchStatus("isEE",1)
    chain.SetBranchStatus("isEMu",1)
    chain.SetBranchStatus("isMuMu",1)
    chain.SetBranchStatus("genWeight",1)
    chain.SetBranchStatus("Jet_mcMatchFlav",1)
    chain.SetBranchStatus("xsec",1)
    chain.SetBranchStatus("Jet_partonId",1)

    #Using Event loop
    #get EList after preselection
    print '\n', "Looping over %s" % s["name"]
    eList = getEList(chain, preselection)
    nEvents = eList.GetN()/reduceStat
    print "Found %i events in %s after preselection %s, looping over %i" % (eList.GetN(),s["name"],preselection,nEvents)


    for ev in range(nEvents):

        increment = 50
        if nEvents>increment and ev%(nEvents/increment)==0:
            sys.stdout.write('\r' + "=" * (ev / (nEvents/increment)) +  " " * ((nEvents - ev)/ (nEvents/increment)) + "]" +  str(round((ev+1) / (float(nEvents)/100),2)) + "%")
            sys.stdout.flush()
            sys.stdout.write('\r')
        chain.GetEntry(eList.GetEntry(ev))
        mt2Calc.reset()
        #event weight (L= 4fb^-1)
        weight = reduceStat*getVarValue(chain, "weight")

        weight = weight*(luminosity/1000.)

        #MET
        met = getVarValue(chain, "met_pt")
        metPhi = getVarValue(chain, "met_phi")
        #jetpt
        leadingjetpt = getVarValue(chain, "Jet_pt",0)
        subleadingjetpt = getVarValue(chain, "Jet_pt",1)
        #leptons
        l0pt = getVarValue(chain, "l1_pt")
        l1pt = getVarValue(chain, "l2_pt")
        mll = getVarValue(chain,"dl_mass")

        isEE = getVarValue(chain, "isEE")
        isMuMu = getVarValue(chain, "isMuMu")
        isEMu = getVarValue(chain, "isEMu")

        #Leptons
        allLeptons = getGoodLeptons(chain)
        muons = getGoodMuons(chain)
        electrons = getGoodElectrons(chain)

        #SF and OF channels
        leptons = {\
            'mu':   {'name': 'mumu', 'file': muons},
            'e':   {'name': 'ee', 'file': electrons},
            'emu': {'name': 'emu', 'file': [electrons,muons]},
            }

        for lep in leptons.keys():
            if (lep == "emu" and isEMu) or (((lep == "e" and isEE) or (lep == "mu" and isMuMu)) and abs(mll-91.2)>15):
                jets = filter(lambda j:j['pt']>30 and abs(j['eta'])<2.4 and j['id'], getJets(chain))
                ht = sum([j['pt'] for j in jets])
                bjetspt = filter(lambda j:j['btagCSV']>btagcoeff, jets)
                nobjets = filter(lambda j:j['btagCSV']<btagcoeff, jets)
                njets = len(jets)
                nbjets = len(bjetspt)
                nmuons = len(muons)
                nelectrons = len(electrons)

                mt2ll = getVarValue(chain,"dl_mt2ll")

                PhiMetJet1 = deltaPhi(metPhi,getVarValue(chain, "Jet_phi",0))
                PhiMetJet2 = deltaPhi(metPhi,getVarValue(chain, "Jet_phi",1))

                PhiMetJet_small = min(PhiMetJet1,PhiMetJet2)

                for cut in mt2llcuts:

                    if mt2ll >= cut and PhiMetJet_small > dphicut:
                        if isEMu:
                            piechart[str(cut)]["OF"]["(>=2,>=1)"][s["name"]]+=weight
                        else:
                            piechart[str(cut)]["SF"]["(>=2,>=1)"][s["name"]]+=weight
    del eList


for s in backgrounds:
    for cut in piechart.keys():
        for flavor in piechart[cut].keys():
            for piece in piechart[cut][flavor].keys():
                if piechart[cut][flavor][piece][s["name"]] <= 0.: piechart[cut][flavor][piece][s["name"]] = 0.

def makefigure(piechart,mt2llcut):

    backgrounds[0]["color"]     = "yellow"
    backgrounds[1]["color"]     = "grey"
    backgrounds[2]["color"]     = "cyan"
    backgrounds[3]["color"]     = "red"

    piechart = piechart[str(mt2llcut)]

    fig1 = plt.figure(figsize=(13,4))
    gridx=len(piechart["SF"])+1
    gridy=4  #jet multiplicity, SF and OF and add one for legend
    #colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral','mediumblue','red','magenta']
    #colors = colors[:len(piechart["SF"])]
    colors = [b["color"] for b in sorted(backgrounds)]
    for ikey,key in enumerate(piechart.keys()):
        plt.subplot(gridx,gridy,ikey+2)
        plt.text(0.5,0.5,key,fontsize=20)
        plt.axis("off")
        k = ikey+6
        for icolumn,column in enumerate(sorted(piechart[key].keys())):
            if ikey == 0:
                plt.subplot(gridx,gridy,k-1)
                plt.text(0.5,0.5,column,fontsize=15)
                plt.axis('off')
            bkgs = [b['name'] for b in sorted(backgrounds)]
            bkgrates = [piechart[key][column][b["name"]] for b in sorted(backgrounds)]
            if k%gridy==0: k+=1
            plt.subplot(gridx,gridy,k)
            if 0<sum(bkgrates)<1 : bkgrates = [i*(1./sum(bkgrates)) for i in bkgrates]
            patches, texts = plt.pie(bkgrates,colors=colors)
            plt.axis('equal')
            k+=4

    plt.subplot(gridx,gridy,1)
    plt.text(0.5,0.5,"mt2ll>"+str(mt2llcut), fontsize=13)
    plt.axis('off')
    plt.subplot(gridx,gridy,gridy+4)

    # yellow_patch       = mpatches.Patch(color="yellow",label=bkgs[0])
    # grey_patch         = mpatches.Patch(color='0.75',label=)
    # lightsalmoon_patch = mpatches.Patch(color='lightsalmon', label)
    # darkred_patch      = mpatches.Patch(color='darkred',label)
    # deeppink_patch     = mpatches.Patch(color='deeppink',label)
    # yellowgreen_patch  = mpatches.Patch(color='yellowgreen',label)
    # cyan_patch         = mpatches.Patch(color='cyan',label)


    #plt.legend([yellowgreen_patch,gold_patch,lightskyblue_patch,lightcoral_patch,mediumblue_patch,red_patch,magenta_patch],bkgs)
    plt.legend(patches,bkgs)
    plt.axis('off')
    plt.savefig('/afs/cern.ch/user/w/wvandrie/www/Stops/test/piechartsTTX/piecharts_mt2llcut_'+str(int(mt2llcut))+'.png')

for cut in mt2llcuts:
    makefigure(piechart,cut)
    latexmaker_2(piechart,cut,"SF")
    latexmaker_2(piechart,cut,"OF")
