from fastapi import FastAPI, Query, HTTPException
import requests
import httpx
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch ToonStream: {str(e)}")
    
    soup = BeautifulSoup(response.text, "html.parser")

    latest_series = []
    latest_movies = []

    # Extract Latest Series
    series_items = soup.select("#widget_list_movies_series-2-all ul.post-lst li")
    if not series_items:
        raise HTTPException(status_code=500, detail="Failed to find latest series section.")

    for series in series_items[:20]:
        img_tag = series.find("img")
        title = img_tag["title"] if img_tag and "title" in img_tag.attrs else "Unknown Title"
        image = img_tag["data-src"] if img_tag and "data-src" in img_tag.attrs else img_tag["src"] if img_tag else ""
        link_tag = series.find("a")
        link = "https://toonstream.co" + link_tag["href"] if link_tag and "href" in link_tag.attrs else "#"

        latest_series.append({"title": title, "image": image, "link": link})

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

        latest_movies.append({"title": title, "image": image, "link": link})

    return {
        "latest_series": latest_series,
        "latest_movies": latest_movies
    }
