from scrapling import StealthyFetcher

async def internet_search(search_query):
    """
    Asynchronously searches the web using google and returns the first search results

    Args:
         search_query (str): Search query for the google

    Returns:
         list: First url from the search
    """
    search_query = f'"{search_query}"'
    search_url = f"https://www.google.com/search?q={search_query}"

    fetcher = StealthyFetcher()

    try:
        page = await fetcher.async_fetch(search_url)
        first_url = page.css("#search a::attr(href)")

        # first_url list take only the element start with https
        first_url = [url for url in first_url if url.startswith("https")]

        return first_url
    except Exception as e:
        print(f"An error occurred: {e}")