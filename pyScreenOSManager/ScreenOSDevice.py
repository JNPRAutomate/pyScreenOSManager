#!/usr/bin/env python
"""
Microburst detection tool for ASIC-based NetScreen platforms
"""
import socket
import paramiko
import time
import sys
import re
import select
import exceptions
import sys
import datetime

#used to enable SSH debugging
#paramiko.common.logging.basicConfig(level=paramiko.common.DEBUG)
class ScreenOSDevice:
    """
    ScreenOSDevice

    Args:
        :host: string containing the host to connect to
        :username: string containing the username to authenticate with
        :password: string contining the password to authenticate with
    """
    def __init__(self,hostname,username,password,output,clear_session):
        self.systemFacts = {"hostname":"","product":"","serialNumber":"","controlNumber":"","version":"","type":""}
        self.remoteHost = hostname
        self.promptEnding = "->"
        self.promptRegex = re.compile(".*->")
        self.username = username
        self.password = password
        self.platform = ""
        self.asicCounters = dict()
        self.clear_session = clear_session
        if output:
            self.output = output
        else:
            self.output = False

    def open(self):
        """
        Opens an SSH CLI session to the specified ScreenOS-based device

        Example:

        .. code-block:: python

            from pyScreenOSManager import ScreenOSDevice

            //creates a connection to the Screen device
            dev = ScreenOSDevice(host="1.2.3.4",username="root",password="Juniper")
            dev.open()

        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(15)
        try:
            #Connect to the remote socket
            self.socket.connect((self.remoteHost,22))
            #Start the ssh transport
            self.transport = paramiko.Transport(self.socket)
            self.transport.start_client()
            self.transport.auth_password(username=self.username,password=self.password)
            #Open a new channel to the ssh host
            self.chan = self.transport.open_session()
            self.chan.set_combine_stderr(False)
            self.chan.setblocking(blocking=1)
            self.chan.settimeout(None)
            self.chan.invoke_shell()
            #Wait until the channel is ready, helpful for slow links
            while self.chan.send_ready() != True:
                pass

            if self.clear_session == True:
                self._clear_admin_sessions()

            self._disablePaging()

        except:
            """Raise an exception that a connection is unable to be made"""
            raise Exception("Unable to connect to host: %s" % (self.remoteHost))

    def _runSilentCommand(self,command,maxMatch):
        """Run a command and supress any output, used for simple housekeeping tasks"""
        #sleep to slow the input to the device
        time.sleep(0.2)
        self.chan.send(command + "\n")
        coutstr=""
        result=""
        promptMatch = 0
        while True:
            #Gather the output from the command until the prompt is detected
            if self.chan.recv_ready():
                coutstr = self.chan.recv(1024)
                result += coutstr
                if len(coutstr) < 1024:
                    lines = result.splitlines()
                    for line in lines:
                        if self.promptRegex.match(line):
                            promptMatch = promptMatch + 1
                            if promptMatch == maxMatch:
                                #Prompt detected exit
                                coutstr=""
                                return

    def _disablePaging(self):
        """disables paging on the console to prevent the need to interact with a pagnated set of output"""
        self._runSilentCommand("set console page 0",2)

    def _enablePaging(self):
        """disables paging on the console to prevent the need to interact with a pagnated set of output"""
        self._runSilentCommand("set console page 20",1)

    def _clear_admin_sessions(self):
        """disables paging on the console to prevent the need to interact with a pagnated set of output"""
        self._runSilentCommand("clear admin all",1)

    def _exit_session(self,save=False):
        """Exit the ssh session. Optionally save config."""
        #sleep to slow input to the device
        time.sleep(0.2)
        self.chan.send("exit\n")
        coutstr=""
        result=""
        promptMatch = 0
        maxMatch = 1
        configModMatch = ".*Configuration modified\, save\? \[y\]\/n.*"
        configModMatchRe = re.compile(configModMatch)
        while True:
            #Gather the output from the command until the prompt is detected
            if self.chan.recv_ready():
                coutstr = self.chan.recv(1024)
                result += coutstr
                if len(coutstr) < 1024:
                    lines = result.splitlines()
                    for line in lines:
                        if self.promptRegex.match(line):
                            promptMatch = promptMatch + 1
                            if promptMatch == maxMatch:
                                #Prompt detected exit
                                return
                        elif configModMatchRe.match(line):
                            if save == True:
                                self.chan.send("y")
                                return
                            else:
                                self.chan.send("n")
                                return

    def runCommand(self,command):
        """Run a specified command against the device, returns the output of the command"""
        #sleep to slow input to the device
        time.sleep(0.2)
        self.chan.send(command + "\n")
        coutstr=""
        result=""
        finalOutput = ""
        promptMatch = 0
        lineCount = 0
        while True:
            #Gather the output from the command until the prompt is detected
            if self.chan.recv_ready():
                coutstr = self.chan.recv(1024)
                result += coutstr
                if len(coutstr) < 1024:
                    lines = result.splitlines()
                    for line in lines:
                        lineCount = lineCount + 1
                        if self.promptRegex.match(line):
                            promptMatch = promptMatch + 1
                            if promptMatch == 1:
                                return finalOutput
                        elif lineCount == 1:
                            """Skip processing this line"""
                            pass
                        else:
                            finalOutput = finalOutput + line + "\n"

    def getSystemFacts(self):
        """Gets all of the needed system facts"""
        self.getHostname()
        self.checkPlatform()

    def getHostname(self):
        """Get system hostname"""
        hostnameMatch = "Hostname: ([\w\W]+)"
        hostnameMatchRe = re.compile(hostnameMatch)

        output = self.runCommand("get hostname")
        splitLines = output.splitlines()
        for line in splitLines:
            #Gather the output from the command until the hostname is detected
            if hostnameMatchRe.match(line):
                result = hostnameMatchRe.match(line)
                self.systemFacts["hostname"] = result.group(1)


    def checkPlatform(self):
        """Determine the local platform type"""

        # Example Match Product Name: NetScreen-5400-III
        systemMatch = "Product Name: ([\w\W]+)"
        systemMatchRe = re.compile(systemMatch)

        # Example Match Serial Number: 0047122010000025, Control Number: 00000000
        serialNumberMatch = "Serial Number: ([\w]+), Control Number: ([\w]+)"
        serialNumberMatchRe = re.compile(serialNumberMatch)

        # Example Match Software Version: 6.2.0r9-cu4.0, Type: Firewall+VPN
        softwareVersionMatch = "Software Version: ([\w\W]+), Type: ([\w\W]+)"
        softwareVersionMatchRe = re.compile(softwareVersionMatch)

        output = self.runCommand("get system")
        splitLines = output.splitlines()
        for line in splitLines:
            #Gather the output from the command until the correct facts are detected
            if systemMatchRe.match(line):
                #Match the product name
                result = systemMatchRe.match(line)
                self.systemFacts["product"] = result.group(1)
            elif serialNumberMatchRe.match(line):
                #Match the serial and control numbers
                result = serialNumberMatchRe.match(line)
                self.systemFacts["serialNumber"] = result.group(1)
                self.systemFacts["controlNumber"] = result.group(2)
            elif softwareVersionMatchRe.match(line):
                #Match the version and type of product
                result = softwareVersionMatchRe.match(line)
                self.systemFacts["version"] = result.group(1)
                self.systemFacts["type"] = result.group(2)

    def _getAsicCounter(self,asicid,qmuid):
        """Get the counters from the specified asic"""
        if self.systemFacts["product"] == "":
            #print "Product facts not gathered"
            pass
        #ISG Match
        elif self.systemFacts["product"] == ASICList["NetScreen-2000"]["productString"] or self.systemFacts["product"] == ASICList["NetScreen-ISG1000"]["productString"]:
            output = self.runCommand("get asic engine qmu pktcnt %s" % (qmuid))
            return output
        #NS5400 Match
        elif self.systemFacts["product"] == ASICList["NetScreen-5400-II"]["productString"] or self.systemFacts["product"] == ASICList["NetScreen-5400-III"]["productString"]:
            output = self.runCommand("get asic %s engine qmu pktcnt %s" % (asicid,qmuid))
            return output
        #NS52000 Match
        elif self.systemFacts["product"] == ASICList["NetScreen-5200-II"]["productString"] or self.systemFacts["product"] == ASICList["NetScreen-5200"]["productString"]:
            output = self.runCommand("get asic %s engine qmu pktcnt %s" % (asicid,qmuid))
            return output

    def _compileAsicDict(self,endValues,asicid,queueList,runid,lines):
        """parse asic data"""
        for queue in queueList:
            if queue in endValues[asicid]:
                #queue initilized already
                pass
            else:
                #Create dict structre for values
                endValues[asicid][queue] = {}

            if runid in endValues[asicid][queue]:
                #runid initalized already
                pass
            else:
                endValues[asicid][queue][runid] = ""

            queueRE = re.compile("pktcnt\[%s\s+\]\s=\s(0x\d{8})\s+(\d*)" % (queue))
            for line in lines:
                #Gather values for the output
                if queueRE.match(line):
                    matchResult = queueRE.match(line)
                    endValues[asicid][queue][runid] = matchResult.group(1)

            return endValues

    def getAllAsicCounters(self,verbose):
        """Get all counters from the platform"""
        #itterate through the asics and the counters on the platform
        endValues = dict()
        verboseOutput = []
        if self.systemFacts["product"] in ASICList:
            asic_list = ASICList[self.systemFacts["product"]]["asic_list"]
            qmu_list = ASICList[self.systemFacts["product"]]["qmu_list"]
            runid = "0"
            for asic in asic_list:
                endValues[asic] = {}
                for qmu in qmu_list:
                    #Get the inital asic counters to initialize the buffer, ignore output
                    self._getAsicCounter(asic,qmu)
                    #Get the ASIC counters and save the output
                    output = self._getAsicCounter(asic,qmu)
                    lines = output.split("\n")
                    if verbose:
                        verboseOutput.extend(lines)
                    queueList = BUFFERList[str(qmu)]
                    endValues = self._compileAsicDict(endValues,asic,queueList,runid,lines)
            runid = "1"
            for asic in asic_list:
                for qmu in qmu_list:
                    self._getAsicCounter(asic,qmu)
                    output = self._getAsicCounter(asic,qmu)
                    lines = output.split("\n")
                    if verbose:
                        verboseOutput.extend(lines)
                    queueList = BUFFERList[str(qmu)]
                    endValues = self._compileAsicDict(endValues,asic,queueList,runid,lines)
            self.asicCounters = endValues
        return endValues, verboseOutput

    def compareAsicCounters(self):
        """compare the two asic values"""
        finalOutput = []
        if len(self.asicCounters) > 0:
            for asic in self.asicCounters:
                for queue in self.asicCounters[asic]:
                    runid0 = ""
                    runid1 = ""
                    if "0" in self.asicCounters[asic][queue]:
                        """queue initilized already"""
                        runid0 = self.asicCounters[asic][queue]["0"]

                    if "1" in self.asicCounters[asic][queue]:
                        """queue initilized already"""
                        runid1 = self.asicCounters[asic][queue]["1"]

                    if runid1 != "" and runid0 != "":
                        asicDiff = int(runid0,0) - int(runid1,0)
                        if asicDiff > 0:
                            if self.output:
                                finalOutput.append("Packet loss of %d packet(s) detected in ASIC %s witin queue %s on host %s" % (asicDiff,asic,queue.rjust(6),self.systemFacts["hostname"]))
                        else:
                            if self.output:
                                finalOutput.append("No packet loss detected in ASIC %s witin queue %s on host %s" % (asic,queue.rjust(6),self.systemFacts["hostname"]))
        return finalOutput

    def disconnect(self):
        """Disconnect from the device"""
        self._enablePaging()
        self._exit_session()
        self.chan.close()
        self.transport.close()
        self.socket.close()
