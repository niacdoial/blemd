#! /usr/bin/python3
class _StringHelper:
    def __init__(self):  # GENERATED!
        pass

    def GetLastIndex(self, srcStr, matchChar):
        i = len(srcStr) -1
        for index in range(len(srcStr)):
            if srcStr[i] == matchChar:
                return i
            i -= 1
        return -1

    def StringReplace(self, srcStr, matchStr, replaceStr):
        # built in!
        return srcStr.replace(matchStr, replaceStr)

        #res = srcStr
        #i = findString(res, matchStr)

        #while i != undefined :
                        
        #    res = replace res i matchStr.count replaceStr
        #    i = findString res matchStr

    def ReplaceChar(self, srcStr, matchChar, replaceChar):
        return srcStr.replace(matchChar, replaceChar)
        # res = srcStr

        #for i in range( 1 , d+ 1) :

        #        return res

StringHelper = _StringHelper()
