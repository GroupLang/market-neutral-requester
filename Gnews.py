from gnews import GNews

# Initialize the GNews object
google_news = GNews()

# Define the keyword for the news search
keyword = 'technology'

# Fetch news articles related to the keyword
news_articles = google_news.get_news(keyword)

# Display the fetched news articles
for article in news_articles:
    print(f"Title: {article['title']}")
    print(f"Publisher: {article['publisher']}")
    print(f"Published Date: {article['published date']}")
    print(f"Description: {article['description']}")
    print(f"URL: {article['url']}\n")
