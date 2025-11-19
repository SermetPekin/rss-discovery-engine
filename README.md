# Recursive Blog Discovery Engine

An intelligent, self-expanding blog discovery system that maps interconnected blog networks through recursive exploration. Like Google's web crawler but optimized for RSS feeds and content discovery.

## 🌟 What Makes This Special

Unlike traditional RSS readers that require manual subscriptions, this engine **automatically discovers blogs** by exploring network relationships:

- **Starts Small, Grows Exponentially**: Begin with curated seeds (e.g., 63 quality blogs)
- **Self-Expanding Network**: Each blog analyzed reveals 10-20 new blogs through citation analysis
- **Infinite Scale**: Discovers hundreds to thousands of blogs depending on network depth
- **Graph-Based Exploration**: Maps the entire blog ecosystem and their interconnections


<img width="1584" height="920" alt="image" src="https://github.com/user-attachments/assets/909e5480-cd89-4cc0-8c77-a98abf503ec6" />


<img width="1418" height="935" alt="image" src="https://github.com/user-attachments/assets/6dd207de-81be-4212-9b08-93a488148bf1" />

## Features

- **Recursive Network Discovery**: Explores blog networks like Google crawls the web, following citations and references
- **Configurable Exploration Strategies**:
  - **Breadth-First**: Process seeds first, explore layer by layer
  - **Depth-First**: Dive deep into niche communities quickly
  - **Random**: Maximum diversity in discovery
  - **Mixed**: Balanced exploration (default)
- **Smart Filtering**:
  - **TLD Validation**: Only crawls domains with allowed extensions (e.g., .com, .org, .io, .edu, .uk, etc.).
  - **Multi-Platform Support**: Substack, WordPress, Blogspot, Medium, Ghost, and custom blogs
  - **robots.txt Compliance**: Respects website policies with rate limiting (2s per domain)
  - **Safety**: Blocks dangerous file extensions and suspicious URL patterns
- **Production-Ready Features**:
  - **Checkpoint Recovery**: Resume from crashes or interruptions
  - **Rate Limiting**: Ethical crawling with configurable delays
  - **Network Visualization**: Interactive graph showing blog relationships
  - **Multi-User System**: Personalized feeds for multiple users
- **Interactive Web Viewer**: Dashboard to explore discovered blogs and visualize the network graph

## Installation

1.  Clone the repository.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Configure Seeds
Add your starting blog URLs to `seeds.txt`, one per line. Lines starting with `#` are comments.

### 2. Run the Crawler
Start the discovery process:
```bash
python discover.py
```

**Options:**
*   **Resume**: By default, it resumes from the last checkpoint
*   **Fresh Start**: `python discover.py --fresh` to archive old results and start over
*   **Choose Strategy**: 
    - `python discover.py --strategy breadth_first` - Seeds first, level-by-level
    - `python discover.py --strategy depth_first` - Explore deep into networks
    - `python discover.py --strategy random` - Random exploration
    - `python discover.py --strategy mixed` - Balanced (default)

**The crawler will:**
1. Start with your seed blogs
2. Fetch their RSS feeds and latest posts
3. Extract blog links from post content
4. Recursively explore discovered blogs
5. Build a network graph of interconnections
6. Save progress every 5 blogs (configurable)

### 3. View Results
Launch the web viewer to explore the discovered blogs and network graph:
```bash
python view.py
```
Open your browser to `http://localhost:5011`.

## Configuration

Edit `config.py` to customize behavior:

### Scale & Performance
- **`MAX_BLOGS_DEFAULT`**: Target number of blogs to discover (default: 250, configurable to thousands)
- **`MAX_POSTS_TO_CHECK`**: Posts to analyze per blog for link discovery (default: 20)
- **`CHECKPOINT_INTERVAL`**: Save progress every N blogs (default: 5)
- **`REQUEST_TIMEOUT`**: HTTP request timeout in seconds (default: 10)

### Queue Strategy
- **`QUEUE_STRATEGY`**: How to prioritize blog discovery
  - `breadth_first`: Process all seeds first, then discovered blogs layer-by-layer
  - `depth_first`: Dive deep into blog networks quickly
  - `random`: Random exploration for maximum diversity
  - `mixed`: 50/50 balance between breadth and depth (default)

### Platform Support
- **`ALLOWED_EXTENSIONS`**: Permitted domain TLDs (.com, .org, .io, etc.)
- **`BLOG_INDICATORS`**: Keywords to identify blog platforms
- **`SKIP_DOMAINS`**: Social media and non-blog sites to ignore

### Network & Security
- Rate limiting: 2 seconds between requests to same domain
- robots.txt: Automatically respected
- User-Agent: Properly identified
- Dangerous URLs: Auto-blocked (.exe, .dll, malware patterns)

## Output Files

- **`json/crawler_checkpoint.json`**: Current crawl state (resumable)
- **`json/discovery_results.json`**: Final discovered blogs with metadata
- **`archive/`**: Archived results from previous runs

## How It Works: The Discovery Algorithm

1. **Seed Phase**: Starts with curated blogs (e.g., 63 high-quality sources)
2. **Fetch & Parse**: Downloads RSS feeds, extracts latest posts (configurable 1-20 posts)
3. **Link Extraction**: Analyzes post content for blog URLs using smart pattern matching
4. **Validation**: 
   - Checks TLD against allowlist
   - Verifies RSS/Atom feed exists
   - Validates robots.txt permissions
   - Filters out social media and known non-blogs
5. **Recursive Expansion**: Newly discovered blogs are queued for processing
6. **Network Building**: Tracks discovery relationships (who linked to whom)
7. **Checkpointing**: Saves progress every 5 blogs for crash recovery

**Growth Pattern:**
- 63 seeds → ~10-20 links per blog → 630-1,260 first-level discoveries
- Each level discovers more blogs exponentially
- Configurable depth limits prevent infinite crawling
- Network quickly reaches hundreds to thousands of interconnected blogs

## Architecture

```
discover.py          # Main crawler engine with recursive logic
├── RecursiveBlogDiscovery class
│   ├── Queue strategies (breadth/depth/random/mixed)
│   ├── Platform detection (Substack, WordPress, etc.)
│   ├── Rate limiting & robots.txt compliance
│   └── Checkpoint system
│
view.py             # Web dashboard for visualization
├── Flask server (port 5011)
├── Network graph rendering
└── Blog metadata display

config.py           # Centralized configuration
seeds.txt          # Starting blog URLs
json/              # All data files (checkpoints, results)
```

## Legal & Ethical Considerations

### RSS Feeds
This project only accesses **publicly available RSS/Atom feeds** that are intentionally published by blog authors for aggregation and syndication. RSS feeds are designed to be consumed by feed readers and aggregators.

### robots.txt Compliance
The crawler respects `robots.txt` directives and implements:
- Rate limiting (2 seconds between requests to the same domain)
- Proper User-Agent identification
- Timeout handling to avoid server overload

### Fair Use
- Only **metadata** (titles, links, summaries) is stored
- Full articles remain on original sites
- All content links back to the source
- No commercial use or redistribution of content

### Disclaimer
This software is provided for **educational and personal use only**. Users are responsible for:
- Complying with applicable laws and regulations
- Respecting the Terms of Service of websites they access
- Ensuring their use constitutes fair use or is otherwise legally permissible
- Not using this tool for commercial purposes without proper authorization

Blog owners who wish to opt-out should use standard `robots.txt` directives, which this crawler respects.

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
- `discovery_results.json`: Final list of discovered blogs and metadata.
- `seeds.txt`: List of seed URLs.
