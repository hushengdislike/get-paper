import requests
import feedparser
from models import Paper, get_session
from datetime import datetime

ARXIV_CATEGORIES = [
    'cs.AI', 'cs.LG', 'stat.ML', 'cs.CV', 'cs.CL', 'cs.NE', 'cs.IR'
]

BASE_URL = 'http://export.arxiv.org/api/query?'


def fetch_arxiv_papers(category, max_results=50):
    query = f'search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={max_results}'
    url = BASE_URL + query
    response = requests.get(url)
    feed = feedparser.parse(response.text)
    papers = []
    for entry in feed.entries:
        paper = {
            'arxiv_id': entry.id.split('/')[-1],
            'title': entry.title,
            'summary': entry.summary,
            'link': entry.link
        }
        papers.append(paper)
    return papers


def save_papers_to_db(papers):
    session = get_session()
    for p in papers:
        if not session.query(Paper).filter_by(arxiv_id=p['arxiv_id']).first():
            paper = Paper(
                arxiv_id=p['arxiv_id'],
                title=p['title'],
                summary=p['summary'],
                link=p['link']
            )
            session.add(paper)
    session.commit()
    session.close()


def main():
    for cat in ARXIV_CATEGORIES:
        papers = fetch_arxiv_papers(cat, max_results=50)
        save_papers_to_db(papers)
    print('爬取完成！')

if __name__ == '__main__':
    main() 