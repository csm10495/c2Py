'''
Brief:
    c2Py.py - A script to convert C-Structures to Python ctypes

Author(s):
    Charles Machalow - MIT License
'''

import argparse
import collections
import os
import re
import time

from pprint import pprint

# Matching braces finders
REGEX_STRUCT_1 = re.compile(r'typedef\s*struct\s*(\w*)\s*{', re.DOTALL | re.MULTILINE)
REGEX_STRUCT_2 = re.compile(r'struct\s*(\w*)\s*{', re.DOTALL | re.MULTILINE)
REGEX_STRUCT_LIST = [REGEX_STRUCT_1, REGEX_STRUCT_2]

REGEX_ARRAY = re.compile(r'\[(\w*)\]')

REGEX_ALIAS_1 = re.compile(r'typedef\s*(.*);')
REGEX_ALIAS_2 = re.compile(r'#define\s*(.*)')
REGEX_ALIAS_LIST = [REGEX_ALIAS_1, REGEX_ALIAS_2]

def printDict(d):
    '''
    Brief:
        prints a dictionary in a sort of pretty way
    '''
    for i in d:
        print(i + ":")
        print(d[i])
        print("")

def typeToCtypeLine(theTypeStr, aliases):
    '''
    Brief:
        Returns a string of a ctype/struct item declaration from a line of C-Structure declaration.
    '''
    theTypeStr = replaceAliases(aliases=aliases, fileText=theTypeStr)
    theTypeStr = theTypeStr.replace(';', '').strip()
    if ':' in theTypeStr:
        # bitField
        bitField = theTypeStr.split(':')[1].strip()
        theTypeStr = theTypeStr.split(':')[0].strip()
        array = False
    elif '[' in theTypeStr:
        # array
        array = ' * '.join(re.findall(REGEX_ARRAY, theTypeStr))
        bitField = False
    else:
        # not bit field or array
        bitField = False
        array = False

    theName = theTypeStr.split()[-1].split("[")[0].strip()
    theTypeStr = ' '.join(theTypeStr.split()[:-1])

    if theTypeStr == 'bool':
        cType = 'c_bool'
    elif theTypeStr == 'int':
        cType = 'c_int'
    elif theTypeStr == 'long':
        cType = 'c_long'
    elif theTypeStr == 'longlong':
        cType = 'c_longlong'
    elif theTypeStr == 'unsigned int':
        cType = 'c_uint'
    elif theTypeStr == 'unsigned long':
        cType = 'c_ulong'
    elif theTypeStr == 'unsigned longlong':
        cType = 'c_ulonglong'
    elif theTypeStr == 'char':
        cType = 'c_char'
    elif theTypeStr == 'int8_t':
        cType = 'c_int8'
    elif theTypeStr == 'int16_t':
        cType = 'c_int16'
    elif theTypeStr == 'int32_t':
        cType = 'c_int32'
    elif theTypeStr == 'int64_t':
        cType = 'c_int64'
    elif theTypeStr == 'uint8_t':
        cType = 'c_uint8'
    elif theTypeStr == 'uint16_t':
        cType = 'c_uint16'
    elif theTypeStr == 'uint32_t':
        cType = 'c_uint32'
    elif theTypeStr == 'uint64_t':
        cType = 'c_uint64'
    elif theTypeStr == 'ubyte':
        cType = 'c_ubyte'
    elif theTypeStr == 'byte':
        cType = 'c_byte'
    elif theTypeStr == 'float':
        cType = 'c_float'
    elif theTypeStr == 'double':
        cType = 'c_double'
    elif theTypeStr == 'short':
        cType = 'c_short'
    elif theTypeStr == 'unsigned short':
        cType = 'c_ushort'
    elif theTypeStr == 'size_t':
        cType = 'c_size_t'
    elif theTypeStr == 'ssize_t':
        cType = 'c_ssize_t'
    elif theTypeStr == 'long double':
        cType = 'c_longdouble'
    elif theTypeStr == 'unsigned char':
        cType = 'c_ubyte'
    else:
        # Todo: look for type above this line in the source
        raise Exception("Unknown type given: %s" % theTypeStr)

    if bitField is not False:
        cType = '%s, %s' % (cType, bitField) 
    elif array is not False:
        cType = '%s * %s' % (cType, array)

    fullLine = "('%s', %s)," % (theName, cType)
    return fullLine

def removeComments(fileText):
    '''
    Brief:
        Removes the comments from a file
    '''
    # TODO
    return fileText

def getAnonName():
    '''
    Brief:
        Gets a anon-safe name for a struct
    '''
    return '_Anon_%s' % str(time.time()).replace('.', '_')

def findStructures(fileLocation=None, fileText=None):
    '''
    Brief:
        Returns a dictionary of name to text for structures directly in the given file or text
    '''
    fileText = _getFileText(fileLocation, fileText)

    # remove comments
    fileText = removeComments(fileText)

    structuresAsText = {} # Name to implementation

    for regex in REGEX_STRUCT_LIST:
        for match in regex.finditer(fileText):
            startIndex = match.start()
            structName = match.groups()[0].strip()
            structText = ""
            if len(structName) == 0:
                structName = getAnonName()

            if structName in structuresAsText:
                raise Exception("Structure with name: %s is already in structuresAsText!" % structName)

            braceCount = 0
            breakOnSemicolonAnd0BraceCount = False
            for idx in range(startIndex, len(fileText)):
                if fileText[idx] == "{":
                    if braceCount == 0:
                        breakOnSemicolonAnd0BraceCount = True
                    braceCount += 1
                elif fileText[idx] == "}":
                    braceCount -= 1

                if breakOnSemicolonAnd0BraceCount and braceCount == 0:
                    for idx in range(idx, len(fileText)):
                        if fileText[idx] == ';':
                            structText = fileText[startIndex:idx + 1]
                            break
                    break

            structuresAsText[structName] = structText

            # Remove this structText from the file to not duplicate, though keep the same text length
            fileText = fileText.replace(structText, " " * len(structText))

    return structuresAsText

def cStructHeaderToPy(headerLine, nameOverride=None):
    '''
    Brief:
        Converts a header line of a struct to ctypes. Also includes the _pack_ and _fields_. 
            Includes % modifier to input fields
                If nameOverride is given, use this as the name instead of looking in the struct for it
    '''
    if nameOverride:
        name = nameOverride
    else:
        name = headerLine.replace('typedef', '').replace("{", "").replace("struct", "").strip()

    # TODO : what if it isn't pack 1?
    headerPy = 'class %s(Structure):\n    _pack_ = 1\n    _fields_ = [\n%%s    ]' % name
    return headerPy

def cStructToPy(fileText, aliases, nameOverride=None):
    '''
    Brief:
        Converts the given struct text to a python ctype struct text
            If nameOverride is given, use this as the name instead of looking in the struct for it
    '''
    fileTextLines = fileText.replace(';','').splitlines()
    firstLine = fileTextLines[0]
    lastLine = fileTextLines[-1]
    structFields = map(str.strip, fileTextLines[1:-1])
    cStructText = cStructHeaderToPy(firstLine, nameOverride)
    fieldText = ""
    for fieldLine in structFields:
        fieldText += ' ' * 8 + typeToCtypeLine(fieldLine, aliases) + "\n"

    return cStructText % fieldText

def _getFileText(fileLocation=None, fileText=None):
    '''
    Brief:
        Helper to get fileText from fileLocation or fileText
    '''
    if fileText is None and fileLocation is None:
        raise Exception("fileLocation and fileText cannot both be None")

    if fileText is not None and fileLocation is not None:
        raise Exception("Do not provide both fileLocation and fileText")

    if fileLocation:
        if not os.path.isfile(fileLocation):
            raise Exception("file not found: %s" % fileLocation)
            return False

        with open(fileLocation, 'r') as f:
            fileText = f.read()
    return fileText

def getTypeAliases(fileLocation=None, fileText=None):
    '''
    Brief:
        Searches the file text looking for aliases
            Looks for typedefs and #defines
    '''
    fileText = _getFileText(fileLocation, fileText)

    # this becomes that
    aliases = collections.OrderedDict()
    for regex in REGEX_ALIAS_LIST:
        for matchText in regex.findall(fileText):
            # typedefs are opposite the order of #defines
            flipOrder = regex.pattern.startswith('typedef')
            matchTextSplit = matchText.split()
            if flipOrder:
                aliases[matchTextSplit[-1]] = ' '.join(matchTextSplit[:-1])
            else:
                aliases[matchTextSplit[0]] = ' '.join(matchTextSplit[1:])

    return aliases

def replaceAliases(aliases, fileLocation=None, fileText=None):
    '''
    Brief:
        Replaces known aliases and returns the updated fileText
    '''
    fileText = _getFileText(fileLocation, fileText)
    for key, value in aliases.items():
        fileText = fileText.replace(key, value)

    return fileText

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="File to try to convert the given structures to ctypes", required=True)
    parser.add_argument("-d", "--debug", help="Debug flag", action='store_true')
    args = parser.parse_args()

    aliases = getTypeAliases(fileLocation=args.file)
    structuresAsText = findStructures(fileLocation=args.file)
    if not structuresAsText:
        sys.exit(1)

    for key, value in structuresAsText.items():
        print (key)
        print (value)
        print (cStructToPy(fileText=value, nameOverride=key, aliases=aliases))
        print ("-" * 40)





