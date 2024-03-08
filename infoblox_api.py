import json
import re, os, sys, requests
import ipaddress
from infoblox_client import connector
from infoblox_client import objects

FRAMEWORK_DEV_URL=''
FRAMEWORK_PROD_URL=''

class mycompany_infoblox: 

    def connect(host: str, user: str, password: str):

        wapi_url = f"https://{host}/wapi/v2.10.5" #This was the latest wapi version as of March. 17th, 2022
        USER = user
        PASS = password

        params = {
                'host': host, 
                'username': user, 
                'password': password, 
                'http_request_timeout': 300, 
                'max_results': 2000, 
                'max_retries': 1
                }
        
        try: 
            conn = connector.Connector(params)
        except Exception as e: 
            print('Unable to make Infoblox connection because of error: ' + e)
        
        return conn
    
###############################################################
#                   UTILITY METHODS                           #
###############################################################

    def is_valid_hostname(hostname):
        if hostname == "localhost":
            return False
        return re.match(r"(?!-)[a-z0-9-]{1,63}(?<!-)$", hostname, re.IGNORECASE)

    def is_valid_fqdn(fqdn):
        #Disable localhost support
        if "localhost" in fqdn:
            return False
        #Disable short name support for fqdn
        if "." not in fqdn:
            return False
        return re.match(r'^(?!.{255}|.{253}[^.])([a-z0-9](?:[-a-z-0-9]{0,61}[a-z0-9])?\.)*[a-z0-9](?:[-a-z0-9]{0,61}[a-z0-9])?[.]?$', fqdn, re.IGNORECASE)
    
    def is_valid_mac(mac_address):
        if (mac_address == None):
            return False

        regex = ("^([0-9A-Fa-f]{2}[:-])" + "{5}([0-9A-Fa-f]{2})|" + "([0-9a-fA-F]{4}\\." + "[0-9a-fA-F]{4}\\." + "[0-9a-fA-F]{4})$")
        compiled_regex = re.compile(regex)

        if(re.search(compiled_regex, mac_address)):
            return True
        else:
            return False
    
    def is_valid_ip(address):
        if address == '0.0.0.0':
            return False
        
        try:
            address = ipaddress.ip_address(address)
            return True
        except ValueError:
            return False

    def get_ptr_addr(address):
        try:
            address = ipaddress.ip_address(address).reverse_pointer
            return address
        except ValueError:
            print(1, f"ERROR: Invalid IP Address {address}")

    def is_valid_network(network):
        if "/" not in network:
            return False
        try:
            network = ipaddress.ip_network(network)
            return True
        except ValueError:
            return False
        
    def check_record_values(conn, name, dns_view, dns_zone, ip_address):
        if not conn.is_valid_hostname(name):
            conn.do_exit(1, f"Error: The hostname {name} is not valid.")
        if not conn.is_valid_zone(conn, dns_view, dns_zone):
            conn.do_exit(1, f"Error: The zone name, {dns_zone}, is not a valid zone.")
        if not conn.is_valid_ip(ip_address):
            conn.do_exit(1, f"Error: The IP address {ip_address} is not valid.")
        if not conn.is_valid_fqdn(f"{name}.{dns_zone}"):
            conn.do_exit(1, f"Error: The FQDN, {name}.{dns_zone}, is not valid.")
        if conn.ip_in_dhcp_range(conn, ip_address):
            conn.do_exit(1, f"Error: The IP address, {ip_address}, is in a DHCP Range.")
        if conn.fqdn_has_record(conn, dns_view, f"{name}.{dns_zone}"):
            conn.do_exit(1, f"Error: The FQDN, {name}.{dns_zone}, is already in use.")


    def check_ping(ip_address):
        response = os.system(f"ping -c 1 {ip_address} >/dev/null 2>&1")
        # and then check the response...
        if response == 0:
            pingstatus = True
        else:
            pingstatus = False
        return pingstatus

    def do_exit(exit_code, message):
        print(f'ಠ_ಠ{message}ಠ_ಠ') # ಠ_ಠ is used as a special seperator to parse output from jenkins logs. :-)
        sys.exit(exit_code)


###############################################################
#                   DNS METHODS                               #
###############################################################

    def getRecord(conn, type, view, name, ipv4addr="", ptrdname=""):
        #Return object if record is found. Otherwise, return None.
        if type == "HostRecordV4":
            return objects.HostRecord.search(connector=conn, view=view, name=name)
        if type == "ARecord":
            return objects.ARecord.search(connector=conn, view=view, name=name, ipv4addr=ipv4addr)
        if type == "PtrRecordV4":
            return objects.PtrRecordV4.search(connector=conn, view=view, name=name, ptrdname=ptrdname)
        if type == "CNAMERecord":
            return objects.CNAMERecord.search(connector=conn, view=view, name=name)

        #If no type matches above return None.
        print(f"{type} does not match a supported type for getRecord.")
        return None
    
    def createRecord(conn, type, view, name, comment, cname="", ipv4addr="", ptrdname="", mac=""):

        if mycompany_infoblox.getRecord(conn, type=type, view=view, name=name, ipv4addr=ipv4addr, ptrdname=ptrdname) is None:
            if type == "HostRecordV4":
                try:
                    ip = objects.IP.create(ip=ipv4addr, mac=mac)
                    return objects.HostRecord.create(conn, view=view, name=name, ip=ip, comment=comment)
                except Exception as e:
                    return f"Error: Unable to create HostRecordV4 for {name} with IP Address {ipv4addr} and MAC Address {mac}"
            if type == "ARecord":
                try:
                    record = objects.ARecord.create(connector=conn, check_if_exists=False, view=view, name=name, ipv4addr=ipv4addr, comment=comment)
                    if name not in record._ref:
                        return f"Error: Conflict with an existing DNS record, {record._ref}"
                    return record
                except Exception as e:
                    return f"Error: Unable to create ARecord for {name} with IP Address {ipv4addr}"
            if type == "PtrRecordV4":
                try:
                    return objects.PtrRecordV4.create(connector=conn, view=view, name=name, ptrdname=ptrdname, ipv4addr=ipv4addr, comment=comment)
                except Exception as e:
                    return f"Error: Unable to create PTR Record for {name} with PTRDName {ptrdname}"
            if type == "CNAMERecord":
                try:
                    return objects.CNAMERecord.create(connector=conn, view=view, name=name, canonical=cname, comment=comment)
                except Exception as e:
                    return (f"Error: Unable to create CNAMERecord, {name}, for {cname}. Error: " + e)
        else:
            return f"Warning: Record not created! {type} already exists for {name}"

    def updateRecord(conn, record, name, ipv4addr, ptrdname=""):
        print(f"Updating {record.__class__.__name__}... ", end='')
        if record.__class__.__name__ == "HostRecordV4":
            #Update Object Attributes
            if hasattr(record, 'extattrs'):
                record.extattrs = "" #Clear Extensible Attributes on update to avoid Inheritance bug
            record.name = name
            record.ipv4addrs[0].ipv4addr = ipv4addr
            record.comment = "Updated via Jenkins automation"
            #record.ipv4addrs[0].configure_for_dhcp = True #If false, a MAC address MUST be supplied.
            try:
                objects.HostRecord.update(record)
            except Exception as e:
                mycompany_infoblox.do_exit(1, f"Error: Unable to update HostRecordV4")
        elif record.__class__.__name__ == "ARecord":
            #Update Object Attributes
            record.name = name
            record.ipv4addr = ipv4addr
            record.comment = "Updated via Jenkins automation"
            try:
                objects.ARecord.update(record)
            except Exception as e:
                mycompany_infoblox.do_exit(1, f"Error: Unable to update ARecord")
        elif record.__class__.__name__ == "PtrRecordV4":
            #Update Object Attributes
            record.name = name
            record.ipv4addr = ipv4addr
            record.ptrdname = ptrdname
            record.comment = "Updated via Jenkins automation"
            try:
                objects.PtrRecordV4.update(record)
            except Exception as e:
                mycompany_infoblox.do_exit(1, f"Error: Unable to update PtrRecordV4")
        else:
            #If no type matches above return None.
            mycompany_infoblox.do_exit(1, f"{record.__class__.__name__} does not match a supported record type for updateRecord.")
        print(f"{record.__class__.__name__} updated successfully!")

    def deleteRecord(conn, record):
        if record.__class__.__name__ == "HostRecordV4":
            try:
                objects.HostRecord.delete(record)
            except Exception as e:
                return f"Error: {e}"
        elif record.__class__.__name__ == "ARecord":
            try:
                objects.ARecord.delete(record)
            except Exception as e:
                return f"Error: {e}"
        elif record.__class__.__name__ == "PtrRecordV4":
            try:
                objects.PtrRecordV4.delete(record)
            except Exception as e:
                return f"Error: {e}"
        elif record.__class__.__name__ == "CNAMERecord":
            try:
                objects.CNAMERecord.delete(record)
            except Exception as e:
                return f"Error: {e}"
        else:
            #If no type matches above return None.
            return f"Error: {record.__class__.__name__} does not match a supported record type for deleteRecord."
        if record.name != None:
            return f"{record.__class__.__name__} for {record.name} deleted successfully!"
        elif record.ptrdname != None:
            return f"{record.__class__.__name__} for {record.ptrdname} deleted successfully!"

    def is_valid_zone(conn, view, zone):
        zone_format="FORWARD" # We only want to return forward zone formated zones
        result = objects.DNSZone.search(connector=conn, view=view, zone_format=zone_format, fqdn=zone)
        if(result == None):
            return False
        return True

    def fqdn_has_record(conn, view, fqdn):
        if objects.HostRecord.search(connector=conn, view=view, name=fqdn) is not None:
            return True
        elif objects.ARecord.search(connector=conn, view=view, name=fqdn) is not None:
            return True
        elif objects.PtrRecordV4.search(connector=conn, view=view, ptrdname=fqdn) is not None:
            return True
        elif objects.CNAMERecord.search(connector=conn, view=view, name=fqdn) is not None:
            return True
        return False

###############################################################
#                   IPAM METHODS                              #
###############################################################

    default_headers = {"Accept":"application/json"}

    def __rest(conn, method, url, auth=None, headers=None, body=None):
        if(headers == None):
            headers = conn.default_headers

        if method == "POST":
            try:
                response = requests.post(url, auth=auth, json=body, headers=headers, verify=False)
            except Exception as e:
                print(f"ERROR calling {url}: {e}")
        elif method == "GET":
            try:
                response = requests.get(url, auth=auth, headers=headers, verify=False)
            except Exception as e:
                print(f"ERROR calling {url}: {e}")
        else:
            print(f"ERROR: Unsupported method: {method}")
            response = None
        return response

    def get_records_by_network(conn, view, network, **kwargs):
        records = objects.IPv4Address.search_all(connector=conn, view=view, network=network, **kwargs)
        # This is not handling types lists properly. It's converting to string when it should do &types=<type1>&types=<type2>...etc.
        # Valid URL Example:
        # https://ddi-lab001.onemycompany.com/wapi/v2.1/ipv4address?network=10.228.28.0%2F22&status=USED&types=HOST&types=A&types=PTR&_return_fields=dhcp_client_identifier%2Cextattrs%2Cip_address%2Cis_conflict%2Clease_state%2Cmac_address%2Cnames%2Cnetwork%2Cnetwork_view%2Cobjects%2Cstatus%2Ctypes%2Cusage%2Cusername&_max_results=2000
        return records

    def get_host_records_by_ip(conn, ip_address):
        try:
            record = conn.get_object('record:host', {'ipv4addr': ip_address})
        except Exception as e:
            mycompany_infoblox.do_exit(1, f"Unable to get Host record for {ip_address}. Reason: {e}")
        return record

    def get_a_records_by_ip(conn, ip_address):
        try:
            record = conn.get_object('record:a', {'ipv4addr': ip_address})
        except Exception as e:
            mycompany_infoblox.do_exit(1, f"Unable to get A record for {ip_address}. Reason: {e}")
        return record

    def get_ipv4_records_by_ip(conn, ip_address):
        try:
            record = conn.get_object('ipv4address', {'ip_address': ip_address})
        except Exception as e:
            mycompany_infoblox.do_exit(1, f"Unable to get IP address record for {ip_address}. Reason: {e}")
        return record

    def ip_in_use(conn, ip_address):
        record = conn.get_ipv4_records_by_ip(conn, ip_address)
        if record:
            if record[0]['status'] != "UNUSED":
                return False
            else:
                return True
        mycompany_infoblox.do_exit(1, f"Unable to find network (subnet) with record for {ip_address}")

    def ip_in_dhcp_range(conn, ip_address):
        record = mycompany_infoblox.get_ipv4_records_by_ip(conn, ip_address)
        if record:
            if 'DHCP_RANGE' in record[0]['types']:
                return True
            else:
                return False
        mycompany_infoblox.do_exit(1, f"Unable to find network (subnet) record for {ip_address}")

    def reserve_ip_address(conn, ip_address, comment):
        try:
            return objects.FixedAddress.create(conn, network_view='default', mac='00:00:00:00:00:00', ip=ip_address, comment=comment, check_if_exists=False)
        except Exception as e:
            mycompany_infoblox.do_exit(1, f"Unable to reserve IP address for {ip_address}")

    def get_network(conn, cidr):
        if not mycompany_infoblox.is_valid_network(cidr):
            conn.print_api_response(ip_address="", status="error", status_message=f"{cidr} is not a valid network CIDR format.")
            mycompany_infoblox.do_exit(1, f"{cidr} is not a valid network CIDR format.")
        url = f"{conn.wapi_url}/network?network={cidr}"
        response = mycompany_infoblox.__rest(method="GET", url=url, auth=(conn.USER, conn.PASS))
        return response.json()

    def get_next_available_ip(conn, network):
        url = f"{conn.wapi_url}/{network[0]['_ref']}?_function=next_available_ip"
        body = {"num":1} 
        response = conn.__rest(method="POST", url=url, auth=(conn.USER, conn.PASS), body=body)
        try:
            ip_address = response.json()['ips'][0]
        except Exception as e:
            conn.print_api_response(ip_address="", status="error", status_message=f"Unable to get available IP address from network {network[0]['network']}")
            mycompany_infoblox.do_exit(1, f"Error: Unable to get available IP address from network {network[0]['network']}")
        return ip_address

    def get_unused_ip(conn, cidr, counter=0):
        network = mycompany_infoblox.get_network(cidr)
        ip_address = mycompany_infoblox.get_next_available_ip(network)
        if not mycompany_infoblox.is_valid_ip(ip_address):
            conn.print_api_response(ip_address="", status="error", status_message=f"IP address, {ip_address}, invalid.")
            mycompany_infoblox.do_exit(1, f"Error: IP address, {ip_address}, invalid.")

        if(mycompany_infoblox.check_ping(ip_address)):
            print(f"WARNING: IP address, {ip_address}, marked unused but pings. Marking IP Bandit in Infoblox.")
            mycompany_infoblox.reserve_ip_address(conn, ip_address, comment="Bandit. Created via the Automated server build process.")
            counter = counter + 1
            if(counter > 5):
                conn.print_api_response(ip_address="", status="error", status_message=f"Aborting after 5 failed ping checks.")
                mycompany_infoblox.do_exit(1, f"Error: Aborting after 5 failed ping checks.")
            return mycompany_infoblox.get_unused_ip(conn, cidr, counter)
        return ip_address
