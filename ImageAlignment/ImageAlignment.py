"""
Swift scripting example: image alignment/summation
Purpose: Given a list of images or an image stack, align and
   sum the images.  This is frequently used with a fast scan
   rate to build up an image of a dose-rate-sensitive sample.
Author: Michael Sarahan, Nion, March 2014
"""

import gettext
import threading
import numpy as np

from nion.swift import Application
import logging

# implementation of processing functionality defined in register.py
import register

_ = gettext.gettext  # for translation

# this is the text that the menu will display
process_name = _("Align Image Stack")
# The prefix to prepend to the result image name:
process_prefix = _("Aligned sum of ")

def align_selected_stack(document_controller):
    with document_controller.create_task_context_manager(_("Image Alignment"), "table") as task:
        data_item = document_controller.selected_data_item
        if data_item is not None:
            logging.info("Starting image alignment.")
            with data_item.data_ref() as d:
                data=d.data
                if len(data.shape) is 3:
                    number_frames=data.shape[0]
                    task.update_progress(_("Starting image alignment."), (0, number_frames))
                    # Pre-allocate an array for the shifts we'll measure
                    shifts = np.zeros((number_frames, 2))
                    # we're going to use OpenCV to do the phase correlation
                    # initial reference slice is first slice
                    ref = data[0][:]
                    ref_shift = np.array([0, 0])
                    for index, _slice in enumerate(data):
                        task.update_progress(_("Cross correlating frame {}.").format(index), (index + 1, number_frames), None)
                        # TODO: make interpolation factor variable (it is hard-coded to 100 here.)
                        shifts[index] = ref_shift+np.array(register.get_shift(ref, _slice, 100))
                        ref = _slice[:]
                        ref_shift = shifts[index]
                    # sum image needs to be big enough for shifted images
                    sum_image = np.zeros(ref.shape)
                    # add the images to the registered stack
                    for index, _slice in enumerate(data):
                        task.update_progress(_("Summing frame {}.").format(index), (index + 1, number_frames), None)
                        sum_image += register.shift_image(_slice, shifts[index, 0], shifts[index, 1])
                    data_element = {"data": sum_image, "properties": {}}
                    data_item = document_controller.add_data_element(data_element)
                else:
                    logging.info("error: a 3D data stack is required for this task")
        else:
            logging.info("no data item is selected")
    

# This is the main function that gets run when the user selects the menu item.
def run_alignment(document_controller):
    threading.Thread(target=align_selected_stack, args=(document_controller, )).start()

# The following is code for adding the menu entry

def build_menus(document_controller):  # makes the menu entry for this plugin
    task_menu = document_controller.get_or_create_menu("script_menu", _("Scripts"), "window_menu")
    task_menu.add_menu_item(process_name, lambda: run_alignment(document_controller))

Application.app.register_menu_handler(build_menus)  # called on import to make the Button for this plugin
