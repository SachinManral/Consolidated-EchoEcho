# This file is responsible for copyright check response schema define karne ke liye.
# Yahan API output fields aur advisory result structure manage kiya jata hai.

from pydantic import BaseModel


class CopyrightCheckResponse(BaseModel):
    safe: bool
    risk: str
    confidence: float
    copyright_status: str
    song_title: str = ""
    artist: str = ""
    recommendation: str
    details: str
