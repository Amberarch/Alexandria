from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.request import urlopen
import html.parser
import datetime
import base64
import sys

args = sys.argv[1:]
template = args[0]
stories = args[1:]

with open(template, 'r') as f:
    template = f.read()

driver = webdriver.Firefox()
driver.implicitly_wait(5)

def navigate(url):
    print("Navigating to", url)
    driver.delete_all_cookies();
    driver.get(url);

def nav_toc():
    nav_toc.index += 1;
    navigate(base_url + '?toc=' + str(nav_toc.index))
def img_encode(element):
    return f"data:image/jpeg;base64,{base64.b64encode(urlopen(element.get_attribute('src')).read()).decode('utf-8')}"

for base_url in stories:

    nav_toc.index = 0;
    output = template

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
    output = output.replace('<!--TITLE-->', title)
    try:
        image = img_encode(driver.find_element(By.CSS_SELECTOR, ".fic_image > img"))
    except:
        with open('noimage', 'r') as n:
            image = n.read()
    output = output.replace('<!--COVER-->', f'<img src={image}></img>')
    synopsis = driver.find_element(By.CSS_SELECTOR, ".wi_fic_desc").get_attribute('innerHTML')
    output = output.replace('<!--SYNOPSIS-->', f'<p>{synopsis}</p>')
    genres = driver.find_elements(By.CSS_SELECTOR, ".wi_fic_genre > span")
    genres = [f'<span class=genre>{genre.text}</span>' for genre in genres];
    output = output.replace('<!--GENRES-->', ''.join(genres))
    tags = driver.find_elements(By.CSS_SELECTOR, ".wi_fic_showtags_inner > a")
    tags = [f'<span class=tag>{tag.text}</span>' for tag in tags];
    output = output.replace('<!--TAGS-->', ''.join(tags))

    auth_img = img_encode(driver.find_element(By.ID, "acc_ava_change none"))
    output = output.replace('<!--AUTH_ICON-->', f'<img src={auth_img}></img>')
    author = driver.find_element(By.CSS_SELECTOR, "span[property='name'] > a")
    auth_name = author.text
    output = output.replace('<!--AUTH_NAME-->', auth_name);
    auth_link = author.get_attribute('href')
    output = output.replace('<!--AUTH_LINK-->', f'<a href="{auth_link}">{auth_name}</a>')

    toc = ""
    contents = f'<contents id=contents style=display:none title="{title}" src="{base_url}">'
    for i, chapter in enumerate(all_chaps):
        contents += f'<chapter page={i + 1} title="{chapter[0]}"{" hasnext" if i < (len(all_chaps) - 1) else ""}{" hasprev" if i > 0 else ""}>'
        toc += f'<li><a href="#{i + 1}">{chapter[0]}</a></li>'
        navigate(chapter[1])
        contents += driver.find_element(By.ID, "chp_raw").get_attribute('innerHTML')
        contents += '</chapter>'
    contents += '</contents>'
    output = output.replace('<!--TOC-->', toc)
    output = output.replace('<!--CONTENTS-->', contents)
    output = f'<!-- Page generated using Alexandria on {datetime.datetime.now().strftime("%Y-%m-%d")} -->\n' + output
    with open(title.replace(' ', '_') + '.html', 'w') as f:
        f.write(output)
driver.quit()
