""" Provides an interface to Modlsim's suite for VHDL compilation.

    Convenience features:
    * Automatically detects the path to Modelsim
    * Knows how to compile only those files that have been changed
      since their last compilation.
"""
import logging, os, re, stat
from shutil import rmtree
from subprocess import Popen, PIPE

from modelsim_utils import make_modelsim_exe_path
from vhdl_utils import vhdl_unit_name


class VHDLCompileError(Exception): pass


class VHDLCompiler(object):
    def __init__(
            self, 
            modelsim_path=None,
            log_file=None,
            log_level=logging.DEBUG,
            ):
        """ Create a new instance of VHDLCompiler.
        
            modelsim_path:
                Suggest VHDLCompiler where to find Modelsim. This
                Should be Modelsim's root directory, such as 
                C:\\Modeltech_6.3f
            
            log_file:
                If a file name is given, this file will be used 
                for logging. Otherwise, logging messages will be
                printed to stderr.
            
            log_level: 
                Set the minimal level of logging messages to be
                shown (logging.CRITICAL to disable logging)
        """
        self.log = logging.getLogger('VHDLCompiler')
        self.log.setLevel(log_level)
        
        if log_file is None:
            handler = logging.StreamHandler()
        else:
            handler = logging.FileHandler(log_file, 'w')
        
        handler.setFormatter(
            logging.Formatter('%(name)s:%(levelname)s: %(message)s'))
        self.log.addHandler(handler)
        
        self._make_paths(modelsim_path)
    
    def compile_files(
            self, 
            files,
            lib='work',
            params='-quiet -pedanticerrors -93 -explicit',
            force_compile_all=False,
            make_lib=True,
            ):
        """ Compile a group of VHDL files. Can recognize when
            the files are up to date and need no compilation.
            
            files: 
                A list of file names.
            
            lib: 
                A library name to compile the files to.
            
            params: 
                Compilation parameters passed to vcom
            
            force_compile_all:
                If this is False, will attempt to see whether the
                file is newer than its compiled object and only
                then compile it.
                If True, always compiles all files.
                
            make_lib:
                Attempt to create the object library with 'vlib'
                if it doesn't exist.
            
            Finishes quietly if no errors occurred. Throws an 
            VHDLCompileError exception otherwise.
        """
        # Make the library if it doesn't exist
        #
        if make_lib and not os.path.exists(lib):
            out = self._run_command("%s %s" % (self.vlib_path, lib))
            
            if out != '':
                if out.find('Error') > -1:
                    raise VHDLCompileError('vlib error: %s' % out)
                else:
                    self.log.info('vlib said: %s' % out)
                
            # If the library has just been created, we have to
            # compile all the files anew
            #
            force_compile_all = True
        
        params = "-work %s " % lib + params
                
        for file in files:
            if not os.path.exists(file):
                raise VHDLCompileError("File '%s' doesn't exist" % file)
            
            if (    force_compile_all or
                    not self._file_is_uptodate(file, lib)
                ):
                self._compile_file(file, params)
    
    #######################   PRIVATE   #######################
    
    def _file_is_uptodate(self, file, lib):
        """ Finds out if the VHDL file is older than its compiled
            object in the library.
        """
        object_dir = self._get_object_dir_name(file, lib)
        
        if object_dir is None:
            # Couldn't find it? Assume the file isn't up to date
            self.log.debug("Didn't find unit name in '%s'" % file)
            return False
                
        file_mtime = os.stat(file)[stat.ST_MTIME]
        
        if os.path.exists(object_dir):
            object_mtime = os.stat(object_dir)[stat.ST_MTIME]
            return object_mtime > file_mtime
        else:
            return False
    
    def _get_object_dir_name(self, file, lib):
        """ Finds out the compiled object directory name for the 
            file.
        """
        unit_name = vhdl_unit_name(file)
        
        if unit_name is None:
            return None        
        return os.path.join(lib, unit_name)
    
    def _compile_file(self, file, params):
        """ Compiles a single VHDL file. Watches the result of
            the compilation.
            In case of an error, the source file is 'touched' to
            force compilation the next time we run.
        """
        out = self._run_command("%s %s %s" % (
                                    self.vcom_path,
                                    file,
                                    params))
        if out != '':
            if out.find('Error') > -1:
                os.utime(file, None)
                raise VHDLCompileError("Error compiling '%s': %s" % (
                                file, out))
            else:
                self.log.info('vcom said: %s' % out)
        
    def _run_command(self, cmd):
        """ Executes the command as a sub-process and returns 
            its output and error streams as a string.
        """
        self.log.info(cmd)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=False)
        return p.stdout.read() + p.stderr.read()
    
    def _make_paths(self, modelsim_path=None):
        """ Given a path to Modelsim's binary directory (usually
            win32), computes the paths to the VHDL compiler
            executables.
            If no path is given (None), uses
            make_modelsim_exe_path to try and find it.
        """
        mpath = modelsim_path
        
        if not modelsim_path:
            mpath = make_modelsim_exe_path()
        
        if mpath is None:
            raise VHDLCompileError("Could not find modelsim's path")
        
        self.vcom_path = os.path.join(mpath, 'vcom.exe')
        self.log.info('vcom path set to %s' % self.vcom_path)
        
        if not os.path.exists(self.vcom_path):
            raise VHDLCompileError("Invalid path to 'vcom': %s" % self.vcom_path)
        
        self.vlib_path = os.path.join(mpath, 'vlib.exe')
        self.log.info('vlib path set to %s' % self.vlib_path)
        
        if not os.path.exists(self.vlib_path):
            raise VHDLCompileError("Invalid path to 'vlib': %s" % self.vlib_path)
    

if __name__ == '__main__':
    
    vc = VHDLCompiler()

