import os, sys
import random
import time
import types
import re
try:
    import json # 2.6
    json_module = "json"
except ImportError:
    try:
        import demjson
        json_module = "demjson"
    except ImportError:
        json_module = "none"

from django.http import HttpResponse
from django.template import Context, loader
from .pyofc2 import *

datadir = os.path.dirname(sys.argv[0])
if not datadir:
    datadir = "."
sys.path.append(datadir + "/..")

from mtop import MTop
from core_datastore import DATETIME_FORMAT
from datetime import datetime


class HtmlFormatter(object):
    def fail(self, txt):
        return "<font color='red'>"+txt+"</font>"
    
    def error(self, txt):
        return "<font color='red'>"+txt+"</font>"
    
    def warn(self, txt):
        return "<font color=#8F8F00>"+txt+"</font>"
    
    def invert(self, txt):
    #    return "\033[7m"+txt+"\033[0m"
        return "<font style='background-color: black' color=#CCCCCC>"+txt+"</font>"
    
    def ok(self, txt):
        return "<font color=#308F00>"+txt+"</font>"
    
    def skip(self, txt):
        return "<font color=#6060B0>"+txt+"</font>"
    
    def home(self):
        return ""
    
    def black3(self, txt):
        return txt
    
    def black2(self, txt):
        return "\033[90m"+txt+"\033[0m"
    
    def black1(self, txt):
        return "\033[37m"+txt+"\033[0m"
    
    def black0(self, txt):
        return "\033[97m"+txt+"\033[0m"

    def monitor_name(self, txt):
        return "<a href='/mtop/monitor/"+txt+"' style='text-decoration:none'>"+txt+"</a>"

    def link(self, datetime, txt2, monitor_id):
        return "<a href=\"/mtop/monitor/"+monitor_id+"/tick/"+datetime.strftime(DATETIME_FORMAT)+"\">" + txt2 + "</a>"


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


mtop = MTop()
mtop.BASE_DATA_DIR = datadir + "/.."
mtop.init_monitors()
mtop.init_datastore()
mtop.width = 120
mtop.frm = HtmlFormatter()


def chart_data(request):
    
    if 'data' in request.GET:
        data = request.GET['data']
    else:
        data = '2,4,1,3,5,6,8,9,7'
        
    if 'cri' in request.GET:
        threshold = float(request.GET['cri'])
    else:
        threshold = None

    if 'wrn' in request.GET:
        warning_level = float(request.GET['wrn'])
    else:
        warning_level = None

    s_chunks = data.split(',')
    data_list = []
    for s_ch in s_chunks:
        data_list.append(float(s_ch))
        
    l1 = area_line() # line()
    l1.width = 2
    l1.colour = "#DFC329"
    l1.dot_size = 5
    l1.values = data_list
#    l1.fill_color = "#FFF9C9"
    l1.fill_color = "#FFFFFF"
    l1.fill_alpha = 0.3
#    l1.text = 'Metric 1'
    l1.font_size = 10
    
    chart = open_flash_chart()
    if 'max' in request.GET:
        max_value = request.GET['max']
        axis = y_axis()
        axis.max = float(max_value)
        if axis.max == 0:
            axis.max = 1
        axis.steps = axis.max/10
        chart.y_axis = axis

    if 'title' in request.GET:
        s_title = request.GET['title']
        t = title(text=s_title)
        chart.title = t
        
    if threshold:
        l2 = line()
        l2.width = 2
        l2.colour = "#FFB369"
        l2.dot_size = 0
        threshold_values = [None]*len(data_list)
        threshold_values[0] = threshold
        threshold_values[len(data_list) - 1] = threshold
        
        l2.values = threshold_values
        l2.font_size = 10
        chart.add_element(l2)
            
    if warning_level:
        l3 = line()
        l3.width = 2
        l3.colour = "#BFD6FF"
        l3.dot_size = 0
        threshold_values2 = [None]*len(data_list)
        threshold_values2[0] = warning_level
        threshold_values2[len(data_list) - 1] = warning_level
        
        l3.values = threshold_values2
        l3.font_size = 10
        chart.add_element(l3)
        
    chart.add_element(l1)
    
    return HttpResponse(chart.render())


def get_and_apply_filter(request):
    s_filter = request.GET.get('filter')

    # Simulate options
    options = AttributeDict({'filter': s_filter, 'cycle_skip_for_logs': '2', 'refresh_time': '5', 'sort': 'i', 'log_lines': '12', 'output_format': 'ascii'})
    mtop.options = options

    return s_filter


def main(request):
    template_dict = {}
    s_filter = get_and_apply_filter(request)

    mtop_output = mtop.step()
    template_dict['body'] = mtop_output
    template_dict['filter'] = s_filter

    t = loader.get_template('index.html')
    c = Context(template_dict)
    return HttpResponse(t.render(c))


def rawout(request):
    get_and_apply_filter(request)

    mtop_output = mtop.step()

    return HttpResponse(mtop_output)


class Measurement_Info(object):
    pass


def analyze_thresholds(thresholds):
    critical_levels = {}
    warning_levels = {}
    for threshold in thresholds:
        # TODO: Looks ugly        
        m = re.match(r"int\(lastSample\(\).getTableVar\(\"[.\w\s]+\", '([.\w\s]+)', 'Value'\)\) > ([.\d]+), int\(lastSample\(\).getTableVar\(\"[.\w\s]+\", '([.\w\s]+)', 'Value'\)\) > ([.\d]+)", threshold)
        if m:
            critical_levels[m.group(1)] = float(m.group(2))
            warning_levels[m.group(3)] = float(m.group(4))
            
        m = re.match(r"lastSample\(\).getVar\('([.\w\s]+)'\) > ([.\d]+), lastSample\(\).getVar\('([.\w\s]+)'\) > ([.\d]+), True", threshold)
        if m:
            critical_levels[m.group(1)] = float(m.group(2))
            warning_levels[m.group(3)] = float(m.group(4))
        
        m = re.match(r"int\(lastSample\(\).getTableVar\(\"[.\w\s]+\", '([.\w\s]+)', 'Value'\)\) > ([.\d]+)", threshold)
        if m:
            critical_levels[m.group(1)] = float(m.group(2))

        m = re.match(r"lastSample\(\).getVar\('([.\w\s]+)'\) > ([.\d]+)", threshold)
        if m:
            critical_levels[m.group(1)] = float(m.group(2))
            
    return critical_levels, warning_levels


def dump(obj):
    if json_module == "json":
        return json.dumps(obj, sort_keys=True, indent=4)
    elif json_module == "demjson":
        return demjson.encode(obj, compactly=False)
    else:
        return str(obj)
    

def monitor(request, mon_id=""):

    gchart_url = mtop.generate_gchart(mon_id)
    measurements, limits = mtop.getAllAvailableMeasurementsAsGchart(mon_id)
    
    mon_definition = mtop.cfg.getMonitorByNameWithParents(mon_id)
    # thresholds
    thresholds = []
    if isinstance(mon_definition.get('threshold'), list):
        for threshold in mon_definition['threshold']:
            thresholds.append(threshold)
    elif mon_definition.get('threshold') is not None:
        thresholds.append(mon_definition['threshold'])
    
    if isinstance(mon_definition.get('threshold_ref'), list):
        for threshold_ref in mon_definition.get('threshold_ref'):
            thresholds.append(mtop.cfg.thresholds.__getattr__(threshold_ref))
    elif mon_definition.get('threshold_ref') is not None:
        thresholds.append(mtop.cfg.thresholds.__getattr__(mon_definition.threshold_ref))
        
    criticals, warnings = analyze_thresholds(thresholds)


    measurement_infos = []
    URL_TEMPLATE = "http://chart.apis.google.com/chart?cht=lc&chd=t:%(data_csv)s&chs=450x200&chxt=y&chg=20,20,1,5&chxr=0,0,%(max_value)s&chds=0,%(max_value)s"
    for measurement in measurements:
        mgchart_url = URL_TEMPLATE % {'data_csv': measurements[measurement], 'max_value': str(limits[measurement])}
        meas_info = Measurement_Info()
        meas_info.mgchart_url = mgchart_url
        meas_info.name = measurement
        meas_info.max_value = str(limits[measurement])
        meas_info.csv = measurements[measurement]
        if measurement in criticals:
            meas_info.critical_level = criticals[measurement]
        if measurement in warnings:
            meas_info.warning_level = warnings[measurement]
            
        
        measurement_infos.append(meas_info)
        
    definition = dump(mon_definition)
   # definition = mon_definition.toString()
        

    t = loader.get_template('monitor.html')
    c = Context({
        'mon_id': mon_id,
        'gchart_url': gchart_url,
        'measurements': measurement_infos,
        'thresholds': thresholds,
        'definition': definition,
        'debug': criticals,
        'debug2': warnings
    })
    return HttpResponse(t.render(c))
        

def measurement(request, mon_id="", mes_id=""):

    measurements, limits = mtop.getAllAvailableMeasurementsAsGchart(mon_id)

    measurement_infos = []
    URL_TEMPLATE = "http://chart.apis.google.com/chart?cht=lc&chd=t:%(data_csv)s&chs=450x200&chxt=y&chg=20,20,1,5&chxr=0,0,%(max_value)s&chds=0,%(max_value)s"
    
    mgchart_url = URL_TEMPLATE % {'data_csv': measurements[mes_id], 'max_value': str(limits[mes_id])}
    meas_info = Measurement_Info()
    meas_info.mgchart_url = mgchart_url
    meas_info.name = mes_id
    meas_info.max_value = str(limits[mes_id])
    meas_info.csv = measurements[mes_id]
    
    measurement_infos.append(meas_info)

    t = loader.get_template('measurement.html')
    c = Context({
        'mon_id': mon_id,
        'mes_id': mes_id,
        'measurements': measurement_infos,
        'gchart_url': "",
    })
    return HttpResponse(t.render(c))


def map_health_to_status(health): # TODO: Move out from here
    if health >= 60:
        return "OK"
    elif health > 30:
        return "WARN"
    else:
        return "ERR"


def tick(request, mon_id="", dt=""):
    
    date_time = datetime.fromisoformat(dt)

    data_entry = mtop.getDataForMonitor(mon_id, date_time)
    if not data_entry:
        pass
    obj, dt, health, stat = data_entry
    
    outfile = None
    if 'outfile' in obj:
        outfile = obj['outfile']
        del(obj['outfile'])

    objects = dump(obj)
    
    health_stat = map_health_to_status(health)
    
    t = loader.get_template('tick.html')
    c = Context({
        'mon_id': mon_id,
        'gchart_url': "",
        'payload': str(objects),
        'status': stat,
        'health': health,
        'health_stat': health_stat,
        'date': dt,
        'outfile': outfile
    })
    return HttpResponse(t.render(c))


def doc(request, page=""):
    t = loader.get_template(page + '.html')
    c = Context({
    })
    return HttpResponse(t.render(c))
