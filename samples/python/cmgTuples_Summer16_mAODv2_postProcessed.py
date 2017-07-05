import copy, os, sys
from RootTools.core.Sample import Sample
import ROOT

# Logging
import logging
logger = logging.getLogger(__name__)

from StopsDilepton.samples.color import color

# Data directory
try:
    data_directory = sys.modules['__main__'].data_directory
except:
    from StopsDilepton.tools.user import data_directory as user_data_directory
    data_directory = user_data_directory 

# Take post processing directory if defined in main module
try:
  import sys
  postProcessing_directory = sys.modules['__main__'].postProcessing_directory
except:
  postProcessing_directory = "postProcessed_80X_SD/dilepTiny/"

logger.info("Loading MC samples from directory %s", os.path.join(data_directory, postProcessing_directory))



dirs = {}
dirs['DY_LO']            = ["DYJetsToLL_M10to50_LO", "DYJetsToLL_M50_LO_ext"]
dirs['TTJets_LO']        = ["TTJets_LO"] 
dirs['diBosonInclusive'] = ["WW", "WZ", "ZZ"]

directories = { key : [ os.path.join( data_directory, postProcessing_directory, dir) for dir in dirs[key]] for key in dirs.keys()}

DY_LO            = Sample.fromDirectory(name="DY_LO",            treeName="Events", isData=False, color=color.DY,              texName="DY (LO)",                           directory=directories['DY_LO'])
TTJets_LO        = Sample.fromDirectory(name="TTJets_LO",        treeName="Events", isData=False, color=color.TTJets,          texName="t#bar{t} + Jets (LO)",              directory=directories['TTJets_LO'])
diBosonInclusive = Sample.fromDirectory(name="diBosonInclusive", treeName="Events", isData=False, color=color.diBoson,         texName="VV (incl.)",                        directory=directories['diBosonInclusive'])
