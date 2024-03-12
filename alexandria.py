from selenium import webdriver
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
        genres = [f'<span class=genre>{genre.text}</span>' for genre in genres];
        self.output = self.output.replace('<!--GENRES-->', ''.join(genres))
        tags = [f'<span class=tag>{tag.text}</span>' for tag in tags];
        self.output = self.output.replace('<!--TAGS-->', ''.join(tags))
    def start_chapters(self, length):
        self.toc = ""
        self.contents = f'<contents id=contents style=display:none title="{title}" src="{base_url}">'
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
    def start_chapters(self, _length):
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

driver = webdriver.Firefox()
driver.implicitly_wait(5)

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

for base_url in stories:
    navigate.wait = time.time()
    nav_toc.index = 0;

    all_chaps = [];
    while True:
        nav_toc();
        if (not driver.find_element(By.CSS_SELECTOR, "div.wi_fic_table.main").text):
            break;
        chaps = driver.find_elements(By.CSS_SELECTOR, "a.toc_a");
        all_chaps.append(list(map(lambda c: (c.text, c.get_attribute('href')), chaps)));

    start = len(all_chaps) - 1
    all_chaps = [item for sublist in all_chaps for item in sublist];
    all_chaps.reverse()

    title = driver.find_element(By.CSS_SELECTOR, ".fic_title").text
    author = driver.find_element(By.CSS_SELECTOR, "span[property='name'] > a")
    auth_name = author.text
    auth_link = author.get_attribute('href')
    auth_img = driver.find_element(By.ID, "acc_ava_change none").get_attribute('src')
    writer.story(title, auth_name, auth_link, auth_img)

    image = driver.find_element(By.CSS_SELECTOR, ".fic_image > img")
    writer.set_cover(image.get_attribute('src') if image else "noimage")

    description = driver.find_element(By.CSS_SELECTOR, ".wi_fic_desc").get_attribute('innerHTML')
    genres = driver.find_elements(By.CSS_SELECTOR, ".wi_fic_genre > span")
    tags = driver.find_elements(By.CSS_SELECTOR, ".wi_fic_showtags_inner > a")
    writer.set_metadata(description, genres, tags)

    writer.start_chapters(len(all_chaps))
    for i, chapter in enumerate(all_chaps):
        navigate(chapter[1])
        contents = driver.find_element(By.ID, "chp_raw").get_attribute('innerHTML')
        writer.chapter(i, chapter[0], contents)
    writer.flush()
driver.quit()
