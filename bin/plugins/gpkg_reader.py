_key = b"7ECp11QpwGlQVmxkXiy2GMUIM6NAkRD3ff_2FWEWOT8="

from cryptography.fernet import Fernet

fernet = Fernet(_key)

def read(filecontent, encode=False):
    if encode:
        return fernet.decrypt(filecontent.encode())
    else:
        return fernet.decrypt(filecontent)