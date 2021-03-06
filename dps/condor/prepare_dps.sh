#!/bin/bash
# remove Analysis.tar in case it exists. We want to ship the latest code!
# also useful for syncing between machines!
echo "Preparing DailyPythonScripts for condor submission"
if [ -f "dps.tar" ]; then
	echo "... deleting old dps.tar"
	rm -f dps.tar
fi
echo "... creating tar file (dps.tar)"
mkdir -p jobs
tar -zcf dps.tar dps bin config data/toy_mc jobs \
--exclude="*.pyc" --exclude="jobs/*/logs" \
--exclude="*.tar" --exclude="config/unfolding" \
--exclude="dps/legacy/*"

# hadoop fs -mkdir -p $1
# hadoop fs -copyFromLocal dps.tar $1
