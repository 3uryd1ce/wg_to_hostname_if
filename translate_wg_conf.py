#!/usr/bin/env python3

# Takes a WireGuard configuration file in INI format.
# Translates it to hostname.if(5) format.

from base64 import b64decode
import configparser
import ipaddress
import sys


class WGConfAccessor:
    """
    Retrieves options from sections in the provided WireGuard INI file.
    """

    def __init__(self, file):
        with open(file=file, mode="r", encoding="utf-8") as f:
            ini_parser = configparser.ConfigParser()
            ini_parser.read_file(f)

        self.ini_parser = ini_parser

    def get_interface_private_key(self):
        """
        Retrieves PrivateKey option from Interface section in the INI file.
        """
        return self.ini_parser.get(section="Interface", option="PrivateKey")

    def get_interface_address(self):
        """
        Retrieves Address option from Interface section in the INI file.
        """
        return self.ini_parser.get(section="Interface", option="Address")

    def get_peer_public_key(self):
        """
        Retrieves PublicKey option from Peer section in the INI file.
        """
        return self.ini_parser.get(section="Peer", option="PublicKey")

    def get_peer_allowed_ips(self):
        """
        Retrieves AllowedIPs option from Peer section in the INI file.
        """
        return self.ini_parser.get(section="Peer", option="AllowedIPs")

    def get_peer_endpoint(self):
        """
        Retrieves Endpoint option from Peer section in the INI file.
        """
        return self.ini_parser.get(section="Peer", option="Endpoint")


class WGKeyValidator:
    """
    Validate public and private WireGuard keys.
    """

    def validate_key(self, key, key_name="Key"):
        """
        Validate the provided key.

        Validation consists of these steps:
        - base64 decode the key.
        - check if its decoded length is 32 bytes.

        If validation fails, raise an exception:
        - If it failed during base64 decoding, see b64decode in base64.
        - If it failed the length check, the exception is a ValueError.
        """
        b64decoded_key = b64decode(bytes(key, "utf-8"), validate=True)
        if len(b64decoded_key) != 32:
            raise ValueError(f"{key_name} didn't base64 decode to 32 bytes.")


class IPAddressFinder:
    """
    Given a list, find IPv4/IPv6 addresses within that list.
    """

    def __init__(self, potential_addresses):
        self.potential_addresses = potential_addresses
        self.ip_addresses = []
        self.ipv4_addresses = []
        self.ipv6_addresses = []

    def _is_ip(self, ip):
        """
        Check if the given input is a valid IP address.

        Parameters:
        ip (str): The input string to be checked.

        Returns:
        - ipaddress.IPv4Interface or ipaddress.IPv6Interface, if ip
          is a valid IP address.
        - False if it isn't.
        """

        try:
            _ip = ipaddress.ip_interface(ip)
        except ipaddress.AddressValueError:
            return False
        return _ip

    def _is_ipv4(self, ip):
        """
        Check if the given input is a valid IPv4 address.

        Parameters:
        ip (str): The input string to be checked.

        Returns:
        - ipaddress.IPv4Interface if ip is a valid IPv4 address.
        - False if it isn't.
        """

        try:
            _ip4 = ipaddress.IPv4Interface(ip)
        except ipaddress.AddressValueError:
            return False
        return _ip4

    def _is_ipv6(self, ip):
        """
        Check if the given input is a valid IPv6 address.

        Parameters:
        ip (str): The input string to be checked.

        Returns:
        - ipaddress.IPv6Interface if ip is a valid IPv6 address.
        - False if it isn't.
        """
        try:
            _ip6 = ipaddress.IPv6Interface(ip)
        except ipaddress.AddressValueError:
            return False
        return _ip6

    def find_ip_addresses(self):
        """
        Searches a list for IP addresses.
        Returns a new list containing the addresses it found.
        """
        for address in self.potential_addresses:
            if self._is_ip(address):
                self.ip_addresses.append(address)
            else:
                continue

            if self._is_ipv4(address):
                self.ipv4_addresses.append(address)
            elif self._is_ipv6(address):
                self.ipv6_addresses.append(address)

        return self.ip_addresses


try:
    INI_FILE = sys.argv[1]
except IndexError:
    print(
        f"{sys.argv[0]} needs a WireGuard configuration file.", file=sys.stderr
    )
    sys.exit(1)

wg_accessor = WGConfAccessor(INI_FILE)
key_validator = WGKeyValidator()

wg_private_key = wg_accessor.get_interface_private_key()
key_validator.validate_key(wg_private_key, key_name="PrivateKey")

wg_public_key = wg_accessor.get_peer_public_key()
key_validator.validate_key(wg_public_key, key_name="PublicKey")

wg_endpoint_ip, wg_endpoint_port = wg_accessor.get_peer_endpoint().split(":")

wg_allowed_ips = wg_accessor.get_peer_allowed_ips().split(",")

wg_if_addrs = wg_accessor.get_interface_address().split(",")
wg_if_ip_finder = IPAddressFinder(wg_if_addrs)
wg_if_ip_finder.find_ip_addresses()


print(f"wgkey {wg_private_key}")
print(f"wgpeer {wg_public_key} \\")
print(f"\twgendpoint {wg_endpoint_ip} {wg_endpoint_port} \\")

for allowed_ip in wg_allowed_ips:
    if allowed_ip == wg_allowed_ips[-1]:
        print(f"\twgaip {allowed_ip}")
    else:
        print(f"\twgaip {allowed_ip} \\")

for ip4_addr in wg_if_ip_finder.ipv4_addresses:
    print(f"inet {ip4_addr}")

for ip6_addr in wg_if_ip_finder.ipv6_addresses:
    print(f"inet6 {ip6_addr}")
