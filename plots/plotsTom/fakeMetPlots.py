#!/usr/bin/env python
''' Analysis script for standard plots
'''
#
# Standard imports and batch mode
#
import ROOT, os
ROOT.gROOT.SetBatch(True)

from math                                import sqrt, cos, sin, pi
from RootTools.core.standard             import *
from StopsDilepton.tools.user            import plot_directory
from StopsDilepton.tools.helpers         import deltaPhi
from StopsDilepton.tools.objectSelection import getFilterCut
from StopsDilepton.plots.pieChart        import makePieChart
from StopsDilepton.tools.cutInterpreter  import cutInterpreter

#
# Arguments
# 
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',       action='store',      default='INFO',          nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], help="Log level for logging")
argParser.add_argument('--signal',         action='store',      default=None,            nargs='?', choices=[None, "T2tt", "DM"], help="Add signal to plot")
argParser.add_argument('--noData',         action='store_true', default=False,           help='also plot data?')
argParser.add_argument('--plot_directory', action='store',      default='fakeMetPlots')
argParser.add_argument('--selection',      action='store',      default=None)
argParser.add_argument('--split',          action='store',      default='Top')
argParser.add_argument('--runLocal',       action='store_true', default=False)
argParser.add_argument('--splitBosons',    action='store_true', default=False)
argParser.add_argument('--splitBosons2',   action='store_true', default=False)
argParser.add_argument('--isChild',        action='store_true', default=False)
argParser.add_argument('--dryRun',         action='store_true', default=False,           help='do not launch subjobs')
args = argParser.parse_args()

#
# Logger
#
import StopsDilepton.tools.logger as logger
import RootTools.core.logger as logger_rt
logger    = logger.get_logger(   args.logLevel, logFile = None)
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None)

#
# Selection strings for which plots need to be produced, as interpreted by the cutInterpreter
#
selectionStrings = ['njet01-btag0-relIso0.12-looseLeptonVeto-mll20-metInv',
                    'njet01-btag0-relIso0.12-looseLeptonVeto-mll20-met80-metSig5',
                    'njet01-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5',
                    'njet01-btag1p-relIso0.12-looseLeptonVeto-mll20-metInv',
                    'njet01-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5',
                    'njet2p-relIso0.12-looseLeptonVeto-mll20',
                    'njet2p-relIso0.12-looseLeptonVeto-mll20-onZ',
                    'njet2p-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiInv-mt2ll100',
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-metInv',
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-met80-metSig5',
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-mt2ll100',
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-mt2ll100',
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiInv',                                # DY control
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiInv-mt2ll100',
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiJet0-dPhiJet1',                # VV control
                    'njet2p-btag0-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiJet0-dPhiJet1-mt2ll100',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-metInv',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1-mt2ll0to100',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1-mt2ll100',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1-mt2ll140',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiJet0-dPhiJet1',
                    'njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiJet0-dPhiJet1-mt2ll100']

def launch(command, logfile):
  if args.runLocal: os.system(command + " --isChild &> " + logfile)
  else:             os.system("qsub -v command=\"" + command + " --isChild\" -q localgrid@cream02 -o " + logfile + " -e " + logfile + " -l walltime=20:00:00 runPlotsOnCream02.sh")

#
# If this is the mother process, launch the childs and exit
#
if not args.isChild and args.selection is None:
  import os
  os.system("mkdir -p log")
  for selection in selectionStrings:
    command = "./fakeMetPlots.py --selection=" + selection + (" --noData"                if args.noData       else "")\
                                                           + (" --splitBosons"           if args.splitBosons  else "")\
                                                           + (" --splitBosons2"          if args.splitBosons2 else "")\
                                                           + (" --signal=" + args.signal if args.signal       else "")\
                                                           + (" --plot_directory=" + args.plot_directory)\
                                                           + (" --split=" + args.split)\
                                                           + (" --logLevel=" + args.logLevel)
    logfile = "log/fakeMet_" + args.split + "_" + selection + ".log"
    logger.info("Launching " + selection + " on cream02 with child command: " + command)
    if not args.dryRun:                                                                                   launch(command, logfile)
    if selection.count('njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1'): launch(command + ' --noData', logfile)
  logger.info("All jobs launched")
  exit(0)

if args.noData:                   args.plot_directory += "_noData"
if args.splitBosons:              args.plot_directory += "_splitMultiBoson"
if args.splitBosons2:             args.plot_directory += "_splitMultiBoson2"
if args.signal == "DM":           args.plot_directory += "_DM"
args.plot_directory += '/' + args.split
DManalysis = (args.signal == "DM")

# Plot no signal for following selections
if args.selection.count("btag0") and args.selection.count("onZ"):                                      args.signal = None
if args.selection.count("njet2p-relIso0.12-looseLeptonVeto-mll20-onZ"):                                args.signal = None
if args.selection.count("njet2p-relIso0.12-looseLeptonVeto-mll20-onZ-met80-metSig5-dPhiInv-mt2ll100"): args.signal = None

#
# Make samples, will be searched for in the postProcessing directory
#
postProcessing_directory = "postProcessed_80X_v31/dilepTiny/"
from StopsDilepton.samples.cmgTuples_Data25ns_80X_03Feb_postProcessed import *
postProcessing_directory = "postProcessed_80X_v35/dilepTiny/"
from StopsDilepton.samples.cmgTuples_Summer16_mAODv2_postProcessed import *
from StopsDilepton.samples.cmgTuples_FastSimT2tt_mAODv2_25ns_postProcessed import *
from StopsDilepton.samples.cmgTuples_FullSimTTbarDM_mAODv2_25ns_postProcessed import TTbarDMJets_DiLept_pseudoscalar_Mchi_1_Mphi_10, TTbarDMJets_DiLept_scalar_Mchi_1_Mphi_10
T2tt                    = T2tt_750_1
T2tt2                   = T2tt_600_300
T2tt2.style             = styles.lineStyle( ROOT.kBlack, width=3, dotted=True )
T2tt.style              = styles.lineStyle( ROOT.kBlack, width=3 )

DM                      = TTbarDMJets_DiLept_pseudoscalar_Mchi_1_Mphi_10
DM2                     = TTbarDMJets_DiLept_scalar_Mchi_1_Mphi_10
DM.style                = styles.lineStyle( ROOT.kBlack, width=3)
DM2.style               = styles.lineStyle( 28,          width=3)



#
# Text on the plots
#
def drawObjects( plotData, dataMCScale, lumi_scale ):
    lumi_scale = 35.9
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(11) # align right
    lines = [
      (0.15, 0.95, 'CMS Preliminary' if plotData else 'CMS Simulation'), 
      (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV) Scale %3.2f'% ( lumi_scale, dataMCScale ) ) if plotData else (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV)' % lumi_scale)
    ]
    if "mt2ll100" in args.selection and args.noData: lines += [(0.55, 0.5, 'M_{T2}(ll) > 100 GeV')] # Manually put the mt2ll > 100 GeV label
    return [tex.DrawLatex(*l) for l in lines] 



def drawPlots(plots, mode, dataMCScale):
  for log in [False, True]:
    for plot in plots:
      if not max(l[0].GetMaximum() for l in plot.histos): continue # Empty plot
      if not args.noData: 
        if mode == "all": plot.histos[1][0].legendText = "Data"
        if mode == "SF":  plot.histos[1][0].legendText = "Data (SF)"
      plotting.draw(plot,
            plot_directory = os.path.join(plot_directory, args.plot_directory, mode + ("_log" if log else ""), args.selection),
            ratio = {'yRange':(0.1,1.9)} if not args.noData else None,
            logX = False, logY = log, sorting = False,
            yRange = (0.03, "auto") if log else (0.001, "auto"),
            scaling = {},
            legend = (0.50,0.88-0.04*sum(map(len, plot.histos)),0.9,0.88) if not args.noData else (0.50,0.9-0.047*sum(map(len, plot.histos)),0.85,0.9),
            drawObjects = drawObjects( not args.noData, dataMCScale , lumi_scale ),
            copyIndexPHP = True
      )




#
# Read variables and sequences
#
read_variables = ["weight/F", "l1_eta/F" , "l1_phi/F", "l2_eta/F", "l2_phi/F", "JetGood[pt/F,eta/F,phi/F,btagCSV/F]", "dl_mass/F", "dl_eta/F", "dl_mt2ll/F", "dl_mt2bb/F", "dl_mt2blbl/F",
                  "met_pt/F", "met_phi/F", "metSig/F", "ht/F", "nBTag/I", "nJetGood/I"]

offZ = "&&abs(dl_mass-91.1876)>15" if not (args.selection.count("onZ") or args.selection.count("allZ")) else ""
def getLeptonSelection(mode):
  if   mode=="mumu": return "(nGoodMuons==2&&nGoodElectrons==0&&isOS&&l1_pt>25&&isMuMu" + offZ + ")"
  elif mode=="mue":  return "(nGoodMuons==1&&nGoodElectrons==1&&isOS&&l1_pt>25&&isEMu)"
  elif mode=="ee":   return "(nGoodMuons==0&&nGoodElectrons==2&&isOS&&l1_pt>25&&isEE" + offZ + ")"


def splitSampleInFakeMet(sample, color):
  fakeMetSplittings = [
                       ('#slash{E}_{T, fake} < 50, ll match'    , 'abs(met_pt-met_genPt)&&abs(met_pt-met_genPt)<=50&&l1_mcMatchId!=0&&l2_mcMatchId!=0'),
                       ('#slash{E}_{T, fake} < 50, ll no match' , 'abs(met_pt-met_genPt)&&abs(met_pt-met_genPt)<=50&&!(l1_mcMatchId!=0&&l2_mcMatchId!=0)'),
                       ('50 < #slash{E}_{T, fake} < 100'        , 'abs(met_pt-met_genPt)>50&&abs(met_pt-met_genPt)<100'),
                       ('#slash{E}_{T, fake} > 100'             , 'abs(met_pt-met_genPt)>100'),
                    #  ('20 < #slash{E}_{T, fake} < 50'         , 'abs(met_pt-met_genPt)>20&&abs(met_pt-met_genPt)<=50'),
                    #  ('#slash{E}_{T, fake} < 20'              , 'abs(met_pt-met_genPt)<=20')
  ]

  splittedList = []
  i = 0
  for texName, selection in fakeMetSplittings:
    splittedSample         = copy.deepcopy(sample)
    splittedSample.name    = sample.name + '_splitInFakeMet' + str(i)
    splittedSample.texName = sample.texName + " " + texName
    splittedSample.color   = color + i 
    splittedSample.addSelectionString(selection)
    splittedList.append(splittedSample)
    i += 1

  return splittedList

#
# Loop over channels
#
yields     = {}
allPlots   = {}
allModes   = ['mumu','mue','ee']
for index, mode in enumerate(allModes):
  yields[mode] = {}
  if   mode=="mumu": data_sample = DoubleMuon_Run2016_backup
  elif mode=="ee":   data_sample = DoubleEG_Run2016_backup
  elif mode=="mue":  data_sample = MuonEG_Run2016_backup
  if   mode=="mumu": data_sample.texName = "data (2 #mu)"
  elif mode=="ee":   data_sample.texName = "data (2 e)"
  elif mode=="mue":  data_sample.texName = "data (1 #mu, 1 e)"

  data_sample.setSelectionString([getFilterCut(isData=True, badMuonFilters="Moriond2017Official"), getLeptonSelection(mode)])
  data_sample.name           = "data"
  data_sample.read_variables = ["evt/I","run/I"]
  data_sample.style          = styles.errorStyle(ROOT.kBlack)
  lumi_scale                 = data_sample.lumi/1000

  if args.noData: lumi_scale = 36.5
  weight_ = lambda event, sample: event.weight

  multiBosonList = [WWNo2L2Nu, WZ, ZZNo2L2Nu, VVTo2L2Nu, triBoson] if args.splitBosons else ([WW, WZ, ZZ, triBoson] if args.splitBosons2 else [multiBoson])

  mc = [Top_pow, DY_HT_LO, TTZ_LO, TTXNoZ] + multiBosonList
  for sample in mc + [DM, DM2]:
    sample.scale          = lumi_scale
    sample.read_variables = ['reweightLeptonTrackingSF/F','reweightTopPt/F','reweightDilepTriggerBackup/F','reweightLeptonSF/F','reweightBTag_SF/F','reweightPU36fb/F', 'nTrueInt/F']
    sample.weight         = lambda event, sample: event.reweightLeptonTrackingSF*event.reweightTopPt*event.reweightLeptonSF*event.reweightBTag_SF*event.reweightDilepTriggerBackup*event.reweightPU36fb
    sample.setSelectionString([getFilterCut(isData=False), getLeptonSelection(mode)])

  for sample in [T2tt, T2tt2]:
    sample.scale          = lumi_scale
    sample.read_variables = ['reweightLeptonTrackingSF/F','reweightTopPt/F','reweightDilepTriggerBackup/F','reweightLeptonSF/F','reweightLeptonFastSimSF/F','reweightBTag_SF/F','reweightPU36fb/F', 'nTrueInt/F']
    sample.weight         = lambda event, sample: event.reweightLeptonTrackingSF*event.reweightTopPt*event.reweightLeptonSF*event.reweightLeptonFastSimSF*event.reweightBTag_SF*event.reweightDilepTriggerBackup*event.reweightPU36fb

  topList        = splitSampleInFakeMet(Top_pow,    ROOT.kCyan)   if args.split == 'Top' else [Top_pow]
  dyList         = splitSampleInFakeMet(DY_HT_LO,   ROOT.kGreen)  if args.split == 'DY' else [DY_HT_LO]
  ttzList        = splitSampleInFakeMet(TTZ_LO,     ROOT.kPink)   if args.split == 'TTZ' else [TTZ_LO]
  ttxList        = splitSampleInFakeMet(TTXNoZ,     ROOT.kRed)    if args.split == 'TTXNoZ' else [TTXNoZ]
  multiBosonList = splitSampleInFakeMet(multiBoson, ROOT.kYellow) if args.split == 'multiBoson' else multiBosonList

  fakeMetList = topList
  if args.split == "DY":         fakeMetList = dyList
  if args.split == "TTZ":        fakeMetList = ttzList
  if args.split == "TTXNoZ":     fakeMetList = ttxList
  if args.split == "multiBoson": fakeMetList = multiBosonList
  
  mc = topList + ttzList + ttxList + multiBosonList + dyList
  for sample in mc: sample.style = styles.fillStyle(sample.color, lineColor = sample.color)


  if not args.noData:
    if not args.signal:         stack = Stack(mc, data_sample)
    elif args.signal == "DM":   stack = Stack(mc, data_sample, DM, DM2)
    elif args.signal == "T2tt": stack = Stack(mc, data_sample, T2tt, T2tt2)
  else:
    if not args.signal:         stack = Stack(mc)
    elif args.signal == "DM":   stack = Stack(mc, DM, DM2)
    elif args.signal == "T2tt": stack = Stack(mc, T2tt, T2tt2)


  # Use some defaults
  Plot.setDefaults(stack = stack, weight = weight_, selectionString = cutInterpreter.cutString(args.selection), addOverFlowBin='upper')
  
  plots = []

  plots.append(Plot(
    name = 'yield', texX = 'yield', texY = 'Number of Events',
    attribute = lambda event, sample: 0.5 + index,
    binning=[3, 0, 3],
  ))

  plots.append(Plot(
    name = 'nVtxs', texX = 'vertex multiplicity', texY = 'Number of Events',
    attribute = TreeVariable.fromString( "nVert/I" ),
    binning=[50,0,50],
  ))

  plots.append(Plot(
      texX = 'E_{T}^{miss} (GeV)', texY = 'Number of Events / 20 GeV',
      attribute = TreeVariable.fromString( "met_pt/F" ),
      binning=[400/20,0,400],
  ))

  plots.append(Plot(
      texX = '#phi(E_{T}^{miss})', texY = 'Number of Events / 20 GeV',
      attribute = TreeVariable.fromString( "met_phi/F" ),
      binning=[10,-pi,pi],
  ))

  plots.append(Plot(
    texX = 'E_{T}^{miss}/#sqrt{H_{T}} (GeV^{1/2})', texY = 'Number of Events',
    attribute = TreeVariable.fromString('metSig/F'),
    binning= [80,20,100] if args.selection.count('metSig20') else ([25,5,30] if args.selection.count('metSig') else [30,0,30]),
  ))

  plots.append(Plot(
    texX = 'M_{T2}(ll) (GeV)', texY = 'Number of Events / 20 GeV',
    attribute = TreeVariable.fromString( "dl_mt2ll/F" ),
    binning=[300/20, 100,400] if args.selection.count('mt2ll100') else ([300/20, 140, 440] if args.selection.count('mt2ll140') else [300/20,0,300]),
  ))

  plots.append(Plot(
    texX = 'number of jets', texY = 'Number of Events',
    attribute = TreeVariable.fromString('nJetGood/I'),
    binning=[14,0,14],
  ))

  plots.append(Plot(
    texX = 'number of medium b-tags (CSVM)', texY = 'Number of Events',
    attribute = TreeVariable.fromString('nBTag/I'),
    binning=[8,0,8],
  ))

  plots.append(Plot(
    texX = 'H_{T} (GeV)', texY = 'Number of Events / 50 GeV',
    attribute = TreeVariable.fromString( "ht/F" ),
    binning=[500/50,50,600],
  ))

  plots.append(Plot(
    texX = 'm(ll) of leading dilepton (GeV)', texY = 'Number of Events / 4 GeV',
    attribute = TreeVariable.fromString( "dl_mass/F" ),
    binning=[200/4,0,200],
  ))

  plots.append(Plot(
    texX = 'p_{T}(ll) (GeV)', texY = 'Number of Events / 10 GeV',
    attribute = TreeVariable.fromString( "dl_pt/F" ),
    binning=[20,0,400],
  ))

  plots.append(Plot(
      texX = '#eta(ll) ', texY = 'Number of Events',
      name = 'dl_eta', attribute = lambda event, sample: abs(event.dl_eta), read_variables = ['dl_eta/F'],
      binning=[10,0,3],
  ))

  plots.append(Plot(
    texX = '#phi(ll)', texY = 'Number of Events',
    attribute = TreeVariable.fromString( "dl_phi/F" ),
    binning=[10,-pi,pi],
  ))

  plots.append(Plot(
    texX = 'Cos(#Delta#phi(ll, E_{T}^{miss}))', texY = 'Number of Events',
    name = 'cosZMetphi',
    attribute = lambda event, sample: cos( event.dl_phi - event.met_phi ), 
    read_variables = ["met_phi/F", "dl_phi/F"],
    binning = [10,-1,1],
  ))

  plots.append(Plot(
    texX = 'p_{T}(l_{1}) (GeV)', texY = 'Number of Events / 5 GeV',
    attribute = TreeVariable.fromString( "l1_pt/F" ),
    binning=[20,0,300],
  ))

  plots.append(Plot(
    texX = '#eta(l_{1})', texY = 'Number of Events',
    name = 'l1_eta', attribute = lambda event, sample: abs(event.l1_eta), read_variables = ['l1_eta/F'],
    binning=[15,0,3],
  ))

  plots.append(Plot(
    texX = '#phi(l_{1})', texY = 'Number of Events',
    attribute = TreeVariable.fromString( "l1_phi/F" ),
    binning=[10,-pi,pi],
  ))

  plots.append(Plot(
    texX = 'p_{T}(l_{2}) (GeV)', texY = 'Number of Events / 5 GeV',
    attribute = TreeVariable.fromString( "l2_pt/F" ),
    binning=[20,0,300],
  ))

  plots.append(Plot(
    texX = '#eta(l_{2})', texY = 'Number of Events',
    name = 'l2_eta', attribute = lambda event, sample: abs(event.l2_eta), read_variables = ['l2_eta/F'],
    binning=[15,0,3],
  ))

  plots.append(Plot(
    texX = '#phi(l_{2})', texY = 'Number of Events',
    attribute = TreeVariable.fromString( "l2_phi/F" ),
    binning=[10,-pi,pi],
  ))

  plots.append(Plot(
    name = "JZB",
    texX = 'JZB (GeV)', texY = 'Number of Events / 32 GeV',
    attribute = lambda event, sample: sqrt( (event.met_pt*cos(event.met_phi)+event.dl_pt*cos(event.dl_phi))**2 + (event.met_pt*sin(event.met_phi)+event.dl_pt*sin(event.dl_phi))**2) - event.dl_pt, 
        read_variables = ["met_phi/F", "dl_phi/F", "met_pt/F", "dl_pt/F"],
    binning=[25,-200,600],
  ))

  # Plots only when at least one jet:
  if args.selection.count('njet'):
    plots.append(Plot(
      texX = 'p_{T}(leading jet) (GeV)', texY = 'Number of Events / 30 GeV',
      name = 'jet1_pt', attribute = lambda event, sample: event.JetGood_pt[0],
      binning=[600/30,0,600],
    ))

    plots.append(Plot(
      texX = '#eta(leading jet) (GeV)', texY = 'Number of Events',
      name = 'jet1_eta', attribute = lambda event, sample: abs(event.JetGood_eta[0]),
      binning=[10,0,3],
    ))

    plots.append(Plot(
      texX = '#phi(leading jet) (GeV)', texY = 'Number of Events',
      name = 'jet1_phi', attribute = lambda event, sample: event.JetGood_phi[0],
      binning=[10,-pi,pi],
    ))

    plots.append(Plot(
      name = 'cosMetJet1phi',
      texX = 'Cos(#Delta#phi(E_{T}^{miss}, leading jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.met_phi - event.JetGood_phi[0]), 
      read_variables = ["met_phi/F", "JetGood[phi/F]"],
      binning = [10,-1,1],
    ))
    
    plots.append(Plot(
      name = 'cosMetJet1phi_smallBinning',
      texX = 'Cos(#Delta#phi(E_{T}^{miss}, leading jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.met_phi - event.JetGood_phi[0] ) , 
      read_variables = ["met_phi/F", "JetGood[phi/F]"],
      binning = [20,-1,1],
    ))

    plots.append(Plot(
      name = 'cosZJet1phi',
      texX = 'Cos(#Delta#phi(Z, leading jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.dl_phi - event.JetGood_phi[0] ) ,
      read_variables =  ["dl_phi/F", "JetGood[phi/F]"],
      binning = [10,-1,1],
    ))

  # Plots only when at least two jets:
  if args.selection.count('njet2p'):
    plots.append(Plot(
      texX = 'p_{T}(2nd leading jet) (GeV)', texY = 'Number of Events / 30 GeV',
      name = 'jet2_pt', attribute = lambda event, sample: event.JetGood_pt[1],
      binning=[600/30,0,600],
    ))

    plots.append(Plot(
      texX = '#eta(2nd leading jet) (GeV)', texY = 'Number of Events',
      name = 'jet2_eta', attribute = lambda event, sample: abs(event.JetGood_eta[1]),
      binning=[10,0,3],
    ))

    plots.append(Plot(
      texX = '#phi(2nd leading jet) (GeV)', texY = 'Number of Events',
      name = 'jet2_phi', attribute = lambda event, sample: event.JetGood_phi[1],
      binning=[10,-pi,pi],
    ))

    plots.append(Plot(
      name = 'cosMetJet2phi',
      texX = 'Cos(#Delta#phi(E_{T}^{miss}, second jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.met_phi - event.JetGood_phi[1] ) , 
      read_variables = ["met_phi/F", "JetGood[phi/F]"],
      binning = [10,-1,1],
    ))
    
    plots.append(Plot(
      name = 'cosMetJet2phi_smallBinning',
      texX = 'Cos(#Delta#phi(E_{T}^{miss}, second jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.met_phi - event.JetGood_phi[1] ) , 
      read_variables = ["met_phi/F", "JetGood[phi/F]"],
      binning = [20,-1,1],
    ))

    plots.append(Plot(
      name = 'cosZJet2phi',
      texX = 'Cos(#Delta#phi(Z, 2nd leading jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.dl_phi - event.JetGood_phi[0] ),
      read_variables = ["dl_phi/F", "JetGood[phi/F]"],
      binning = [10,-1,1],
    ))

    plots.append(Plot(
      name = 'cosJet1Jet2phi',
      texX = 'Cos(#Delta#phi(leading jet, 2nd leading jet))', texY = 'Number of Events',
      attribute = lambda event, sample: cos( event.JetGood_phi[1] - event.JetGood_phi[0] ) ,
      read_variables =  ["JetGood[phi/F]"],
      binning = [10,-1,1],
    ))

    plots.append(Plot(
      texX = 'M_{T2}(bb) (GeV)', texY = 'Number of Events / 30 GeV',
      attribute = TreeVariable.fromString( "dl_mt2bb/F" ),
      binning=[420/30,70,470],
    ))

    plots.append(Plot(
      texX = 'M_{T2}(blbl) (GeV)', texY = 'Number of Events / 30 GeV',
      attribute = TreeVariable.fromString( "dl_mt2blbl/F" ),
      binning=[420/30,0,400],
    ))



  plotting.fill(plots, read_variables = read_variables, sequence = [])

  # Get normalization yields from yield histogram
  for plot in plots:
    if plot.name == "yield":
      for i, l in enumerate(plot.histos):
        for j, h in enumerate(l):
          yields[mode][plot.stack[i][j].name] = h.GetBinContent(h.FindBin(0.5+index))
          h.GetXaxis().SetBinLabel(1, "#mu#mu")
          h.GetXaxis().SetBinLabel(2, "e#mu")
          h.GetXaxis().SetBinLabel(3, "ee")
  if args.noData: yields[mode]["data"] = 0

  yields[mode]["MC"] = sum(yields[mode][s.name] for s in mc)
  dataMCScale        = yields[mode]["data"]/yields[mode]["MC"] if yields[mode]["MC"] != 0 else float('nan')

  drawPlots(plots, mode, dataMCScale)
  makePieChart(os.path.join(plot_directory, args.plot_directory, mode, args.selection), "pie_chart",         yields, mode, mc)
  makePieChart(os.path.join(plot_directory, args.plot_directory, mode, args.selection), "pie_chart_VV",      yields, mode, multiBosonList)
  makePieChart(os.path.join(plot_directory, args.plot_directory, mode, args.selection), "pie_chart_fakeMet", yields, mode, fakeMetList)
  allPlots[mode] = plots



# Add the different channels into SF and all
import itertools
for mode in ["SF","all"]:
  yields[mode] = {}
  for y in yields[allModes[0]]:
    try:    yields[mode][y] = sum(yields[c][y] for c in (['ee','mumu'] if mode=="SF" else ['ee','mumu','mue']))
    except: yields[mode][y] = 0
  dataMCScale = yields[mode]["data"]/yields[mode]["MC"] if yields[mode]["MC"] != 0 else float('nan')

  for plot in allPlots['mumu']:
    for plot2 in (p for p in (allPlots['ee'] if mode=="SF" else allPlots["mue"]) if p.name == plot.name):  #For SF add EE, second round add EMu for all
      for i, j in enumerate(list(itertools.chain.from_iterable(plot.histos))):
        for k, l in enumerate(list(itertools.chain.from_iterable(plot2.histos))):
          if i==k:
            j.Add(l)

  drawPlots(allPlots['mumu'], mode, dataMCScale)
  makePieChart(os.path.join(plot_directory, args.plot_directory, mode, args.selection), "pie_chart",         yields, mode, mc)
  makePieChart(os.path.join(plot_directory, args.plot_directory, mode, args.selection), "pie_chart_VV",      yields, mode, multiBosonList)
  makePieChart(os.path.join(plot_directory, args.plot_directory, mode, args.selection), "pie_chart_fakeMet", yields, mode, fakeMetList)


# Write to tex file
columns = [i.name for i in mc] + ["MC", "data"] + ([DM.name, DM2.name] if args.signal=="DM" else []) + ([T2tt.name, T2tt2.name] if args.signal=="T2tt" else [])
texdir = "tex"
try:    os.makedirs("./" + texdir)
except: pass
with open("./" + texdir + "/" + args.selection + ".tex", "w") as f:
  f.write("&" + " & ".join(columns) + "\\\\ \n")
  for mode in allModes + ["SF","all"]:
    f.write(mode + " & " + " & ".join([ (" %12.0f" if i == "data" else " %12.2f") % yields[mode][i] for i in columns]) + "\\\\ \n")



logger.info( "Done with prefix %s and selectionString %s", args.selection, cutInterpreter.cutString(args.selection))

