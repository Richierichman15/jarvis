# Enhanced Web Search for Jarvis

This document explains the enhanced web search capabilities implemented for the Jarvis AI Assistant.

## Features

The enhanced web search tool adds the following improvements:

1. **Multiple Search Types**
   - Text search (general web results)
   - News search (recent articles and updates)
   - Image search (with descriptions)

2. **Intelligent Search Type Detection**
   - Automatically detects the most appropriate search type based on query content
   - Uses pattern matching to identify news or image-related queries

3. **Multi-Search Capability**
   - Can perform multiple search types for a single query
   - Combines results from different search types for comprehensive information
   - Prioritizes results based on query context

4. **Result Filtering and Quality Improvements**
   - Removes duplicate or highly similar results
   - Filters out low-quality or irrelevant information
   - For news results, prioritizes recent articles

5. **Improved Error Handling**
   - Automatic retries for failed searches
   - Graceful fallback to alternative search types
   - Detailed logging for debugging

6. **Rate Limiting Respect**
   - Enforces minimum intervals between searches
   - Prevents API rate limit errors

7. **Better Result Formatting**
   - Enhanced formatting for different result types
   - Special handling for news articles (includes publication date and source)
   - Special handling for image results

## Usage

### Basic Usage

```python
from jarvis.tools.web_search import WebSearch

# Create a web search instance
web_search = WebSearch()

# Perform a search with automatic type detection
query = "latest AI developments"
search_type = web_search.detect_search_type(query)
results = web_search.search(query, search_type)

# Get formatted results
summary = web_search.summarize_results(results)
print(summary)
```

### Multi-Search Example

```python
# Perform a multi-search (combines different search types)
query = "recent news about SpaceX launches"
results = web_search.multi_search(query)
summary = web_search.summarize_results(results)
print(summary)
```

### Specific Search Types

```python
# Perform a news search
news_results = web_search.search("climate change initiatives", "news")

# Perform an image search
image_results = web_search.search("images of Mars rover", "images")
```

## Testing

A test script is provided to verify the enhanced web search capabilities:

```bash
# Run all test types
./test_web_search.py

# Run with a specific query
./test_web_search.py --query "artificial intelligence trends"

# Run only specific test types
./test_web_search.py --regular  # Regular search
./test_web_search.py --multi    # Multi-search
./test_web_search.py --news     # News search
./test_web_search.py --images   # Image search
```

## Integration with Jarvis

The enhanced web search capabilities are fully integrated with the Jarvis assistant:

1. The `tool_manager.py` detects when web searches are needed and automatically selects the most appropriate search type.

2. The `jarvis.py` module uses specialized prompts based on the type of search results to generate more relevant and helpful responses.

3. All web search responses include source attribution to ensure credibility.

## Customization

You can customize the web search tool by modifying these parameters:

- `max_results`: Maximum number of search results to return (default: 5)
- `timeout`: Timeout in seconds for search requests (default: 10)
- `retries`: Number of retry attempts if a search fails (default: 2)

Example:
```python
# Create a customized web search instance
web_search = WebSearch(max_results=10, timeout=15, retries=3)
```

## Implementation Details

The enhanced web search tool is implemented in the following files:

- `jarvis/tools/web_search.py`: Core implementation of the web search tool
- `jarvis/tools/tool_manager.py`: Integration with Jarvis's tool system
- `jarvis/jarvis.py`: Integration with response generation
- `test_web_search.py`: Test script for the web search capabilities 