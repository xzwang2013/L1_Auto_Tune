from StcIntPythonPL import *

global logger
logger = PLLogger.GetLogger('spirent.core.utils.WizardDMTranslator')

# List of properties that need to be filtered -- enhancements to be added.
childClassList = ['VpnMplsRsvpSessionParams', 'BgpSrSessionParams', 'BgpSrGlobalConfig', 'BgpSrGlobalBlock', 'BgpAuthenticationParams', 'VpnMplsLdpSessionParams', 'VpnIgpOspfv2SessionParams', 'VpnIgpIsisSessionParams', 'VpnEvpnGenCustPortParams', 'VpnEvpnGenCorePortParams', 'VpnMplsLdpP2mpSessionParams', 'VpnMplsRsvpTeP2mpSessionParams',
                  'RtgTestGenIpv4PortParams', 'RtgTestGenIpv6PortParams', 'LdpAuthenticationParams', 'EvpnMplsMcastConfigParams', 'Ospfv2AuthenticationParams', 'IsisAuthenticationParams', 'EvpnMplsConfigGenParams',
                  'EvpnMplsProviderPortGenParams', 'EvpnMplsProviderRouterGenParams', 'EvpnMplsRouteGenParams', 'EvpnMplsEviParams', 'EvpnMplsHostBehindPeGenParams', 'EvpnMplsCustPortGenParams']


# -----------BASIC UTILITIES-------------------
def GetObjectFromHandle(Scriptablehandle):
    handleReg = CHandleRegistry.Instance()
    return(handleReg.Find(Scriptablehandle))


def GetDataModelObjectProperties(DataModelObject):
    '''
    Desc: The function returns a list of properties for the class specified
    Args: className, object
    Returns: A list of the properties for the object of class 'className'
    '''
    className = DataModelObject.Get('Name').split(" ")[0]

    # Create a command for retrieving the property names for this class
    ctor = CScriptableCreator()
    cmd = ctor.CreateCommand('GetPropertyTypeMetaInfoCommand')
    cmd.Set('ClassName', className)
    cmd.Execute()
    PropertyNames = cmd.GetCollection('PropertyNames')
    # Retrieve the value for each property name by querying the object passed in.
    propDict = {}
    for i in range(0, len(PropertyNames)):
        meta = CMeta.GetPropertyMeta(className, PropertyNames[i])
        if meta.get('isCollection'):
            propDict[PropertyNames[i]] = DataModelObject.GetCollection(PropertyNames[i])
        else:
            propDict[PropertyNames[i]] = DataModelObject.Get(PropertyNames[i])

    propDict['handle'] = DataModelObject.GetObjectHandle()
    return propDict


# -----------/BASIC UTILITIES------------------
def ExtractObjectContents(WizardGenParamsObj):
    '''
    Desc: This function is responsible for coverting the contents of the WizardGenParams
    object that is given as input into a list of properties and objects that can be parsed
    over by the preview object model creator function for the appropriate datamodel class.
    '''
    # WizardGenParamsObj = GetObjectFromHandle(WizardGenParams)

    # Extract the properties for this object and append them to the existing list of properties
    propertiesDict = GetDataModelObjectProperties(WizardGenParamsObj)
    # ########## IN THE FUTURE , THIS LIST WOULD BE RETRIEVED THROUGH A COMMAND LIKE GETCHILDREN() ################# -- Barry would be adding an enhancement for this soon.
    # Extract properties for the child objects

    # Go through all the child objects under the current object, extract its properties and send them to the appropriate Tree Creator class.
    childrenPropertiesList = []

    for className in childClassList:
        childObjectsForClassname = WizardGenParamsObj.GetObjects(className, RelationType('ParentChild'))
        for childObj in childObjectsForClassname:
            if childObj.Get('Active') is True:
                childPropDict = ExtractObjectContents(childObj)
                childrenPropertiesList.append(childPropDict)

    propertiesDict['children'] = childrenPropertiesList
    return propertiesDict
