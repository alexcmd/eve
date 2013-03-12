#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\carbon\staticData\schema\dataWalker.py


def DefaultContinueWalkingFunction(rootObj, obj, schemaNode, path):
    return True


def WalkOverDictionary(rootObj, obj, schema, path, continueWalkingFunction):
    retValue = continueWalkingFunction(rootObj, obj, schema, path)
    if retValue == False:
        return
    for each in obj:
        Walk(each, schema.get('keyTypes'), path + '<%s>' % each, continueWalkingFunction, rootObj)
        Walk(obj[each], schema.get('valueTypes'), path + '[%s]' % each, continueWalkingFunction, rootObj)


def WalkOverList(rootObj, obj, schema, path, continueWalkingFunction):
    retValue = continueWalkingFunction(rootObj, obj, schema, path)
    if retValue == False:
        return
    for index, each in enumerate(obj):
        Walk(each, schema.get('itemTypes'), path + '[%d]' % index, continueWalkingFunction, rootObj)


def WalkObject(rootObj, obj, schema, path, continueWalkingFunction):
    retValue = continueWalkingFunction(rootObj, obj, schema, path)
    if retValue == False:
        return
    for each in obj:
        Walk(obj[each], schema.get('attributes')[each], path + '.%s' % each, continueWalkingFunction, rootObj)


def WalkLeafNode(rootObj, obj, schema, path, continueWalkingFunction):
    continueWalkingFunction(rootObj, obj, schema, path)


builtInWalkingFunctions = {'dict': WalkOverDictionary,
 'list': WalkOverList,
 'object': WalkObject}

def Walk(obj, schemaNode, path = 'root', continueWalkingFunction = DefaultContinueWalkingFunction, rootObj = None):
    attributeType = schemaNode['type']
    if attributeType == None:
        raise 'Attribute type is not present in the schemaNode'
    if rootObj == None:
        rootObj = obj
    if attributeType in builtInWalkingFunctions:
        builtInWalkingFunctions[attributeType](rootObj, obj, schemaNode, path, continueWalkingFunction)
    else:
        WalkLeafNode(rootObj, obj, schemaNode, path, continueWalkingFunction)