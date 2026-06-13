# This file is responsible for copyright check request schema define karne ke liye.
# Yahan incoming lyrics payload ki validation shape manage ki jati hai.

from pydantic import BaseModel, constr


class CopyrightCheckRequest(BaseModel):
    lyrics: constr(strip_whitespace=True, min_length=1)
