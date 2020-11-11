import subprocess
import sys
import socket
import platform
import signal


if platform.system().lower().startswith('windows'):
    WINDOWS = True
else:
    WINDOWS = False
    from ctypes import cdll

LOG_LEVEL_NONE = 0
LOG_LEVEL_DEBUG = 1
LOG_LEVEL_INFO = 2
LOG_LEVEL_WARNING = 3
LOG_LEVEL_ERROR = 4


class ServiceLauncherUtils(object):

    def __init__(self, logger=None):
        self.__logger = logger

    def PrintLog(self, text, level):
        if self.__logger is None:
            sys.stderr.write(text)
        else:
            if level == LOG_LEVEL_DEBUG:
                self.__logger.LogDebug(text)
            elif level == LOG_LEVEL_INFO:
                self.__logger.LogInfo(text)
            elif level == LOG_LEVEL_WARNING:
                self.__logger.LogWarn(text)
            elif level == LOG_LEVEL_ERROR:
                self.__logger.LogError(text)

    def GetAvailablePortFromRange(self, serviceHost, minPort, maxPort, preferredPort):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rc = False
        if preferredPort >= minPort and preferredPort <= maxPort:
            port = preferredPort
        else:
            port = minPort
        while True and port < maxPort:
            try:
                s.bind((serviceHost, port))
            except socket.error:
                print('cant attach to port' + str(port))
                rc = False
                port += 1
                continue

            rc = True
            break
        s.close()
        return (rc, port)

    def GetHostIP(self):
        try:
            # Attempt to get the publicly visible IP address first, via DNS records.
            hostname = socket.gethostname()
            address = socket.gethostbyname(hostname)
            if not address or address == '127.0.0.1' or address.find('localhost') != -1:
                raise Exception('gethostbyname failed')
            return address
        except Exception as e:
            # Fall back to internal IP address, which still **may** be the public one,
            # but in the VPN case, it likely will not be, as the request would not
            # go through the VPN.
            self.__logger.LogWarn(str(e))
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                address = s.getsockname()[0]
            except Exception as e:
                # We did the best we could. Return loopback address.
                # TODO There will likely be corner cases in which neither
                # method above will work or will be incorrect based on DNS problems, etc.
                # We should add a user configurable setting to allow the customer to set his own IP address.
                # This is what most server software, e.g. apache, nginx, do.
                self.__logger.LogError(str(e))
                address = '127.0.0.1'
            finally:
                s.close()
            return address

    def LaunchService(self, cmd, logFile, execPath, parentOwnsProcess):
        pid = 0
        print cmd
        print execPath
        try:
            stdOutErrLog = open(logFile, 'w')
            if WINDOWS or not parentOwnsProcess:
                p = subprocess.Popen(cmd,
                                     stdout=stdOutErrLog,
                                     stderr=stdOutErrLog,
                                     cwd=execPath)
            else:
                # Setup to send TERM signal to service when the parent dies.
                # The same is handled for Windows via "Job Objects".
                libc = cdll.LoadLibrary('libc.so.6')
                p = subprocess.Popen(cmd,
                                     stdout=stdOutErrLog,
                                     stderr=stdOutErrLog,
                                     cwd=execPath,
                                     preexec_fn=lambda *args: libc.prctl(1, signal.SIGTERM, 0, 0, 0))

            if p.poll() is None:
                pid = str(p.pid)

        except subprocess.CalledProcessError as e:
            self.PrintLog("Failed to launch  Service : " +
                          e.returncode + " : " + e.output + "\n",
                          LOG_LEVEL_ERROR)
        return pid
