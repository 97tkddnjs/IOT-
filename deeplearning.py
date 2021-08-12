import tensorflow as tf
from tensorflow.keras.layers import LSTM, Dense

def make_model(x, y, a):
    model = tf.keras.Sequential()
    model.add(Dense(100, activation='relu', input_shape=(1,)))
    model.add(Dense(256, activation='relu'))
    model.add(Dense(64, activation='relu'))
    model.add(tf.keras.layers.Dropout(rate=0.2))
    model.add(Dense(2, activation='softmax'))

    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    # #
    model.summary()
    model.fit(x, y, epochs=10, verbose=1, batch_size=1)
    #
    model_name = str(a)+'.h5'
    model.save(model_name)

def retrain_model(x, y, a):
    model_name = str(a) + '.h5'
    model = tf.keras.models.load_model(model_name)
    model.fit(x, y, epochs=10, verbose=1, batch_size=1)
    #
    model.save(model_name)