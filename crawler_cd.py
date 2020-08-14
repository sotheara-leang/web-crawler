import re
import os
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import copy

CONT_SEP = '|@@@|'

@dataclass
class Article:
    title: str
    content: str
    link: str
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

    title = soup.select('header h1.entry-title')
    title = title[0].text if len(title) == 1 else ''
    
    ps = soup.select('div.td-post-content p')
    contents = []
    for idx, p in enumerate(ps):
        if idx < len(ps) - 1:
            contents.append(p.text.strip().split('\n')[0])
        
    article = Article(title, ' '.join(contents), article_link, soup)

    return article

def save_article(article, output_dir):
    # save article
    file = '%s/%s' % (output_dir, articles_fname)
    with open(file, 'a', encoding='utf-8') as writer:
        writer.write('%s %s %s\n' % (article.title, CONT_SEP, article.content))

    # save article link
    file = '%s/%s' % (output_dir, links_fname)
    with open(file, 'a', encoding='utf-8') as writer:
        writer.write('%s\n' % article.link)

def get_articles_links(page):
    links = []
    e_links = page.select('h3.td-module-title a')
    for e in e_links:
        links.append(e['href'].strip())
    return links

def get_next_page(page):
    next_page = page.select('div.page-nav a')
    if len(next_page) > 0:
        return next_page[-1]['href']
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
    'news': ' https://www.cambodiadaily.com/page/1267/'
}

out_dir         = 'work/text/raw/cambodiadaily'
total_articles  = -1
line_break      = ' '
link_map        = {}
articles_fname  = 'articles.txt'
links_fname     = 'links.txt'

if __name__ == '__main__':
    run()
