# Create your views here.
import os, sys

datadir = os.path.dirname(sys.argv[0])
if not datadir:
    datadir = "."
sys.path.append(datadir + "/../")

from mtop import MTop, BaseFormatter


class AttributeableDictWrapper(object):
    """Table wrapper."""
    
    dictionary = None
    
    def __init__(self, dict):
        self.dictionary = dict
    
    def __getattr__(self, attr):
        return self.dictionary[attr]

def main():
    
    mtop = MTop()
    mtop.BASE_DATA_DIR = datadir + "/../"
    
    print mtop.BASE_DATA_DIR
    
    mtop.init_monitors()
    mtop.init_datastore()
    
    mtop.width = 120
    
    # Simulate options
    options = {'filter': 'ui', 'cycle_skip_for_logs': '5', 'refresh_time': '5', 'sort': 'i', 'log_lines': '0', 'output_format': 'ascii'}
    mtop.options = AttributeableDictWrapper(options)
    mtop.frm = BaseFormatter()
    str = mtop.step()
    
    print str


if __name__ == "__main__":
    print "asdfasdfasdf"
    main()
