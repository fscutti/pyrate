import argparse
import yaml

from pyrate.core.Job import Job

parser = argparse.ArgumentParser(description="Command line options for pyrate")

# -------------------------------------------------------------------
# A single job is identified by just one job configuration file. 
# Several of these can be passed to this script using the -j flag.
# This means that the system will launch several jobs in sequence.
# One job corresponds locally to a single instance of a Run.
# -------------------------------------------------------------------
parser.add_argument(
    "--job_config", "-j", help="job configuration file/s", nargs="+", required=True
)
parser.add_argument(
    "--logging_level", "-l", help="logging level", required=False, default="CRITICAL"
)

args = parser.parse_args()

if __name__ == "__main__":
    for jc in args.job_config:

        stream = open(jc, "r")

        jconfig = yaml.full_load(stream)

        jname = jc.split(".")[0]

        log_level = args.logging_level

        job = Job(jname, jconfig, log_level)

        job.setup()
        job.launch()

# EOF

