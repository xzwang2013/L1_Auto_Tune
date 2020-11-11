# from StcIntPythonPL import *
import sys
import copy
import os
import stat

# global logger
# logger = PLLogger.GetLogger('spirent.Core.Utils.Topology')


# For printing entry/exit logs for each function, uncomment the logger statement
def printInfo(string):
    # logger.LogInfo(string)
    pass


def printWarn(string):
    # logger.LogWarn(string)
    pass


def printErr(string):
    # logger.LogError(string)
    pass


class TopologyNode:
    '''
        A class which represents a node in the STC Wizard preview object tree
    '''

    def __init__(self, name, classId, parent, properties, secondaryId=""):
        self.__displayName = name            # Editable by the user
        self.__internalName = name           # Internal and not editable by the user
        self.__classId = classId             # Datamodel class
        self.__secondaryId = secondaryId     # Tag value : P, PE, Host etc. ( to be renamed as __tag )
        self.__propertiesDict = properties   # A list of property elements ( eg: [hostInfo{}, ifInfo{}] )
        self.__parentObj = parent
        self.__relationshipsList = []        # A List of relationship elements --- {Type,Direction,OtherEndpt}
        self.__childrenList = []             # A list of children (TopologyNodes)

    def GetDisplayName(self):
        return self.__displayName

    def SetDisplayName(self, name):
        self.__displayName = name

    def GetInternalName(self):
        return self.__internalName

    def GetClassId(self):
        return self.__classId

    def GetSecondaryId(self):
        return self.__secondaryId

    def SetSecondaryId(self, secId):
        self.__secondaryId = secId

    def GetParentObj(self):
        return self.__parentObj

    def GetChildrenList(self):
        return self.__childrenList

    def AddRelationship(self, relType, direction, OtherEndpoint):
        '''
        Desc: Adds a relationship between the calling object and another existing node object in the tree.
        type: The relation type -- string ( Eg. ParentChild )
        direction: Forward/Reverse (String)
        OtherEndpoint: An object reference to the other endpoint
        '''
        relationshipObj = {}
        relationshipObj['type'] = relType
        relationshipObj['direction'] = direction
        relationshipObj['OtherEndPt'] = OtherEndpoint
        self.__relationshipsList.append(relationshipObj)

    def GetRelationshipByType(self, type):
        '''
        Desc: Retrieve a dictionary with the relationships of a certain type for this node
        Args: type: Type of relationship (E.g. ParentChild)
        '''
        relationshipsList = []
        for relationshipObj in self.__relationshipsList:
            if relationshipObj['type'] == type:
                relationshipsList.append(relationshipObj)
        return relationshipsList

    def GetAllRelationships(self):
        '''
        Desc: Retrieve a dictionary with all the relationships for this node
        '''
        return self.__relationshipsList

    def PrintRelationships(self, fileHandle):
        fileHandle.write("\nRelationships for: " + str(self.GetDisplayName()))
        for relObj in self.__relationshipsList:
            fileHandle.write("\n    Dest Endpt: " + str(relObj['OtherEndPt'].GetDisplayName()))
            fileHandle.write("\n    Type: " + str(relObj['type']))
            fileHandle.write("\n    Direction: " + str(relObj['direction']) + "\n")

    def GetPropertiesDict(self):
        return self.__propertiesDict

    def SetObjectProperties(self, propertiesDict):
        self.__propertiesDict = propertiesDict

    def GetProperty(self, propertyName):
        if propertyName in self.__propertiesDict:
            return self.__propertiesDict[propertyName]
        return None

    def SetProperty(self, propertyName, propertyValue):
        self.__propertiesDict[propertyName] = propertyValue

    def RemoveProperty(self, propertyName):
        '''
        Desc: Removes a property for this node from the set of properties defined for this node.
              This is useful when we need to store values during creation of the tree.
              We may not need to show these values to the user though.
        Args: propertyName - Name of the property to be deleted
        Return: True/False
        '''
        if propertyName in self.__propertiesDict:
            del self.__propertiesDict[propertyName]
            return True
        return False

    def AddChildNode(self, child):
        '''
        Desc: Adds a child node and sets relationships
        '''
        self.AddRelationship('ParentChild', 'Forward', child)
        child.AddRelationship('ParentChild', 'Reverse', self)
        self.__childrenList.append(child)

    def CloneNodeContents(self, newParent, newName="", recursive=True):
        '''
        Desc: Clones the node and any subnodes that it may have.
        Args: newParent - The parent node under which we need to put the clone
              recursive - Whether to recursively clone the children of this node as well
        '''
        printInfo('Entering CloneNodeContents() -- ' + self.GetInternalName() + ' node')
        if self.GetSecondaryId() == 'root':
            printErr('Cannot clone the root node')
            return None

        if newName is "":
            newName = self.GetInternalName()

        newNode = TopologyNode(newName, self.GetClassId(), newParent, copy.deepcopy(self.GetPropertiesDict()), self.GetSecondaryId())
        self.CloneRelationships(newNode)
        newParent.AddChildNode(newNode)

        if recursive is True:
            childrenList = self.GetChildrenList()
            for elem in childrenList:
                elem.CloneNodeContents(newNode)
        printInfo('Exiting CloneNodeContents() -- ' + self.GetInternalName() + ' node')
        return newNode

    def CloneRelationships(self, newNode):
        '''
        Desc: Creates a copy of the relationships for the current object and assigns them to the new object
        '''
        origRel = self.__relationshipsList
        for relObj in origRel:
            if relObj['type'] != 'ParentChild':
                relCopy = copy.copy(relObj)
                newNode.__relationshipsList.append(relCopy)

    def DumpNodeContents(self, fileName=''):
        '''
        Desc: The function takes care of dumping contents of this node only.
        Args: fileName - name of the file to print the contents to.
        Return: Nothing
        '''
        if fileName == "":
            fileHandle = open('PreviewNodeContents.txt', 'w')
            self.GetTopologySummary(fileHandle, False)
            fileHandle.close()

    def GetTopologySummary(self, fileHandle, recursive=True):
        '''
        Desc: Prints its own summary and/or prints its children as well.
        Args: fileHandle: The file object handle for dumping the contents of the node/tree
              recursive: Whether to recursively print the tree below the node (True/False)
                         - False: Print the contents of this node only
                         - True: Print the contents of this node and recursively print the contents of its children.
        '''
        if fileHandle != "":
            fileHandle.write("\n----------------------------")
            fileHandle.write("\n\nName: " + str(self.__displayName))
            fileHandle.write("\nClassId: " + str(self.__classId))
            fileHandle.write("\nSecondary Id: " + str(self.__secondaryId))
            if self.__classId != "project":
                fileHandle.write("\nParent: " + str(self.__parentObj.GetDisplayName()))

            fileHandle.write("\nChild nodes: ")
            if len(self.__childrenList) == 0:
                fileHandle.write("None")
            for child in self.__childrenList:
                fileHandle.write("\n  - " + str(child.GetDisplayName()))

            fileHandle.write("\nProperties:")
            for key, value in self.__propertiesDict.iteritems():
                if type(value) is dict:
                    fileHandle.write("\n    " + str(key) + ":")
                    for childKey, childVal in value.iteritems():
                        fileHandle.write("\n        " + str(childKey) + ":" + str(childVal))
                else:
                    fileHandle.write("\n    " + str(key) + ":" + str(value))
            self.PrintRelationships(fileHandle)

            if recursive is True:
                for child in self.__childrenList:
                    child.GetTopologySummary(fileHandle)


class TopologyTree:
    '''
    Desc: A class which represents a tree of preview node objects
    '''

    def __init__(self):
        '''
        Desc: The init method.
              Creates a brand new tree with a root node and returns the node
        Args: None
        Return: Node object
        '''
        self.__rootNode = TopologyNode("Project", "project", None, {}, 'root')
        print self.__rootNode.GetDisplayName()

    def GetRootNode(self):
        if self.__rootNode is None:
            self.__rootNode = TopologyNode()
        return self.__rootNode

    def AddTopologyNode(self, name, classId, parent, properties, secondaryId=""):
        '''
        Desc: Adds a new node object to the tree.
        '''
        newNode = TopologyNode(name, classId, parent, properties, secondaryId)
        if parent is not None:
            parent.AddChildNode(newNode)                            # Add the node as a child to 'parent'

        return newNode

    def AddRelationshipTwoWay(self, nodeA, nodeB, type, direction):
        '''
        Desc: Adds a relationship link between nodeA and nodeB
              This will take care of adding the relationship in both directions
        '''
        if direction == 'Forward':
            nodeA.AddRelationship(type, 'Forward', nodeB)
            nodeB.AddRelationship(type, 'Reverse', nodeA)
        elif direction == 'Reverse':
            nodeA.AddRelationship(type, 'Reverse', nodeB)
            nodeB.AddRelationship(type, 'Forward', nodeA)
        else:
            printErr('Incorrect direction: ' + direction)

    def CloneSubTree(self, treeNode):
        return treeNode.CloneNodeContents()

    def GetTopologySummary(self, fileName=""):
        '''
        Desc: Writes the preview summary for this tree to a file
        Args: Takes a file handle
        '''
        if fileName != "":
            try:
                fileHandle = open(fileName, 'w+')
                os.chmod(fileName, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
                fileHandle.write("STC Wizard Preview Tree:")
                self.__rootNode.GetTopologySummary(fileHandle)
            except IOError:
                return "error"
            fileHandle.close()
        return


if __name__ == "__main__":

    # Here we create a tree node.
    tree = TopologyTree()
    root = tree.GetRootNode()
    print "Name:" + root.GetDisplayName()

    obj1 = tree.AddTopologyNode('Child1', 'Router', root, {'prop1': 'no', 'prop2': 'b'})

    obj2 = tree.AddTopologyNode('Child2', 'Router', root, {'prop1': 'no', 'prop2': 'b'})
    tree.AddRelationshipTwoWay(obj1, obj2, 'SampleRelationship', 'Forward')
    tree.AddTopologyNode('Child3', 'Router', obj1, {'prop1': 'no', 'prop2': 'b'})
    tree.AddTopologyNode('Child4', 'Router', obj2, {'prop1': 'no', 'prop2': 'b'})

    obj3 = obj1.CloneNodeContents(obj1.GetParentObj(), 'child5', True)
    propDict = obj3.SetProperty('prop1', 'yes')

    root.GetTopologySummary(sys.stdout)

    obj1.DumpNodeContents()

    tree.GetTopologySummary('PreviewFile.txt')
