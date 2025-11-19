#!/usr/bin/env python3
"""
Combined Blog Discovery Viewer - Posts + Network in One App
"""

from flask import Flask, render_template_string
import json
import os
import argparse

app = Flask(__name__)

COMBINED_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog Discovery Network</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --bg: #f8fafc;
            --text: #1e293b;
            --text-dim: #64748b;
            --border: #e2e8f0;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
            z-index: 0;
        }
        
        .content { position: relative; z-index: 1; }
        
        nav {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 80px;
        }
        
        .logo {
            font-size: 1.5em;
            font-weight: 800;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 10px;
        }
        
        .nav-link {
            color: var(--text-dim);
            padding: 10px 20px;
            border-radius: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .nav-link:hover {
            color: var(--text);
            background: rgba(99, 102, 241, 0.08);
        }
        
        .nav-link.active {
            color: white;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.25);
        }
        
        .stats-badge {
            background: rgba(99, 102, 241, 0.2);
            color: var(--primary);
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .view {
            display: none;
        }
        
        .view.active {
            display: block;
        }
        
        /* Posts View */
        .header {
            max-width: 1400px;
            margin: 60px auto 40px;
            padding: 0 30px;
            text-align: center;
        }
        
        h1 {
            font-size: 3.5em;
            font-weight: 800;
            background: linear-gradient(135deg, var(--text), var(--text-dim));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
            letter-spacing: -2px;
        }
        
        .subtitle {
            color: var(--text-dim);
            font-size: 1.2em;
            margin-bottom: 40px;
        }
        
        .search-container {
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }
        
        .search-box {
            width: 100%;
            padding: 18px 24px 18px 50px;
            font-size: 16px;
            background: white;
            border: 2px solid var(--border);
            border-radius: 16px;
            color: var(--text);
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }
        
        .search-icon {
            position: absolute;
            left: 18px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-dim);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 30px 80px;
        }
        
        .blog-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(420px, 1fr));
            gap: 30px;
        }
        
        .blog-card {
            background: white;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 32px;
            transition: all 0.4s;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            position: relative;
            overflow: hidden;
        }
        
        .blog-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .blog-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(99, 102, 241, 0.12);
        }
        
        .blog-card:hover::before {
            opacity: 1;
        }
        
        .blog-name {
            font-size: 1.4em;
            font-weight: 700;
            color: var(--text);
            margin-bottom: 8px;
        }
        
        .blog-url {
            color: var(--primary);
            font-size: 0.9em;
            text-decoration: none;
            margin-bottom: 20px;
            display: block;
        }
        
        .post-title {
            font-size: 1.15em;
            font-weight: 600;
            margin-bottom: 14px;
        }
        
        .post-title a {
            color: var(--text);
            text-decoration: none;
        }
        
        .post-title a:hover {
            color: var(--primary);
        }
        
        .post-content {
            color: var(--text-dim);
            line-height: 1.8;
            margin-bottom: 20px;
        }
        
        .post-meta {
            display: flex;
            justify-content: space-between;
            padding-top: 16px;
            border-top: 1px solid var(--border);
            font-size: 0.85em;
        }
        
        .discovery-badge {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
            color: var(--primary);
            padding: 6px 14px;
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        
        /* Network View */
        #network-view {
            height: calc(100vh - 80px);
        }
        
        #graph {
            width: 100%;
            height: 100%;
        }
        
        .network-controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }
        
        .btn {
            background: white;
            border: 1px solid var(--border);
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }
        
        .btn:hover {
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }
        
        .tooltip {
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 12px;
            border-radius: 8px;
            pointer-events: none;
            display: none;
            max-width: 300px;
            font-size: 0.9em;
        }
        
        .node { cursor: pointer; stroke: #fff; stroke-width: 2px; transition: all 0.2s; }
        .node:hover { stroke-width: 3px; filter: brightness(1.2); }
        .node.seed { fill: #6366f1; }
        .node.depth-1 { fill: #48bb78; }
        .node.depth-2 { fill: #eab308; }
        .node.depth-3 { fill: #f97316; }
        .node.depth-4plus { fill: #ef4444; }
        .link { stroke: rgba(99, 102, 241, 0.2); stroke-width: 1.5px; }
        .label { font-size: 10px; fill: var(--text); pointer-events: none; text-anchor: middle; }
        
        .legend {
            position: absolute;
            top: 100px;
            right: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--border);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .legend-title {
            font-weight: 700;
            margin-bottom: 12px;
            color: var(--text);
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid white;
        }
        
        @media (max-width: 768px) {
            .blog-grid { grid-template-columns: 1fr; }
            h1 { font-size: 2.5em; }
        }
    </style>
</head>
<body>
    <div class="content">
        <nav>
            <div class="nav-container">
                <div class="logo">✦ Discovery</div>
                <div class="nav-links">
                    <div class="nav-link active" onclick="showView('posts')">
                        <span>📚</span>
                        <span>Posts</span>
                        <span class="stats-badge">{{ total_blogs }}</span>
                    </div>
                    <div class="nav-link" onclick="showView('network')">
                        <span>🕸️</span>
                        <span>Network</span>
                    </div>
                </div>
            </div>
        </nav>
        
        <!-- Posts View -->
        <div id="posts-view" class="view active">
            <div class="header">
                <h1>Discovered Blogs</h1>
                <p class="subtitle">Exploring {{ total_blogs }} interconnected blogs</p>
                <div class="search-container">
                    <span class="search-icon">🔍</span>
                    <input type="text" class="search-box" id="searchInput" placeholder="Search blogs, posts, or content...">
                </div>
            </div>
            
            <div class="container">
                <div class="blog-grid" id="blogGrid">
                    {% for blog in blogs %}
                    <div class="blog-card" data-search="{{ (blog.name + ' ' + blog.latest_post.title + ' ' + blog.latest_post.summary)|lower }}">
                        <div class="blog-name">{{ blog.name }}</div>
                        <a href="{{ blog.url }}" target="_blank" class="blog-url">{{ blog.domain }}</a>
                        <div class="post-title">
                            <a href="{{ blog.latest_post.link }}" target="_blank">{{ blog.latest_post.title }}</a>
                        </div>
                        <div class="post-content">
                            {{ blog.latest_post.summary[:350] }}{% if blog.latest_post.summary|length > 350 %}...{% endif %}
                        </div>
                        <div class="post-meta">
                            <span>{{ blog.latest_post.published[:10] if blog.latest_post.published else 'Unknown' }}</span>
                            {% if blog.discovered_from %}
                            <span class="discovery-badge">✨ Discovered</span>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- Network View -->
        <div id="network-view" class="view">
            <svg id="graph"></svg>
            <div class="legend">
                <div class="legend-title">Discovery Depth</div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #6366f1;"></div>
                    <span>Seed Blogs</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #48bb78;"></div>
                    <span>Level 1</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #eab308;"></div>
                    <span>Level 2</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f97316;"></div>
                    <span>Level 3</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ef4444;"></div>
                    <span>Level 4+</span>
                </div>
            </div>
            <div class="network-controls">
                <button class="btn" onclick="resetNetworkView()">🔄 Reset View</button>
            </div>
            <div class="tooltip" id="tooltip"></div>
        </div>
    </div>
    
    <script>
        const graphData = {{ graph_data|tojson }};
        let network = null;
        
        function showView(view) {
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
            
            document.getElementById(view + '-view').classList.add('active');
            event.target.closest('.nav-link').classList.add('active');
            
            if (view === 'network' && !network) {
                initNetwork();
            }
        }
        
        function initNetwork() {
            const width = window.innerWidth;
            const height = window.innerHeight - 80;
            
            const svg = d3.select("#graph").attr("width", width).attr("height", height);
            const g = svg.append("g");
            
            const zoom = d3.zoom().scaleExtent([0.1, 10]).on("zoom", e => g.attr("transform", e.transform));
            svg.call(zoom);
            
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(120))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width/2, height/2))
                .force("x", d3.forceX(width/2).strength(0.1))
                .force("y", d3.forceY(height/2).strength(0.1));
            
            const link = g.append("g").selectAll("line").data(graphData.links).join("line").attr("class", "link");
            const node = g.append("g").selectAll("circle").data(graphData.nodes).join("circle")
                .attr("class", d => `node ${d.type}`)
                .attr("r", d => d.type === 'seed' ? 10 : (8 - Math.min(d.depth, 4)))
                .call(d3.drag()
                    .on("start", (e,d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx=d.x; d.fy=d.y; })
                    .on("drag", (e,d) => { d.fx=e.x; d.fy=e.y; })
                    .on("end", (e,d) => { if (!e.active) simulation.alphaTarget(0); d.fx=null; d.fy=null; }))
                .on("click", (e, d) => window.open(d.url, '_blank'))
                .on("mouseover", (e,d) => {
                    const t = document.getElementById('tooltip');
                    t.style.display = 'block';
                    t.style.left = (e.pageX+10)+'px';
                    t.style.top = (e.pageY+10)+'px';
                    const depthText = d.type === 'seed' ? 'Seed Blog' : `Level ${d.depth}`;
                    t.innerHTML = `<strong>${d.name}</strong><br><small>${d.url}</small><br><em>${depthText}</em>${d.source ? '<br><br><em>Found by: '+d.source+'</em>' : ''}`;
                })
                .on("mouseout", () => document.getElementById('tooltip').style.display = 'none');
            
            const label = g.append("g").selectAll("text").data(graphData.nodes).join("text")
                .attr("class", "label").text(d => d.label.substring(0,20));
            
            simulation.on("tick", () => {
                link.attr("x1", d=>d.source.x).attr("y1", d=>d.source.y).attr("x2", d=>d.target.x).attr("y2", d=>d.target.y);
                node.attr("cx", d=>d.x).attr("cy", d=>d.y);
                label.attr("x", d=>d.x).attr("y", d=>d.y-12);
            });
            
            window.resetNetworkView = function() {
                const bounds = g.node().getBBox();
                const scale = 0.9 / Math.max(bounds.width/width, bounds.height/height);
                const translate = [width/2 - scale*(bounds.x+bounds.width/2), height/2 - scale*(bounds.y+bounds.height/2)];
                svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale));
            };
            
            setTimeout(() => window.resetNetworkView(), 2000);
            network = true;
        }
        
        // Search functionality
        document.getElementById('searchInput').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            document.querySelectorAll('.blog-card').forEach(card => {
                card.style.display = card.getAttribute('data-search').includes(searchTerm) ? 'block' : 'none';
            });
        });
    </script>
</body>
</html>
'''


def load_data():
    checkpoint_path = os.path.join('json', 'crawler_checkpoint.json')
    results_path = os.path.join('json', 'discovery_results.json')
    
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r') as f:
            data = json.load(f)
            # If checkpoint exists, we assume it's the primary source for current state
            # and return the count of discovered blogs.
            # The rest of the function expects a full data structure, so this path
            # needs to be handled carefully if the UI expects more than just a count.
            # For now, we'll return a dummy full structure if only count is needed.
            # If the UI needs full data from checkpoint, this logic needs adjustment.
            blogs_dict = data['discovered_blogs']
    elif os.path.exists(results_path):
        with open(results_path, 'r') as f:
            data = json.load(f)
        blogs_dict = {b['domain']: b for b in data.get('blogs', [])}
    else:
        return {'blogs': [], 'total_blogs': 0, 'graph_data': {'nodes': [], 'links': []}}
    
    # Posts data
    blogs_list = [{'domain': domain, **info} for domain, info in blogs_dict.items()]
    blogs_list.sort(key=lambda b: b['latest_post'].get('published', '') or '', reverse=True)
    
    # Graph data
    nodes, links = [], []
    for domain, info in blogs_dict.items():
        is_seed = info.get('discovered_from') is None
        depth = info.get('depth', 0)
        
        # Determine node type based on depth
        if is_seed or depth == 0:
            node_type = 'seed'
        elif depth == 1:
            node_type = 'depth-1'
        elif depth == 2:
            node_type = 'depth-2'
        elif depth == 3:
            node_type = 'depth-3'
        else:
            node_type = 'depth-4plus'
        
        nodes.append({
            'id': domain, 'name': info['name'], 'label': info['name'][:25],
            'url': info['url'], 'type': node_type, 'depth': depth,
            'source': info['discovered_from'].get('source_blog_name') if info.get('discovered_from') else None
        })
    
    for domain, info in blogs_dict.items():
        if info.get('discovered_from'):
            source_url = info['discovered_from'].get('source_blog')
            if source_url:
                source_domain = next((d for d,i in blogs_dict.items() if i['url']==source_url), None)
                if source_domain:
                    links.append({'source': source_domain, 'target': domain})
    
    return {
        'blogs': blogs_list,
        'total_blogs': len(blogs_list),
        'graph_data': {'nodes': nodes, 'links': links}
    }


@app.route('/')
def index():
    return render_template_string(COMBINED_TEMPLATE, **load_data())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combined Blog Discovery Viewer')
    parser.add_argument('-p', '--port', type=int, default=5011, 
                        help='Port number to run the server on (default: 5011)')
    args = parser.parse_args()
    
    print("=" * 80)
    print("✦ Combined Blog Discovery Viewer")
    print("=" * 80)
    data = load_data()
    print(f"\n📊 {data['total_blogs']} blogs loaded")
    print(f"🌐 http://localhost:{args.port}\n")
    app.run(debug=False, host='0.0.0.0', port=args.port)
