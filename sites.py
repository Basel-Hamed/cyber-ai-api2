"""
Cyber AI Learning Resources Configuration
"""

SITES = {
    "portswigger": {
        "name": "PortSwigger",
        "url": "https://portswigger.net/web-security",
        "category": "web-security",
        "language": "en",
        "priority": 1
    },
    "owasp": {
        "name": "OWASP",
        "url": "https://owasp.org/www-community/",
        "category": "web-security",
        "language": "en",
        "priority": 2
    },
    "hacksplaining": {
        "name": "Hacksplaining",
        "url": "https://www.hacksplaining.com/lessons",
        "category": "security-training",
        "language": "en",
        "priority": 3
    },
    "exploit-db": {
        "name": "Exploit Database",
        "url": "https://www.exploit-db.com/docs",
        "category": "exploits",
        "language": "en",
        "priority": 4
    },
    "cybrary": {
        "name": "Cybrary",
        "url": "https://www.cybrary.it/catalog/cybersecurity/",
        "category": "training",
        "language": "en",
        "priority": 5
    },
    "sans": {
        "name": "SANS Institute",
        "url": "https://www.sans.org/white-papers/",
        "category": "research",
        "language": "en",
        "priority": 6
    },
    "nist": {
        "name": "NIST",
        "url": "https://csrc.nist.gov/publications",
        "category": "standards",
        "language": "en",
        "priority": 7
    },
    "cve": {
        "name": "CVE Details",
        "url": "https://www.cvedetails.com/",
        "category": "vulnerabilities",
        "language": "en",
        "priority": 8
    },
    "security-blogs": {
        "name": "Security Blogs",
        "url": "https://security.googleblog.com/",
        "category": "blogs",
        "language": "en",
        "priority": 9
    }
}

# Helper functions
def get_sites_by_category(category: str) -> dict:
    """Get sites filtered by category"""
    return {
        name: info 
        for name, info in SITES.items() 
        if info.get("category") == category
    }

def get_sites_by_priority(limit: int = 5) -> dict:
    """Get top priority sites"""
    sorted_sites = sorted(
        SITES.items(), 
        key=lambda x: x[1].get("priority", 999)
    )
    return dict(sorted_sites[:limit])

def get_site_info(site_name: str) -> dict:
    """Get specific site information"""
    return SITES.get(site_name, {})

def get_all_categories() -> list:
    """Get all unique categories"""
    categories = set()
    for info in SITES.values():
        if "category" in info:
            categories.add(info["category"])
    return sorted(list(categories))

def get_site_count() -> int:
    """Get total number of sites"""
    return len(SITES)

# Site statistics
SITE_STATS = {
    "total": get_site_count(),
    "categories": get_all_categories(),
    "languages": ["en", "bn"],
    "last_updated": "2024-01-01"
}
