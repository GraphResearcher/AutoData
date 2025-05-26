# Demo
Here, we present an example to leverage AutoData to collect dataset  with the following task instruction:

```
Collect all papers accepted in NeurIPS 2024.
```

## Plan Agent 
```python   
{
    "step_1": {
        "name": "Identify Data Sources",
        "description": "Research and list all official sources where NeurIPS 2024 papers are published (e.g., NeurIPS Proceedings, official website, arXiv, etc.).",
        "agent": "Tool Agent"
    },
    "step_2": {
        "name": "Analyze Web Structure",
        "description": "Examine the NeurIPS 2024 official website and/or proceedings page to understand the structure (URLs, pagination, paper detail pages, etc.).",
        "agent": "Web Agent"
    },
    "step_3": {
        "name": "Define Data Schema",
        "description": "Determine which metadata fields to collect for each paper.",
        "agent": "Web Agent"
    },
    "step_4": {
        "name": "Locate Download Links",
        "description": "Identify the precise location and format of paper download links (PDFs, supplementary files, etc.) on the site.",
        "agent": "Web Agent"
    },
    "step_5": {
        "name": "Investigate API Availability",
        "description": "Search for any official APIs or data dumps provided by NeurIPS for bulk paper access.",
        "agent": "Web Browser Agent"
    },
    "step_6": {
        "name": "Survey Existing Tools",
        "description": "Research existing open-source tools or libraries for scraping NeurIPS or similar conference sites.",
        "agent": "Web Browser Agent"
    },
    "step_7": {
        "name": "Identify Anti-Scraping Measures",
        "description": "Investigate if the site employs anti-scraping mechanisms (CAPTCHA, rate limiting, etc.) and document them.",
        "agent": "Web Browser Agent"
    }
}
            
```

## Tool Agent
### Input:
```python
{
    "tool": "SearchGoogleTool",
    "description": "Search Google for the given query.",
    "parameters": {
        "query": "neurips 2024 proceedings"
    }
}
```
### Output:
```python
{
    "results": [
        {
            "title": "NeurIPS 2024 Proceedings",
            "url": "https://papers.nips.cc/"
        }
    ]
}
```

## Web Agent
```python
'''
I have identified the data structure in the url https://papers.nips.cc/ and the data is in the following format:
- The url https://papers.nips.cc/paper_files/paper/2024 contains all the paper information about accepted papers in NeurIPS 2024.
- Under the above url, each paper is listed between tag <li class="conference"></li> or <li class="datasets_and_benchmarks_track"> with an paper detailed url between tag <a></a>
'''
```

***Skip further steps for clarity***


## Blueprint Agent

### Technical Analysis and HTML Structure Mapping

#### 1. NeurIPS Website Structure Analysis

**Base URL Pattern Analysis:**
- Main proceedings: `https://papers.nips.cc/`
- Year-specific proceedings: `https://papers.nips.cc/paper_files/paper/2024`
- Individual paper detail: `https://papers.nips.cc/paper_files/paper/2024/hash/{hash}-Abstract-Conference.html`

**URL Construction Strategy:**
- Base URL: `https://papers.nips.cc`
- Proceedings URL: `{base_url}/paper_files/paper/{year}`
- Paper detail URL: `{base_url}/paper_files/paper/{year}/hash/{paper_hash}-Abstract-Conference.html`

#### 2. Proceedings Page HTML Structure (2024 Analysis)

**Paper Listing Extraction Strategy:**
```html
<!-- Target structure for paper listings -->
<li class="conference">
    <a href="/paper_files/paper/2024/hash/000f947dcaff8fbffcc3f53a1314f358-Abstract-Conference.html">
        Paper Title Here
    </a>
</li>

<li class="datasets_and_benchmarks_track">
    <a href="/paper_files/paper/2024/hash/another_hash-Abstract-Conference.html">
        Another Paper Title
    </a>
</li>
```

**Key Extraction Selectors:**
- **Main Conference Track Papers**: `li.conference > a[href*="/hash/"]`
- **Datasets & Benchmarks Track**: `li.datasets_and_benchmarks_track > a[href*="/hash/"]`
- **Fallback All Papers**: `a[href*="/paper_files/paper/2024/hash/"][href*="-Abstract-Conference.html"]`
- **Paper Title**: Extract from `<a>` tag text content
- **Paper URL**: Extract from `href` attribute, make absolute with base URL

**Track Identification Logic:**
- Check parent `<li>` class attribute
- `class="conference"` → "Main Conference Track"
- `class="datasets_and_benchmarks_track"` → "Datasets and Benchmarks Track"
- Default fallback → "Main Conference Track"

#### 3. Paper Detail Page HTML Structure Analysis

**Title Extraction:**
```html
<h4>Paper Title Goes Here</h4>
```
- **Primary selector**: `h4` (most reliable based on provided HTML)
- **Fallback selectors**: `h1`, `h2`, `h3`, `meta[name="citation_title"]`

**Authors Extraction:**
```html
<p><i>Author Name 1, Author Name 2, Author Name 3</i></p>
```
- **Primary selector**: `p > i` (italic text within paragraph)
- **Fallback selectors**: `meta[name="citation_author"]` (multiple meta tags)
- **Parsing strategy**: Split by comma, strip whitespace, handle multiple formats

**Abstract Extraction:**
```html
<h4>Abstract</h4>
<p>
    <p>The actual abstract content goes here...</p>
</p>
```
- **Primary strategy**: Find `h4` containing "Abstract", get next sibling `p` element
- **Nested paragraph handling**: Extract from nested `<p>` within the sibling
- **Fallback selector**: `meta[name="citation_abstract"]`

**Download Links Extraction:**
```html
<!-- Paper PDF Link -->
<a href="/paper_files/paper/2024/file/000f947dcaff8fbffcc3f53a1314f358-Paper-Conference.pdf">
    <button>Paper</button>
</a>

<!-- BibTeX Link -->
<a href="/paper_files/paper/2024/hash/000f947dcaff8fbffcc3f53a1314f358-Abstract-Conference-bib.txt">
    <button>Bibtex</button>
</a>

<!-- Supplemental Material Link -->
<a href="/paper_files/paper/2024/file/000f947dcaff8fbffcc3f53a1314f358-Supplemental-Conference.zip">
    <button>Supplemental</button>
</a>
```

**Link Extraction Selectors:**
- **Paper PDF**: `a[href*="-Paper-Conference.pdf"]` or button text contains "Paper"
- **BibTeX**: `a[href*="-bib.txt"]` or button text contains "Bibtex"
- **Supplemental**: `a[href*="-Supplemental-"]` or button text contains "Supplement"

**Meta Tags for Additional Data:**
```html
<meta name="citation_title" content="Paper Title">
<meta name="citation_author" content="Author Name 1">
<meta name="citation_author" content="Author Name 2">
<meta name="citation_publication_date" content="2024">
<meta name="citation_conference_title" content="Advances in Neural Information Processing Systems 37">
<meta name="citation_pdf_url" content="https://papers.nips.cc/paper_files/paper/2024/file/hash-Paper-Conference.pdf">
```

#### 4. Adaptive Extraction Strategy for 2025

**Structure Change Detection:**
- Monitor for changes in CSS class names (`conference`, `datasets_and_benchmarks_track`)
- Validate URL patterns remain consistent
- Check for new track categories or paper types
- Verify meta tag structure consistency

**Fallback Mechanisms:**
- If track-specific classes change, use URL pattern matching
- If title selector changes, try multiple heading levels
- If author format changes, implement multiple parsing strategies
- If abstract structure changes, use text pattern matching

**Year-Agnostic URL Construction:**
```python
# Dynamic URL building for any year
base_url = "https://papers.nips.cc"
proceedings_url = f"{base_url}/paper_files/paper/{year}"
paper_detail_pattern = f"{base_url}/paper_files/paper/{year}/hash/{{hash}}-Abstract-Conference.html"
```

#### 5. Data Extraction Implementation Strategy

**Multi-Strategy Extraction:**
1. **Primary Strategy**: Use 2024-validated selectors
2. **Secondary Strategy**: Use meta tags as fallback
3. **Tertiary Strategy**: Use text pattern matching
4. **Validation**: Cross-check extracted data between strategies

**Error Handling for Missing Elements:**
- Graceful degradation when elements not found
- Log missing data for analysis
- Continue processing other papers if one fails
- Implement retry logic for network failures

**Data Quality Validation:**
- Title: Minimum 5 characters, no HTML tags
- Authors: At least one author, proper name format
- Abstract: Minimum 50 characters, coherent text
- URLs: Valid HTTP/HTTPS format, accessible links

#### 6. Specific Implementation Details

**CSS Selector Priority Order:**
```python
TITLE_SELECTORS = [
    'h4',  # Primary based on 2024 structure
    'h1', 'h2', 'h3',  # Fallback heading levels
    'meta[name="citation_title"]'  # Meta tag fallback
]

AUTHOR_SELECTORS = [
    'p > i',  # Primary italic text in paragraph
    'meta[name="citation_author"]',  # Meta tags (multiple)
    '.authors',  # Potential class-based selector
    '[class*="author"]'  # Any class containing "author"
]

ABSTRACT_SELECTORS = [
    'h4:contains("Abstract") + p p',  # Nested paragraph after Abstract header
    'h4:contains("Abstract") + p',  # Direct paragraph after Abstract header
    'meta[name="citation_abstract"]',  # Meta tag fallback
    '.abstract'  # Potential class-based selector
]
```

**Link Pattern Matching:**
```python
LINK_PATTERNS = {
    'paper_pdf': [
        r'href="[^"]*-Paper-Conference\.pdf"',
        r'href="[^"]*\.pdf"'
    ],
    'bibtex': [
        r'href="[^"]*-bib\.txt"',
        r'href="[^"]*\.bib"'
    ],
    'supplemental': [
        r'href="[^"]*-Supplemental-[^"]*"',
        r'href="[^"]*supplement[^"]*"'
    ]
}
```

**Track Detection Logic:**
```python
def detect_track(li_element):
    class_attr = li_element.get('class', [])
    if 'datasets_and_benchmarks_track' in class_attr:
        return "Datasets and Benchmarks Track"
    elif 'conference' in class_attr:
        return "Main Conference Track"
    else:
        # Fallback: check surrounding text or URL patterns
        return determine_track_from_context(li_element)
```

This technical analysis provides the specific implementation details needed to build a robust scraper that can adapt from the known 2024 structure to the anticipated 2025 structure while maintaining high reliability and data quality.


## Engineer Agent
```python
import asyncio
import aiohttp
import json
import csv
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Paper:
    """Data model for NeurIPS paper"""
    title: str
    authors: List[str]
    abstract: str
    conference: str = "Advances in Neural Information Processing Systems"
    abbr: str = "NeurIPS"
    track: str = ""
    paper_link: Optional[str] = None
    bibtex_link: Optional[str] = None
    supp_link: Optional[str] = None
    year: int = 2025
    paper_id: Optional[str] = None
    source_url: Optional[str] = None
    scraped_at: str = ""

    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()

class NeurIPSCrawler:
    """Main crawler for NeurIPS papers"""
    
    def __init__(self, year: int = 2025, delay: float = 1.0):
        self.year = year
        self.delay = delay
        self.base_url = "https://papers.nips.cc"
        self.session = None
        self.papers: List[Paper] = []
        
        # Selectors based on technical analysis
        self.TITLE_SELECTORS = ['h4', 'h1', 'h2', 'h3', 'meta[name="citation_title"]']
        self.AUTHOR_SELECTORS = ['p > i', 'meta[name="citation_author"]']
        self.ABSTRACT_SELECTORS = ['h4:contains("Abstract") + p p', 'h4:contains("Abstract") + p', 'meta[name="citation_abstract"]']
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> str:
        """Fetch a web page with error handling and rate limiting"""
        await asyncio.sleep(self.delay)
        
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise
    
    def get_proceedings_url(self) -> str:
        """Generate proceedings URL for the target year"""
        return f"{self.base_url}/paper_files/paper/{self.year}"
    
    def extract_paper_listings(self, html: str) -> List[Dict[str, str]]:
        """Extract paper listings from proceedings page"""
        soup = BeautifulSoup(html, 'html.parser')
        papers = []
        
        # Extract Main Conference Track papers
        main_papers = soup.select('li.conference > a[href*="/hash/"]')
        for link in main_papers:
            paper_info = self._extract_paper_info_from_link(link, "Main Conference Track")
            if paper_info:
                papers.append(paper_info)
        
        # Extract Datasets and Benchmarks Track papers
        datasets_papers = soup.select('li.datasets_and_benchmarks_track > a[href*="/hash/"]')
        for link in datasets_papers:
            paper_info = self._extract_paper_info_from_link(link, "Datasets and Benchmarks Track")
            if paper_info:
                papers.append(paper_info)
        
        # Fallback: extract all papers if track-specific extraction fails
        if not papers:
            all_links = soup.select(f'a[href*="/paper_files/paper/{self.year}/hash/"][href*="-Abstract-Conference.html"]')
            for link in all_links:
                track = self._determine_track_from_context(link)
                paper_info = self._extract_paper_info_from_link(link, track)
                if paper_info:
                    papers.append(paper_info)
        
        logger.info(f"Found {len(papers)} papers in proceedings")
        return papers
    
    def _extract_paper_info_from_link(self, link_element, track: str) -> Optional[Dict[str, str]]:
        """Extract paper information from a link element"""
        href = link_element.get('href')
        if not href:
            return None
        
        # Make URL absolute
        detail_url = urljoin(self.base_url, href)
        
        # Validate URL pattern
        if not re.search(r'/paper_files/paper/\d+/hash/[a-f0-9]+-Abstract', detail_url):
            return None
        
        # Extract paper title and ID
        title = link_element.get_text(strip=True)
        paper_id = self._extract_paper_id_from_url(href)
        
        return {
            'title': title,
            'detail_url': detail_url,
            'track': track,
            'paper_id': paper_id
        }
    
    def _determine_track_from_context(self, link_element) -> str:
        """Determine track from surrounding HTML context"""
        parent = link_element.find_parent(['li', 'div', 'section'])
        if parent:
            class_attr = parent.get('class', [])
            if 'datasets_and_benchmarks_track' in class_attr:
                return "Datasets and Benchmarks Track"
            elif 'conference' in class_attr:
                return "Main Conference Track"
        
        return "Main Conference Track"  # Default
    
    def _extract_paper_id_from_url(self, url: str) -> str:
        """Extract paper ID from URL"""
        match = re.search(r'/hash/([a-f0-9]+)-', url)
        return match.group(1) if match else ""
    
    async def extract_paper_details(self, paper_info: Dict[str, str]) -> Optional[Paper]:
        """Extract detailed information from a paper's detail page"""
        try:
            html = await self.fetch_page(paper_info['detail_url'])
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup) or paper_info.get('title', '')
            
            # Extract authors
            authors = self._extract_authors(soup)
            
            # Extract abstract
            abstract = self._extract_abstract(soup)
            
            # Extract links
            paper_link = self._extract_paper_pdf_link(soup)
            bibtex_link = self._extract_bibtex_link(soup)
            supp_link = self._extract_supplemental_link(soup)
            
            # Create Paper object
            paper = Paper(
                title=title,
                authors=authors,
                abstract=abstract,
                track=paper_info.get('track', 'Main Conference Track'),
                paper_link=paper_link,
                bibtex_link=bibtex_link,
                supp_link=supp_link,
                year=self.year,
                paper_id=paper_info.get('paper_id', ''),
                source_url=paper_info['detail_url']
            )
            
            return paper
            
        except Exception as e:
            logger.error(f"Error extracting details for {paper_info.get('title', 'Unknown')}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract paper title using multiple strategies"""
        # Try h4 first (primary selector based on analysis)
        title_elem = soup.find('h4')
        if title_elem:
            title = title_elem.get_text(strip=True)
            if len(title) > 5:  # Basic validation
                return title
        
        # Try other heading levels
        for tag in ['h1', 'h2', 'h3']:
            title_elem = soup.find(tag)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 5:
                    return title
        
        # Try meta tag
        meta_title = soup.find('meta', attrs={'name': 'citation_title'})
        if meta_title:
            return meta_title.get('content', '').strip()
        
        return ""
    
    def _extract_authors(self, soup: BeautifulSoup) -> List[str]:
        """Extract author names using multiple strategies"""
        authors = []
        
        # Try meta tags first (most reliable)
        meta_authors = soup.find_all('meta', attrs={'name': 'citation_author'})
        if meta_authors:
            authors = [meta.get('content', '').strip() for meta in meta_authors if meta.get('content')]
            if authors:
                return authors
        
        # Try italic text in paragraph (primary HTML selector)
        author_elem = soup.select_one('p > i')
        if author_elem:
            author_text = author_elem.get_text(strip=True)
            # Split by comma and clean up
            authors = [name.strip() for name in author_text.split(',') if name.strip()]
            if authors:
                return authors
        
        return []
    
    def _extract_abstract(self, soup: BeautifulSoup) -> str:
        """Extract paper abstract using multiple strategies"""
        # Look for Abstract header and following paragraph
        abstract_headers = soup.find_all(['h4', 'h3'], string=re.compile(r'Abstract', re.IGNORECASE))
        for header in abstract_headers:
            next_elem = header.find_next_sibling(['p', 'div'])
            if next_elem:
                # Check for nested paragraph
                nested_p = next_elem.find('p')
                if nested_p:
                    abstract = nested_p.get_text(strip=True)
                else:
                    abstract = next_elem.get_text(strip=True)
                
                if len(abstract) > 50:  # Basic validation
                    return abstract
        
        # Try meta tag fallback
        meta_abstract = soup.find('meta', attrs={'name': 'citation_abstract'})
        if meta_abstract:
            return meta_abstract.get('content', '').strip()
        
        return ""
    
    def _extract_paper_pdf_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract PDF download link"""
        # Look for PDF link by pattern
        pdf_links = soup.find_all('a', href=re.compile(r'-Paper-Conference\.pdf'))
        if pdf_links:
            return urljoin(self.base_url, pdf_links[0].get('href'))
        
        # Look for button with "Paper" text
        paper_buttons = soup.find_all('a', string=re.compile(r'Paper', re.IGNORECASE))
        for button in paper_buttons:
            href = button.get('href')
            if href and '.pdf' in href:
                return urljoin(self.base_url, href)
        
        # Try meta tag
        meta_pdf = soup.find('meta', attrs={'name': 'citation_pdf_url'})
        if meta_pdf:
            return meta_pdf.get('content', '').strip()
        
        return None
    
    def _extract_bibtex_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract BibTeX link"""
        # Look for BibTeX link by pattern
        bib_links = soup.find_all('a', href=re.compile(r'-bib\.txt'))
        if bib_links:
            return urljoin(self.base_url, bib_links[0].get('href'))
        
        # Look for button with "Bibtex" text
        bib_buttons = soup.find_all('a', string=re.compile(r'Bibtex', re.IGNORECASE))
        if bib_buttons:
            href = bib_buttons[0].get('href')
            if href:
                return urljoin(self.base_url, href)
        
        return None
    
    def _extract_supplemental_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract supplemental material link"""
        # Look for supplemental link by pattern
        supp_links = soup.find_all('a', href=re.compile(r'-Supplemental-'))
        if supp_links:
            return urljoin(self.base_url, supp_links[0].get('href'))
        
        # Look for button with "Supplement" text
        supp_buttons = soup.find_all('a', string=re.compile(r'Supplement', re.IGNORECASE))
        if supp_buttons:
            href = supp_buttons[0].get('href')
            if href:
                return urljoin(self.base_url, href)
        
        return None
    
    async def crawl_all_papers(self) -> List[Paper]:
        """Main method to crawl all papers"""
        logger.info(f"Starting NeurIPS {self.year} paper crawling...")
        
        # Step 1: Get paper listings from proceedings page
        proceedings_url = self.get_proceedings_url()
        proceedings_html = await self.fetch_page(proceedings_url)
        paper_listings = self.extract_paper_listings(proceedings_html)
        
        if not paper_listings:
            logger.warning(f"No papers found for year {self.year}")
            return []
        
        logger.info(f"Found {len(paper_listings)} papers to process")
        
        # Step 2: Extract detailed information for each paper
        papers = []
        for i, paper_info in enumerate(paper_listings):
            logger.info(f"Processing paper {i+1}/{len(paper_listings)}: {paper_info.get('title', 'Unknown')}")
            
            paper = await self.extract_paper_details(paper_info)
            if paper:
                papers.append(paper)
            
            # Rate limiting
            if i < len(paper_listings) - 1:
                await asyncio.sleep(self.delay)
        
        self.papers = papers
        logger.info(f"Successfully crawled {len(papers)} papers")
        return papers
    
    def save_results(self, filename: str = None, format: str = 'json'):
        """Save results to file"""
        if not self.papers:
            logger.warning("No papers to save")
            return
        
        if not filename:
            filename = f"neurips_{self.year}_papers.{format}"
        
        if format.lower() == 'json':
            with open(filename, 'w', encoding='utf-8') as f:
                papers_dict = [asdict(paper) for paper in self.papers]
                json.dump(papers_dict, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'csv':
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if self.papers:
                    fieldnames = asdict(self.papers[0]).keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for paper in self.papers:
                        paper_dict = asdict(paper)
                        # Convert list to comma-separated string for CSV
                        if isinstance(paper_dict.get('authors'), list):
                            paper_dict['authors'] = ', '.join(paper_dict['authors'])
                        writer.writerow(paper_dict)
        
        logger.info(f"Saved {len(self.papers)} papers to {filename}")
    
    def print_summary(self):
        """Print crawling summary"""
        if not self.papers:
            print("No papers found")
            return
        
        print(f"\n=== NeurIPS {self.year} Crawling Summary ===")
        print(f"Total papers: {len(self.papers)}")
        
        # Track distribution
        track_counts = {}
        for paper in self.papers:
            track = paper.track
            track_counts[track] = track_counts.get(track, 0) + 1
        
        print("\nTrack distribution:")
        for track, count in track_counts.items():
            print(f"  {track}: {count}")
        
        # Data completeness
        complete_abstracts = sum(1 for p in self.papers if len(p.abstract) > 50)
        complete_authors = sum(1 for p in self.papers if p.authors)
        pdf_links = sum(1 for p in self.papers if p.paper_link)
        
        print(f"\nData completeness:")
        print(f"  Papers with abstracts: {complete_abstracts}/{len(self.papers)}")
        print(f"  Papers with authors: {complete_authors}/{len(self.papers)}")
        print(f"  Papers with PDF links: {pdf_links}/{len(self.papers)}")

async def main():
    """Main execution function"""
    # Configure for NeurIPS 2024 (adaptable to any year)
    year = 2024
    delay = 1.5  # Be respectful with rate limiting
    
    async with NeurIPSCrawler(year=year, delay=delay) as crawler:
        try:
            # Crawl all papers
            papers = await crawler.crawl_all_papers()
            
            # Save results in multiple formats
            crawler.save_results(format='json')
            crawler.save_results(format='csv')
            
            # Print summary
            crawler.print_summary()
            
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(main())
```
