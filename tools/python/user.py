import os

runOnGentT2 = True

if os.environ['USER'] in ['schoef', 'rschoefbeck', 'schoefbeck']:
    # Where you store cmg output
    cmg_directory      = "/scratch/rschoefbeck/cmgTuples/80X_1l_9"
    # Where postprocessed data goes 
    data_output_directory      = "/afs/hephy.at/data/rschoefbeck02/cmgTuples/"
    #data_output_directory      = "/afs/hephy.at/data/rschoefbeck02/cmgTuples/"
    # Where you store the data
    data_directory      = "/afs/hephy.at/data/dspitzbart02/cmgTuples/"
    # Where the plots go
    plot_directory      = "/afs/hephy.at/user/r/rschoefbeck/www/"
    #plot_directory      = "/afs/cern.ch/work/s/schoef/www/"
    # Analysis result files
    analysis_results        =  '/afs/hephy.at/data/rschoefbeck01/StopsDilepton/results/80X_v12' #Path to analysis results
    dpm_directory           = '/dpm/oeaw.ac.at/home/cms/store/user/schoef/'
    cern_proxy_certificate  = '/afs/cern.ch/user/s/schoef/private/.proxy'
    # directory with veto lists
    veto_lists = "/afs/hephy.at/data/rschoefbeck01/StopsDilepton/vetoLists/"
    # 715 release for limit calculation 
    combineReleaseLocation = '/afs/hephy.at/work/r/rschoefbeck/CMS/tmp/CMSSW_7_1_5/src'
    runOnGentT2 = False

if os.environ['USER'] in ['dspitzbart', 'dspitzba']:
    # Where you store cmg output
    cmg_directory      = "/scratch/rschoefbeck/cmgTuples/80X_1l_9"
    # Where postprocessed data goes 
    data_output_directory      = "/afs/hephy.at/data/dspitzbart02/cmgTuples/"
    #data_output_directory      = "/afs/hephy.at/data/rschoefbeck02/cmgTuples/"
    # Where you store the data
    data_directory      = "/afs/hephy.at/data/dspitzbart02/cmgTuples/"
    # Where the plots go
    plot_directory      = "/afs/hephy.at/user/d/dspitzbart/www/stopsDilepton/"
    #plot_directory      = "/afs/cern.ch/work/d/dspitzba/www/stopsDilepton/"
    # Analysis result files
    analysis_results        = '/afs/hephy.at/data/dspitzbart02/StopsDilepton/results/80X_v35' #Path to analysis results
    dpm_directory           = '/dpm/oeaw.ac.at/home/cms/store/user/dspitzba/'
    cern_proxy_certificate  = '/afs/cern.ch/user/d/dspitzba/private/.proxy'
    # directory with veto lists
    veto_lists = "/afs/hephy.at/data/rschoefbeck01/StopsDilepton/vetoLists/"
    # 715 release for limit calculation 
    combineReleaseLocation = '/afs/hephy.at/work/d/dspitzbart/stops/CMSSW_7_4_7/src'
    if 'cern' in os.getenv("HOSTNAME"):
      analysis_results        = '/afs/cern.ch/work/d/dspitzba/StopsDilepton/results/80X_v30'
      combineReleaseLocation = '/afs/cern.ch/work/d/dspitzba/CMS/stop/CMSSW_7_4_7/src'
    runOnGentT2 = False

if os.environ['USER'] in ['tomc']:
    # Where you store cmg output
    cmg_directory              = "/pnfs/iihe/cms/store/user/tomc/cmgTuples/80X_1l_24"
    # Where postprocessed data goes 
    data_output_directory      = "/user/tomc/StopsDilepton/data"
    # Where you store the data for plotting, analysis etc.
    data_directory             = "/user/tomc/StopsDilepton/data"
    # Where the plots go
    plot_directory             = "/user/tomc/StopsDilepton/plots_80X_v35"
    # Analysis result files
    analysis_results           = "/user/tomc/StopsDilepton/results_80X_v35"
    # Release for limit calculation (seems the 74X release is now also recommended for users)
    combineReleaseLocation     = '/user/tomc/StopsDilepton/CMSSW_7_4_7/src/'

# change the paths accordingly
if os.environ['USER'] in ['newUser']:
    # Where you store cmg output, basically obsolete now (no need to change)
    cmg_directory      = "/scratch/rschoefbeck/cmgTuples/80X_1l_9"
    # Where postprocessed data goes. Either add your own path, or use the ones produced by Daniel
    data_output_directory      = "/afs/hephy.at/data/dspitzbart02/cmgTuples/"
    # Where you store the data. Either add your own path, or use the ones produced by Daniel
    data_directory      = "/afs/hephy.at/data/dspitzbart02/cmgTuples/"
    # Where the plots go
    plot_directory      = "/afs/hephy.at/user/d/dspitzbart/www/stopsDilepton/"
    # Analysis result files
    analysis_results        = '/afs/hephy.at/data/dspitzbart02/StopsDilepton/results/80X_v35' #Path to analysis results
    dpm_directory           = '/dpm/oeaw.ac.at/home/cms/store/user/dspitzba/'
    cern_proxy_certificate  = '/afs/cern.ch/user/d/dspitzba/private/.proxy'
    # 715 release for limit calculation 
    combineReleaseLocation = '/afs/hephy.at/work/d/dspitzbart/stops/CMSSW_7_4_7/src'
    runOnGentT2 = False


