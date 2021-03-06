import re
import os
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

CONT_SEP = '|@@@|'

@dataclass
class Article:
    title: str
    content: str
    link: str
    audio_link: str
    soup: any

def clean_article(article):
    link = article.link.strip()
    article.link = link

    content = article.content.strip()
    content = re.sub(r"\s{2,}", " ", content)
    content = content.replace('\u200b', ' ')
    content = content.replace('\n', line_break).replace('\r', line_break)
    article.content = content

def extract_article(article_link):
    print('Extract article: ', article_link)

    page = requests.get(article_link)
    if page.status_code != 200:
        print('Error loading article page: ', article_link)
        return

    soup = BeautifulSoup(page.content, 'html.parser')
    
    audio = soup.select('audio.story_audio')
    if audio is None or len(audio) == 0:
        return None
    else:
        title = soup.title.text
        content = soup.select('div#storytext')[0].text
        audio_link = audio[0]['src']
        article = Article(title, content, article_link, audio_link, soup)

    return article

def save_article(article, output_dir):
    audio_fname = article.video_link.rsplit('/', 1)[-1]
    
    # save article
    file = '%s/%s' % (output_dir, articles_fname)
    with open(file, 'a', encoding='utf-8') as writer:
        writer.write('%s %s %s\n' % (audio_fname, CONT_SEP, article.content))

    # save article link
    file = '%s/%s' % (output_dir, links_fname)
    with open(file, 'a', encoding='utf-8') as writer:
        writer.write('%s\n' % article.link)
        
    # download audio
    r = requests.get(article.video_link)
    audio_file = '%s/audio/%s' % (output_dir, audio_fname)
    with open(audio_file, 'wb') as f:
        f.write(r.content)

def get_articles_links(page):
    links = []
    e_links = page.select('div.sectionteaser h2 a')
    for e in e_links:
        links.append(e['href'].strip())
    return links

def get_next_page(page):
    next_page = page.select('span.next a')
    if len(next_page) > 0:
        return next_page[0]['href']
    else:
        return None

def extract_articles_in_page(page_link):
    print('--> Extract in page: ', page_link)

    response = requests.get(page_link)
    if response.status_code != 200:
        print('Error loading page: ', page_link)
        return

    page = BeautifulSoup(response.content, 'html.parser')
    articles_links = get_articles_links(page)

    print('Articles Nb: ', len(articles_links))

    articles = []
    for link in articles_links:
        # check if link already extracted
        if link_map.get(link) is not None:
            print('Skip article: ', link)
            continue

        article = extract_article(link)
        if article is None:
            continue
            
        clean_article(article)
        articles.append(article)

    next_page = get_next_page(page)

    return articles, next_page

def run():
    # make output dir
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    for module, module_url in modules.items():
        # 
        print('Crawling module %s ..... ' % module)
        
        # make module dir
        module_dir = '%s/%s' % (out_dir, module)
        if not os.path.exists(module_dir):
            os.makedirs(module_dir)
            os.makedirs('%s/audio' % module_dir)
        
        # load crawled links
        link_file = '%s/%s' % (module_dir, links_fname)
        if os.path.exists(link_file) is True:
            with open(link_file, 'r') as reader:
                print('--> Load extracted links')
                for link in reader:
                    link_map[link.strip()] = ''

        # crawl
        url = module_url
        article_counter = 0
        while True:
            if url is None:
                break

            if total_articles != -1 and article_counter > total_articles:
                break
                
            articles, next_url = extract_articles_in_page(url)
            for article in articles:
                save_article(article, module_dir)
                
                link_map[article.link] = ''
                article_counter += 1
    
            print('--> Total article: ', article_counter)
    
            url = next_url

#####################

modules = {
    'social-economy': 'https://www.rfa.org/khmer/news/social-economy/story_archive',
    # 'economy': 'https://www.rfa.org/khmer/news/economy/story_archive',
    # 'human-rights': 'https://www.rfa.org/khmer/news/human-rights/story_archive',
    # 'environment': 'https://www.rfa.org/khmer/news/environment',
    # 'health': 'https://www.rfa.org/khmer/news/health',
    # 'history': 'https://www.rfa.org/khmer/news/history/story_archive',
    # 'law': 'https://www.rfa.org/khmer/news/law/story_archive',
    # 'krt': 'https://www.rfa.org/khmer/news/krt/story_archive',
    # 'politics': 'https://www.rfa.org/khmer/news/politics/story_archive',
    # 'analysis': 'https://www.rfa.org/khmer/news/analysis/story_archive',
    # 'land': 'https://www.rfa.org/khmer/news/land/story_archive'
}

out_dir         = 'work/raw/rfa'
total_articles  = -1
line_break      = ' '
link_map        = {}
articles_fname  = 'articles.txt'
links_fname     = 'links.txt'

if __name__ == '__main__':
    run()
    # extract_article('https://www.rfa.org/khmer/news/politics/7th-protest-of-families-of-jailed-cnrp-activists-07312020185537.html')
