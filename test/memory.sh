
# --------------------------------------------------
# memory consumption monitored using memory_profiler
# https://github.com/pythonprofilers/memory_profiler
# --------------------------------------------------

#mprof run mpyrate.py -j ../job_Example.yaml 

mprof run mpyrate.py -j ../job_ROOT.yaml 
#mprof run mpyrate.py -j ../job_WC.yaml 
#mprof run mpyrate.py -j ../job_WD.yaml 


# this is to print line-by-line memory usage
#python3 -m memory_profiler mpyrate.py -j ../job_WD.yaml
