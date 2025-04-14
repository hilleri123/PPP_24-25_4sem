import os

class FastApiServerInfo:
    SIGN_UP_ENDPOINT = "/sign-up/"
    LOGIN_ENDPOINT = "/login/"
    USER_INFO_ENDPOINT = "/users/me/"
    UNRAR_TOOL = os.path.join(os.path.expandvars(r'%PROGRAMFILES%'),'WinRAR','UnRAR.exe')
    BRUT_HASH = "/brut_hash/"
    GET_STATUS = "/get_status/"
    
    PORT = "8000"
    IP = "127.0.0.1"
    PORT = 7777