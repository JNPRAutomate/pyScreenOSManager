
class HostParser:
    """
    HostParser

    This class is designed to parse a CSV file containing the host,
     username and password for devices that the user wishes to connect to.

    Input CSV Example:
    #Comment lines start with #
    //Comments can also start with C flavored comments as well
    #IP,username,password example
    1.2.3.4,foo,bar
    #hostname,username,password
    nshost.example.com,netscreen,netscreen

    """
    def __init__(self, sourceFile):
        """When creating the class you must specify the source file location"""
        self.sourceFile = sourceFile
        self.hostList = [] # host,username,password
        self.currentHost = 0
        self._parse()
    def _parse(self):
        """parse host file"""
        try:
            """Try to open the file for reading"""
            openFile = open(self.sourceFile)
            lines = openFile.readlines()
            openFile.close()
            """Comment line regex matches"""
            commentLineRE = re.compile("^#.*|^//.*")
            newlineOnlyRE = re.compile("^\n$")
            for line in lines:
                if commentLineRE.match(line):
                    """Comment ignoring line"""
                    pass
                else:
                    """parse lines"""
                    lineItems = line.split(",")
                    if len(lineItems) == 3 and lineItems[0] != "" and lineItems[1] != "" and lineItems[2] != "":
                        if newlineOnlyRE.match(lineItems[0]) or newlineOnlyRE.match(lineItems[1]) or newlineOnlyRE.match(lineItems[2]):
                            """carrige return only found"""
                            pass
                        else:
                            self.hostList.append({"host":lineItems[0].rstrip(),"username":lineItems[1].rstrip(),"password":lineItems[2].rstrip()})
                    elif len(lineItems) == 1 and lineItems[0] == "" and lineItems[1] == "" and lineItems[2] == "":
                        """Only host was specified"""
                        if newlineOnlyRE.match(lineItems[0]) or newlineOnlyRE.match(lineItems[1]) or newlineOnlyRE.match(lineItems[2]):
                            """carrige return only found"""
                            pass
                        else:
                            self.hostList.append({"host":lineItems[0].rstrip(),"username":"","password":""})
                    else:
                        """Ignore line"""
                        pass
        except:
            raise Exception("Unable to open file")
    def getHosts(self):
        """return the current hostList as a list of dicts"""
        return self.hostList
