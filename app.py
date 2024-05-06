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
# Function to generate PDF

# df = pd.DataFrame({
#     'A': [1, 2, 3],
#     'B': [4, 5, 6]
# })

def generate_pdf(df, website_name, start_date, finish_date):
    # Get current date and time
    now = datetime.now()
    # Format date and time for the PDF content
    pdf_date = now.strftime("%Y-%m-%d")
    pdf_time = now.strftime("%H:%M:%S")
    # Format date and time for the filename without '-' and ':'
    filename_date = now.strftime("%Y%m%d")
    filename_time = now.strftime("%H%M%S")

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)

    # Draw things on the PDF. Here's where the PDF generation happens.
    p.drawString(100, 790, f"Website: {website_name}")
    p.drawString(100, 770, f"Dates: {start_date + ' - ' + finish_date} ")
    p.setLineWidth(.3) # Set the line width
    p.line(100, 750, 500, 750) # Draw a line from x=100 to x=500 at y=710
    p.drawString(100, 720, f"Report Generation Date: {pdf_date}")
    p.drawString(100, 700, f"Report Generation Time: {pdf_time}")

    p.setLineWidth(.3) # Set the line width
    p.line(100, 680, 500, 680) # Draw a line from x=100 to x=500 at y=710

    p.drawString(100, 650, f"Number Of Articles Found: {len(df)}")
    p.drawString(100, 630, f"Sentiment Analysis Results:")

    from reportlab.lib.pagesizes import letter

    img_path = 'sentiment_analysis_results.png'
    p.drawImage(img_path, 100, 350, width=350, height=250)

    # Close the PDF object cleanly.
    p.showPage()
    p.save()

    # Get the value stored in the buffer and write it to a file.
    pdf = buffer.getvalue()
    buffer.close()

    # Create the filename using the current date and time without '-' and ':'
    filename = f"{filename_date}_{filename_time}.pdf"

    # Save the PDF to a file with the generated filename
    with open(filename, "wb") as f:
        f.write(pdf)

    # Return the path to the PDF
    return filename


def perform_sentiment_analysis(text):
    start = time.time()
    prediction = model.predict([text])
    end = time.time()
    results.append(prediction[0])

def format_date_for_url(date):
    return date.strftime("%d/%m/%Y").replace('/', '.')

start_date, finish_date = st.date_input("Выберите даты", [datetime.now(), datetime.now()], format="DD/MM/YYYY")

if st.button('CNews'):
    start = time.time()

    start_date_str = format_date_for_url(start_date)
    finish_date_str = format_date_for_url(finish_date)

    url = f'https://www.cnews.ru/archive/date_{start_date_str}_{finish_date_str}/type_top_lenta_articles/page_1'

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
        page_url = f'https://www.cnews.ru/archive/date_{start_date_str}_{finish_date_str}/type_top_lenta_articles/page_{page}'
        st.write(page_url)

        response = requests.get(page_url)
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')
        news_items = soup.find_all('div', class_='allnews_item')

        urls = [item.find('a')['href'] for item in news_items]
        result.append(urls)

        st.write(f'Длина for page {page}:')
        st.write(len(urls))

    # urls_list = result
    urls_list = [url for sublist in result for url in sublist]
    st.write('urls_list:', urls_list)
    def extract_article_details(urls_list):
        articles_details = []
        count = 0
        for url in urls_list:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the title from the <h1> tag
            title_tag = soup.find('h1')
            title = title_tag.get_text(strip=True) if title_tag else "No title found"

            # Extract the main text/content of the article from <p> tags
            content_paragraphs = soup.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in content_paragraphs)

            # Optionally extract the date and time
            date_tag = soup.find('time', class_='article-date-desktop')
            date_time = date_tag.get_text(strip=True) if date_tag else "No date found"

            # Append the extracted details to the list
            articles_details.append((title, content, date_time, url))
            count += 1
            st.write('count:', count)
            st.write('title:', title)
            st.write('content:', content)
            st.write('url:', url)

        return articles_details


 # Example usage
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
                'sentiment': results[-1] # Use the last sentiment result
            })
        else:
            articles_data.append({
                'title': article[0],
                'text': article[1],
                'url': article[2]
                # 'sentiment': results[-1] # Use the last sentiment result
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

        colors = ['lightcoral', 'lightgray', 'lightgreen', 'lightblue'] # Example colors

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors)])
        fig.update_layout(title_text='Sentiment Analysis Results', plot_bgcolor='rgba(0,0,0,0)') # Set background color to transparent

        # Save the figure as a PNG file
        pio.write_image(fig, 'sentiment_analysis_results.png')

        # Display the figure in Streamlit
        st.plotly_chart(fig)

    end = time.time()
    st.write('Время на обработку запроса: ', round(end-start, 2), 'seconds')

    # df = pd.DataFrame({
    # 'A': [1, 2, 3],
    # 'B': [4, 5, 6]
    # })



    # Example usage
    # Assuming 'df' is a pandas DataFrame

    filename = generate_pdf(df, 'CNews', start_date_str, finish_date_str)
    st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")

if st.button('Время электроники'):
    start = time.time()


    def fetch_article_dates(page_number, urls_list):
        url = f"https://russianelectronics.ru/page/{page_number}/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        flag = False
        articles = []
        for article in soup.find_all('article'):
            # Use select() to find the date element with multiple class names
            date_element = article.select_one('time.entry-date.published, time.entry-date.published.updated')
            title_element = article.find('h2', class_='entry-title card-title').find('a', class_='text-dark')
            if date_element and title_element:
                date_text = date_element.get('datetime')
                date_obj = datetime.strptime(date_text, "%Y-%m-%dT%H:%M:%S%z")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                print('Date type:', type(formatted_date))
                title = title_element.get_text()
                urltest = title_element.get('href')
                articles.append((formatted_date))
                if datetime.strptime(start_date, "%d.%m.%Y") <= datetime.strptime(formatted_date, "%d.%m.%Y") <= datetime.strptime(finish_date, "%d.%m.%Y"):
                    urls_list.append(urltest)
                    # articles.append((formatted_date))
        return articles

    start_date_str = format_date_for_url(start_date)
    finish_date_str = format_date_for_url(finish_date)
    start_date = start_date_str
    finish_date = finish_date_str
    start_date_page = -1
    finish_date_page = -1
    start_date_found = False
    finish_date_found = False
    urls_list = []
    current_page = 1
    while not start_date_found or not finish_date_found:
        articles = fetch_article_dates(current_page, urls_list)
        st.write(current_page)
        st.write(articles)
        if current_page == 1:
            if start_date == finish_date and len(articles) == 0:
                st.write('Статьи не найдены')
                break
            if len(articles) > 0:
                if datetime.strptime(finish_date, "%d.%m.%Y") > datetime.strptime(articles[0], "%d.%m.%Y"):
                    finish_date = articles[0]
                    st.write('HERE')
                    break
        if start_date in articles:
            start_date_found = True
            start_date_page = current_page
        else:
            for i in range(len(articles) - 1):
                if datetime.strptime(articles[i], "%d.%m.%Y") > datetime.strptime(start_date, "%d.%m.%Y") > datetime.strptime(articles[i + 1], "%d.%m.%Y"):
                    start_date_found = True
                    start_date_page = current_page
                    break
        if finish_date in articles:
            finish_date_found = True
            finish_date_page = current_page
        else:
            for i in range(len(articles) - 1):
                if datetime.strptime(articles[i], "%d.%m.%Y") > datetime.strptime(finish_date, "%d.%m.%Y") > datetime.strptime(articles[i + 1], "%d.%m.%Y"):
                    finish_date_found = True
                    finish_date_page = current_page
                    break
        current_page += 1
    st.write(start_date_found)
    st.write(finish_date_found)



    pages_to_parse = [finish_date_page, start_date_page]
    for i in range(finish_date_page + 1, start_date_page):
        pages_to_parse.append(i)


    articles_data = []

    st.write('URLS LIST:', urls_list)

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
    config = Config()
    config.browser_user_agent = user_agent
    count = 0

    def extract_article_details(urls_list):
        articles_details = []
        count = 0
        for url in urls_list:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the title from the <h1> tag within the entry-header class
            title_tag = soup.find('h1', class_='entry-title')
            title = title_tag.get_text(strip=True) if title_tag else "No title found"

            # Extract the main text/content of the article from entry-content class
            content_div = soup.find('div', class_='entry-content')
            if content_div:
                content_paragraphs = content_div.find_all('p')
                content = ' '.join(p.get_text(strip=True) for p in content_paragraphs)
            else:
                content = "No content found"

            # Append the extracted details to the list
            articles_details.append((title, content, url))
            count += 1
            st.write('count:', count)
            st.write('title:', title)
            st.write('content:', content)
            st.write('url:', url)

        return articles_details


    # Example usage
    articles_info = extract_article_details(urls_list)

    articles_data = []

    for article in articles_info:

        perform_sentiment_analysis(article[1])

        if len(urls_list) > 0:
            articles_data.append({
                'title': article[0],
                'text': article[1],
                'url': article[2],
                'sentiment': results[-1] # Use the last sentiment result
            })
        else:
            articles_data.append({
                'title': article[0],
                'text': article[1],
                'url': article[2]
                # 'sentiment': results[-1] # Use the last sentiment result
            })

    df = pd.DataFrame(articles_data)

    st.write(df)

    df.to_csv('articles_data.csv', mode='a', index=False, header=False)

    # df_2 = pd.read_csv('articles_data.csv')

    end = time.time()
    st.write('Время на обработку запроса: ', round(end-start, 2), 'seconds')

    if len(urls_list) > 0:
        import plotly.io as pio
        sentiment_counts = df['sentiment'].value_counts().to_dict()
        labels = list(sentiment_counts.keys())
        values = list(sentiment_counts.values())

        colors = ['lightcoral', 'lightgray', 'lightgreen', 'lightblue'] # Example colors

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors)])
        fig.update_layout(title_text='Sentiment Analysis Results', plot_bgcolor='rgba(0,0,0,0)') # Set background color to transparent

        # Save the figure as a PNG file
        pio.write_image(fig, 'sentiment_analysis_results.png')

        # Display the figure in Streamlit
        st.plotly_chart(fig)

    end = time.time()
    st.write('Время на обработку запроса: ', round(end-start, 2), 'seconds')

    # df = pd.DataFrame({
    # 'A': [1, 2, 3],
    # 'B': [4, 5, 6]
    # })



    # Example usage
    # Assuming 'df' is a pandas DataFrame
    filename = generate_pdf(df, 'Vremya Elektroniki', start_date, finish_date)
    st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")

if 'button1' not in st.session_state:
    st.session_state['button1'] = False






if st.button('ECHEMISTRY'):
    website_name = 'ECHEMISTRY'
    start = time.time()
    st.session_state['button1'] = True


    def fetch_article_dates(page_number, urls_list):
        # Calculate the start parameter for pagination
        if current_page == 1:
            url = f"https://echemistry.ru/novosti/novosti-mikroelektroniki.html"
        else:
            start = 50 * (page_number - 1)
            url = f"https://echemistry.ru/novosti/novosti-mikroelektroniki.html?start={start}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []

        # Find all article blocks
        for article in soup.find_all('div', class_='row blog blog-medium margin-bottom-40'):
            # Extract the title and URL
            title_element = article.find('h2').find('a')
            title = title_element.get_text(strip=True)
            article_url = title_element.get('href')
            # Extract the date
            date_icon = article.find('i', class_='fa fa-calendar')
            if date_icon:
                # Check the next sibling directly
                next_sibling = date_icon.next_sibling
                if next_sibling and not next_sibling.strip():  # If it's whitespace
                    date_element = next_sibling.next_sibling  # Try the next next sibling
                else:
                    date_element = next_sibling
            else:
                date_element = None

            # Now check if date_element contains the expected date or further processing is needed
            if date_element:
                date_text = date_element.strip()
            else:
                date_text = "Date not found"
            # Parse and format the date
            if date_text:
                date_obj = datetime.strptime(date_text, "%d.%m.%Y")
                formatted_date = date_obj.strftime("%d.%m.%Y")
                articles.append(formatted_date)
                # Check if the date is within the desired range (assuming start_date and finish_date are defined)
                if datetime.strptime(start_date, "%d.%m.%Y") <= date_obj <= datetime.strptime(finish_date, "%d.%m.%Y"):
                    urls_list.append('https://echemistry.ru/' + article_url)
                    # articles.append(formatted_date)

        return articles

    # Test the function
    # start_date = '08.02.2024'
    # finish_date = '13.02.2024'
    start_date_str = format_date_for_url(start_date)
    finish_date_str = format_date_for_url(finish_date)
    start_date = start_date_str
    finish_date = finish_date_str
    start_date_page = -1
    finish_date_page = -1
    start_date_found = False
    finish_date_found = False
    urls_list = []
    current_page = 1
    while not start_date_found or not finish_date_found:
        articles = fetch_article_dates(current_page, urls_list)
        st.write(current_page)
        st.write(articles)
        if current_page == 1:
            if start_date == finish_date and len(articles) == 0:
                st.write('Статьи не найдены')
                break
            if len(articles) > 0:
                if datetime.strptime(finish_date, "%d.%m.%Y") > datetime.strptime(articles[0], "%d.%m.%Y"):
                    finish_date = articles[0]
                    st.write('HERE')
                    break
        if start_date in articles:
            start_date_found = True
            start_date_page = current_page
        else:
            for i in range(len(articles) - 1):
                if datetime.strptime(articles[i], "%d.%m.%Y") > datetime.strptime(start_date, "%d.%m.%Y") > datetime.strptime(articles[i + 1], "%d.%m.%Y"):
                    start_date_found = True
                    start_date_page = current_page
                    break
        if finish_date in articles:
            finish_date_found = True
            finish_date_page = current_page
        else:
            for i in range(len(articles) - 1):
                if datetime.strptime(articles[i], "%d.%m.%Y") > datetime.strptime(finish_date, "%d.%m.%Y") > datetime.strptime(articles[i + 1], "%d.%m.%Y"):
                    finish_date_found = True
                    finish_date_page = current_page
                    break
        current_page += 1




    pages_to_parse = [finish_date_page, start_date_page]
    for i in range(finish_date_page + 1, start_date_page):
        pages_to_parse.append(i)

    def extract_article_details(urls_list):
        articles_details = []
        count = 0
        for url in urls_list:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract the title from the <title> tag
            title_tag = soup.find('title')
            title = title_tag.get_text() if title_tag else "No title found"

            # Extract the main text/content of the article
            content_elements = soup.find_all('p')
            content = ' '.join(p.get_text(strip=True) for p in content_elements)

            # Append the extracted details to the list
            articles_details.append((title, content, url))

            count += 1
            st.write('count:', count)
            st.write('title:', title)
            st.write('content:', content)
            st.write('url:', url)

        return articles_details

    # Example usage
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
                'sentiment': results[-1] # Use the last sentiment result
            })
        else:
            articles_data.append({
                'title': article[0],
                'text': article[1],
                'url': article[2]
                # 'sentiment': results[-1] # Use the last sentiment result
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

        colors = ['lightcoral', 'lightgray', 'lightgreen', 'lightblue'] # Example colors

        fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker_colors=colors)])
        fig.update_layout(title_text='Sentiment Analysis Results', plot_bgcolor='rgba(0,0,0,0)') # Set background color to transparent

        # Save the figure as a PNG file
        pio.write_image(fig, 'sentiment_analysis_results.png')

        # Display the figure in Streamlit
        st.plotly_chart(fig)

    end = time.time()
    st.write('Время на обработку запроса: ', round(end-start, 2), 'seconds')

    # df = pd.DataFrame({
    # 'A': [1, 2, 3],
    # 'B': [4, 5, 6]
    # })



    # Example usage
    # Assuming 'df' is a pandas DataFrame
    filename = generate_pdf(df, website_name, start_date, finish_date)
    st.success(f"PDF-отчет успешно сгенерирован. Название отчета: {filename}")






