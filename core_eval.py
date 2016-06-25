'''
Created on May 25, 2009
@author: vbuell
'''
import re
import unittest
import logging
from core_datastore import DataStore
from core import SmartMonContext


def avg(obj):
    """Average value of sequence."""
    sum_ = 0
    num = 0
    for o in obj:
        sum_ += o
        num += 1
    if num != 0:
        return sum_ / num
    else:
        return 0


def wrapDictObjects(obj):
    # Wrap dictionary to make their elements behave as properties
    if type(obj) is dict:
        return AttributeableDict(obj)
    return obj


def getAttributeWithFailover(obj, attr_name):
    try:
        return wrapDictObjects(obj[attr_name])
    except KeyError:
        for o in obj:
#            if o.replace(' ', '_').replace('.', '_').lower() == attr_name.lower():
            if re.sub(r'\W', '_', o).lower() == attr_name.lower():
                return wrapDictObjects(obj[o])
        raise KeyError(attr_name + " variable not found in: " + str(object))
        
        
class AttributeableDict(dict):
    """Table wrapper."""
    
    def __getattr__(self, attr):
        obj = getAttributeWithFailover(self, attr)
        return obj

    
class Samples(object):
    """Samplestore."""

    objects = []
    single_entry = False

    def getLastSample(self):
        """Return last sample."""
        raise ValueError("getLastSample Stub invocation")

    def getLastSamples(self, number_of_entries):
        """Return n last samples."""
        raise ValueError("getLastSamples Stub invocation")

    def getVar(self, variable_name):
        """Return a value of variable of the sample or list of values for multisampling objects."""
        if self.single_entry:
            if self.objects:
                assert len(self.objects) < 2
                return getAttributeWithFailover(self.objects[0], variable_name)
        else:
            return list([getAttributeWithFailover(obj, variable_name) for obj in self.objects])
#            list_ = []
#            for obj in self.objects:
#                list_.append(getAttributeWithFailover(obj, variable_name))
#            return list_

    def getTableVar(self, table_name, row_name, column_name):
        """Return a value(s) of the cell of table or the columns."""
        if self.single_entry:
            if self.objects:
                assert len(self.objects) < 2
                return self.objects[0][table_name][row_name][column_name]
        else:
            return list([obj[table_name][row_name][column_name] for obj in self.objects])
#            list_ = []
#            for obj in self.objects:
#                list_.append(obj[table_name][row_name][column_name])
#                # yield object[table_name][row_name][column_name]
#            return list_
        
    def __getattr__(self, attr):
        return self.getVar(attr)
        
    
class MonitorSamples(Samples):
    """Sample subclass for monitor instance. Used in thresholds using other monitor data."""

    def __init__(self, name):
        self.name = name
    
    def getLastSample(self):
        """Return last sample as a Samples object."""
        store = DataStore()
        store.setWorkingDirectory(SmartMonContext().datastore_directory)
        configuration = SmartMonContext()
        storage = store.getStorage(self.name)
        
        entries = Samples()
        entries.single_entry = True
        entries.objects = storage.getLastEntries(1)
        return entries

    def getLastSamples(self, number_of_entries):
        """Return n last samples as a Samples object."""
        configuration = SmartMonContext()
        store = DataStore()
        store.setWorkingDirectory(SmartMonContext().datastore_directory)
        storage = store.getStorage(self.name)
        
        entries = Samples()
        entries.objects = storage.getLastEntries(number_of_entries)
        return entries

    def getLastSamplesForPeriod(self, amount, units):
        """Return last samples for time interval."""
        # print "Samples.getLastTime", number_of_entries, units

        store = DataStore()
        store.setWorkingDirectory(SmartMonContext().datastore_directory)
        storage = store.getStorage(self.name)
        
        entries = Samples()
        entries.objects = storage.getLastEntriesForPeriod(amount, units)
        return entries
    
    def __getattr__(self, attr):
        """Attribute-like version of getter for monitor's current sample without using getLastSample() method."""
        return self.getLastSample().getVar(attr)


def monitor(name):
    """Return monitor samplestore instance by given name."""
    return MonitorSamples(name)

    
def lastSamples(number_of_entries):
    """Return last n samples for current monitor."""
    configuration = SmartMonContext()

    store = DataStore()
    store.setWorkingDirectory(configuration.datastore_directory)     # TODO: move out
    storage = store.getStorage(configuration.monitor_name)
    
    entries = Samples()
    entries.objects = storage.getLastEntries(number_of_entries)
    return entries
    

def lastSample():
    """Return last n samples for current monitor."""
    configuration = SmartMonContext()
    entries = Samples()
    entries.single_entry = True
    entries.objects = []
    entries.objects.append(configuration.state_variables)
    return entries

        
def threesomeAnal(critical, warning, ok):
    """Return an array based of result of tree lambda functions."""
    # TODO: rename function ;)
    return critical(), warning(), ok()
    # optimized block.
    if critical():
        return True, False, False
    if warning():
        return False, True, False
    if ok():
        return False, False, True 
    return False, False, False


class MonitorEvaluator(object):
    """MonitorEvaluator class."""

    def __init__(self):
        """Constructor."""
        pass
        
    def evaluate(self, script, state_variables=None):
        """Evaluate script."""
        if state_variables is not None:
            for var in state_variables:
                vars()[var] = state_variables[var]
        elif SmartMonContext().state_variables is not None:
            for var in SmartMonContext().state_variables:
                vars()[var] = SmartMonContext().state_variables[var]
        return eval(script)
    

class  Test_evaluator(unittest.TestCase):
    def setUp(self):
        LOG_FILENAME = "./sFTP_monitor.out__"
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,)
        configuration = SmartMonContext()
        configuration.monitor_name = "test_000"
        configuration.datastore_directory = "./testdata"

    def test_object_style(self):
        self.assertEqual(len(monitor('test_000').getLastSamples(5).objects), 5)
        self.assertEqual(len(list(monitor('test_000').getLastSamples(5).getVar("SRP DM performance measurements"))), 5)
        self.assertEqual(len(list(monitor('test_000').getLastSamples(5).getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Value'))), 5)
        self.assertEqual(monitor('test_000').getLastSample().getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Value'), 391)
        self.assertEqual(avg(monitor('test_000').getLastSamples(5).getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Value')), 391)
        
    def test_threesomeAnal(self):
        self.assertEqual(threesomeAnal(lambda: True, lambda: True, lambda: False), (True, True, False)) # Too strict
        self.assertEqual(threesomeAnal(lambda: True, lambda: True, lambda: False)[0], True)
        self.assertEqual(threesomeAnal(lambda: False, lambda: True, lambda: False)[0], False)
        self.assertEqual(threesomeAnal(lambda: False, lambda: True, lambda: False)[1], True)
        self.assertEqual(threesomeAnal(lambda: False, lambda: False, lambda: True), (False, False, True))
        self.assertEqual(threesomeAnal(lambda: False, lambda: False, lambda: False), (False, False, False))

    def test_native_getters(self):
        self.assertEqual(len(monitor('testdata').getLastSamples(5).result), 5)
        self.assertEqual(sum(monitor('testdata').getLastSamples(3).result), 3)
        self.assertEqual(sum(monitor('testdata').getLastSamples(7).result), 1+2+3+4+5+6)
        self.assertEqual(monitor('testdata').getLastSample().result, 0)
        
    def test_current_state(self):
        configuration = SmartMonContext()
        configuration.monitor_name = "testdata"
        configuration.state_variables = monitor('testdata').getLastSample().objects[0]
#        self.assertEqual(configuration.state_variables.result, 0)
        self.assertEqual(lastSample().result, 0)
        self.assertEqual(sum(lastSamples(5).result), 0+1+2+3+4)

    def test_current_state_of_other_monitor_root_variables(self):
        self.assertEqual(monitor('testdata').result, 0)

    def __test_time_interval_sampling(self):
        self.assertEqual(len(monitor('testdata').getLastSamplesForPeriod(1, "days").objects), 3)
        self.assertEqual(sum(monitor('testdata').getLastSamplesForPeriod(1, "days").result), 3)
        self.assertEqual(avg(monitor('testdata').getLastSamplesForPeriod(1, "days").result), 1)
        self.assertEqual(avg(monitor('testdata').getLastSamplesForPeriod(1, "minutes").result), 0)

    def test_attribute_getter_failover(self):
        self.assertEqual(len(list(monitor('test_000').getLastSamples(5).SRP_DM_performance_measurements)), 5)
        self.assertEqual(len(list(monitor('test_000').getLastSample().SRP_DM_performance_measurements)), 19)

    def test_attribute_getter_table(self):
        configuration = SmartMonContext()
        self.assertEqual(monitor('test_000').getLastSample().getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Value'), 391)
        self.assertEqual(monitor('test_000').getLastSample().SRP_DM_performance_measurements['dmMonitor.login']['Value'], 391)
        self.assertEqual(monitor('test_000').getLastSample().SRP_DM_performance_measurements.dmMonitor_login.Value, 391)
        
    def test_multiple_group(self):
        pass

    def test_unexisted_objects(self):
        self.assertEqual(monitor('test_000').getLastSample().getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Value'), 391)
        try:
            self.assertEqual(monitor('test_000').getLastSample().getTableVar("SRP _DM performance measurements", 'dmMonitor.login', 'Value'), 391)
            self.fail("Should be risen exception when the table not found")
        except KeyError:
            pass
        try:
            self.assertEqual(monitor('test_000').getLastSample().getTableVar("SRP DM performance measurements", '_dmMonitor.login', 'Value'), 391)
            self.fail("Should be risen exception when the element not found")
        except KeyError:
            pass
        try:
            self.assertEqual(monitor('test_000').getLastSample().getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Val'), 391)
            self.fail("Should be risen exception when the column not found")
        except KeyError:
            pass

    def test_unexisted_objects_in_comparison(self):
        try:
            self.assertFalse(int(monitor('test_000').getLastSample().getTableVar("SRP DM performance measurements", 'dmMonitor.login', 'Measurement')) < 391)
            self.fail("An exception should be risen")
        except ValueError:
            pass
        
    def test_evaluator(self):
        evaluator = MonitorEvaluator()
        result = evaluator.evaluate("int(monitor('test_000').getLastSample().getTableVar('SRP DM performance measurements', 'dmMonitor.login', 'Val')) > 391", {})
        self.assertEquals(result, 6)


        
if __name__ == '__main__':
    unittest.main()
