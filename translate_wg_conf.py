#!/usr/bin/env python3

# Takes a WireGuard configuration file in INI format.
# Translates it to hostname.if(5) format.

from base64 import b64decode
import configparser
import ipaddress
import sys


def check_wg_key_validity(key, key_name="Key"):
    """
    Validate the provided WireGuard key.

    Validation consists of these steps:
    - base64 decode the key.
    - check if its decoded length is 32 bytes.

    Raises a ValueError if the length check fails.
    """
    b64decoded_key = b64decode(bytes(key, "utf-8"), validate=True)
    if len(b64decoded_key) != 32:
        raise ValueError(f"{key_name} didn't base64 decode to 32 bytes.")
    return True


def find_ip_addresses(potential_addresses):
    """
    Searches a list for IP addresses.

    Returns a dictionary with these entries:
    "ip": list of IP addresses
    "ip4": list of IPv4 addresses
    "ip6": list of IPv6 addresses
    """
    ip_addresses = {
        "ip": [],
        "ip4": [],
        "ip6": [],
    }

    for address in potential_addresses:
        try:
            _ip = ipaddress.ip_interface(address)
        except ipaddress.AddressValueError:
            continue

        if _ip.version == 4:
            ip_addresses["ip4"].append(_ip.with_prefixlen)
        elif _ip.version == 6:
            ip_addresses["ip6"].append(_ip.with_prefixlen)

        ip_addresses["ip"].append(_ip.with_prefixlen)

    return ip_addresses


try:
    INI_FILE = sys.argv[1]
except IndexError:
    print(
        f"{sys.argv[0]} needs a WireGuard configuration file.", file=sys.stderr
    )
    sys.exit(1)

with open(file=INI_FILE, mode="r", encoding="utf-8") as f:
    ini_parser = configparser.ConfigParser()
    ini_parser.read_file(f)


wg_config_data = {
    "address": ini_parser.get(section="Interface", option="Address"),
    "private_key": ini_parser.get(section="Interface", option="PrivateKey"),
    "allowed_ips": ini_parser.get(section="Peer", option="AllowedIPs"),
    "endpoint": ini_parser.get(section="Peer", option="Endpoint"),
    "public_key": ini_parser.get(section="Peer", option="PublicKey"),
}

check_wg_key_validity(wg_config_data["private_key"], key_name="PrivateKey")
check_wg_key_validity(wg_config_data["public_key"], key_name="PublicKey")

wg_endpoint_ip, wg_endpoint_port = wg_config_data["endpoint"].split(":")

wg_allowed_ips = find_ip_addresses(wg_config_data["allowed_ips"].split(","))
wg_if_addresses = find_ip_addresses(wg_config_data["address"].split(","))


print("wgkey " + wg_config_data["private_key"])
print("wgpeer " + wg_config_data["public_key"] + " \\")
print("\t" + f"wgendpoint {wg_endpoint_ip} {wg_endpoint_port} \\")

for allowed_ip in wg_allowed_ips["ip"]:
    if allowed_ip == wg_allowed_ips["ip"][-1]:
        print("\t" + f"wgaip {allowed_ip}")
    else:
        print("\t" + f"wgaip {allowed_ip} \\")

for ip4_addr in wg_if_addresses["ip4"]:
    print(f"inet {ip4_addr}")

for ip6_addr in wg_if_addresses["ip6"]:
    print(f"inet6 {ip6_addr}")
