import unittest
import sys, os
from core_eval import *
from core_parser import *
from core_configuration import get_configuration, SchemalessConfig
from core_expressions import last


TABLE_MEASUREMENTS_OUT = """<--table SRP DM performance measurements starts-->
Measurement|Value|Units|Result
dmMonitor.login|391|milliseconds|OK
account.search|1123|milliseconds|OK
account.open|257|milliseconds|OK
contract.search|155|milliseconds|OK
contract.open|98|milliseconds|OK
product.search|799|milliseconds|OK
product.open|545|milliseconds|OK
open.page.mySRP|234|milliseconds|OK
open.page.myProcesses|22|milliseconds|OK
open.page.searchSalesBatch|189|milliseconds|OK
open.page.searchSalesLines|318|milliseconds|OK
open.page.search.artistContract|111|milliseconds|OK
open.page.search.crossingLicense|86|milliseconds|OK
open.page.search.product|144|milliseconds|OK
open.page.search.account|275|milliseconds|OK
open.page.search.tva|41|milliseconds|OK
open.page.SystemReferences|71|milliseconds|OK
open.page.reportSubscription|181|milliseconds|OK
dmMonitor.logout|23|milliseconds|OK
<--table SRP DM performance measurements ends-->
"""

'''
Evaluator tests. See specific tests in core_eval module
'''
class Test_evaluator_basic(unittest.TestCase):

    def setUp(self):
        LOG_FILENAME = "./sFTP_monitor.out__"
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,)
        configuration = SmartMonContext()
        configuration.monitor_name = "testdata"

    def test_evaluation(self):
        evaluator = MonitorEvaluator()
        result = evaluator.evaluate("1.0 + 2.0", None)
        self.assertEqual(result, 3.0)

    def test_evaluation_complex(self):
        evaluator = MonitorEvaluator()
        result = evaluator.evaluate("param>3", {"param" : 0, "param2" : "OK"})
        self.assertEqual(result, False)

    def test_evaluation_functions(self):
        evaluator = MonitorEvaluator()
        result = evaluator.evaluate("sum(lastSamples(4).result)", {"result" : 0, "param2" : "OK"})
        self.assertEqual(result, 6)
        
    def test_DSL_style(self):
        # WIP
        last(5).entries().of('result')
#        monitor('aaa').getLastEntries(5)
        
    def test_eval_function(self):
        self.assertEqual(sum(lastSamples(4).result), 6)
        

'''
Datastore tests
'''
class Test_datastore(unittest.TestCase):
    def setUp(self):
        LOG_FILENAME = "./sFTP_monitor.out"
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO)
    
    def test_datastore(self):
        store = DataStore()
        store.setWorkingDirectory("./testdata")

    def test_entry_put(self):
        store = DataStore()
        store.setWorkingDirectory("./testdata")
        storage = store.getStorage("test")

        obj = storage.getLastEntries(10)
        self.assertEqual(len(obj), 0)

        t = 12345, 54321, 'hello!'
        storage.putEntry(t, 10)

        obj = storage.getLastEntries(0)
        self.assertEqual(len(obj), 0)

        obj = storage.getLastEntries(1)
        self.assertEqual(len(obj), 1)

        obj = storage.getLastEntries(10)
        self.assertEqual(len(obj), 1)

        store.dropStorage("test")


    def test_pass_none_as_storage_name(self):
        try:
            store = DataStore()
            store.setWorkingDirectory("./testdata")
            storage = store.getStorage(None)
        except ValueError:
            pass
        else:
            self.fail("Expected a ValueError")


    def test_empty_data(self):
        store = DataStore()
        store.setWorkingDirectory("./testdata")
        storage = store.getStorage("empty")
        obj = storage.getLastEntries(5)
        self.assertEqual(len(obj), 0)

        store.dropStorage("empty")


    def test_last_time(self):
        store = DataStore()
        store.setWorkingDirectory("./testdata")
        storage_empty = store.getStorage("empty")
        obj = storage_empty.getLastEntries(5)
        self.assertEqual(len(obj), 0)
        self.assertEqual(storage_empty.getLastTime(), None)

        storage_test = store.getStorage("test")
        t = 12345, 54321, 'hello!'
        storage_test.putEntry(t, 10)

        obj = storage_test.getLastEntries(5)
        self.assertNotEqual(storage_test.getLastTime(), None)

        store.dropStorage("empty")
        store.dropStorage("test")


    def test_entry_put_and_read_extended(self):
        store = DataStore()
        store.setWorkingDirectory("./testdata")
        storage = store.getStorage("test")

        t = 12345, 54321, 'hello!'
        storage.putEntry(t, 10)

        obj = storage.getLastEntriesWithResult(1)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0][2], 10)

        storage.putEntry(t, -99)
        obj = storage.getLastEntriesWithResult(1)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0][2], -99)

        storage.putEntry(t)
        obj = storage.getLastEntriesWithResult(1)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0][2], 0)

        store.dropStorage("test")


'''
Output parser
'''
class Test_outputparser(unittest.TestCase):

    def setUp(self):
        LOG_FILENAME = "./sFTP_monitor.out__"
        logging.basicConfig(filename=LOG_FILENAME, level=logging.INFO,)

    def test_null(self):
        try:
            parser = MonitorOutputParser()
            parser.parse()
        except ValueError:
            pass
        else:
            self.fail("Expected a NameError")
            
    def test_file_outputparse(self):
        parser = MonitorOutputParser()
        parser.setDelimiter("=")
        parser.setAllowTables(False)
        parser.setColumnsDelimiter("")
        filename = "./testdata/outfile/sftp_alden.led-22_out.txt"
        res = parser.parse(filename)
        self.assertEqual(res["message"], 'OK')
        self.assertEqual(res["result"], 1)
        
    def test_table_output(self):
        parser = MonitorOutputParser()
        parser.setDelimiter("=")
        parser.setAllowTables(True)
        parser.setColumnsDelimiter("|")
        parser.setColumnKey("Measurement")
        parser.setTableHeader("<--table (.+) starts-->")
        parser.setTableFooter("<--table (.+) ends-->")
        res = parser.parse(lines=TABLE_MEASUREMENTS_OUT.splitlines())
        self.assertEqual(len(res['SRP DM performance measurements']), 19)
        table = res['SRP DM performance measurements']
        self.assertEqual(len(table['open.page.search.account']), 4)
        self.assertEqual(table['open.page.search.account']['Units'], 'milliseconds')
        self.assertEqual(table['open.page.search.account']['Result'], 'OK')
        self.assertEqual(table['open.page.search.account']['Value'], 275)
        self.assertEqual(table['open.page.search.account']['Measurement'], 'open.page.search.account')

    def test_regex_parsing(self):
        parser = MonitorOutputParser()
        parser.setRegex([r"Test (?P<key>[.\w]+)\s+(SUCCEED in (?P<value>[.\d]+)sec)",
                         r"Test (?P<key>[.\w]+)\s+(SUCCEED with (?P<value>.+))",
                         r"Test (?P<key>[.\w]+)\s+(?P<value>FAILED .+)"])
        parser.setAllowTables(False)
        parser.setColumnsDelimiter("")
        filename = "./testdata/outfile/checker_output.txt"
        res = parser.parse(filename)
        
        self.assertEqual(res["startSession"], 0)
        self.assertEqual(res["login"], 0)
        self.assertEqual(res["service.reports.generate.oltp.report"], 0)
        self.assertEqual(res["service.reports.generate.dw.report"], "WARNING:Report instance ID=-1. DW Reports aren't enabled on the instance.")
        self.assertEqual(res["service.dw.status.service.dw.status.read"], "WARNING:DW status=null. DW is not installed.")
        self.assertEqual(res["ui.about.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        
        self.assertEqual(res["ui.mySRP.navigateToPage"], 0.035)
        self.assertEqual(res["ui.myProcesses.navigateToPage"], 1.257)
        self.assertEqual(res["ui.myProcesses.search"], 0.974)
        self.assertEqual(res["ui.myProcesses.checkSearchResult"], 0)
        self.assertEqual(res["ui.salesBatches.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.salesLines.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.artistContract.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.crossingLicense.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.product.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.account.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.tva.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.users.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["ui.loggedInUsers"], "FAILED due to error:java.lang.reflect.InvocationTargetException")
        self.assertEqual(res["ui.references.assignment.navigateToPage"], 0.065)
        self.assertEqual(res["ui.reportSubscription.navigateToPage"], "FAILED due to error:java.lang.NullPointerException")
        self.assertEqual(res["logout"], 0)
#Result=FAILED in 2.331sec.
        

class Test_configuration(unittest.TestCase):

    def setUp(self):
        global cfg
        cfg = get_configuration()

    def test_getByName(self):
        check = cfg.getMonitorByName("testMonitor")
        self.assertEqual(check.host, "crux.soneengroup.led")

    def test_getByNameBase(self):
        check = cfg.getMonitorByName("nfs")
        self.assertEqual(check.id, "nfs") 

    def test_getAllMonitors(self):
        check = cfg.getMonitorsIds()
        self.assertTrue(len(check) > 16) 

    def test_getByNameWithParent(self):
        check = cfg.getMonitorByNameWithParents("nfs-lira")
        self.assertTrue(isinstance(type(check), SchemalessSection.__class__))
        self.assertEqual(check.id, "nfs-lira") 
#        print check.toString()

    def test_getByNameUnexistingMonitor(self):
        check = cfg.getMonitorByName("_unexisting_monitor_")
        self.assertTrue(isinstance(check, None.__class__))

    def test_substitution(self):
        check = cfg.getMonitorByName("testMonitor")
        self.assertEqual(check.command, '/cygdrive/c/SRP_monitoring/SRP_SelfTests/output/nfs_lira.soneengroup.led_out.txt')
        
    def test_subst_bootstrap(self):
        from ZConfig.schemaless import loadConfigFile
        f = open("./etc/defines.conf", "r")
        config = loadConfigFile(f)
        print((config['monitor-basedir-crux']))

    def test_parametrized_monitors(self):
        check = cfg.getMonitorByName("testMonitorParam?crux,6440")
        print(type(check))
        self.assertEqual(check.host, "your.host.com")
        self.assertEqual(check.ssh, "root:pass@your.host.com")
        #TODO: validate number of arguments

    def test_re(self):
        str = "root:Ab54$#@%1.host.com"
        m = re.match(r'.*%[0-9]', str)
        if not m:
            self.fail("Regexp isn't working")


class Test_functional(unittest.TestCase):
    def test_baselining_expression_from_table_output(self):
        parser = MonitorOutputParser()
        parser.setDelimiter("=")
        parser.setAllowTables(True)
        parser.setColumnsDelimiter("|")
        parser.setColumnKey("Measurement")
        parser.setTableHeader("<--table (.+) starts-->")
        parser.setTableFooter("<--table (.+) ends-->")
        res = parser.parse(lines=TABLE_MEASUREMENTS_OUT.splitlines())

        store = DataStore()
        store.setWorkingDirectory("./testdata")
        storage = store.getStorage("test_000")
        storage.putEntry(res, 100)

    def test_baselining_expression_from_table_output_loading(self):
        configuration = SmartMonContext()
        configuration.monitor_name = "test_000"

        evaluator = MonitorEvaluator()
#        threshold_script = "last(5)"
#        result = evaluator.evaluate(threshold, res)

#        result = evaluator.evaluate("sum(lastEntries('SRP DM performance measurements.open.page.reportSubscription', 4))")
#        print result
#        self.assertEquals(result, 6)

    def test_delta(self):
        import time
        before = time.time()
        time.sleep(1)
        after = time.time()
        print("////" + "%.2f seconds" % (after - before))
        print(sys.path)
        
    def test_time(self):
        from datetime import datetime, timedelta
        
        DATETIME_FORMAT = "%Y-%m-%d,%H:%M:%S"
        
        str_dt = "2009-10-27,14:45:24"
        
        dt = datetime.strptime(str_dt, DATETIME_FORMAT)
        
        str_dt_new = dt.strftime(DATETIME_FORMAT)
        self.assertEqual(str_dt,str_dt_new)

        


if __name__ == '__main__':
    unittest.main()
