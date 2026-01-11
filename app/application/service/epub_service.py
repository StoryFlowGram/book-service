import asyncio
from typing import List
from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT, ITEM_IMAGE

class EpubService:


    def __init__(self):
        self.loop = asyncio.get_running_loop()

    async def read_metadata(self, epub_path: str) -> dict:
        book = await self.loop.run_in_executor(None, epub.read_epub, epub_path)
        
        title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'Unknown Title'
        author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else 'Unknown Author'
        description = book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else 'No description'
        
        cover_content = None
        cover_item = book.get_item_with_id('cover') or next((item for item in book.get_items_of_type(ITEM_IMAGE) if 'cover' in item.file_name.lower()), None)
        
        if cover_item:
            cover_content = await self.loop.run_in_executor(None, cover_item.get_content)

        return {
            "title": title,
            "author": author,
            "description": description,
            "cover_content": cover_content,
            "book_obj": book 
        }

    async def extract_chapters(self, book_obj) -> List[dict]:
        chapters = []
        order_number = 1
        
        items = book_obj.get_items_of_type(ITEM_DOCUMENT)
        
        for item in items:
            if not item.is_chapter():
                continue

            html_content = await self.loop.run_in_executor(None, item.get_content)
            soup = BeautifulSoup(html_content.decode('utf-8', errors='ignore'), 'html.parser')
            text = soup.get_text(separator='\n', strip=True)

            if len(text) < 100:
                continue

            title_tag = soup.find(['h1', 'h2', 'h3'])
            chapter_title = title_tag.text.strip() if title_tag else f"Chapter {order_number}"
            
            chapters.append({
                "title": chapter_title,
                "text": text,
                "word_count": len(text.split()),
                "order_number": order_number
            })
            order_number += 1
            
        return chapters