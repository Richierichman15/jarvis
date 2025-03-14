#!/usr/bin/env python3
"""
Test script for the enhanced web search capabilities.
This script tests the web search tool with different types of queries.
"""
import os
import sys
import logging
from typing import List, Dict, Any
import argparse

from jarvis.tools.web_search import WebSearch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_regular_search(web_search: WebSearch, query: str):
    """Test a regular web search.
    
    Args:
        web_search: WebSearch instance
        query: Search query
    """
    logger.info("=" * 50)
    logger.info(f"Testing regular search with query: {query}")
    logger.info("=" * 50)
    
    # Detect the best search type
    search_type = web_search.detect_search_type(query)
    logger.info(f"Detected search type: {search_type}")
    
    # Perform the search
    results = web_search.search(query, search_type)
    
    # Summarize the results
    summary = web_search.summarize_results(results)
    
    print("\n" + "=" * 80)
    print(f"REGULAR SEARCH RESULTS FOR: {query}")
    print("=" * 80)
    print(summary)
    print("=" * 80 + "\n")


def test_multi_search(web_search: WebSearch, query: str):
    """Test a multi-type search.
    
    Args:
        web_search: WebSearch instance
        query: Search query
    """
    logger.info("=" * 50)
    logger.info(f"Testing multi-search with query: {query}")
    logger.info("=" * 50)
    
    # Perform multi-search
    results = web_search.multi_search(query)
    
    # Log the result types
    for result_type, type_results in results.items():
        logger.info(f"Found {len(type_results)} {result_type} results")
    
    # Summarize the results
    summary = web_search.summarize_results(results)
    
    print("\n" + "=" * 80)
    print(f"MULTI-SEARCH RESULTS FOR: {query}")
    print("=" * 80)
    print(summary)
    print("=" * 80 + "\n")


def test_news_search(web_search: WebSearch, query: str):
    """Test a news search.
    
    Args:
        web_search: WebSearch instance
        query: Search query
    """
    logger.info("=" * 50)
    logger.info(f"Testing news search with query: {query}")
    logger.info("=" * 50)
    
    # Perform the search
    results = web_search.search(query, "news")
    
    # Summarize the results
    summary = web_search.summarize_results(results)
    
    print("\n" + "=" * 80)
    print(f"NEWS SEARCH RESULTS FOR: {query}")
    print("=" * 80)
    print(summary)
    print("=" * 80 + "\n")


def test_image_search(web_search: WebSearch, query: str):
    """Test an image search.
    
    Args:
        web_search: WebSearch instance
        query: Search query
    """
    logger.info("=" * 50)
    logger.info(f"Testing image search with query: {query}")
    logger.info("=" * 50)
    
    # Perform the search
    results = web_search.search(query, "images")
    
    # Summarize the results
    summary = web_search.summarize_results(results)
    
    print("\n" + "=" * 80)
    print(f"IMAGE SEARCH RESULTS FOR: {query}")
    print("=" * 80)
    print(summary)
    print("=" * 80 + "\n")


def main():
    """Run the test script."""
    parser = argparse.ArgumentParser(description="Test the enhanced web search capabilities")
    parser.add_argument("--query", "-q", help="Search query to test")
    parser.add_argument("--all", "-a", action="store_true", help="Run all test types")
    parser.add_argument("--regular", "-r", action="store_true", help="Test regular search")
    parser.add_argument("--multi", "-m", action="store_true", help="Test multi-search")
    parser.add_argument("--news", "-n", action="store_true", help="Test news search")
    parser.add_argument("--images", "-i", action="store_true", help="Test image search")
    
    args = parser.parse_args()
    
    # Create web search instance
    web_search = WebSearch(max_results=5, timeout=10, retries=1)
    
    # Use default query if none provided
    query = args.query or "latest developments in artificial intelligence"
    
    # If no test types specified, run all tests
    if not (args.regular or args.multi or args.news or args.images):
        args.all = True
        
    if args.all or args.regular:
        test_regular_search(web_search, query)
        
    if args.all or args.multi:
        test_multi_search(web_search, query)
        
    if args.all or args.news:
        news_query = args.query or "latest news in technology"
        test_news_search(web_search, news_query)
        
    if args.all or args.images:
        image_query = args.query or "images of the Grand Canyon"
        test_image_search(web_search, image_query)
        
    return 0


if __name__ == "__main__":
    sys.exit(main()) 