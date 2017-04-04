'''
Brief:
    c2Py.py - A script to convert C-Structures to Python ctypes

Author(s):
    Charles Machalow - MIT License
'''

import argparse
import collections
import ctypes
import os
import re
import sys
import time

from pprint import pprint

# Matching braces finders
REGEX_STRUCT_1 = re.compile(r'typedef\s*(struct|union)\s*(\w*)\s*{', re.DOTALL | re.MULTILINE)
REGEX_STRUCT_2 = re.compile(r'(struct|union)\s*(\w*)\s*{', re.DOTALL | re.MULTILINE)
REGEX_STRUCT_LIST = [REGEX_STRUCT_1, REGEX_STRUCT_2]

REGEX_ARRAY = re.compile(r'\[(\w*)\]')

REGEX_ALIAS_1 = re.compile(r'typedef\s*(.*);')
REGEX_ALIAS_2 = re.compile(r'#define\s*(.*)')
REGEX_ALIAS_LIST = [REGEX_ALIAS_1, REGEX_ALIAS_2]

# Used to remove the volatile keyword in general
REGEX_VOLATILE = re.compile(r'(\s+|^)volatile\s+')

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
    
    theTypeStrLower = theTypeStr.lower() # going lower here to catch LONGLONG which isn't in wintypes for some reason

    if theTypeStrLower == 'bool':
        cType = 'c_bool'
    elif theTypeStrLower == 'int':
        cType = 'c_int'
    elif theTypeStrLower == 'long':
        cType = 'c_long'
    elif theTypeStrLower == 'longlong':
        cType = 'c_longlong'
    elif theTypeStrLower == 'unsigned int':
        cType = 'c_uint'
    elif theTypeStrLower == 'unsigned long':
        cType = 'c_ulong'
    elif theTypeStrLower == 'unsigned longlong':
        cType = 'c_ulonglong'
    elif theTypeStrLower == 'char':
        cType = 'c_char'
    elif theTypeStrLower == 'int8_t':
        cType = 'c_int8'
    elif theTypeStrLower == 'int16_t':
        cType = 'c_int16'
    elif theTypeStrLower == 'int32_t':
        cType = 'c_int32'
    elif theTypeStrLower == 'int64_t':
        cType = 'c_int64'
    elif theTypeStrLower == 'uint8_t':
        cType = 'c_uint8'
    elif theTypeStrLower == 'uint16_t':
        cType = 'c_uint16'
    elif theTypeStrLower == 'uint32_t':
        cType = 'c_uint32'
    elif theTypeStrLower == 'uint64_t':
        cType = 'c_uint64'
    elif theTypeStrLower == 'ubyte':
        cType = 'c_ubyte'
    elif theTypeStrLower == 'byte':
        cType = 'c_byte'
    elif theTypeStrLower == 'float':
        cType = 'c_float'
    elif theTypeStrLower == 'double':
        cType = 'c_double'
    elif theTypeStrLower == 'short':
        cType = 'c_short'
    elif theTypeStrLower == 'unsigned short':
        cType = 'c_ushort'
    elif theTypeStrLower == 'size_t':
        cType = 'c_size_t'
    elif theTypeStrLower == 'ssize_t':
        cType = 'c_ssize_t'
    elif theTypeStrLower == 'long double':
        cType = 'c_longdouble'
    elif theTypeStrLower == 'unsigned char':
        cType = 'c_ubyte'
    elif hasattr(ctypes.wintypes, theTypeStr.upper()): # go upper since all winapi types are caps
        cType = 'wintypes.%s' % theTypeStr
    else:
        # Todo: look for type above this line in the source
        #raise Exception("Unknown type given: %s" % theTypeStr)
        cType = theTypeStr

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

def removeVolatile(fileText):
    '''
    Brief:
        Remove useless examples of the volatile keyword
    '''
    def qual(m):
        '''
        Brief:
            Inner function to be called for each regex match to know what to do

            if it starts with \n, leave in the pre-whitespace. Otherwise, remove it.
        '''
        theMatch = m.group()
        if theMatch.startswith("\n"):
            return theMatch.split("volatile")[0]
        return " "

    fileText = re.sub(REGEX_VOLATILE, qual, fileText)
    return fileText

def removeEmptyLines(fileText):
    '''
    Brief:
        Removes empty lines from text
    '''
    # remove empty lines
    finalLines = []
    fileTextLines = fileText.splitlines()
    for i in fileTextLines:
        if i.strip() != '':
            finalLines.append(i)
    return '\n'.join(finalLines)

def _testEvalOr0(text):
    '''
    Brief:
        will attempt to eval the text to give a True/False, if we can't returns False
    '''
    try:
        return bool(eval(text))
    except:
        return False

def removePreprocessorIfs(fileText, aliases):
    '''
    Brief:
        Removes preprocessor directives (#if, #ifdef, #ifndef) from a file along with the associated code.
    '''

    # Switch '!' into 'not '
    fileTextLines = fileText.splitlines()
    # Make directive lines eval-able
    for idx, line in enumerate(fileTextLines):
        # possible directive
        if line.lstrip().startswith("#") and not [i for i in ['#include', '#define', '#undef', '#pragma', '#error', '#endif'] if i in line]:
            fileTextLines[idx] = line.replace("!", "not ")
            fileTextLines[idx] = replaceAliases(aliases, fileText=line)

            testLine = replaceAliases({"#if" : "", "#ifdef" :  "", "#ifndef" : ""}, fileText=line).strip()
            if testLine.startswith("#if "):
                bool(eval(testLine)) # This is a test to make sure we can eval this line for later.... will fail if we can't evaluate the directive. Only matters for #if

    # Try to remove code that would be removed by directives
    inFalseDirective = False # In a directive that will make code be removed
    directiveStartLine = None
    directiveCount = 0
    countToLookFor = None
    for idx, line in enumerate(fileTextLines):
        line = line.lstrip()
        if line.startswith("#i"):
            directiveCount += 1
        elif line.startswith('#endif'):
            directiveCount -= 1

        if countToLookFor == directiveCount:
            # Clear outted lines, reset markers
            for i in range(directiveStartLine, idx):
                fileTextLines[i] = "\n"
            countToLookFor = None
            directiveStartLine = None

        if line.startswith('#if ') and not inFalseDirective:
            inFalseDirective = not bool(eval(line.replace("#if", "").strip()))
        elif line.startswith('#ifdef') or line.startswith("#ifndef") and not inFalseDirective:
            ifdef = line.startswith("#ifdef") # ifndef is opposite ifdef
            items = line.replace("#ifdef", "").replace("#ifndef", "").strip().replace("||", " or ").replace("&&", " and ").split()
            replaceList = {}
            for i in items:
                if i in ['or', 'and']:
                    continue
                if i in aliases or _testEvalOr0(i):
                    replaceList[i] = "True"
                else:
                    replaceList[i] = "False"
            evalAbleItems = replaceAliases(replaceList, fileText=' '.join(items))
            if ifdef:
                inFalseDirective = not bool(eval(evalAbleItems))
            else:
                inFalseDirective = bool(eval(evalAbleItems))

        if inFalseDirective and directiveStartLine is None:
            countToLookFor = directiveCount - 1
            directiveStartLine = idx

    for idx, line in enumerate(fileTextLines):
        line = line.strip()
        if line.startswith("#i") or line.startswith("#end"):
            fileTextLines[idx] = ""

    fileText = '\n'.join(fileTextLines)
    return fileText

def getAnonName():
    '''
    Brief:
        Gets a anon-safe name for a struct
    '''
    return '_Anon_%s' % str(time.time()).replace('.', '_')

def findStructures(aliases, fileLocation=None, fileText=None):
    '''
    Brief:
        Returns a dictionary of name to text for structures directly in the given file or text
    '''
    fileText = _getFileText(fileLocation, fileText)

    # remove comments
    fileText = removeComments(fileText)
    fileText = removePreprocessorIfs(fileText, aliases)
    fileText = removeEmptyLines(fileText)
    fileText = removeVolatile(fileText)

    structuresAsText = {} # Name to implementation

    for regex in REGEX_STRUCT_LIST:
        for match in regex.finditer(fileText):
            startIndex = match.start()
            structName = match.groups()[1].strip()
            structType = match.groups()[0].strip() # union or struct
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
        name = headerLine.replace('typedef', '').replace("{", "").replace("struct", "").replace("union", "").strip()

    if 'union' in headerLine and 'struct' in headerLine:
        raise Exception("Ambiguity detected. Based off the headerLine (%s), can't tell if this is a union or struct... contains both words" % headerLine)

    if 'union' in headerLine:
        theType = 'Union'
    elif 'struct' in headerLine:
        theType = 'Structure'
    else:
        raise Exception("Ambiguity detected. Did not find struct or union in the headerLine (%s)" % headerLine)

    # TODO : what if it isn't pack 1?
    headerPy = 'class %s(%s):\n    _pack_ = 1\n    _fields_ = [\n%%s    ]\n' % (name, theType)
    return headerPy

def cStructToPy(fileText, aliases, nameOverride):
    '''
    Brief:
        Converts the given struct text to a python ctype struct text
            Requires nameOverride to give the name of the struct
    '''
    fileTextLines = fileText.replace(';','').splitlines()
    firstLine = fileTextLines[0]
    lastLine = fileTextLines[-1].replace("}", "")    # '' or 'NAME, *PNAME'
    structFields = map(str.strip, fileTextLines[1:-1])
    cStructText = cStructHeaderToPy(firstLine, nameOverride)
    fieldText = ""
    for fieldLine in structFields:
        fieldText += ' ' * 8 + typeToCtypeLine(fieldLine, aliases) + "\n"

    fullStructDefinition = cStructText % fieldText

    # Get extra declarations at the end of the struct
    for extraName in lastLine.split():
        if extraName == nameOverride:
            continue # Don't add extra names that match the top name
        pointerCount = extraName.count('*')
        extraNameDefinition = (pointerCount * "POINTER(") + nameOverride + (")" * pointerCount)
        fullStructDefinition += "%s = %s\n" % (extraName, extraNameDefinition)

    return fullStructDefinition

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
    parser.add_argument("-la", "--list_aliases", help="List of aliases delimited by semicolons (use to define #defines) for example: DEBUG=3;WORK_LVL=2", type=str, required=False)
    parser.add_argument("-d", "--debug", help="Debug flag", action='store_true')
    args = parser.parse_args()

    aliases = getTypeAliases(fileLocation=args.file)

    # Add specified aliases / #defines
    if args.list_aliases:
        for oneAlias in args.list_aliases.split(";"):
            left, right = map(str.strip, oneAlias.split("="))

            # Note that I'm not checking for an override here. Overrides are allowed.
            aliases[left] = right

    structuresAsText = findStructures(fileLocation=args.file, aliases=aliases)
    if not structuresAsText:
        print ("Found no structures.")
        sys.exit(1)

    for key, value in structuresAsText.items():
        print (key)
        print (value)
        print (cStructToPy(fileText=value, nameOverride=key, aliases=aliases))
        print ("-" * 40)
