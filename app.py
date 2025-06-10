from flask import Flask, render_template, request, jsonify
from models import Paper, get_session
from sqlalchemy import desc
import requests
import feedparser
from datetime import datetime, timedelta
import time
from arxiv_spider import fetch_arxiv_papers, save_papers_to_db as spider_save_papers

app = Flask(__name__)

# arXiv API配置
ARXIV_CATEGORIES = [
    'cs.AI', 'cs.LG', 'stat.ML', 'cs.CV', 'cs.CL', 'cs.NE', 'cs.IR'
]

def get_citations(arxiv_id):
    """获取论文引用次数（模拟数据）"""
    return hash(arxiv_id) % 1000

def save_papers_to_db(time_range):
    """保存论文到数据库"""
    session = get_session()
    try:
        # 如果是新爬取，先清除旧数据
        if time_range == 'week':
            session.query(Paper).filter_by(is_weekly=1).delete()
        elif time_range == 'month':
            session.query(Paper).filter_by(is_yearly=1).delete()
        
        total_papers = 0
        for category in ARXIV_CATEGORIES:
            papers = fetch_arxiv_papers(category, time_range=time_range)
            for p in papers:
                # 添加额外字段
                p['citations'] = get_citations(p['arxiv_id'])
                p['is_weekly'] = 1 if time_range == 'week' else 0
                p['is_yearly'] = 1 if time_range == 'month' else 0
                p['category'] = category
                
                # 直接保存到数据库
                paper = Paper(
                    arxiv_id=p['arxiv_id'],
                    title=p['title'],
                    summary=p['summary'],
                    link=p['link'],
                    category=p['category'],
                    citations=p['citations'],
                    is_weekly=p['is_weekly'],
                    is_yearly=p['is_yearly'],
                    crawled_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(paper)
                total_papers += 1
            
            session.commit()  # 每个分类提交一次
            time.sleep(1)  # 避免请求过快
            
        return total_papers
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

@app.route('/')
def 首页():
    """首页：显示论文列表"""
    会话 = get_session()
    关键词 = request.args.get('keyword', '')
    时间范围 = request.args.get('time_range', 'all')
    排序方式 = request.args.get('sort', 'citations')
    
    try:
        query = 会话.query(Paper)
        
        if 时间范围 == 'week':
            query = query.filter_by(is_weekly=1)
        elif 时间范围 == 'month':
            query = query.filter_by(is_yearly=1)
        
        if 关键词:
            query = query.filter(Paper.title.contains(关键词) | Paper.summary.contains(关键词))
        
        if 排序方式 == 'citations':
            论文列表 = query.order_by(desc(Paper.citations)).all()
        else:
            论文列表 = query.order_by(desc(Paper.id)).all()
    except Exception as e:
        print(f"查询数据库出错: {e}")
        论文列表 = []
    
    会话.close()
    
    return render_template('index.html', 
                         papers=论文列表, 
                         keyword=关键词,
                         time_range=时间范围,
                         sort=排序方式)

@app.route('/crawl', methods=['POST'])
def crawl():
    """爬取论文"""
    try:
        data = request.get_json()
        time_range = data.get('time_range', 'week')
        count = save_papers_to_db(time_range)
        return jsonify({'status': 'success', 'message': f'成功爬取{count}条论文数据！'})
    except Exception as e:
        print(f"爬取失败: {str(e)}")  # 添加错误日志
        return jsonify({'status': 'error', 'message': f'爬取失败：{str(e)}'}), 500

@app.route('/delete', methods=['POST'])
def delete():
    """删除论文"""
    try:
        data = request.get_json()
        time_range = data.get('time_range', 'all')
        会话 = get_session()
        if time_range == 'week':
            会话.query(Paper).filter_by(is_weekly=1).delete()
        elif time_range == 'month':
            会话.query(Paper).filter_by(is_yearly=1).delete()
        else:
            会话.query(Paper).delete()
        会话.commit()
        会话.close()
        return jsonify({'message': '删除成功！'})
    except Exception as e:
        return jsonify({'message': f'删除失败：{str(e)}'}), 500

@app.route('/visualization')
def visualization():
    """可视化分析页面"""
    会话 = get_session()
    try:
        # 获取各分类的论文数量
        分类统计 = {}
        for category in ARXIV_CATEGORIES:
            count = 会话.query(Paper).filter_by(category=category).count()
            if count > 0:  # 只显示有论文的分类
                分类统计[category] = count
        
        # 获取引用次数最多的前10篇论文
        热门论文 = 会话.query(Paper).order_by(desc(Paper.citations)).limit(10).all()
        
        # 处理论文标题，使其更短
        for paper in 热门论文:
            if len(paper.title) > 50:
                paper.title = paper.title[:47] + '...'
        
        return render_template('visualization.html', 
                             categories=分类统计,
                             hot_papers=热门论文)
    except Exception as e:
        print(f"可视化数据获取失败: {e}")
        return render_template('visualization.html', 
                             categories={},
                             hot_papers=[])
    finally:
        会话.close()

if __name__ == '__main__':
    app.run(debug=True)