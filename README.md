# Recursive Blog Discovery

A self-expanding blog discovery system that automatically finds new blogs by exploring network relationships. Start with a few seed blogs and watch it recursively discover hundreds more through link analysis.

👉 **[View Live Demo](https://sermetpekin.github.io/rss-discovery-engine/)**

## Key Features

- **Automated Discovery**: Finds blogs by analyzing posts and following citations
- **Multiple Strategies**: Breadth-first, depth-first, random, or mixed exploration
- **Smart Filtering**: TLD validation, platform detection, robots.txt compliance
- **Network Visualization**: Interactive graph showing blog relationships
- **Checkpoint Recovery**: Resume from interruptions

## Screenshots

<img width="1592" height="907" alt="Network visualization" src="https://github.com/user-attachments/assets/6646746b-579c-4d02-9d8f-0957e9d90480" />

<img width="1418" height="935" alt="Blog dashboard" src="https://github.com/user-attachments/assets/6dd207de-81be-4212-9b08-93a488148bf1" />

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Add seed blogs to seeds.txt, then run
python discover.py

# Start fresh (archives old results)
python discover.py --fresh

# View results
python view.py -p 5011
```

Open `http://localhost:5011` to explore discovered blogs and the network graph.

## Configuration

Key settings in `config.py`:

- `MAX_BLOGS_DEFAULT`: Target number of blogs (default: 250)
- `QUEUE_STRATEGY`: `breadth_first`, `depth_first`, `random`, or `mixed`
- `MAX_POSTS_TO_CHECK`: Posts to analyze per blog (default: 20)
- `CHECKPOINT_INTERVAL`: Save progress every N blogs (default: 5)

Run options:
```bash
python discover.py --fresh              # Start from scratch
python discover.py --strategy depth_first
```

## Technical Details

### How it detects "Blogs"
The engine uses a multi-layered approach to distinguish blogs from other websites:
1.  **RSS/Atom Feed**: The strongest signal. A site must have a valid feed to be indexed.
2.  **Domain Filtering**: Allows standard TLDs (.com, .org, .io, .edu) but blocks social media platforms (Twitter, Facebook, LinkedIn), code repositories (GitHub), and encyclopedias (Wikipedia).
3.  **Platform Indicators**: Detects common blog platforms (Substack, WordPress, Ghost) and URL patterns (e.g., `/blog/`, `/posts/`).

### Graph Construction
This tool focuses on the **crawling and graph construction** phase. It builds a directed graph of the blogosphere based on citations (links). While it does not currently implement ranking algorithms (like eigenvector centrality), the resulting graph data can be used for such analysis.

## Credits

Inspired by [Andrew Gelman's Statistical Modeling Blog](https://statmodeling.stat.columbia.edu/). The initial 63 seed blogs were sourced from his curated blogroll, providing an excellent foundation of quality, interconnected blogs.

Special thanks to Andrew for [featuring this project](https://statmodeling.stat.columbia.edu/2025/11/30/sermet-pekins-open-source-project-that-discovers-blogs-through-recursive-network-exploration/) on his blog!

## Notes

- Only accesses public RSS feeds
- Respects robots.txt and implements rate limiting
- Stores metadata only (titles, links, summaries)
- For educational and personal use

## License

BSD 3-Clause License
