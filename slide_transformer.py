# -*- coding: utf-8 -*-
"""slide transformer

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1zvOy9vYIk_RL16Ih8-3-3vmHhAW6R7iB
"""

import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.models import Sequential
from keras.layers.core import Dense, Dropout,Flatten
from keras.layers.recurrent import SimpleRNN,LSTM,GRU
from keras import regularizers
from google.colab import drive
from random import sample
from keras.layers.embeddings import Embedding
import random
!pip install attention
from attention import Attention
from tensorflow.keras import Input
from tensorflow.keras.models import Model
from keras.models import load_model

drive.mount('/content/drive', force_remount=True)

FOLDERNAME = 'dataset'
assert FOLDERNAME is not None, "[!] Enter the foldername."

import sys
sys.path.append('/content/drive/My Drive/{}'.format(FOLDERNAME))

slide_num = 100
repeat_time = 30
print("Start")
print("Slide number: ", slide_num)
print("Repeat number: ", repeat_time)

input_data_machine = '/content/drive/MyDrive/町洋code/data_1212.xlsx'
input_data_rate = '/content/drive/MyDrive/町洋code/1212瞬測儀資料.xlsx'
data_machine = pd.read_excel(input_data_machine, usecols=["package","frequency","Speed","Status"])
data_rate = pd.read_excel(input_data_rate,'不良率＿用這個表', usecols=["編碼","總不良率"])
data_machine = data_machine.dropna()
data_rate = data_rate.dropna()

print(data_machine.head())
print(data_rate.head())
print(data_machine.shape)
print(data_rate.shape)

"""
將瞬測儀和機台數據資料分包&配對
"""
data_machine.set_index("package", inplace=True)
all_data_machineId = np.array(data_machine.index.drop_duplicates(keep='first').values)
data_machine.reset_index(inplace=True)

data_rate.set_index("編碼", inplace=True)
all_data_rateId = np.array(data_rate.index.drop_duplicates(keep='first').values)
data_rate.reset_index(inplace=True)

print(all_data_machineId.size)
print(all_data_rateId.size)

pkg_num = 0

for data_machineId in all_data_machineId:
  for data_rateId in all_data_rateId:
    if data_machineId == data_rateId:
      pkg_num += 1 
      globals()['x_'+str(pkg_num)] = data_machine[data_machine["package"] == data_machineId]
      globals()['y_'+str(pkg_num)] = data_rate[data_rate["編碼"] == data_rateId]
    else :
      pass

max_pkg_num = pkg_num
print("Total package number: ", max_pkg_num)

"""
計算筆數小於slide_num筆包數
"""
usable_pkg = 0
lessthan = 0

for pkg_num in range(1, max_pkg_num+1):
  if len(globals()['x_'+str(pkg_num)]) < slide_num:
    lessthan += 1
  else:
    if usable_pkg == 0:
      first_pkg = pkg_num 
    usable_pkg += 1
  globals()['x_'+str(pkg_num)] = globals()['x_'+str(pkg_num)].drop(["package"], axis=1)
  globals()['y_'+str(pkg_num)] = globals()['y_'+str(pkg_num)].drop(columns = ["編碼"])

print("Less than slide_num data package: ",lessthan)
print("Usable package: ",usable_pkg)
print("First package number: ",first_pkg)

"""
處理feature，one hot encode & 各包抽slide_num*n筆, 處理label
"""
for pkg_num in range(1, max_pkg_num+1):
  pkg_size = len(globals()['x_'+str(pkg_num)])

  if len(globals()['x_'+str(pkg_num)]) < slide_num:
    pass
  else: 
    """
    slide repeat_time次, 挑連續slide_num筆feature data, shape = (包*repeat_time*slide_num ,3)
    """
    for num in range(repeat_time):
      end = pkg_size - slide_num
      random_start = random.randint(0,end)

      if num == 0:
        globals()['x_slide_'+str(pkg_num)] = globals()['x_'+str(pkg_num)][random_start:random_start+slide_num]
      else:
        globals()['x_slide_'+str(pkg_num)] = pd.concat([globals()['x_slide_'+str(pkg_num)], globals()['x_'+str(pkg_num)][random_start:random_start+slide_num]])
    
    globals()['x_slide_'+str(pkg_num)] = pd.get_dummies(globals()['x_slide_'+str(pkg_num)]).values

    """
    處理label, shape = (包*repeat_time, 1)
    """
    pkg_rate = globals()['y_'+str(pkg_num)].iloc[0].round(2).values
    slide_time = int(len(globals()['x_slide_'+str(pkg_num)])/slide_num)
    globals()['y_slide_'+str(pkg_num)] = np.zeros((slide_time,1))

    for y_num in range(slide_time):
      globals()['y_slide_'+str(pkg_num)][y_num] = np.array([pkg_rate])


# print(x_slide_6)
# print(y_slide_6)
# print(x_slide_6.shape)  
# print(y_slide_6.shape)

print(globals()['x_slide_'+str(first_pkg)].shape)  
print(globals()['y_slide_'+str(first_pkg)].shape)

"""
依序存進data & label
"""
for pkg_num in range(1, max_pkg_num+1):
# for pkg_num in range(1, 100):
  if len(globals()['x_'+str(pkg_num)]) < slide_num:
    pass
  else:
    if pkg_num == first_pkg:
      data = pd.DataFrame(globals()['x_slide_'+str(pkg_num)])    
      label = pd.DataFrame(globals()['y_slide_'+str(pkg_num)])    
    else:
      data = pd.concat([data, pd.DataFrame(globals()['x_slide_'+str(pkg_num)])])
      label = pd.concat([label, pd.DataFrame(globals()['y_slide_'+str(pkg_num)])])

data = data.values
label = label.values

print(data.shape) 
print(label.shape) 
# data = data.reshape(-1, 1, 3)
# print(data.shape)

slide_size = 0
pkg_size = 0
data_temp = []
data_temp1 = []

for pkg_num in range(1, max_pkg_num+1):
# for pkg_num in range(1, 100):
  if len(globals()['x_'+str(pkg_num)]) < slide_num:
    pass
  else: 
    for num in range(repeat_time): 
      # print(data[slide_size:(slide_size+100), 0:3])
      data_temp.append(data[slide_size:(slide_size+slide_num), 0:3])
      slide_size += slide_num

data = np.array(data_temp)

print(data.shape)
print(label.shape)

permutation=np.random.permutation(label.shape[0])
shuffled_data=data[permutation,:,:]
shuffled_label=label[permutation]

rate=0.7
X_train=shuffled_data[:int(shuffled_data.shape[0]*rate)]
Y_train=shuffled_label[:int(shuffled_label.shape[0]*rate)]
X_test=shuffled_data[int(shuffled_data.shape[0]*rate):]
Y_test=shuffled_label[int(shuffled_label.shape[0]*rate):]

print(X_train.shape)
print(Y_train.shape)
print(X_test.shape)
print(Y_test.shape)

def min_max(data):
  return (data-data.min())/(data.max()-data.min())

X_train = min_max(X_train)
X_test = min_max(X_test)

print(X_train.shape)
print(X_test.shape)

def transformer_encoder(inputs, head_size, num_heads, ff_dim, dropout=0):
    # Attention and Normalization
    x = layers.MultiHeadAttention(
        key_dim=head_size, num_heads=num_heads, dropout=dropout
    )(inputs, inputs)
    x = layers.Dropout(dropout)(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x)
    res = x + inputs

    # Feed Forward Part
    x = layers.Conv1D(filters=ff_dim, kernel_size=1, activation="relu")(res)
    x = layers.Dropout(dropout)(x)
    x = layers.Conv1D(filters=inputs.shape[-1], kernel_size=1)(x)
    x = layers.LayerNormalization(epsilon=1e-6)(x)
    return x + res

def build_model(
    input_shape,
    head_size,
    num_heads,
    ff_dim,
    num_transformer_blocks,
    mlp_units,
    dropout=0,
    mlp_dropout=0,
):
    inputs = keras.Input(shape=input_shape)
    x = inputs
    for _ in range(num_transformer_blocks):
        x = transformer_encoder(x, head_size, num_heads, ff_dim, dropout)

    x = layers.GlobalAveragePooling1D(data_format="channels_first")(x)
    for dim in mlp_units:
        x = layers.Dense(dim, activation="relu")(x)
        x = layers.Dropout(mlp_dropout)(x)
    outputs = layers.Dense(1,activation='sigmoid')(x)
    return keras.Model(inputs, outputs)

from tensorflow import keras
from tensorflow.keras import layers

input_shape = X_train.shape[1:]

model = build_model(
    input_shape,
    head_size=256,
    num_heads=4,
    ff_dim=4,
    num_transformer_blocks=4,
    mlp_units=[128],
    mlp_dropout=0.4,
    dropout=0.25,
)

model.compile(
    loss="mae",
    optimizer=keras.optimizers.Adam(learning_rate=1e-4),
    metrics=["mse"],
)
model.summary()

callbacks = [keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)]


test=model.fit(
    X_train,
    Y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=1000,
    callbacks=callbacks,
)

pred=model.predict(X_test,batch_size=1000)
print(pred.shape)
df = pd.DataFrame(Y_test, columns=['true'])
pred = pred.reshape(-1,1)
df['pred'] = pred
mse,mae=model.evaluate(X_test,Y_test)
print("mae_test:",mae)
print("mse_test:",mse)
df.to_csv('/content/drive/MyDrive/町洋code/slide100_trans.csv', header=True, index=True) 
print(df.head(10))
print(df.tail(10))

#plot model loss
plt.rcParams["figure.figsize"]=(6,4)
plt.plot(test.history['loss'],label='training loss')
plt.plot(test.history['val_loss'],label='val_loss')
plt.legend(loc='upper right')
plt.show()
plt.close()



"""
true & pred 散布圖
"""
data_plt = pd.read_csv('/content/drive/MyDrive/町洋code/slide100_trans.csv', usecols=["true","pred"])
plt.figure(figsize=(6,6)) 
plt.scatter('true', 'pred', data=data_plt, s = 1)
plt.xlabel('TRUE')
plt.ylabel('PRED')
plt.xlim(-0.1,1.1)
plt.ylim(-0.1,1.1)
plt.title('trans_slide_100')
plt.show()