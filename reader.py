# python 3.8.3 needed
import yaml

# This is only a test script. It will be deleted.

#stream = open("data_preparation.yaml", "r")
#stream = open("reconstruction.yaml", "r")
stream = open("/Users/fscutti/pyrate/config/algorithms.yaml", "r")
dictionary = yaml.full_load(stream)
for key, value in dictionary.items():
    print(key + " : " + str(value))

