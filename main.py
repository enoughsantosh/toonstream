from fastapi import FastAPI, Query, HTTPException
import requests
import httpx
from urllib.parse import urlparse
from pydantic import BaseModel
from bs4 import BeautifulSoup
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def home():
    return {"message": "Anime Search API is running!"}
# Homepage 
@app.get("/home")
def scrape_toonstream():
    url = "https://toonstream.co/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTP errors (like 404, 500)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch Api: {str(e)}")
    
    soup = BeautifulSoup(response.text, "html.parser")

    latest_series = []
    latest_movies = []

    # Extract Latest Series
    series_items = soup.select("#widget_list_movies_series-2-all ul.post-lst li")
    if not series_items:
        raise HTTPException(status_code=500, detail="Failed to find latest series section.")

    for series in series_items[:20]:
        title_tag = series.find("h2", class_="entry-title")
        title = title_tag.text.strip() if title_tag else "Unknown Title"
        img_tag = series.find("img")
        image = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else img_tag["src"] if img_tag else ""
        link_tag = series.find("a", class_="lnk-blk")
        link = link_tag["href"] if link_tag and "href" in link_tag.attrs else "#"
        parsed_link = urlparse(link).path
        latest_series.append({"title": title, "image": image, "link": parsed_link})
    # Extract Latest Movies
    movie_items = soup.select("#widget_list_movies_series-3-all ul.post-lst li")
    
    if not movie_items:
        raise HTTPException(status_code=500, detail="Failed to find latest movies section.")

    for movie in movie_items[:20]:
        title_tag = movie.find("h2", class_="entry-title")
        title = title_tag.text.strip() if title_tag else "Unknown Title"
        img_tag = movie.find("img")
        image = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else img_tag["src"] if img_tag else ""
        link_tag = movie.find("a", class_="lnk-blk")
        
        link = link_tag["href"] if link_tag and "href" in link_tag.attrs else "#"
        parsed_link = urlparse(link).path  # Extracts only the path

        latest_movies.append({"title": title, "image": image, "link": parsed_link})

    return {
        "latest_series": latest_series,
        "latest_movies": latest_movies
    }


# ✅ FIXED: Fully synchronous `/type` endpoint
@app.get("/type")
def get_category(type: str = Query(..., title="Anime Category")):
    """Fetch anime/movies from the given category type"""
    url = f"https://toonstream.co/category/{type}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch category details: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")

    movies_list = []
    for item in soup.select(".post-lst li"):  # ✅ Fixed selector
        title_tag = item.select_one("h2.entry-title")
        image_tag = item.select_one("img")
        link_tag = item.select_one("a.lnk-blk")
        link = link_tag.get("href")
        parsed_link = urlparse(link).path
        

        if title_tag and image_tag and link_tag:
            movies_list.append({
                "title": title_tag.text.strip(),
                "image": image_tag.get("data-src") or image_tag.get("src"),
                "link": parsed_link
            })

    if not movies_list:
        return {"error": "No results found"}

    return {"category": type, "results": movies_list}


from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/search/")
def scrape_anime_details(q: str):
    url = f"https://toonstream.co/?s={q}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "Failed to retrieve data"}

    soup = BeautifulSoup(response.text, "lxml")
    items = soup.select("ul.post-lst li")[:10]  # More specific selection

    results = []
    for item in items:
        title_tag = item.find("h2", class_="entry-title")
        img_tag = item.find("img")
        link_tag = item.find("a", class_="lnk-blk")

        if title_tag and img_tag and link_tag:
            title = title_tag.text.strip()
            image = img_tag["src"]
            link = link_tag["href"]
            parsed_link = urlparse(link).path

            results.append({"title": title, "image": image, "link": parsed_link})

    return results


@app.get("/searchsug/")
def search_animesug(term: str):
    url = "https://toonstream.co/wp-admin/admin-ajax.php"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }
    data = {
        "action": "action_tr_search_suggest",
        "term": term
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        results = []
        for li in soup.find_all("li", class_="fa-play-circle"):
            a_tag = li.find("a")
            if a_tag:
                anime_type = a_tag.find("span").text if a_tag.find("span") else "unknown"
                anime_title = a_tag.text.strip().replace(anime_type, "").strip()
                anime_url = a_tag["href"]
                parsed_link = urlparse(anime_url).path

                results.append({
                    "title": anime_title,
                    "type": anime_type,
                    "url": parsed_link
                })

        return results
    else:
        return {"error": "Failed to fetch data", "status_code": response.status_code}
        


@app.get("/series/")
def scrape_anime_details(q: str):
    url = f"https://toonstream.co{q}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "Failed to retrieve data"}

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.find("h1", class_="entry-title").text.strip()
    thumbnail = soup.find("div", class_="post-thumbnail").find("img")["data-src"]
    background = soup.find("div", class_="bghd").find("img")["src"] if soup.find("div", class_="bghd") else None
    description = soup.find("div", class_="description").find("p").text.strip()
    seasons = [s.text.strip() for s in soup.select(".aa-cnt .sel-temp a")]

    no_of_seasons = len(seasons)
    no_of_episodes = int(soup.find("span", class_="episodes").find("span").text.strip())

    return {
        "title": title,
        "thumbnail": thumbnail,
        "background_image": background,
        "description": description,
        "no_of_seasons": no_of_seasons,
        "no_of_episodes": no_of_episodes,
        "seasons_available": seasons,
    }

from fastapi import FastAPI
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/movies/")
def scrape_anime_details(q: str):
    url = f"https://toonstream.co{q}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "Failed to retrieve data"}

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract title
    title = soup.find("h1", class_="entry-title").text.strip() if soup.find("h1", class_="entry-title") else None

    # Extract thumbnail
    thumbnail_tag = soup.select_one(".post-thumbnail img")
    thumbnail = thumbnail_tag["data-src"] if thumbnail_tag else None

    # Extract background image (if available)
    background_tag = soup.select_one(".bghd img")
    background_image = background_tag["src"] if background_tag else None

    # Extract description
    description_tag = soup.select_one(".description p")
    description = description_tag.text.strip() if description_tag else None

    # Extract duration
    duration_tag = soup.select_one(".duration")
    duration = duration_tag.text.strip() if duration_tag else None

    # Extract video sources
    sources = []
    for iframe in soup.select(".video iframe"):
        src = iframe.get("data-src") or iframe.get("src")
        if src:
            sources.append(src)

    return {
        "title": title,
        "thumbnail": thumbnail,
        "background_image": background_image,
        "description": description,
        "duration": duration,
        "sources": sources,
    }
