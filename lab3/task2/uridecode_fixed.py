import afl
import sys

HEX_CHARS = set('0123456789abcdefABCDEF')

def uridecode(s):
    ret = []
    i = 0
    while i < len(s):
        # Translate %xx to its corresponding ASCII character
        if (i + 2 < len(s) and
                s[i + 1] in HEX_CHARS and
                s[i + 2] in HEX_CHARS):
            a = s[i + 1]
            b = s[i + 2]
            char_code = (int(a, 16) * 16) + int(b, 16)
            ret.append(chr(char_code))
            i += 3
        
        # Translates '+' into space
        elif s[i] == '+':
            ret.append(' ')
            i += 1
        
        # Leave other characters unchanged
        else:
            ret.append(s[i])
            i += 1
    return ''.join(ret)
    
if __name__ == '__main__':
    afl.init()
    print(uridecode(sys.stdin.read()))
