import yaml

stream = open("data_preparation.yaml", "r")
#dictionary = yaml.load(stream, Loader=yaml.FullLoader)
dictionary = yaml.full_load(stream)
for key, value in dictionary.items():
    print(key + " : " + str(value))

