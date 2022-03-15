import numpy
from PyEMD import EMD
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from pandas import read_csv
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
import math
import pylab as mpl


def create_dataset(dataset, look_back):
    dataX, dataY = [], []
    for i in range(0, len(dataset) - look_back, 12):
        a = dataset[i:(i + look_back), 0]
        dataX.append(a)
        b = dataset[(i + look_back):(i + look_back + 12), 0]
        dataY.append(b)
    return numpy.array(dataX), numpy.array(dataY)

def imf_data(data, look_back):
    X1 = []
    for i in range(look_back, len(data)):
        X1.append(data[i - look_back:i])
    X1.append(data[len(data) - 1:len(data)])
    X_train = np.array(X1)
    return X_train

def data_split_LSTM(trainX,  testX):
    trainX = numpy.reshape(trainX, (trainX.shape[0], 36,1))
    testX = numpy.reshape(testX, (testX.shape[0], 36, 1))
    return (trainX,  testX)

def LSTM_Model(trainX):
    model = Sequential()
    model.add(LSTM(60, activation='relu', input_shape=(trainX.shape[1], trainX.shape[2]),return_sequences=False))
    model.add(Dropout(0.3))
    model.add(Dense(12,activation='linear'))
    model.summary()
    model.compile(loss='mse',optimizer='adam', metrics=['accuracy'])
    return model

def RMSE(test, predicted):
    rmse = math.sqrt(mean_squared_error(test, predicted))
    return (rmse)
def MAPE(Y_true, Y_pred):
    return (np.mean(np.abs((Y_true - Y_pred) / Y_true)) * 100)

if __name__ == '__main__':  #EMD_LSTM

    dataframe = read_csv('', usecols=[1], engine='python', skipfooter=0)
    dataset = dataframe.values  # 将dataframe转化为numpy数组
    dataset = dataset.astype('float32')
    scaler = MinMaxScaler(feature_range=(0, 1))
    dataset = scaler.fit_transform(dataset)

    emd = EMD()
    imfs = emd.emd(dataset.reshape(-1), None, 8)

    print(len(imfs))
    fig=plt.figure(figsize=(10.5,8.5))
    plt.subplot(10,1,1)
    plt.plot(dataset)
    plt.ylabel('signal',fontsize=15)
    fig.align_ylabels()
    i = 1
    for imf in imfs:
        plt.tight_layout()
        fig.align_ylabels()
        plt.subplot(len(imfs)+1, 1, i+1)
        plt.ylabel('IMF'+ str(i),fontsize=15)
        plt.subplots_adjust(hspace=0.5)
        if i==7:
            fig.align_ylabels()
            mpl.rcParams['font.sans-serif'] = ['Times New Roman']
            plt.rcParams['axes.unicode_minus'] = False
            plt.ylabel('Res',fontsize=15)
            mpl.rcParams['font.sans-serif'] = ['SimHei']
            plt.rcParams['axes.unicode_minus'] = False
            plt.xlabel('time/2h',fontsize=15)
        plt.plot(imf)
        i += 1

    look_back = 36
    tool = np.zeros([220*12, 1])

    print('tool:',tool.shape)
    for imf in imfs:
        data = imf_data(imf, 1)
        train_size = 611368
        train, test = data[0:train_size, :], data[train_size:len(data), :]
        testX, testY = create_dataset(test, 36)
        testY = testY.reshape(-1, 1)
        tool = tool + testY
    a=[]
    j=1
    prediction = np.zeros([220*12, 1])
    fig3 = plt.figure(figsize=(10, 9))
    for imf in imfs:
       print('-'*45)
       print('This is ' + str(j) + ' time(s)')
       print('*'*45)
       data=imf_data(imf,1)
       train_size = 61368
       train, test = data[0:train_size, :], data[train_size:len(data), :]
       trainX, trainY = create_dataset(train, 36)
       testX, testY = create_dataset(test, 36)
       trainX, testX= data_split_LSTM(trainX,testX)
       model= LSTM_Model(trainX)
       history = model.fit(trainX,trainY,epochs=100,batch_size=36,verbose=2)
       ax1 = plt.subplot(3, 3, j)
       plt.tight_layout()
       if j==9:
           plt.plot(history.history['loss'])
           plt.plot(history.history['val_loss'])
           plt.title('Res',fontsize=15)
           plt.ylabel('loss', fontsize=15)
           plt.xlabel('epoch', fontsize=15)
           plt.legend(['train', 'test'], loc='upper right', fontsize=10)
           plt.savefig('H:\\Core\\loss_function.svg',format='svg',dpi=600)
           plt.show()
       plt.subplots_adjust(hspace=1)
       plt.plot(history.history['loss'])
       plt.plot(history.history['val_loss'])
       plt.title('IMF_'+str(j),fontsize=15)
       plt.ylabel('loss',fontsize=15)
       plt.xlabel('epoch',fontsize=15)
       plt.legend(['train', 'test'], loc='upper right',fontsize=10)
       prediction_Y = model.predict(testX)  # (47,12)
       a.append(prediction_Y)
       j+=1;

    a = np.array(a)
    prediction = [0.0 for i in range(len(tool))]
    prediction = np.array(prediction)
    prediction=prediction.reshape(220,12)
    for i in range(220):
        t = 0.0
        for imf_prediction in a:
            t += imf_prediction[i][:]
        prediction[i,:] = t
    prediction = prediction.reshape(-1,1)

    true = scaler.inverse_transform(tool)
    prediction = scaler.inverse_transform(prediction)

    rmse = math.sqrt(mean_squared_error(true, prediction))
    mape = format(MAPE(true, prediction), '.4f')
    r2 = format(r2_score(true, prediction), '.4f')
    mae = format(mean_absolute_error(true, prediction), '.4f')
    print('RMSE:' + str(rmse) + '\n' + 'MAE:' + str(mae) + '\n' + 'MAPE:' + str(mape) + '\n' + 'R2:' + str(r2))
