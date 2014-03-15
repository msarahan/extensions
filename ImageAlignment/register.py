# -*- coding: utf-8 -*-
"""
Created on Tue Mar 11 11:13:51 2014

@author: Michael Sarahan
"""

import cv2
import numpy as np

import dftregister

def blur(image, blur_size=7):
    """
    Blurs input input with a Gaussian filter.  Sigma for the Gaussian filter is 3.

    Parameters
    ----------
    image : array_like
            The input image
    blur_size : int, optional, defaults to 7
            The pixel size of the Gaussian convolution kernel.  Should be odd.

    Returns
    -------
    array_like
            Filtered (blurred) image
    """
    return cv2.GaussianBlur(image, (blur_size, blur_size), 3)

def edge_filter(image):
    """
    Highlights edges in image using Sobel filtering (with Scharr kernels)

    Parameters
    ----------
    image : array_like
            Input image to be filtered

    Returns
    -------
    array_like
            Edge-filtered image
    """
    vertical = cv2.Scharr(image, -1, 0, 1)
    horizontal = cv2.Scharr(image, -1, 1, 0)
    return np.sqrt(vertical**2+horizontal**2)

def get_shift(data1, data2, blur_image=True, edge_filter_image=False,
                        interpolation_factor=100):
    """
    Parameters
    ----------
    data1 : array_like, 2D
            Reference image
    data2 : array_like, 2D
            Target image (shift should be applied to this image to register it with data1)
    blur_image : bool, default True
            If True, blurs image before registering.  Should improve robustness.
    edge_filter_image : bool, default False
            If True, edge filters image before registering.  May improve results for stacks in which
            image contrast changes.
    interpolation_factor : int
            Fraction of a pixel to which to register.  100 means 1/100 of a pixel precision.

    Returns
    -------
    array_like
            Shift required to register data2 with data1.  Shift is in columns, rows (Y, X)
    """
    ref = data1[:]
    target = data2[:]
    if blur_image:
        ref = blur(ref)
        target = blur(target)
    if edge_filter_image:
        ref = edge_filter(ref)
        target = edge_filter(target)
    return dftregister.dftregistration(ref, target, interpolation_factor)

def align_and_sum_stack(stack, blur_image=True, edge_filter_image=False,
                        interpolation_factor=100):
    """
    Given image list or 3D stack, this function uses cross correlation and Fourier space supersampling
    to find the subpixel shift between images, then apply those offsets and sum the images.

    Parameters
    ----------
    stack : array_like, 3D
            Input stack of images to be registered.  They should all be at the same magnification.
    blur_image : bool, default True
            If True, blurs image before registering.  Should improve robustness.
    edge_filter_image : bool, default False
            If True, edge filters image before registering.  May improve results for stacks in which
            image contrast changes.
    interpolation_factor : int
            Fraction of a pixel to which to register.  100 means 1/100 of a pixel precision.

    Returns
    -------
    array_like
            The registered, summed stack (2D)
    """
    # Pre-allocate an array for the shifts we'll measure
    shifts = np.zeros((stack.shape[0], 2))
    # we're going to use OpenCV to do the phase correlation
    # initial reference slice is first slice
    ref = stack[0][:]
    ref_shift = np.array([0, 0])
    for index, _slice in enumerate(stack):
        shifts[index] = ref_shift+np.array(get_shift(ref, _slice, blur_image, edge_filter_image, interpolation_factor))
        ref = _slice[:]
        ref_shift = shifts[index]
    # sum image needs to be big enough for shifted images
    sum_image = np.zeros(ref.shape)
    # add the images to the registered stack
    for index, _slice in enumerate(stack):
        sum_image += shift_image(_slice, shifts[index, 0], shifts[index, 1])
    return sum_image

def shift_image(data, row_shift=0, col_shift=0):
    """
    Shifts input image in Fourier space, effectively wrapping around at boundaries.

    Parameters
    ----------
    data : array_like
            The image data (real-space) to be shifted
    row_shift : int or float
            The shift to be applied along rows (Y-shift)
    col_shift : int or float
            The shift to be applied along columns (X-shift)

    Returns
    -------
    array_like
            The shifted image (in real-space)
    """
    data = np.fft.fft2(data)
    rows, cols = data.shape
    row_vector = np.fft.ifftshift(np.arange(-np.fix(rows/2), np.ceil(rows/2)))
    col_vector = np.fft.ifftshift(np.arange(-np.fix(cols/2), np.ceil(cols/2)))
    col_array, row_array = np.meshgrid(col_vector, row_vector)
    return np.fft.ifft2(data*np.exp(1j*2*np.pi*(-row_shift*row_array/rows-col_shift*col_array/cols))).real
