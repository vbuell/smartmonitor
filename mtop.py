'''
Created on Jun 19, 2009

@author: vbuell
'''
import time
import fcntl
import struct
import datetime
import os, sys
import re
from optparse import OptionParser
from datetime import datetime
from core_configuration import get_configuration
from core_datastore import DataStore


class AnsiFormatter(object):
    def fail(self, txt):
        return "\033[31m"+txt+"\033[0m"
    
    def error(self, txt):
        return "\033[31m\033[1m"+txt+"\033[0m"
    
    def warn(self, txt):
        return "\033[33m"+txt+"\033[0m"
    
    def invert(self, txt):
    #    return "\033[7m"+txt+"\033[0m"
        return "\033[40m\033[37m"+txt+"\033[0m"
    
    def ok(self, txt):
        return "\033[32m"+txt+"\033[0m"
    
    def skip(self, txt):
        return "\033[34m\033[1m"+txt+"\033[0m"
    
    def home(self):
        return "\033[2J\033[H"
    
    def black3(self, txt):
        return txt
    
    def black2(self, txt):
        return "\033[90m"+txt+"\033[0m"
    
    def black1(self, txt):
        return "\033[37m"+txt+"\033[0m"
    
    def black0(self, txt):
        return "\033[97m"+txt+"\033[0m"

    def monitor_name(self, txt):
        return txt

    def link(self, txt, txt2, monitor_id):
        return txt2


class BaseFormatter(object):
    def fail(self, txt):
        return txt
    
    def error(self, txt):
        return txt
    
    def warn(self, txt):
        return txt
    
    def invert(self, txt):
    #    return "\033[7m"+txt+"\033[0m"
        return txt
    
    def ok(self, txt):
        return txt
    
    def skip(self, txt):
        return txt
    
    def home(self):
        return "\n"
    
    def black3(self, txt):
        return txt
    
    def black2(self, txt):
        return txt
    
    def black1(self, txt):
        return txt
    
    def black0(self, txt):
        return txt

    def monitor_name(self, txt):
        return txt

    def link(self, txt, txt2, monitor_id):
        return txt2


class _GetchUnix(object):
    """Gets a single character from standard input. Does not echo to the screen."""
        
    old_settings = None
    fd = None
        
    def init_raw(self):
        import sys, tty, termios
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setraw(sys.stdin.fileno())
        
    def quit_raw(self):
        import termios
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)
        
    def __call__(self):
        import sys, select
#        fd = sys.stdin.fileno()
#        old_settings = termios.tcgetattr(fd)
#        try:
#            tty.setraw(sys.stdin.fileno())
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            ch = sys.stdin.read(1)
            return ch
        else:
#                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return None 
#        finally:
#            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#        return ch


class MTop(object):

    width = 0
    height = 0
    
    BASE_DATA_DIR = "."
    LOG_FILES_DIR = "/logs"
    MONITORS_LOG_FILES_DIR = "/../log"
    DATA_FILES_DIR = "/data"
    
    GRAPH_LENGTH = 50
    
    frm = None

    def init_monitors(self):
        self.cfg, self.cfg_thresholds = get_configuration(self.BASE_DATA_DIR)
        self.monitors = [mon for mon in self.cfg.getMonitorsIds() if not self.cfg.getMonitorByName(mon).get('abstract')]
        self.monitors = sorted(self.monitors)

        # detect max length of monitors' names
        mon_len = max(map(len, self.monitors))

        self.pattern = "%(monname)-" + str(mon_len) + "s"

    def init_datastore(self):
        self.store = DataStore()
        self.store.setWorkingDirectory(self.BASE_DATA_DIR + self.DATA_FILES_DIR)
        
    def get_log_errors(self, directory, lines):
        import commands
# return commands.getstatusoutput('cat '+directory+'/*.log | grep "[1-9]\{3\} ERROR" | sort | tail -n 10 | sort -r')[1]
        return commands.getstatusoutput('for a in ' + directory +
                                        '/*.log; do tail "$a" -n50; done|grep "[1-9]\{3\} ERROR" | sort | tail -n ' +
                                        str(lines) + ' | sort -r')[1]

    def run(self):
        self.init_monitors()
        self.parseCommandLine()
        self.init_datastore()
        if self.options.output_format == 'ansi':
            self.frm = AnsiFormatter()
        else:
            self.frm = BaseFormatter()
        
#        inkey = _GetchUnix()
#        inkey.init_raw()
        
        cols, rows = terminal_size()
        print cols, rows
        self.width = cols
        self.height = rows

#        for i in range(1,7):
        while True:
            print self.step()
            
            time.sleep(int(self.options.refresh_time))
#            print 'Press a key'
#            import sys
#            for i in xrange(sys.maxint):
#            k=inkey()
#                if k>='':break
#            print '************* you pressed ', str(k)

#            getch = _Getch()
#            print "*************" + str(getch)
#            inkey.quit_raw()
#            print 
#            inkey.init_raw()
                
#        inkey.quit_raw()

    ui_step_count = 0
    
    def parseCommandLine(self):
        """Parse command line options."""
        parser = OptionParser(conflict_handler="resolve")
#        parser.add_option("-l", "--log-enable", dest="log_lines", help="log files analyze enable", 
#                          default=False, action="store_true")
        parser.add_option("-n", "--log-lines", dest="log_lines",
                          help="number of lines to be printed for errors got from log files. Set to 0 to disable log analysis",
                          default="10")
        parser.add_option("-r", "--refresh-time", dest="refresh_time", help="UI refresh time (in seconds)", 
                          default="5")
        parser.add_option("-c", "--refresh-skip-cycles", dest="cycle_skip_for_logs",
                          help="UI refresh cycles to be skipped before heavyweight analyze operations (non-zero positive number 1,2...)",
                          default="5")
        parser.add_option("-f", "--filter", dest="filter", help="regex pattern", 
                          default=None)

        # WIP
        parser.add_option("-s", "--sort", dest="sort", help="sorting (parameter is a column, like 'i' for ID)", 
                          default="i")
        parser.add_option("-o", "--output_format", dest="output_format", help="output_format [ansi, ascii, html]", 
                          default="ansi")
    
        (options, args) = parser.parse_args()
        self.options = options

    def step(self):
        screen_str = ""
        now = datetime.utcnow()
        screen_str += self.frm.home() + "SmartMon control panel. WIP version. " + str(now) + "\n"
        screen_str += ("-" * self.width) + "\n"

        screen_str += 'Clear : {}    Warning : {}    Error : {}    Timeout : {}    Killed : {}    Other errors : {}\n'.\
            format(self.frm.ok("-"), self.frm.warn("w"), self.frm.fail("e"),
                   self.frm.fail("t"), self.frm.fail("K"), self.frm.fail("!"))

        print "Monitors status...  ",
        sys.stdout.flush()
        
        header_line = self.pattern % {'monname': "MID"} + "\t" + "%% " + "\t" + "STAT" + "\t" + "GRAPH                                           " + "\t" + "LAST POLL"
        header_line += " " * (self.width - len(header_line) - 4 * 6)
        screen_str += self.frm.invert(header_line) + "\n"
        for mon in self.monitors:
            if mon:
                if self.options.filter:
                    if re.search(self.options.filter, mon, re.I) is None:
                        continue

                dt = "----"
                health = "--"

                storage = self.store.getStorage(mon)
                entry = storage.getLastEntriesWithResult(self.GRAPH_LENGTH, do_json=False)
                if entry:
                    # Get last entry
                    obj, dt, health, stat = entry[-1]
                    array = self.generate_graph(entry, mon)
                else:
                    array = " " * self.GRAPH_LENGTH
                    
#                    print "**** ", entry, " ****"
#                    print type(entry) 
#                if storage.getLastTime():
#                    dt = storage.getLastTime()
                delta = ""
                if type(dt) is datetime:
                    delta = now - dt
                    delta = self.colorize_delta(delta)

                screen_str += self.frm.monitor_name(self.pattern % {'monname': mon}) + "\t" + str(health) + "\t" + self.map_health_to_status(health) + "\t" + str(array) + "\t" + str(dt) + "\t" + "(- " + str(delta) + ")\n"

        log_lines_count = int(self.options.log_lines)

        if log_lines_count > 0:
            screen_str += "\n"
            if self.ui_step_count == 0:
                print "Wrapper errors parsing...  ",
                sys.stdout.flush()
                screen_str += self.frm.invert("Last wrapper errors:\n")
                self.last_wrapper_log_errors = self.get_log_errors(self.BASE_DATA_DIR + self.LOG_FILES_DIR, log_lines_count)
            else:
                screen_str += self.frm.invert("Last wrapper errors: (cached)\n")
            screen_str += self.last_wrapper_log_errors + "\n"
        
            screen_str += "\n"
            if self.ui_step_count == 0:
                print "Monitors' errors parsing...  ",
                sys.stdout.flush()
                screen_str += self.frm.invert("Last monitors' errors:\n")
                self.last_monitors_log_errors = self.get_log_errors(self.BASE_DATA_DIR + self.MONITORS_LOG_FILES_DIR, log_lines_count)
            else:
                screen_str += self.frm.invert("Last monitors' errors: (cached)\n")
            screen_str += self.last_monitors_log_errors + "\n"
            
        self.ui_step_count += 1
        if self.ui_step_count >= int(self.options.cycle_skip_for_logs):
            self.ui_step_count = 0

        return screen_str
            
    def colorize_delta(self, delta):
        
        str_delta = ""
        if delta.days:
            str_delta = self.frm.skip(str(delta.days) + " days")
        elif delta.seconds:
            if delta.seconds > (3600):
                str_delta = self.frm.skip(str(delta.seconds / (3600)) + " hours")
            elif delta.seconds > 60:
                str_delta = str(delta.seconds / 60) + " minutes"
            else:
                str_delta = str(delta.seconds) + " seconds"
        return str_delta
        
    def generate_graph(self, entries, mon):
        array = ""
        if len(entries) < self.GRAPH_LENGTH:
            array = " " * (self.GRAPH_LENGTH - len(entries))
        
        for entry in entries:
            obj, dt, health, stat = entry
            array += self.map_health_to_char(health, dt, mon, stat)

        return array
    
    def generate_gchart(self, mon_id):
        URL_TEMPLATE = 'http://chart.apis.google.com/chart?cht=lc&chd=t:{}&chs=450x160&chxt=y,r&chg=20,20,1,5&chxl=1:|err|warn|ok&chxp=1,10,40,95'
        
        storage = self.store.getStorage(mon_id)
        entries = storage.getLastEntriesWithResult(self.GRAPH_LENGTH, do_json=False)
        
        entries = [health for obj, dt, health, stat in entries]
        data_csv = ','.join(map(str, entries))
        return URL_TEMPLATE.format(data_csv)
    
    def getDataForMonitor(self, mon_id, dt):
        storage = self.store.getStorage(mon_id)
        entry = storage.getEntryByTimeWithResult(dt)
        return entry

    def getAllAvailableMeasurements(self, mon_id):
        entries = self.getLastMeasurementsForMonitor(mon_id)
        measurements = set()
        for entry in entries:
            obj, dt, health, stat = entry
#            for attr in dir(obj):
#                if attr.startswith("__"):
#                    continue
#                measurements.add(attr)
            for key in obj:
                measurements.add(key)
        return measurements

    def getLastMeasurementsForMonitor(self, mon_id):
        storage = self.store.getStorage(mon_id)
        entries = storage.getLastEntriesWithResult(self.GRAPH_LENGTH, do_json=True)
        return entries

    def getAllAvailableMeasurementsAsGchart(self, mon_id):
        entries = self.getLastMeasurementsForMonitor(mon_id)
        measurements = {}
        limits = {}
        for entry in entries:
            obj, dt, health, stat = entry
            for key in obj:
                if getattr(obj[key], '__iter__', False):
                    for key_measurement in obj[key]:
                        value_dict_with_columns = obj[key][key_measurement]
                        if "Value" in value_dict_with_columns:
                            try:
                                f_value = float(value_dict_with_columns["Value"])
                            except ValueError, e:
                                continue
                            if key_measurement in measurements:
                                measurements[key_measurement] += "," + str(f_value)
                                if limits[key_measurement] < f_value:
                                    limits[key_measurement] = f_value
                            else:
                                measurements[key_measurement] = str(f_value)
                                limits[key_measurement] = f_value
                            
                    continue    # TODO: support for tables
                try:
                    f_value = float(obj[key])
                except ValueError, e:
                    continue
                    
                if key in measurements:
                    measurements[key] += "," + str(obj[key])
                    if limits[key] < f_value:
                        limits[key] = f_value
                else:
                    measurements[key] = str(obj[key])
                    limits[key] = f_value
        return measurements, limits
        
    def map_health_to_char(self, result, date_time, mon, stat):
        if result >= 60:
            return self.frm.link(date_time, self.frm.ok("-"), mon)
        elif result > 30:
            return self.frm.link(date_time, self.frm.warn("w"), mon)
        else:
            if stat == "CONN" or stat == "IO" or stat == "TRGG":
                return self.frm.link(date_time, self.frm.fail("!"), mon)
            if stat == "TIMEOUT":
                return self.frm.link(date_time, self.frm.fail("t"), mon)
            if stat == "KILLED":
                return self.frm.link(date_time, self.frm.fail("K"), mon)
            else:
                return self.frm.link(date_time, self.frm.fail("e"), mon)

    def map_health_to_status(self, health):
        if type(health) is str:
            return "n/a"
        if health >= 60:
            return self.frm.ok("OK")
        elif health > 30:
            return self.frm.warn("WARN")
        else:
            return self.frm.error("ERR")
    

def getChar():
    import termios, fcntl, sys, os, select

    fd = sys.stdin.fileno()
    
    oldterm = termios.tcgetattr(fd)
    newattr = oldterm[:]
    newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
    termios.tcsetattr(fd, termios.TCSANOW, newattr)
    
    oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)
    
    try:
#        while 1:
        r, w, e = select.select([fd], [], [])
        if r:
            c = sys.stdin.read(1)
            print "Got character", repr(c)
            if c == "q":
                return
    finally:
        termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)
        return c         


def ioctl_GWINSZ(fd): #### TABULATION FUNCTIONS
    """Discover terminal width."""
    try:
        import termios
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
        return None
    return cr


def terminal_size():
    """Decide on *some* terminal size."""
    # try open fds
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        # ...then ctty
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        # env vars or finally defaults
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            cr = (25, 80)
    # reverse rows, cols
    return int(cr[1]), int(cr[0])


if __name__ == "__main__":
    
    try:
        mtop = MTop()
        mtop.run()
    except KeyboardInterrupt:
        print "Interrupted by user..."
