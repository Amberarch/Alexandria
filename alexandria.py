#!/usr/bin/python3
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from urllib.request import urlopen
import datetime
import base64
import random
import pypub
import time
import sys
import re

args = sys.argv[1:]
template = args[0]
stories = args[1:]

def b64(src):
    return f"data:image/jpeg;base64,{base64.b64encode(src).decode('utf-8')}"

class TemplateWriter:
    def __init__(self, template_file) -> None:
        with open(template_file, 'r') as f:
            self.template = f.read()
    def story(self, name, author, auth_url, auth_img):
        self.output = self.template
        self.title = name
        self.output = self.output.replace('<!--TITLE-->', name)
        self.output = self.output.replace('<!--AUTH_NAME-->', author);
        self.output = self.output.replace('<!--AUTH_LINK-->', f'<a href="{auth_url}">{author}</a>')
        auth_img = b64(urlopen(auth_img).read())
        self.output = self.output.replace('<!--AUTH_ICON-->', f'<img src={auth_img}></img>')
    def set_cover(self, cover):
        if cover == "noimage":
            with open(cover, 'r') as c:
                img_data = b64(c.read())
        else:
            img_data = b64(urlopen(cover).read())
        self.output = self.output.replace('<!--COVER-->', f'<img src={img_data}></img>')
    def set_metadata(self, desc, genres, tags):
        self.output = self.output.replace('<!--SYNOPSIS-->', f'<p>{desc}</p>')
        genres = [f'<span class=genre>{genre}</span>' for genre in genres];
        self.output = self.output.replace('<!--GENRES-->', ''.join(genres))
        tags = [f'<span class=tag>{tag}</span>' for tag in tags];
        self.output = self.output.replace('<!--TAGS-->', ''.join(tags))
    def start_chapters(self, length, base_url):
        self.toc = ""
        self.contents = f'<contents id=contents style=display:none title="{self.title}" src="{base_url}">'
        self.len = length
    def chapter(self, index, chap, contents):
        self.contents += f'<chapter page={index + 1} title="{chap}"{" hasnext" if index < (self.len - 1) else ""}{" hasprev" if index > 0 else ""}>'
        self.toc += f'<li><a href="#{index + 1}">{chap}</a></li>'
        self.contents += contents
        self.contents += '</chapter>'
    def flush(self):
        self.contents += '</contents>'
        self.output = self.output.replace('<!--TOC-->', self.toc)
        self.output = self.output.replace('<!--CONTENTS-->', self.contents)
        self.output = f'<!-- Page generated using Alexandria on {datetime.datetime.now().strftime("%Y-%m-%d")} -->\n' + self.output
        with open(f"{self.title.replace(' ', '_')}.html", 'w') as f:
            f.write(self.output)


class EpubWriter:
    def __init__(self) -> None:
        pass
    def story(self, name, author, _auth_url, _auth_img):
        self.title = name
        self.epub = pypub.Epub(name, author)
        self.epub.publisher = "Alexandria"
    def set_cover(self, cover):
        if cover == "noimage":
            self.epub.cover = cover
        else:
            with open('cover', 'wb') as c:
                opn = urlopen(cover)
                read = opn.read()
                c.write(read)
            self.epub.cover = 'cover'
    def set_metadata(self, _desc, _genres, _tags):
        # ;<
        pass
    def start_chapters(self, _length, _base_url):
        pass
    def chapter(self, _index, chap, contents):
        contents = re.sub(r'<div class="wi_authornotes">\n(.*?)<\/div>\n*<p>\n*<\/p>\n*<\/div>', r'<hr/><br/> <blockquote class="wi_authornotes">\1</div><p></p></blockquote> <br/><hr/>', contents, flags=re.DOTALL)
        chapter = pypub.create_chapter_from_html(contents.encode('utf-8'), chap)
        self.epub.add_chapter(chapter)
    def flush(self):
        self.epub.create(f"{self.title.replace(' ', '_')}.epub")
 
if template == "epub":
    writer = EpubWriter()
else:
    writer = TemplateWriter(template)

## Webdriver stuff

driver = webdriver.Firefox()

def interceptor(request):
#    del request.headers['Referer']  # Remember to delete the header first
#    request.headers['Referer'] = 'some_referer'  # Spoof the referer
    del request.headers['Connection']
    request.headers['Connection'] = 'keep-alive'
    del request.headers['Sec-Fetch-Site']
    request.headers['Sec-Fetch-Site'] = 'cross-site'
    del request.headers['Upgrade-Insecure-Requests']
    request.headers['Upgrade-Insecure-Requests'] = '1'
    del request.headers['TE']
    request.headers['TE'] = 'trailers'
    del request.headers['X-Amzn-Trace-Id']

driver.implicitly_wait(5)


## end webdriver stuff

def navigate(url):
    now = time.time()
    if (now < navigate.wait):
        time.sleep(navigate.wait - now)
    print("Navigating to", url)
    driver.delete_all_cookies();
    driver.get(url);
    navigate.wait = now + random.randrange(8, 15)
def nav_toc():
    nav_toc.index += 1;
    navigate(base_url + '?toc=' + str(nav_toc.index))

DATA_CATEGORIES = ['title', 'author', 'auth_url', 'auth_avi', 'cover', 'desc', 'genre', 'tags']
META_COUNT = 8

for request in driver.requests:
    if request.response:
        print(
            request.url,
            request.response.status_code,
            request.response.headers['Content-Type']
        )

def build_toc(buffer, count, chaps):
    nav_toc()
    if not count:
        count = int(driver.find_element(By.CSS_SELECTOR, ".cnt_toc").text)
        buffer.write(f"{repr(count)}\n")
    while True:
        if (not driver.find_element(By.CSS_SELECTOR, "div.wi_fic_table.main").text):
            break
        page = list(map(lambda c: (c.text, c.get_attribute('href')), driver.find_elements(By.CSS_SELECTOR, "a.toc_a")))
        for chap in page:
            if chap not in chaps:
                chaps.append(chap)
                buffer.write(f"{repr(chap)}\n")
        nav_toc()
    buffer.write("#DATA\n")

def build_meta(buffer, index, metadata):
    print('build_meta')
    if index < 0:
        buffer.write(f"{repr(META_COUNT)}\n")
    elif index == 0:
        metadata['title'] = driver.find_element(By.CSS_SELECTOR, ".fic_title").text
        buffer.write(f"{repr(metadata['title'])}\n")
    elif index == 1:
        metadata['author'] = driver.find_element(By.CSS_SELECTOR, "span[property='name'] > a").text
        buffer.write(f"{repr(metadata['author'])}\n")
    elif index == 2:
        metadata['auth_url'] = driver.find_element(By.CSS_SELECTOR, "span[property='name'] > a").get_attribute('href')
        buffer.write(f"{repr(metadata['auth_url'])}\n")
    elif index == 3:
        metadata['auth_avi'] = driver.find_element(By.ID, "acc_ava_change none").get_attribute('src')
        buffer.write(f"{repr(metadata['auth_avi'])}\n")
    elif index == 4:
        image = driver.find_element(By.CSS_SELECTOR, ".fic_image > img")
        image = image.get_attribute('src') if image else "noimage"
        metadata['cover'] = image
        buffer.write(f"{repr(metadata['cover'])}\n")
    elif index == 5:
        metadata['desc'] = driver.find_element(By.CSS_SELECTOR, ".wi_fic_desc").get_attribute('innerHTML')
        buffer.write(f"{repr(metadata['desc'].strip())}\n")
    elif index == 6:
        metadata['genre'] = list(map(lambda g: g.text, driver.find_elements(By.CSS_SELECTOR, ".wi_fic_genre > span")))
        buffer.write(f"{repr(metadata['genre'])}\n")
    elif index == 7:
        metadata['tags'] = list(map(lambda t: t.text, driver.find_elements(By.CSS_SELECTOR, ".wi_fic_showtags_inner > a")))
        buffer.write(f"{repr(metadata['tags'])}\n")
    else:
        buffer.write('#TEXT\n')
        return
    build_meta(buffer, index + 1, metadata)

for base_url in stories:
    story_id = list(filter(lambda n: n, base_url.split('/')))[-1]
    navigate.wait = time.time()
    nav_toc.index = 0;

    with open(story_id, 'a+') as buffer:
        buffer.seek(0)
        chap_count = buffer.readline()
        tmp = buffer.readline()
        all_chaps = []
        if not chap_count:
            build_toc(buffer, None, all_chaps)
        else:
            chap_count = int(chap_count)
            while tmp.strip() != '#DATA':
                if not tmp.strip():
                    buffer.seek(buffer.tell() - 1)
                    build_toc(buffer, chap_count, all_chaps)
                    break
                all_chaps.append(eval(tmp))
                tmp = buffer.readline()
        all_chaps.reverse()

        i = 0
        metadata = {}
        data_count = buffer.readline()
        tmp = buffer.readline()
        if not data_count:
            build_meta(buffer, -1, metadata)
        else:
            data_count = int(data_count)
            while tmp.strip() != '#TEXT':
                if not tmp.strip():
                    buffer.seek(buffer.tell() - 1)
                    build_meta(buffer, i, metadata)
                    break
                if i < data_count:
                    metadata[DATA_CATEGORIES[i]] = eval(tmp)
                    i+= 1
                tmp = buffer.readline()
        # Insert metadata into writer
        writer.story(metadata['title'], metadata['author'], metadata['auth_url'], metadata['auth_avi'])
        writer.set_cover(metadata['cover'])
        writer.set_metadata(metadata['desc'], metadata['genre'], metadata['tags'])

        chap_count = len(all_chaps)
        writer.start_chapters(chap_count, base_url)
        tmp = buffer.readline()
        i = 0
        while buffer.readline().strip() == '#CHAP':
            chap_text = eval(tmp)
            writer.chapter(i, all_chaps[i][0], chap_text)
            i+=1
            tmp = buffer.readline()
        while i < chap_count:
            chap = all_chaps[i]
            navigate(chap[1])
            contents = driver.find_element(By.ID, "chp_raw").get_attribute('innerHTML')
            writer.chapter(i, chap[0], contents)
            buffer.write(f"{repr(contents)}\n#CHAP\n")
            i+=1
        writer.flush()
driver.quit()
