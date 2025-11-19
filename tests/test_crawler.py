
import logging
from discover import RecursiveBlogDiscovery

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_crawler():
    print("Starting test crawl...")
    
    # Initialize with small limits for testing
    crawler = RecursiveBlogDiscovery(max_blogs=5, max_posts_to_check=20)
    
    # Use a small subset of seeds
    test_seeds = [
        "https://statmodeling.stat.columbia.edu/",
        "https://flowingdata.com/"
    ]
    
    # Run discovery
    results = crawler.run_discovery(test_seeds)
    
    print(f"Discovery complete. Found {len(results)} blogs.")
    
    # Save results to verify output generation
    crawler.save_results('test_results.json')
    print("Results saved.")


if __name__ == "__main__":
    test_crawler()
