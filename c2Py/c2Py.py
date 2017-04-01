'''
Brief:
    c2Py.py - A script to convert C-Structures to Python ctypes

Author(s):
    Charles Machalow - MIT License
'''

import argparse
import os
import re

from pprint import pprint

# Matching braces finders
REGEX_STRUCT_1 = re.compile(r'typedef\s*struct\s*(\w*)\s*{', re.DOTALL | re.MULTILINE)
REGEX_STRUCT_2 = re.compile(r'struct\s*(\w*)\s*{', re.DOTALL | re.MULTILINE)
REGEX_STRUCT_LIST = [REGEX_STRUCT_1, REGEX_STRUCT_2]

REGEX_ARRAY = re.compile(r'\[(\w*)\]')

def printDict(d):
    '''
    Brief:
        prints a dictionary in a sort of pretty way
    '''
    for i in d:
        print(i + ":")
        print(d[i])
        print("")

def typeToCtypeLine(theTypeStr):
    '''
    Returns a string of a ctype/struct item declaration from a line of C-Structure declaration.
    '''
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

def findStructures(fileLocation=None, fileText=None):
    '''
    Brief:
        Returns a dictionary of name to text for structures directly in the given file or text
    '''
    if fileText is None and fileLocation is None:
        raise Exception("fileLocation and fileText cannot both be None")

    if fileText is not None and fileLocation is not None:
        raise Exception("Do not provide both fileLocation and fileText")

    if fileLocation:
        if not os.path.isfile(fileLocation):
            print ("file not found: %s" % fileLocation)
            return False

        with open(fileLocation, 'r') as f:
            fileText = f.read()

    # remove comments
    fileText = removeComments(fileText)

    structuresAsText = {} # Name to implementation

    for regex in REGEX_STRUCT_LIST:
        for match in regex.finditer(fileText):
            startIndex = match.start()
            structName = match.groups()[0]

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

            # Remove this structText from the file to not duplicate
            fileText = fileText.replace(structText, "")

    return structuresAsText

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="File to try to convert the given structures to ctypes", required=True)
    parser.add_argument("-d", "--debug", help="Debug flag", action='store_true')
    args = parser.parse_args()

    structuresAsText = findStructures(fileLocation=args.file)
    if not structuresAsText:
        sys.exit(1)

    if args.debug:
        printDict(structuresAsText)

        for i in structuresAsText:
            for line in structuresAsText[i].splitlines():
                try:
                    print (typeToCtypeLine(line))
                except Exception as ex:
                    pass





