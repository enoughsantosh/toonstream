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
        series_items = soup.select(".gs_logo_single--wrapper")
        if not series_items:
            raise HTTPException(status_code=500, detail="Failed to find latest series section.")

        for series in series_items[:20]:
            title = series.find("img")["title"] if series.find("img") else "Unknown Title"
            image = series.find("img")["data-src"] if series.find("img") and "data-src" in series.find("img").attrs else series.find("img")["src"]
            link = "https://toonstream.co" + series.find("a")["href"] if series.find("a") else "#"

            latest_series.append({"title": title, "image": image, "link": link})

        # Extract Latest Movies
        movie_items = soup.select(".post.dfx.fcl.movies.fa-play-circle")
        if not movie_items:
            raise HTTPException(status_code=500, detail="Failed to find latest movies section.")

        for movie in movie_items[:20]:
            title = movie.find("h2", class_="entry-title").text.strip() if movie.find("h2") else "Unknown Title"
            image = movie.find("img")["data-src"] if movie.find("img") and "data-src" in movie.find("img").attrs else movie.find("img")["src"]
            link = movie.find("a", class_="lnk-blk")["href"] if movie.find("a", class_="lnk-blk") else "#"

            latest_movies.append({"title": title, "image": image, "link": link})

        return {
            "latest_series": latest_series,
            "latest_movies": latest_movies
        }
    
    
