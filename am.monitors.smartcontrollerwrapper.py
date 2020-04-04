#!/usr/bin/env python
__author__ = "vbuell"
__date__ = "$May 14, 2009 2:24:59 PM$"

import warnings
warnings.simplefilter('ignore', DeprecationWarning)

import sys, os
import subprocess
import re
import logging
import logging.handlers
import types
try:
    import paramiko
except ImportError:
    print("Paramico not found. SSH disabled.")
import time
import signal
from signal import *
from optparse import OptionParser
from core import *
from core_parser import *
from core_datastore import *
from core_eval import *
from core_configuration import get_configuration


OUTPUT_FILES_DIR = "./output"
LOG_FILES_DIR = "./logs"
DATA_FILES_DIR = "./data"

DATA_VARIABLE_OUTFILE = 'outfile'

OUTFILE_PROPERTY_RESULT = "wrp_result"
OUTFILE_PROPERTY_DEBUG = "wrp_debug"
OUTFILE_PROPERTY_EXEC_TIME = "wrp_execution_time"
OUTFILE_PROPERTY_MESSAGE = "wrp_message"

RESULT_OK = 100
RESULT_CRITICAL = 0
RESULT_WARNING = 40

LOGGER_FORMAT = '%(asctime)s %(levelname)-8s %(message)s'

cfg, cfg_thresholds = get_configuration()


class ProcessTimeoutError(IOError):
    pass


class InternalProcessingException(Exception):

    def __init__(self, msg, health, stat, do_outfile=True, do_dbentry=True):
        self.msg = msg
        self.stat = stat
        self.health = health
        self.do_outfile = do_outfile 
        self.do_dbentry = do_dbentry
        

class SmartWrapper(object):
    
    lowest_result = RESULT_OK
    original_output_file_lines = None
    execution_time = None
    
    def parse_command_line(self):
        """Parse command line options."""
        parser = OptionParser(conflict_handler="resolve")
        parser.add_option("-o", "--output_file", dest="output_file", help="write output to FILE")
        parser.add_option("-t", "--log_file", dest="log_file", help="write logs to FILE",
                    default="./sFTP_monitor.out")
        parser.add_option("-m", "--monitor", dest="monitor_name", help="monitor name", default="")
#        parser.add_option("-i", "--input_file", dest="input_file", help="input FILE to analyze. Default: "+OUTPUT_FILES_DIR+"/<monitor_id>_wrapped.txt")    # TODO

        (options, args) = parser.parse_args()
        self.options = options
        return args
    
    def exec_monitor_2_6(self, cline, cwd=None):
        """Execute external script. Python 2.6 version."""
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
        p = subprocess.Popen(cline)
        pid = p.pid
        timebefore = time.time()
        str_stdout = ""
        ec = -1
        while ec == -1:
            ec = p.poll()
            str_stdout += p.fromchild.read()
            if timeout and (time.time() - timebefore) > timeout:
                timeout_detected = True
                break
    
        if timeout_detected:
            # Kill process
            os.kill(pid, signal.SIGKILL)
            raise ProcessTimeoutError
            return

        print("exit code: %d, signal %d" % ( (ec >> 8) & 0xFF, ec & 0xFF ))
        print("---")
#        str_stdout = p.fromchild.read()  # dump stdout from child process
    #    print str_stdout
        print("---")
        retcode = (ec >> 8) & 0xFF
    #    print type(retcode) 
        if cwd:
            os.chdir(cwd_backup)
        return retcode, str_stdout

    def process_quit(self, signum, frame):
        global logger
        logger.info("SIGQUIT detected")

    def process_tstp(self, signum, frame):
        global logger
        logger.info("SIGTSTP detected")

    def process_term(self, signum, frame):
        global logger
        logger.info("SIGTERM detected")
        self.store_to_datastore({}, RESULT_CRITICAL, "KILLED")
        
    def handle_signals(self):
        signal(SIGQUIT, self.process_quit)
        signal(SIGTSTP, self.process_tstp)
        signal(SIGTERM, self.process_term)

    def setup_bootstrap_logger(self):
        # Logging initialization
        LOG_FILENAME = LOG_FILES_DIR + "/bootstrap.log"

        self.logger_bootstrap = logging.getLogger('smartwrapperapp')
        hdlr = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=5)
        formatter = logging.Formatter(LOGGER_FORMAT)
        hdlr.setFormatter(formatter)
        self.logger_bootstrap.addHandler(hdlr)
        self.logger_bootstrap.setLevel(logging.DEBUG)

        self.logger_bootstrap.info('-- SmartWrapper started --')
        self.logger_bootstrap.info('PID:' + str(os.getpid()) + " PPID:" + str(os.getppid()) + " UID:" + str(os.getuid()))

    def run(self):
        global logger

        self.setup_bootstrap_logger()

        args = self.parse_command_line()

        # signal handler initialization
        self.handle_signals()

        datadir = os.path.dirname(sys.argv[0])
        self.logger_bootstrap.info('Data directory of script: ' + datadir)
        self.logger_bootstrap.info('Current working directory: ' + os.getcwd())

        self.configuration = SmartMonContext()

        if self.options.monitor_name == ".+":
            self.logger_bootstrap.info("Monitors to be checked: " + str(cfg.getMonitorsIds()))
            for monitor_name in cfg.getMonitorsIds():
                try:
                    self.run_monitor(monitor_name, args)
                except Exception as e:
                    self.logger_bootstrap.exception(e)
        else:
            try:
                self.run_monitor(self.options.monitor_name, args)
            except Exception as e:
                self.logger_bootstrap.exception(e)

    def run_monitor(self, monitor_name, args):
        self.logger_bootstrap.info('Running monitor: ' + monitor_name)
        # Logging initialization
        if monitor_name:
            self.LOG_FILENAME = LOG_FILES_DIR + "/" + monitor_name + ".log"
        else:
            self.LOG_FILENAME = LOG_FILES_DIR + "/!unnamed.log"
        self.log_file_abspath = os.path.abspath(self.LOG_FILENAME)

        global logger
        logger = logging.getLogger(monitor_name)
        hdlr = logging.handlers.RotatingFileHandler(self.LOG_FILENAME, maxBytes=1000000, backupCount=5)
        formatter = logging.Formatter(LOGGER_FORMAT)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr) 
        logger.setLevel(logging.DEBUG)
        
        logger.info('-- SmartWrapper started --')
        logger.info('PID:' + str(os.getpid()) + " PPID:" + str(os.getppid()) + " UID:" + str(os.getuid()))
    
        self.debug_message = ""
        
        mon_arguments = ""
        if monitor_name is not None:
            # find monitor by id
            self.configuration.monitor_name = monitor_name
            check = cfg.getMonitorByNameWithParents(monitor_name)
            if check is None:
                print("ERROR: No monitor with specified id '" + monitor_name + "' defined.")
                return
            
            # store itself
            self.check = check
            
            # get all needed info
            mon_command = check.get('command')
            mon_cwd = check.get('working_directory')
            if check.get('arguments'):
                mon_arguments = check.get('arguments')
            mon_output_file = check.get('output_file')
            
            # thresholds
            self.thresholds = []
            if isinstance(check.get('threshold'), list):
                for threshold in check.get('threshold'):
                    self.thresholds.append(threshold)
            elif not isinstance(check.get('threshold'), type(None)):
                self.thresholds.append(check.get('threshold'))
            
            if isinstance(check.get('threshold-ref'), list):
                for threshold_ref in check.get('threshold-ref'):
                    self.thresholds.append(self.get_threshold_by_name(threshold_ref))
            elif not isinstance(check.get('threshold-ref'), type(None)):
                self.thresholds.append(self.get_threshold_by_name(check.get('threshold-ref')))
                
            logger.debug("Thresholds: " + str(self.thresholds))
            
            logger.debug("Monitor command: " + mon_command)
            logger.debug("Monitor cwd: " + str(mon_cwd))
            logger.debug("Monitor arguments: " + mon_arguments)
            logger.debug("Monitor outfile: " + str(mon_output_file))
        else:
            self.configuration.monitor_name = "mock"    # TODO

        self.child_argv = mon_arguments
        for arg in args:
            self.child_argv += " " + arg
            
        logger.info("Combined arguments:" + self.child_argv)
        
        before = time.time()
        
        try:
            param_timeout = int(self.check.get('timeout'))
        except TypeError:
            param_timeout = None

        type = self.check.get('type')
        print(">>> type:", type)
        if type == "simple":
            print("Simple script invocation.")
        else:
            pass

        # Main flow starts here
        try:  
        
            # Execute external script
            print("Executing...")
            if self.check.get('ssh'):
                print("Executing via SSH...")
                m = re.match(r"(\w+):(\S+)@([\w.]+)", self.check.get('ssh'))
                
                username = m.group(1)
                password = m.group(2)
                host = m.group(3)
                
                print(username)
                print(password)
                print(host)
                
                try:
                    self.connect_to_host(host, username, password)
                except Exception as e:
                    logger.error("Cannot connect to host: " + host)
                    raise InternalProcessingException("Cannot connect to host: " + host, RESULT_CRITICAL, "CONN")
#                    self.system_error("Cannot connect to host " + host + ": " + str(e))
                
                # emulate cwd via cd
                print(("cd {}; {} {}".format(mon_cwd, mon_command, self.child_argv)))
                exec_output = self.exec_via_ssh_timeout("cd "+mon_cwd+"; " + mon_command + " " + self.child_argv, param_timeout)
                
                exec_output = self.exec_via_ssh_timeout("cat "+mon_output_file, 5)
                self.original_output_file_lines = exec_output
                if not self.original_output_file_lines:
                    logger.error("Output file is empty or doesn't exist: '" + mon_output_file + "'")
                    raise InternalProcessingException("Output file is empty or does not exist: '" + mon_output_file + "'", RESULT_CRITICAL, "IO")
#                    self.system_error("Output file is empty or does not exist: '" + mon_output_file + "'")
            else:
                try:
                    self.retcode, str_stdout = self.exec_monitor(mon_command + " " + self.child_argv, cwd=mon_cwd, timeout=param_timeout)
                except ProcessTimeoutError as e:
                    print("Timeout")
                    logger.error("Script execution timeout")
                    raise InternalProcessingException("Script execution timeout", RESULT_CRITICAL, "TIMEOUT")
                except OSError as e:
                    print("File/dir not found")
                    logger.error("File/dir not found")
                    raise InternalProcessingException("File/directory not found", RESULT_CRITICAL, "IO")
#                    self.system_error("Script execution timeout")
                if self.retcode == 0:
                    logger.info("Return code: " + str(self.retcode))
                else:
                    logger.error("Return code: " + str(self.retcode) + ". Please review what could this means")
                
                if type != "simple" and mon_output_file:
                    try:
                        with open(mon_output_file, "r") as f:
                            self.original_output_file_lines = f.readlines()
                    except IOError as e:
                        print("IOError error!!!!!!")
                        logger.exception(e)
                        message = str(e)
                        if self.retcode != 0:
                            message += ". Return code: " + str(self.retcode)
                        raise InternalProcessingException(message, RESULT_CRITICAL, "IO")
    #                    self.system_error(message)
                
            after = time.time()
            self.execution_time = after - before
            
            # Parse return information
            if type != "simple":
                parser = MonitorOutputParser()
                parser.setDelimiter(cfg.parser.delimiter)
                parser.setAllowTables(cfg.parser.allowTables)
                parser.setColumnsDelimiter(cfg.parser.columnsDelimiter)

                if self.check.parser and self.check.parser.regex:
                    parser.setRegex(self.check.parser.regex)
                    logger.info("Regex pattern used for parsing:" + str(self.check.parser.regex))
                res = parser.parse(lines=self.original_output_file_lines)
                logger.info("Parsed outfile:" + str(res))

                self.configuration.state_variables = res
            else:
                self.configuration.state_variables = {}

            self.configuration.state_variables["return_code"] = self.retcode
            
            # What we need in configuration for analyzer: delimiter setting, out_filename
            self.analyse_data()
            
            # Initialize variables
            if not self.debug_message:
                self.debug_message = "OK"
            self.error_message = "OK"
            self.return_value = self.lowest_result
            outfile = self.generate_output_file()
            self.configuration.state_variables[DATA_VARIABLE_OUTFILE] = outfile

            self.store_to_datastore(self.configuration.state_variables, self.lowest_result, None)
            
#            storage.appendHealthInfoToLastEntry(self.lowest_result)
    
            # Generate "fake" output file
            self.write_output_and_exit(self.generate_output_file())
            
        except InternalProcessingException as e:
            if not self.configuration.state_variables:
                self.configuration.state_variables = {}
            if e.do_outfile:
                print("Will create outfile")
                self.return_value = e.health
                self.error_message = "Wrapper error: " + e.msg + ". See log file for details: " + self.log_file_abspath
                self.debug_message = e.msg
                outfile = self.generate_output_file()
                self.configuration.state_variables[DATA_VARIABLE_OUTFILE] = outfile
            if e.do_dbentry:
                print("Storing to db...")
                self.store_to_datastore(self.configuration.state_variables, e.health, e.stat)
                print("Stored")
            if e.do_outfile:
                self.write_output_and_exit(outfile, False)
        
    def store_to_datastore(self, object, health, stat):
        print("Writing to storage...")
        store = DataStore()
        store.setWorkingDirectory(DATA_FILES_DIR)
        storage = store.getStorage(self.configuration.monitor_name)
        storage.putEntry(object, health, stat)
        
    def get_threshold_by_name(self, id):
        global cfg_thresholds
        return cfg_thresholds.get(id)

    def analyse_data(self):
        global logger
        # Analyze data
        print("Analyzing...")
        try:
            evaluator = MonitorEvaluator()
            for threshold in self.thresholds:
                result = evaluator.evaluate(threshold, self.configuration.state_variables)
                logger.info("Threshold state: {}    ('{}')".format(result, threshold))
#                print "Threshhold result type:", type(result)
                self.collect_result(self.map_result(result))
#                print "Critical:", result[0], "Warning:", result[1], "Ok:", result[2]
                # generate debug info
                if self.map_result(result) == RESULT_CRITICAL:
                    self.append_debug("ERROR: Threshold:" + threshold)
                elif self.map_result(result) == RESULT_WARNING:
                    self.append_debug("WARN: Threshold:" + threshold)
                
        except Exception as e:
            logger.exception(e)
            raise InternalProcessingException(str(type(e)) + ":" + str(e), RESULT_CRITICAL, "TRGG")
#            self.system_error(str(type(e)) + ":" + str(e))

    def append_debug(self, error_message):
        global logger
        self.debug_message += error_message + ";"
        logger.warn(error_message)

    def map_result(self, var):
        if isinstance(var, bool):
            if var:
                return RESULT_CRITICAL
            else:
                return RESULT_OK
        if isinstance(var, tuple):
            if var[0]:
                return RESULT_CRITICAL
            if var[1]:
                return RESULT_WARNING
            if var[2]:
                return RESULT_OK
        
    def collect_result(self, result):
        global logger
        if result < self.lowest_result:
            self.lowest_result = result
            logger.info("Lowest_result dropped to " + str(result))

    def generate_output_file(self):
        str_out = OUTFILE_PROPERTY_RESULT + "=" + str(self.return_value) + "\n"
        if self.debug_message:
            str_out += OUTFILE_PROPERTY_DEBUG + "=" + self.filter_illegal_chars(str(self.debug_message)) + "\n"
        print(">> execution-time", self.check.get('execution-time'))
        if self.check.get('execution-time') == "yes" and self.execution_time:
            str_out += OUTFILE_PROPERTY_EXEC_TIME + "="+"%.2f" % self.execution_time+"\n"
        str_out += OUTFILE_PROPERTY_MESSAGE + "=" + self.filter_illegal_chars(str(self.error_message))
        if self.check.get('copy_original') == "yes" and self.original_output_file_lines:
#            f = open(self.check.output_file, "r")
            str_out += "\n"
            for line in self.original_output_file_lines:
                str_out += self.filter_illegal_chars(line)
        return str_out
    
    def write_output_and_exit(self, content, do_exit=True):
        if self.options.output_file:
            with open(self.options.output_file, "w") as outfile:
                outfile.write(content)
            print("Output file written to " + self.options.output_file)
#        exit(self.return_value)
        # Disabled sys.exit() as now application can run several monitors. What status should we return?
#        if do_exit:
#            sys.exit(0)

    def connect_to_host(self, host, username, password):
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        self.ssh.connect(host, username=username, password=password, timeout=10.0)

    def exec_via_ssh(self, command):
        """Call shell-command and return its output"""
        stdin_, stdout_, stderr = self.ssh.exec_command(command)
        return stdout_.readlines()

    def exec_via_ssh_timeout(self, command, timeout):
        """Call shell-command and either return its output or kill it
        if it doesn't normally exit within timeout seconds and return None"""
        stdin_, stdout_, stderr_ = self.ssh.exec_command(command)
        stdout_.channel.settimeout(timeout)
        return stdout_.readlines()

    def filter_illegal_chars(self, message):
        message = message.replace("'", " ")
        message = message.replace("[", " ")
        message = message.replace("]", " ")
        return message
    

if __name__ == "__main__":

    logger = None
    wrapper = SmartWrapper()
    try:
        wrapper.run()
    except SystemExit:
        pass
        sys.exit()
    # except Exception, e:
    #     # TODO: error handling
    #     print "Unhandled exception detected!!! Output file may not be written."
    #     print e
    #     logger.error("Unhandled exception detected!!! Output file may not be written.")
    #     logger.exception(e)
    #     sys.exit(2)
