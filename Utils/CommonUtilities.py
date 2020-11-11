from StcIntPythonPL import *
import re
from collections import defaultdict
from collections import OrderedDict
from spirent.core.utils.scriptable import AutoCommand


# All the global values that might or might not be used
logger = PLLogger.GetLogger('spirent.Core.Utils.CommonUtilities')
MAX_VLAN = 4095


def printInfo(string):
    # logger.LogInfo(string)
    pass


def printLog(string):
    # logger.LogWarn(string)
    pass


def printErr(string):
    logger.LogError(string)


def CreateProtocol(deviceDict, protoClassId):
    '''
    Desc: Returns the protocol scriptable object for a given protocol class ID on a device
    args: deviceDict : a dictonary of a device and its prop, protoClassId: the class name for the protocol config
    return: protocol -- A scriptable object
    '''
    printInfo("CreateProtocol start")
    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand('ProtocolCreateCommand')
    phndList = cmd.GetCollection('ParentList')

    # get the handle
    deviceHandle = deviceDict['m_router'].GetObjectHandle()

    if deviceDict['m_loopbackRouter']:
        phndList.append(deviceDict['m_loopbackRouter'].GetObjectHandle())
    else:
        phndList.append(deviceHandle)

    cmd.SetCollection('Parentlist', phndList)
    cmd.Set('CreateClassId', protoClassId)
    cmd.Execute()

    if len(cmd.GetCollection('ReturnList')) == 0:
        printErr('Wizard failed to create protocol object. ProtocolCreateCommand did not return any protocol objects.')
        return None

    protoHandle = cmd.GetCollection('ReturnList')[0]

    if protoHandle is None:
        printErr('Wizard failed to create protocol object. ProtocolCreateCommand returned an invalid protocol object handle.')
        return None

    hndReg = CHandleRegistry.Instance()
    protocol = hndReg.Find(protoHandle)
    printInfo('CreateProtocol end')
    return protocol


def SetIpv6If(device, ifInfo):
    '''
    Desc: Sets Ipv6 interface info on device
    args: router : a dictonary of a device and its prop, ifInfo : a dict with interface info
    return: True if the protocol is configured on the router
    '''
    printInfo("SetIpv6If Start")

    ivec = device.GetObjects('Ipv6If', RelationType('ParentChild'))
    globIpv6If = None
    localIpv6If = None
    globIpv6If = device.GetObject('Ipv6If')
    localIpv6If = device.GetObject('Ipv6If')

    if len(ivec) >= 1:
        globIpv6If = ivec[0]

    if len(ivec) >= 2:
        localIpv6If = ivec[1]

    if globIpv6If:
        globIpv6If.Set('PrefixLength', ifInfo['ipv6PrefixLength'])
        globIpv6If.Set('Address', ifInfo['ipv6Addr'])
        if 'ipv6AddrStep' in ifInfo:
            if ifInfo['ipv6AddrStep']:
                globIpv6If.Set("AddrStep", ifInfo["ipv6AddrStep"])

        if ifInfo['ipv6GatewayAddr']:
            globIpv6If.Set('Gateway', ifInfo['ipv6GatewayAddr'])
        if 'ipv6GatewayAddrStep' in ifInfo:
            if ifInfo['ipv6GatewayAddrStep']:
                globIpv6If.Set('GatewayStep', ifInfo["ipv6GatewayAddrStep"])

    if localIpv6If:
        localIpv6If.Set('PrefixLength', 128)
        localIpv6If.Set('Address', ifInfo['ipv6LinkLocalAddr'])

    printInfo('SetIpv6If End')
    return True


def SetIpv4If(device, ifInfo):
    ipv4If = device.GetObject('Ipv4If')
    if ipv4If:
        ipv4If.Set('PrefixLength', ifInfo['ipv4PrefixLength'])
        if ifInfo['ipv4Addr']:
            ipv4If.Set('Address', ifInfo['ipv4Addr'])
        else:
            ipv4If.Set('Address', '1.1.1.1')

        if 'ipv4AddrStep' in ifInfo:
            ipv4If.Set("AddrStep", ifInfo['ipv4AddrStep'])

        if ifInfo['ipv4GatewayAddr']:
            ipv4If.Set('Gateway', ifInfo['ipv4GatewayAddr'])

        if 'ipv4GatewayAddrStep' in ifInfo:
            ipv4If.Set("GatewayStep", ifInfo['ipv4GatewayAddrStep'])


def AddIpv6If(device, ipParentNi):
    '''
    Desc: Adds Ipv6 interface info on device
    args: device :a scriptable object: , ipParentNi : NetworkInterface scriptable obj
    return: True/False depending on whether the protocol gets configured on the device/router
    '''
    printInfo('AddIpv6If Start')
    if ipParentNi is None or device is None:
        return False
# New instances of Scriptables and Commands are created via the ScriptableCreator
    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand('IfStackAttachCommand')
    cmd.Set('DeviceList', device.GetObjectHandle())
    typeVec = cmd.GetCollection('IfStack')
    typeVec.append('Ipv6If')
    cntVec = cmd.GetCollection('IfCount')
    cntVec.append(1)
    cmd.SetCollection('IfStack', typeVec)
    cmd.SetCollection('IfCount', cntVec)
    cmd.Set('AttachToIf', ipParentNi.GetObjectHandle())
    cmd.Execute()
    printInfo('AddIpv6If End')
    return True


def AddIpv4If(device, ipParentNi):
    '''
    Desc: Adds Ipv4 interface info on device
    args: device :a scriptable object: , ipParentNi : NetworkInterface scriptable obj
    return: True/False depending on whether the protocol gets configured on the device/router
    '''
    printInfo("AddIpv4If Start")
    if ipParentNi is None or device is None:
        return False

    # New instances of Scriptables and Commands are created via the ScriptableCreator
    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand('IfStackAttachCommand')
    cmd.Set('DeviceList', device.GetObjectHandle())
    typeVec = cmd.GetCollection('IfStack')
    typeVec.append('Ipv4If')
    cntVec = cmd.GetCollection('IfCount')
    cntVec.append(1)
    cmd.SetCollection('IfStack', typeVec)
    cmd.SetCollection('IfCount', cntVec)
    cmd.Set('AttachToIf', ipParentNi.GetObjectHandle())

    cmd.Execute()
    printInfo("AddIpv4If end")
    return True


def CreateEmulatedDevice(testDevice, ifInfo):
    '''
    Desc: Creats a Emulated device object with the given parameters
    args: testDevice : Device dict with 'port' as key and device role and type, ifInfo : interface info
    return: the device  --- a sriptable object
    '''
    printInfo('CreateEmulatedDevice Start')
    printLog('ifInfo %s .' % ifInfo)

    intfVec = []
    project = CStcSystem.Instance().GetObject('project')
    assert(testDevice['m_port']), "Invalid port object."
    assert(testDevice['deviceType']), "Invalid device type."
    printLog("deviceType = %s, DeviceRole = %s" % (testDevice['deviceType'], testDevice['deviceRole']))

    if project is None:
        printErr('Wizard failed to create the emulated  object.  Unable to find project object.')
        return 0

    # Configure the interfaces.
    # We first add the IP interface if enabled

    subIfEnable = ifInfo['subIfEnable']

    if ifInfo['ipv6Enable'] is True:
        intfVec.append('Ipv6If')

    if ifInfo['ipv4Enable'] is True:
        intfVec.append('Ipv4If')

    # Check for the VLan Interface
    if subIfEnable:
        intfVec.append('VlanIf')
    # Finally we add the Eth If (Other Phy types are not supported right now)
    intfVec.append('EthIIIf')

    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand('DeviceCreateCommand')
    cmd.SetCollection('ParentList', [project.GetObjectHandle()])
    cmd.Set('Port', testDevice['m_port'].GetObjectHandle())

    cntVec = []
    cntVec = [1] * len(intfVec)

    cmd.SetCollection('IfStack', intfVec)
    cmd.SetCollection('IfCount', cntVec)
    cmd.Set('DeviceType', testDevice['deviceType'])
    cmd.SetCollection('DeviceRole', testDevice['deviceRole'])

    if 'DeviceCount' in ifInfo:
        cmd.Set('DeviceCount', ifInfo['DeviceCount'])

    cmd.Execute()

    if len(cmd.GetCollection('ReturnList')) == 0:
        LogError('Wizard failed to create router object. The command "DeviceCreateCommand" did not return any device objects.')
        return None
    deviceHandle = cmd.GetCollection('ReturnList')[0]

    if deviceHandle == 0:
        LogError('Wizard failed to create router object. The command "DeviceCreateCommand" returned an invalid device object handle.')
        return None

    hndReg = CHandleRegistry.Instance()
    device = hndReg.Find(deviceHandle)
    printLog("Device Name: %s" % device.Get('Name'))
    if 'SubRoleType' in ifInfo:
        name = device.Get('Name')
        device.Set('Name', name + ' ' + ifInfo['SubRoleType'])

    if ifInfo:
        ipParentNi = device.GetObject('NetworkInterface', RelationType('TopLevelIf'))
        ipParentNi = ipParentNi.GetObject('NetworkInterface', RelationType('StackedOnEndpoint'))

        ethIf = device.GetObject('EthIIIf')
        printLog('ethIf is %s.' % ethIf)

        if ethIf:
            if 'HostMacStart' in ifInfo:
                ethIf.Set('SourceMac', ifInfo['HostMacStart'])
            if 'HostMacStep' in ifInfo:
                ethIf.Set('SrcMacStep', ifInfo['HostMacStep'])

        if ifInfo['subIfEnable']:
            vlanIf = device.GetObject('VlanIf', RelationType('ParentChild'))

            if vlanIf:
                if ifInfo['vlanId'] > MAX_VLAN:
                    ifInfo['vlanId'] = ifInfo['vlanId'] % MAX_VLAN
                vlanIf.Set('VlanId', ifInfo['vlanId'])
                if 'vlanIdStep' in ifInfo:
                    vlanIf.Set('IdStep', ifInfo['vlanIdStep'])
                vlanIf.Set('IfRecycleCount', ifInfo['IfRecycleCount'])


        if ifInfo['ipv4Enable'] is True:
            SetIpv4If(device, ifInfo)

        elif ifInfo['ipv6Enable'] is True:
            AddIpv6If(device, ipParentNi)
            SetIpv6If(device, ifInfo)
            if ifInfo["dualStackEnabled"]:
                AddIpv4If(device, ipParentNi)
                SetIpv4If(device, ifInfo)

    printInfo('CreateEmulatedDevice End')
    return device


def BuildDeviceInfo(port, deviceInfo):
    '''
    Desc: Creates the router/device dict with its port and router/device Info
    args: port : a sriptable obj, deviceInfo : basic router Info
    return: a device/router dictionary
    '''

    deviceDict = {}
    printLog('deviceInfo is %s.' % deviceInfo)
    deviceName = 'Device'
    regExMatch = re.search('([a-zA-Z]+)\d+', deviceInfo['name'])
    if regExMatch:
        deviceName = regExMatch.group(1)

    deviceDict['m_port'] = port
    deviceDict['m_name'] = deviceName
    deviceDict['m_routerId'] = deviceInfo['routerId']
    if 'routerIdStep' in deviceInfo:
        deviceDict['m_routerIdStep'] = deviceInfo['routerIdStep']
    deviceDict['deviceType'] = deviceInfo['deviceType']
    deviceDict['deviceRole'] = deviceInfo['deviceRole']

    return deviceDict


def CreateDevice(port, deviceInfo, ifInfo):
    '''
    Desc: This basic utility creates the emulated device/router
    args: port : a sriptable obj, deviceInfo : basic router/device Info dict with keys (routerId,name), \
    ifInfo: interface info dict with keys
    return: a router/device dictionary
    '''
    printInfo('CreateRouter or Device Start')

    testDevice = BuildDeviceInfo(port, deviceInfo)

    if testDevice == 0:
        return testDevice

    # including the CreateRouterIf code here
    assert(testDevice), "Invalid Test Router/Device object."

    routerDevice = CreateEmulatedDevice(testDevice, ifInfo)
    printLog("testDevice['m_name'] = %s" % testDevice['m_name'])
    printLog("routerDevice.Name = %s " % routerDevice.Get('Name'))
    routerDevice.Set('Name', testDevice['m_name'] + " " + routerDevice.Get('Name'))

    if testDevice['m_routerId']:
        routerDevice.Set('RouterId', testDevice['m_routerId'])

    if 'm_routerIdStep' in testDevice:
        routerDevice.Set('RouterIdStep', testDevice['m_routerIdStep'])

    testDevice['m_router'] = routerDevice
    testDevice['m_loopbackRouter'] = routerDevice
    printInfo('CreateDevice End')

    return testDevice


def CheckDiskSpaceAvailability(PortGroupHandleList, ILPathName, RequiredSize):
    '''
    Desc: Check for space availability on IL for
    args: PortGroupHandleList : list of port group handles, ILPathName : IL path to check space,
        RequiredSize: size(bytes) required
    return: returns a dictionary containing two keys 'Success' and 'Failure'. The
            values in the dictionary are lists of port group handles for which space is
            available or not available respectively.
    '''

    if not PortGroupHandleList or not ILPathName or RequiredSize <= 0:
        return False

    # Extract the 4th field (Available) on lines other than the first
    # df command output:
    # Filesystem  1kBlocks  Used   Available  Use%  Mounted on
    dfCmd = 'df -k ' + ILPathName + " | awk '!/^Filesystem/ {print $4}'"
    logger.LogDebug('DF Cmd ' + dfCmd)
    handleReg = CHandleRegistry.Instance()
    portHandleToGroupDict = OrderedDict()
    for hnd in PortGroupHandleList:
        portGroup = handleReg.Find(hnd)
        if portGroup.IsTypeOf('PhysicalPortGroup'):
            # Get the logical port from the portGroup and add it's port handle to the
            # list of port handles that gets passed to the 'dfCmd'
            # Need to get the first online port in the port group to
            # optimize the time spent in checking space availability as
            # space available is the same for all ports in a port group
            phyPortList = portGroup.GetObjects('PhysicalPort', RelationType('ParentChild'))
            for phyPort in phyPortList:
                port = phyPort.GetObject('Port', RelationType('PhysicalLogical'))
                # If the port is not online we cannot get to the port from the physical port
                # using the "PhysicalLogical" relation type
                if port is not None:
                    portHandleToGroupDict[port.GetObjectHandle()] = hnd
                    break

    outputList = []
    with AutoCommand('GenericExecutionCommand') as cmd:
        cmd.Set('Cmd', dfCmd)
        cmd.SetCollection('PortList', portHandleToGroupDict.keys())
        cmd.Execute()
        outputList = cmd.GetCollection('OutputList')

    logger.LogDebug('OutputList')
    logger.LogDebug(str(outputList))
    retVal = defaultdict(list)

    for i, output in enumerate(outputList):
        if output == '':
            retVal['Failure'].append(portHandleToGroupDict.values()[i])
            continue
        output = output.strip()
        if not output.isdigit():
            retVal['Failure'].append(portHandleToGroupDict.values()[i])
            continue
        spaceLeft = int(output)
        logger.LogDebug('Space Left ' + str(spaceLeft))
        spaceLeft *= 1024
        # It's possible to occupy at most twice the size.
        # Also, reduce the available size by 5% just in case
        if RequiredSize * 2 <= (0.95 * spaceLeft):
            retVal['Success'].append(portHandleToGroupDict.values()[i])
        else:
            retVal['Failure'].append(portHandleToGroupDict.values()[i])

    return retVal


def GetFileListFromDir(PortRefList, ILDirectory, Recursive):
    '''
    Desc: Get file list from a IL directory
    args: portRefList : list of port handle, ILDirectory : IL dir to get files
    return: List of file names with dir if recursive
        [dir1:, file1, file2, dir2:, file3, file4,...]
    '''

    if not PortRefList or ILDirectory == '':
        raise Exception('Invalid parameters')

    # List files only from the directory in a list.
    # Adding a print helps get rid of any garbage that may be there.
    lsCmd = 'ls -1'
    if Recursive:
        lsCmd += 'R '
    lsCmd += ILDirectory + "|awk '{print}'"

    logger.LogDebug('ls Cmd ' + lsCmd)
    outputList = []
    with AutoCommand('GenericExecutionCommand') as cmd:
        cmd.Set('Cmd', lsCmd)
        cmd.SetCollection('PortList', PortRefList)
        cmd.Execute()
        outputList = cmd.GetCollection('OutputList')

    if not outputList:
        return []
    if outputList[0].startswith('ls:'):
        raise Exception('Cannot access or directory not found:' + ILDirectory)
    return outputList[0].strip().split('\n')
