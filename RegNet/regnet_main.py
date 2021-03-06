from RegNet.regnet import make_dir_path, DataGenerator, RegNet
import numpy as np
import argparse
from keras.utils import plot_model
from keras.optimizers import Adam, Adadelta
import keras.metrics as K_Metrics
import keras.backend as K


def PCK_3D_Metrics(y_true, y_pred):
    ones21 = K.ones((21,1), dtype=np.float)
    threshold_tensor = ones21 * 0.5
    ones = K.ones((3,1), dtype=np.float)

    diff = K.square(y_true-y_pred)
    diff = K.dot(diff, ones)            # (-1, 21, 1, 3) x (3, 1) => (-1, 21, 1, 1)
    diff = K.sqrt(diff)
    diff = K.reshape(diff, (-1, 21,1))  # (-1, 21, 1, 1) => (-1, 21, 1)
    diff = K.less(diff, threshold_tensor)      # PCK means less than threshold percentage.
    diff = K.cast(diff, np.float)       # bool to float
    diff = K.reshape(diff, (-1, 21))    # (-1, 21)
    mean_value = K.dot(diff, ones21) / 21.    # (-1, 1)
    return K.mean(mean_value)


def custom_metrics(y_true, y_pred):

    if y_pred.shape[-1] == 21:
        return K.mean(y_pred)
    else:
        return PCK_3D_Metrics(y_true, y_pred)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Argument for training regnet')
    parser.add_argument('--data', type=str, help='data path for training regnet. I recommended you to GANerated Dataset')
    parser.add_argument('--model', type=str, help='model weight path')

    FLAGS = parser.parse_args()
    root_path = FLAGS.data
    if root_path is None:
        train_data = []
        fp = open("train_path_list.ini", "r")
        train_path = fp.readlines()
        for path in train_path:
            train_data.append(path.rstrip('\n'))

        fp = open("test_path_list.ini", "r")
        test_data = []
        test_pathes = fp.readlines()
        for path in test_pathes:
            test_data.append(path.rstrip('\n'))

        print("Not train")

    else:
        print(root_path)
        pathes = make_dir_path(root_path)
        np.random.shuffle(pathes)
        path_len = len(pathes)
        train_data = pathes[:-path_len//10]
        test_data = pathes[-path_len//10:]
        fp = open("train_path_list.ini", "w")
        for path in train_data:
            fp.write(path+"\n")
        fp.close()
        fp = open("test_path_list.ini", "w")
        for path in test_data:
            fp.write(path+"\n")

    print("train_set:{0}, test_set:{1}".format(len(train_data), len(test_data)))
    heatmap_shape = (32,32)
    train_gen = DataGenerator(dir_path=train_data, batch_size=28, heatmap_shape=heatmap_shape)
    test_gen = DataGenerator(dir_path=test_data, shuffle=False, heatmap_shape=heatmap_shape)
    regNet = RegNet(input_shape=(256, 256, 3), heatmap_shape=(32,32))

    optimizer = Adam(lr=1e-4)

    regNet.model.compile(optimizer=optimizer,
                         loss=['mse',
                               'mse',
                               'mse'],
                         loss_weights=[100,
                                       100,
                                       1],
                         metrics=['mse', custom_metrics]
                         )
    plot_model(regNet.model, to_file='model.png')

    print(regNet.model.metrics_names)
    print(FLAGS.model)
    if FLAGS.model is not None:
        regNet.model.load_weights(FLAGS.model)

    regNet.train_on_batch(epoch=100, train_generator=train_gen, test_generator=test_gen)


