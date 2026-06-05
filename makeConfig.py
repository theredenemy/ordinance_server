
import configparser


def makeConfig():
   import configparser
   config_file = configparser.ConfigParser()


   config_file.add_section("ORDINANCE")


   config_file.set("ORDINANCE", "player", "SERVICE")
   config_file.set("ORDINANCE", "timestamp", "1230681600")
   config_file.set("ORDINANCE", "date", "DECEMBER 31TH 2008")
   config_file.set("ORDINANCE", "state", "alive")
   config_file.set("ORDINANCE", "trigger", "submit")
   config_file.set("ORDINANCE", "team", "UNKNOWN")
   config_file.set("ORDINANCE", "weapon", "UNKNOWN")
   config_file.set("ORDINANCE", "playerclass", "UNKNOWN")
   config_file.set("ORDINANCE", "mode", "game")
   config_file.set("ORDINANCE", "allow_mode_change", "True")
   config_file.set("ORDINANCE", "log_post_requests", "False")
   config_file.set("ORDINANCE", "log_chat", "False")
   config_file.set("ORDINANCE", "block_vpn", "False")


   with open(r"ORDINANCE.ini", 'w') as configfileObj:
      config_file.write(configfileObj)
      configfileObj.flush()
      configfileObj.close()

   print("Config file 'ORDINANCE.ini' created")

def makeClientConfig():
   import configparser
   config_file = configparser.ConfigParser()


   config_file.add_section("Client")


   config_file.set("Client", "ip", "127.0.0.1")
   config_file.set("Client", "port", "4456")


   with open(r"Client.ini", 'w') as configfileObj:
      config_file.write(configfileObj)
      configfileObj.flush()
      configfileObj.close()

   print("Config file 'Client.ini' created")

if __name__ == "__main__":
   makeConfig()