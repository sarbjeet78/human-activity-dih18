from keras.utils import np_utils
from utility.cv_utils import *
from config import *


def load_data(categories):
    if len(categories) == 1:
        raise ValueError("Cannot classify single class")
    data = []
    labels = []
    for label, category in enumerate(categories):
        files = glob.glob(os.path.join(category, '*'))
        print("Category %s --- %d files" % (category, len(files)))
        for file in files:
            image = imread(file, MODE)
            image = cv2.resize(image, SIZE)
            data.append(image)
            labels.append(label)
    X = np.array(data)
    y = np.array(labels)
    y = np_utils.to_categorical(y, len(categories))
    print('X.shape:', X.shape)
    print('y.shape:', y.shape)
    return X, y
