from StopsDilepton.tools.localInfo import analysisOutputDir
import copy
#Numerical constants
zMassRange=15

#define samples
from StopsDilepton.samples.cmgTuples_Data25ns_mAODv2_postProcessed import *
from StopsDilepton.samples.cmgTuples_Spring15_mAODv2_25ns_1l_postProcessed import *

#choices for specific samples
DYSample      = DY #NLO M10t050 + M50
#DYSample      = DY_HT_LO #LO, HT binned including a low HT bin starting from zero from the inclusive sample
TTJetsSample  = TTJets #NLO
#TTJetsSample  = TTJets_Lep #LO, very large dilep + single lep samples

allChannels = ['all', 'EE', 'MuMu', 'EMu']

#to run on data
lumi = {'EMu':MuonEG_Run2015D['lumi'], 'MuMu':DoubleMuon_Run2015D['lumi'], 'EE':DoubleEG_Run2015D['lumi']}
#10/fb to run on MC
#lumi = {c:10000 for c in allChannels}

from systematics import jmeVariations
def getCuts(selectionModifier=None, nBTags=(1,-1)):
  if selectionModifier: assert selectionModifier in jmeVariations, "Don't know about systematic variation %r, take one of %s"%(selectionModifier, ",".join(jmeVariations))
  sysStr="" if not selectionModifier else "_"+selectionModifier
  nbstr = "nBTags" if not selectionModifier else "nbJets" #Correct stupid naming convention I already fixed in the postprocessing...

  assert nBTags[0]>=0 and (nBTags[1]>=nBTags[0] or nBTags[1]<0), "Not a good nBTags selection: %r"%nBTags
  nbtstr = nbstr+sysStr+">="+str(nBTags[0])
  kstr = "nbtag"+str(nBTags[0])
  if nBTags[1]>0: 
    nbtstr+= "&&"+nbstr+sysStr+"<="+str(nBTags[1])
    kstr+='-'+str(nBTags[1])
  return [
 ("isOS", "isOS"),
 ("njet2", "nGoodJets"+sysStr+">=2"),
 (kstr, nbtstr), 
# ("nbtag1", nbtstr),
# ("nbtag0", "Sum$(Jet_pt>30&&abs(Jet_eta)<2.4&&Jet_id&&Jet_btagCSV>0.890)==0"),
 ("mll20", "dl_mass>20"),
 ("met80", "met_pt"+sysStr+">80"),
 ("metSig5", "met_pt"+sysStr+"/sqrt(ht"+sysStr+")>5"),
 ("dPhiJet0-dPhiJet1", "cos(met_phi"+sysStr+"-Jet_phi[0])<cos(0.25)&&cos(met_phi"+sysStr+"-Jet_phi[1])<cos(0.25)"),
  ]

from StopsDilepton.analysis.setupHelpers import getZCut, loadChain
#import json
class _setup:
  def __init__(self):
    self.verbose=False
    self.analysisOutputDir = analysisOutputDir
    self.zMassRange   = zMassRange
    self.useTriggers=True
    self.lumi=lumi
    self.sys          = {'weight':'weightPU', 'reweight':[], 'selectionModifier':None}

    self.sample = {
    'DY':         {c:DYSample for c in allChannels},
    'TTJets' :    {c:TTJetsSample for c in allChannels},
    'singleTop' : {c:singleTop for c in allChannels},
    'TTZ'    :    {c:TTZ for c in allChannels},
    'diBoson':    {c:diBoson for c in allChannels},
    'triBoson' :  {c:triBoson for c in allChannels},
    'TTXNoZ'   :  {c:TTXNoZ for c in allChannels},
    'WJetsToLNu_HT' : {c: WJetsToLNu_HT for c in allChannels} ,
    'QCD'    :    {'MuMu':QCD_Mu5, 'EE': QCD_EMbcToE, 'EMu':QCD_Mu5EMbcToE, 'all':QCD_Mu5EMbcToE},
    'Data'   : {'MuMu':DoubleMuon_Run2015D, 'EE': DoubleEG_Run2015D, 'EMu':MuonEG_Run2015D},
    }
    for s in sum([s.values() for s in self.sample.values()],[]):
      loadChain(s)
    self.prefix = '-'.join(c[0] for c in getCuts())

  #Clone the setup and optinally modify the systematic variation
  def sysClone(self, sys=None):
    '''Clone setup and change systematic if provided'''
    res     = copy.copy(self)
    res.sys = copy.deepcopy(self.sys)
    if sys:
      for k in sys.keys():
        if k=='reweight':
#          res.sys[k]=list(set(res.sys[k]+sys[k])) #Add with unique elements 
          res.sys[k] = res.sys[k]+sys[k] #Add with unique elements 
          if len(res.sys[k])!=len(list(set(res.sys[k]))): print "Warning! non-exclusive list of reweights: %s"% ",".join(res.sys['k'])
        else:
          res.sys[k]=sys[k]# if sys[k] else res.sys[k]
    return res

  def weightString(self):
    wStr = setup.sys['weight']
    if setup.sys['reweight']:
      wStr += "*"+"*".join(setup.sys['reweight'])
    return wStr

  def preselection(self, dataMC , channel='all', zWindow = 'offZ'):
    return self.selection(dataMC, channel = channel, zWindow = zWindow, nBTags = (1,-1))

  def selection(self, dataMC, channel = 'all', zWindow = 'offZ', nBTags = (1,-1) ):
    '''Get preselection  cutstring.
Arguments: dataMC: 'Data' or 'MC'
sys: Systematic variation, default is None. '''

    triggerMuMu   = "HLT_mumuIso"
    triggerEleEle = "HLT_ee_DZ"
    triggerMuEle  = "HLT_mue"
    preselMuMu = "isMuMu==1&&nGoodMuons==2&&nGoodElectrons==0"
    preselEE   = "isEE==1&&nGoodMuons==0&&nGoodElectrons==2"
    preselEMu  = "isEMu==1&&nGoodMuons==1&&nGoodElectrons==1"
    filterCut = "(Flag_HBHENoiseFilter&&Flag_goodVertices&&Flag_CSCTightHaloFilter&&Flag_eeBadScFilter&&weight>0)"

    assert dataMC in ['Data','MC'], "dataMC = Data or MC, got %r."%dataMC
    assert channel in allChannels, "channel must be one of "+",".join(allChannels)+". Got %r."%channel
    assert zWindow in ['offZ', 'onZ', 'allZ'], "zWindow must be one of onZ, offZ, allZ. Got %r"%zWindow
    if self.sys['selectionModifier']: assert self.sys['selectionModifier'] in jmeVariations, "Don't know about systematic variation %r, take one of %s"%(self.sys['selectionModifier'], ",".join(jmeVariations))
    assert not (dataMC=='Data' and self.sys['selectionModifier']), "Why would you need data preselection with selectionModifier=%r? Should be None."%self.sys['selectionModifier']

  #basic cuts
    cuts = getCuts(self.sys['selectionModifier'], nBTags=nBTags)
    presel = "&&".join(c[1] for c in cuts)
  #Z window
    if zWindow in ['onZ', 'offZ']:
       presel+="&&"+getZCut(zWindow, self.zMassRange)
  #triggers
    if self.useTriggers:
      pMuMu = preselMuMu + "&&" + triggerMuMu
      pEE   = preselEE  + "&&" + triggerEleEle 
      pEMu  = preselEMu + "&&" + triggerMuEle
    else:
      pMuMu = preselMuMu 
      pEE   = preselEE  
      pEMu  = preselEMu 
  # dilepton channels    
    if channel=="MuMu":
      presel+="&&"+pMuMu
    if channel=="EE":
      presel+="&&"+pEE
    if channel=="EMu":
      presel+="&&"+pEMu
    if channel=="all":
      presel+="&&("+pMuMu+'||'+pEE+'||'+pEMu+')'

    if dataMC=='Data':
      presel+="&&"+filterCut
    return presel 

setup=_setup()

#define analysis regions
from regions import regions1D, regions3D
regions =  regions1D[:1]

from collections import OrderedDict
from MCBasedEstimate import MCBasedEstimate
from DataDrivenDYEstimate import DataDrivenDYEstimate
#from WardsGreatCode import DataDrivenDYEstimate, DataDrivenTTZEstimate
cacheDir = os.path.join(setup.analysisOutputDir, 'cacheFiles', setup.prefix)
estimates = [
   DataDrivenDYEstimate(name='DY-DD', cacheDir=None),
   MCBasedEstimate(name='TTJets',    sample=setup.sample['TTJets'], cacheDir=cacheDir),
   MCBasedEstimate(name='TTZ',       sample=setup.sample['TTZ'], cacheDir=cacheDir),
   MCBasedEstimate(name='TTXNoZ',    sample=setup.sample['TTXNoZ'], cacheDir=cacheDir),
   MCBasedEstimate(name='singleTop', sample=setup.sample['singleTop'], cacheDir=cacheDir),
   MCBasedEstimate(name='diBoson',   sample=setup.sample['diBoson'], cacheDir=cacheDir),
   MCBasedEstimate(name='triBoson',  sample=setup.sample['triBoson'], cacheDir=cacheDir),
   MCBasedEstimate(name='WJetsToLNu_HT', sample=setup.sample['WJetsToLNu_HT'], cacheDir=cacheDir),
   MCBasedEstimate(name='DY',        sample=setup.sample['DY'], cacheDir=cacheDir),
   MCBasedEstimate(name='QCD',      sample=setup.sample['QCD'], cacheDir=cacheDir),
]
nList = [e.name for e in estimates]
assert len(list(set(nList))) == len(nList), "Names of estimates are not unique: %s"%",".join(nList)