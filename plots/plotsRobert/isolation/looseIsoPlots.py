#Standard imports
import ROOT
from math import sqrt, cos, sin, pi, acos, atan2
import itertools
import pickle

#RootTools
from RootTools.core.standard import *

#StopsDilepton
from StopsDilepton.tools.helpers import getCollection, deltaR
from StopsDilepton.tools.objectSelection import getFilterCut
from StopsDilepton.tools.objectSelection import getGoodAndOtherLeptons, leptonVars_data, default_ele_selector, default_muon_selector, getLeptons, getOtherLeptons, getGoodLeptons, eleSelector, muonSelector
from StopsDilepton.tools.mt2Calculator import mt2Calculator
mt2Calc = mt2Calculator() 

# argParser
import argparse
argParser = argparse.ArgumentParser(description = "Argument parser")
argParser.add_argument('--logLevel', 
      action='store',
      nargs='?',
      choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET'],
      default='INFO',
      help="Log level for logging"
)

argParser.add_argument('--mode',
    default='doubleEle',
    action='store',
    choices=['doubleMu', 'doubleEle',  'muEle'])

argParser.add_argument('--isolation',
    default='standard',
    #default='VeryLoose',
    action='store',
    choices=['VeryLoose', 'VeryLooseInverted', 'VeryLoosePt10', 'standard'])

argParser.add_argument('--charges',
    default='OS',
    action='store',
    choices=['OS', 'SS'])

argParser.add_argument('--zMode',
    default='offZ',
    action='store',
    choices=['onZ', 'offZ', 'allZ']
)

argParser.add_argument('--noData',
    action='store_true',
    help='Skip data',
)

argParser.add_argument('--small',
    action='store_true',
    #default = True,
    help='Small?',
)

argParser.add_argument('--removeLeptonsFromMET',
    action='store_true',
    #default = True,
    help='Try that for Alexis.',
)

argParser.add_argument('--reversed',
    action='store_true',
    help='Reversed?',
)

argParser.add_argument('--signals',
    action='store',
    nargs='*',
    type=str,
    default=[],
    help="Signals?"
    )

argParser.add_argument('--overwrite',
#    default = False,
    default = True,
    action='store_true',
    help='overwrite?',
)

argParser.add_argument('--plot_directory',
    default='80X_looseIso',
    action='store',
)

args = argParser.parse_args()

# Logging
import StopsDilepton.tools.logger as logger
logger = logger.get_logger(args.logLevel, logFile = None )
import RootTools.core.logger as logger_rt
logger_rt = logger_rt.get_logger(args.logLevel, logFile = None )

#make samples

if args.isolation=='standard':
    data_directory = "/afs/hephy.at/data/dspitzbart01/cmgTuples/"
    postProcessing_directory = "postProcessed_80X_v30/dilep/"
    from StopsDilepton.samples.cmgTuples_Summer16_mAODv2_postProcessed import *
    data_directory = "/afs/hephy.at/data/rschoefbeck02/cmgTuples/"
    postProcessing_directory = "postProcessed_80X_v31/dilep/"
    from StopsDilepton.samples.cmgTuples_Data25ns_80X_03Feb_postProcessed import *

elif args.isolation=="VeryLoose" or args.isolation=="VeryLooseInverted":
    #postProcessing_directory = "postProcessed_80X_v12/dilepVeryLoose/" 
    raise NotImplementedError
else: raise ValueError
    
def getZCut(mode):
    mZ = 91.2
    zstr = "abs(dl_mass - "+str(mZ)+")"
    if mode.lower()=="onz": return zstr+"<15"
    if mode.lower()=="offz": return zstr+">15"
    return "(1)"

if args.mode=="doubleMu":
    leptonSelectionString = "&&".join(["isMuMu==1&&nGoodMuons==2&&nGoodElectrons==0", getZCut(args.zMode)])
    data_sample = DoubleMuon_Run2016_backup if not args.noData else None
    #qcd_sample = QCD_Mu5 #FIXME
elif args.mode=="doubleEle":
    leptonSelectionString = "&&".join(["isEE==1&&nGoodMuons==0&&nGoodElectrons==2", getZCut(args.zMode)])
    data_sample = DoubleEG_Run2016_backup if not args.noData else None
    #qcd_sample = QCD_EMbcToE
elif args.mode=="muEle":
    leptonSelectionString = "&&".join(["isEMu==1&&nGoodMuons==1&&nGoodElectrons==1", getZCut(args.zMode)])
    data_sample = MuonEG_Run2016_backup if not args.noData else None
    #qcd_sample = QCD_Mu5EMbcToE
else:
    raise ValueError( "Mode %s not known"%args.mode )

# Extra requirements on data
mcFilterCut   = getFilterCut(isData=False) 
dataFilterCut = getFilterCut(isData=True) +"&&weight>0"

#mc = [ DY, TTJets, qcd_sample, singleTop, TTX, diBoson, triBoson, WJetsToLNu]
#mc = [ DY, TTJets, qcd_sample, TTZ]
TTJets_1l    = TTJets_Singlelep
TTJets_1l.name = "TTJets_1l"
TTJets_1l.texName = "TTJets 1l"
TTJets_1l.color = ROOT.kAzure - 2

#ttjets_sample = TTJets_Dilep
ttjets_2l_sample = TTLep_pow

TTJets_l2_prompt    = ttjets_2l_sample
TTJets_l2_prompt.name = "TTJets_2l_prompt"
TTJets_l2_prompt.texName = "TTJets 2l (prompt)"
TTJets_l2_prompt.weight = lambda event, sample: not event.l2_matched_nonPrompt

TTJets_l2_nonPrompt = copy.deepcopy(ttjets_2l_sample)
TTJets_l2_nonPrompt.name = "TTJets_2l_nonPrompt"
TTJets_l2_nonPrompt.texName = "TTJets 2l (non-prompt)"
TTJets_l2_nonPrompt.weight = lambda event, sample: event.l2_matched_nonPrompt
TTJets_l2_nonPrompt.color = ROOT.kAzure + 9

mc = [ DY_HT_LO, TTJets_l2_prompt, TTJets_1l, singleTop, TTZ, TTXNoZ, diBoson, triBoson, TTJets_l2_nonPrompt]
mc_for_normalization = [ DY_HT_LO, TTLep_pow, singleTop, TTZ, TTXNoZ, diBoson, triBoson]

if args.small:
    for s in mc + mc_for_normalization:
        s.reduceFiles(to = 1)

if not args.noData:
    data_sample.style = styles.errorStyle( ROOT.kBlack )
    lumi_scale = data_sample.lumi/1000

for sample in mc:
    sample.style = styles.fillStyle( sample.color)

from StopsDilepton.tools.user import plot_directory

# official PU reweighting
weight = lambda event, sample:event.weight

cuts=[
]

if args.isolation=="VeryLooseInverted":
    cuts+=[ ("trailingLepNonIso", "l2_relIso03>0.12") ]

cuts+=[
    ("njet2", "(Sum$(JetGood_pt>30&&abs(JetGood_eta)<2.4&&JetGood_id))>=2"),
    ("nbtag1", "Sum$(JetGood_pt>30&&abs(JetGood_eta)<2.4&&JetGood_id&&JetGood_btagCSV>0.800)>=1"),
#    ("mll20", "dl_mass>20"),
    ("met80", "met_pt>80"),
    ("metSig5", "met_pt/sqrt(Sum$(JetGood_pt*(JetGood_pt>30&&abs(JetGood_eta)<2.4&&JetGood_id)))>5"),
    ("dPhiJetMET", "Sum$( ( cos(met_phi-JetGood_phi)>cos(0.25) )*(Iteration$<2) )+Sum$( ( cos(met_phi-JetGood_phi)>0.8 )*(Iteration$==0) )==0"), 
]

def add_histos( l ):
    res = l[0].Clone()
    for h in l[1:]: res.Add(h)
    return res
                
def drawObjects( dataMCScale ):
    tex = ROOT.TLatex()
    tex.SetNDC()
    tex.SetTextSize(0.04)
    tex.SetTextAlign(11) # align right

    lines = [ (0.15, 0.95, 'CMS Preliminary') ]
    if dataMCScale is not None: 
        lines.append( (0.45, 0.95, 'L=%3.2f fb{}^{-1} (13 TeV) Scale %3.2f'% ( int(data_sample.lumi/100)/10., dataMCScale ) ) )
    else:
        lines.append( (0.50, 0.95, '13 TeV' ) )
    return [tex.DrawLatex(*l) for l in lines] 

stack = Stack(mc)
if not args.noData:
    stack.append( [data_sample] )

def fromTau( gen_lepton ):
    return gen_lepton['n_tau']>0
def prompt( gen_lepton ):
    return not fromTau( gen_lepton) and gen_lepton['n_B']==0 and gen_lepton['n_D']==0
def nonPrompt( gen_lepton ):
    return not fromTau( gen_lepton) and not ( gen_lepton['n_B']==0 and gen_lepton['n_D']==0 ) 

gen_ttbar_sequence = []

# Match l1 and l2
def matchLeptons( event, sample ):
    # Get Gen leptons
    gen_leps = getCollection(event, "GenLep", ["pt", "eta", "phi", "n_t", "n_W", "n_B", "n_D", "n_tau", "pdgId"], "nGenLep" )
    non_prompt = filter(lambda l: nonPrompt(l), gen_leps )
    # Get selected leptons
    l1 = {'pt':event.l1_pt, 'eta':event.l1_eta, 'phi':event.l1_phi, 'pdgId':event.l1_pdgId} 
    l2 = {'pt':event.l2_pt, 'eta':event.l2_eta, 'phi':event.l2_phi, 'pdgId':event.l2_pdgId} 
    # match l1 and l2 
    event.l1_matched_nonPrompt = False 
    event.l2_matched_nonPrompt = False 
    for gl in non_prompt:
        if gl['pdgId']==l1['pdgId'] and deltaR(gl, l1)<0.2 and abs(1-gl['pt']/l1['pt'])<0.5:
            event.l1_matched_nonPrompt = True
        if gl['pdgId']==l2['pdgId'] and deltaR(gl, l2)<0.2 and abs(1-gl['pt']/l2['pt'])<0.5:
            event.l2_matched_nonPrompt = True
    return

gen_ttbar_sequence.append( matchLeptons )

read_variables = [\
    "weight/F" , "JetGood[pt/F,eta/F,phi/F]", 
    "l1_pt/F", "l1_eta/F", "l1_phi/F", "l1_pdgId/I",
    "l2_pt/F", "l2_eta/F", "l2_phi/F", "l2_pdgId/I",
]

read_variables.extend([\
    "nLepGood/I",  "LepGood[pt/F,eta/F,etaSc/F,phi/F,pdgId/I,tightId/I,miniRelIso/F,relIso03/F,sip3d/F,mediumMuonId/I,mvaIdSpring15/F,lostHits/I,convVeto/I,dxy/F,dz/F,jetPtRelv2/F,jetPtRatiov2/F,eleCutId_Spring2016_25ns_v1_ConvVetoDxyDz/I]",
    "nLepOther/I", "LepOther[pt/F,eta/F,etaSc/F,phi/F,pdgId/I,tightId/I,miniRelIso/F,relIso03/F,sip3d/F,mediumMuonId/I,mvaIdSpring15/F,lostHits/I,convVeto/I,dxy/F,dz/F,jetPtRelv2/F,jetPtRatiov2/F,eleCutId_Spring2016_25ns_v1_ConvVetoDxyDz/I]",
])

def fs(pdgId):
    if abs(pdgId)==11:
        return "e"
    elif abs(pdgId)==13:
        return "m"
    else: raise ValueError

mu_selector = muonSelector( relIso03 = 0.2 )
ele_selector = eleSelector( relIso03 = 0.2 )

sequence = []

if args.isolation == "standard":
    def initSwappedMT2ll( event, sample ):
        # initial values
        for fh in ["leadingLepIso", "leadingLepNonIso"]:
            for swap in ["L1", "L2"]:
                for fs in ["mm","me","em","ee"]:
                    setattr(event, "dl_mt2ll_%s_swap%s_%s"%(fh, swap, fs), float('nan') )
                    # print "dl_mt2ll_%s_swap%s_%s"%(fh, swap, fs)

    sequence.append( initSwappedMT2ll )

    def makeSwappedMT2ll(event, l1, l2, nonIsoLep, verbose = False):
        mt2Calc.reset()


        # swap l1
        final_hierarchy = "leadingLepNonIso" if nonIsoLep['pt']>l2['pt'] else "leadingLepIso"
        l1p, l2p = (nonIsoLep, l2) if nonIsoLep['pt']>l2['pt'] else (l2, nonIsoLep)
        finalState = "".join(fs(p['pdgId']) for p in [l1p, l2p])
        pfix = "_".join([final_hierarchy, "swapL1", finalState])
        mt2Calc.setLeptons(l1p['pt'], l1p['eta'], l1p['phi'], l2p['pt'], l2p['eta'], l2p['phi'])
        if args.removeLeptonsFromMET:
            d_met_x = l1['pt']*cos(l1['phi']) + l2['pt']*cos(l2['phi']) - l1p['pt']*cos(l1p['phi']) - l2p['pt']*cos(l2p['phi'])
            d_met_y = l1['pt']*sin(l1['phi']) + l2['pt']*sin(l2['phi']) - l1p['pt']*sin(l1p['phi']) - l2p['pt']*sin(l2p['phi'])
            met_corr_x = event.met_pt*cos(event.met_phi) + d_met_x
            met_corr_y = event.met_pt*sin(event.met_phi) + d_met_y

            met_corr = sqrt( met_corr_x**2 + met_corr_y**2 )
            met_phi_corr = atan2( met_corr_y, met_corr_x ) 
            mt2Calc.setMet( met_corr, met_phi_corr )
        else:
            mt2Calc.setMet(event.met_pt, event.met_phi)
        setattr(event, "dl_mt2ll_"+pfix, mt2Calc.mt2ll() )

        if verbose: print "dl_mt2ll_"+pfix, mt2Calc.mt2ll()

        # swap l2
        final_hierarchy = "leadingLepNonIso" if nonIsoLep['pt']>l1['pt'] else "leadingLepIso"
        l1p, l2p = (nonIsoLep, l1) if nonIsoLep['pt']>l1['pt'] else (l1, nonIsoLep)
        finalState = "".join(fs(p['pdgId']) for p in [l1p, l2p])
        pfix = "_".join([final_hierarchy, "swapL2", finalState])
        mt2Calc.setLeptons(l1p['pt'], l1p['eta'], l1p['phi'], l2p['pt'], l2p['eta'], l2p['phi'])
        if args.removeLeptonsFromMET:
            d_met_x = l1['pt']*cos(l1['phi']) + l2['pt']*cos(l2['phi']) - l1p['pt']*cos(l1p['phi']) - l2p['pt']*cos(l2p['phi'])
            d_met_y = l1['pt']*sin(l1['phi']) + l2['pt']*sin(l2['phi']) - l1p['pt']*sin(l1p['phi']) - l2p['pt']*sin(l2p['phi'])
            met_corr_x = event.met_pt*cos(event.met_phi) + d_met_x
            met_corr_y = event.met_pt*sin(event.met_phi) + d_met_y

            met_corr = sqrt( met_corr_x**2 + met_corr_y**2 )
            met_phi_corr = atan2( met_corr_y, met_corr_x ) 
            mt2Calc.setMet( met_corr, met_phi_corr )
        else:
            mt2Calc.setMet(event.met_pt, event.met_phi)

        setattr(event, "dl_mt2ll_"+pfix, mt2Calc.mt2ll() )

        if verbose: print "dl_mt2ll_"+pfix, mt2Calc.mt2ll() 

    verbose = False
    def makeNonIsoLeptons( event, sample ):

        goodLeptons = getGoodLeptons( event, collVars = leptonVars_data , mu_selector = mu_selector, ele_selector = ele_selector)
        allExtraLeptons = sorted( \
            [l for l in getLeptons( event, collVars = leptonVars_data ) if l not in goodLeptons] + getOtherLeptons( event , collVars = leptonVars_data ), 
                        key=lambda l: -l['pt'] )

        #for l in goodLeptons:
        #    print "good", l
        #for l in allExtraLeptons:
        #    print "extra", l
        #print len(goodLeptons), len(allExtraLeptons) 
        assert len(goodLeptons)==2, "Analysis leptons not found!"
        l1, l2 = goodLeptons
        #print l1['pt'] - event.l1_pt, l2['pt'] - event.l2_pt
        event.allExtraLeptons = allExtraLeptons

        nonIsoMus  = filter(lambda l: abs(l['pdgId'])==13 and l['relIso03']>0.12 and l['pt']>5, allExtraLeptons )
        nonIsoEles = filter(lambda l: abs(l['pdgId'])==11 and l['relIso03']>0.12 and l['pt']>7, allExtraLeptons )
        #print nonIsoMus, nonIsoEles

        event.nonIsoMu  = nonIsoMus[-1] if len(nonIsoMus)>0 else None 
        event.nonIsoEle = nonIsoEles[-1] if len(nonIsoEles)>0 else None 

        # extra ele
        if event.nonIsoEle is not None:
            makeSwappedMT2ll( event, l1, l2, event.nonIsoEle, verbose = verbose)
        # extra mu
        if event.nonIsoMu is not None:
            makeSwappedMT2ll( event, l1, l2, event.nonIsoMu, verbose = verbose)
        if verbose: print

    sequence.append( makeNonIsoLeptons )

for sample in [TTJets_l2_prompt, TTJets_l2_nonPrompt]:
    sample.sequence = gen_ttbar_sequence        
    sample.read_variables = [ "nGenLep/I", "GenLep[pt/F,eta/F,phi/F,n_t/I,n_W/I,n_B/I,n_D/I,n_tau/I,pdgId/I]"]

#rev = reversed if args.reversed else lambda x:x
#for i_comb in rev( range( len(cuts)+1 ) ):
for i_comb in [len(cuts)]:
    for comb in itertools.combinations( cuts, i_comb ):

        if not args.noData: data_sample.setSelectionString([dataFilterCut])
        for sample in mc:
            sample.setSelectionString([ mcFilterCut ])

        if args.charges=="OS":
            presel = [("isOS","isOS")]
        elif args.charges=="SS":
            presel = [("isSS","l1_pdgId*l2_pdgId>0")]
        else:
            raise ValueError

        # presel += [("highMiniRelIso","max(l1_miniRelIso,l2_miniRelIso)>0.4")]
 
        presel.extend( comb )

        ppfixes = [args.mode, args.zMode, args.isolation]
        if args.small: ppfixes = ['small'] + ppfixes
        prefix = '_'.join( ppfixes + [ '-'.join([p[0] for p in presel ] ) ] )
        if args.removeLeptonsFromMET:
            prefix += "_removeLeptonsFromMET"

        plot_path = os.path.join(plot_directory, args.plot_directory, prefix)

        if os.path.exists(plot_path) and not args.overwrite:
            logger.info( "Path %s not empty. Skipping."%path )
            continue

        if "nbtag1" in prefix and "nbtag0" in prefix: continue

        selectionString = "&&".join( [p[1] for p in presel] + [leptonSelectionString] )

        logger.info( "Now plotting with prefix %s and selectionString %s", prefix, selectionString )

        if not args.noData:
            logger.info( "Calculating normalization constants" )        
            yield_mc    = sum(s.getYieldFromDraw( selectionString = selectionString, weightString = 'weight')['val'] for s in mc_for_normalization)
            yield_data  = data_sample.getYieldFromDraw( selectionString = selectionString, weightString = 'weight')['val']

            for sample in mc:
                dataMCScale = yield_data/(yield_mc*lumi_scale)
                sample.scale = lumi_scale*dataMCScale

            logger.info( "Data/MC Scale: %4.4f Yield MC %4.4f Yield Data %4.4f Lumi-scale %4.4f", dataMCScale, yield_mc, yield_data, lumi_scale )
        else:
            dataMCScale = None 


        plots = []

        dl_mass  = Plot(
            texX = 'm(ll) (GeV)', texY = 'Number of Events / 3 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_mass/F" ),
            binning=[150/3,0,150],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( dl_mass )

        dl_pt  = Plot(
            texX = 'p_{T}(ll) (GeV)', texY = 'Number of Events / 10 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_pt/F" ),
            binning=[40,0,400],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( dl_pt )

        dl_eta  = Plot(
            texX = '#eta(ll) ', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_eta/F" ),
            binning=[30,-3,3],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( dl_eta )

        dl_phi  = Plot(
            texX = '#phi(ll) (GeV)', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_phi/F" ),
            binning=[30,-pi,pi],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( dl_phi )

        dl_mt2ll  = Plot(
            texX = 'MT_{2}^{ll} (GeV)', texY = 'Number of Events / 15 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_mt2ll/F" ),
            binning=[300/15,0,300],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( dl_mt2ll )

        if args.isolation == "standard":
            mt2ll_leadingLepIso_swapL1_mm  = Plot(
                name = "mt2ll_leadingLepIso_swapL1_mm",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l1, mm)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL1_mm,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL1_mm )

            mt2ll_leadingLepIso_swapL2_mm  = Plot(
                name = "mt2ll_leadingLepIso_swapL2_mm",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l2, mm)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL2_mm,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL2_mm )

            mt2ll_leadingLepIso_swapL1_me  = Plot(
                name = "mt2ll_leadingLepIso_swapL1_me",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l1, me)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL1_me,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL1_me )

            mt2ll_leadingLepIso_swapL2_me  = Plot(
                name = "mt2ll_leadingLepIso_swapL2_me",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l2, me)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL2_me,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL2_me )

            mt2ll_leadingLepIso_swapL1_em  = Plot(
                name = "mt2ll_leadingLepIso_swapL1_em",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l1, em)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL1_em,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL1_em )

            mt2ll_leadingLepIso_swapL2_em  = Plot(
                name = "mt2ll_leadingLepIso_swapL2_em",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l2, em)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL2_em,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL2_em )

            mt2ll_leadingLepIso_swapL1_ee  = Plot(
                name = "mt2ll_leadingLepIso_swapL1_ee",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l1, ee)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL1_ee,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL1_ee )

            mt2ll_leadingLepIso_swapL2_ee  = Plot(
                name = "mt2ll_leadingLepIso_swapL2_ee",
                texX = 'MT_{2}^{ll}(l.l. Iso, swap l2, ee)', texY = 'Number of Events / 15 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.dl_mt2ll_leadingLepIso_swapL2_ee,
                binning=[300/15,0,300],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( mt2ll_leadingLepIso_swapL2_ee )

            extra_mu_pt  = Plot(
                name = "extra_mu_pt",
                texX = 'p_{T}(extra #mu) (GeV)', texY = 'Number of Events / 1 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.nonIsoMu['pt'] if event.nonIsoMu is not None else float('nan'),
                binning=[30,0,30],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( extra_mu_pt )

            extra_ele_pt  = Plot(
                name = "extra_ele_pt",
                texX = 'p_{T}(extra e) (GeV)', texY = 'Number of Events / 1 GeV',
                stack = stack, 
                attribute = lambda event, sample:event.nonIsoEle['pt'] if event.nonIsoEle is not None else float('nan'),
                binning=[30,0,30],
                selectionString = selectionString,
                weight = weight,
                )
            plots.append( extra_ele_pt )

        dl_mt2bb  = Plot(
            texX = 'MT_{2}^{bb} (GeV)', texY = 'Number of Events / 15 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_mt2bb/F" ),
            binning=[300/15,0,300],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( dl_mt2bb )

        dl_mt2blbl  = Plot(
            texX = 'MT_{2}^{blbl} (GeV)', texY = 'Number of Events / 15 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "dl_mt2blbl/F" ),
            binning=[300/15,0,300],
            selectionString = selectionString,
            weight = weight,
            ) 
        plots.append( dl_mt2blbl )
         
        l1_pt  = Plot(
            texX = 'p_{T}(l_{1}) (GeV)', texY = 'Number of Events / 5 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "l1_pt/F" ),
            binning=[60,0,300],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_pt )

        l1_eta  = Plot(
            texX = '#eta(l_{1})', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "l1_eta/F" ),
            binning=[36,-3.3,3.3],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_eta )

        l1_phi  = Plot(
            texX = '#phi(l_{1})', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "l1_phi/F" ),
            binning=[30,-pi,pi],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_phi )

        l1_miniRelIso  = Plot(
            texX = 'I_{rel.mini}', texY = 'Number of Events / 5 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "l1_miniRelIso/F" ),
            binning=[40,0,2],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_miniRelIso )

        l1_dxy  = Plot(
            name = "l1_dxy",
            texX = '|d_{xy}|', texY = 'Number of Events',
            stack = stack, 
            attribute = lambda event, sample:abs(event.l1_dxy), 
            read_variables = ["l1_dxy/F"],
            binning=[40,0,1],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_dxy )

        l1_dz  = Plot(
            name = "l1_dz",
            texX = '|d_{z}|', texY = 'Number of Events',
            stack = stack, 
            attribute = lambda event, sample:abs(event.l1_dz), 
            read_variables = ["l1_dz/F"],
            binning=[40,0,0.15],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_dz )

        l1_pdgId  = Plot(
            texX = 'pdgId(l_{1})', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "l1_pdgId/I" ),
            binning=[32,-16,16],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l1_pdgId )

        l2_pt  = Plot(
            texX = 'p_{T}(l_{2}) (GeV)', texY = 'Number of Events / 5 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "l2_pt/F" ),
            binning=[60,0,300],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_pt )

        l2_eta  = Plot(
            texX = '#eta(l_{2})', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "l2_eta/F" ),
            binning=[30,-3,3],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_eta )

        l2_phi  = Plot(
            texX = '#phi(l_{2})', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "l2_phi/F" ),
            binning=[30,-pi,pi],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_phi )

        l2_miniRelIso  = Plot(
            texX = 'I_{rel.mini}', texY = 'Number of Events / 5 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "l2_miniRelIso/F" ),
            binning=[40,0,2],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_miniRelIso )

        l2_dxy  = Plot(
            name = "l2_dxy",
            texX = '|d_{xy}|', texY = 'Number of Events',
            stack = stack, 
            attribute = lambda event, sample:abs(event.l2_dxy), 
            read_variables = ["l2_dxy/F"],
            binning=[40,0,1],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_dxy )

        l2_dz  = Plot(
            name = "l2_dz",
            texX = '|d_{z}|', texY = 'Number of Events',
            stack = stack, 
            attribute = lambda event, sample:abs(event.l2_dz), 
            read_variables = ["l2_dz/F"],
            binning=[40,0,0.15],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_dz )

        l2_pdgId  = Plot(
            texX = 'pdgId(l_{2})', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "l2_pdgId/I" ),
            binning=[32,-16,16],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( l2_pdgId )

        metZoomed  = Plot(
            name = "met_pt_zoomed",
            texX = '#slash{E}_{T} (GeV)', texY = 'Number of Events / 10 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "met_pt/F" ),
            binning=[22,0,220],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( metZoomed )

        met  = Plot(
            texX = '#slash{E}_{T} (GeV)', texY = 'Number of Events / 50 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "met_pt/F" ),
            binning=[1050/50,0,1050],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( met )

        JZB  = Plot(
            name = "JZB",
            texX = 'JZB (GeV)', texY = 'Number of Events / 32 GeV',
            stack = stack, 
            attribute = lambda event, sample: sqrt( (event.met_pt*cos(event.met_phi)+event.dl_pt*cos(event.dl_phi))**2 + (event.met_pt*sin(event.met_phi)+event.dl_pt*sin(event.dl_phi))**2) - event.dl_pt, 
            read_variables =  ["met_phi/F", "dl_phi/F", "met_pt/F", "dl_pt/F"],
            binning=[25,-200,600],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( JZB )

        metSig  = Plot(
            name = "metSig",
            texX = '#slash{E}_{T}/#sqrt{H_{T}} (GeV^{1/2})', texY = 'Number of Events / 100 GeV',
            stack = stack, 
            attribute = lambda event, sample: event.met_pt/sqrt(event.ht) if event.ht>0 else float('nan'), 
            read_variables = ["met_pt/F", "ht/F"],
            binning=[30,0,30],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( metSig )

        ht  = Plot(
            texX = 'H_{T} (GeV)', texY = 'Number of Events / 100 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "ht/F" ),
            binning=[2600/100,0,2600],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( ht )

        ht_zoomed  = Plot(
            name = "ht_zoomed",
            texX = 'H_{T} (GeV)', texY = 'Number of Events / 30 GeV',
            stack = stack, 
            attribute = TreeVariable.fromString( "ht/F" ),
            binning=[390/15,0,390],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( ht_zoomed )

        nbtags  = Plot(
            texX = 'number of b-tags (CSVM)', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString('nBTag/I'),
            binning=[8,0,8],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( nbtags )

        njets  = Plot(
            texX = 'number of jets', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString('nJetGood/I'),
            binning=[14,0,14],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( njets )

        nVert  = Plot(
            texX = 'vertex multiplicity', texY = 'Number of Events',
            stack = stack, 
            attribute = TreeVariable.fromString( "nVert/I" ),
            binning=[50,0,50],
            selectionString = selectionString,
            weight = weight,
            )
        plots.append( nVert )

        plotting.fill(plots, read_variables = read_variables, sequence = sequence)
        if not os.path.exists( plot_path ): os.makedirs( plot_path )

        ratio = {'yRange':(0.1,1.9)} if not args.noData else None

        for plot in plots:
            plotting.draw(plot, 
                plot_directory = plot_path, ratio = ratio, 
                logX = False, logY = True, sorting = True, 
                yRange = (0.03, "auto"), 
                drawObjects = drawObjects( dataMCScale )
            )

        # Dump dl_mt2ll extra lepton histos
        if args.isolation=='standard':
            for fh in ["leadingLepIso"]:
                for swap in ["L1", "L2"]:
                    for fs in ["mm","me","em","ee"]:
                        ofile = os.path.join(plot_path, "dl_mt2ll_%s_swap%s_%s.pkl"%(fh, swap, fs))
                        pickle.dump(getattr( eval("mt2ll_%s_swap%s_%s"%(fh, swap, fs)), "histos"), file( ofile, 'w') )
                        logger.info( "Written %s", ofile )
        elif 'Loose' in args.isolation:
            # load mt2ll extra lepton histos (same directory but with isolation 'standard')
            histos = {}
            for m in ['doubleMu', 'doubleEle', 'muEle']:
                for fh in ["leadingLepIso"]:
                    for swap in ["L1", "L2"]:
                        for fs in ["mm","me","em","ee"]:
                            ofile = os.path.join(plot_directory, args.plot_directory, prefix.replace(args.isolation, "standard").replace("small_","").replace(args.mode, m), "dl_mt2ll_%s_swap%s_%s.pkl"%(fh, swap, fs))
                            if os.path.isfile(ofile):
                                logger.info( "Loading %s", ofile )
                                histos["%s_mt2ll_%s_swap%s_%s"%(m, fh, swap, fs)] = pickle.load( file( ofile) )
                            else:
                                logger.warning( "File not found: %s", ofile)

            # construct shape of swapped leptons
            if args.mode == 'doubleMu':
                fss = ["mm"]
            elif args.mode == 'doubleEle':
                fss = ['ee']
            elif args.mode== 'muEle':
                fss = ['em', 'me']
            else: raise ValueError( "Unknown mode %s"%args.mode )

            # sum up all contributions
            shape_histos = []
            for m in ['doubleMu', 'doubleEle', 'muEle']:
                for fh in ["leadingLepIso"]:
                    for swap in ["L1", "L2"]:
                        for fs in fss:
                            logger.info( "Adding %s_mt2ll_%s_swap%s_%s"%(m, fh, swap, fs) )
                            shape_histos.extend( histos["%s_mt2ll_%s_swap%s_%s"%(m, fh, swap, fs)][0] )

            shape = add_histos( shape_histos )
            #shape.Scale( dl_mt2ll.histos[0][ mc.index( TTJets_l2_nonPrompt  ) ].Integral() / shape.Integral() )
            bin_low, bin_high = shape.FindBin( 90 ), shape.FindBin( 290 )
            h_TTJets_l2_nonPrompt = dl_mt2ll.histos[0][ mc.index( TTJets_l2_nonPrompt  ) ] 
            shape.Scale( h_TTJets_l2_nonPrompt.Integral( bin_low, bin_high ) / shape.Integral( bin_low, bin_high ) )
            shape.style = styles.lineStyle( ROOT.kRed )

            plotting.draw(
                Plot.fromHisto(name = "dl_mt2ll_comp", histos = dl_mt2ll.histos + [[ shape ]], texX = dl_mt2ll.texX, texY = dl_mt2ll.texY),
                plot_directory = plot_path, #ratio = ratio, 
                logX = False, logY = True, sorting = False,
                 yRange = (0.003, "auto"), legend = None ,
                # scaling = {0:1},
                 drawObjects = drawObjects( dataMCScale )
            )
            plotting.draw(
                Plot.fromHisto(name = "dl_mt2ll_shape", histos = [[h_TTJets_l2_nonPrompt]] + [[ shape ]], texX = dl_mt2ll.texX, texY = dl_mt2ll.texY),
                plot_directory = plot_path, #ratio = ratio, 
                logX = False, logY = True, sorting = False,
                 yRange = (0.003, "auto"), legend = None ,
                # scaling = {0:1},
                 drawObjects = drawObjects( dataMCScale )
            )
             
        logger.info( "Done with prefix %s and selectionString %s", prefix, selectionString )

