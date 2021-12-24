import configparser

config = configparser.ConfigParser()
config.read('lens_file.ini')

for item in config['fields']:
  pass #print(item.get())
