# Standard imports 
import os
import ROOT

# RootTools
from RootTools.core.standard import *

# Logging
import logging
logger = logging.getLogger(__name__)

def singleton(class_):
  instances = {}
  def getinstance(*args, **kwargs):
    if class_ not in instances:
        instances[class_] = class_(*args, **kwargs)
    return instances[class_]
  return getinstance


def getSubDir(dataset, path):
    import re
    m=re.match("\/(.*)\/(.*)\/(.*)",dataset)
    if not m :
        print "NO GOOD DATASET"
        return
    if os.environ['USER'] in ['tomc']: 
      d=re.match("(.*)/cmgTuples/(.*)",path)
      return m.group(1)+"/"+m.group(2)+'_'+d.group(2)
    else :                             
      return m.group(1)+"_"+m.group(2)

def fromHeppySample(sample, data_path, module = None, maxN = None):
    ''' Load CMG tuple from local directory
    '''

    import importlib
    if module is not None:
        module_ = module
    elif "Run2016" in sample:
        module_ = 'CMGTools.RootTools.samples.samples_13TeV_DATA2016'
        #module_ = 'CMGTools.StopsDilepton.samples_13TeV_Moriond2017'
    elif ("T2tt" in sample) or ("T2bt" in sample) or ("T2bW" in sample):
        module_ = 'CMGTools.RootTools.samples.samples_13TeV_signals'
    elif "T8bbllnunu" in sample:
        module_ = 'CMGTools.RootTools.samples.samples_13TeV_signals'
    elif "TTbarDM" in sample:
        module_ = 'CMGTools.StopsDilepton.TTbarDMJets_signals_RunIISummer16MiniAODv2'
    else: 
        module_ = 'CMGTools.RootTools.samples.samples_13TeV_RunIISummer16MiniAODv2'

    try:
        heppy_sample = getattr(importlib.import_module( module_ ), sample)
    except:
        raise ValueError( "Could not load sample '%s' from %s "%( sample, module_ ) )

    subDir = getSubDir(heppy_sample.dataset, data_path)
    if not subDir:
        raise ValueError( "Not a good dataset name: '%s'"%heppy_sample.dataset )

    path = os.path.join( data_path, subDir )
    from StopsDilepton.tools.user import runOnGentT2
    if runOnGentT2: 
        sample = Sample.fromCMGCrabDirectory(
            heppy_sample.name, 
            path, 
            treeFilename = 'tree.root', 
            treeName = 'tree', isData = heppy_sample.isData, maxN = maxN)
    else:  # Vienna -> Load from DPM 
        if True: #'/dpm' in data_path:

            from RootTools.core.helpers import renew_proxy
            user = os.environ['USER']
            # Make proxy in afs to allow batch jobs to run
            proxy_path = os.path.expandvars('$HOME/private/.proxy')
            proxy = renew_proxy( proxy_path )
            logger.info( "Using proxy %s"%proxy )

            if module is not None:
                module_ = module
            if "Run2016" in sample:
                from StopsDilepton.samples.heppy_dpm_samples import data_heppy_mapper as data_heppy_mapper
                return data_heppy_mapper.from_heppy_samplename(heppy_sample.name, maxN = maxN)
            elif ("T2tt" in sample) or ("T8bb" in sample) or ("T2b" in sample):
                from StopsDilepton.samples.heppy_dpm_samples import SUSY_heppy_mapper
                return SUSY_heppy_mapper.from_heppy_samplename(heppy_sample.name, maxN = maxN)
            elif "TTbarDM" in sample:
                from StopsDilepton.samples.heppy_dpm_samples import ttbarDM_heppy_mapper
                return ttbarDM_heppy_mapper.from_heppy_samplename(heppy_sample.name, maxN = maxN)
            else: 
                from StopsDilepton.samples.heppy_dpm_samples import mc_heppy_mapper
                return mc_heppy_mapper.from_heppy_samplename(heppy_sample.name, maxN = maxN)
            raise ValueError
        else:                           
            sample = Sample.fromCMGOutput(
                heppy_sample.name, 
                path, 
                treeFilename = 'tree.root', 
                treeName = 'tree', isData = heppy_sample.isData, maxN = maxN)

    sample.heppy = heppy_sample
    return sample

def getT2ttSignalWeight(sample, lumi):
    '''Get a dictionary for T2tt signal weights
    '''
    from StopsDilepton.tools.xSecSusy import xSecSusy
    xSecSusy_ = xSecSusy()
    channel='stop13TeV'
    signalWeight={}
    mMax = 1550
    bStr = str(mMax)+','+str(mMax)
    #sample.chain.Draw("GenSusyMNeutralino:GenSusyMStop>>hNEvents("+','.join([bStr, bStr])+")", "","goff")
    sample.chain.Draw("Max$(genPartAll_mass*(abs(genPartAll_pdgId)==1000022)):Max$(genPartAll_mass*(abs(genPartAll_pdgId)==1000006))>>hNEvents("+','.join([bStr, bStr])+")", "","goff")
    hNEvents = ROOT.gDirectory.Get("hNEvents")
    for i in range (mMax):
        for j in range (mMax):
            n = hNEvents.GetBinContent(hNEvents.FindBin(i,j))
            if n>0:
                signalWeight[(i,j)] = {'weight':lumi*xSecSusy_.getXSec(channel=channel,mass=i,sigma=0)/n, 'xSecFacUp':xSecSusy_.getXSec(channel=channel,mass=i,sigma=1)/xSecSusy_.getXSec(channel=channel,mass=i,sigma=0), 'xSecFacDown':xSecSusy_.getXSec(channel=channel,mass=i,sigma=-1)/xSecSusy_.getXSec(channel=channel,mass=i,sigma=0)}
    #            logger.info( "Found mStop %5i mNeu %5i Number of events: %6i, xSec: %10.6f, weight: %6.6f (+1 sigma rel: %6.6f, -1 sigma rel: %6.6f)", i,j,n, xSecSusy_.getXSec(channel=channel,mass=i,sigma=0),  signalWeight[(i,j)]['weight'], signalWeight[(i,j)]['xSecFacUp'], signalWeight[(i,j)]['xSecFacDown'] )
    del hNEvents
    return signalWeight
