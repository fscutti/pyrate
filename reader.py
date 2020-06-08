# python 3.8.3 needed
import yaml

#stream = open("data_preparation.yaml", "r")
#stream = open("reconstruction.yaml", "r")
stream = open("analysis.yaml", "r")
dictionary = yaml.full_load(stream)
for key, value in dictionary.items():
    print(key + " : " + str(value))

