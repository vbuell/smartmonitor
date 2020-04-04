# To change this template, choose Tools | Templates
# and open the template in the editor.

import logging
import re


def eval_number(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


class MonitorOutputParser(object):

    # default values
    delimiter = "="
    tableHeader = "<--table (.+) starts-->"
    tableFooter = "<--table (.+) ends-->"
    allowTables = False
    columnDelimiter = " "
    columnKey = None
    regex = None
    
    def setDelimiter(self, delimiter):
        self.delimiter = delimiter

    def setAllowTables(self, flag=True):
        self.allowTables = flag

    def setColumnsDelimiter(self, delimiter):
        self.columnDelimiter = delimiter

    def setColumnKey(self, delimiter):
        self.columnKey = delimiter

    def setTableHeader(self, delimiter):
        self.tableHeader = delimiter

    def setTableFooter(self, delimiter):
        self.tableFooter = delimiter
        
    def setRegex(self, regex):
        self.regex = []
        if isinstance(regex, list):
            for regex_element in regex:
                self.regex.append(regex_element)
        elif not isinstance(regex, type(None)):
            self.regex.append(regex)

    def parse(self, filename=None, lines=None):
        if filename:
            f = open(filename, "r")
            _lines = f.readlines()
        elif lines:
            _lines = lines
        else:
            raise ValueError("either filename or lines must be specified")

        objects_dict = {}
        in_table = False
        wait_for_column_header = False
        column_key_idx = 0
        table_headers = None
        for line in _lines:
            line = line.strip()
            
            if line == "":
                continue
            
            if self.regex:
                for regex_element in self.regex:                 
                    m = re.match(regex_element, line.strip())
                    if m:
                        measurement = m.group('key')
                        value = m.group('value')
                        objects_dict[measurement] = eval_number(value.strip())
                        break
                continue
            else:
                if wait_for_column_header:
                    headers = line.split("|")
                    table_headers = headers
                    # print headers
                    if not self.columnKey:
                        column_key_idx = 0
                    elif self.columnKey in headers:
                        column_key_idx = headers.index(self.columnKey)
                    else:
                        raise ValueError("column "+str(self.columnKey)+" isn't found in ["+str(line)+"]")
                        
                    wait_for_column_header = False
                    continue
                    
                if in_table:
                    # Table mode
                    m = re.match(self.tableFooter, line)
                    if m:
    #                    print "Table ends", m.group(1)
                        table_name = m.group(1)
                        in_table = False
                    else:
                        values = line.split(self.columnDelimiter)
    #                    objects_dict[table_name][values[column_key_idx]] = values
                        objects_dict[table_name][values[column_key_idx]] = {}
                        i = 0
                        for value in values:
                            objects_dict[table_name][values[column_key_idx]][table_headers[i]] = eval_number(value.strip())
                            i+=1
                
                else:
                    # Non table mode
                    if self.allowTables:
                        m = re.match(self.tableHeader, line)
                    if self.allowTables and m:
    #                    print "Table starts", m.group(1)
                        table_name = m.group(1)
    #                    objects_dict[table_name] = []
                        objects_dict[table_name] = {}
                        in_table = True
                        wait_for_column_header = True
    #                    print "In table = true"
                    else:
                        try:
                            key, value = line.split(self.delimiter)
                            objects_dict[key.strip()] = eval_number(value.strip())
                        except ValueError as e:
                            print(line)
                            logging.exception(e)
                        except Exception as e:
                            print(line)
                            logging.exception(e)

        return objects_dict

