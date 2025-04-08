from groq import Groq
from flask import Flask, render_template, request
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

### HARDCODED AI_KEY TUTORIAL VERSION ###
AI_KEY = "masukan api key groq disini"  #
###  -------------------------------- ###

client = Groq(api_key=AI_KEY)

def ai_call(year):
    try:
        chat_completion = client.chat.completions.create(
            messages=[{
                "role": "user",
                "content": f"berikan 1 fakta menarik seputar teknologi pada tahun {year}"
            }],
            model="llama-3.2-1b-preview",
            stream=False,
        )
        return chat_completion.choices[0].message.content
    except Exception:
        return "Maaf, AI tidak tersedia saat ini. Silakan coba lagi nanti."

def class_filter(media_name):
    if media_name == "mtlnovel_header":
        return {"class": "list-right", "element": "div"}
    elif media_name == "mtlnovel_daftar_isi":
        return {"class": "ch-list", "element": "div"}
    return {"class": "", "element": ""}

def scrape_news(name, url):
    detector = class_filter(name)
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        container = soup.find(detector["element"], class_=detector["class"])
        
        if not container:
            return [] if name == "mtlnovel_daftar_isi" else "Container tidak ditemukan"
        
        if name == "mtlnovel_header":
            headline = container.find("h1")
            return headline.text.strip() if headline else "Judul tidak ditemukan"
        
        elif name == "mtlnovel_daftar_isi":
            chapters = []
            base_url = "https://id.mtlnovels.com"
            for link in container.find_all('a', class_='ch-link'):
                chapter_num = link.find('strong').get_text(strip=True)
                chapter_title = link.contents[-1].strip('" ')
                chapter_url = urljoin(base_url, link['href'])
                chapters.append({
                    'number': chapter_num,
                    'title': chapter_title,
                    'url': chapter_url
                })
            return chapters
            
    except Exception as e:
        print(f"Error scraping {name}: {e}")
        return [] if name == "mtlnovel_daftar_isi" else f"Error: {e}"

def scrape_chapter_content(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Dapatkan judul chapter
        chapter_title = soup.find('h1', class_='main-title')
        title = chapter_title.get_text(strip=True) if chapter_title else "Judul Chapter Tidak Ditemukan"
        
        # Dapatkan konten chapter
        content_div = soup.find('div', class_='par fontsize-16')
        if not content_div:
            return title, "Konten chapter tidak ditemukan"
        
        # Proses konten
        cleaned_content = []
        for element in content_div.children:
            if element.name == 'p':
                text = element.get_text(strip=True)
                if text and text != '@':
                    cleaned_content.append(text)
        
        return title, "\n\n".join(cleaned_content)
        
    except Exception as e:
        print(f"Error scraping chapter content: {e}")
        return "Error", f"Gagal memuat konten: {e}"

@app.route("/")
def main():
    novel_url = "https://id.mtlnovels.com/lord-of-the-people-discount-artifact-for-signing-in-at-the-start/chapter-list/"
    header = scrape_news("mtlnovel_header", novel_url)
    chapters = scrape_news("mtlnovel_daftar_isi", novel_url)
    
    current_year = datetime.now().year
    tech_fact = ai_call(current_year)
    
    return render_template("index.html",
                         header=header,
                         chapters=chapters,
                         tech_fact=tech_fact)

@app.route("/chapter")
def chapter():
    chapter_url = request.args.get('url')
    if not chapter_url:
        return "URL chapter tidak valid", 400
    
    title, content = scrape_chapter_content(chapter_url)
    return render_template("chapter.html",
                         chapter_title=title,
                         content=content,
                         chapter_url=chapter_url)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)