SmartMonitor


SmartWrapper is the helper layer between ApplicationManager and custom scripts. It allows to write complex threshold, 
store statistics, invoke scripts via SSH using all authentication methods (AM have partial implementation). It have
internal console line tool for the real-time monitoring of the status of monitors managed by SmartWrapper which can 
be handy alternative to email notification.


Design and technical info
-------------------------



Requirements
------------

* Python: 2.3+
* python-paramiko: ??
* python-crypto


Installation
------------

1a. Installation of python development headers (SLES)

yast -i python-devel
yast -i python-xml


1b. Installation of python development headers (Debian/Ubuntu)

apt-get install python-dev


2. Installation of python modules 

python-demjson, python-paramiko and python-crypto are needed

You can install them manually (see section 2.1) or automatically by supplied script (see section 2.2)


2.1 Manual installation

wget http://www.amk.ca/files/python/crypto/pycrypto-2.0.1.tar.gz
wget http://www.lag.net/paramiko/download/paramiko-1.7.4.tar.gz

tar zxvf pycrypto-2.0.1.tar.gz;cd pycrypto-2.0.1;python setup.py install
tar zxvf paramiko-1.7.4.tar.gz;cd paramiko-1.7.4;python setup.py install


2.2 Automatic installation

cd ./installation
sudo sh build-dependencies.sh


Make sure that 'monitor-basedir' variable in etc/defines.conf points to actual SRP_SelfTest directory.



Directories
-----------

Typical 

./data - directory which is used as the data storage. Each file in the directory is the database for one monitor. 
	Note that filename of the file is the same as an ID of the monitor.
 
./etc - here all configuration files placed. The directory have main configuration file (smartmon.conf) and  
	additional configuration file for defines (defines.conf). Also here should be directory named "services". This
	is a start point to search all chunks recursively. (see section "Configuration")
	
./installation - scripts for installing SmartWrapper dependencies (see section "Installation")

./logs - here the wrapper stores its logs. Logs are differentiated by monitor ID, so you can find logs for YOUR 
	monitor using this pattern: "<monitor-id>.log"

./test_scripts - test scripts for checking monitors without appmanager.

./var - directory for temporary files. Can be a symlink to /tmp

There may be other directories but listed above are mandatory (it can be configurable in future releases) and
should exist.

As SmartMonitor looks for its configuration and data in a current directory, all monitors that use application 
manager have to be configured in its configuration dialogs to have current directory set to wrapper's root directory 
(for example '/opt/SRP_SelfTests'). 


Usage
-----

am.monitors.smartcontrollerwrapper.py [-m|-o|-t|-i] [--<arguments to be passed>]

options:
  -h, --help            show this help message and exit
  -oOUTPUT_FILE, --output_file=OUTPUT_FILE
                        write output to FILE
  -tLOG_FILE, --log_file=LOG_FILE
                        write logs to FILE
  -mMONITOR_NAME, --monitor=MONITOR_NAME
                        monitor name
  -iINPUT_FILE, --input_file=INPUT_FILE
                        input FILE to analyze. Default:
                        ./output/<monitor_id>.txt

As the wrapper was designed to work with configured monitors definitions, the typical usage is:

am.monitors.smartcontrollerwrapper.py -m mon-id -o ./outfile.txt 

Here: mon-id - monitor ID. A Unique name of the monitor.
      outfile.txt - file which will hold result of the monitor.


Configuration
-------------

Configuration files could be separated into several directories according to your vision of how to group all 
monitors. All chunks will be joined together before parsing. Configuration files have to be with ".conf" extension, 
in that case it will be proceed. Otherwise the file will be skipped. It's possible to do the trick to disable monitor 
definitions by renaming its conf file to the file with an extension like ".conf.bak".

For example, all these definition are equal:

Case 1:

file ./etc/services/nfs.conf

<monitor>
	id nfs-testmachine
	param1 qq
	param2 aa
<monitor>

<monitor>
	id nfs-lira
	param1 ee
<monitor>

Case 2:

file ./etc/services/nfs-testmachine.conf

<monitor>
	id nfs-testmachine
	param1 qq
	param2 aa
<monitor>

file ./etc/services/nfs-lira.conf

<monitor>
	id nfs-lira
	param1 ee
<monitor>

Or you can even place your monitors in the root configuration:

Case 3:

file ./etc/smartmon.conf

# SmartMon wrapper for AM
log-level           INFO
mail-from           vbuiel@email.nl
out-dir				./var
log-dir				./logs

<parser>
	delimiter =
    allowTables True
    columnsDelimiter |
</parser>

<monitor>
	id nfs-testmachine
	param1 qq
	param2 aa
<monitor>

<monitor>
	id nfs-lira
	param1 ee
<monitor>





Attributes
----------

* abstract yes - shows that monitor is abstract and used only as parent for other monitors

* id <name> - unique monitor id. The same identifier is used for command line option -m <name>

* base <name> - indicates that that monitor is based on properties of abstract on non-abstract monitor with id=<name>

* threshold <python eval> - script which calculates health of resource. (see section Scripts)

* threshold-ref <threshold-id> - reference to predefined threshold

* ssh <user:pass@host> - indicates that monitor will be executed remotely at host via SSH. 
	Example: root:wert@host.internal.corp

* command <command> -
* arguments <arguments> - 
* working-directory <dir> - these three parameters define what command is used to run script and what directory 
	will be working directory when the scripts will be invoked. Arguments will be appended just after the command.

* output-file <file-path> - output file of the script to be analyzed.

* timeout <seconds> - defines timeout of the script. If there will be overtime wrapper will kill the script and this 
	poll will be unsuccessful.

* copy-original <yes|no> - indicates that into the output file will be included original unfiltered information.

* interval <seconds> - WIP

* enabled <true|false> - default is enabled.

* execution-time <yes|no> - add execution time into output file in the form of "wrp_execution_time=5.56". 
	Units: seconds.



Scripts
-------

Scripts are based on python (they are actually python), so your scripts can do everything that python can.

Examples:




Scripts cookbook
----------------

Rise event in order if there were three non-zero results:

sum(lastSamples(3).result)>0



mtop
----

MTop - is an utility for the real-time tracking of wrapper status. It show current status of monitors managed 
by SmartWrapper, graph of statuses for 50 last polls, date of the last poll. Also it analyzes log file (both 
wrapper's and custom monitor's) and shows last n lines with error messages. UI was inspired by 'top' utility.

Typical screen of MTop looks like:

<code>
SmartMon terminal control panel. WIP version. 2009-07-31 13:45:18.779669
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------Clear : -	Warning : w	Error : e
MID                          	%% 	STAT	GRAPH                                           	LAST POLL                                                                                                                   
ui-crater-bademo10           	100	OK	--------------------------------------------------	2009-07-21 13:59:00	(- 9 days)
ui-crater-bademo9            	100	OK	--------------------------------------------------	2009-07-21 13:54:05	(- 9 days)
nfs-cepheus                  	40	WARN	--w-w--------------------------ww------w---------w	2009-07-31 13:44:02	(- 1 minutes)
nfs-lepus                    	100	OK	---------ww-------------------wwwe-----w----------	2009-07-31 13:43:03	(- 2 minutes)
nfs-vela                     	100	OK	-------w-w--------------------wwwe-----w----------	2009-07-31 13:43:03	(- 2 minutes)
nfs-lynx                     	100	OK	--w----------------w-----------ww------w----------	2009-07-31 13:43:04	(- 2 minutes)
nfs-tanana                   	100	OK	----------------------------------------w--w------	2009-07-31 13:40:01	(- 5 minutes)
nfs-reno                     	100	OK	-------------------------------w---------------w--	2009-07-31 13:44:03	(- 1 minutes)
nfs-parlin                   	40	WARN	------------------------w-------w----------------w	2009-07-31 13:40:00	(- 5 minutes)
nfs-lira                     	0	ERR	eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee	2009-07-31 13:44:03	(- 1 minutes)
sftp-alden-qaumgsmoke1       	40	WARN	wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww	2009-07-31 13:41:05	(- 4 minutes)
srp-crater-bademo10          	0	ERR	eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee	2009-07-31 13:43:04	(- 2 minutes)
ldap-dev2.srv.soneengroup.led	100	OK	--------------------------------------------------	2009-07-31 13:44:05	(- 1 minutes)
ldap-dev1.srv.soneengroup.led	40	WARN	wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww	2009-07-31 13:44:01	(- 1 minutes)
maven                        	100	OK	--------------------------------------------------	2009-07-31 13:42:03	(- 3 minutes)

Last wrapper errors: (cached)
2009-07-31 17:44:58,386 ERROR    Return code: 126. Please review what could this means
2009-07-31 17:44:19,195 ERROR    Return code: 126. Please review what could this means
2009-07-31 17:43:46,886 ERROR    Return code: 1. Please review what could this means
2009-07-31 17:43:26,678 ERROR    Unhandled exception detected!!! Output file may not be written.
2009-07-31 17:43:26,678 ERROR    'NoneType' object has no attribute 'base'
2009-07-31 17:40:11,773 ERROR    Unhandled exception detected!!! Output file may not be written.

Last monitors' errors: (cached)
2009-07-31 17:44:52,155 ERROR    ERROR: Can't touch file on nfs filesystem. Expected: 0. Actual: 1
2009-07-31 17:44:24,238 ERROR    ERROR: Can't touch file on nfs filesystem. Expected: 0. Actual: 1
2009-07-31 17:41:57,155 ERROR    ERROR: file './UMG/Outbound/License/convert' doesn't exist or not accessible
2009-07-31 17:41:56,938 ERROR    ERROR: file './UMG/Outbound/Subledger/flglaccount/convert' doesn't exist or not accessible
2009-07-31 17:41:56,722 ERROR    ERROR: file './UMG/Outbound/Subledger/paymentdetail/convert' doesn't exist or not accessible
2009-07-31 17:41:56,614 ERROR    ERROR: file './UMG/Outbound/Subledger/vendor/convert' doesn't exist or not accessible
</code>



mtop invocation
---------------

MTop is an python application so it requires python. (It don't use anything that not listed in "Requirements" 
sections, so you can relax about that.) You can run it by ./mtop.sh bash script




Command line options:

	"-n" or "--log-lines"           - Number of lines to be printed for errors got from log files. Set to 0 to 
		disable log analysis. Default=10
	"-r" or "--refresh-time"        - UI refresh time (in seconds). Default=5
	"-c" or "--refresh-skip-cycles" - UI refresh cycles to be skipped before heavyweight analyze operations 
		(non-zero positive number 1,2...). Default=5

Note the --refresh-skip-cycles parameter. As logs files could be really huge the time of parsing and sorting 
may take a long time and moreover it loads machine's resources, so such a heavy operations may perform rarely 
than UI refresh. This parameter defines a divisor for UI refresh for such heavy-weight operations. If divisor
is equal to 10 that means that log analyze will be performed only once of 10 refresh cycles. 


