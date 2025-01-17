from datetime import datetime, timedelta

import openai
import pandas as pd
from gdeltdoc import GdeltDoc, Filters
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from market_router import (
    OPENAI_API_KEY,
)
from market_router.expections import CreateCompletionError, SearchError, SummarizeError
from src import exa_sector_query_tpl, summarize_sector_system_tpl
from src.utils.ai_utils import create_completion
from src.utils.time_utils import datetime_to_iso8601

openai.api_key = OPENAI_API_KEY
gdelt = GdeltDoc()

_MAX_NUM_DOCUMENTS = 5
_MAX_SUMMARY_LENGTH = 2000 * 4  # one token is 4 characters aprox


class News:
    def __init__(self, entity, eval_date: str):
        self.entity = entity
        self.eval_date = datetime.strptime(eval_date, "%Y-%m-%d")
        self.contents_results = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(SearchError),
    )
    def _search(self) -> list:
        try:
            search_query = self._build_search_query()
            
            # Convert string dates to datetime objects for GDELT
            start_date = self.eval_date - timedelta(days=1)
            end_date = self.eval_date
            
            # Set up GDELT filters with proper date formatting
            f = Filters(
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                num_records=_MAX_NUM_DOCUMENTS,
                keyword=search_query,
                country="US"
            )
            
            # Search articles
            news_response = gdelt.article_search(f)
            
            if news_response.empty:
                logger.warning(f"No news found for {self.entity}")
                # Return empty results if no news found
                class NewsResults:
                    def __init__(self):
                        self.results = []
                self.contents_results = NewsResults()
                return
            
            # Create a results object with consistent structure
            class NewsResult:
                def __init__(self, article):
                    title = article.get('title', '')
                    source = article.get('sourcecountry', '')
                    url = article.get('url', '')
                    self.text = f"{title}. {source} - {url}"
                    self.summary = None
            
            class NewsResults:
                def __init__(self, articles):
                    self.results = [NewsResult(article) for article in articles.to_dict('records')]
            
            self.contents_results = NewsResults(news_response)

        except Exception as e:
            logger.error(e)
            raise SearchError(f"Error during searching news for {self.entity}: {e}")

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(SummarizeError),
    )
    def _summarize(self):
        summarize_query = self._build_summarize_query()
        try:
            for _news in self.contents_results.results:
                summary = create_completion(summarize_query, _news.text[:_MAX_SUMMARY_LENGTH])
                _news.summary = summary

            return self.contents_results.results
        except CreateCompletionError as e:
            logger.error(e)
            raise SummarizeError(f"Error during creating Completion for {self.entity}: {e}")
        except Exception as e:
            logger.error(e)
            raise SummarizeError(f"Error during summarizing news fpr {self.entity}: {e}")


class SectorNews(News):
    """This class downloads and saves the news for the given sector."""

    def get(self):
        self._search()
        self._summarize()
        return self._concatenate_news()

    def _build_search_query(self):
        return f"{self.entity}"

    def _build_summarize_query(self):
        return summarize_sector_system_tpl

    def _concatenate_news(self) -> str:
        return "\n\n\n\n".join([news.summary for news in self.contents_results.results])[
            :_MAX_SUMMARY_LENGTH
        ]
