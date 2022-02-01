import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(name):
    """Look up quote for symbol."""

    # Contact API
    try:
        # api_key = os.environ.get("API_KEY")
        api_key = "k_bqzb9re0"
        url = f"https://imdb-api.com/en/API/SearchSeries/{api_key}/{name}"
        # url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        resultlist = []
        results = quote["results"]
        for result in results:
            resultlist.append(result)
        return resultlist
    except (KeyError, TypeError, ValueError):
        return None

def lookupanime(name):
    try:
        url = "https://jikan1.p.rapidapi.com/search/anime"
        querystring = {"q":name}
        headers = {
                'x-rapidapi-host': "jikan1.p.rapidapi.com",
                'x-rapidapi-key': "1b7269acadmsh7b21a1bbe7c535bp150b55jsn03e7ccad58a3"
        }
        response = requests.request("GET", url, headers=headers, params=querystring)
    except requests.RequestException:
        return None
    try:
        quote = response.json()
        resultlist = []
        results = quote["results"]
        for result in results:
            resultlist.append(result)
        return resultlist
    except (KeyError, TypeError, ValueError):
        return None

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
