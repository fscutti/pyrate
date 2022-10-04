# dependencies
sudo yum -y update
sudo yum -y groupinstall "Development Tools"
sudo yum -y install openssl-devel bzip2-devel libffi-devel gcc

# download and unpack
wget https://www.python.org/ftp/python/3.8.3/Python-3.8.3.tgz
tar xvf Python-3.8.3.tgz
cd Python-3.8.3/

# install to /usr/local, 
# '--enable-shared'is important to build with ROOT so it can find the '.so's
./configure --enable-optimizations --enable-shared --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"
sudo make -j$(nproc) install

# test
python3.8 -c "print('Python3.8 properly installed')" && echo "Python3.8 at\n$(which python3.8)"

# clean up
cd ..
rm -rf Python-3.8.3.tgz*
rm -rf Python-3.8.3

