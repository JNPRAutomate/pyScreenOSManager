class OutputLogger:
    """
    OutputLogger

    Handles writing to a file and priting output
    """
    def __init__(self,output,outputFile=""):
        """Initializes all of the bufferes for logging"""
        self.printStdout = output
        self.outputFileName = outputFile
        self.prefix = []
        self.suffix = []
        if self.outputFileName != "":
            self._openFile()

    def _openFile(self):
        """Opens a file for writing"""
        self.outputFile = open(self.outputFileName, 'w')

    def addPrefix(self,newPrefix):
        """Appends a prefix to the output. Each prefix added is put into a list. When a prefix is output each element is seperated by a space. The prefix is added to the front of the output after the timestamp"""
        self.prefix.append(newPrefix)

    def clearPrefix(self):
        """Removes prefixes from logger"""
        self.prefix = []

    def clearSuffix(self):
        """Removes suffix from logger"""
        self.suffix = []

    def addSuffix(self,newSuffix):
        """Appends a suffix to the output. Each suffix added is put into a list. When a suffix is output each element is seperated by a space. The suffix is added to the end of the output."""
        self.suffix.append(newPrefix)

    def _closeFile(self):
        self.outputFile.close()

    def start(self,outputFile=""):
        """Prepares the logger to start logging by opening the file to write to"""
        self.outputFileName = outputFile
        if self.outputFileName != "":
            self._openFile()

    def stop(self):
        """Stops the logger by closing the file"""
        if self.outputFileName != "":
            self._closeFile()

    def log(self,message,timestamp=False):
        """Logs a message with an optional timestamp"""
        baseMessage = message

        message = message.rstrip()

        if len(self.prefix) > 0:
            finalPrefix = " ".join(self.prefix)
            message = "%s %s" % (finalPrefix,message)

        if len(self.suffix) > 0:
            finalSuffix = finalPrefix = " ".join(self.suffix)
            message = "%s %s" % (message,finalSuffix)

        if timestamp:
            message = datetime.datetime.now().isoformat() + " " + message

        if baseMessage != "" and baseMessage != "\n" and len(baseMessage) > 0:
            if self.printStdout:
                print message
            if self.outputFileName != "":
                self.outputFile.write(message + "\n")
