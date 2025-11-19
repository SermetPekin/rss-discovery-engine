# RSS Discovery Engine

A self-expanding blog discovery system that automatically finds new blogs by exploring network relationships. Start with a few seed blogs and watch it recursively discover hundreds more through link analysis.

## Key Features

- **Automated Discovery**: Finds blogs by analyzing posts and following citations
- **Multiple Strategies**: Breadth-first, depth-first, random, or mixed exploration
- **Smart Filtering**: TLD validation, platform detection, robots.txt compliance
- **Network Visualization**: Interactive graph showing blog relationships
- **Checkpoint Recovery**: Resume from interruptions

## Screenshots

<img width="1584" height="920" alt="Network visualization" src="https://github.com/user-attachments/assets/909e5480-cd89-4cc0-8c77-a98abf503ec6" />

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

## Credits

Inspired by [Andrew Gelman's Statistical Modeling Blog](https://statmodeling.stat.columbia.edu/). The initial 63 seed blogs were sourced from his curated blogroll, providing an excellent foundation of quality, interconnected blogs.

## Notes

- Only accesses public RSS feeds
- Respects robots.txt and implements rate limiting
- Stores metadata only (titles, links, summaries)
- For educational and personal use

## License

MIT License
