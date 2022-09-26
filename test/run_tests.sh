#!/usr/env bash

TESTDIR=$PYRATE/test/
LOGDIR=$TESTDIR/logs/

# run all robot tests in $TESTDIR
# this also hooks the memory profiler in between the tests
robot --listener $TESTDIR/RoughMemoryProfile.py:$LOGDIR --outputdir $LOGDIR  $TESTDIR

echo "You can checkout the resutsl with your browser..."
echo "firefox ${LOGDIR}/report.html"


