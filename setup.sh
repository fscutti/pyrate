## ========================
## Setup script for running 
## on the muondaq machine.
## ========================

## ----------------------
## pre-setup, don't touch
## ----------------------

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
## python utilities
## ----------------

#pip install --user file_read_backwards
#pip install --user tqdm
#pip install --user colorama
#pip install --user scipy
#pip install --user matplotlib
#pip install --user pandas

## ----------------
## setup PYTHONPATH
## ----------------

echo "  Setting up your PYTHONPATH."
add_to_python_path ${PYRATE}
add_to_python_path ${PYRATE}/pyrate
echo "  done."

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

#EOF


pip3 install --user tqdm
#pip3 install --user file_read_backwards
pip3 install --user colorama
#pip3 install --user scipy
#pip3 install --user matplotlib
#pip3 install --user pandas
pip3 install --user pyaml
#pip3 install --user strictyaml
pip3 install --user psycopg2-binary

pip3 install --user black
#pip3 install --user memory_profiler


