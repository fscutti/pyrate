FROM cern/cc7-base

# dependencies
# python3.8:
# openssl-devel bzip2-devel libffi-devel gcc wget which cmake3 
# ROOT:
# git cmake3 gcc-c++ gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel openssl-devel
# the group 'Development Tools' contains 'make' and its stuff
RUN yum -y update && \
    yum -y groupinstall "Development Tools" && \
    yum -y install openssl-devel bzip2-devel libffi-devel gcc wget which git cmake3 gcc-c++ gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel
 
# download and unpack
RUN wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz && tar xvf Python-3.8.3.tgz
# install to /usr/local, 
# '--enable-shared'is important to build with ROOT so it can find the '.so's
RUN cd Python-3.8.3/ && \
    ./configure --enable-optimizations --enable-shared --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib" &&\
    make -j$(nproc) install

# clean up
RUN rm -rf /Python-3.8.3.tgz* && rm -rf /Python-3.8.3

##########################################################################################
# ROOT 
##########################################################################################

# linux has a dir named 'root' ...
ARG ROOT_DIR=/cern_root/
ARG INSTALL_DIR=$ROOT_DIR/rootv6.22py3.8/

# branches of https://github.com/root-project/root
ARG ROOT_VERSION=v6-22-00-patches
ARG BUILD_DIR=$ROOT_DIR/root_build/
ARG SRC_DIR=$ROOT_DIR/root_src/

RUN mkdir -p $ROOT_DIR && mkdir -p $BUILD_DIR && mkdir -p $INSTALL_DIR && mkdir -p $SRC_DIR

# get source files
RUN git clone --branch $ROOT_VERSION https://github.com/root-project/root.git $SRC_DIR

# check if we have python3.8
RUN python3.8 -c "print('Found python3.8 - all good so far...')" || echo "Did not find python3.8 did you install it?"

# configure needs cmake>3.14 on centos7 his is diffrencent from 'cmake'
# note: 
#   - x11 deactivated
#   - -Dclad=OFF (auto differentiation) doesnt pull the git repo for whatever reason
RUN cd $BUILD_DIR &&\ 
    cmake3 -j$(nproc) -DCMAKE_INSTALL_PREFIX=$INSTALL_DIR -Dcxx11=ON -DPYTHON_EXECUTABLE=$(which python3.8) -Droofit=ON -Dx11=OFF -Dclad=OFF $SRC_DIR &&\  
    make -j$(nproc) &&\ 
    make install

# clean
RUN rm -rf $BUILD_DIR && rm -rf $SRC_DIR && echo "Done"

###########################################################################################

# for some reason the docker bash ignores all rc, /etc/profile and /etc/profile.d files 
# so we have to manually source root before starting our shell
RUN echo "source ${INSTALL_DIR}/bin/thisroot.sh && /bin/bash" >> /entrypoint.sh && chmod +x /entrypoint.sh 

# setup root and do quick test
RUN ["/bin/bash", "-c", "source ${INSTALL_DIR}/bin/thisroot.sh && python3.8 -c \"import ROOT\""]

###########################################################################################


# if you run the container with 'docker run' this will be called and python will know about ROOT
ENTRYPOINT ["bin/bash", "-c", "/entrypoint.sh"]


