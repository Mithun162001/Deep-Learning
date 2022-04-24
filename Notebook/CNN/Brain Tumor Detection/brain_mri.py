# -*- coding: utf-8 -*-
"""Brain MRI.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1q95yvMhqqaHU07CW5ZGV9DGmck36kgIP

<h1>Brain MRI Images for Brain Tumor Detection</h1>

importing the libraries
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import cv2
from matplotlib.image import imread

from google.colab import drive
drive.mount('/content/drive')

import zipfile
zip_ref = zipfile.ZipFile('/content/drive/MyDrive/brain tumor.zip')
zip_ref.extractall('/tmp')
zip_ref.close()

os.listdir('/tmp/brain_tumor_dataset')

len(os.listdir('/tmp/brain_tumor_dataset/yes/'))

len(os.listdir('/tmp/brain_tumor_dataset/no/'))

root_dir = '/tmp/brain_tumor_dataset'
number_of_images = {}

for dir in os.listdir(root_dir):
  number_of_images[dir] = len(os.listdir(os.path.join(root_dir,dir)))

number_of_images

"""we shall split the dataset into:
* 70% training data
* 15% testing data
* 15% validation data
"""

import math
import shutil

"""creating the folder - train, test, val"""

def datafolder(path,split):
  if not os.path.exists("./"+path):
    os.mkdir("./"+path)     # root --> train

    for dir in os.listdir(root_dir):
      os.makedirs("./"+path+"/"+dir)   # root --> train --> yes/no
      for img in np.random.choice(a=os.listdir(os.path.join(root_dir,dir)),
                                  size=(math.floor(split*number_of_images[dir])),
                                  replace=False):
        O = os.path.join(root_dir, dir, img)    # origin
        D = os.path.join("./"+path,dir)         # destination  root -->train---> yes ---> imagefile
        shutil.copy(O,D)
        os.remove(O)
  else:
    print("Path already exists")

datafolder('train',0.7)

train_n_img = {}
for dir in os.listdir("./train/"):
  train_n_img[dir] = len(os.listdir(os.path.join("./train/",dir)))

train_n_img

datafolder('test',0.15)

datafolder('val',0.15)

os.listdir('train'+'/yes')[0]
plt.imshow(imread('train'+'/yes/Y1.jpg'))
plt.title("A Brain Tumor MRI Image")

os.listdir('train'+'/no')[0]
plt.imshow(imread('train'+'/no/1 no.jpeg'))
plt.title("A Normal MRI Image without brain tumor")

fig, axes = plt.subplots(1,2)
axes[0].imshow(imread('train'+'/yes/Y1.jpg'))
axes[0].title.set_text('Brain Tumor MRI Image')

axes[1].imshow(imread('train'+'/no/11 no.jpg'))
axes[1].title.set_text('A Normal MRI\n Image without brain tumor')

plt.tight_layout()
plt.autoscale(enable=True, axis='both')

imread('train'+'/yes/Y1.jpg').shape

"""# Building CNN model"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, MaxPool2D, Flatten, Dropout

model = Sequential()
model.add(Conv2D(filters=16, kernel_size=(3,3), input_shape=(150,150,3), activation='relu'))
model.add(MaxPool2D(pool_size=(2,2)))

model.add(Conv2D(filters=32, kernel_size=(3,3), activation='relu'))
model.add(MaxPool2D(pool_size=(2,2)))

model.add(Conv2D(filters=64, kernel_size=(3,3), activation='relu'))
model.add(MaxPool2D(pool_size=(2,2)))

model.add(Dropout(0.2))

model.add(Flatten())

model.add(Dense(units=128, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(units=1, activation='sigmoid'))

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

model.summary()

"""Data pre-processing"""

from tensorflow.keras.preprocessing.image import ImageDataGenerator

def preprocessing(path):
  image_data = ImageDataGenerator(rotation_range=10,
                                   width_shift_range=0.1,
                                   zoom_range=0.2,
                                   rescale=1/255,
                                   shear_range=0.2,
                                   horizontal_flip=True)
  image = image_data.flow_from_directory(directory=path, target_size=(150,150),
                                         batch_size=16, class_mode='binary')
  return image

train_data = preprocessing('/content/train')

def preprocessing2(path):
  image_data = ImageDataGenerator(rescale=1/255)
  image = image_data.flow_from_directory(directory=path, target_size=(150,150),
                                         batch_size=16, class_mode='binary',
                                         shuffle=False)
  return image

test_data = preprocessing2('/content/test')
val_data = preprocessing2('/content/val')

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
early_stop = EarlyStopping(monitor='val_loss', patience=5)
mc = ModelCheckpoint(monitor='val_loss', filepath='./bestmodel.h5',save_best_only=True, mode='auto')

cb = [early_stop,mc]

model.fit(train_data, epochs=50, validation_data=val_data,callbacks=cb)

df = pd.DataFrame(model.history.history)
df

df[['loss','val_loss']].plot()

from tensorflow.keras.models import load_model
best_model = load_model("./bestmodel.h5")

"""Model Evaluation"""

acc = best_model.evaluate(test_data)
print("The accuracy of our model: ",acc[1]*100,"%")

from tensorflow.keras.preprocessing import image
img = image.load_img('/content/test/yes/Y10.jpg', target_size=(150,150))
img_arr = image.img_to_array(img)/255
img_arr = np.expand_dims(img_arr, axis=0)

plt.imshow(img_arr.reshape(150,150,3))
plt.title("to be predicted")

pred = best_model.predict(img_arr)
pred_classes = (pred > 0.5).astype("int32")
pred_classes

if pred_classes == 0:
  print("The image is not having a tumor")
elif pred_classes == 1:
  print("The image is having a tumor")
else:
  print("Not known!!!")

test_data.class_indices

pred_total = best_model.predict(test_data)
pred_classes_total = (pred_total > 0.5).astype("int32")

from sklearn.metrics import classification_report, confusion_matrix
print(classification_report(test_data.classes, pred_classes_total))
print(confusion_matrix(test_data.classes, pred_classes_total))

"""We have achieved 76% accuracy

# Transfer Learning using MobileNet
"""

from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.applications.mobilenet import MobileNet, preprocess_input

"""Data pre-processing"""

def preprocessing(path):
  image_data = ImageDataGenerator(rotation_range=10,
                                   width_shift_range=0.1,
                                   zoom_range=0.2,
                                   preprocessing_function=preprocess_input,
                                   shear_range=0.2,
                                   horizontal_flip=True)
  image = image_data.flow_from_directory(directory=path, target_size=(150,150),
                                         batch_size=16, class_mode='binary')
  return image

train_data = preprocessing('/content/train')

def preprocessing2(path):
  image_data = ImageDataGenerator(preprocessing_function=preprocess_input)  # preprocess_input is from the same pre-processing steps taking place from MObilNet Architecture
  image = image_data.flow_from_directory(directory=path, target_size=(150,150),
                                         batch_size=16, class_mode='binary',
                                         shuffle=False)
  return image

test_data = preprocessing2('/content/test')
val_data = preprocessing2('/content/val')

base_model = MobileNet(input_shape=(150,150,3), include_top=False)

# to make sure we won't re-train the model again
for layer in base_model.layers:
  layer.trainable = False

base_model.summary()

# club the pre-trained model with our custom model
X =Flatten()(base_model.output)  # last layer in base_model
X = Dense(units=1, activation='sigmoid')(X)

tf_model = Model(base_model.input, X)

tf_model.summary()

tf_model.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['accuracy'])

early_stop = EarlyStopping(monitor='val_loss', patience=5)
mc = ModelCheckpoint(monitor='val_loss', filepath='./bestmodel2.h5',save_best_only=True, mode='auto')

cb = [early_stop,mc]

"""Training the model"""

result_tf = tf_model.fit(train_data, 
                          steps_per_epoch=8,
                         epochs=30, 
                         validation_data=val_data, 
                         callbacks=cb)

best_model_2 = load_model('/content/bestmodel2.h5')

result_df = pd.DataFrame(tf_model.history.history)
result_df

result_df[['val_loss','loss']].plot()

"""Model Evaluation"""

acc = tf_model.evaluate(test_data)[1]
print("The accuracy of our model: ",acc*100,"%")

from tensorflow.keras.preprocessing import image
img = image.load_img('/content/test/yes/Y10.jpg', target_size=(150,150))
img_arr = image.img_to_array(img)/255
img_arr = np.expand_dims(img_arr, axis=0)

plt.imshow(img_arr.reshape(150,150,3))
plt.title("to be predicted")

pred = best_model_2.predict(img_arr)
pred_classes = (pred > 0.5).astype("int32")
pred_classes

if pred_classes == 0:
  print("The image is not having a tumor")
elif pred_classes == 1:
  print("The image is having a tumor")
else:
  print("Not known!!!")

pred_total = best_model_2.predict(test_data)
pred_classes_total = (pred_total > 0.5).astype("int32")

from sklearn.metrics import classification_report, confusion_matrix
print(classification_report(test_data.classes, pred_classes_total))
print(confusion_matrix(test_data.classes, pred_classes_total))

"""We achieved 84% accuracy using transfer leaning technique"""