import paramiko
import os
import fileinuse_functions
def upload_dir(dir, remotepath, host, port, user, ssh_keyfile):
    print(f"Uploading {dir}")
    ssh_client = paramiko.SSHClient()

    ssh_client.load_system_host_keys()

    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting")
    ssh_client.connect(hostname=host, port=port, username=user, allow_agent=True, key_filename=ssh_keyfile, disabled_algorithms={'pubkeys': ['ssh-rsa']})
    print("Connected")
    sftp = ssh_client.open_sftp()
    print("Uploading Files")
    for file in os.listdir(dir):
        filepath = os.path.join(dir, file)
        basefile = os.path.basename(filepath)
        if os.path.isfile(filepath):
            while fileinuse_functions.is_file_in_use(filepath):
                pass
            print(filepath)
            sftp.put(localpath=filepath, remotepath=f"/{remotepath}/{basefile}")
        else:
            print(f"File Does Not Exist : {filepath}")
        
    sftp.close()
    ssh_client.close()
    print(f"Done Uploading {dir}")

def upload_file(filepath, remotepath, host, port, user, ssh_keyfile):
    print(f"Uploading {filepath}")
    ssh_client = paramiko.SSHClient()

    ssh_client.load_system_host_keys()

    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting")
    ssh_client.connect(hostname=host, port=port, username=user, allow_agent=True, key_filename=ssh_keyfile, disabled_algorithms={'pubkeys': ['ssh-rsa']})
    print("Connected")
    sftp = ssh_client.open_sftp()
    print("Uploading File")
    basefile = os.path.basename(filepath)
    if os.path.isfile(filepath):
        print(filepath)
        while fileinuse_functions.is_file_in_use(filepath):
            pass
        sftp.put(localpath=filepath, remotepath=f"/{remotepath}/{basefile}")
        print(f"Done Uploading {filepath}")
        return True
    else:
        print(f"File Does Not Exist : {filepath}")
        return False