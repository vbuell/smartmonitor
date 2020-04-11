import json
import logging
import re
import os
from datetime import datetime, timedelta
from core_parser import eval_number


DATETIME_FORMAT = "%Y-%m-%d,%H:%M:%S"


class Storage(object):
    """Samples storage."""

    def __init__(self, filename):
        """Constructor."""
        self.file = open(filename, 'a+')
        self.last_timestamp = None
        self.re_pattern_entry = re.compile(r"^(.+) (-?\d+)hu( ([A-Z]+))?$")

    def getLastEntries(self, number_of_entries):
        """Read last n entries from the storage file."""
        entries = []
        self.file.seek(0)
        lines = self._tail_lines(self.file, number_of_entries)
        
        if len(lines) < number_of_entries:
            number_of_entries = len(lines)
        
        for idx in range(len(lines) - number_of_entries, len(lines)):
            line = lines[idx].strip()
            try:
                obj, dt, var_xxx, stat = self._line_to_obj(line)
                if idx == len(lines) - 1:
                    self.last_timestamp = dt
                entries.append(obj)
            except ValueError as e:
                logging.exception(e)

        return entries
    
    def getLastEntriesWithResult(self, number_of_entries, do_json=True):
        """Read last n entries from the storage file."""
        entries = []
        self.file.seek(0)
        lines = self._tail_lines(self.file, number_of_entries)
        
        if len(lines) < number_of_entries:
            number_of_entries = len(lines)
        
        for idx in range(len(lines) - number_of_entries, len(lines)):
            line = lines[idx].strip()
            try:
                obj, dt, var_xxx, stat = self._line_to_obj(line, do_json)
                if idx == len(lines) - 1:
                    self.last_timestamp = dt
                entries.append((obj, dt, var_xxx, stat))
            except ValueError as e:
                logging.exception(e)

        return entries
    
    def getEntryByTimeWithResult(self, dt, lines_limit=100):
        str_dt = dt.isoformat()
        self.file.seek(0)
        lines = self._tail_lines(self.file, lines_limit)
        for line in lines:
            if line.startswith(str_dt):
#                try:
                    obj, dt, var_xxx, stat = self._line_to_obj(line)
                    return obj, dt, var_xxx, stat
#                except ValueError, e:
#                    logging.exception(e)
                
        return None
            
    def getLastTime(self):
        return self.last_timestamp
    
    def getLastEntriesForPeriod(self, amount, units):
        entries = []
        self.file.seek(0)
        lines = self.file.readlines()
        
        now = datetime.utcnow()
        # TODO: units.lowcase()
        
        if units.startswith("day"):
            now = now - timedelta(days=amount)
        elif units.startswith("ho"):
            now = now - timedelta(hours=amount)
        elif units.startswith("min"):
            now = now - timedelta(minutes=amount)
        elif units.startswith("sec"):
            now = now - timedelta(seconds=amount)
        
        for idx in reversed(list(range(0, len(lines)))):
            line = lines[idx].strip()
            try:
                obj, dt, var_xxx, stat = self._line_to_obj(line)
                if dt > now:
                    entries.append(obj)
            except ValueError as e:
                logging.exception(e)

        return entries
    
    def _line_to_obj(self, line, do_json=True):
        start_idx = line.find(" ")
        dt = datetime.fromisoformat(line[0:start_idx])
        
        m = self.re_pattern_entry.match(line[start_idx:])
        if m:
            json_body = m.group(1)
            health = eval_number(m.group(2))
            stat = m.group(4)
        else:
            health = 0
            stat = "OK"
            json_body = line[start_idx:]

        if not do_json:
            return None, dt, health, stat
        return json.loads(json_body), dt, health, stat

    def _obj_to_line(self, object, health=None, stat=None):

        str_out = datetime.utcnow().isoformat() + " " 

        str_out += json.dumps(object)
            
        if health is not None:
            str_out += " " + str(health) + "hu"

        if stat:
            str_out += " " + str(stat)

        return str_out
    
    def putEntry(self, object, health=None, stat=None):
        """Append object to the storage file."""
        self.file.write(self._obj_to_line(object, health, stat) + "\n")
        self.file.flush()
        
    def _tail_lines(self, file, linesback=10):
        """Does what "tail -10 filename" would have done
           Parameters:
                filename   file to read
                linesback  Number of lines to read from end of file
        """
        if linesback == 0:
            return []
        
        avgcharsperline = 600
    
        while True:
            try: file.seek(int(-1 * avgcharsperline * linesback),2)
            except IOError: file.seek(0)
            if file.tell() == 0: atstart=1
            else: atstart=0
    
            lines=file.read().split("\n")
            if (len(lines) > (linesback+1)) or atstart: break
            #The lines are bigger than we thought
            avgcharsperline=avgcharsperline * 2 # Inc avg for retry
#        file.close()
    
        if len(lines) > linesback: 
            start = len(lines)-linesback -1
        else: 
            start = 0
        return lines[start:len(lines)-1]


class DataStore(object):

    def setWorkingDirectory(self, directory):
        """setWorkingDirectory."""
        self.directory = directory

    def getStorage(self, name):
        """getStorage."""
        if not name:
            raise ValueError("name must not be None")
        return Storage(self.directory + "/" + name + ".txt")

