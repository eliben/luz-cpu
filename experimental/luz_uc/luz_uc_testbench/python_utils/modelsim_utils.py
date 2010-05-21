import os
import sys


def make_modelsim_exe_path():
    """ Finds the path to Modelsim's binaries.
        Tries both the environment variables and a common
        installation directory search.
        
        Returns the path or None if it wasn't found
    """
    
    # Try to find in env vars
    if os.environ.has_key('PATH'):
        for path in os.environ['PATH'].split(';'):
            if path.find('Modeltech') > -1:
                return path
    
    # Try to find in some directories:
    #
    dirs = [
        'C:\\', 'D:\\',
        'C:\\Program Files', 'D:\\Program Files',
    ]
    
    for dir in dirs:
        if not os.path.exists(dir): continue
        
        for path in os.listdir(dir):
            if path.find('Modeltech') > -1:
                return os.path.join(dir, path, 'win32')

    return None


if __name__ == '__main__':
    print make_modelsim_exe_path()


