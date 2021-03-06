
import hou

# import fee_HDA

# from importlib import reload
# reload(fee_HDA)


def isUnlockedHDA(node):
    return not node.isLockedHDA() and node.type().definition() is not None


def isFeENode(nodeType, detectName = True, detectPath = False):
    if detectName:
        if not nodeType.nameComponents()[2].endswith("_fee") or not nodeType.description().startswith("FeE"):
            return False
    if detectPath:
        defi = nodeType.definition()
        if defi is None:
            libraryFilePath = 'None'
        else:
            libraryFilePath = defi.libraryFilePath()
        pathFeELib = hou.getenv('FeELib')
        pathFeEProject = hou.getenv('FeEProjectHoudini')
        pathFeEmiHoYo = hou.getenv('FeEmiHoYo')
        if not (pathFeELib in libraryFilePath or pathFeEProject in libraryFilePath or pathFeEmiHoYo in libraryFilePath):
            return False
    
    return True



def copyParms_NodetoNode(sourceNode, targetNode):
    origParmTemplateGroup = sourceNode.parmTemplateGroup()
    if 0:
        targetNode.setParmTemplateGroup(origParmTemplateGroup, rename_conflicting_parms=False)
    else:
        try:
            targetNode.setParmTemplateGroup(origParmTemplateGroup, rename_conflicting_parms=False)
        except:
            '''Parameters don't support MinMax, MaxMin, StartEnd, BeginEnd, or XYWH parmNamingSchemes'''
            print(sourceNode, targetNode)
            print(origParmTemplateGroup.asDialogScript())
        
    for parm in sourceNode.parms():
        if parm.parmTemplate().type() == hou.parmTemplateType.Folder:
            try:
                parmVal = parm.evalAsInt()
                #print(parmVal)
                #print(parm.multiParmStartOffset())
                parentFolder = targetNode.parm(parm.name())
                #parentFolder.setFromParm(parm)
                for idx in range(0, parentFolder.evalAsInt()):
                    parentFolder.removeMultiParmInstance(0)
                for idx in range(0, parmVal):
                    parentFolder.insertMultiParmInstance(idx)
            except:
                print('')
                #print(targetNode)
                print(parm)
                
    if 0:
        for parm in targetNode.parms():
            if parm.isMultiParmInstance():
                print(parm)

    for parm in sourceNode.parms():
        #break
        try:
            targetparm = targetNode.parm(parm.name())
            targetparm.deleteAllKeyframes()
            targetparm.setFromParm(parm)
        except:
            #print(targetNode)
            print(targetNode.parm(parm.name()))
            #print(parm)
    

def bake_optypeExp_to_str(targetNode, sourceNode, optype_exp, optype_exp1):
    relativePathTo = targetNode.relativePathTo(sourceNode)
    str_optype0 = r"optype('" + relativePathTo + r"/.')" # r"optype('../.')"
    str_optype1 = r"optype('" + relativePathTo + r"')" # r"optype('..')"
    str_py_optype0 = r"hou.node('" + relativePathTo + r"/.').type().nameComponents()[2]" # r"hou.node('../.').type().nameComponents()[2]"
    str_py_optype1 = r"hou.node('" + relativePathTo + r"').type().nameComponents()[2]" # r"hou.node('..').type().nameComponents()[2]"
    #print(str_py_optype0)

    parms = targetNode.parms()
    for parm in parms:
        rawValue = parm.rawValue()
        try:
            expLang = parm.expressionLanguage()
        except:
            #没有exp
            if parm.parmTemplate().dataType() == hou.parmData.String:
                #是string类型
                if r'`' + str_optype0 + r'`' in rawValue:
                    rawValue = rawValue.replace(r'`' + str_optype0 + r'`', optype_exp)
                    parm.set(rawValue)
                if r'`' + str_optype1 + r'`' in rawValue:
                    rawValue = rawValue.replace(r'`' + str_optype1 + r'`', optype_exp)
                    parm.set(rawValue)
                if str_optype0 in rawValue:
                    rawValue = rawValue.replace(str_optype0, optype_exp1)
                    parm.set(rawValue)
                if str_optype1 in rawValue:
                    rawValue = rawValue.replace(str_optype1, optype_exp1)
                    parm.set(rawValue)
        else:
            #有exp
            if expLang == hou.exprLanguage.Python:
                if str_py_optype0 in rawValue:
                    rawValue = rawValue.replace(str_py_optype0, optype_exp1)
                    parm.deleteAllKeyframes()
                    parm.setExpression(rawValue, hou.exprLanguage.Python, True)
                if str_py_optype1 in rawValue:
                    rawValue = rawValue.replace(str_py_optype1, optype_exp1)
                    parm.deleteAllKeyframes()
                    parm.setExpression(rawValue, hou.exprLanguage.Python, True)

            elif expLang == hou.exprLanguage.Hscript:
                if str_optype0 in rawValue:
                    rawValue = rawValue.replace(str_optype0, optype_exp1)
                    parm.deleteAllKeyframes()
                    parm.setExpression(rawValue, hou.exprLanguage.Hscript, True)
                if str_optype1 in rawValue:
                    rawValue = rawValue.replace(str_optype1, optype_exp1)
                    parm.deleteAllKeyframes()
                    parm.setExpression(rawValue, hou.exprLanguage.Hscript, True)



def convertSubnet(node, ignoreUnlock = False, Only_FeEHDA = True, ignore_SideFX_HDA = True, detectName = True, detectPath = False):
    nodeType = node.type()
    
    ##### 检测各种情况
    if nodeType.name() == 'subnet':
        convertSubnet_recurseSubChild(node, node, '', ignoreUnlock, Only_FeEHDA, ignore_SideFX_HDA)

    definition = nodeType.definition()
    if definition is None:
        return

    if not ignoreUnlock and not node.matchesCurrentDefinition():
        #print(node)
        convertSubnet_recurseSubChild(node, node, '', ignoreUnlock, Only_FeEHDA)
        return
    
    if Only_FeEHDA:
        if not isFeENode(nodeType, detectName, detectPath):
            return

    if ignore_SideFX_HDA:
        defaultLibPath = hou.getenv('HFS') + r'/houdini/otls/'
        if definition.libraryFilePath().startswith(defaultLibPath):
            convertSubnet_recurseSubChild(node, node, '', ignoreUnlock, Only_FeEHDA)
            return

    node.allowEditingOfContents()

    ##### 记录flag情况
    parent = node.parent()
    #print(parent.childTypeCategory().name())
    if parent.childTypeCategory().name() != 'Sop':
        raise('error')
    if node.isHardLocked():
        raise('isHardLocked')
    if node.isSoftLocked():
        raise('isSoftLocked')
    
    displayFlag = node == parent.displayNode()
    renderFlag = node == parent.renderNode()
    bypass = node.isBypassed()
    isTemplateFlagSet = node.isTemplateFlagSet()
    isHighlightFlagSet = node.isHighlightFlagSet()
    isSelectableTemplateFlagSet = node.isSelectableTemplateFlagSet()
    isUnloadFlagSet = node.isUnloadFlagSet()

    inputConnectors = node.inputConnectors()
    nInputs = len(inputConnectors)

    #### 处理4号以后的输入口
    if nInputs > 4:
        shiftVector2 = hou.Vector2(0.0, -1.0)
        nulls = []

        ###算出nulls列表的所有元素，后面有用
        for idx in range(4, nInputs):
            if len(inputConnectors[idx]) == 0:
                # 说明没有连
                nulls.append(None)
                continue
            
            inputConnection = inputConnectors[idx][0]
            subnetIndirectInput = inputConnection.subnetIndirectInput()

            #### 查找输入的类型
            flag = False
            if subnetIndirectInput is None:
                inputNode = inputConnection.inputNode()
                if inputNode is None:
                    ####说明输入是一个个dot，最终连接到subnet input
                    inputItem = inputConnection.inputItem()
                    while type(inputItem).__name__ == 'NetworkDot':
                        ####寻找dot的最终链接
                        inputItem = inputItem.inputItem()
                    
                    if type(inputItem).__name__ == 'SubnetIndirectInput':
                        subnetIndirectInput = inputItem
                        flag = True
                    else:
                        raise(hou.Error('fee : 不可能的情况'))
                        return 0
                        #nulls.append(inputItem)
                        #flag = False
                else:
                    ####说明输入是一个node
                    nulls.append(inputNode)
                    flag = False
            else:
                ####说明输入是一个subnet input
                flag = True
            
            #### 建立null节点
            if flag:
                null = None
                for outputConnection in subnetIndirectInput.outputConnections():
                    outputNode = outputConnection.outputNode()
                    if outputNode.type().name() == 'null':
                        if outputNode.parm('copyinput').evalAsInt() == 1:
                            null = outputNode
                            nulls.append(null)
                            break

                if null is None:
                    if 1:
                        null = subnetIndirectInput.createOutputNode('null', exact_type_name=True)
                    else:
                        null = parent.createNode('null', exact_type_name=True)
                        null.setInput(0, subnetIndirectInput, output_index=0)
                    # null.setPosition(subnetIndirectInput.position().__add__(shiftVector2))
                    null.setPosition(subnetIndirectInput.position() + shiftVector2)
                    nulls.append(null)
            
        indirectInputs = node.indirectInputs()
        for idx in range(4, nInputs):
            if nulls[idx-4] is None: #没有连
                continue
            objectMerge = node.createNode('object_merge', exact_type_name=True)
            objectMerge.parm('objpath1').set('../../' + nulls[idx-4].name() )
            objectMerge.setPosition(indirectInputs[idx].position())
            for outputConnection in indirectInputs[idx].outputConnections():
                outputNode = outputConnection.outputNode()
                outputNode.setInput(outputConnection.inputIndex(), objectMerge)


    #### 处理0-3号输入口
    inputItems = []
    inputItem_output_index = []
    for idx in range(0, min(nInputs, 4)):
        if len(inputConnectors[idx]) == 0:
            # 说明没有连
            inputItems.append(None)
            inputItem_output_index.append(None)
            continue
        inputConnection = inputConnectors[idx][0]
        inputItem = inputConnection.inputItem()
        inputItems.append(inputItem)
        #if type(inputItem).__name__ == 'NetworkDot' or type(inputItem).__name__ == 'SubnetIndirectInput':
        if isinstance(inputItem, hou.NetworkDot) or isinstance(inputItem, hou.SubnetIndirectInput):
            inputItem_output_index.append(0)
        else:
            inputItem_output_index.append(inputConnection.outputIndex())


    ############ 修改节点类型 ############
    #origNodeshape = node.userData('nodeshape')
    copyOrigNode = hou.copyNodesTo([node], parent)[0]
    newNode = node.changeNodeType('subnet', keep_parms=False)
    newNode.removeSpareParms()
    for idx in range(0, min(nInputs, 4)):
        if inputItems[idx] is not None:
            try:
                newNode.setInput(idx, inputItems[idx], inputItem_output_index[idx])
            except:
                print(newNode)
                print(inputItems[idx])
                print(inputItem_output_index[idx])
                raise(hou.Error('setInput Error'))
    # newNode.parm('label1').hide(True)
    # newNode.parm('label2').hide(True)
    # newNode.parm('label3').hide(True)
    # newNode.parm('label4').hide(True)

    oldIndirectInputs = copyOrigNode.indirectInputs()
    newIndirectInputs = newNode.indirectInputs()
    for idx in range(0, min(len(oldIndirectInputs), 4)):
        try:
            pos = oldIndirectInputs[idx].position()
            newIndirectInputs[idx].setPosition(pos)
        except:
            print(copyOrigNode)
            print(newNode)
            print(oldIndirectInputs[idx])
            print(newIndirectInputs[idx])
            raise(hou.Error('fee Error'))


    copyParms_NodetoNode(copyOrigNode, newNode)

    #if origNodeshape is not None:
        #这个是自动的啦
        #pass
        #newNode.setUserData('nodeshape', origNodeshape)
    
    newNodeParmTemplateGroup = newNode.parmTemplateGroup()
    # folder = newNodeParmTemplateGroup.findFolder('Standard')
    # folder.endsTabGroup()
    #print(folder)
    #newNodeParmTemplateGroup.hideFolder('Standard', True)
    #newNode.setParmTemplateGroup(newNodeParmTemplateGroup, rename_conflicting_parms=False)

    #newNode.removeSpareParmFolder(('Standard', ))
    #newNode.removeSpareParmTuple(newNode.parmTuple('Standard'))

    newNode.setDisplayFlag(displayFlag)
    newNode.setRenderFlag(renderFlag)
    newNode.bypass(bypass)
    newNode.setTemplateFlag(isTemplateFlagSet)
    newNode.setHighlightFlag(isHighlightFlagSet)
    newNode.setSelectableTemplateFlag(isSelectableTemplateFlagSet)
    newNode.setUnloadFlag(isUnloadFlagSet)

    optype_exp = copyOrigNode.type().nameComponents()[2]
    optype_exp1 = '\'' + optype_exp + '\''
    bake_optypeExp_to_str(newNode, newNode, optype_exp, optype_exp1)
    convertSubnet_recurseSubChild(newNode, newNode, optype_exp, ignoreUnlock, Only_FeEHDA, ignore_SideFX_HDA, detectName, detectPath)
    #print(optype_exp)

    copyOrigNode.destroy()

    



def convertSubnet_recurseSubChild(sourceNode, recurseNode, optype_exp = '', ignoreUnlock = False, Only_FeEHDA = True, ignore_SideFX_HDA = True, detectName = True, detectPath = False):
    nodeType = recurseNode.type()
    isNotSubnet = nodeType.name() != 'subnet'
    if recurseNode.matchesCurrentDefinition() and isNotSubnet:
        return
    
    if nodeType.definition() is None and isNotSubnet:
        return
    
    if optype_exp == '':
        optype_exp = sourceNode.type().nameComponents()[2]

    optype_exp1 = '\'' + optype_exp + '\''
    
    for child in recurseNode.children():
        bake_optypeExp_to_str(child, sourceNode, optype_exp, optype_exp1)

        """
        relativePathTo = child.relativePathTo(sourceNode)
        str_optype = r"optype('" + relativePathTo + r"/.')" # r"optype('../.')"
        str_py_optype = r"hou.node('" + relativePathTo + r"/.').type().nameComponents()[2]" # r"hou.node('../.').type().nameComponents()[2]"
        # print(str_py_optype)

        parms = child.parms()
        for parm in parms:
            rawValue = parm.rawValue()
            try:
                expLang = parm.expressionLanguage()
            except:
                #没有exp
                if parm.parmTemplate().dataType() == hou.parmData.String:
                    #是string类型
                    if r'`' + str_optype + r'`' in rawValue:
                        rawValue = rawValue.replace(r'`' + str_optype + r'`', optype_exp)
                        parm.set(rawValue)
                    if str_optype in rawValue:
                        rawValue = rawValue.replace(str_optype, optype_exp1)
                        parm.set(rawValue)
            else:
                #有exp
                if expLang == hou.exprLanguage.Python:
                    if str_py_optype in rawValue:
                        rawValue = rawValue.replace(str_py_optype, optype_exp1)
                        parm.deleteAllKeyframes()
                        parm.setExpression(rawValue, hou.exprLanguage.Python, True)
                elif expLang == hou.exprLanguage.Hscript:
                    if str_optype in rawValue:
                        rawValue = rawValue.replace(str_optype, optype_exp1)
                        parm.deleteAllKeyframes()
                        parm.setExpression(rawValue, hou.exprLanguage.Hscript, True)
                
                #print(rawValue)
        """

        childNodeType = child.type()
        typename = childNodeType.name()
        #if "fee" in typename.lower() and child.matchesCurrentDefinition():
        
        if typename == 'subnet':
            pass
            convertSubnet_recurseSubChild(sourceNode, child, optype_exp, ignoreUnlock, Only_FeEHDA, ignore_SideFX_HDA, detectName, detectPath)
        else:
            if Only_FeEHDA:
                if isFeENode(childNodeType, detectName, detectPath):
                    convertSubnet(child, ignoreUnlock, Only_FeEHDA, ignore_SideFX_HDA, detectName, detectPath)
                else:
                    convertSubnet_recurseSubChild(sourceNode, child, optype_exp, ignoreUnlock, Only_FeEHDA, ignore_SideFX_HDA, detectName, detectPath)
            else:
                convertSubnet(child, ignoreUnlock, Only_FeEHDA, ignore_SideFX_HDA, detectName, detectPath)



def convert_All_FeENode_to_Subnet(node, ignoreUnlock = False, ignore_SideFX_HDA = True, detectName = True, detectPath = False):
    node.allowEditingOfContents()
    for child in node.children():
        childNodeType = child.type()
        #if isFeENode(childNodeType, detectName, detectPath):
        convertSubnet(child, ignoreUnlock, Only_FeEHDA = True, ignore_SideFX_HDA = ignore_SideFX_HDA, detectName = detectName, detectPath = detectPath)


def convert_All_HDA_to_Subnet(node, ignoreUnlock = False, ignore_SideFX_HDA = True):
    node.allowEditingOfContents()
    for child in node.children():
        convertSubnet(child, ignoreUnlock, Only_FeEHDA = False, ignore_SideFX_HDA = ignore_SideFX_HDA)



def unlock_All_FeENode(node, detectName = True, detectPath = False):
    node.allowEditingOfContents()
    for child in node.children():
        childNodeType = child.type()
        if isFeENode(childNodeType, detectName, detectPath):
            # child.allowEditingOfContents()
            unlock_All_FeENode(child, detectName, detectPath)
        elif isUnlockedHDA(child):
            unlock_All_FeENode(child, detectName, detectPath)


# def unlock_All_FeENode_recurseSubChild(node, detectName = True, detectPath = False):





def findAllSubParmRawValue(subnet, strValue):
    for child in subnet.allSubChildren(recurse_in_locked_nodes=False):
        for parm in child.parms():
            if strValue in parm.rawValue():
                print(child)
                print(parm)







def extract_LockedNull(node, subPath = 'extractLockedGeo', savePath_rel_to_HIP = True, keep_name = True):
    nodetype = node.type()
    if nodetype.name() == 'null' and node.isGenericFlagSet(hou.nodeFlag.Lock):
        
        filepath = ''.join(['/', subPath, '/', node.path().lstrip('/').replace('/', '.'), '.bgeo'])

        envName = "HIP" if savePath_rel_to_HIP else "TEMP"
        filepath_abs = hou.getenv(envName) + filepath
        filepath_rel = '$' + envName + filepath
        # print(filepath_abs)
        # print(filepath_rel)
        import os
        pathDir = os.path.split(filepath_abs)[0]
        if not os.path.exists(pathDir):
            os.mkdir(pathDir)
        # print(pathDir)
        node.geometry().saveToFile(filepath_abs)

        node.setGenericFlag(hou.nodeFlag.Lock, 0)
        newnode = node.changeNodeType(new_node_type='file', keep_name = keep_name, keep_parms=False, keep_network_contents=True, force_change_on_node_type_match=True)
        newnode.setParms({"file": filepath_rel})

    elif node.isNetwork() and nodetype.category().name() == 'Sop' and not node.isLockedHDA():
        for child in node.children():
            foreverychildren(child)



def removeEmbeded(netCategories):
    dictNodeTypes = netCategories.nodeTypes()
    for nodeTypeDictsKey in dictNodeTypes:
        nodeType = dictNodeTypes[nodeTypeDictsKey]
        defi = nodeType.definition()
        if not defi:
            continue
        if defi.libraryFilePath() == 'Embedded':
            defi.destroy()


def hasEmbeded(netCategories):
    dictNodeTypes = netCategories.nodeTypes()
    for nodeTypeDictsKey in dictNodeTypes:
        secNodeType = dictNodeTypes[nodeTypeDictsKey]
        defi = secNodeType.definition()
        if not defi:
            continue
        if defi.libraryFilePath() == 'Embedded':
            return True
    return False


"""
def TABSubmenuPathfromDefi(defi):
    sections = defi.sections()
    try:
        sectionToolShelf = sections[r'Tools.shelf']
    except:
        print('not found section: Tools Shelf:', end = ' ')
        print(nodeType)
    contents = sectionToolShelf.contents()#hou.compressionType.NoCompression
    #print(contents)

    '''
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET
    '''
    import xml.etree.ElementTree as ET

    tree = ET.fromstring(str(contents))
    toolSubmenu = tree.find('tool').find('toolSubmenu').text
"""


def TABSubmenuPathfromContents(contents):
    '''
    try:
        import xml.etree.cElementTree as ET
    except ImportError:
        import xml.etree.ElementTree as ET
    '''
    import xml.etree.ElementTree as ET

    tree = ET.fromstring(str(contents))
    toolSubmenu = tree.find('tool').find('toolSubmenu').text

def TABSubmenuPathfromSectionToolShelf(sectionToolShelf):
    contents = sectionToolShelf.contents()#hou.compressionType.NoCompression
    return TABSubmenuPathfromContents(contents)


def TABSubmenuPathfromSections(sections):
    try:
        sectionToolShelf = sections[r'Tools.shelf']
        return TABSubmenuPathfromSectionToolShelf(sectionToolShelf)
    except:
        print('not found section: Tools Shelf:', end = ' ')
        print(nodeType)
        return None
    



def TABSubmenuPathfromDefi(defi):
    sections = defi.sections()
    return TABSubmenuPathfromSections(sections)

