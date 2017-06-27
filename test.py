import ipaddress as ip

ipaddr = ip.IPv4Address('192.10.1.15')
print(ipaddr)
netmask = ip.IPv4Address('255.255.255.0')
print(netmask)
ipmask = int(ipaddr) & int(netmask)
print(ip.IPv4Address(ipmask))
