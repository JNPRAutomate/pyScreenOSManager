
#Create argument parser
parser = argparse.ArgumentParser(description="Gather options from the user")
parser.add_argument("--output", dest="output", action="store_true",help="Specify if you want to print output to standard out. Defaults to printing output.")
parser.add_argument("--no-output", dest="output", action="store_false",help="Specify if you do not want to print output to standard out.")
parser.add_argument("--clear-session", dest="clear_session", action="store_true",help="Clears all other admin sessions. Ensure the successful completion of the script.")
parser.set_defaults(clear_session=False)
parser.set_defaults(output=True)
parser.add_argument("--log",dest="log",default="",help="Specify the file name where to save the output to.")
parser.add_argument("--log-level",dest="logLevel",default="0",metavar="LOGLEVEL",help="Specify the verbosity of logging. Default 0 provides basic logging. Setting log level to 1 provides max output.")
parser.add_argument("--csv", dest="hostCSVFile", default="",metavar="CSVFile",help="Specify the CSV file to read hosts from.")
parser.add_argument("--host", dest="host", default="",metavar="HOST",help="Specify single host to connect to. Can not be used with --csv.")
parser.add_argument("--username", dest="username", default="netscreen",metavar="USERNAME",help="Specify the default username to use when not specified within the csv.")
parser.add_argument("--password", dest="password", default="netscreen",metavar="PASSWORD",help="Specify the default password to use when not specified within the csv.")
parser.add_argument("--password-secure", dest="passwordSecure", action="store_true", help="Be prompted for the the default password.")
args = parser.parse_args()

userPassword = ""
verboseLogging = False

#check for secure password
if args.passwordSecure == True:
    password = getpass.getpass()
    userPassword = password
else:
    userPassword = args.password

#check for logging level
if args.logLevel == "0":
    verboseLogging = False
elif args.logLevel == "1":
    verboseLogging = True

logger = OutputLogger(args.output,args.log)
logger.addPrefix(socket.gethostname())

if args.hostCSVFile != "": #check if singular hosts are specified

    hp = HostParser(args.hostCSVFile)
    if args.output:
        if len(hp.hostList) > 1:
            logger.log("Found %s hosts in %s CSV file. Starting stats gathering." % (len(hp.hostList),args.hostCSVFile),True)
        elif len(hp.hostList) == 0:
            logger.log("Found %s hosts in %s CSV file. No hosts to gather stats from." % (len(hp.hostList),args.hostCSVFile),True)
        else:
            logger.log("Found %s hosts in %s CSV file. Starting stats gathering." % (len(hp.hostList),args.hostCSVFile),True)

    for item in hp.getHosts():
        if item["username"] == "":
            item["username"] = args.username

        if item["password"] == "":
            item["password"] = userPassword

        #Add local hostname to the log

        agent = NetScreenAgent(item["host"],item["username"],item["password"],args.output,args.clear_session)
        if args.output:
            logger.log("======================================================================",True)
            logger.log("Connecting to host %s" % (item["host"]),True)
        try:
            agent.connect()
            agent.getSystemFacts()
            if agent.systemFacts["product"] != "":
                if args.output:
                    logger.log("Successfully connected to host %s" % (item["host"]),True)
                    logger.log("Host: %s Product: %s Serial Number: %s" % (agent.systemFacts["hostname"],agent.systemFacts["product"],agent.systemFacts["serialNumber"]),True)
                endValues, verboseOutput = agent.getAllAsicCounters(verboseLogging)
                if len(verboseOutput) > 0:
                    for line in verboseOutput:
                        logger.log(line,True)

                agent.disconnect()
                counters = agent.compareAsicCounters()
                for line in counters:
                    logger.log(line,True)
                logger.log("======================================================================\n",True)
            else:
                logger.log("Failed to fetch system facts about host: %s" % (item["host"]),True)
        except Exception, e:
            logger.log(str(e))
elif args.host != "":
    agent = NetScreenAgent(args.host,args.username,userPassword,args.output,args.clear_session)
    if args.output:
        logger.log("======================================================================",True)
        logger.log("Connecting to host %s" % (args.host),True)
    try:
        agent.connect()
        agent.getSystemFacts()
        if agent.systemFacts["product"] != "":
            if args.output:
                logger.log("Successfully connected to host %s" % (args.host),True)
                logger.log("Host: %s Product: %s Serial Number: %s" % (agent.systemFacts["hostname"],agent.systemFacts["product"],agent.systemFacts["serialNumber"]),True)

            endValues, verboseOutput = agent.getAllAsicCounters(verboseLogging)
            if len(verboseOutput) > 0:
                for line in verboseOutput:
                    logger.log(line,True)

            agent.disconnect()

            counters = agent.compareAsicCounters()
            for line in counters:
                logger.log(line,True)
            logger.log("======================================================================\n",True)
        else:
            logger.log("Failed to fetch system facts about host: %s" % (args.host),True)
    except Exception, e:
        logger.log(str(e))
else:
    parser.print_help()
