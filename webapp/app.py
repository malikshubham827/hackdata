import io, traceback

from flask import Flask, request, g
from flask import send_file
from flask_mako import MakoTemplates, render_template
from plim import preprocessor
import pickle
from PIL import Image, ExifTags
from scipy.misc import imresize
import numpy as np
from keras.models import load_model, Sequential, Model
from keras.applications import VGG16
from keras.preprocessing import image, sequence
from keras.layers import Dense, Convolution2D, Dropout, LSTM, TimeDistributed, concatenate, Embedding, Bidirectional, Activation, RepeatVector, Merge
from keras.optimizers import Nadam
import tensorflow as tf

app = Flask(__name__, instance_relative_config=True)
# For Plim templates
mako = MakoTemplates(app)
app.config['MAKO_PREPROCESSOR'] = preprocessor
app.config.from_object('config.ProductionConfig')
max_len = 36
vocab_size = 3346

with open('./model/indices_2_word.p', 'rb') as f:
    indices_2_word = pickle.load(f)

with open('./model/word_2_indices.p', 'rb') as f:
    word_2_indices = pickle.load(f)

# Preload our model
print("Loading model")
# model = load_model('./model/model.h5', compile=False)
graph = tf.get_default_graph()


embedding_size = 128
image_model = Sequential()

image_model.add(Dense(embedding_size, input_shape=(4096,), activation='relu'))
image_model.add(RepeatVector(max_len))

language_model = Sequential()

language_model.add(Embedding(input_dim=vocab_size, output_dim=embedding_size, input_length=max_len))
language_model.add(LSTM(256, return_sequences=True))
language_model.add(TimeDistributed(Dense(embedding_size)))

model = Sequential()

model.add(Merge([image_model, language_model], mode='concat', concat_axis=-1))
model.add(Bidirectional(LSTM(1000, return_sequences=False)))
model.add(Dense(vocab_size))
model.add(Activation('softmax'))

model.load_weights("./model/second_weights.h5")
model.compile(loss='categorical_crossentropy', optimizer=Nadam(), metrics=['accuracy'])



def preprocess_input(img):
    img = img[:, :, :, ::-1]  # RGB to BGR
    img[:, :, :, 0] -= 103.939
    img[:, :, :, 1] -= 116.779
    img[:, :, :, 2] -= 123.68
    return img


def preprocessing(img_path):
    im = image.load_img(img_path, target_size=(224, 224, 3))
    im = image.img_to_array(im)
    im = np.expand_dims(im, axis=0)
    im = preprocess_input(im)
    return im


def predict_captions(image):
    start_word = ["<start>"]
    while True:
        par_caps = [word_2_indices[i] for i in start_word]
        par_caps = sequence.pad_sequences(
            [par_caps], maxlen=max_len, padding='post')
        e = image
        preds = model.predict([np.array([e]), np.array(par_caps)])
        word_pred = indices_2_word[np.argmax(preds[0])]
        start_word.append(word_pred)

        if word_pred == "<end>" or len(start_word) > max_len:
            break

    return ' '.join(start_word[1:-1])

def ml_predict(image):
    with graph.as_default():
        # Add a dimension for the batch
        prediction = predict_captions(image)
    # prediction = prediction.reshape((224,224, -1))
    return prediction


def get_encoding(mod, img):
    image = preprocessing(img)
    pred = mod.predict(image)
    pred = np.reshape(pred, pred.shape[1])
    return pred

def rotate_by_exif(image):
    try :
        for orientation in ExifTags.TAGS.keys() :
            if ExifTags.TAGS[orientation]=='Orientation' : break
        exif=dict(image._getexif().items())
        if not orientation in exif:
            return image

        if   exif[orientation] == 3 :
            image=image.rotate(180, expand=True)
        elif exif[orientation] == 6 :
            image=image.rotate(270, expand=True)
        elif exif[orientation] == 8 :
            image=image.rotate(90, expand=True)
        return image
    except:
        traceback.print_exc()
        return image

THRESHOLD = 0.5
@app.route('/predict', methods=['POST'])
def predict():
    # Load image
    img = request.files['file']
    img = Image.open(image)
    # image = rotate_by_exif(image)
    # resized_image = imresize(image, (224, 224)) / 255.0
    vgg = VGG16(weights='imagenet', include_top=True, input_shape=(224,224,3))
    vgg = Model(inputs=vgg.input, outputs=vgg.layers[-2].output)
    resized_image = get_encoding(vgg, img)


    # Model input shape = (224,224,3)
    # [0:3] - Take only the first 3 RGB channels and drop ALPHA 4th channel in case this is a PNG
    prediction = ml_predict(resized_image[:, :, 0:3])
    print('PREDICTION COUNT', (prediction[:, :, 1]>0.5).sum())

    # Resize back to original image size
    # [:, :, 1] = Take predicted class 1 - currently in our model = Person class. Class 0 = Background
    # prediction = imresize(prediction[:, :, 1], (image.height, image.width))
    # prediction[prediction>THRESHOLD*255] = 255
    # prediction[prediction<THRESHOLD*255] = 0

    # Append transparency 4th channel to the 3 RGB image channels.
    transparent_image = np.append(np.array(image)[:, :, 0:3], prediction[: , :, None], axis=-1)
    transparent_image = Image.fromarray(transparent_image)


    # Send back the result image to the client
    # byte_io = io.BytesIO()
    # transparent_image.save(byte_io, 'PNG')
    # byte_io.seek(0)
    # return send_file(byte_io, mimetype='image/png')
    return prediction

@app.route('/')
def homepage():
    return render_template('index.html.slim', name='mako')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
