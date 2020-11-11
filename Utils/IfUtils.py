import math
import re


def module_exists(module_name):
    try:
        __import__(module_name)
    except ImportError:
        return False
    else:
        return True


###
#  Name:    expand_int_pattern
#  Inputs:  i - generate value at position i of the sequence (zero-based)
#           count - number of values to generate
#           start - start value
#           step - step value
#           repeat - repeat value
#           recycle - recycle value
#           max - a maximum value (if needed, say for VLANs)
#  Outputs: list of generated values starting at position i (zero-based)
#  Description: Generates a list of ints based on the given start, step,
#           repeat, and recycle parameters.  Will generate values from
#           position i.  i is zero based so i = 8 will map to the 9th
#           value in the sequence.
#  Equations:
#    i is zero based
#
#   With Recycling:
#     cycle - number of values that will be repeated and recycled.
#     If 0, open-ended (no recycling).
#     repPattern - repeat structure given recycling
#     value - value given start, step, repeat, recycle, and i
#
#     cycle = (repeat + 1) * recycle
#     repPattern = floor ((i % cycle) / (repeat + 1))
#     value = start + (step * repPattern)
#
#   Without Recycling:
#     repPattern - repeat structure
#     value - value given start, step, repeat, recycle, and i
#
#     repPattern = floor (i / repeat)
#     value = start + (step * repPattern)
#
#  Example:
# Start=100, step=1, max=103
# expand_int_pattern(0, 10, 100, 1, 0, 0, 103)
# [100, 101, 102, 103, 0, 1, 2, 3, 4, 5]
#
# Repeat each value once
# expand_int_pattern(0, 10, 100, 1, 1, 0, 103)
# [100, 100, 101, 101, 102, 102, 103, 103, 0, 0]
#
# Recycle pattern after four (unique) values
# expand_int_pattern(0, 10, 100, 1, 0, 4)
# [100, 101, 102, 103, 100, 101, 102, 103, 100, 101]
#
# Recycle pattern after four values with a max (wrap)
# expand_int_pattern(0, 10, 100, 1, 0, 4, 102)
# [100, 101, 102, 0, 100, 101, 102, 0, 100, 101]
#
# Repeat each value, recycle after four values, wrap
# expand_int_pattern(0, 10, 100, 1, 1, 4, 102)
# [100, 100, 101, 101, 102, 102, 0, 0, 100, 100]
###
def expand_int_pattern(i, count, start, step, repeat, recycle, max=None):
    if count < 0:
        return None
    if i < 0:
        return None
    if repeat < 0:
        repeat = 0
    if recycle < 0:
        recycle = 0

    val_list = []
    j = 0

    while j < count:
        cycle = (repeat + 1) * recycle
        if cycle > 0:
            # We have recycling (fixed number of values)
            rep_pattern = int(math.floor((i % cycle) / (repeat + 1)))
        else:
            # Open-ended value incrementation (unless there is a max)
            rep_pattern = int(math.floor(i / (repeat + 1)))

        # For Ipv4, Ipv6, and MAC, this is the only line that must change
        val = start + (step * rep_pattern)

        # Apply the max if necessary
        if max is not None:
            val = val % (max + 1)
        val_list.append(val)
        i = i + 1
        j = j + 1

    return val_list


###
#  Name:    expand_ip_pattern
#  Inputs:  i - generate value at position i of the sequence (zero-based)
#           count - number of values to generate
#           start - start value
#           step - step value
#           repeat - repeat value
#           recycle - recycle value
#  Outputs: list of generated values starting at position i (zero-based)
#  Description: Generates a list of ip addrs based on the given start, step,
#           repeat, and recycle parameters.  Will generate values from
#           position i.  i is zero based so i = 8 will map to the 9th
#           value in the sequence.
#  See expand_int_pattern for more details
###
def expand_ip_pattern(i, count, start, step, repeat, recycle, prefix=None):
    if count < 0:
        return None
    if i < 0:
        return None
    if repeat < 0:
        repeat = 0
    if recycle < 0:
        recycle = 0

    val_list = []
    j = 0

    while j < count:
        cycle = (repeat + 1) * recycle
        if cycle > 0:
            # We have recycling (fixed number of values)
            rep_pattern = int(math.floor((i % cycle) / (repeat + 1)))
        else:
            # Open-ended value incrementation (unless there is a max)
            rep_pattern = int(math.floor(i / (repeat + 1)))

        val = GetNextIPAddress(start, step, rep_pattern, prefix)
        val_list.append(val)
        i = i + 1
        j = j + 1

    return val_list


###
#  Name:    expand_mac_pattern
#  Inputs:  i - generate value at position i of the sequence (zero-based)
#           count - number of values to generate
#           start - start value
#           step - step value
#           repeat - repeat value
#           recycle - recycle value
#  Outputs: list of generated values starting at position i (zero-based)
#  Description: Generates a list of MAC addrs based on the given start, step,
#           repeat, and recycle parameters.  Will generate values from
#           position i.  i is zero based so i = 8 will map to the 9th
#           value in the sequence.
#  See expand_int_pattern for more details
###
def expand_mac_pattern(i, count, start, step, repeat, recycle):
    if count < 0:
        return None
    if i < 0:
        return None
    if repeat < 0:
        repeat = 0
    if recycle < 0:
        recycle = 0

    val_list = []
    j = 0

    while j < count:
        cycle = (repeat + 1) * recycle
        if cycle > 0:
            # We have recycling (fixed number of values)
            rep_pattern = int(math.floor((i % cycle) / (repeat + 1)))
        else:
            # Open-ended value incrementation (unless there is a max)
            rep_pattern = int(math.floor(i / (repeat + 1)))

        val = GetNextMacAddr(start, step, rep_pattern)
        val_list.append(val)
        i = i + 1
        j = j + 1

    return val_list


def GetNextIPAddress(address, step, index, prefix=None):
    '''
    Desc: Computes and returns back the next IP (IPv4 or IPv6) address
          based on the input params. The step can be a valid IP or an
          integer for IPv4 but has to be an integer for IPv6.
    Args: address - IP address in IPv4/v6 format
          step - Increment value (IPv4/integer format for IPv4 addresses
                 and integer format for IPv6 addresses)
          index - The multipler for multiplying the step value with.
          prefix - Prefix value (integer) -- Can be empty if the step
                   is in IPv4 format
    Return: An incremental IP address in the same format as the input
    '''
    if isinstance(step, int) and module_exists('netaddr') and prefix is not None:
        import netaddr
        startNwk = netaddr.IPNetwork(address + '/' + str(prefix))
        nextNwk = startNwk.next(step * index)
        nextAddr = netaddr.IPAddress(nextNwk.value)
        return str(nextAddr)
    elif IsValidIpv4(step):
        return GetNextIpv4AddrWithStepAsIp(address, step, index)
    elif IsValidIpv6(step):
        return GetNextIpv6AddrWithStepAsIp(address, step, index)
    else:
        return ""


def GetPrevIPAddress(address, step, index, prefix=None):
    '''
    Desc: Computes and returns back the previous IP (IPv4 or IPv6) address
          based on the input params. The step can be a valid IP or an
          integer for IPv4 but has to be an integer for IPv6.
    Args: address - IP address in IPv4/v6 format
          step - Decrement value (IPv4/integer format for IPv4 addresses
                 and integer format for IPv6 addresses)
          index - The multipler for multiplying the step value with.
          prefix - Prefix value (integer) -- Can be empty if the step
                   is in IPv4 format
    Return: An incremental IP address in the same format as the input
    '''
    if isinstance(step, int) and module_exists('netaddr') and prefix is not None:
        import netaddr
        startNwk = netaddr.IPNetwork(address + '/' + str(prefix))
        nextNwk = startNwk.next(step * index)
        nextAddr = netaddr.IPAddress(nextNwk.value)
        return str(nextAddr)
    elif IsValidIpv4(step):
        return GetPrevIpv4AddrWithStepAsIp(address, step, index)
    elif IsValidIpv6(step):
        return GetPrevIpv6AddrWithStepAsIp(address, step, index)
    else:
        return ""


def GetNextMacAddress(address, prefix, step, index):
    '''
    Desc: Compute and retrieve the next MAC address based on the inputs
          provided.
    Args: address - Base MAC address
          prefix - The bit position to increment the MAC address from (0-48)
          step - The base value to increment the MAC by
          index - The multipler for multiplying the step value with.
    '''
    nextMacAddr = address
    if module_exists('netaddr'):
        import netaddr
        startMacAddr = netaddr.EUI(address)
        startV6Addr = netaddr.IPAddress(int(startMacAddr))
        startNwk = netaddr.IPNetwork('::/0')
        startNwk.value = int(startV6Addr)
        startNwk.prefixlen = prefix + 80
        nextNwk = startNwk.next(step * index)
        nextMacAddr = netaddr.EUI(nextNwk.value)

        # Create custom formatted mac address, zero padded and upper cased
        class mac_custom(netaddr.mac_unix):
            pass
        mac_custom.word_fmt = '%.2X'
        nextMacAddr.dialect = mac_custom
    else:
        macStep = GetMacStepFromPrefix(prefix)
        nextMacAddr = GetNextMacAddr(address, macStep, index)

    return str(nextMacAddr)


def GetPrevMacAddress(address, prefix, step, index):
    '''
    Desc: Compute and retrieve the next MAC address based on the inputs
          provided.
    Args: address - Base MAC address
          prefix - The bit position to decrement the MAC address from (0-48)
          step - The base value to decrement the MAC by
          index - The multipler for multiplying the step value with.
    '''
    nextMacAddr = address
    if module_exists('netaddr'):
        import netaddr
        startMacAddr = netaddr.EUI(address)
        startV6Addr = netaddr.IPAddress(int(startMacAddr))
        startNwk = netaddr.IPNetwork('::/0')
        startNwk.value = int(startV6Addr)
        startNwk.prefixlen = prefix + 80
        nextNwk = startNwk.next(-step * index)
        nextMacAddr = netaddr.EUI(nextNwk.value)

        # Create custom formatted mac address, zero padded and upper cased
        class mac_custom(netaddr.mac_unix):
            pass
        mac_custom.word_fmt = '%.2X'
        nextMacAddr.dialect = mac_custom
    else:
        macStep = GetMacStepFromPrefix(prefix)
        nextMacAddr = GetPrevMacAddr(address, macStep, index)

    return str(nextMacAddr)


def ConvertMacToU64(baseMacAddrList):
    val = int(baseMacAddrList[0], 16)
    i = 1
    while (i < 6):
        val = val << 8
        val = val | int(baseMacAddrList[i], 16)
        i = i + 1
    return val


def ConvertIpToU32(baseIpAddrList):
    '''
    Desc: Converts a single IPv4 address into a 32 bit integer value
    Args: Provide a list of integers representing an IPv4 address i.e.
          192.168.1.1 would be passed in as [192,168,1,1]
    Return: An integer value representation of the input IPv4 address
    '''
    val = int(baseIpAddrList[0])
    i = 1
    while (i < 4):
        val = val << 8
        val = val | int(baseIpAddrList[i])
        i = i + 1
    return val


def ConvertMacToString(macAddrVal):

    macAddrList = [0, 0, 0, 0, 0, 0]
    val = macAddrVal
    i = 0
    while (i < 6):
        macAddrList[5 - i] = int(val & 0xff)
        val = val >> 8
        i = i + 1

    return ':'.join([str(item) for item in macAddrList])


def ConvertMacToHexString(macAddrVal):
    '''
    Desc: Converts a mac address value into the hexadecimal string format.
    Args: macAddrVal: mac address as a numeric value.
    Return: Mac address in string format.
    '''
    macAddrList = [0, 0, 0, 0, 0, 0]
    val = macAddrVal
    i = 0
    while (i < 6):
        macAddrList[5 - i] = int(val & 0xff)
        val = val >> 8
        i = i + 1

    return ':'.join([str(hex(item)[2:]).upper().zfill(2) for item in macAddrList])


def ConvertIpToString(ipAddrVal):
    '''
    Desc: Cpnverts an Ipv4 address in integer format into a string
    Args: ipAddrVal: ip addr as an integer
    Return: String value for the IP
    '''
    ipAddrList = [0, 0, 0, 0]
    val = ipAddrVal
    i = 0
    while (i < 4):
        ipAddrList[3 - i] = int(val & 0xff)
        val = val >> 8
        i = i + 1

    return ".".join([str(item) for item in ipAddrList])


def GetMacStepFromPrefix(macPrefix):
    '''
    Desc: Computes a MAC step from the prefix value given as input
    Args: prefix: Prefix for a MAC address. Valid values MAC
    return: MAC address string in the format X:X:X:X:X:X
    '''
    maxMacPrefixLen = 48
    if macPrefix == 0:
        return '0:0:0:0:0:0'
    elif macPrefix > maxMacPrefixLen:
        macPrefix = 48

    offset = maxMacPrefixLen - macPrefix
    macStep = 0x000000000001 << offset
    stringMacStep = ConvertMacToString(macStep)

    return stringMacStep


def GetNextMacAddr(baseMacAddrStr, macAddrStepStr, multiplier):
    '''
    Desc: Computes and returns the next MAC address based on the
          inputs provided
    Args:
        baseMacAddrStr: Start address
        macAddrStepStr: Increment
        multipler: Multiplier for the increment
    '''
    baseMacAddrList = baseMacAddrStr.split(':')
    macAddrStepList = macAddrStepStr.split(':')
    macAddrVal = ConvertMacToU64(baseMacAddrList)
    macAddrStepVal = ConvertMacToU64(macAddrStepList)
    macAddrVal = macAddrVal + (macAddrStepVal * multiplier)
    nextMacAddr = ConvertMacToHexString(macAddrVal)

    return nextMacAddr


def GetPrevMacAddr(baseMacAddrStr, macAddrStepStr, multiplier):
    '''
    Desc: Computes and returns the next MAC address based on the
          inputs provided
    Args:
        baseMacAddrStr: Start address
        macAddrStepStr: Decrement
        multipler: Multiplier for the increment
    '''
    baseMacAddrList = baseMacAddrStr.split(':')
    macAddrStepList = macAddrStepStr.split(':')
    macAddrVal = ConvertMacToU64(baseMacAddrList)
    macAddrStepVal = ConvertMacToU64(macAddrStepList)
    macAddrVal = macAddrVal - (macAddrStepVal * multiplier)
    nextMacAddr = ConvertMacToHexString(macAddrVal)

    return nextMacAddr


def GetIpStepFromPrefix(ipPrefix):
    '''
    Desc: Computes an Ipv4 step from the prefix value given as input
    Args: prefix: Prefix for an IPv4 address. Valid values: 0-24
    return: IPv4 address string in the format X.X.X.X
    '''
    maxIpPrefixLen = 32
    if ipPrefix == 0:
        return '0.0.0.0'
    elif ipPrefix > maxIpPrefixLen:
        ipPrefix = maxIpPrefixLen

    offset = maxIpPrefixLen - ipPrefix
    ipstep = 0x00000001 << offset
    stringIpStep = ConvertIpToString(ipstep)

    return stringIpStep


def IsValidMac(mac):
    mac_elems = mac.split(":")
    if len(mac_elems) != 6:
        return False
    for elem in mac_elems:
        try:
            int(elem, 16)
        except:
            return False
        if int(elem, 16) < 0 or int(elem, 16) > 255:
            return False
    return True


def IsValidIpv4(ip):
    '''
    Desc: Determines if the string value given as input is a valid IPv4 address
    Args: ip - IP address to validate
    Returns: True/False
    '''
    strVal = str(ip)
    ipElems = strVal.split('.')
    if len(ipElems) != 4:
        return False
    for elem in ipElems:
        try:
            int(elem)
        except:
            return False
        if int(elem) < 0 or int(elem) > 255:
            return False
    return True


def IsValidIpv6(ip):
    '''
    Desc: Determines if the string value given as input is a valid IPv6 address
    Args: ip - IP address to validate
    Returns: True/False
    '''

    # Regex from: https://stackoverflow.com/questions/319279/how-to-validate-ip-address-in-python
    pattern = re.compile(r"""
        ^
        \s*                         # Leading whitespace
        (?!.*::.*::)                # Only a single whildcard allowed
        (?:(?!:)|:(?=:))            # Colon iff it would be part of a wildcard
        (?:                         # Repeat 6 times:
            [0-9a-f]{0,4}           #   A group of at most four hexadecimal digits
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
        ){6}                        #
        (?:                         # Either
            [0-9a-f]{0,4}           #   Another group
            (?:(?<=::)|(?<!::):)    #   Colon unless preceeded by wildcard
            [0-9a-f]{0,4}           #   Last group
            (?: (?<=::)             #   Colon iff preceeded by exacly one colon
             |  (?<!:)              #
             |  (?<=:) (?<!::) :    #
             )                      # OR
         |                          #   A v4 address with NO leading zeros
            (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            (?: \.
                (?:25[0-4]|2[0-4]\d|1\d\d|[1-9]?\d)
            ){3}
        )
        \s*                         # Trailing whitespace
        $
    """, re.VERBOSE | re.IGNORECASE | re.DOTALL)
    return pattern.match(ip) is not None


def GetNextIpv4AddrWithStepAsIp(baseIpAddr, ipAddrStep, multiplier):
    '''
    Desc: Computes and returns the next Ipv4 address based on the
          inputs provided
    Args:
        baseIpAddr: Start address
        ipAddrStep: Increment
        multipler: Multiplier for the increment
    '''
    sumIpAddr = []
    baseIpAddrList = baseIpAddr.split('.')
    ipAddrStepList = ipAddrStep.split('.')
    ipAddrVal = ConvertIpToU32(baseIpAddrList)
    ipAddrStepVal = ConvertIpToU32(ipAddrStepList)
    ipAddrVal = ipAddrVal + (ipAddrStepVal * multiplier)
    baseIpAddrList = ConvertIpToString(ipAddrVal).split('.')
    i = 0
    while(i < 4):
        sumIpAddr.append(baseIpAddrList[i])
        i = i + 1
    nextIpAddr = ".".join([str(x) for x in sumIpAddr])
    return nextIpAddr


def GetPrevIpv4AddrWithStepAsIp(baseIpAddr, ipAddrStep, multiplier):
    '''
    Desc: Computes and returns the previous Ipv4 address based on the
          inputs provided
    Args:
        baseIpAddr: Start address
        ipAddrStep: Decrement
        multipler: Multiplier for the decrement
    '''
    sumIpAddr = []
    baseIpAddrList = baseIpAddr.split('.')
    ipAddrStepList = ipAddrStep.split('.')
    ipAddrVal = ConvertIpToU32(baseIpAddrList)
    ipAddrStepVal = ConvertIpToU32(ipAddrStepList)
    ipAddrVal = ipAddrVal - (ipAddrStepVal * multiplier)
    baseIpAddrList = ConvertIpToString(ipAddrVal).split('.')
    i = 0
    while(i < 4):
        sumIpAddr.append(baseIpAddrList[i])
        i = i + 1
    nextIpAddr = ".".join([str(x) for x in sumIpAddr])
    return nextIpAddr


def GetNextIpv6AddrWithStepAsIp(baseIpv6Addr, ipv6AddrStep, multiplier):
    # Expand address to flat list
    base_list = GetFlatIpv6AddressList(baseIpv6Addr)
    step_list = GetFlatIpv6AddressList(ipv6AddrStep)

    # Multiplying it
    temp_list = [0, 0, 0, 0, 0, 0, 0, 0]
    for count in range(0, multiplier):
        temp_list = AddIpv6Addr(temp_list, step_list)

    step_list = temp_list
    sum_ip_list = AddIpv6Addr(base_list, step_list)
    return ConvertIpv6ListToString(sum_ip_list)


def GetPrevIpv6AddrWithStepAsIp(baseIpv6Addr, ipv6AddrStep, multiplier):
    # Expand address to flat list
    base_list = GetFlatIpv6AddressList(baseIpv6Addr)
    step_list = GetFlatIpv6AddressList(ipv6AddrStep)

    # Multiplying it
    temp_list = [0, 0, 0, 0, 0, 0, 0, 0]
    for count in range(0, multiplier):
        temp_list = AddIpv6Addr(temp_list, step_list)

    step_list = temp_list
    sum_ip_list = SubIpv6Addr(base_list, step_list)
    return ConvertIpv6ListToString(sum_ip_list)


def GetFlatIpv6AddressList(ipAddr):

    # normalize if address is "::", "X::", or "::X"
    if ipAddr.startswith(":"):
        ipAddr = "0" + ipAddr
    if ipAddr.endswith(":"):
        ipAddr = ipAddr + "0"

    # find out the :: portion
    elems = ipAddr.split("::")

    ip_list = []
    # if there is no ::, that means everything is in a flat list
    # put them in a int list
    if len(elems) == 1:
        elems = elems[0].split(":")
        for elem in elems:
            val = int(elem, 16)
            ip_list.append(val)
    elif len(elems) == 2:

        # for the first portion, see how many element by splitting with ":"
        first_elems = elems[0].split(":")
        first_portion_count = 0
        for elem in first_elems:
            if elem == "":
                ip_list.append(0)
            else:
                ip_list.append(int(elem, 16))
            first_portion_count = first_portion_count + 1

        # Now count how many item in the second portion
        sec_elems = elems[1].split(":")
        zero_cnt = 9 - (first_portion_count + len(sec_elems))

        for count in range(1, zero_cnt):
            ip_list.append(0)

        for elem in sec_elems:
            ip_list.append(int(elem, 16))

    return ip_list


def ConvertIpv6ListToString(ipList):

    ipString = ""
    for elem in ipList:
        if elem == 0:
            ipString = ipString + ":" + "0"
        else:
            ipString = ipString + ":" + hex(elem).rstrip("L").lstrip("0x")

    ipString = ipString.lstrip(":")
    return ipString


def AddIpv6Addr(firstAddressList, secondAddressList):
    '''
    Desc: Adds two IPv6 addresses with the input being in list format
    Args: firstAddressList - The first ipv6 address in list format
          secondAddressList - The second ipv6 address in list format
    Return: The sum of the two ipv6 addresses
    '''
    ipv6AddrSumList = [0, 0, 0, 0, 0, 0, 0, 0]

    ipSum = 0
    carryOver = 0

    for count in range(7, -1, -1):
        ipSum = int(firstAddressList[count]) + int(secondAddressList[count]) + carryOver
        ipv6AddrSumList[count] = ipSum % 65536
        carryOver = ipSum / 65536

    return ipv6AddrSumList


def SubIpv6Addr(firstAddressList, secondAddressList):
    '''
    Desc: Adds two IPv6 addresses with the input being in list format
    Args: firstAddressList - The first ipv6 address in list format
          secondAddressList - The second ipv6 address in list format
    Return: The diff of the two ipv6 addresses

    TODO: Verify that the carryOver is negative and that adding it back
          in is correct.
    '''
    ipv6AddrSumList = [0, 0, 0, 0, 0, 0, 0, 0]

    ipSum = 0
    carryOver = 0

    for count in range(7, -1, -1):
        ipSum = int(firstAddressList[count]) - int(secondAddressList[count]) + carryOver
        ipv6AddrSumList[count] = ipSum % 65536
        carryOver = ipSum / 65536

    return ipv6AddrSumList


def GetNextVlan(baseVlan, vlanStep):
    '''
    Desc: Computes and returns the next Vlan.
    '''
    return(baseVlan + vlanStep)


def GetNextOverlayId(baseOverlayId, baseOverlayStep):
    '''
    Desc: Computes and returns the next overlay Id.
    '''
    return(baseOverlayId + baseOverlayStep)


if __name__ == "__main__":
    # Main function for testing individual utilities
    print(GetNextIPAddress("192.168.1.1", '0.0.0.1', 1, 1))

    print(GetNextIPAddress("2001::1", 2, 1, 64))

    print(GetNextIPAddress("192.168.1.1", 1, 1, 32))

    print(GetNextMacAddress("00:00:00:00:00:04", 48, 1, 3))

    print(GetNextMacAddress("00:00:00:00:00:04", 48, 1, 3))
