# This is the new version of the pyrate offline software
  Generally what you need beforehand is python3.8 and ROOT build with it.

## How to set it up
  There are scripts in ./scripts/install_scripts/ that will python3.8 and ROOT for you, assuming you are running a centos7 machine. If you are running Ubuntu you have to replace the 'yum' stuff with 'apt' but probably all the dependencies are already there. Note that ROOT has to be build with cmake>3.14.
  On **SPARTAN** you will not need these scripts you can load an environment module that contains all you need.
    module load root/6.22.02-python-3.8.2	
    module avail # see whats available 

## Testing
  We use robot-framework for testing. All tests go to `./test` and end with `.robot`. See the example.	
  Run all tests:
    robot ./test # runs all tests in the directory ending with `.robot`




