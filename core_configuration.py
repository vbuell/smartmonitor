import configparser
import os
import re
from itertools import chain
from datetime import datetime
import logging


def getConfigFiles(ending):
    confs = chain(os.walk(CORE_CONFIGURATION_ROOT_DIRECTORY + '/etc/services'), 
                  os.walk(CORE_CONFIGURATION_ROOT_DIRECTORY + '/etc/defaults'), 
                  os.walk(CORE_CONFIGURATION_ROOT_DIRECTORY + '/etc/test'))
    for base, dirs, files in confs:
        if not files:
            continue
        for name in files:
            if name.endswith(ending):
                yield "%s/%s" % (base, name)


def assembleConfig():
    config = configparser.ConfigParser()
    config.read(getConfigFiles('.conf'))
    return config


class BaseConfig(object):
    """
    A base configuration wrapper.
    """

    def __getattr__(self, attr):
        try:
            return self.__dict__.get(attr)
        except AttributeError:
            return self.config.__getattr__(attr)

    def getEnabledServices(self):
        """A set-powered means of geting the services."""
        enabled = sets.Set(self.getEnabledNames())
        pymonServices = sets.Set(self.services.getSectionAttributes())
        return enabled.intersection(pymonServices)

    def checkForMaintenanceWindow(self, config):
        try:
            start, end = config.scheduled_downtime.split('-')
            start = parseDate(start)
            end = parseDate(end)
        except AttributeError:
            start = end = None
        if (start <= datetime.now().timetuple() <= end):
            return True
        return False

    def checkForDisabledService(self, config):
        if config.enabled == False:
            return True
        return False

    def getStateNames(self):
        return list(self.stateLookup.values())

    def getStateNumbers(self):
        return list(self.stateLookup.keys())

    def getStateNameFromNumber(self, num):
        return self.stateLookup[str(num)]

    def getStateNumberFromName(self, name):
        return getattr(self.state_definitions, name.lower())


class SchemalessConfig(BaseConfig):

    def __init__(self, config):
        self.config = config

    def getEnabledServices(self):
        """
        A set-powered means of geting the services.
        """
        return self.config.sections()

    def getMonitorByName(self, name):
        found_section = None
        for section in self.config.sections():
            if self.config.get(section, 'id') == name:
                found_section = section

        return dict(self.config.items(found_section))

    def replacePlaceholdersByParameters(self, check, operands):
        for attribute in check.config:
            value = check.__getattr__(attribute)
            if value and type(value) is str:
                m = re.match(r".*%[0-9]", value)
                if m:
                    i = 0
                    for operand in operands:
                        value = value.replace("%"+str(i+1), operands[i])
                        i += 1
                    check.__setattr__(attribute, value)
        return check

    def getMonitorsIds(self):
        monitors = []
        enaServices = self.getEnabledServices()
        for pymonService in enaServices:
            if pymonService is None:
                continue
            # for check in pymonService.checks:
            #     if not check.id:
            #         continue
            monitors.append(self.config.get(pymonService, 'id'))
        return monitors
    
    def getMonitorByNameWithParents(self, name):
        monitor = self.getMonitorByName(name)
        return monitor
        # if monitor is None or monitor.base is None:
        #     return monitor
        # else:
        #     base = self.getMonitorByNameWithParents(monitor.base)
        #     for attribute in base.config:
        #         if monitor.__getattr__(attribute) == None:
        #             # copy monitor's attributes to base object
        #             monitor.__setattr__(attribute, base.__getattr__(attribute))
        #     return monitor



def get_configuration(rootdir="."):
    global CORE_CONFIGURATION_ROOT_DIRECTORY
    CORE_CONFIGURATION_ROOT_DIRECTORY = rootdir
    f = open(rootdir + "/etc/defines.conf", "r")
    # bootstrap_config = flatten_dictionary(dict(loadConfigFile(f)))

    # global config
    # config = loadConfigFileWithDefines(assembleConfig(), defines=bootstrap_config)

    global cfg
    cfg = SchemalessConfig(assembleConfig())

    global cfg_thresholds
    config = configparser.ConfigParser()
    config.readfp(open(CORE_CONFIGURATION_ROOT_DIRECTORY + "/etc/thresholds.conf"))
    cfg_thresholds = dict(config.items('thresholds'))

    return cfg, cfg_thresholds
