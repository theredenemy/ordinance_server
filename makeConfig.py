
import configparser


def makeConfig():
  import configparser
  config_file = configparser.ConfigParser()


  config_file.add_section("ORDINANCE")

  config_file.set("ORDINANCE", "player", "SERVICE")
  config_file.set("ORDINANCE", "timestamp", "4102387200")
  config_file.set("ORDINANCE", "state", "alive")

  with open(r"ORDINANCE.ini", 'w') as configfileObj:
     config_file.write(configfileObj)
     configfileObj.flush()
     configfileObj.close()

  print("Config file 'ORDINANCE.ini' created")

if __name__ == "__main__":
   makeConfig()