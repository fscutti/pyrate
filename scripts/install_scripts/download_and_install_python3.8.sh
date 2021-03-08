

# dependencies
sudo yum -y update
sudo yum -y groupinstall "Development Tools"
sudo yum -y install openssl-devel bzip2-devel libffi-devel gcc

# download and unpack
wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz
tar xvf Python-3.8.3.tgz
cd Python-3.8.3/

# install to /usr/local, 
# enable shared important to build with ROOT
# add correct search path for .so 
./configure --enable-optimizations --enable-shared --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
sudo make -j$(nproc) install

# test
python3.8 -c "print('Python3.8 properly installed')" && echo "Python3.8 at\n$(which python3.8)"

rm -rf Python-3.8.3.tgz*

