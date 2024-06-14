import streamlit as st
import pickle
import re
import time
import requests
from bs4 import BeautifulSoup
from newspaper import Article, Config
import plotly
import plotly.graph_objects as go
import os
from datetime import datetime
import pandas as pd
from reportlab.pdfgen import canvas
import io

# model = pickle.load(open('twitter_sentiment.pkl', 'rb'))
results = []
neutralValue = 0
negativeValue = 0
skipValue = 0
positiveValue = 0
speechValue = 0
resultsDict = {'neutral': neutralValue, 'negative': negativeValue, 'skip': skipValue, 'positive': positiveValue, 'speech': speechValue}

from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel

tokenizer = RegexTokenizer()
model = FastTextSocialNetworkModel(tokenizer=tokenizer)

def format_date_for_url(date):
    return date.strftime("%d/%m/%Y").replace('/', '.')

start_date, finish_date = st.date_input("Выберите даты", [datetime.now(), datetime.now()], format="DD/MM/YYYY")
start_date = format_date_for_url(start_date)
finish_date = format_date_for_url(finish_date)


def generate_pdf_success(success):
  filename = generate_pdf(df, 'Vremya Elektroniki', start_date, finish_date, success)
  st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")

def display_sentiment_analysis():
  articles_data = []

  for article in articles_info:

      perform_sentiment_analysis(article[1])

      if len(urls_list) > 0:
          articles_data.append({
              'title': article[0],
              'text': article[1],
              'url': article[2],
              'sentiment': results[-1]
          })
      else:
          articles_data.append({
              'title': article[0],
              'text': article[1],
              'url': article[2]
          })
  resultsDict['neutral'] /= len(articles_info)
  resultsDict['negative'] /= len(articles_info)
  resultsDict['skip'] /= len(articles_info)
  resultsDict['positive'] /= len(articles_info)
  resultsDict['speech'] /= len(articles_info)
  df = pd.DataFrame(articles_data)
  if len(urls_list) > 0:
      import plotly.io as pio
      labels = list(resultsDict.keys())
      values = list(resultsDict.values())
      colors = {
          'neutral': '#D3D3D3',
          'negative': '#FFB6C1',
          'positive': '#90EE90',
          'speech': '#D2B48C',
          'skip': '#ADD8E6'
      }
      color_sequence = [colors[label] for label in labels]
      fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=color_sequence)])
      fig.update_layout(title_text='Результаты Анализа Тональности Текста', plot_bgcolor='rgba(0,0,0,0)')
      pio.write_image(fig, 'sentiment_analysis_results.png')
  st.markdown('<span style="font-size: 20px; font-weight: bold;">Датасет статей</span>', unsafe_allow_html=True)
  df.drop('sentiment', axis=1, inplace=True)
  st.write(df)
  df.to_csv('articles_data.csv', mode='a', index=False, header=False)
  st.plotly_chart(fig)
  # df = pd.read_csv('articles_data.csv', header=None)
  df.rename(columns={0: 'name', 1: 'text', 2: 'url'}, inplace=True)
  docs = df.text.tolist()
  from top2vec import Top2Vec
  success = False
  try:
    model = Top2Vec(docs)
    topic_sizes, topic_nums = model.get_topic_sizes()
    # st.write(topic_sizes)
    # st.write(topic_nums)
    topic_words, word_scores, topic_nums = model.get_topics(len(topic_nums))
    # for words, scores, num in zip(topic_words, word_scores, topic_nums):
    #   st.write(num)
    #   st.write(f"Words: {words}")
    documents, document_scores, document_ids = model.search_documents_by_topic(topic_num = 0, num_docs = 10)
    # for doc, score, doc_id, in zip(documents, document_scores, document_ids):
    #   st.write(f"Document: {doc_id}, Score: {score}")
    #   st.write("-------------")
    #   st.write()

    import pymorphy2

    # Инициализация морфологического анализатора
    morph = pymorphy2.MorphAnalyzer()

    # Приведение слов к словарной форме и удаление повторяющихся
    results_2 = []
    for words in topic_words:
        normalized_words = set(morph.parse(word)[0].normal_form for word in words)
        results_2.append(normalized_words)

    # Получение уникальных слов из всех множеств
    unique_words = sorted(set(word for result in results_2 for word in result))

    # Создание пустой DataFrame с заголовками
    df_2 = pd.DataFrame(0, index=range(len(results_2)), columns=unique_words)

    # Заполнение DataFrame
    for i, result in enumerate(results_2):
        for word in result:
            df_2.at[i, word] = 1
    
    # Инициализация морфологического анализатора
    morph = pymorphy2.MorphAnalyzer()

    # Приведение слов к словарной форме и удаление повторяющихся
    results_2 = []
    for words in topic_words:
        normalized_words = set(morph.parse(word)[0].normal_form for word in words)
        results_2.append(normalized_words)

    # Получение уникальных слов из всех множеств
    unique_words = sorted(set(word for result in results_2 for word in result))

    # Создание пустой DataFrame с заголовками
    df_3 = pd.DataFrame(0, index=range(df['text'].count()), columns=unique_words)

    # Заполнение DataFrame
    for i in range(df['text'].count()):
        words = df['text'][i].split()
        normalized_words = set(morph.parse(word)[0].normal_form for word in words)
        for word in normalized_words:
            if word in df_3.columns:
                df_3.at[i, word] = 1


    import numpy as np
    from collections import Counter

    # Примерные данные для df_2 и df_3
    # df_2 = pd.DataFrame(...)  # Замените на ваши данные
    # df_3 = pd.DataFrame(...)  # Замените на ваши данные

    # Создадим пустой список для хранения результатов
    results_2 = []

    # Пройдемся по каждой строке в df_3
    for i, row_3 in df_3.iterrows():
        max_scalar_product = -np.inf
        max_indices = []

        # Пройдемся по каждой строке в df_2
        for j, row_2 in df_2.iterrows():
            scalar_product = np.dot(row_3, row_2)

            if scalar_product > max_scalar_product:
                max_scalar_product = scalar_product
                max_indices = [j]
            elif scalar_product == max_scalar_product:
                max_indices.append(j)

        # Добавим результат в список
        results_2.append(max_indices)


    # Добавим новую колонку в df_3
    df_3['max_indices'] = results_2

    # Подсчитаем количество вхождений каждого индекса
    all_indices = [index for sublist in df_3['max_indices'] for index in sublist]
    counter = Counter(all_indices)

    # Выведем количество вхождений каждого индекса
    # st.write(counter)

    df['max_indices'] = results_2
    st.write(df)
    success = True 
  except Exception as e:
    st.write("Ошибка top2vec. Часть с top2vec будет отсутствовать в итогом отчете.")
    st.write(f"Детали ошибки: {e}")
  

  return df, success

def split_text(text, max_width, canvas, font_name="Helvetica", font_size=10):
    """
    Разбивает текст на строки, которые помещаются в заданную ширину.
    """
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if canvas.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines

def generate_pdf(df, website_name, start_date, finish_date, success):
  import io
  from datetime import datetime
  from reportlab.pdfgen import canvas
  from reportlab.lib.pagesizes import letter
  from transliterate import translit
  now = datetime.now()
  pdf_date = now.strftime("%Y-%m-%d")
  pdf_time = now.strftime("%H:%M:%S")
  filename_date = now.strftime("%Y%m%d")
  filename_time = now.strftime("%H%M%S")
  buffer = io.BytesIO()
  p = canvas.Canvas(buffer, pagesize=letter)
  
  # Основная информация
  y_position = 750  # Начинаем немного ниже
  p.drawString(100, y_position, f"Website: {website_name}")
  y_position -= 20
  p.drawString(100, y_position, f"Dates: {start_date + ' - ' + finish_date} ")
  y_position -= 20
  p.setLineWidth(.3)
  p.line(100, y_position, 500, y_position)
  y_position -= 20
  p.drawString(100, y_position, f"Report Generation Date: {pdf_date}")
  y_position -= 20
  p.drawString(100, y_position, f"Report Generation Time: {pdf_time}")
  y_position -= 20
  p.setLineWidth(.3)
  p.line(100, y_position, 500, y_position)
  y_position -= 20
  p.drawString(100, y_position, f"Number Of Articles Found: {len(df)}")
  y_position -= 20
  p.drawString(100, y_position, f"Sentiment Analysis Results:")
  y_position -= 20
  
  # Изображение
  img_path = 'sentiment_analysis_results.png'
  p.drawImage(img_path, 100, y_position - 250, width=350, height=250)
  if success:
    # Переход на новую страницу
    p.showPage()
    
    # Добавление информации о множестве значений max_indices и их процентном соотношении
    y_position = 750
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, y_position, "Topics and their percentages:")
    y_position -= 20
    
    all_max_indices = [index for sublist in df['max_indices'] for index in sublist]
    unique_indices = set(all_max_indices)
    total_count = len(all_max_indices)
    percentages = {index: (all_max_indices.count(index) / total_count) * 100 for index in unique_indices}
    
    p.setFont("Helvetica", 10)
    for index, percentage in percentages.items():
        p.drawString(100, y_position, f"{index}: {percentage:.2f}%")
        y_position -= 20
    
    y_position -= 20  # Отступ перед списком статей
    
    # Добавление информации о статьях
    for i in range(len(df)):
        if y_position < 100:  # Проверка, нужно ли перейти на новую страницу
            p.showPage()
            y_position = 750
        
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y_position, f"Article {i}")
        y_position -= 20
        
        p.setFont("Helvetica", 10)
        name_translit = translit(df.iloc[i]['title'], 'ru', reversed=True)
        lines = split_text(f"Name: {name_translit}", 400, p)
        for line in lines:
            p.drawString(100, y_position, line)
            y_position -= 20
        
        lines = split_text(f"URL: {df.iloc[i]['url']}", 400, p)
        for line in lines:
            p.drawString(100, y_position, line)
            y_position -= 20
        
        lines = split_text(f"Topic: {df.iloc[i]['max_indices']}", 400, p)
        for line in lines:
            p.drawString(100, y_position, line)
            y_position -= 20
        
        y_position -= 20  # Отступ перед следующей статьёй
  
  p.save()
  pdf = buffer.getvalue()
  buffer.close()
  
  filename = f"{filename_date}_{filename_time}.pdf"
  with open(filename, "wb") as f:
      f.write(pdf)
  
  return filename



def perform_sentiment_analysis(text):
  text = [text]
  start = time.time()
  prediction = model.predict(text, k=5)
  resultsDict['neutral'] += prediction[0]['neutral']
  resultsDict['negative'] += prediction[0]['negative']
  resultsDict['skip'] += prediction[0]['skip']
  resultsDict['positive'] += prediction[0]['positive']
  resultsDict['speech'] += prediction[0]['speech']
  end = time.time()
  results.append(prediction[0])


if st.button('CNews'):
  start = time.time()
  def get_urls_cnews():
      start = time.time()
      url = f'https://www.cnews.ru/archive/date_{start_date}_{finish_date}/type_top_lenta_articles/page_1'
      response = requests.get(url)
      html_content = response.text
      soup = BeautifulSoup(html_content, 'html.parser')
      next_page_link = soup.find('a', class_='ff')
      if next_page_link:
          href = next_page_link['href']
          page_number = int(href.split('page_')[-1])
          print(f"The last page number is: {page_number}")
      else:
          print("No next page link found.")
          page_number = 1
      result = []
      for page in range(1, page_number + 1):
          page_url = f'https://www.cnews.ru/archive/date_{start_date}_{finish_date}/type_top_lenta_articles/page_{page}'
          response = requests.get(page_url)
          html_content = response.text
          soup = BeautifulSoup(html_content, 'html.parser')
          news_items = soup.find_all('div', class_='allnews_item')
          urls = [item.find('a')['href'] for item in news_items]
          result.append(urls)
      urls_list = [url for sublist in result for url in sublist]

      return urls_list
  def extract_article_details(urls_list):
      articles_details = []
      count = 0
      st.markdown('<span style="font-size: 20px; font-weight: bold;">Парсинг статей</span>', unsafe_allow_html=True)
      startparsing = time.time()
      numberOfArticles = len(urls_list)
      for url in urls_list:
          response = requests.get(url)
          soup = BeautifulSoup(response.text, 'html.parser')
          title_tag = soup.find('h1')
          title = title_tag.get_text(strip=True) if title_tag else "No title found"
          content_paragraphs = soup.find_all('p')
          content = ' '.join(p.get_text(strip=True) for p in content_paragraphs)
          date_tag = soup.find('time', class_='article-date-desktop')
          date_time = date_tag.get_text(strip=True) if date_tag else "No date found"
          articles_details.append((title, content, url))
          count += 1
          st.write(f'Статья ({count}/{numberOfArticles}): {title}')
          st.write('URL:', url)
      endparsing = time.time()
      st.write('Время на парсинг статей: ', round(endparsing-startparsing, 2), 'seconds')
      return articles_details

  urls_list = get_urls_cnews()
  if len(urls_list) == 0:
      st.success('Статьи не найдены')
      end = time.time()
      st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
  else:
      articles_info = extract_article_details(urls_list)
      success = False
      df, success = display_sentiment_analysis()
      end = time.time()
      filename = generate_pdf(df, 'CNews', start_date, finish_date, success)
      st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
      st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")


def find_start_finish_date(start_date, finish_date, website_name):
  start_date_found = False
  finish_date_found = False
  urls_list = []
  current_page = 1
  startstartpage = time.time()
  startfinalpage = time.time()
  st.markdown('<span style="font-size: 20px; font-weight: bold;">Поиск страниц с начальной и конечной датами</span>', unsafe_allow_html=True)
  while not start_date_found or not finish_date_found:
      if website_name == 'Vremya Elektroniki':
          articles = fetch_article_dates_vremya_elektroniki(current_page, urls_list)
      if website_name == 'ECHEMISTRY':
          articles = fetch_article_dates_echemistry(current_page, urls_list)
      st.write('Текущая страница:', current_page)
      if current_page == 1:
          if len(urls_list) == 0:
              st.success('Статьи не найдены')
              return False, False, False
          if len(urls_list) > 0:
              if datetime.strptime(finish_date, "%d.%m.%Y") > datetime.strptime(articles[0], "%d.%m.%Y"):
                  finish_date = articles[0]
                  finish_date_page = 1
                  finish_date_found = True
      if start_date in articles:
          start_date_found = True
          start_date_page = current_page
          st.success('Страница с начальной датой найдена!')
          st.write('Номер страницы с начальной датой: ', start_date_page)
          endstartpage = time.time()
          st.write('Время на поиск страницы с начальной датой: ', round(endstartpage-startstartpage, 2), 'seconds')
      else:
          for i in range(len(articles) - 1):
              if datetime.strptime(articles[i], "%d.%m.%Y") > datetime.strptime(start_date, "%d.%m.%Y") > datetime.strptime(articles[i + 1], "%d.%m.%Y"):
                  start_date_found = True
                  start_date_page = current_page
                  st.success('Страница с начальной датой найдена!')
                  st.write('Номер страницы с начальной датой: ', start_date_page)
                  endstartpage = time.time()
                  st.write('Время на поиск страницы с начальной датой: ', round(endstartpage-startstartpage, 2), 'seconds')
                  break
      if finish_date in articles:
          finish_date_found = True
          finish_date_page = current_page
          st.success('Страница с конечной датой найдена!')
          st.write('Номер страницы с конечной датой: ', finish_date_page)
          endfinalpage = time.time()
          st.write('Время на поиск страницы с конечной датой: ', round(endfinalpage-startfinalpage, 2), 'seconds')
      else:
          for i in range(len(articles) - 1):
              if datetime.strptime(articles[i], "%d.%m.%Y") > datetime.strptime(finish_date, "%d.%m.%Y") > datetime.strptime(articles[i + 1], "%d.%m.%Y"):
                  finish_date_found = True
                  finish_date_page = current_page
                  st.success('Страница с конечной датой найдена!')
                  st.write('Номер страницы с конечной датой: ', finish_date_page)
                  endfinalpage = time.time()
                  st.write('Время на поиск страницы с конечной датой: ', round(endfinalpage-startfinalpage, 2), 'seconds')
                  break
      current_page += 1

  return start_date_page, finish_date_page, urls_list

if st.button('Время Электроники'):
  def fetch_article_dates_vremya_elektroniki(page_number, urls_list):
      url = f"https://russianelectronics.ru/page/{page_number}/"
      response = requests.get(url)
      soup = BeautifulSoup(response.text, 'html.parser')
      articles = []
      for article in soup.find_all('article'):
          date_element = article.select_one('time.entry-date.published, time.entry-date.published.updated')
          title_element = article.find('h2', class_='entry-title card-title').find('a', class_='text-dark')
          if date_element and title_element:
              date_text = date_element.get('datetime')
              date_obj = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S%z")
              formatted_date = date_obj.strftime("%d.%m.%Y")
              urltest = title_element.get('href')
              articles.append(formatted_date)
              if datetime.strptime(start_date, "%d.%m.%Y") <= datetime.strptime(formatted_date, "%d.%m.%Y") <= datetime.strptime(finish_date, "%d.%m.%Y"):
                  urls_list.append(urltest)
      return articles

  def extract_article_details_vremya_elektroniki(urls_list):
      articles_details = []
      count = 0
      numberOfArticles = len(urls_list)
      st.markdown('<span style="font-size: 20px; font-weight: bold;">Парсинг статей</span>', unsafe_allow_html=True)
      startparsing = time.time()
      for url in urls_list:
          response = requests.get(url)
          soup = BeautifulSoup(response.text, 'html.parser')
          title_tag = soup.find('h1', class_='entry-title')
          title = title_tag.get_text(strip=True) if title_tag else "No title found"
          content_div = soup.find('div', class_='entry-content')
          if content_div:
              content_paragraphs = content_div.find_all('p')
              content = ' '.join(p.get_text(strip=True) for p in content_paragraphs)
          else:
              content = "No content found"
          articles_details.append((title, content, url))
          count += 1
          st.write(f'Статья ({count}/{numberOfArticles}): {title}')
          st.write('URL:', url)
      endparsing = time.time()
      st.write('Время на парсинг статей: ', round(endparsing-startparsing, 2), 'seconds')
      return articles_details

  start = time.time()
  start_date_page, finish_date_page, urls_list = find_start_finish_date(start_date, finish_date, 'Vremya Elektroniki')
  if not start_date_page and not finish_date_page and not urls_list:
      end = time.time()
      st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
  else:
      st.write('Количество статей:', len(urls_list))
      articles_info = extract_article_details_vremya_elektroniki(urls_list)
      success = False
      df = display_sentiment_analysis(success)
      end = time.time()
      st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
      generate_pdf_success(success)


if st.button('ECHEMISTRY'):
  def fetch_article_dates_echemistry(page_number, urls_list):
      if page_number == 1:
          url = f"https://echemistry.ru/novosti/novosti-mikroelektroniki.html"
      else:
          start = 50 * (page_number - 1)
          url = f"https://echemistry.ru/novosti/novosti-mikroelektroniki.html?start={start}"
      response = requests.get(url)
      soup = BeautifulSoup(response.text, 'html.parser')
      articles = []
      for article in soup.find_all('div', class_='row blog blog-medium margin-bottom-40'):
          title_element = article.find('h2').find('a')
          title = title_element.get_text(strip=True)
          article_url = title_element.get('href')
          date_icon = article.find('i', class_='fa fa-calendar')
          if date_icon:
              next_sibling = date_icon.next_sibling
              if next_sibling and not next_sibling.strip():
                  date_element = next_sibling.next_sibling
              else:
                  date_element = next_sibling
          else:
              date_element = None
          if date_element:
              date_text = date_element.strip()
          else:
              date_text = "Дата не найдена"
          if date_text:
              date_obj = datetime.strptime(date_text, "%d.%m.%Y")
              formatted_date = date_obj.strftime("%d.%m.%Y")
              articles.append(formatted_date)
              if datetime.strptime(start_date, "%d.%m.%Y") <= date_obj <= datetime.strptime(finish_date, "%d.%m.%Y"):
                  urls_list.append('https://echemistry.ru/' + article_url)

      return articles



  def extract_article_details_echemistry(urls_list):
      articles_details = []
      count = 0
      numberOfArticles = len(urls_list)
      st.markdown('<span style="font-size: 20px; font-weight: bold;">Парсинг статей</span>', unsafe_allow_html=True)
      startparsing = time.time()
      for url in urls_list:
          response = requests.get(url)
          soup = BeautifulSoup(response.text, 'html.parser')

          title_tag = soup.find('title')
          title = title_tag.get_text() if title_tag else "No title found"

          content_elements = soup.find_all('p')
          content = ' '.join(p.get_text(strip=True) for p in content_elements)

          articles_details.append((title, content, url))

          count += 1
          st.write(f'Статья ({count}/{numberOfArticles}): {title}')
          st.write('URL:', url)
      endparsing = time.time()
      st.write('Время на парсинг статей: ', round(endparsing-startparsing, 2), 'seconds')

      return articles_details




  website_name = 'ECHEMISTRY'
  start = time.time()
  # current_page = 1
  start_date_page, finish_date_page, urls_list = find_start_finish_date(start_date, finish_date, 'ECHEMISTRY')
  if not start_date_page and not finish_date_page and not urls_list:
      end = time.time()
      st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
  else:
      st.write('Количество статей:', len(urls_list))
      articles_info = extract_article_details_echemistry(urls_list)
      success = False
      df, success = display_sentiment_analysis()
      end = time.time()
      filename = generate_pdf(df, 'ECHEMISTRY', start_date, finish_date, success)
      st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
      st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")
