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
    <title>The Discovery Engine</title>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=Libre+Franklin:wght@300;400;500;700&display=swap" rel="stylesheet">
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root {
            --bg: #ffffff;
            --text: #121212;
            --text-secondary: #5a5a5a;
            --border: #e2e2e2;
            --accent: #000000;
            --link: #326891;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }
        
        /* Header / Masthead */
        header {
            border-bottom: 1px solid #000;
            padding: 20px 0;
            margin-bottom: 40px;
            text-align: center;
            position: relative;
        }
        
        .masthead-top {
            border-bottom: 1px solid #e2e2e2;
            padding: 0 20px 10px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #333;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }

        .logo {
            font-family: 'Playfair Display', serif;
            font-size: 3.5rem;
            font-weight: 900;
            letter-spacing: -1px;
            color: #000;
            margin: 10px 0;
            line-height: 1;
        }
        
        .logo-sub {
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 5px;
            color: #666;
        }

        /* Navigation */
        nav {
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            padding: 12px 0;
            margin-top: 20px;
            position: sticky;
            top: 0;
            background: white;
            z-index: 100;
        }
        
        .nav-container {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: center;
            gap: 40px;
        }
        
        .nav-link {
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #000;
            cursor: pointer;
            padding: 5px 0;
            border-bottom: 2px solid transparent;
            transition: border-color 0.2s;
        }
        
        .nav-link:hover, .nav-link.active {
            border-bottom-color: #000;
        }

        /* Content Layout */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px 60px;
        }
        
        .view { display: none; }
        .view.active { display: block; }

        /* Search Bar */
        .search-container {
            margin: 0 auto 40px;
            max-width: 400px;
            text-align: center;
        }
        
        .search-box {
            width: 100%;
            padding: 10px 15px;
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.9rem;
            border: 1px solid #ccc;
            border-radius: 3px;
            background: #f9f9f9;
        }
        
        .search-box:focus {
            outline: none;
            background: #fff;
            border-color: #000;
        }

        /* Blog Grid */
        .blog-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 40px;
            border-top: 1px solid #000;
            padding-top: 40px;
        }
        
        .blog-card {
            padding-bottom: 20px;
            border-bottom: 1px solid #e2e2e2;
        }
        
        .blog-meta-top {
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }
        
        .blog-name {
            color: #000;
        }

        .post-title {
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 12px;
        }
        
        .post-title a {
            color: #000;
            text-decoration: none;
            transition: color 0.2s;
        }
        
        .post-title a:hover {
            color: #555;
        }
        
        .post-summary {
            font-family: 'Georgia', serif;
            font-size: 1rem;
            color: #333;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        
        .post-meta-bottom {
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.75rem;
            color: #888;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .blog-link {
            color: #326891;
            text-decoration: none;
            font-weight: 500;
        }
        
        .blog-link:hover {
            text-decoration: underline;
        }

        /* Network View */
        #network-view {
            height: 80vh;
            border: 1px solid #e2e2e2;
            background: #fcfcfc;
            position: relative;
        }
        
        .network-controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
        }
        
        .btn {
            background: #fff;
            border: 1px solid #000;
            color: #000;
            padding: 8px 16px;
            font-family: 'Libre Franklin', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            cursor: pointer;
            letter-spacing: 1px;
        }
        
        .btn:hover {
            background: #000;
            color: #fff;
        }

        .legend {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.9);
            padding: 15px;
            border: 1px solid #ccc;
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.8rem;
        }

        /* Tooltip */
        .tooltip {
            position: absolute;
            background: #fff;
            border: 1px solid #000;
            padding: 10px;
            font-family: 'Libre Franklin', sans-serif;
            font-size: 0.8rem;
            pointer-events: none;
            display: none;
            box-shadow: 4px 4px 0px rgba(0,0,0,0.1);
        }

        /* D3 Styles */
        .node { stroke: #fff; stroke-width: 2px; filter: drop-shadow(0px 1px 2px rgba(0,0,0,0.1)); transition: all 0.3s; }
        .node:hover { stroke: #000; stroke-width: 2px; filter: drop-shadow(0px 4px 6px rgba(0,0,0,0.2)); }
        .link { stroke: #cbd5e1; stroke-width: 1px; opacity: 0.6; }

    </style>
</head>
<body>
    <header>
        <div class="masthead-top">
            <span>{{ total_blogs }} Sources Discovered</span>
            <span>Updated: Today</span>
        </div>
        <div class="logo">The Discovery Engine</div>
        <div class="logo-sub">Curated Blog Network & Feed Reader</div>
    </header>

    <nav>
        <div class="nav-container">
            <div class="nav-link active" onclick="showView('posts')">Front Page</div>
            <div class="nav-link" onclick="showView('network')">Network Map</div>
        </div>
    </nav>

    <div class="container">
        <!-- Posts View -->
        <div id="posts-view" class="view active">
            <div class="search-container">
                <input type="text" class="search-box" id="searchInput" placeholder="Search articles...">
            </div>
            
            <div class="blog-grid" id="blogGrid">
                {% for blog in blogs %}
                <div class="blog-card" data-search="{{ (blog.name + ' ' + blog.latest_post.title + ' ' + blog.latest_post.summary)|lower }}">
                    <div class="blog-meta-top">
                        <span class="blog-name">{{ blog.name }}</span>
                    </div>
                    <div class="post-title">
                        <a href="{{ blog.latest_post.link }}" target="_blank">{{ blog.latest_post.title }}</a>
                    </div>
                    <div class="post-summary">
                        {{ blog.latest_post.summary[:250] }}{% if blog.latest_post.summary|length > 250 %}...{% endif %}
                    </div>
                    <div class="post-meta-bottom">
                        <span>{{ blog.latest_post.published[:10] if blog.latest_post.published else 'Unknown Date' }}</span>
                        <a href="{{ blog.url }}" target="_blank" class="blog-link">Visit Site &rarr;</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Network View -->
        <div id="network-view" class="view">
            <svg id="graph"></svg>
            <div class="legend">
                <strong>Discovery Depth</strong><br><br>
                <span style="color:#4f46e5">●</span> Seed Blog<br>
                <span style="color:#059669">●</span> Level 1<br>
                <span style="color:#d97706">●</span> Level 2<br>
                <span style="color:#db2777">●</span> Level 3<br>
                <span style="color:#475569">●</span> Level 4+
            </div>
            <div class="network-controls">
                <button class="btn" onclick="resetNetworkView()">Reset View</button>
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
            event.target.classList.add('active');
            
            if (view === 'network' && !network) {
                initNetwork();
            }
        }
        
        function initNetwork() {
            const container = document.getElementById('network-view');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            const svg = d3.select("#graph").attr("width", width).attr("height", height);
            const g = svg.append("g");
            
            const zoom = d3.zoom().scaleExtent([0.1, 10]).on("zoom", e => g.attr("transform", e.transform));
            svg.call(zoom);
            
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-200))
                .force("center", d3.forceCenter(width/2, height/2));
            
            const link = g.append("g").selectAll("line").data(graphData.links).join("line").attr("class", "link");
            
            // Vibrant palette for network
            const getColor = (type) => {
                if (type === 'seed') return '#4f46e5';      // Indigo
                if (type === 'depth-1') return '#059669';   // Emerald
                if (type === 'depth-2') return '#d97706';   // Amber
                if (type === 'depth-3') return '#db2777';   // Pink
                return '#475569';                           // Slate
            };

            const node = g.append("g").selectAll("circle").data(graphData.nodes).join("circle")
                .attr("class", "node")
                .attr("r", d => d.type === 'seed' ? 8 : (6 - Math.min(d.depth, 3)))
                .attr("fill", d => getColor(d.type))
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
                    t.innerHTML = `<strong>${d.name}</strong><br>${d.url}`;
                })
                .on("mouseout", () => document.getElementById('tooltip').style.display = 'none');
            
            // Add labels to nodes
            const label = g.append("g").selectAll("text").data(graphData.nodes).join("text")
                .attr("class", "label")
                .text(d => d.name.length > 15 ? d.name.substring(0, 15) + '...' : d.name)
                .attr("dx", 12)
                .attr("dy", 4);

            simulation.on("tick", () => {
                link.attr("x1", d=>d.source.x).attr("y1", d=>d.source.y).attr("x2", d=>d.target.x).attr("y2", d=>d.target.y);
                node.attr("cx", d=>d.x).attr("cy", d=>d.y);
                label.attr("x", d=>d.x).attr("y", d=>d.y);
            });
            
            window.resetNetworkView = function() {
                svg.transition().duration(750).call(zoom.transform, d3.zoomIdentity);
            };
            
            network = true;
        }
        
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
