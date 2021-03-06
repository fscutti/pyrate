
#########################################################################
# these you have to setup
WORK_DIR=/home/$USER/ROOTv6.22/

OS=`uname -a | head -n1 | awk '{print $1;}'`
echo -e "Operating system \"$OS\" found..."
if [ $OS == "Darwin" ]; then
  echo -e "OSX prerequisites are XCODE: "
  echo -e "install via \"xcode-select --install\""
  # on mac "home" is a mountpoint,
  # so we need to go elesewhere to make our dirs
  WORK_DIR=/Users/$USER/ROOTv6.22/
fi

# pick whatever you want
# /usr/... migh be a good idea if you want that
INSTALL_DIR=$WORK_DIR/rootv6.22py3.8/

# branches of https://github.com/root-project/root
ROOT_VERSION=v6-22-00-patches

#########################################################################
# this is temporary stuff
BUILD_DIR=$WORK_DIR/root_build/
SRC_DIR=$WORK_DIR/root_src/

mkdir -p $WORK_DIR 
mkdir -p $BUILD_DIR
mkdir -p $INSTALL_DIR
mkdir -p $SRC_DIR

# get source files
git clone --branch $ROOT_VERSION https://github.com/root-project/root.git $SRC_DIR

cd $BUILD_DIR

# check if we have python3.8
python3.8 -c "print('Found python3.8 - all good so far...')" || echo "Did not find python3.8 did you install it?"

# configure needs cmake>3.14 on centos7 this is diffrencent from 'cmake'
if [ $OS == "Darwin" ]; then
  cmake -j$(nproc) -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR -Dcxx11=ON -DPYTHON_EXECUTABLE=$(which python3.8) -Droofit=ON -Dx11=ON $SRC_DIR
else
  cmake3 -j$(nproc) -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR -Dcxx11=ON -DPYTHON_EXECUTABLE=$(which python3.8) -Droofit=ON -Dx11=ON $SRC_DIR
fi
# install
make -j$(nproc)
make install

# setup root and do quick test
source $INSTALL_DIR/bin/thisroot.sh
python3.8 -c "import ROOT" && echo "Looks like everything worked." || echo "Something went wrong!"

# clean
rm -rf $BUILD_DIR
rm -rf $SRC_DIR
echo "Done"

