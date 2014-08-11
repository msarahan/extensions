import sys

# finds whatever is on the user's PATH (TODO: might not be the same as Swift!)
sys.executable = "python"

from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport

class IPythonConnector(object):
    def __init__(self):
        super(IPythonConnector, self).__init__()
        app = guisupport.get_app_qt4()
        self.kernel_manager = QtInProcessKernelManager()
        self.kernel_manager.start_kernel()
        self.kernel = self.kernel_manager.kernel
        self.kernel.gui = 'inline'

        self.kernel_client = self.kernel_manager.client()
        self.kernel_client.start_channels()

    def show_console(self):
        control = RichIPythonWidget()
        control.kernel_manager = self.kernel_manager
        control.kernel_client = self.kernel_client
        control.show()

    def print_connection_info(self):
    	"""Ideally, this would print info that would allow us to connect an IPython notebook to our kernel.
    	Unfortunately, this particular kind of kernel does not seem to have this information."""
        print("Connection file:")
        print(self.kernel.connection_file)
        print("Profile:")
        print(self.kernel.profile)

    def push(self, data_dict):
        self.kernel.shell.push(data_dict)

    def pull(self, key):
        return self.kernel.shell.user_ns[key]
