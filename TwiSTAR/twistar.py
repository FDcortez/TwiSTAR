# -*- coding: utf-8 -*-
"""TwiSTAR.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aYXOyrjOrRpC0fd1w0q52pC_5j04ELiv

# **TwiSTAR - Flat earth data**

##Librerías
"""

import os
import numpy as np 
import pandas as pd 
import re
import matplotlib.pyplot as plt
import plotly.express as px
!pip install neattext
import neattext as ntx

import nltk.downloader
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from collections import Counter
from nltk.util import ngrams

"""##Lectura de datos

Para el presente análisis de texto, se usa un dataset extraído con Tweepy y relacionado a *menciones* sobre "*flat earth*" en Twitter.
"""

data = pd.read_csv('flat_earth_tweets.csv')

data.head()

display(data.shape, str(data.shape[0])+" tweets in dataset")

data.info()

data['date'] = pd.to_datetime(data['date']).dt.date  #converting date column to date format
data.head()

"""##Detección preliminar de datos



*   Conteo de tweets en función de la localización del usuario.
*   Conteo de tweets en función de la plataforma utilizada por el usuario.


"""

#Conteo de tweets en función de la localización del usuario
plt.figure(figsize=(15,10))
data['user_location'].value_counts().nlargest(20).plot(kind='bar')
plt.xticks(rotation=60)

#Depuración de tweets duplicados
data=data.drop_duplicates('text')             
data.shape

data.source.value_counts()

#Visualización de los tweets en función de la plataforma utilizada por el usuario
plt.figure(figsize=(15,10))
data['source'].value_counts().nlargest(6).plot(kind='bar')
plt.xticks(rotation=80)

#Número de días considerados en el dataset
len(data['date'].unique())

data.sort_values(by=['date'], ascending=[True]).head(100)

"""##Limpieza de datos

Se puntualiza la data de interés y se depuran los demás elementos que no aportan valor al desarrollo del análisis.
"""

#Depuración de datos innecesarios
data.drop(columns={"id","user_name","user_description","user_created","user_followers",\
                   "user_friends","user_favourites","user_verified","hashtags","source","retweets","favorites","is_retweet"},inplace=True)

pd.set_option('display.max_colwidth', 700)
data.head()

#Limpieza de los datos del dataset a través de la librería neattext
data['clean_data']=data['text'].apply(ntx.remove_hashtags)
data['clean_data']=data['clean_data'].apply(ntx.remove_urls)
data['clean_data']=data['clean_data'].apply(ntx.remove_userhandles)
data['clean_data']=data['clean_data'].apply(ntx.remove_multiple_spaces)
data['clean_data']=data['clean_data'].apply(ntx.remove_special_characters)

data[['clean_data','text']].head()

"""# **Análisis de Sentimientos - Flat earth data**

##Librerías
"""

import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

lemmatizer = WordNetLemmatizer()
nltk.download('stopwords')
nltk.download('wordnet')

"""## Detección y depuración de stopwords

El lenguaje requiere del uso de artículos, preposiciones y pronombres, que en el presente análisis son denominados "*stopwords*" y que comúnmente son palabras que no tienden a generar ningún cambio en la polaridad del tweet.
"""

print(stopwords.words("english"))

#Detección de 'stopwords'
stop_words = stopwords.words('english')
len(stop_words),stop_words[5:10]

#Depuración de stopwords
def stopWords(tweet):
  clean_tweet = tweet
  clean_tweet = " ".join(word for word in clean_tweet.split() if word not in stop_words)
# clean_tweet = " ".join(lemmatizer.lemmatize(word) for word in clean_tweet.split())
  return clean_tweet

data['clean_data'] = data['clean_data'].apply(lambda x: stopWords(x))

data.head(100)

"""## Estudio de la polarización y subjetividad de los tweets"""

# Definición de la función que asigna polaridad/subjetividad a los tweets
from textblob import TextBlob
def blob_fun(text):
  senti = TextBlob(text)
  senti_polarity = senti.sentiment.polarity
  senti_subjectivity = senti.sentiment.subjectivity

  if senti_polarity > 0:
    res = 'Positive'

  elif senti_polarity < 0:
    res = 'Negative'

  elif senti_polarity == 0:
    res ="Neutral"

  result = {'polarity':senti_polarity,'subjectivity':senti_subjectivity,'sentiment':res}

  return result

blob_fun(data['clean_data'][5])

data['results'] = data['clean_data'].apply(blob_fun)

data.drop(columns={"user_location",'text'},inplace=True)

data.head(100)

data = data.join(pd.json_normalize(data=data['results']))

data.head()

# Clasificación de tweets por series
positive_tweet =  data[data['sentiment'] == 'Positive']['clean_data']
negative_tweet =  data[data['sentiment'] == 'Negative']['clean_data']
neutral_tweet =  data[data['sentiment'] == 'Neutral']['clean_data']

"""## Generación de WordClouds por opinión"""

# Definición de la función WordCloud
from wordcloud import WordCloud
def cloud_of_Words(tweet_cat,title):
    forcloud = ' '.join([tweet for tweet in tweet_cat])
    wordcloud = WordCloud(width =500,height = 300,random_state =5,max_font_size=110).generate(forcloud)
    plt.imshow(wordcloud, interpolation ='bilinear')
    plt.title(title)
    plt.axis('off')
    plt.show()
    plt.figure(figsize = (10,8))

# Creación de wordclouds por opinión
plt.figure(figsize = (10,8))
cloud_of_Words(positive_tweet, 'Opiniones Positivas')
cloud_of_Words(negative_tweet, 'Opiniones Negativas')
cloud_of_Words(neutral_tweet, 'Opiniones Neutrales')

"""## Visualización del análisis de sentimientos"""

# Clasificación de tweets por opinión
positive_tokens = [token for line in positive_tweet for token in line.split()]
negative_tokens = [token for line in negative_tweet for token in line.split()]
neutral_tokens = [token for line in neutral_tweet for token in line.split()]

# Obtención de palabras más usadas
from collections import Counter
def get_maxtoken(tweets,num=30):
  word_tokens = Counter(tweets)
  max_common = word_tokens.most_common(num)
  return dict(max_common)

def token_df_vis(x, title):
  df = pd.DataFrame(get_maxtoken(x).items(),columns=['words','count'])
  # plt.figure(figsize = (20,5))
  # plt.title(title)
  # plt.xticks(rotation=45)
  fig = px.bar(df,x='words',y='count',title = title)
  fig.show()

token_df_vis(positive_tokens,'Opiniones Positivas')
token_df_vis(negative_tokens,'Opiniones Negativas')
token_df_vis(neutral_tokens,'Opiniones Neutrales')

fig = px.scatter(data,x='polarity',y='subjectivity')
fig.show()

def percent(x,y):
  return print("Percentage of "+y+" tweets :",round(len(x)/data.shape[0]*100,3),"%")

percent(positive_tweet, 'positive')
percent(negative_tweet, 'negative')
percent(neutral_tweet, 'neutral')

data['sentiment'].value_counts().plot(kind='bar')