# RSS Discovery Engine

A recursive crawler designed to map the independent web. It starts with a handful of seed blogs and follows the breadcrumbs—citations, blogrolls, and links—to discover the hidden network of writers and thinkers.

👉 **[View Live Demo](https://sermetpekin.github.io/rss-discovery-engine/)**


## Why this exists

Most discovery today is algorithmic, driven by engagement metrics on centralized platforms. This engine takes a different approach: it trusts the writers you already read. By following who they link to, we can uncover a graph of high-quality, human-curated content that often flies under the radar of search engines and social feeds.

## How it works

The engine uses a recursive strategy:
1.  **Ingest**: Starts with a list of trusted "seed" blogs.
2.  **Crawl**: Fetches the latest posts via RSS/Atom feeds.
3.  **Analyze**: Scans content for outbound links to other domains.
4.  **Verify**: Checks if those domains are valid blogs (active feeds, non-corporate, non-spam).
5.  **Expand**: Adds verified blogs to the queue and repeats.

The result is a directed graph of the blogosphere, visualized interactively to show communities and connections.

## Architecture

Built with Python, this project emphasizes robustness and modularity:
-   **Data Validation**: Uses **Pydantic** for strict type checking and data modeling.
-   **Configuration**: Environment-aware settings management via `pydantic-settings`.
-   **State Management**: Resilient checkpointing system that saves progress automatically, allowing long-running crawls to be paused and resumed.
-   **Graph Visualization**: A D3.js frontend to explore the discovered network.

## Getting Started

### Prerequisites
-   Python 3.9+
-   `pip`

### Installation

```bash
git clone https://github.com/sermetpekin/rss-discovery-engine.git
cd rss-discovery-engine
pip install -r requirements.txt
```

### Usage

1.  **Seed the crawler**: Add your favorite blog URLs to `seeds.txt`.

2.  **Run discovery**:
    ```bash
    python discover.py
    ```
    By default, this will automatically resume from the most recent checkpoint with the most progress. If no checkpoint exists, it starts fresh.

    **Command Line Options:**

    *   `--fresh`: Archive all old results and start a completely new crawl from the seeds.
    *   `--checkpoint [file|count]`: Resume from a specific point. You can provide a full file path or just the number of blogs (e.g., `--checkpoint 140` will find the checkpoint with ~140 blogs).
    *   `--strategy [mixed|breadth_first|depth_first|random]`: Change how the crawler prioritizes the queue. Default is `mixed`.

    **Examples:**
    ```bash
    # Resume from the best available checkpoint (default behavior)
    python discover.py

    # Start over completely
    python discover.py --fresh

    # Resume from a specific backup with ~140 blogs
    python discover.py --checkpoint 140

    # Prioritize exploring deep into the network
    python discover.py --strategy depth_first
    ```

3.  **Visualize**:
    ```bash
    python view.py
    ```
    Open `http://localhost:5011` to see the graph.

## Configuration

Settings are managed in `config.py` and can be overridden by environment variables.

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_BLOGS_DEFAULT` | 250 | Target number of blogs to find |
| `QUEUE_STRATEGY` | `mixed` | How to prioritize the crawl queue |
| `CHECKPOINT_INTERVAL` | 5 | Save state every N blogs |

## Screenshots
<img width="1592" height="907" alt="Network visualization" src="https://github.com/user-attachments/assets/6646746b-579c-4d02-9d8f-0957e9d90480" />

<img width="1360" height="932" alt="Network Graph" src="https://github.com/user-attachments/assets/1a0278b7-bd15-4b39-82be-ccf9303e8b2b" />

## Credits

This project was inspired by [Andrew Gelman's Statistical Modeling Blog](https://statmodeling.stat.columbia.edu/). The initial seed list was sourced from his blogroll, which provided a dense, high-quality starting point for the network.

Special thanks to Andrew for [featuring this project](https://statmodeling.stat.columbia.edu/2025/11/30/sermet-pekins-open-source-project-that-discovers-blogs-through-recursive-network-exploration/).

## License

BSD 3-Clause License
