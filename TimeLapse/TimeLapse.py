# standard libraries
import functools
import gettext
import threading
import time

# third party libraries
# None

# local libraries
from nion.swift import Application
from nion.swift.model import HardwareSource


_ = gettext.gettext


# This section sets up the menu item to run a time lapse sequence.
def build_menus(document_controller):
    if not hasattr(document_controller, "script_menu"):
        document_window = document_controller.document_window
        document_controller.script_menu = document_window.insert_menu(_("Scripts"), document_controller.window_menu)
    document_controller.script_menu.add_menu_item(_("Run Time Lapse"), lambda: run_time_lapse(document_controller),
                                                  key_sequence="Ctrl+T")


Application.app.register_menu_handler(build_menus)


# This function will run on a thread. Consequently, it cannot modify the document model directly.
# Instead, when it needs to add data items to the containing data group, it will queue that operation
# to the main UI thread.
def perform_time_lapse(document_controller, data_group):
    with document_controller.create_task_context_manager(_("Time Lapse"), "table") as task:

        task.update_progress(_("Starting time lapse."), (0, 5))

        # Get a data item generator for the hardware source 'video_capture'.
        # data_item_generator will be a function, which, when called, will return a data item from the camera.
        with HardwareSource.get_data_item_generator_by_id("video_capture") as data_item_generator:

            task_data = {"headers": ["Number", "Time"]}

            for i in xrange(5):

                # update task results table. data should be in the form of
                # { "headers": ["Header1", "Header2"],
                #   "data": [["Data1A", "Data2A"], ["Data1B", "Data2B"], ["Data1C", "Data2C"]] }
                data = task_data.setdefault("data", list())
                task_data_entry = [str(i), time.strftime("%c", time.localtime())]
                data.append(task_data_entry)
                task.update_progress(_("Acquiring time lapse item {}.").format(i), (i + 1, 5), task_data)

                # Grab the next data item.
                data_item = data_item_generator()
                if data_item is None:
                    break

                # Appending a data item to a group needs to happen on the UI thread.
                # This function will be placed in the document controllers UI thread queue.
                def append_data_item(_document_model, _data_group, _data_item):
                    assert threading.current_thread().getName() == "MainThread"
                    _document_model.append_data_item(_data_item)
                    _data_group.append_data_item(_data_item)

                document_controller.queue_main_thread_task(
                    functools.partial(append_data_item, document_controller.document_model, data_group, data_item))

                # Go to sleep and wait for the next frame.
                time.sleep(1.0)

        task.update_progress(_("Finishing time lapse."), (5, 5))

        time.sleep(1.0)  # only here as a demonstration


# This is the main function that gets run when the user selects the menu item.
def run_time_lapse(document_controller):
    data_group = document_controller.document_model.get_or_create_data_group(_("Time Lapse"))
    threading.Thread(target=perform_time_lapse, args=(document_controller, data_group)).start()
