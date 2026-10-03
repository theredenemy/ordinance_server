import configparser
import os

def write_config(configfile, config, comment=None):
    with open(configfile, 'w', encoding='utf-8', errors='ignore') as f:
        if comment:
            f.write(comment)
        config.write(f)
    
def read_config(configfile, section, option, default_value=0, comment=None, is_int=False, is_bool=False):
    config = configparser.ConfigParser(allow_no_value=True)
    if os.path.isfile(configfile) == False:
        config.add_section(section)
        config.set(section, option, str(default_value))
        write_config(configfile, config)
    config.read(configfile)
    
    if not config.has_section(section):
        config.add_section(section)
        write_config(configfile, config, comment=comment)
    if not config.has_option(section, option):
        config.set(section, option, str(default_value))
        write_config(configfile, config, comment=comment)
    write_config(configfile, config, comment=comment)
    # get value
    if is_int == True:
        value = config.getint(section, option)
    elif is_bool == True:
        value = config.getboolean(section, option)
    else:
        value = config[section][option]
    
    return value


def set_config(configfile, section, option, value=0, comment=None):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(configfile)
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, option, str(value))
    write_config(configfile, config, comment=comment)
    return True
