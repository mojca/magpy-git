import sys, os, struct
from twisted.python import log
try: # version > 0.8.0
    from autobahn.wamp1.protocol import WampClientProtocol
except:
    from autobahn.wamp import WampClientProtocol
# For converting Unicode text
import collections
# Timing
from datetime import datetime, timedelta
# Database
import MySQLdb

try:
    import magpy.stream as st
    from magpy.database import stream2db
    from magpy.opt import cred as mpcred
    from magpy.transfer import scptransfer
except:
    sys.path.append('/home/leon/Software/magpy/trunk/src')
    import stream as st
    from database import stream2db
    from opt import cred as mpcred
    from transfer import scptransfer

clientname = 'default'
s = []
o = []
marcospath = ''

IDDICT = {0:'clientname',1:'time',2:'date',3:'time',4:'time',5:'coord',
                10:'f',11:'x',12:'y',13:'z',14:'df',
                30:'t1',31:'t1',32:'t2',33:'var1',34:'t2',40:'var2',60:'var2',61:'var3',62:'var4'} 

MODIDDICT = {'env': [1,30,33,34], 'ow': [1,30,33,60,61,62], 'lemi': [1,4,11,12,13,31,32] ,'pos': [1,4,10,14,40], 'cs': [1,10]}

UNITDICT = {'env': ['degC','percent','degC'], 'ow': ['degC','percent','V','V','V'], 'lemi': ['nT','nT','nT','degC','degC'] ,'pos': ['nT','nT','index'], 'cs': ['nT']}

NAMEDICT = {'env': ['T','rh','Dewpoint'], 'ow': ['T','rh','VDD','VAD','VIS'], 'lemi': ['x','y','z','Ts','Te'] ,'pos': ['f','df','errorcode'], 'cs': ['f']}

def sendparameter(cname,cip,marcospath,op,sid,sshc,sensorlist,owlist,pd,dbc=None):
    print "Getting parameters ..." 
    global clientname
    clientname = cname
    global clientip
    clientip = cip
    global output      # desired storage type - "file" or "db"
    output = op
    global stationid   # Station code
    stationid = sid
    global sshcred     # List containing credentials for scp transfer
    sshcred = sshc
    global o           # List containing one wire information and ids
    o = owlist
    global s           # List containing sensor information and ports
    s = sensorlist
    global destpath    # String for storing data - used for getting new sensor data for db upload and for file saving
    destpath = marcospath
    global printdata   # BOOL for testing purpose - prints received data to screen
    printdata = pd
    if output == 'db':
        if not dbc:
            log.msg('collectors owclient: for db output you need to provide the credentials as last option')
        global dbcred
        dbcred = dbc
    print "Parameters transfered"
    return    

def timeToArray(timestring):
    # Converts time string of format 2013-12-12T23:12:23.122324
    # to an array similiat to a datetime object
    try:
        splittedfull = timestring.split(' ')
        splittedday = splittedfull[0].split('-')
        splittedsec = splittedfull[1].split('.')
        splittedtime = splittedsec[0].split(':')
        datearray = splittedday + splittedtime
        datearray.append(splittedsec[1])
        datearray = map(int,datearray)
        return datearray
    except:
        log.msg('collectors owclient: Error while extracting time array')
        return []

def dataToFile(outputdir, sensorid, filedate, bindata, header):
    # File Operations
    try:
        path = os.path.join(outputdir,sensorid)
        # outputdir defined in main options class
        if not os.path.exists(path):
            os.makedirs(path)
        savefile = os.path.join(path, sensorid+'_'+filedate+".bin")
        if not os.path.isfile(savefile):
            with open(savefile, "wb") as myfile:
                myfile.write(header + "\n")
                myfile.write(bindata + "\n")
        else:
            with open(savefile, "a") as myfile:
                myfile.write(bindata + "\n")
    except:
        log.msg('collectors owclient: Error while saving file')        

class PubSubClient(WampClientProtocol):
    """
    Class for OneWire communication
    """ 
    def onSessionOpen(self):
        print "Starting"
        global clientname
        global clientip
        global o
        global s
        global destpath
        global printdata
        global output
        global module
        global stationid
        global dbcred
        global sshcred
        log.msg("Starting " + clientname + " session")
        # TODO Make all the necessary parameters variable
        # Basic definitions to change
        self.stationid = stationid
        self.output = output
        self.sensorid = ''
        self.sensortype = ''
        self.sensorgroup = ''
        self.module = ''
        self.typ = ''
        #self.output = output # can be either 'db' or 'file', if not db, then file is used
        # Open database connection
        self.db = None
        self.cursor = None
        if not output == 'file':
            log.msg("collectors client: Connecting to DB ...")
            self.db = MySQLdb.connect(dbcred[0],dbcred[1],dbcred[2],dbcred[3] )
            # prepare a cursor object using cursor() method
            self.cursor = self.db.cursor()
            log.msg("collectors client: ... DB successfully connected ")
        # Initiate subscriptions
        self.line = []
        for row in s:
            module = row[0]
            log.msg("collectors client: Starting subscription for %s" % module)
            self.subscribeInst(self.db, self.cursor, clientname, module, output)

    def subscribeOw(self, client, output, module, owlist):
        """
        Subscribing to all Onewire Instruments
        """
        self.prefix(module, "http://example.com/" + client +"/"+module+"#")
        if output == 'db':        
            # -------------------------------------------------------
            # A. Create database input 
            # -------------------------------------------------------
            # ideal way: upload an already existing file from moon for each sensor
            # check client for existing file:
            for row in owlist:
                subs = True
                print "collectors owclient: Running for sensor", row[0]
                # Try to find sensor in db:
                sql = "SELECT SensorID FROM SENSORS WHERE SensorID LIKE '%s%%'" % row[0]
                try:
                    # Execute the SQL command
                    self.cursor.execute(sql)
                except:
                    log.msg("collectors owclient: Unable to execute SENSOR sql")
                try:
                    # Fetch all the rows in a list of lists.
                    results = self.cursor.fetchall()
                except:
                    log.msg("collectors owclient: Unable to fetch SENSOR data from DB")
                    results = []
                if len(results) < 1:
                    # Initialize e.g. ow table
                    log.msg("collectors owclient: No sensors registered so far - Getting file from moon and uploading it")
                    # if not present then get a file and upload it
                    #destpath = [path for path, dirs, files in os.walk("/home") if path.endswith('MARCOS')][0]
                    day = datetime.strftime(datetime.utcnow(),'%Y-%m-%d')
                    destfile = os.path.join(destpath,'MoonsFiles', row[0]+'_'+day+'.bin') 
                    datafile = os.path.join('/srv/ws/', clientname, row[0], row[0]+'_'+day+'.bin')
                    try:
                        log.msg("collectors owclient: Downloading data: %s" % datafile)
                        scptransfer(sshcred[0]+'@'+clientip+':'+datafile,destfile,sshcred[1])
                        stream = st.read(destfile)
                        log.msg("collectors owclient: Reading with MagPy... Found: %s datapoints" % str(len(stream)))
                        stream.header['StationID'] = self.stationid
                        stream.header['SensorModule'] = 'OW' 
                        stream.header['SensorType'] = row[1]
                        if not row[2] == 'typus':
                            stream.header['SensorGroup'] = row[2] 
                        if not row[3] == 'location':
                            stream.header['DataLocationReference'] = row[3]
                        if not row[4] == 'info':
                            stream.header['SensorDescription'] = row[4]
                        stream2db(self.db,stream)
                        log.msg("collectors owclient: Stream uploaded successfully")
                    except:
                        log.msg("collectors owclient: Could not upload data to the data base - subscription to %s failed" % row[0])
                        subs = False
                else:
                    log.msg("collectors owclient: Found sensor(s) in DB - subscribing to the highest revision number")
                if subs:
                    subscriptionstring = "%s:%s-value" % (module, row[0])
                    print "collectors owclient: Subscribing (directing to DB): ", subscriptionstring
                    self.subscribe(subscriptionstring, self.onEvent)
        elif output == 'file':
            for row in o:
                print "collectors owclient: Running for sensor", row[0]
                subscriptionstring = "%s:%s-value" % (module, row[0])
                print "collectors owclient: Subscribing (directing to file): ", subscriptionstring
                self.subscribe(subscriptionstring, self.onEvent)

    def subscribeSensor(self,client,output,module,sensorshort,sensorid):
        """
        Subscribing to Sensors:
        principally any subscrition is possible if the subscription string is suppported by the moons protocols
        """
        self.prefix(module, "http://example.com/" + client +"/"+module+"#")
        if output == 'db':
            # -------------------------------------------------------
            # 1. Get available Sensors - read sensors.txt
            # -------------------------------------------------------
            # Try to find sensor in db:
            sql = "SELECT SensorID FROM SENSORS WHERE SensorID LIKE '%s%%'" % sensorid
            try:
                # Execute the SQL command
                self.cursor.execute(sql)
            except:
                log.msg("collectors client: Unable to execute SENSOR sql")
            try:
                # Fetch all the rows in a list of lists.
                results = self.cursor.fetchall()
            except:
                log.msg("collectors client: Unable to fetch SENSOR data from DB")
                results = []
            if len(results) < 1:
                # if not present then get a file and upload it
                log.msg("collectors client: No sensors registered so far - Getting data file from moon and uploading it using stream2db")
                day = datetime.strftime(datetime.utcnow(),'%Y-%m-%d')
                destfile = os.path.join(destpath,'MoonsFiles', sensorid+'_'+day+'.bin') 
                datafile = os.path.join('/srv/ws/', clientname, sensorid, sensorid+'_'+day+'.bin')
                try:
                    log.msg("collectors client: Downloading data: %s" % datafile)
                    scptransfer(sshcred[0]+'@'+clientip+':'+datafile,destfile,sshcred[1])
                    stream = st.read(destfile)
                    log.msg("collectors client: Reading with MagPy... Found: %s datapoints" % str(len(stream)))
                    stream.header['StationID'] = self.stationid
                    stream.header['SensorModule'] = sensorshort
                    try:
                        stream.header['SensorRevision'] = sensorid[-4:]
                    except:
                        log.msg("collectors client: Could not extract revision number for %s" % sensorid)
                        pass
                    try:
                        stream.header['SensorSerialNum'] = sensorid.split('_')[-2]
                    except:
                        log.msg("collectors client: Could not extract serial number for %s" % sensorid)
                        pass
                    stream2db(self.db,stream)
                except:
                    log.msg("collectors client: Could not upload data to the data base - subscription failed")
            else:
                log.msg("collectors client: Found sensor(s) in DB - subscribing to the highest revision number")
            subscriptionstring = "%s:%s-value" % (module, sensorid)
            print "collectors sensor client: Subscribing: ", subscriptionstring
            self.subscribe(subscriptionstring, self.onEvent)
        elif output == 'file':
            for row in o:
                print "collectors client: Running for sensor", sensorid
                subscriptionstring = "%s:%s-value" % (module, sensorid)
                self.subscribe(subscriptionstring, self.onEvent)


    def subscribeInst(self, db, cursor, client, mod, output):
        """
        Main Method for Subscribing:
        calls subscribeSensor and subscribeOw 
        """
        sensshort = mod[:3]
        if sensshort in ['GSM','POS','G82']:
            self.typ = 'f'
        elif sensshort in ['LEM','FGE']:
            self.typ = 'xyz'
        elif sensshort in ['ENV']:
            self.typ = 'env'
        else:
            self.typ = 'unknown'
        if sensshort == 'G82':
            module = 'cs'
        else:
            module = sensshort.lower()
        self.module = module
        if module == 'ow':
            if not len(o) > 0:
                log.msg('collectors client: No OW sensors available')
            else:
                log.msg('Subscribing all OneWire Sensors ...')
                self.subscribeOw(client,output,module,o)
        else:
            self.subscribeSensor(client,output,module,sensshort,mod)
   
       
    def convertUnicode(self, data):
        # From RichieHindle
        if isinstance(data, unicode):
            return str(data)
        elif isinstance(data, collections.Mapping):
            return dict(map(self.convertUnicode, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(self.convertUnicode, data))
        else:
            return data
 
    def onEvent(self, topicUri, event):
        eventdict = self.convertUnicode(event)
        time = ''
        eol = ''
        try:
            sensorid = topicUri.split('/')[-1].split('-')[0].split('#')[1]
            module = topicUri.split('/')[-1].split('-')[0].split('#')[0]
            #print sensorid, module
            if eventdict['id'] == 99:
                eol = eventdict['value']
            if eol == '':
                if eventdict['id'] in MODIDDICT[module]: # replace by some eol parameter
                     self.line.append(eventdict['value'])
            else:
                paralst = []
                for elem in MODIDDICT[module]:
                    var = IDDICT[elem]
                    if var == 'time' and time in paralst:
                        var = 'sectime'
                    paralst.append(var)

                if printdata:
                    print "Received from %s: %s" % (sensorid,str(self.line))

                if self.output == 'file':
                    # missing namelst, unitlst and multilst - create dicts for that based on STANDARD
                    packcode = '6hL'
                    multiplier = 100000
                    namelst = [elem for elem in NAMEDICT[module]]
                    unitlst = [elem for elem in UNITDICT[module]]
 
                    if module == 'ow':
                        # TODO
                        if not len(self.line) == len(paralst):
                            if len(self.line) == 2:
                                paralst = ['time','t1']
                                namelst = ['T']
                                unitlst = ['degC']
                            elif len(self.line) == 5:
                                paralst = ['time','t1','var1','var2','var3','var4']
                                namelst = ['T','RH_P','VDD','VAD','VIS']
                                unitlst = ['degC','percent_mBar','V','V','V']
                        # check length of paralst and self.line
                        else:
                            pass

                    keylst = paralst[1:]
                    packcode = packcode + 'l'*len(keylst)
                    multilst = [multiplier]*len(keylst)

                    if not len(self.line) == len(paralst):
                        # Output only for testing purpose if you dont want to smash your logs
                        #log.msg("ERRRRRRRRRRRRRRRRRRRRROR")
                        self.line = []
                    else:
                        for i, elem in enumerate(self.line):
                            if i == 0:
                                datearray = timeToArray(self.line[0])
                            else:
                                datearray.append(int(self.line[i]*multiplier))
                        day = datetime.strftime((datetime.strptime(self.line[0],"%Y-%m-%d %H:%M:%S.%f")),'%Y-%m-%d')
                        self.line = []
                        try:
                            header = "# MagPyBin %s %s %s %s %s %s %d" % (sensorid, str(keylst), str(namelst), str(unitlst), str(multilst), packcode, struct.calcsize(packcode))
                            data_bin = struct.pack(packcode,*datearray)
                            dataToFile(os.path.join(destpath,'MoonsFiles'), sensorid, day, data_bin, header)
                        except:
                            #log.msg("error")
                            pass
                else:
                    """
                    Please note:
                    Data is always automatically appended to datainfoid 0001 
                    """
                    if module == 'ow':
                        # DB request is necessary as sensorid has no revision information
                        sql = "SELECT SensorID, SensorGroup, SensorType FROM SENSORS WHERE SensorID LIKE '%s%%'" % sensorid
                        self.cursor.execute(sql)
                        results = self.cursor.fetchall()
                        sid = results[-1][0]
                        sgr = results[-1][1]
                        sty = results[-1][2]
                        datainfoid = sid+'_0001'
                        if sty == 'DS18B20':
                            paralst = ['time','t1']
                        elif sty == 'DS2438':
                            if sgr == 'humidity':
                                paralst = ['time', 't1', 'var1', 'var2', 'var3', 'var4']
                            elif sgr == 'pressure':
                                paralst = ['time', 't1', 'var1', 'var2', 'var3', 'var4']
                            else:
                                paralst = ['time', 't1', 'var1', 'var2', 'var3', 'var4']
                        self.typ = 'ow'
                    else:
                        datainfoid = sensorid+'_0001'
                    
                    # define insert from provided param
                    parastr = ', '.join(paralst)
                    # separate floats and string        
                    nelst = []
                    for elem in self.line:
                        if isinstance(elem, str):
                            elem = "'"+elem+"'"
                        nelst.append(elem)
                    linestr = ', '.join(map(str, nelst))
                    sql = "INSERT INTO %s(%s, flag, typ) VALUES (%s, '0000000000000000-', '%s')" % (datainfoid, parastr, linestr, self.typ)
                    #print "!!!!!!!!!!!!!!!! SQL !!!!!!!!!!!!!!", sql
                    self.line = []
                    # Prepare SQL query to INSERT a record into the database.
                    try:
                        # Execute the SQL command
                        self.cursor.execute(sql)
                        # Commit your changes in the database
                        self.db.commit()
                    except:
                        # No regular output here. Otherwise log-file will be smashed
                        #log.msg("client: could not append data to table")
                        # Rollback in case there is any error
                        self.db.rollback()
        except:
            pass

