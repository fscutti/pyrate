## ========================
## Setup script for running 
## on the muondaq machine.
## ========================

## ----------------------
## pre-setup, don't touch
## ----------------------

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

path_of_this_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYRATE=${path_of_this_dir}

add_to_python_path()
{
    export PYTHONPATH=$1:$PYTHONPATH
    echo "  Added $1 to your PYTHONPATH."
}

add_to_path()
{
    export PATH=$1:$PATH
    echo "  Added $1 to your PATH."
}

## ----------------
## ROOT setup
## ----------------

#eval "setupROOT6.14.04"
## ----------------
## setup PYTHONPATH
## ----------------

# echo "  Setting up your PYTHONPATH."
# add_to_python_path ${PYRATE}
# add_to_python_path ${PYRATE}/pyrate
# echo "  done."

## ---------------------------------------------
## Add pyrate/scripts directory to PATH
## ---------------------------------------------
#echo "  Add scripts to PATH."
#add_to_path ${PYRATE}/scripts
#echo "  done."

export DAQ_SCRIPTS=$(pwd)/scripts
if [ -n "${PATH}" ]; then
    export PATH=${DAQ_SCRIPTS}:${PATH}
else
    export PATH=${DAQ_SCRIPTS}
fi


# virtual environmens are very helpful for development
# and cause 0 overhead; essentially just add another location
# for python packages
VENV_NAME=pyrate_venv
if [ -z "$VIRTUAL_ENV" ]; then
	echo -e "${RED}No virtual environment found. Ill set one up at 'pyrate_venv'."
	echo -e "To get your old python environment back simply run 'deactivate'.${NC}"

	# get this module as a global user module
	python3.8 -m pip install --user virtualenv
	python3.8 -m venv $VENV_NAME
	source $VENV_NAME/bin/activate
else
	echo -e "${GREEN}Virtual environment found at:\n${NC}${CYAN}${VIRTUAL_ENV}${NC}\n${GREEN}Using it to install our dependencies.${NC}"
fi


# install all specified packages in that file
#QUIET="-q" # unset his if you ned to debug the setup

pip3.8 $QUIET install pip --upgrade
pip3.8 $QUIET install -r requirements.txt
#  install pyrate
# the -e option is impotant so that pyrate is globall recognised
# so you can run it independent of were $(pwd) is. 
pip3.8 $QUIET install -e .

bash ./test/check_for_root_test.sh
if [ $? -ne 0 ]; then # last exitcode
	echo -e "${RED}Could not find ${NC}${CYAN}ROOT$NC${RED}! Did you set it up? ${NC}"
else
	echo -e "${GREEN}Succesfully found ${NC}${CYAN}ROOT${NC}"
fi

# short test
bash ./test/install_test.sh
if [ $? -ne 0 ]; then # last exitcode
	echo -e "${RED}SOMETHING WENT WRONG.${NC}"
else
	echo -e "${GREEN}Succesfully setup ${NC}${CYAN}pyrate.${NC}"
	echo -e "${GREEN}You may need to start the virtual environment with:\n${NC}${CYAN}source ${VIRTUAL_ENV}/bin/activate${NC}"
fi

#EOF


