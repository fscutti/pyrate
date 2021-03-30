# This is the new version of the pyrate offline software
Generally what you need beforehand is python3.8 and ROOT build with it.

## Setting up pyrate
### Dependencies
There are scripts in `./scripts/install_scripts/` that will install python3.8 and ROOT for you, assuming you are running a centos7 machine. If you are running Ubuntu you have to replace the `yum` stuff with `apt` but probably all the dependencies are already there. Note that ROOT has to be build with cmake>3.14.

On **SPARTAN** you will not need these scripts you can load an environment module that contains all you need.

    module load root/6.22.02-python-3.8.2	
    module avail # see whats available 

### Setup pyrate itself
We use python virtual environments to isntall our python packages to not pollute your system python. You can get your system python stuff back with `deactivate`. And restart pyrates python with 
    
    source ./pyrate_venv/bin/activate && export PYRATE=<path to where you have your pyrate repo>

But before that you need to install pyrate at least once with:

    source setup.sh

Alternatively you can run above also everytime you want to use pyrate (just might take a couple of seconds longer). It sets the $PYRATE variable which is important for pyrate to know is root directory (`source` makes sure this variable persists after running the script, so just doing `./setup.sh` will result in crashes).

## Testing
We use robot-framework for testing. All tests go to `./test` and end with `.robot`. See the example.	
Run all tests:

    robot ./test # runs all tests in the directory ending with `.robot`

Please implement a test for every new feature you implement.

## Some git basics
When you create new branches please use the prefixes `feature` and `bugfix`. The keyword `release` will later be used for relases.

Make a new branch

    git checkout -b feature/my-feature-name

Add some files you changed

    git add <file name>

Commit the files (this is still happening locally)

    git commit -m "Some meaningful message about what you did"

Now push to a new remote branch in te remote repository

    git push --set-upstream origin feature/my-feature-name

It is important here that `feature/my-feature-name` is the same name as you created locally earlier. You could also do

    git push --set-upstream origin feature/my-feature-name:origin/feature/different-name

if you want a deffenrent name on the remote repo. (Maybe you have a typo earlier but you can also rename locally with `git banch -m new-name`).
Then make a pull request. Go to "branches" and klick on "open pull request", select "master" as destination (should be default) you need to include at least Federico.

