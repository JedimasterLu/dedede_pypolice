CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
BLUE = '\033[34m'
RED = '\033[31m'
NORMAL = '\033[0m' #要以此结尾，还原默认颜色

def print_info(text, end='\n'):
    print( CYAN + text + NORMAL,end=end)

def print_warning(text, end='\n'):
    print( YELLOW + text + NORMAL,end=end)

def print_error(text, end='\n'):
    print( RED + text + NORMAL,end=end)
