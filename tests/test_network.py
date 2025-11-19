#!/usr/bin/env python3
"""
Simple test to check network viewer data
"""
import json
import os

checkpoint_path = os.path.join('json', 'aggressive_checkpoint.json')
if os.path.exists(checkpoint_path):
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)
    
    blogs_dict = data['discovered_blogs']
    
    # Sample a few blogs
    print("Sample blogs:")
    for i, (domain, info) in enumerate(list(blogs_dict.items())[:3]):
        print(f"\n{i+1}. {info['name']}")
        print(f"   Domain: {domain}")
        print(f"   URL: {info['url']}")
        print(f"   Has discovered_from: {info.get('discovered_from') is not None}")
        if info.get('discovered_from'):
            print(f"   Source: {info['discovered_from'].get('source_blog_name')}")

print("\nOpen http://localhost:5005 in your browser")
print("Check browser console (F12) for any JavaScript errors")
