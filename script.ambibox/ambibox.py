import socket
import os


class AmbiBox:

#	host = '127.0.0.1'    # The remote host
#	port = 3636           # The same port as used by the server

    def __init__(self, _host, _port):
        self.host = _host
        self.port = _port

    def __readResult(self):  # Return last-command API answer  (call in every local method)
        total_data = []
        data = self.connection.recv(8192)
        total_data.append(data)
        result = ''.join(total_data)
        # we remove the linesep
        return result[0:result.index(os.linesep)]

    def connect(self):
        try:  # Try to connect to the server API
            self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection.connect((self.host, self.port))
            self.__readResult()
            return 0
        except:
            print 'AmbiBox API server is missing'
            return -1

    def disconnect(self):
        self.unlock()
        self.connection.close()

    def lock(self):
        cmd = 'lock' + os.linesep
        self.connection.send(cmd)
        self.__readResult()

    def unlock(self):
        cmd = 'unlock' + os.linesep
        self.connection.send(cmd)
        self.__readResult()

    def turnOn(self):
        self.setStatus('on')

    def turnOff(self):
        self.setStatus('off')

    def setStatus(self, s):
        cmd = 'setstatus:' + s + os.linesep
        self.connection.send(cmd)
        self.__readResult()

    def getStatus(self):
        cmd = 'getstatus' + os.linesep
        self.connection.send(cmd)
        status = self.__readResult()
        status = status.split(':')[1]
        return status

    def setProfile(self, p):
        cmd = 'setprofile:' + p + os.linesep
        self.connection.send(cmd)
        return self.__readResult()

    def getProfile(self):
        cmd = 'getprofile' + os.linesep
        self.connection.send(cmd)
        result = self.__readResult()
        return result[(result.index(':') + 1):len(result)]

    def getProfiles(self):
        cmd = 'getprofiles' + os.linesep
        self.connection.send(cmd)
        result = self.__readResult()
        profiles = (result[(result.index(':') + 1):len(result)]).split(';')
        profiles.remove('')
        return profiles
