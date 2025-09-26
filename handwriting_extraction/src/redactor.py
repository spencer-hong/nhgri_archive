import numpy as np
from numpy.lib.stride_tricks import as_strided as ast
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()
from tensorflow.python.platform import gfile
import cv2
import skimage as sk
from tqdm import tqdm
import os
from pathlib import Path
from urllib import request, parse
import json
from skimage import filters


class redactor(object):
    """A redactor to remove handwriting from image
    ...

    Attributes
    ----------
    model_path : str
        path to the model 

    Methods
    -------
    mask_handwriting(input_path):
        removes handwriting

    unet_inference(input_image):
        runs the model

    proc_image(image):
        apply sliding window to the inference
    """

    def __init__(self, model_path):
        """
        Constructs all the necessary attributes for the redactor object.

        Parameters
        ----------
        model_path: str
            path to the model .pb

        Returns
        ----------
        None
        """
        
        os.environ['CUDA_VISIBLE_DEVICES']='1'
        gpu_options = tf.GPUOptions(allow_growth=True)
        sess = tf.Session(config=tf.ConfigProto(gpu_options = gpu_options, device_count = {'GPU': 1}))
        with tf.gfile.GFile(model_path,'rb') as f:
            graph_def = tf.GraphDef()

        graph_def.ParseFromString(f.read())
        sess.graph.as_default()
        tf.import_graph_def(graph_def, name='')
        graph_nodes=[n for n in graph_def.node]
        names = []
        for t in graph_nodes:
            names.append(t.name)
        # Get handles to # and output tensors
        ops = tf.get_default_graph().get_operations()
        all_tensor_names = {output.name for op in ops for output in op.outputs}
        tensor_dict = {}
        for key in [ 'conv2d_18/Sigmoid' ]:
            tensor_name = key + ':0'
            if tensor_name in all_tensor_names:
                tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(tensor_name)
        # Model
        image_tensor = tf.get_default_graph().get_tensor_by_name('input_1:0')
        
        self.input_tensor = image_tensor

        self.model_tensors = tensor_dict
        
        self.sess = sess

    def mask_handwriting(self, input_path):
        """
        Mask handwriting from the input image
        Parameters
        ----------
        input_path :str
            image path

        Returns
        ----------
        result : dict
            dictionary containing removed, original, handwriting-only, and cleaned 
        """
        
        _img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
        _out = self.proc_image(_img, height_prop=1, width_prop=1)
        rows, cols = _img.shape[:2]
        area = rows * cols
        # invert colors
        _out = (255-_out)
#         handwritten = _out.copy()
#         handwritten[handwritten == 1] = 255
        # binarize images
        th = filters.threshold_sauvola(_img, window_size=15, k=0.2)
        _img = _img > th
        _img = _img.astype('uint8')
        th = filters.threshold_sauvola(_out, window_size=1, k=0.2)
        handwritten = _out.copy() > th
        handwritten = handwritten.astype('uint8')
        handwritten[handwritten == 1] = 255
        th = filters.threshold_sauvola(_out, window_size=15, k=0.2)
        _out = _out > th
        _out = _out.astype('uint8')
        ima_result = _img - _out
        median_blur= cv2.medianBlur(ima_result, 3)

#         contours, hierarchy = cv2.findContours(_out, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#         ima2 = _img.copy()
#         for c in contours:
#             # get the bounding rect
#             x, y, w, h = cv2.boundingRect(c)
#             # draw a green rectangle to visualize the bounding rect
#             rect = (w-x)*(h-y)
#             if rect < area: # avoid big areas
#                 cv2.rectangle(ima2, (x, y), (x+w, y+h), (0, 255, 0), -2)
#         ima2[ima2 == 1] = 255
        _img[_img == 1] = 255
#         _out[_out == 1] = 255
        
#         # Location of the handwriting information (output of the UNET model)
        threshold = 1
        lineIdx = np.where(_out < threshold)
        # Perform inpainting on the located area
        mask = np.zeros(_out.shape, dtype=np.uint8)
        mask[lineIdx] = 1
        ima_proc_final = cv2.inpaint(_img, mask, 0, cv2.INPAINT_NS)
        ima_proc_final[ima_proc_final == 1] = 255
        median_blur = (255-median_blur)
        median_blur[median_blur == 1] = 255


        return {'ORIGINAL': _img, 'HANDWRITTEN_TO': handwritten, 'CLEANED_TO': median_blur}

    def unet_inference(self, input_image):
        
        __DEF_WIDTH = 2048
        __DEF_HEIGHT = 2048
        OUTPUT=np.empty((1,__DEF_HEIGHT,__DEF_WIDTH,1))
        INPUT=np.empty((1,__DEF_HEIGHT,__DEF_WIDTH,1))
        orig_h = input_image.shape[0]
        orig_w = input_image.shape[1]
        _img = 1 - (input_image/255)
        _img = cv2.resize(_img, (__DEF_WIDTH, __DEF_HEIGHT), interpolation=cv2.INTER_CUBIC)
        _img = (_img.reshape((__DEF_WIDTH, __DEF_HEIGHT, 1)))
        INPUT[0,:,:,0] = cv2.resize(_img,(__DEF_WIDTH,__DEF_HEIGHT), interpolation=cv2.INTER_CUBIC)
        # Inference
        output_dict = self.sess.run(self.model_tensors, feed_dict={self.input_tensor: INPUT})
        # Mapping output
        OUTPUT=output_dict['conv2d_18/Sigmoid']
        _out_image = sk.img_as_ubyte(OUTPUT[0,:]) #convert for 8 bits
        _out_image = cv2.resize(_out_image, (orig_w, orig_h), interpolation=cv2.INTER_CUBIC)
        return _out_image

    def proc_image(self, _img, height_prop=1, width_prop=1):
        orig_height, orgi_width = _img.shape
        
        win_dim = (orig_height // height_prop, orgi_width // width_prop)
        win = sliding_window(_img, win_dim, shiftSize=None, flatten=False)
        
        _out=np.ones((orig_height, orgi_width))
        
        for h in range (win.shape[0]):
            for w in range (win.shape[1]):
                windows = win[h,w]
                proc_windows = self.unet_inference(windows)
                t, b, l, r = get_win_pixel_coords((h, w), win_dim, None)
                _out[t:b, l:r] = proc_windows
        return _out
    

# taken from http://www.johnvinyard.com/blog/?p=268
def norm_shape(shape):
    '''
    Normalize numpy array shapes so they're always expressed as a tuple,
    even for one-dimensional shapes.
    Parameters
        shape - an int, or a tuple of ints
    Returns
        a shape tuple
    '''
    try:
        i = int(shape)
        return (i,)
    except TypeError:
        # shape was not a number
        pass
    try:
        t = tuple(shape)
        return t
    except TypeError:
        # shape was not iterable
        pass
    raise TypeError('shape must be an int, or a tuple of ints')
    
def get_win_pixel_coords(grid_pos, win_shape, shift_size=None):
    if shift_size is None:
        shift_size = win_shape
        
    gr, gc = grid_pos
    sr, sc = shift_size
    wr, wc = win_shape
    
    top, bottom = gr * sr, (gr * sr) + wr
    left, right = gc * sc, (gc * sc) + wc
    return top, bottom, left, right

# taken from http://www.johnvinyard.com/blog/?p=268
def sliding_window(image, windowSize, shiftSize=None, flatten=True):
    '''
    Return a sliding window over a in any number of dimensions
    Parameters:
        image  - an n-dimensional numpy array
        ws - an int (a is 1D) or tuple (a is 2D or greater) representing the size
             of each dimension of the window
        ss - an int (a is 1D) or tuple (a is 2D or greater) representing the
             amount to slide the window in each dimension. If not specified, it
             defaults to ws.
        flatten - if True, all slices are flattened, otherwise, there is an
                  extra dimension for each dimension of the input.
    Returns
        an array containing each n-dimensional window from a
    '''
    if None is shiftSize:
        # ss was not provided. the windows will not overlap in any direction.
        shiftSize = windowSize
    windowSize = norm_shape(windowSize)
    shiftSize = norm_shape(shiftSize)
    # convert ws, ss, and a.shape to numpy arrays so that we can do math in every
    # dimension at once.
    windowSize = np.array(windowSize)
    shiftSize = np.array(shiftSize)
    shape = np.array(image.shape)
    # ensure that ws, ss, and a.shape all have the same number of dimensions
    ls = [len(shape),len(windowSize),len(shiftSize)]
    if 1 != len(set(ls)):
        raise ValueError(\
        'a.shape, ws and ss must all have the same length. They were %s' % str(ls))
    # ensure that ws is smaller than a in every dimension
    if np.any(windowSize > shape):
        raise ValueError(\
        'ws cannot be larger than a in any dimension. a.shape was %s and ws was %s' % (str(image.shape),str(windowSize)))

    # how many slices will there be in each dimension?
    newshape = norm_shape(((shape - windowSize) // shiftSize) + 1)
    # the shape of the strided array will be the number of slices in each dimension
    # plus the shape of the window (tuple addition)
    newshape += norm_shape(windowSize)
    # the strides tuple will be the array's strides multiplied by step size, plus
    # the array's strides (tuple addition)
    newstrides = norm_shape(np.array(image.strides) * shiftSize) + image.strides
    strided = ast(image,shape = newshape,strides = newstrides)
    if not flatten:
        return strided
    # Collapse strided so that it has one more dimension than the window.  I.e.,
    # the new array is a flat list of slices.
    meat = len(windowSize) if windowSize.shape else 0
    firstdim = (np.product(newshape[:-meat]),) if windowSize.shape else ()
    dim = firstdim + (newshape[-meat:])
    # remove any dimensions with size 1
    dim = filter(lambda i : i != 1,dim)
    return strided.reshape(dim)
