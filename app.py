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


model = pickle.load(open('twitter_sentiment.pkl', 'rb'))
results = []

from reportlab.pdfgen import canvas
import io


def generate_pdf(df, website_name, start_date, finish_date):
    now = datetime.now()
    pdf_date = now.strftime("%Y-%m-%d")
    pdf_time = now.strftime("%H:%M:%S")
    filename_date = now.strftime("%Y%m%d")
    filename_time = now.strftime("%H%M%S")
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 790, f"Website: {website_name}")
    p.drawString(100, 770, f"Dates: {start_date + ' - ' + finish_date} ")
    p.setLineWidth(.3)
    p.line(100, 750, 500, 750)
    p.drawString(100, 720, f"Report Generation Date: {pdf_date}")
    p.drawString(100, 700, f"Report Generation Time: {pdf_time}")
    p.setLineWidth(.3)
    p.line(100, 680, 500, 680)
    p.drawString(100, 650, f"Number Of Articles Found: {len(df)}")
    p.drawString(100, 630, f"Sentiment Analysis Results:")
    from reportlab.lib.pagesizes import letter
    img_path = 'sentiment_analysis_results.png'
    p.drawImage(img_path, 100, 350, width=350, height=250)
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    filename = f"{filename_date}_{filename_time}.pdf"
    with open(filename, "wb") as f:
        f.write(pdf)
    return filename


def perform_sentiment_analysis(text):
    start = time.time()
    prediction = model.predict([text])
    end = time.time()
    results.append(prediction[0])

def format_date_for_url(date):
    return date.strftime("%d/%m/%Y").replace('/', '.')

start_date, finish_date = st.date_input("Выберите даты", [datetime.now(), datetime.now()], format="DD/MM/YYYY")
start_date = format_date_for_url(start_date)
finish_date = format_date_for_url(finish_date)

if st.button('CNews'):
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
        st.write(page_number)
    else:
        print("No next page link found.")
        page_number = 1
    result = []
    articles_data = []
    for page in range(1, page_number + 1):
        page_url = f'https://www.cnews.ru/archive/date_{start_date}_{finish_date}/type_top_lenta_articles/page_{page}'
        st.write(page_url)

        response = requests.get(page_url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.find_all('div', class_='allnews_item')

        urls = [item.find('a')['href'] for item in news_items]
        result.append(urls)

        st.write(f'Длина for page {page}:')
        st.write(len(urls))
    urls_list = [url for sublist in result for url in sublist]
    st.write('urls_list:', urls_list)
    def extract_article_details(urls_list):
        articles_details = []
        count = 0
        for url in urls_list:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "No title found"
            content_paragraphs = soup.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in content_paragraphs)
            date_tag = soup.find('time', class_='article-date-desktop')
            date_time = date_tag.get_text(strip=True) if date_tag else "No date found"
            articles_details.append((title, content, date_time, url))
            count += 1
            st.write('count:', count)
            st.write('title:', title)
            st.write('content:', content)
            st.write('url:', url)

        return articles_details

    articles_info = extract_article_details(urls_list)
    for article in articles_info:
        st.write("Title:", article[0])
        st.write("Content:", article[1])
        st.write("URL:", article[2])
        st.write("\n---\n")

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

    df = pd.DataFrame(articles_data)

    st.write(df)

    df.to_csv('articles_data.csv', mode='a', index=False, header=False)

    df_2 = pd.read_csv('articles_data.csv')

    end = time.time()
    st.write('Время на обработку запроса: ', round(end-start, 2), 'seconds')

    if len(urls_list) > 0:
        import plotly.io as pio
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        labels = list(sentiment_counts.keys())
        values = list(sentiment_counts.values())

        colors = ['lightcoral', 'lightgray', 'lightgreen', 'lightblue']

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors)])
        fig.update_layout(title_text='Sentiment Analysis Results', plot_bgcolor='rgba(0,0,0,0)')
        pio.write_image(fig, 'sentiment_analysis_results.png')
        st.plotly_chart(fig)

    end = time.time()
    st.write('Время на обработку запроса: ', round(end-start, 2), 'seconds')

    filename = generate_pdf(df, 'CNews', start_date, finish_date)
    st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")

def generate_pdf_success():
    filename = generate_pdf(df, 'Vremya Elektroniki', start_date, finish_date)
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

    df = pd.DataFrame(articles_data)

    st.markdown('<span style="font-size: 20px; font-weight: bold;">Датасет статей</span>', unsafe_allow_html=True)
    st.write(df)

    df.to_csv('articles_data.csv', mode='a', index=False, header=False)

    if len(urls_list) > 0:
        import plotly.io as pio
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        labels = list(sentiment_counts.keys())
        values = list(sentiment_counts.values())

        colors = ['lightcoral', 'lightgray', 'lightgreen', 'lightblue']

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors)])
        fig.update_layout(title_text='Sentiment Analysis Results', plot_bgcolor='rgba(0,0,0,0)')
        pio.write_image(fig, 'sentiment_analysis_results.png')
        st.plotly_chart(fig)

    return df

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
if st.button('Время электроники'):
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
                print('Date type:', type(formatted_date))
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
        df = display_sentiment_analysis()
        df.drop('sentiment', axis=1, inplace=True)
        end = time.time()
        st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
        generate_pdf_success()



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
        df = display_sentiment_analysis()
        df.drop('sentiment', axis=1, inplace=True)
        end = time.time()
        st.write('Суммарное время на обработку запроса: ', round(end-start, 2), 'seconds')
        generate_pdf_success()
