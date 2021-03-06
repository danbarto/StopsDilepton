#PBS -l nodes=1:ppn=1
#!/bin/zsh
echo "cmgPostProcessing of sample ${sample} in $cmssw" >&2
echo "Id: $PBS_JOBID" >&2

source $VO_CMS_SW_DIR/cmsset_default.sh
cd "/user/$USER/cmgPostProcessing/$skim/${sample// /}/$cmssw/src/StopsDilepton/cmgPostProcessing/"
eval `scram runtime -sh`
python cmgPostProcessing.py --dataDir=/pnfs/iihe/cms/store/user/tomc/cmgTuples/80X_v6 --sample ${sample} --log=TRACE --skim=$skim --overwrite --processingEra=postProcessed_80X_tom --targetDir=/user/tomc/StopsDilepton/data
cd /user/$USER
rm -rf "/user/$USER/cmgPostProcessing/$skim/${sample// /}"
