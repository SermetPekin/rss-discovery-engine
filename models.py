from datetime import datetime
from typing import List, Optional, Dict, Set, Tuple, Any
from pydantic import BaseModel, Field, HttpUrl

class BlogPost(BaseModel):
    """Represents a single blog post."""
    title: str
    link: HttpUrl
    published: Optional[datetime] = None
    summary: Optional[str] = None
    full_content: Optional[str] = None
    raw_html_content: Optional[str] = None

class DiscoveredFrom(BaseModel):
    """Traceability for where a blog was discovered."""
    source_blog: str
    source_blog_name: Optional[str] = None
    post_link: Optional[str] = None

class BlogInfo(BaseModel):
    """Represents a discovered blog."""
    url: HttpUrl
    name: str
    feed_url: Optional[HttpUrl] = None
    latest_post: Optional[BlogPost] = None
    discovered_from: Optional[DiscoveredFrom] = None
    depth: int = 0
    discovered_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DiscoveryState(BaseModel):
    """Represents the state of the crawler for checkpointing."""
    timestamp: datetime = Field(default_factory=datetime.now)
    discovered_blogs: Dict[str, BlogInfo] = Field(default_factory=dict)
    processed_domains: Set[str] = Field(default_factory=set)
    failed_domains: Set[str] = Field(default_factory=set)
    failed_base_domains: Set[str] = Field(default_factory=set)
    queued_domains: Set[str] = Field(default_factory=set)
    blogs_to_process: List[Tuple[str, Optional[Dict[str, Any]]]] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: list
        }
