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
    if blur_image:
        ref = blur(ref)
    if edge_filter_image:
        ref = edge_filter(ref)
    ref_shift = np.array([0, 0])
    for index, _slice in enumerate(stack):
        filtered_slice = _slice[:]
        if blur_image:
            filtered_slice = blur(filtered_slice)
        if edge_filter_image:
            filtered_slice = edge_filter(filtered_slice)
        shifts[index] = ref_shift+np.array(dftregister.dftregistration(ref,
                                        filtered_slice, interpolation_factor))
        ref = filtered_slice[:]
        ref_shift = shifts[index]
    # sum image needs to be big enough for shifted images
    sum_image = np.zeros(ref.shape)
    # add the images to the registered stack
    for index, _slice in enumerate(stack):
        sum_image += dftregister.shift_image(_slice, shifts[index, 0], shifts[index, 1])
    return sum_image
