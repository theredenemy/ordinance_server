import os
import configHelper
import configparser
import hashlib
import shutil
config = configparser.ConfigParser()
venvdir = "venv"
configfile = "checksums.ini"
requirements_md5 = configHelper.read_config(configfile, "venv", "requirements_md5", "hi")
getmd5 = hashlib.md5(open('requirements.txt', 'rb').read()).hexdigest()
if not requirements_md5 == getmd5:
    if os.path.isdir(venvdir) == True:
        shutil.rmtree(venvdir)
    config.read(configfile)
    config.set("venv", "requirements_md5", str(getmd5))
    with open(configfile, 'w') as f:
        config.write(f)

if os.path.isdir(venvdir) == False:
    
    f = open("make_venv.bat", "w")
    makevenvbat = f'''python -m venv {venvdir}
    call {venvdir}/Scripts/activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt'''
    f.write(makevenvbat)
    f.close()
    os.system("make_venv.bat")

f = open("load_venv.bat", "w" )
loadvenvbat = f'''call {venvdir}/Scripts/activate.bat
python app.py'''
f.write(loadvenvbat)
f.close()
os.system("load_venv.bat")
    