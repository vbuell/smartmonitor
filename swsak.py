'''
Created on Jun 19, 2009

@author: vbuell
'''
import time
import fcntl
import struct
import datetime
import os
import sys
from optparse import OptionParser
from core_configuration import get_configuration
from core_datastore import DataStore


DATA_FILES_DIR = "./data"

cfg = get_configuration()

class Command(object):
    
    def run(self):
        ''' Export data '''
        parser = OptionParser(conflict_handler="resolve")
        self.command_parser(parser)

        args = sys.argv
        del args[1]
        (options, args) = parser.parse_args(args)
        self.options = options
        self.do()
        
    def command_parser(self, parser):
        pass
    
    def do(self):
        pass


class Export(Command):
    
    def command_parser(self, parser):
        parser.add_option("-m", "--mon-id", dest="monitor_id", help="monitor id", 
                          default="")
        parser.add_option("-p", "--measurement", dest="measurement", help="measurement name", 
                          default="messageQueueSize")
        parser.add_option("-t", "--type", dest="output_type", help="output type (csv, gchart)", 
                          default="csv")
        parser.add_option("-s", "--separator", dest="separator", help="separator for CSV values", 
                          default=",")
        parser.add_option("-n", "--samples", dest="samples", help="number of samples", 
                          default="200")
    
    def do(self):
        self.store = DataStore()
        self.store.setWorkingDirectory(DATA_FILES_DIR)
        
        if self.options.output_type == "gchart":
            print self.generate_gchart_url(self.options.monitor_id, self.options.measurement)
        elif self.options.output_type == "csv":
            print self.export_csv(self.options.monitor_id, self.options.measurement)

    def generate_gchart_url(self, mon_id, parameter_name):
        ''' Read ticks and create the chart using google chart'''
#        url = "http://chart.apis.google.com/chart?cht=lc&chd=t:%(data_csv)s&chs=450x200&chl=%(data_csv)"
        URL_TEMPLATE = "http://chart.apis.google.com/chart?cht=lc&chd=t:%(data_csv)s&chs=450x200&chxt=y&chg=20,20,1,5"

        data_csv = self.export_csv(mon_id, parameter_name)

#        monitor = cfg.getMonitorByName(mon_id)
#        print str(monitor)
        
        return URL_TEMPLATE % {'data_csv': data_csv}
    
    # http://google-latlong.blogspot.com/2009/10/introducing-google-building-maker.html

    def export_csv(self, mon_id, parameter_name):
        ''' Get values for selected measurement of given monitor'''
        storage = self.store.getStorage(mon_id)
        entries = storage.getLastEntriesWithResult(int(self.options.samples), do_json=True)
        
        data_csv = ""
        first = True
        max_value = 0
        for entry in entries:
            if not first:
                data_csv += self.options.separator
            first = False
            obj, dt, health, stat = entry

            measurement_value = obj[parameter_name]
            data_csv += str(measurement_value)
            if measurement_value > max_value:
                max_value = measurement_value
        return data_csv
    

class Backup(Command):
    pass    


class Fix(Command):
    pass


class SwSAK(object):

    monitors = []
    
    def __init__(self):
        for mon in cfg.getMonitorsIds():
            if not cfg.getMonitorByName(mon).abstract:
                self.monitors.append(mon)
        self.mon_len = 0
        
    def run(self):
        self.store = DataStore()
        self.store.setWorkingDirectory(DATA_FILES_DIR)
        self.parseCommandLine()
        
        # detect max monitor lengh
        for mon in self.monitors:
            if len(str(mon)) > self.mon_len:
                self.mon_len = len(str(mon))
                
                
    def parseCommandLine(self):
        
        if len(sys.argv) > 1:
            if sys.argv[1] == 'export':
                export = Export()
                export.run()
            else:
                print "Error: unknown subcommand: " + sys.argv[1]
                sys.exit()           
        else:
            print "Error: use subcommand"
            sys.exit()           
        
        
if __name__ == "__main__":
    
    try:
        mtop = SwSAK()
        mtop.run()
    except KeyboardInterrupt:
        print "Interrupted by user..."
