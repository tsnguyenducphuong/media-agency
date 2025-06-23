from pydantic import BaseModel
from typing import Optional

class UserSelection(BaseModel):
    media_folder: str
    # image_list: list[str]
    brand_background_image: Optional[str] = None