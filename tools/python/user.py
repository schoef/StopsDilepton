import os

runOnGentT2 = True

if os.environ['USER'] in ['schoef', 'rschoefbeck', 'schoefbeck']:
    # Where you store the data
#    data_directory      = "/scratch/rschoefbeck/cmgTuples/postProcessed_Fall15_mAODv2/dilepTiny"
    data_directory      = "/scratch/rschoefbeck/cmgTuples/fromTom"
    # Where postprocessed data goes 
    data_output_directory      = "/scratch/rschoefbeck/cmgTuples/"
    # Where you store cmg output
    cmg_directory      = "/scratch/rschoefbeck/cmgTuples/763_1l"
    # Where the plots go
    plot_directory      = "/afs/hephy.at/user/r/rschoefbeck/www/"
    # Analysis result files
    analysis_results    = '/afs/hephy.at/data/rschoefbeck01/StopsDilepton/results/test' #Path to analysis results
    # directory with veto lists
    veto_lists = "/afs/hephy.at/data/rschoefbeck01/StopsDilepton/vetoLists/"
    # 715 release for limit calculation 
    releaseLocation71XC = '/afs/hephy.at/work/r/rschoefbeck/CMS/tmp/CMSSW_7_1_5/src'
    runOnGentT2 = False


if os.environ['USER'] in ['tomc']:
    # Where you store cmg output
    cmg_directory              = "/pnfs/iihe/cms/store/user/tomc/cmgTuples/763_4"
    # Where postprocessed data goes 
    data_output_directory      = "/user/tomc/StopsDilepton/data"
    # Where the plots go
    plot_directory             = "/user/tomc/StopsDilepton/plots"
    # Analysis result files
    analysis_results           = "/user/tomc/StopsDilepton/results"
    # directory with veto lists
    veto_lists                 = "/user/tomc/StopsDilepton/vetoLists"
