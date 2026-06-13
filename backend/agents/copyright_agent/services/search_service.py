# This file provides the SerpApi-backed search abstraction used by agents.

from __future__ import annotations

from typing import Any

from ..config import config


class SearchService:
    def _run_search(self, query: str, search_type: str) -> dict[str, Any]:
        if not config.serpapi_api_key:
            raise RuntimeError("SerpApi API key is not configured.")

        params: dict[str, Any] = {
            "engine": "google",
            "q": query,
            "api_key": config.serpapi_api_key,
            "num": config.serpapi_result_count,
        }
        if search_type == "news":
            params["tbm"] = "nws"
        elif search_type == "images":
            params["tbm"] = "isch"

        try:
            from serpapi import GoogleSearch
        except ImportError as exc:
            raise RuntimeError("google-search-results is not installed.") from exc

        try:
            data = GoogleSearch(params).get_dict()
        except Exception as exc:
            message = str(exc)
            if "rate" in message.lower() or "quota" in message.lower():
                raise RuntimeError(f"SerpApi rate limit reached: {message}") from exc
            raise RuntimeError(f"SerpApi search failed: {message}") from exc

        error = data.get("error")
        if error:
            message = str(error)
            if "rate" in message.lower() or "quota" in message.lower():
                raise RuntimeError(f"SerpApi rate limit reached: {message}")
            raise RuntimeError(f"SerpApi search failed: {message}")
        return data

    def search(self, query: str) -> list[dict]:
        data = self._run_search(query, "web")
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
            }
            for item in data.get("organic_results", [])
        ]

    def search_news(self, query: str) -> list[dict]:
        data = self._run_search(query, "news")
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url": item.get("link", ""),
            }
            for item in data.get("news_results", [])
        ]

    def search_images(self, query: str) -> list[dict]:
        data = self._run_search(query, "images")
        return [
            {
                "title": item.get("title", ""),
                "snippet": item.get("source", ""),
                "url": item.get("link") or item.get("original", ""),
                "image_url": item.get("original") or item.get("thumbnail", ""),
            }
            for item in data.get("images_results", [])
        ]
