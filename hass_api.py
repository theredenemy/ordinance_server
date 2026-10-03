import requests
# Not Using This
def wol_wake(mac, url, ha_token, broadcast_address="255.255.255.255", broadcast_port="9"):
    wol_url = f"{url}/api/services/wake_on_lan/send_magic_packet"
    headers = {"Authorization": f"Bearer {ha_token}"}
    data = {"mac": mac, "broadcast_address": broadcast_address, "broadcast_port": broadcast_port}
    req = requests.post(wol_url, headers=headers, json=data)
    if req:
        return True
    else:
        return False