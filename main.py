import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
import time

#from tensorflow.python.client import graph_util
#from tensorflow.python.client import graph_utils
#from graph_utils import load_graph


# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """
    # TODO: Implement function
    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag                    = 'vgg16'
    vgg_input_tensor_name      = 'image_input:0'
    vgg_keep_prob_tensor_name  = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    graph = tf.saved_model.loader.load(sess, ['vgg16'], vgg_path)

    image_input = sess.graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob   = sess.graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    vgg_layer3  = sess.graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    vgg_layer4  = sess.graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    vgg_layer7  = sess.graph.get_tensor_by_name(vgg_layer7_out_tensor_name)
    
    return image_input, keep_prob, vgg_layer3, vgg_layer4, vgg_layer7
tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer7_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer3_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    # following slack message https://carnd.slack.com/archives/C6F0M0AF8/p1501659626810682
    # TODO: check whether to follow http://cv-tricks.com/image-segmentation/transpose-convolution-in-tensorflow/

    # kernel initializer
    mykernelinitializer = tf.truncated_normal_initializer(stddev = 0.02)

    # prepare & upsample layer 7
    fc7 = tf.layers.conv2d(vgg_layer7_out, num_classes, kernel_size=1, strides=(1, 1), kernel_initializer=mykernelinitializer)
    fc7_up = tf.contrib.layers.conv2d_transpose(fc7, num_classes, kernel_size=4, stride=2, padding='SAME')

    # prepare layer, skip & upsample 4
    fc4 = tf.layers.conv2d(vgg_layer4_out, num_classes, kernel_size=1, strides=(1, 1), kernel_initializer=mykernelinitializer)
    fc4_skip = tf.add(fc7_up, fc4)
    fc4_up = tf.contrib.layers.conv2d_transpose(fc4_skip, num_classes, kernel_size=4, stride=2, padding='SAME')

    # prepare layer, skip & upsample 3
    fc3 = tf.layers.conv2d(vgg_layer3_out, num_classes, kernel_size=1, strides=(1, 1), kernel_initializer=mykernelinitializer)
    fc3_skip = tf.add(fc4_up, fc3)
    fc3_up = tf.contrib.layers.conv2d_transpose(fc3_skip, num_classes, kernel_size=16, stride=8, padding='SAME')

    return fc3_up
tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    # use approach from term 1, project 2
    #logits = nn_last_layer #LeNet(x)
    logits = tf.reshape(nn_last_layer, (-1, num_classes))    
    labels = tf.reshape(correct_label, (-1, num_classes))

    #cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=labels)
    #loss_operation = tf.reduce_mean(cross_entropy)
    #optimizer = tf.train.AdamOptimizer(learning_rate = learning_rate)
    #training_operation = optimizer.minimize(loss_operation)
    #cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits, labels))

    cross_entropy_loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=logits,labels=labels, name="Softmax"))
    training_operation = tf.train.AdamOptimizer(learning_rate).minimize(cross_entropy_loss)
    # model evaluation
    #correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(one_hot_y, 1))
    #accuracy_operation = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    #saver = tf.train.Saver()

    return logits, training_operation, cross_entropy_loss #loss_operation
tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function

    # use approach from term 1, project 2
    start_time = time.time()

    print("Training...")
    print("learning rate=" + str(learning_rate) + "  ●  batch size=" + 
                  str(batch_size) + "  ●  epochs=" + str(epochs))
    print()
    for i in range(epochs):
        print()
        print("EPOCH {} ...".format(i+1))
        batch_counter = 0
        for image, label in get_batches_fn(batch_size):
            _, loss = sess.run([train_op, cross_entropy_loss], 
                                 feed_dict = {input_image:   image, 
                                              correct_label: label, 
                                              keep_prob:     1, 
                                              learning_rate: 0.0001})

            """
            _, loss = sess.run([train_op, cross_entropy_loss], 
                                 feed_dict = {input_image:   image, 
                                              correct_label: label, 
                                              keep_prob:     keep_prob.eval(), 
                                              learning_rate: learning_rate.eval()})
            """

            #print("    batch {}: loss = {:.5f}".format(batch_counter+1, loss))
            print("    batch {}:  loss = {:.5f}".format(batch_counter+1, loss))
            #mylr = sess.run(lr)
            #print(mylr)
            batch_counter += 1

        delta = (time.time() - start_time)
        print("time since start = {} s  s/epoch {}".format(delta, delta/(i+1)))
       
tests.test_train_nn(train_nn)

"""
def mean_iou(ground_truth, prediction, num_classes):
    # TODO: Use `tf.metrics.mean_iou` to compute the mean IoU.
    iou, iou_op = tf.metrics.mean_iou(ground_truth, prediction, num_classes)
    return iou, iou_op
"""
# iou, iou_op = mean_iou(ground_truth, prediction, 4)
"""
with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        # need to initialize local variables for this to run `tf.metrics.mean_iou`
        sess.run(tf.local_variables_initializer())
        
        sess.run(iou_op)
        # should be 0.53869
        print("Mean IoU =", sess.run(iou))
"""

def run():
    num_classes = 2
    image_shape = (160, 576)
    data_dir = './data'
    runs_dir = './runs'
    tests.test_for_kitti_dataset(data_dir)

    # hyperparameters
    epochs = 20
    batch_size = 1 #10 #50 # to large: 100 --> 23 GB
    #keep_prob 0.5, 1

    # after 1 epoch
    # lr = 0.0001  keep_prob = 0.5   batch_size = 1/289 loss = 0.50866   time 1978= s/epoch   
    # lr = 0.0001    keep_prob = 0     batch = 1/289: loss =      time = s/epoch   


    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        #sess.run(tf.global_variables_initializer())
        # need to initialize local variables for this to run `tf.metrics.mean_iou`
        #sess.run(tf.local_variables_initializer())

        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        input_image, keep_prob, vgg_layer3, vgg_layer4, vgg_layer7 = load_vgg(sess, vgg_path)
        nn_last_layer = layers(vgg_layer3, vgg_layer4, vgg_layer7, num_classes)
        learning_rate = tf.placeholder(dtype = tf.float32)
        #keep_prob = tf.placeholder(dtype = tf.float32)
        correct_label = tf.placeholder(dtype = tf.float32, shape = (None, None, None, num_classes))
        logits, training_operation, cross_entropy_loss = optimize(nn_last_layer, correct_label, learning_rate, num_classes)

        # TODO: Train NN using the train_nn function
        sess.run(tf.global_variables_initializer())
        train_nn(sess, epochs, batch_size, get_batches_fn, training_operation, cross_entropy_loss, input_image, correct_label, keep_prob, learning_rate)

        # TODO: Save inference data using helper.save_inference_samples
        helper.save_inference_samples(runs_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
