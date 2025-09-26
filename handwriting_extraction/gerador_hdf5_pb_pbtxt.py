import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

from tensorflow.python.framework import graph_io
import logging


import os

os.environ['CUDA_VISIBLE_DEVICES']='1'

hdf5_path = './checkpoint/unet_2048.hdf5'
pb_and_pbtxt_destiny = './checkpoint'


def dice_coef(y_true, y_pred, smooth=1000.0):
    y_true_f = tf.keras.backend.flatten(y_true)
    y_pred_f = tf.keras.backend.flatten(y_pred)
    intersection = tf.keras.backend.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (tf.keras.backend.sum(y_true_f) + tf.keras.backend.sum(y_pred_f) + smooth)

def dice_coef_loss(y_true, y_pred):
    return -dice_coef(y_true, y_pred)


model = tf.keras.models.load_model(hdf5_path, custom_objects={'dice_coef_loss': dice_coef_loss, 'dice_coef': dice_coef})

model.summary()
tf.keras.backend.set_learning_phase(0)
sess = tf.compat.v1.keras.backend.get_session()

orig_output_node_names = [node.op.name for node in model.outputs]
print(orig_output_node_names)
converted_output_node_names = orig_output_node_names
constant_graph = tf.compat.v1.graph_util.convert_variables_to_constants( sess, sess.graph.as_graph_def(), converted_output_node_names)
graph_io.write_graph(constant_graph, pb_and_pbtxt_destiny, "pre_trained_model.pb", as_text=False)
tf.train.write_graph(constant_graph, pb_and_pbtxt_destiny,"pre_trained_model.pbtxt", as_text=True)
logging.info('Graph definition in ascii format at %s', "./pre_trained_model.pbtxt")
logging.info('Freezed graph at %s', "./pre_trained_model.pb")

