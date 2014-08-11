This provides a simple class for creating an IPython in-process kernel in Swift, and provides a few methods to talk to the kernel.  
It has been tested with IPython version 2.1.0 on Windows.  It has been tested on Linux also, but crashes due to a Qt version mismatch issue 
(Swift is Qt5, but IPython is Qt4.)  Workarounds and solutions are being investigated.

Required setup:
- Install pyside (this is necessary to use the newer "version 2" API
- Set an environment variable QT_API to pyside

Example usage:
import IPythonConnection
# start up the kernel and instantiate the connector object
c = IPythonConnection.IPythonConnector()
# open up a QtConsole window for IPython
c.show_console()
# push a data item from Swift to the kernel
c.push({"d": r337})
# pull a variable from the kernel into Swift
c.pull("d")