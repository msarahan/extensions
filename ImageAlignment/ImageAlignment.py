"""
Swift scripting example: image alignment/summation
Purpose: Given a list of images or an image stack, align and
   sum the images.  This is frequently used with a fast scan
   rate to build up an image of a dose-rate-sensitive sample.
Author: Michael Sarahan, Nion, March 2014
"""

import gettext

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
    data_item = document_controller.selected_data_item
    if data_item is not None:
        logging.info("Starting image alignment.")
        with data_item.data_ref() as d:
            if len(d.data.shape) is 3:
                aligned_image = register.align_and_sum_stack(d.data)
                data_element = {"data": aligned_image, "properties": {}}
                data_item = document_controller.add_data_element(data_element)
            else:
                logging.info("error: a 3D data stack is required for this task")
    else:
        logging.info("no data item is selected")


# The following is code for adding the menu entry

def build_menus(document_controller):  # makes the menu entry for this plugin
    task_menu = document_controller.get_or_create_menu("script_menu", _("Scripts"), "window_menu")
    task_menu.add_menu_item(process_name, lambda: align_selected_stack(document_controller))

Application.app.register_menu_handler(build_menus)  # called on import to make the Button for this plugin
