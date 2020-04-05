# To change this template, choose Tools | Templates
# and open the template in the editor.

import warnings
warnings.filterwarnings("ignore", message="The popen2 module is deprecated")

try:
    import subprocess # 2.6
    subprocess_module_loaded = True
except ImportError: 
    subprocess_module_loaded = False
import popen2
import logging
import re
import os
import time
import signal

    
class ProcessTimeoutError(IOError):
    pass


class LocalExecutor(object):

    def call(self, cmd, cwd=None, timeout=None):
        """The parameter 'cmd' is the shell command to execute in a
        sub-process. 'cwd' is a working directory. If timeout is specified
        and process overrun its value ProcessTimeoutError will be raised."""
        if subprocess_module_loaded:
            return self.exec_monitor_2_6(cmd, cwd)
        else:
            return self.exec_monitor(cmd, cwd, timeout)
    
    def exec_monitor_2_6(self, cline, cwd=None):
        """Execute external script. Python 2.6 version. Doesn't support timeout 
        thus currently is disabled"""
        import subprocess
        import io
        file = io.StringIO()
        retcode = subprocess.call([cline, ""], shell=True, cwd=cwd)
        return retcode

    def exec_monitor(self, cline, cwd=None, timeout=None):
        """Execute external script."""
        timeout_detected = False
        if cwd:
            cwd_backup = os.getcwd()
            os.chdir(cwd)
        p = popen2.Popen3(cline)
        pid = p.pid
        timebefore = time.time()
        ec = -1
        while ec == -1:
            ec = p.poll()
            if timeout and (time.time() - timebefore) > timeout:
                timeout_detected = True
                break
    
        if timeout_detected:
            # Kill process
            os.kill(pid, signal.SIGKILL)
            raise ProcessTimeoutError

        print("exit code: %d, signal %d" % ( (ec >> 8) & 0xFF, ec & 0xFF ))
        print("---")
        str_stdout = p.fromchild.read()  # dump stdout from child process
    #    print str_stdout
        print("---")
        retcode = (ec >> 8) & 0xFF
    #    print type(retcode) 
        if cwd:
            os.chdir(cwd_backup)
        return retcode, str_stdout
    
    def read_output_file(self):
        pass
    

if __name__ == "__main__":

    try:
        print("before")
        executor = LocalExecutor()
        executor.call("sleep 10", timeout=3)
        print("after")
    except ProcessTimeoutError as e:
        print("timeout caught")
