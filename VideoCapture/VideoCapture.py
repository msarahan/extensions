# standard libraries
import gettext
import logging
import threading
import time

import numpy


# third party libraries
# see http://docs.opencv.org/index.html
import cv2
import cv2.cv as cv

# local libraries
from nion.swift.model import HardwareSource

_ = gettext.gettext


# does not currently work. to switch to this, copy the hardware source code out of
# simulator mp and enable this. add necessary imports too.
def video_capture_process(buffer, cancel_event, ready_event, done_event):
    logging.debug("video capture process start")
    video_capture = cv2.VideoCapture(0)
    logging.debug("video capture: %s", video_capture)
    #video_capture.open(0)
    logging.debug("video capture open")
    while not cancel_event.is_set():
        retval, image = video_capture.read()
        logging.debug("video capture read %s", retval)
        if retval:
            logging.debug("video capture image %s", image.shape)
            with buffer.get_lock(): # synchronize access
                buffer_array = numpy.frombuffer(buffer.get_obj(), dtype=numpy.uint8) # no data copying
                buffer_array.reshape(image.shape)[:] = image
            ready_event.set()
            done_event.wait()
            done_event.clear()
        time.sleep(0.001)
    video_capture.release()

# informal measurements show read() takes approx 70ms (14fps)
# on Macbook Pro. CEM 2013-July.
# after further investigation, read() can take about 6ms on same
# computer. to do this, need to read out less frequently (by
# limiting frame rate to 15fps). this means that the next frame
# is constantly ready, so doesn't have to wait for it.
# the hardware manager will happily eat up 100% of python-cpu time.
MAX_FRAME_RATE = 20  # frames per second
MINIMUM_DUTY = 0.05  # seconds
TIMEOUT = 5.0  # seconds

def video_capture_thread(video_capture, buffer, cancel_event, ready_event, done_event):

    while not cancel_event.is_set():
        start = time.time()
        retval, image = video_capture.read()
        if retval:
            buffer[:] = image
            ready_event.set()
            done_event.wait()
            done_event.clear()
            elapsed = time.time() - start
            delay = max(1.0/MAX_FRAME_RATE - elapsed, MINIMUM_DUTY)
            cancel_event.wait(delay)
        else:
            # we MUST give other threads a chance to process - so sleep here.
            time.sleep(0.001)

    video_capture.release()


class VideoCaptureHardwareSource(HardwareSource.HardwareSource):

    def __init__(self):
        self.hardware_source_id = "video_capture"
        self.hardware_source = _("Video Capture")
        super(VideoCaptureHardwareSource, self).__init__(self.hardware_source_id, self.hardware_source)

    def start_acquisition(self, mode, mode_data):
        video_capture = cv2.VideoCapture(0)
        width = video_capture.get(cv.CV_CAP_PROP_FRAME_WIDTH)
        height = video_capture.get(cv.CV_CAP_PROP_FRAME_HEIGHT)
        self.buffer = numpy.empty((height, width, 3), dtype=numpy.uint8)
        self.cancel_event = threading.Event()
        self.ready_event = threading.Event()
        self.done_event = threading.Event()
        self.thread = threading.Thread(target=video_capture_thread, args=(video_capture, self.buffer, self.cancel_event, self.ready_event, self.done_event))
        self.thread.start()

    def acquire_data_elements(self):
        self.ready_event.wait()
        self.ready_event.clear()
        data = self.buffer.copy()
        self.done_event.set()
        data_element = {
            "version": 1,
            "data": data,
            "properties": {
                "hardware_source": self.hardware_source,
                "hardware_source_id": self.hardware_source_id,
            }
        }
        return [data_element]

    def stop_acquisition(self):
        self.cancel_event.set()
        self.done_event.set()
        self.thread.join()


HardwareSource.HardwareSourceManager().register_hardware_source(VideoCaptureHardwareSource())
