"""
增广贤文 Chinese-English Version
process:
    base on zgxw.txt (260 verses version)
    using translation from zgxw.html (《增广贤文》当代汉英注译), improved using chatGPT
    missing part translated using chatGPT with manual inspection

output:
    json raw data
    printable card format
"""

import openai
import re
from bs4 import BeautifulSoup
import json
import subprocess
from urllib.parse import urlparse, parse_qs

"""
translate numbering to chinese
"""
def number_eng_to_chs(num):
    if num < 0 or num > 260:
        return
    number_chs = "〇一二三四五六七八九十"

    if num <= 10:
        return number_chs[num]
    if num > 10 and num < 20:
        return number_chs[10] + number_chs[num - 10]
    
    hundred = num // 100
    ten = num % 100 // 10
    digit = num % 10

    if num < 100:
        return number_chs[ten] + number_chs[10] + (number_chs[digit] if digit > 0 else '')
    
    return number_chs[hundred] + number_chs[ten] + number_chs[digit]

"""
format (增广贤文 txt)[https://www.zhihu.com/tardis/zm/art/526791595?source_id=1003]
"""
def parse_txt():
    cur = 1
    lines = []
    for line in open('zgxw.txt'):
        if "大义" in line:
            print (number_eng_to_chs(cur))
            print (''.join(lines))
            cur += 1
            lines = []
            continue
        lines.append(line)

def get_full_text_txt():
    for line in open('zgxw.txt'):
        if "大义" in line:
            continue
        print (line.strip())
    return

def get_initials_txt(group_size=5):
    cur = 0
    lines = []
    initials = []
    for line in open('zgxw.txt'):
        if "大义" in line:
            initials.append(lines[0][0])
            cur += 1
            lines = []
            if cur % group_size == 0:
                print (''.join(initials))
                initials = []
                continue
            continue
        lines.append(line)

"""
crawl (ebook)[https://xianxiao.ssap.com.cn/bibliography/1875431.html] in order to get English translation
"""
def parse_html():
    html_content = open('zgxw.html').read()
    soup = BeautifulSoup(html_content, 'html.parser')
    list_items = soup.select('.t_items .list_01')

    # Initialize lists to store extracted data
    h5_texts = []
    hrefs = []

    # Iterate through the list items
    for item in list_items:
        # Find the <a> tag with class 'read'
        a_tag = item.find('a', class_='read')
        # Find the <h5> tag
        h5_tag = item.find('h5')
        
        if a_tag and h5_tag:
            # Append the text of the <h5> tag to the 'h5_texts' list
            h5_texts.append(h5_tag.text)
            # Append the href attribute of the <a> tag to the 'hrefs' list
            hrefs.append(a_tag['try_read_url'])
    

    articles = []
    # Print the extracted data
    for i in range(len(h5_texts)):
        # Parse the URL
        parsed_url = urlparse(hrefs[i])

        # Get the query parameters as a dictionary
        query_params = parse_qs(parsed_url.query)
        resource_id = query_params['resource_id'][0]

        # print(f"Title: {h5_texts[i]}, Link: {resource_id}")
        p = subprocess.run(cmd.replace('<$id>', resource_id), shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        article = json.loads(p.stdout)
        articles.append(article)
        print (json.dumps(article, ensure_ascii=False))
        print (f"{i+1}/{len(h5_texts)} parsed.")
    
    json.dump(articles, open('res.json', 'w'), ensure_ascii=False)

def fix_numbering(text, pattern):
    # Initialize an offset to keep track of the start index
    counter = 1

    # Define a function to replace the matched content
    def replace(match):
        nonlocal counter
        replacement = f"<superscript>{counter}</superscript>"
        counter += 1
        print (counter)
        return replacement

    # Use re.sub() with the defined pattern and replacement function
    return re.sub(pattern, replace, text)

"""
group verses
format crawl result
"""
def parse_json(group_size=5):
    res = json.load(open('res.json'))
    # Group articles
    dl = []
    for i in range(0, len(res), group_size):
        d = []
        for r in res[i: i+group_size]:
            content = r['posts']['content'][0]
            for key in ['title', 'content']:
                for j in range(len(content)):
                    if j >= len(d):
                        d.append({})
                    if not key in d[j]:
                        d[j][key] = ''
                    d[j][key] += content[j][key] + '\n'
        dl.append(d)
    for d in dl:
        content = d

        for c in content:
            c['title'] = c['title'].replace('\n', '<br>')

        back_html = f"<h1>{re.sub('<superscript>[^<]*</superscript>', '', content[0]['title'])}</h1>\n"
        back_html += f"<h2>{re.sub('<[^<]*>', '', content[-1]['content'])}</h2>".replace('\n', '<br>')

        content[1]['title'] = '注释'
        content[2]['title'] = '译文'
        content[4]['title'] = 'English'

        content[0]['content'] = fix_numbering(content[0]['content'], r'<superscript>(\d+)</superscript>')
        content[1]['content'] = fix_numbering(content[1]['content'], r'\[(\d+)\]')

        front_html = f"<h1>{content[0]['title']}</h1>\n"
        for c in [content[i] for i in [1,2,4]]:
            front_html += f"<h3>{c['title']}</h3>\n"
            front_html += f"{c['content']}"

        front_html = front_html.replace('superscript', 'sup')

        # print (back_html,'\n',front_html)
        exit()

def get_initials_json(group_size=5):
    res = json.load(open('res.json'))
    for i in range(0, len(res), group_size):
        initials = list(map(lambda r: re.sub('<superscript>[^<]*</superscript>', '', r['posts']['content'][0][0]['title'])[0], res[i:i+group_size]))
        print (initials)

def get_full_text_json():
    res = json.load(open('res.json'))
    for r in res:
        print (re.sub('<superscript>[^<]*</superscript>', '', r['posts']['content'][0][0]['title']))

def get_translation_from_json():
    res = json.load(open('res.json'))
    d = {}
    for r in res:
        content = r['posts']['content'][0]
        chs = f"{re.sub('<superscript>[^<]*</superscript>', '', content[0]['title'])}"
        eng = f"{re.sub('<[^<]*>', '', content[-1]['content'])}"
        d[chs] = eng
    return d

def get_missing_translations(translation):
    for m in open('missing_translated.txt'):
        m = m.strip()
        translation[m.split('|')[0]] = m.split('|')[1]

def print_all(translation):
    cur = 1
    lines = []
    mapping = {}
    for l in open('different.txt'):
        mapping[l.split('|')[0]] = l.split('|')[1].strip()
    for line in open('zgxw.txt'):
        line = line.strip()
        if "大义" in line:
            print (number_eng_to_chs(cur))
            print (''.join(lines))
            print (''.join(map(lambda l: translation[l if not l in mapping else mapping[l]], lines)))
            print()
            cur += 1
            lines = []
            continue
        lines.append(line)

def translate_missing(group_size = 50):
    messages = [
        {"role": "system", "content": "You are a professional translator. You are proficient in both Chinese and English."},
    ]
    messages.append({"role": "user", "content": "I want to translate some Chinese proverbs into English. The output follows the following format: the original proverb in Chinese, followed by a delimiter '|', then the actual English translation. The translation need to be concise. The output line numbers must equal to input line numbers, don't miss or combine any lines."},)
    entries = [m.strip() for m in open('missing.txt')]

    for i in range(50, len(entries), group_size):
        el = entries[i: i+group_size]
        chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages+[{"role": "user", "content": '\n'.join(el)}]
        )
        reply = chat.choices[0].message.content
        print(reply)

def improve_translation(group_size = 50):
    messages = [
        {"role": "system", "content": "You are a professional translator. You are proficient in both Chinese and English."},
    ]
    messages.append({"role": "user", "content": "I want to improve the following translations, the input format is as follows: Chinese proverb, followed by delimeter '|', then the English translation. I want you to improve on the English translation to make it more concise and idomatic. The output only output the improved English translation. The output line numbers should equal to the input line numbers."},)

    entries = []
    res = json.load(open('res.json'))
    for r in res:
        chs = re.sub('<superscript>[^<]*</superscript>', '', r['posts']['content'][0][0]['title'])
        eng = re.sub('<[^<]*>', '', r['posts']['content'][0][-1]['content'])
        entries.append(f"{chs}|{eng}")

    for i in range(50, len(entries), group_size):
        el = entries[i: i+group_size]
        chat = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages+[{"role": "user", "content": '\n'.join(el)}]
        )
        reply = chat.choices[0].message.content
        print(reply)

if __name__ == '__main__':
    # parse_txt()
    # parse_html()
    # parse_json()

    # get_initials_txt(5)
    # get_initials_json(1)
    # get_full_text_txt()
    # get_full_text_json()

    # translate_missing()
    # improve_translation()

    t = get_translation_from_json()
    get_missing_translations(t)
    t[''] = ''

    print_all(t)