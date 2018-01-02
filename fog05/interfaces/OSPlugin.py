from fog05.interfaces.Plugin import Plugin
import uuid

class OSPlugin(Plugin):
    """
    Interfaces for plugins that allow interaction with underlying operating system
    provide an abstraction layer for some managment and monitoring functions

    """

    def __init__(self,version, plugin_uuid=None):
        super(OSPlugin, self).__init__(version, plugin_uuid)

    def get_base_path(self):
        raise NotImplemented
    def executeCommand(self, command, blocking):

        """
        Execute a command to cli of underlying os, IDK should return bool or the command output?

        :command: String
        :return: String or bool?
        """
        
        raise NotImplementedError("This is and interface!")

    def installPackage(self, packages):
        """
        Install all packages passed within the parameter, return a bool
        to know the retult of operation

        :packages: tuple
        :return: bool

        """

        raise NotImplementedError("This is and interface!")
    
    def storeFile(self, content, file_path, filename):

        """
        Store a file in local disk, maybe can convert from windows dir separator to unix dir separator

        :content: byte
        :file_path: string
        :filename: string
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def fileExists(self, file_path):
        raise NotImplementedError

    def dirExists(self, path):
        raise NotImplemented

    def createDir(self, path):
        raise NotImplemented

    def createFile(self, path):
        raise NotImplemented

    def removeDir(self, path):
        raise NotImplemented

    def removeFile(self, path):
        raise NotImplemented

    def readFile(self, file_path,root = False):

        """
        Read the content from a file in the local disk, maybe can convert from windows dir separator to unix dir separator
        return the file content
        throw an exception if file not exits
        
        :file_path: String
        :return: byte

        """

        raise NotImplementedError("This is and interface!")

    def readBinaryFile(self, file_path):
        raise NotImplemented

    def downloadFile(self, url, file_path):
        raise NotImplemented

    def getCPUID(self):
        """
        Return the underlying hw cpuid
        :return: String
        """

        raise NotImplementedError("This is and interface!")

    def getCPULevel(self):
        """
        Return the current cpu usage level
        :return: float
        """

        raise NotImplementedError("This is and interface!")

    def getMemoryLevel(self):
        """
        Return the current memory usage level
        :return: float
        """
        raise NotImplementedError("This is and interface!")

    def getStorageLevel(self):
        """
        Return the current local storage usage level
        :return: float
        """
        raise NotImplementedError("This is and interface!")

    def getNetworkLevel(self):

        """
        Return the current network usage level
        :return: float
        """
        raise NotImplementedError("This is and interface!")

    def removePackage(self, packages):

        """
        Remove all packages passed within the parameter, return a bool
        to know the retult of operation

        :packages: tuple
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def sendSignal(self, signal, pid):

        """
        Send a signal to the process identified by pid
        throw an exception if pid not exits

        :signal: int
        :pid: int
        :return: bool

        """

        raise NotImplementedError("This is and interface!")

    def getPid(self,process):
        """
        Try to get the the pid from the process name
        :process: string
        :return: int
        """
        raise NotImplementedError("This is and interface!")

    def sendSigInt(self, pid):

        """
        Send a SigKill (Ctrl+C) to the process identified by pid
        throw an exception if pid not exits
        :pid: int
        :return: bool
        """

        raise NotImplementedError("This is and interface!")

    def sendSigKill(self, pid):

        """
        Send a SigKill (kill the process) to the process identified by pid
        throw an exception if pid not exits
        :pid: int
        :return: bool
        """

        raise NotImplementedError("This is and interface!")

    def getUUID(self):
        return uuid.uuid4()

    def getProcessorInformation(self):
        raise NotImplemented

    def getMemoryInformation(self):
        raise NotImplemented

    def getDisksInformation(self):
        raise NotImplemented

    def getIOInformations(self):
        raise NotImplemented

    def getAcceleratorsInformations(self):
        raise NotImplemented

    def getNetworkInformations(self):
        raise NotImplemented

    def getPositionInformation(self):
        raise NotImplemented

    def addKnowHost(self, hostname, ip):
        raise NotImplemented

    def removeKnowHost(self, hostname):
        raise NotImplemented

    def get_intf_type(self, name):
        raise NotImplemented

    def set_io_unaviable(self, io_name):
       raise NotImplemented

    def set_io_available(self, io_name):
        raise NotImplemented

    def set_accelerator_unaviable(self, acc_name):
        raise NotImplemented

    def set_accelerator_available(self, acc_name):
        raise NotImplemented

    def set_interface_unaviable(self, intf_name):
        raise NotImplemented

    def set_interface_available(self, intf_name):
        raise NotImplemented

    def get_intf_type(self, name):
        raise NotImplemented

class ProcessNotExistingException(Exception):
    def __init__(self, message, errors):

        super(ProcessNotExistingException, self).__init__(message)
        self.errors = errors


class FileNotExistingException(Exception):
    def __init__(self, message, errors):

        super(FileNotExistingException, self).__init__(message)
        self.errors = errors