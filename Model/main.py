import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import pandas as pd

from keras.preprocessing import image, sequence
from keras.applications import VGG16
from keras.layers import Dense, Convolution2D, Dropout, LSTM, TimeDistributed, concatenate, Embedding, Bidirectional, Activation, RepeatVector, Merge
from keras.models import Sequential, Model
from keras.optimizers import Nadam



images_dir = os.listdir("./Flickr8k_Dataset/")
images_path = './Flickr8k_Dataset/'
captions_path = './Flickr8k.token.txt'

captions = open(captions_path, 'r').read().split("\n")

#Creating dictionary corresponding to the images
tokens = {}

for ix in range(len(captions)):
    temp = captions[ix].split("#")
    if temp[0] in tokens:
        tokens[temp[0]].append(temp[1][2:])
    else:
        tokens[temp[0]] = [temp[1][2:]]


print captions[2000].split("#")

print tokens[temp[0]]

print "Number of Training Images {}".format(len(images_dir))

vgg = VGG16(weights='imagenet', include_top=True, input_shape=(224,224,3))

def preprocess_input(img):
    img = img[:, :, :, ::-1] #RGB to BGR
    img[:, :, :, 0] -= 103.939 
    img[:, :, :, 1] -= 116.779
    img[:, :, :, 2] -= 123.68
    return img

def preprocessing(img_path):
    im = image.load_img(img_path, target_size=(224,224,3))
    im = image.img_to_array(im)
    im = np.expand_dims(im, axis=0)
    im = preprocess_input(im)
    return im

x = preprocessing(images_path+temp[0])
print x.shape

# vgg.summary()

vgg = Model(inputs=vgg.input, outputs=vgg.layers[-2].output)

# vgg.summary()

#Encoding Images using VGG 

def get_encoding(model, img):
    image = preprocessing(images_path+img)
    pred = model.predict(image)
    pred = np.reshape(pred, pred.shape[1])
    return pred

train_dataset = open('./fl_flickr_8k_train_dataset.txt','wb')
train_dataset.write("image_id\tcaptions\n")

train_encoded_images = {}

c_train = 0
for img in images_dir:
    train_encoded_images[img] = get_encoding(vgg, img)
    for capt in tokens[img]:
        caption = "<start> "+ capt + " <end>"
        train_dataset.write(img+"\t"+caption+"\n")
        train_dataset.flush()
        c_train += 1
train_dataset.close()

with open( "train_encoded_images.p", "wb" ) as pickle_f:
    pickle.dump(train_encoded_images, pickle_f )  

# Building Vocabulary #

pd_dataset = pd.read_csv("./fl_flickr_8k_train_dataset.txt", delimiter='\t')
ds = pd_dataset.values
print ds.shape

sentences = []
for ix in range(ds.shape[0]):
    sentences.append(ds[ix, 1])
    
print len(sentences)

words = [i.split() for i in sentences]

unique = []
for i in words:
    unique.extend(i)

print len(unique)

unique = list(set(unique))
print len(unique)

vocab_size = len(unique)

word_2_indices = {val:index for index, val in enumerate(unique)}
indices_2_word = {index:val for index, val in enumerate(unique)}

print word_2_indices['<start>']
print indices_2_word[3213]

max_len = 0

for i in sentences:
    i = i.split()
    if len(i) > max_len:
        max_len = len(i)

print max_len

# Creating Padded Sequences and Next Words 

padded_sequences, subsequent_words = [], []

for ix in range(ds.shape[0]):
    partial_seqs = []
    next_words = []
    text = ds[ix, 1].split()
    text = [word_2_indices[i] for i in text]
    for i in range(1, len(text)):
        partial_seqs.append(text[:i])
        next_words.append(text[i])
    padded_partial_seqs = sequence.pad_sequences(partial_seqs, max_len, padding='post')

    next_words_1hot = np.zeros([len(next_words), vocab_size], dtype=np.bool)
    
    #Vectorization
    for i,next_word in enumerate(next_words):
        next_words_1hot[i, next_word] = 1
        
    padded_sequences.append(padded_partial_seqs)
    subsequent_words.append(next_words_1hot)
    
padded_sequences = np.asarray(padded_sequences)
subsequent_words = np.asarray(subsequent_words)

print padded_sequences.shape
print subsequent_words.shape

with open('./train_encoded_images.p', 'rb') as f:
        encoded_images = pickle.load(f)

imgs = []

for ix in range(ds.shape[0]):
    imgs.append(encoded_images[ds[ix, 0]])

imgs = np.asarray(imgs)
print imgs.shape

captions = np.zeros([0, max_len])
next_words = np.zeros([0, vocab_size])

for ix in range(padded_sequences.shape[0]):#number_of_images):
    captions = np.concatenate([captions, padded_sequences[ix]])
    next_words = np.concatenate([next_words, subsequent_words[ix]])

np.save("./captions_first15k_imgs_final.npy", captions)
np.save("./next_words_first15k_imgs_final.npy", next_words)

print captions.shape
print next_words.shape

images = []

for ix in range(padded_sequences.shape[0]):
    for iy in range(padded_sequences[ix].shape[0]):
        images.append(imgs[ix])
        
images = np.asarray(images)

print images.shape

image_names = []

for ix in range(number_of_images):
    for iy in range(padded_sequences[ix].shape[0]):
        image_names.append(ds[ix, 0])
        
print len(image_names)

embedding_size = 128

image_model = Sequential()

image_model.add(Dense(embedding_size, input_shape=(4096,), activation='relu'))
image_model.add(RepeatVector(max_len))

image_model.summary()

language_model = Sequential()

language_model.add(Embedding(input_dim=vocab_size, output_dim=embedding_size, input_length=max_len))
language_model.add(LSTM(256, return_sequences=True))
language_model.add(TimeDistributed(Dense(embedding_size)))

language_model.summary()

model = Sequential()

model.add(Merge([image_model, language_model], mode='concat', concat_axis=-1))
model.add(Bidirectional(LSTM(1000, return_sequences=False)))
model.add(Dense(vocab_size))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer=Nadam(lr=1e-4), metrics=['accuracy'])
model.summary()

model.fit([images, captions], next_words, batch_size=512, epochs=40)#, shuffle=False)

model.save_weights("./weights_second.h5")

test_img = images[11004]

def predict_captions(image):
    start_word = ["<start>"]
    while True:
        par_caps = [word_2_indices[i] for i in start_word]
        par_caps = sequence.pad_sequences([par_caps], maxlen=max_len, padding='post')
        e = image
        preds = model.predict([np.array([e]), np.array(par_caps)])
        word_pred = indices_2_word[np.argmax(preds[0])]
        start_word.append(word_pred)
        
        if word_pred == "<end>" or len(start_word) > max_len:
            break
            
    return ' '.join(start_word[1:-1])

Argmax_Search = predict_captions(test_img)

def beam_search_predictions(image, beam_index = 3):
    start = [word_2_indices["<start>"]]
    
    start_word = [[start, 0.0]]
    
    while len(start_word[0][0]) < max_len:
        temp = []
        for s in start_word:
            par_caps = sequence.pad_sequences([s[0]], maxlen=max_len, padding='post')
            e = image
            preds = model.predict([np.array([e]), np.array(par_caps)])
            
            word_preds = np.argsort(preds[0])[-beam_index:]
            
            # Getting the top <beam_index>(n) predictions and creating a 
            # new list so as to put them via the model again
            for w in word_preds:
                next_cap, prob = s[0][:], s[1]
                next_cap.append(w)
                prob += preds[0][w]
                temp.append([next_cap, prob])
                    
        start_word = temp
        # Sorting according to the probabilities
        start_word = sorted(start_word, reverse=False, key=lambda l: l[1])
        # Getting the top words
        start_word = start_word[-beam_index:]
    
    start_word = start_word[-1][0]
    intermediate_caption = [indices_2_word[i] for i in start_word]

    final_caption = []
    
    for i in intermediate_caption:
        if i != '<end>':
            final_caption.append(i)
        else:
            break
    
    final_caption = ' '.join(final_caption[1:])
    return final_caption


Beam_Search_index_3 = beam_search_predictions(test_img, beam_index=3)
Beam_Search_index_5 = beam_search_predictions(test_img, beam_index=5)
Beam_Search_index_7 = beam_search_predictions(test_img, beam_index=7)

print "Agrmax Prediction : ",
print Argmax_Search
print "\n"
print "Beam Search Prediction with Index = 3 : ",
print Beam_Search_index_3
print "\n"
print "Beam Search Prediction with Index = 5 : ",
print Beam_Search_index_5
print "\n"
print "Beam Search Prediction with Index = 7 : ",
print Beam_Search_index_7

