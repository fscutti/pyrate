.. code:: robotframework

| *** Settings ***      |
| Documentation         |
| Library               | OperatingSystem |

# application will be the the main command we run in our integration tests
| *** Variables *** |
# this is how you translate from the environment. Note the '%'
| ${PYRATE_BASE_DIR}        | %{PYRATE}  
| ${APPLICATION}            | python3.8 ${PYRATE_BASE_DIR}/scripts/pyrate
| ${MUONJOBFILE}            | ${PYRATE_BASE_DIR}/scripts/job_MuonDetTest.yaml 

| *** Test Cases ***         |
| Test muon detector scripts | [Documentation]             | Test various detector scripts and ensure the scripts didn't crash\n'Run And Return Rc' is from OperatingSystem library 
|                            | Should Be True              | $PYRATE_BASE_DIR != ''
|                            | Should Exist                | ${MUONJOBFILE}           |
|                            | ${rc}                       | Run And Return Rc        | ${APPLICATION} -j ${MUONJOBFILE}
|                            | Should Be Equal As Integers | ${rc}                    | 0   

