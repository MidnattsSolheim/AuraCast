import subprocess

PHUE_IP_ADDRESS = "10.42.0.95"
LIGTHNAME = "fluxlight"

VETH_MAIN = "veth0"
VETH_PEER = "veth1"

def veth_exists(interface):
    try:
        subprocess.check_output(["ip", "link", "show", interface], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def create_veth_pair():
    if veth_exists(VETH_MAIN):
        print(f"[veth] {VETH_MAIN} already exists. Skipping creation.")
        return
    try:
        subprocess.run(["ip", "link", "add", VETH_MAIN, "type", "veth", "peer", "name", VETH_PEER], check=True)
        subprocess.run(["ip", "link", "set", VETH_MAIN, "up"], check=True)
        subprocess.run(["ip", "link", "set", VETH_PEER, "up"], check=True)
        print(f"[veth] Created and brought up {VETH_MAIN} and {VETH_PEER}")
    except subprocess.CalledProcessError as e:
        print(f"[veth] Error creating veth pair: {e}")

def delete_veth_pair():
    if veth_exists(VETH_MAIN):
        try:
            subprocess.run(["ip", "link", "delete", VETH_MAIN], check=True)
            print(f"[veth] Deleted veth pair {VETH_MAIN} and {VETH_PEER}")
        except subprocess.CalledProcessError as e:
            print(f"[veth] Error deleting veth pair: {e}")


