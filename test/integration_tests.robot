.. code:: robotframework

| *** Settings ***      |
| Documentation         |
| Library               | OperatingSystem |

# application will be the the main command we run in our integration tests
| *** Variables *** |
# this is how you translate from the environment. Note the '%'
| ${PYRATE_BASE_DIR}        | %{PYRATE}  
| ${APPLICATION}            | python3 ${PYRATE_BASE_DIR}/pyrate.py
| ${MUONJOBFILE}            | ${PYRATE_BASE_DIR}/test/job_MuonDetTest.yaml
| ${WAVEFORMALGFILE}        | ${PYRATE_BASE_DIR}/test/job_WaveformAlgorithmsTest.yaml

| *** Test Cases ***         |
| Test algorithm scripts     | [Documentation]             | Test various detector scripts and ensure the scripts didn't crash\n'Run And Return Rc' is from OperatingSystem library 
|                            | Should Be True              | $PYRATE_BASE_DIR != ''
|                            | Should Exist                | ${MUONJOBFILE}           |
|                            | ${rc}                       | Run And Return Rc        | ${APPLICATION} -j ${MUONJOBFILE}
|                            | Should Be Equal As Integers | ${rc}                    | 0
|                            | Should Exist                | ${WAVEFORMALGFILE}       |
|                            | ${rc}                       | Run And Return Rc        | ${APPLICATION} -j ${WAVEFORMALGFILE}
|                            | Should Be Equal As Integers | ${rc}                    | 0   

