#!/usr/bin/env python
''' Analysis script for standard plots
'''
#
# Standard imports and batch mode
#
import ROOT
ROOT.gROOT.SetBatch(True)

from math                                import sqrt, cos, sin, pi
from RootTools.core.standard             import *
from RootTools.plot.helpers              import copyIndexPHP
from StopsDilepton.tools.user            import plot_directory
from StopsDilepton.tools.helpers         import deltaPhi
from StopsDilepton.tools.objectSelection import getFilterCut
from StopsDilepton.tools.cutInterpreter  import cutInterpreter
from StopsDilepton.plots.pieChart        import makePieChart

import pickle, os, time
import errno
#
# Arguments
# 
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel',          action='store',      default='INFO',     nargs='?', choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'], help="Log level for logging")
argParser.add_argument('--signal',            action='store',      default='T2tt',        nargs='?', choices=['None', "T2tt",'DM'], help="Add signal to plot")
argParser.add_argument('--noData',            action='store_true', default=False,       help='also plot data?')
argParser.add_argument('--plot_directory',    action='store',      default='systematicsPlots_v2')
#argParser.add_argument('--selection',         action='store',      default=None)
argParser.add_argument('--selection',         action='store',            default='njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1')
argParser.add_argument('--normalizationSelection',  action='store',      default='njet2p-btag1p-relIso0.12-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1-mt2llTo100')
argParser.add_argument('--selectSys',         action='store',      default='all')
#argParser.add_argument('--noMultiThreading',  action='store_true', default='False', help="noMultiThreading?") # Need no multithreading when doing batch-to-natch
argParser.add_argument('--showOnly',          action='store',      default=None)
argParser.add_argument('--small',             action='store_true',     help='Run only on a small subset of the data?', )
argParser.add_argument('--runLocal',             action='store_true',     help='Run local or submit?', )
argParser.add_argument('--copyIndexPHP',      action='store_true',     help='copy index.php to directories?', )
argParser.add_argument('--splitBosons',       action='store_true', default=False)
argParser.add_argument('--splitTop',          action='store_true', default=False)
argParser.add_argument('--powheg',            action='store_true', default=True)
argParser.add_argument('--isChild',           action='store_true', default=False)
argParser.add_argument('--normalizeBinWidth', action='store_true', default=False,       help='normalize wider bins?')
argParser.add_argument('--dryRun',            action='store_true', default=False,       help='do not launch subjobs')
args = argParser.parse_args()

#
# Logger
#
import StopsDilepton.tools.logger as logger
import RootTools.core.logger as logger_rt
logger    = logger.get_logger(   args.logLevel, logFile = None)
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None)


def waitForLock(filename):
    lockAcquired = False
    while not lockAcquired:
      try:
           f = os.open(filename + "_lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
           os.close(f)
           lockAcquired = True
      except OSError as e:
           if e.errno == errno.EEXIST:  # Failed as the file already exists.
             time.sleep(1)
           else:  # Something unexpected went wrong
             print e.errno
             print e
             print "Problem acquiring the lock"
             exit(1)

def removeLock(filename):
    os.system("rm " + filename + "_lock")

#
# Selections (two leptons with pt > 20 GeV)
#
from StopsDilepton.tools.objectSelection import multiIsoLepString
multiIsoWP = multiIsoLepString('VT','VT', ('l1_index','l2_index'))
def getLeptonString(nMu, nE, multiIso=False):
  leptonString = "nGoodMuons==" + str(nMu) + "&&nGoodElectrons==" + str(nE) + "&&l1_pt>25"
  if multiIso: leptonString += "&&l1_mIsoWP>4&&l2_mIsoWP>4"
  else:        leptonString += "&&l1_relIso03<0.12&&l2_relIso03<0.12"
  return leptonString


jetSelection    = "nJetGood"
bJetSelectionM  = "nBTag"


#
# Systematics to run over
#
jet_systematics    = ['JECUp','JECDown']# 'JERDown','JECVUp','JECVDown']
met_systematics    = ['UnclusteredEnUp', 'UnclusteredEnDown']
jme_systematics    = jet_systematics + met_systematics
weight_systematics = ['PU36fbUp', 'PU36fbDown', 'TopPt', 'BTag_SF_b_Down', 'BTag_SF_b_Up', 'BTag_SF_l_Down', 'BTag_SF_l_Up', 'DilepTriggerBackupDown', 'DilepTriggerBackupUp', 'LeptonSFDown', 'LeptonSFUp']


if args.selectSys != "all" and args.selectSys != "combine": all_systematics = [args.selectSys if args.selectSys != 'None' else None]
else:                                                       all_systematics = [None] + weight_systematics + jme_systematics
#else:                                                       all_systematics = [None] + jet_systematics


sys_pairs = [\
    ('JEC',         'JECUp', 'JECDown'),
    ('Unclustered', 'UnclusteredEnUp', 'UnclusteredEnDown'), 
    ('PU36fb',      'PU36fbUp', 'PU36fbDown'),
    ('TopPt',       'TopPt', None),
#   ('JER',         'JERUp', 'JERDown'),
    ('BTag_b',      'BTag_SF_b_Down', 'BTag_SF_b_Up' ),
    ('BTag_l',      'BTag_SF_l_Down', 'BTag_SF_l_Up'),
    ('trigger',     'DilepTriggerBackupDown', 'DilepTriggerBackupUp'),
    ('leptonSF',    'LeptonSFDown', 'LeptonSFUp'),
]

#
# If this is the mother process, launch the childs and exit (I know, this could potententially be dangereous if the --isChild and --selection commands are not given...)
#

def wrapper(com):
  import os
  os.system(com)

#if not args.isChild and args.selection is None and (args.selectSys == "all" or args.selectSys == "combine"):
if not args.isChild and (args.selectSys == "all" or args.selectSys == "combine"):
  jobs = []
  for sys in (all_systematics if args.selectSys == "all" else ["combine"]):
    command = "python systematicsPlots_v2.py --selection=" + args.selection + (" --noData" if args.noData else "")\
               + (" --isChild")\
               + (" --small" if args.small else "")\
               + (" --plot_directory=" + args.plot_directory)\
               + (" --logLevel=" + args.logLevel)\
               + (" --selectSys=" + str(sys))\
               + (" --signal=" + args.signal)\
               + (" --splitBosons" if args.splitBosons else "")\
               + (" --splitTop" if args.splitTop else "")\
               + (" --powheg" if args.powheg else "")\
               + (" --normalizeBinWidth" if args.normalizeBinWidth else "")
    if args.selectSys == 'combine':
        jobs.append(command)
    elif args.selectSys == 'all':
        if args.runLocal:
            jobs.append(command)
        else:
            jobs.append( "submitBatch.py --title='sys' '%s'"%command )

#  if args.noMultiThreading: 
  logger.info("Running/submitting all systematics.")
  results = map(wrapper, jobs)
  logger.info("Done with running/submitting systematics.")
  exit(0)

if args.noData:                   args.plot_directory += "_noData"
if args.splitBosons:              args.plot_directory += "_splitMultiBoson"
if args.signal == "DM":           args.plot_directory += "_DM"
if args.signal == "T2tt":         args.plot_directory += "_T2tt"
if args.small:                    args.plot_directory += "_small"

try: os.makedirs(os.path.join(plot_directory, args.plot_directory, mode, args.selection))
except: pass

if args.copyIndexPHP:
    copyIndexPHP( plot_directory )
    copyIndexPHP( os.path.join( plot_directory, args.plot_directory ) )

#
# Make samples, will be searched for in the postProcessing directory
#
postProcessing_directory = "postProcessed_80X_v23/dilepTiny/"
from StopsDilepton.samples.cmgTuples_Spring16_mAODv2_postProcessed import *
postProcessing_directory = "postProcessed_80X_v22/dilepTiny/"
from StopsDilepton.samples.cmgTuples_Data25ns_80X_23Sep_postProcessed import *

signals = []
if   args.signal == "T2tt": 
    postProcessing_directory = "postProcessed_80X_v28/dilepTiny/"
    from StopsDilepton.samples.cmgTuples_FastSimT2tt_mAODv2_25ns_postProcessed import *
    T2tt                    = T2tt_650_1
    T2tt2                   = T2tt_500_250
    T2tt2.style             = styles.lineStyle( ROOT.kBlack, width=3, dotted=True )
    T2tt.style              = styles.lineStyle( ROOT.kBlack, width=3 )
    signals = [T2tt, T2tt2]
elif args.signal == "DM":   
    #from StopsDilepton.samples.cmgTuples_FullSimTTbarDM_mAODv2_25ns_postProcessed import *
    #DM                      = TTbarDMJets_pseudoscalar_Mchi_1_Mphi_10
    #DM2                     = TTbarDMJets_scalar_Mchi_1_Mphi_10
    #DM.style                = styles.lineStyle( ROOT.kBlack, width=3)
    #DM2.style               = styles.lineStyle( 28,          width=3)
    signals = [DM, DM2]

#
# Text on the plots
#
def drawObjects( plotData, dataMCScale, lumi_scale ):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(11) # align right
    lines = [
      (0.15, 0.95, 'CMS Preliminary' if plotData else 'CMS Simulation'), 
      (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV) Scale %3.2f'% ( lumi_scale, dataMCScale ) ) if False else (0.45, 0.95, 'L=%3.1f fb{}^{-1} (13 TeV)' % lumi_scale)
    ]
    return [tex.DrawLatex(*l) for l in lines] 


def addSys( selectionString , sys = None ):
    if   sys in jet_systematics: return selectionString.replace('nJetGood', 'nJetGood_' + sys).replace('nBTag', 'nBTag_' + sys).replace('dl_mt2ll', 'dl_mt2ll_' + sys).replace('dl_mt2bb', 'dl_mt2bb_' + sys).replace('dl_mt2blbl', 'dl_mt2blbl_' + sys)
    elif sys in met_systematics: return selectionString.replace('met_pt', 'met_pt_' + sys).replace('metSig', 'metSig_' + sys).replace('dl_mt2ll', 'dl_mt2ll_' + sys).replace('dl_mt2bb', 'dl_mt2bb_' + sys).replace('dl_mt2blbl', 'dl_mt2blbl_' + sys)
    else:                        return selectionString


def weightMC( sys = None ):
    if sys is None:                 return (lambda event, sample:event.weight*event.reweightLeptonSF*event.reweightPU36fb*event.reweightDilepTriggerBackup*event.reweightBTag_SF, "weight*reweightLeptonSF*reweightDilepTriggerBackup*reweightPU36fb*reweightBTag_SF")
    elif 'PU' in sys:               return (lambda event, sample:event.weight*event.reweightLeptonSF*getattr(event, "reweight"+sys)*event.reweightDilepTriggerBackup*event.reweightBTag_SF, "weight*reweightLeptonSF*reweightDilepTriggerBackup*reweight"+sys+"*reweightBTag_SF")
    elif 'BTag' in sys:             return (lambda event, sample:event.weight*event.reweightLeptonSF*event.reweightPU36fb*event.reweightDilepTriggerBackup*getattr(event, "reweight"+sys), "weight*reweightLeptonSF*reweightDilepTriggerBackup*reweightPU36fb*reweight"+sys)
    elif sys in weight_systematics: return (lambda event, sample:event.weight*event.reweightLeptonSF*event.reweightDilepTriggerBackup*event.reweightPU36fb*event.reweightBTag_SF*getattr(event, "reweight"+sys), "weight*reweightLeptonSF*reweightDilepTriggerBackup*reweightPU36fb*reweightBTag_SF*reweight"+sys)
    elif sys in jme_systematics :   return weightMC( sys = None )
    else:                           raise ValueError( "Systematic %s not known"%sys )
    
#
# Read variables and sequences
#
read_variables = ["weight/F", "l1_pt/F", "l2_pt/F", "l1_eta/F" , "l1_phi/F", "l2_eta/F", "l2_phi/F", "JetGood[pt/F,eta/F,phi/F,btagCSV/F]", "dl_mass/F", "dl_eta/F", "dl_mt2ll/F", "dl_mt2bb/F", "dl_mt2blbl/F",
                  "met_pt/F", "met_phi/F", "LepGood[pt/F,eta/F,miniRelIso/F]", "nGoodMuons/F", "nGoodElectrons/F", "l1_mIsoWP/F", "l2_mIsoWP/F",
                  "metSig/F", "ht/F", "nBTag/I", "nJetGood/I","run/I","evt/l"]

sequence = []

offZ = "&&abs(dl_mass-91.1876)>15" if not (args.selection.count("onZ") or args.selection.count("allZ") or args.selection.count("offZ")) else ""
def getLeptonSelection( mode ):
  if   mode=="mumu": return "nGoodMuons==2&&nGoodElectrons==0&&isOS&&isMuMu" + offZ
  elif mode=="mue":  return "nGoodMuons==1&&nGoodElectrons==1&&isOS&&isEMu"
  elif mode=="ee":   return "nGoodMuons==0&&nGoodElectrons==2&&isOS&&isEE" + offZ
  elif mode=="all":  return "(" + "||".join([getLeptonSelection(m) for m in ["mumu","mue","ee"]]) + ")"


#
# Loop over channels
#
allPlots   = {}
allModes   =['mue','ee','mumu','all']
for index, mode in enumerate(allModes):

  logger.info('Working on mode ' + str(mode))

  if mode=="mumu":
    data_sample         = DoubleMuon_Run2016_backup
    data_sample.texName = "data (2 #mu)"
  elif mode=="ee":
    data_sample         = DoubleEG_Run2016_backup
    data_sample.texName = "data (2 e)"
  elif mode=="mue":
    data_sample         = MuonEG_Run2016_backup
    data_sample.texName = "data (1 #mu, 1 e)"
  elif mode=="all":
    data_sample         = [DoubleMuon_Run2016_backup, DoubleEG_Run2016_backup, MuonEG_Run2016_backup]
    DoubleMuon_Run2016_backup.setSelectionString([getFilterCut(isData=True), getLeptonSelection("mumu")])
    DoubleEG_Run2016_backup.setSelectionString([getFilterCut(isData=True), getLeptonSelection("ee")])
    MuonEG_Run2016_backup.setSelectionString([getFilterCut(isData=True), getLeptonSelection("mue")])
    for d in data_sample:
      d.texName = "data"
      d.read_variables = ['weight/F']
      d.style   = styles.errorStyle( ROOT.kBlack )
    lumi_scale = sum(d.lumi for d in data_sample)/float(len(data_sample))/1000

  if mode != "all":
    data_sample.setSelectionString([getFilterCut(isData=True), getLeptonSelection(mode)])
    data_sample.name  = "data"
    data_sample.read_variables = ['weight/F']
    data_sample.style = styles.errorStyle( ROOT.kBlack )
    lumi_scale        = data_sample.lumi/1000

#  # Blinding policies for DM and T2tt analyses
#  if "njet2-btagM-looseLeptonVeto-mll20-met80" in args.selection:
#    pass # doesn't work
#    #if args.signal == "DM":
#    #  weight_       = lambda event, sample: event.weight if (sample not in [DoubleMuon_Run2016_backup, DoubleEG_Run2016_backup, MuonEG_Run2016_backup]) else event.weight*(1 if (event.evt % 15 == 0) else 0)
#    #  data_weight_string = "weight*(evt%15==0)"
#    #  lumi_scale    = lumi_scale/15.
#    #else:
#    #  weight_       = lambda event, sample: event.weight if (sample not in [DoubleMuon_Run2016_backup, DoubleEG_Run2016_backup, MuonEG_Run2016_backup]) else event.weight*(1 if (event.run <= 276811) or (event.run >= 278820 and event.run <= 279931) else 0)
#    #  data_weight_string = "weight*(run<=276811||(run>=277820&&279931))"
#    #  lumi_scale    = 17.3
#  else:
  data_weight = lambda event, sample: event.weight
  data_weight_string = "weight"

  logger.info('Lumi scale is ' + str(lumi_scale))

  if args.splitBosons: mc = [ Top_pow, TTZ_LO, TTXNoZ, WWNo2L2Nu, WZ, ZZNo2L2Nu, VVTo2L2Nu, triBoson, DY_HT_LO]
  else:                mc = [ Top_pow, TTZ_LO, TTXNoZ, multiBoson, DY_HT_LO]
  if args.small:
    for sample in mc:# + ([data_sample] if type(data_sample)!=type([]) else data_sample):
      sample.reduceFiles( to = 1 )

  for sample in mc:
    sample.scale           = lumi_scale
    sample.style           = styles.fillStyle(sample.color, lineColor = sample.color)
    sample.read_variables  = ['reweightLeptonHIPSF/F','reweightDilepTriggerBackup/F','reweightLeptonSF/F','reweightBTag_SF/F','reweightPU36fb/F','nTrueInt/F']
    sample.read_variables += ["reweight%s/F"%s    for s in weight_systematics]
    sample.read_variables += ["dl_mt2ll_%s/F"%s   for s in jme_systematics]
    sample.read_variables += ["dl_mt2bb_%s/F"%s   for s in jme_systematics]
    sample.read_variables += ["dl_mt2blbl_%s/F"%s for s in jme_systematics]
    sample.read_variables += ["nJetGood_%s/I"%s   for s in jet_systematics]
    sample.read_variables += ["nBTag_%s/I"%s      for s in jet_systematics]
    sample.setSelectionString([getFilterCut(isData=False), getLeptonSelection(mode)])

#    # Apply scale factors in the mt2ll > 100 GeV signal region (except Top which will be already scaled anyway)
#    if args.selection.count('njet2-btagM-looseLeptonVeto-mll20-met80-metSig5-dPhiJet0-dPhiJet1-mt2ll100') and False: # Turn on when scalefactors are rederived
#      if sample == DY_HT_LO:   sample.scale = lumi_scale*1.30
#      if sample == multiBoson: sample.scale = lumi_scale*1.45
#      if sample == TTZ_LO:     sample.scale = lumi_scale*0.89


  if args.signal == "T2tt":
    for s in signals:
      s.scale          = lumi_scale
      s.read_variables = ['reweightLeptonHIPSF/F','reweightDilepTriggerBackup/F','reweightLeptonSF/F','reweightLeptonFastSimSF/F','reweightBTag_SF/F','reweightPU36fb/F','nTrueInt/F']
      s.weight         = lambda event, sample: event.reweightLeptonFastSimSF
      s.setSelectionString([getFilterCut(isData=False), getLeptonSelection(mode)])

  if args.signal == "DM":
    for s in signals:
      s.scale          = lumi_scale
      s.read_variables = ['reweightLeptonHIPSF/F','reweightDilepTriggerBackup/F','reweightLeptonSF/F','reweightBTag_SF/F','reweightPU36fb/F','nTrueInt/F']
      s.setSelectionString([getFilterCut(isData=False), getLeptonSelection(mode)])

  # Use some defaults
  Plot.setDefaults( selectionString = cutInterpreter.cutString(args.selection) )
  
  stack_mc   = Stack( mc )

  if   args.signal == "T2tt": stack_data = Stack( data_sample, T2tt, T2tt2 ) 
  elif args.signal == "DM":   stack_data = Stack( data_sample, DM, DM2) 
  else:                       stack_data = Stack( data_sample )
  sys_stacks = {sys:copy.deepcopy(stack_mc) for sys in [None] + weight_systematics + jme_systematics }
  plots = []
  

  dl_mt2ll_data  = Plot(
      name = "dl_mt2ll_data",
      texX = 'M_{T2}(ll) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
      binning=Binning.fromThresholds([0,20,40,60,80,100,140,240,340]),
      stack = stack_data,
      attribute = TreeVariable.fromString( "dl_mt2ll/F" ),
      weight = data_weight,
      )
  plots.append( dl_mt2ll_data )

  dl_mt2ll_mc  = { sys:Plot(\
      name            = "dl_mt2ll" if sys is None else "dl_mt2ll_mc_%s" % sys,
      texX            = 'M_{T2}(ll) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
      binning         = Binning.fromThresholds([0,20,40,60,80,100,140,240,340]),
      stack           = sys_stacks[sys],
      attribute        = TreeVariable.fromString( "dl_mt2ll/F" ) if sys is None or sys in weight_systematics else TreeVariable.fromString( "dl_mt2ll_%s/F" % sys ),
      selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
      weight          = weightMC( sys = sys )[0],
      ) for sys in all_systematics }
  plots.extend( dl_mt2ll_mc.values() )

  if args.selection.count('njet2'):
    dl_mt2bb_data  = Plot( 
  name            = "dl_mt2bb_data",
  texX            = 'M_{T2}(bb) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack           = stack_data,
  attribute       = TreeVariable.fromString( "dl_mt2bb/F" ),
  binning         = Binning.fromThresholds([70,90,110,130,150,170,190,210,230,250,300,350,400,450]),
  weight = data_weight,
  ) 
    plots.append( dl_mt2bb_data )

    dl_mt2bb_mc  = {sys: Plot(
  name = "dl_mt2bb" if sys is None else "dl_mt2bb_mc_%s" % sys,
  texX = 'M_{T2}(bb) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack = sys_stacks[sys],
  attribute = TreeVariable.fromString( "dl_mt2bb/F" ) if sys is None or sys in weight_systematics else TreeVariable.fromString( "dl_mt2bb_%s/F" % sys ),
  binning=Binning.fromThresholds([70,90,110,130,150,170,190,210,230,250,300,350,400,450]),
  selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
  weight = weightMC( sys = sys )[0],
  ) for sys in all_systematics }
    plots.extend( dl_mt2bb_mc.values() )

    dl_mt2bb_data_2 = Plot( 
  name            = "dl_mt2bb_data_2",
  texX            = 'M_{T2}(bb) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack           = stack_data,
  attribute        = TreeVariable.fromString( "dl_mt2bb/F" ),
  binning         = Binning.fromThresholds([70,90,110,130,150,170,190,210,230,250,300,350,400,450,500,550,600,700,800,1000]),
  weight = data_weight,
  ) 
    plots.append( dl_mt2bb_data_2 )

    dl_mt2bb_mc_2  = {sys: Plot(
  name = "dl_mt2bb_2" if sys is None else "dl_mt2bb_mc_2_%s" % sys,
  texX = 'M_{T2}(bb) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack = sys_stacks[sys],
  attribute = TreeVariable.fromString( "dl_mt2bb/F" ) if sys is None or sys in weight_systematics else TreeVariable.fromString( "dl_mt2bb_%s/F" % sys ),
  binning         = Binning.fromThresholds([70,90,110,130,150,170,190,210,230,250,300,350,400,450,500,550,600,700,800,1000]),
  selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
  weight = weightMC( sys = sys )[0],
  ) for sys in all_systematics }
    plots.extend( dl_mt2bb_mc_2.values() )



    dl_mt2blbl_data  = Plot( 
  name = "dl_mt2blbl_data",
  texX = 'M_{T2}(blbl) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack = stack_data,
  attribute = TreeVariable.fromString( "dl_mt2blbl/F" ),
  binning=Binning.fromThresholds([0,20,40,60,80,100,120,140,160,200,250,300,350]),
  weight = data_weight,
  ) 
    plots.append( dl_mt2blbl_data )

    dl_mt2blbl_mc  = {sys: Plot(
  name = "dl_mt2blbl" if sys is None else "dl_mt2blbl_mc_%s" % sys,
  texX = 'M_{T2}(blbl) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack = sys_stacks[sys],
  attribute = TreeVariable.fromString( "dl_mt2blbl/F" ) if sys is None or sys in weight_systematics else TreeVariable.fromString( "dl_mt2blbl_%s/F" % sys ),
  binning=Binning.fromThresholds([0,20,40,60,80,100,120,140,160,200,250,300,350]),
  selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
  weight = weightMC( sys = sys )[0],
  ) for sys in all_systematics }
    plots.extend( dl_mt2blbl_mc.values() )


    dl_mt2blbl_data_2  = Plot( 
  name = "dl_mt2blbl_data_2",
  texX = 'M_{T2}(blbl) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack = stack_data,
  attribute = TreeVariable.fromString( "dl_mt2blbl/F" ),
  binning=Binning.fromThresholds([0,20,40,60,80,100,120,140,160,200,250,300,350,400,450,500,600,700]),
  weight = data_weight,
  ) 
    plots.append( dl_mt2blbl_data_2 )

    dl_mt2blbl_mc_2  = {sys: Plot(
  name = "dl_mt2blbl_2" if sys is None else "dl_mt2blbl_mc_2_%s" % sys,
  texX = 'M_{T2}(blbl) (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Events",
  stack = sys_stacks[sys],
  attribute = TreeVariable.fromString( "dl_mt2blbl/F" ) if sys is None or sys in weight_systematics else TreeVariable.fromString( "dl_mt2blbl_%s/F" % sys ),
  binning=Binning.fromThresholds([0,20,40,60,80,100,120,140,160,200,250,300,350,400,450,500,600,700]),
  selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
  weight = weightMC( sys = sys )[0],
  ) for sys in all_systematics }
    plots.extend( dl_mt2blbl_mc_2.values() )

  nBtagBinning = [5, 1, 6] if args.selection.count('btagM') else [1,0,1]

  nbtags_data  = Plot( 
      name = "nbtags_data",
      texX = 'number of b-tags (CSVM)', texY = 'Number of Events',
      stack = stack_data,
      attribute = TreeVariable.fromString('nBTag/I'),
      binning=nBtagBinning,
      weight = data_weight,
      ) 
  plots.append( nbtags_data )

  nbtags_mc  = {sys: Plot(
      name = "nbtags" if sys is None else "nbtags_mc_%s" % sys,
      texX = 'number of b-tags (CSVM)', texY = 'Number of Events',
      stack = sys_stacks[sys],
      attribute = TreeVariable.fromString('nBTag/I') if sys is None or sys in weight_systematics or sys in met_systematics else TreeVariable.fromString( "nBTag_%s/I" % sys ),
      binning=nBtagBinning,
      selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
      weight = weightMC( sys = sys )[0],
      ) for sys in all_systematics }
  plots.extend( nbtags_mc.values() )

  jetBinning = [8,2,10] if args.selection.count('njet2') else [2,0,2]

  njets_data  = Plot( 
      name = "njets_data",
      texX = 'number of jets', texY = 'Number of Events',
      stack = stack_data,
      attribute = TreeVariable.fromString('nJetGood/I'),
      binning=jetBinning,
      weight = data_weight,
      )
  plots.append( njets_data )

  njets_mc  = {sys: Plot(
      name = "njets" if sys is None else "njets_mc_%s" % sys,
      texX = 'number of jets', texY = 'Number of Events',
      stack = sys_stacks[sys],
      attribute = TreeVariable.fromString('nJetGood/I') if sys is None or sys in weight_systematics or sys in met_systematics else TreeVariable.fromString( "nJetGood_%s/I" % sys ),
      binning= jetBinning,
      selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
      weight = weightMC( sys = sys )[0],
      ) for sys in all_systematics }
  plots.extend( njets_mc.values() )

  metBinning = [0,20,40,60,80] if args.selection.count('metInv') else [80,130,180,230,280,320,420,520,800] if args.selection.count('met80') else [0,80,130,180,230,280,320,420,520,800]

  met_data  = Plot( 
      name = "met_data",
      texX = 'E_{T}^{miss} (GeV)', texY = 'Number of Events / 50 GeV' if args.normalizeBinWidth else "Number of Event",
      stack = stack_data, 
      attribute = TreeVariable.fromString( "met_pt/F" ),
      binning=Binning.fromThresholds( metBinning ),
      weight = data_weight,
      )
  plots.append( met_data )

  met_mc  = {sys: Plot(
      name = "met_pt" if sys is None else "met_pt_mc_%s" % sys,
      texX = 'E_{T}^{miss} (GeV)', texY = 'Number of Events / 50 GeV' if args.normalizeBinWidth else "Number of Event",
      stack = sys_stacks[sys],
      attribute = TreeVariable.fromString('met_pt/F') if sys not in met_systematics else TreeVariable.fromString( "met_pt_%s/F" % sys ),
      binning=Binning.fromThresholds( metBinning ),
      selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
      weight = weightMC( sys = sys )[0],
      ) for sys in all_systematics }
  plots.extend( met_mc.values() )

  metBinning2 = [0,20,40,60,80] if args.selection.count('metInv') else [80,100,120,140,160,200,500] if args.selection.count('met80') else [0,80,100,120,140,160,200,500]

  met2_data  = Plot(
      name = "met2_data",
      texX = 'E_{T}^{miss} (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Event",
      stack = stack_data,
      attribute = TreeVariable.fromString( "met_pt/F" ),
      binning=Binning.fromThresholds( metBinning2 ),
      weight = data_weight,
      )
  plots.append( met2_data )

  met2_mc  = {sys: Plot(
      name = "met2_pt" if sys is None else "met2_pt_mc_%s" % sys,
      texX = 'E_{T}^{miss} (GeV)', texY = 'Number of Events / 20 GeV' if args.normalizeBinWidth else "Number of Event",
      stack = sys_stacks[sys],
      attribute = TreeVariable.fromString('met_pt/F') if sys not in met_systematics else TreeVariable.fromString( "met_pt_%s/F" % sys ),
      binning=Binning.fromThresholds( metBinning2 ),
      selectionString = addSys(cutInterpreter.cutString(args.selection), sys),
      weight = weightMC( sys = sys )[0],
      ) for sys in all_systematics }
  plots.extend( met2_mc.values() )

  plotConfigs = [\
         [ dl_mt2ll_mc, dl_mt2ll_data, 20],
         [ nbtags_mc, nbtags_data, -1],
         [ njets_mc, njets_data, -1],
         [ met_mc, met_data, 50],
         [ met2_mc, met2_data, 20],
    ]
  if args.selection.count('njet2'):
    plotConfigs.append([ dl_mt2bb_mc, dl_mt2bb_data, 20])
    plotConfigs.append([ dl_mt2blbl_mc, dl_mt2blbl_data, 20])
    plotConfigs.append([ dl_mt2bb_mc_2, dl_mt2bb_data_2, 20])
    plotConfigs.append([ dl_mt2blbl_mc_2, dl_mt2blbl_data_2, 20])


  result_file = os.path.join(plot_directory, args.plot_directory, mode, args.selection, 'results.pkl')
  try: os.makedirs(os.path.join(plot_directory, args.plot_directory, mode, args.selection))
  except: pass
  if args.copyIndexPHP:
    copyIndexPHP ( os.path.join(plot_directory, args.plot_directory, mode, args.selection) )

  if args.selectSys != "combine": 
    normalization_selection_string = cutInterpreter.cutString(args.normalizationSelection)
    #normalization_selection_string = normalization_selection_string.replace('&&dl_mt2ll>100','')
    mc_weight_func, mc_weight_string = weightMC( sys = (args.selectSys if args.selectSys != 'None' else None) )

    yield_mc = {s.name + (args.selectSys if sys else ""):s.scale*s.getYieldFromDraw( selectionString =  addSys(normalization_selection_string ), weightString = mc_weight_string)['val'] for s in mc}
    if mode == "all": yield_data = sum(s.getYieldFromDraw(       selectionString = normalization_selection_string, weightString = data_weight_string)['val'] for s in data_sample )
    else:             yield_data = data_sample.getYieldFromDraw( selectionString = normalization_selection_string, weightString = data_weight_string)['val']

    plotting.fill(plots, read_variables = read_variables, sequence = sequence)

    waitForLock( result_file ) 
    if os.path.exists(result_file):
      (allPlots, yields) = pickle.load(file( result_file ))
      allPlots.update({p.name : p.histos for p in plots})
      yields.update(yield_mc)
    else:                           
      allPlots = {p.name : p.histos for p in plots}
      yields = yield_mc
    yields['data'] = yield_data
    pickle.dump( (allPlots, yields), file( result_file, 'w' ) )
    removeLock( result_file ) 
    logger.info( "Done for sys " + args.selectSys )

#    # Write one  pkl file sys
#    result_file = os.path.join(plot_directory, args.plot_directory, mode, args.selection, 'results_%s.pkl' % args.selectSys )
#    allPlots = {p.name : p.histos for p in plots}
#    yields = yield_mc
#    yields['data'] = yield_data
#    pickle.dump( (allPlots, yields), file( result_file, 'w' ) )

  else:
    (allPlots, yields) = pickle.load(file( result_file ))
#    allPlots, yields = {}, {}
#    dirname = os.path.join(plot_directory, args.plot_directory, mode, args.selection)
#    for filename in os.listdir( dirname ):
#        if filename.startswith('results_') and filename.endswith('.pkl'):
#            (allPlots_, yields_) = pickle.load(file( os.path.join(dirname, filename) ))
#            allPlots.update( allPlots_ )
#            yields.update( yields_ )

    from RootTools.plot.Plot import addOverFlowBin1D
    for p in plots:
      p.histos = allPlots[p.name]
      for s in p.histos:
        for h in s:
          addOverFlowBin1D(h, "upper")
          if h.Integral()==0: logger.warning( "Found empty histogram %s in results file %s", h.GetName(), result_file )

    topName = Top_pow.name if args.powheg else Top.name
    top_sf = {}

    dataMCScaling = True
    if dataMCScaling:
      yield_data    = yields['data']
      yield_non_top = sum(yields[s.name + 'None'] for s in mc if s.name != topName)
      top_sf[None]  = (yield_data - yield_non_top)/yields[topName+'None']
      total         = yield_data
      logger.info( "Data: %i MC TT %3.2f MC other %3.2f SF %3.2f", yield_data, yields[topName+'None'], yield_non_top, top_sf[None] )
      if args.selection.count('njet01-btag0-looseLeptonVeto-mll20-metInv') and mode != "mue":
        top_sf[None] = 1
    else:
      top_sf[None] = 1
      total        = sum(yield_mc.values())


    #Scaling systematic shapes to MT2ll<100 region
    for sys_pair in sys_pairs:
      for sys in sys_pair[1:]:
        if not top_sf.has_key( sys ):
            mc_sys_weight_func, mc_sys_weight_string = weightMC( sys = sys )
            non_top                                  = sum(yields[s.name+sys] for s in mc if s.name != topName)
            top_sf[sys]                              = (total - non_top)/yields[topName+sys]
            logger.info( "Total: %i sys %s MC TT %3.2f MC other %3.2f SF %3.2f", total, sys, yields[topName+sys], non_top, top_sf[sys] )

            if args.selection.count('njet01-btag0-looseLeptonVeto-mll20-metInv') and mode != "mue":
              top_sf[sys] = 1
              logger.info( "NOT scaling top for " + args.selection + " (mode " + mode + ")" )


    for plot_mc, plot_data, bin_width in plotConfigs:
      if args.normalizeBinWidth and bin_width>0:
        for p in plot_mc.values() + [plot_data]:
          for histo in sum(p.histos, []): 
            for ib in range(histo.GetXaxis().GetNbins()+1):
              val = histo.GetBinContent( ib )
              err = histo.GetBinError( ib )
              width = histo.GetBinWidth( ib )
              histo.SetBinContent(ib, val / (width / bin_width)) 
              histo.SetBinError(ib, err / (width / bin_width)) 
      topHist = None
      ttzHist = None
      ttxHist = None
      mbHist  = None
      dyHist  = None

      # Scaling Top
      for k in plot_mc.keys():
        for s in plot_mc[k].histos:
      #    for h in s:
      #      h.Scale(lumi_scale)
          pos_top = [i for i,x in enumerate(mc) if x == (Top_pow if args.powheg else Top)][0]
          pos_ttz = [i for i,x in enumerate(mc) if x == TTZ_LO][0]
          pos_ttx = [i for i,x in enumerate(mc) if x == TTXNoZ][0]
          pos_dy  = [i for i,x in enumerate(mc) if x == DY_HT_LO][0]
          pos_mb  = [i for i,x in enumerate(mc) if x == multiBoson][0]
          plot_mc[k].histos[0][pos_top].Scale(top_sf[k])
          topHist = plot_mc[k].histos[0][pos_top]
          ttzHist = plot_mc[k].histos[0][pos_ttz]
          ttxHist = plot_mc[k].histos[0][pos_ttx]
          mbHist  = plot_mc[k].histos[0][pos_mb]
          dyHist  = plot_mc[k].histos[0][pos_dy]
          
      #Calculating systematics
      h_summed = {k: plot_mc[k].histos_added[0][0].Clone() for k in plot_mc.keys()}

      ##Normalize systematic shapes
      #if args.sysScaling:
      #    for k in h_summed.keys():
      #        if k is None: continue
      #        h_summed[k].Scale( top_sf[ k ] )

      h_rel_err = h_summed[None].Clone()
      h_rel_err.Reset()

      #MC statistical error
      for ib in range( 1 + h_rel_err.GetNbinsX() ):
          h_rel_err.SetBinContent(ib, h_summed[None].GetBinError(ib)**2 )

      h_sys = {}
      goOn = False
      for k, s1, s2 in ([s for s in sys_pairs if s[0] == args.showOnly] if args.showOnly else sys_pairs):
        goOn = True
        h_sys[k] = h_summed[s1].Clone()
        h_sys[k].Scale(-1)
        h_sys[k].Add(h_summed[s2])
      if not goOn: continue

      # Adding in quadrature
      for k in h_sys.keys():
          for ib in range( 1 + h_rel_err.GetNbinsX() ):
            h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + h_sys[k].GetBinContent(ib)**2 )

      # When making plots with mt2ll > 100 GeV, include also our background shape uncertainties
      if args.selection.count('mt2ll100') or plot_mc == dl_mt2ll_mc and False:
        for ib in range(1 + h_rel_err.GetNbinsX() ):
          if plot_mc == dl_mt2ll_mc and h_rel_err.GetBinCenter(ib) < 100: continue
          topUnc = 1 if (plot_mc == dl_mt2ll_mc and h_rel_err.GetBinCenter(ib) > 240) else 0.5
          h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (topUnc*topHist.GetBinContent(ib))**2 )
          h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (0.2*ttxHist.GetBinContent(ib))**2 )
          h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (0.25*ttxHist.GetBinContent(ib))**2 )
          h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (0.25*dyHist.GetBinContent(ib))**2 )
          h_rel_err.SetBinContent(ib, h_rel_err.GetBinContent(ib) + (0.25*mbHist.GetBinContent(ib))**2 )

      # take sqrt
      for ib in range( 1 + h_rel_err.GetNbinsX() ):
          h_rel_err.SetBinContent(ib, sqrt( h_rel_err.GetBinContent(ib) ) )

      # Divide
      h_rel_err.Divide(h_summed[None])

      plot = plot_mc[None]
      if args.normalizeBinWidth: plot.name += "_normalizeBinWidth"
      signal_histos = plot_data.histos[1:]
      data_histo    = plot_data.histos[0][0]
      for h in plot_data.histos[0][1:]:
        data_histo.Add(h)

      data_histo.style = styles.errorStyle( ROOT.kBlack )
      plot.histos += [[ data_histo ]]
      for h in signal_histos: plot.histos += [h]
      plot_data.stack[0][0].texName = data_sample.texName if mode != "all" else data_sample[0].texName 
      plot.stack += [[ plot_data.stack[0][0] ]]
      for i, signal in enumerate(signals):
        plot_data.stack[i+1][0].texName = signal.texName
        plot_data.stack[i+1][0].style   = signal.style
        plot.stack += [[ plot_data.stack[i+1][0] ]]

      boxes = []
      ratio_boxes = []
      for ib in range(1, 1 + h_rel_err.GetNbinsX() ):
          val = h_summed[None].GetBinContent(ib)
          if val<0: continue
          sys = h_rel_err.GetBinContent(ib)
          box = ROOT.TBox( h_rel_err.GetXaxis().GetBinLowEdge(ib),  max([0.03, (1-sys)*val]), h_rel_err.GetXaxis().GetBinUpEdge(ib), max([0.03, (1+sys)*val]) )
          box.SetLineColor(ROOT.kBlack)
          box.SetFillStyle(3444)
          box.SetFillColor(ROOT.kBlack)
          r_box = ROOT.TBox( h_rel_err.GetXaxis().GetBinLowEdge(ib),  max(0.1, 1-sys), h_rel_err.GetXaxis().GetBinUpEdge(ib), min(1.9, 1+sys) )
          r_box.SetLineColor(ROOT.kBlack)
          r_box.SetFillStyle(3444)
          r_box.SetFillColor(ROOT.kBlack)

          boxes.append( box )
          ratio_boxes.append( r_box )

          ratio = {'yRange':(0.1,1.9), 'drawObjects':ratio_boxes}
             

      for log in [False, True]:
        plotDir = os.path.join(plot_directory, args.plot_directory, mode + ("_log" if log else "") + "_scaled", args.selection)
        if args.copyIndexPHP:
            copyIndexPHP( os.path.join(plot_directory, args.plot_directory, mode + ("_log" if log else "") + "_scaled") )
            copyIndexPHP(plotDir)
        if args.showOnly: plotDir = os.path.join(plotDir, "only_" + args.showOnly)
        plotting.draw(plot,
            plot_directory = plotDir,
            ratio = ratio,
            legend = (0.50,0.88-0.04*sum(map(len, plot.histos)),0.95,0.88),
            logX = False, logY = log, #sorting = True,
            yRange = (0.03, "auto"),
            drawObjects = drawObjects( True, top_sf[None], lumi_scale ) + boxes,
            copyIndexPHP = args.copyIndexPHP
        )
