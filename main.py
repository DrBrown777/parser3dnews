# mod parser 3d-news for TorrentPier-II 2.1.5 alpha
# ver 1.0 by dr_brown

from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote
from bs4 import BeautifulSoup
from time import sleep
import pymysql.cursors
import urllib
import time
import re

'''If use re-uploading images to your image hosting, set True (only chevereto support)'''
image_api = False
key_api = ''  # api key
url_api = ''  # url image hosting

network_news_forum_id = 2  # id forum news
bot_uid = -746
user_agent = 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
             'Chrome/78.0.3904.70 Safari/537.36'

global_url = 'https://3dnews.ru/'
url = 'https://3dnews.ru/news'

'''Connect to Database'''
db_connect = dict(host=' ', user=' ', password=' ', db=' ', charset='utf8mb4',
                  cursorclass=pymysql.cursors.DictCursor)

connection = pymysql.connect(**db_connect)


def run():
    try:
        with connection.cursor() as cursor:
            page = parse_html(url)
            if page is None:
                return False
            links = parse_links(page, cursor)
            if links is None:
                return False
            for link in links:
                html = parse_html(link)
                if html is None:
                    return False
                data = parse_inner_page(html)
                save_row(data, cursor)
                sleep(1)
    finally:
        connection.close()


def parse_html(parse_url):
    req = Request(parse_url, headers={'User-Agent': user_agent})
    try:
        page = BeautifulSoup(urlopen(req).read().decode('UTF-8'), 'html.parser')
    except HTTPError:
        return None
    return page


def parse_links(page, cursor):
    name_id = []
    try:
        for wrap in page.find_all('div', {'class': 'article-entry article-infeed marker_sw nImp0 nIcat10 cat_10 nIaft '
                                                   'newsAllFeedHideItem'}):
            name_id.append(wrap.get('id'))
    except AttributeError:
        return None
    links = []
    for ids in name_id:
        sql = "SELECT * FROM bb_news_grab WHERE import_id = %s"
        cursor.execute(sql, (ids,))
        result = cursor.fetchone()
        if result is not None:
            continue
        import_sql = "INSERT INTO bb_news_grab (import_id) VALUES (%s)"
        cursor.execute(import_sql, (ids,))
        connection.commit()
        links.append(global_url + ids)
    return links


def parse_inner_page(html):
    try:
        name_text = html.find('div', {'class': 'js-mediator-article'})
    except AttributeError:
        name_text = ''
    else:
        name_text = clear_url(name_text)
    try:
        name_title = html.find('h1', {'itemprop': 'headline'}).get_text('h1')
    except AttributeError:
        name_title = ''
    result = dict(text=name_text, title=name_title)
    return result


def clear_url(name_text):
    if image_api:
        images = name_text.find_all('img')
        upload_image = []
        pic_image = []
        for image in images:
            try:
                image_clr = urllib.parse.quote(image['src'], safe='-._~:/?#[]@!$&\'()*+,;=')
                pic_req = Request(url_api.format(key_api, image_clr))
                pic = urlopen(pic_req).read().decode('UTF-8')
                if pic == 'Invalid file source':
                    continue
                elif pic == 'File too big - max 2 MB':
                    continue
            except HTTPError:
                continue
            else:
                upload_image.append(image['src'])
                pic_image.append(pic)
    regex = r'<a.*?>([\s\S]*?)<\/a>'
    name_text = str(name_text)
    clear_text = re.sub(regex, r'\1', name_text)
    clear_text = re.sub(r'<br\s*?>', r' ', clear_text)
    clear_text = re.sub(r'\s+', r' ', clear_text)
    if image_api:
        for (a, b) in zip(upload_image, pic_image):
            clear_text = re.sub(a, b, clear_text)
    return clear_text


def save_row(data, cursor):
    topic_sql = "INSERT INTO bb_topics (topic_title, topic_poster, topic_time, forum_id, topic_status, " \
                "topic_type, topic_dl_type, topic_vote, topic_last_post_time) VALUES (%s, %s, %s, %s, " \
                "%s, %s, %s, %s, %s)"
    cursor.execute(topic_sql, (data['title'], bot_uid, time.time(), network_news_forum_id, '0', '0',
                               '0', '0', time.time(),))
    connection.commit()
    topic_last_id = "SELECT LAST_INSERT_ID() as last"
    cursor.execute(topic_last_id)
    topic_id = cursor.fetchone()
    post_sql = "INSERT INTO bb_posts (topic_id, forum_id, poster_id, post_username, post_time, " \
               "poster_ip) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(post_sql, (topic_id['last'], network_news_forum_id, bot_uid, 'Bot', time.time(),
                              '127.0.0.1',))
    connection.commit()
    post_last_id = "SELECT LAST_INSERT_ID() as last"
    cursor.execute(post_last_id)
    post_id = cursor.fetchone()
    update_topic = "UPDATE bb_topics SET topic_first_post_id = %s, topic_last_post_id = %s WHERE " \
                   "topic_id = %s"
    cursor.execute(update_topic, (post_id['last'], post_id['last'], topic_id['last'],))
    post_text_sql = "INSERT INTO bb_posts_text (post_id, post_text) VALUES (%s, %s)"
    cursor.execute(post_text_sql, (post_id['last'], data['text'],))
    update_forum = "UPDATE bb_forums SET forum_posts = forum_posts + 1, forum_last_post_id = %s, " \
                   "forum_topics = forum_topics + 1 WHERE forum_id = %s"
    cursor.execute(update_forum, (post_id['last'], network_news_forum_id,))
    connection.commit()


run()
