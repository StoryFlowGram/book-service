import asyncio
import unittest
from pathlib import PurePosixPath

from ebooklib import ITEM_DOCUMENT, ITEM_IMAGE

from app.application.service.epub_service import EpubService


async def _create_service() -> EpubService:
    return EpubService()


def _make_service() -> EpubService:
    return asyncio.run(_create_service())


class FakeEpubItem:
    def __init__(
        self,
        item_id: str,
        file_name: str,
        item_type: int,
        content: bytes,
        media_type: str | None = None,
        properties=None,
    ):
        self._item_id = item_id
        self.file_name = file_name
        self._item_type = item_type
        self._content = content
        self.media_type = media_type
        self.properties = properties

    def get_id(self):
        return self._item_id

    def get_type(self):
        return self._item_type

    def get_content(self):
        return self._content


class FakeEpubBook:
    def __init__(self, items, metadata=None, spine=None, guide=None):
        self._items = list(items)
        self._items_by_id = {item.get_id(): item for item in self._items}
        self._metadata = metadata or {}
        self.spine = spine or []
        self.guide = guide or []

    def get_metadata(self, namespace: str, key: str):
        return self._metadata.get((namespace, key), [])

    def get_item_with_id(self, item_id: str):
        return self._items_by_id.get(item_id)

    def get_item_with_href(self, href: str):
        normalized = PurePosixPath(href.replace("\\", "/").lstrip("/")).as_posix().lower()
        for item in self._items:
            item_path = PurePosixPath(item.file_name.replace("\\", "/").lstrip("/")).as_posix().lower()
            if item_path == normalized:
                return item
        return None

    def get_items_of_type(self, item_type: int):
        for item in self._items:
            if item.get_type() == item_type:
                yield item

    def get_items(self):
        return iter(self._items)


class EpubServiceCleanHtmlTestCase(unittest.TestCase):
    def test_build_clean_chapter_html_keeps_only_semantic_tags(self):
        service = _make_service()
        source_html = """
        <html>
          <body>
            <h1 class=\"title\" style=\"color:red\" id=\"chapter-title\">Chapter 1</h1>
            <p class=\"a\" style=\"font-size: 12px;\">First line
            second line</p>
            <div class=\"wrapper\"><p id=\"x\">Another paragraph</p></div>
            <script>alert(\"x\")</script>
          </body>
        </html>
        """

        cleaned_html = service._build_clean_chapter_html(source_html)

        self.assertIn('<h1>Chapter 1</h1>', cleaned_html)
        self.assertIn('<p>First line second line</p>', cleaned_html)
        self.assertIn('<p>Another paragraph</p>', cleaned_html)
        self.assertNotIn('class=', cleaned_html)
        self.assertNotIn('style=', cleaned_html)
        self.assertNotIn('id=', cleaned_html)
        self.assertNotIn('<script>', cleaned_html)
        self.assertNotIn('<div', cleaned_html)

    def test_normalize_text_removes_technical_line_break_hyphenation(self):
        service = _make_service()
        raw = "inter-\nrupted\r\nword\u00ad and\n\n spaced"
        normalized = service._normalize_text(raw)
        self.assertEqual(normalized, "interrupted word and spaced")

    def test_find_cover_item_from_opf_meta_reference(self):
        service = _make_service()

        logo = FakeEpubItem(
            item_id="img_logo",
            file_name="OPS/Images/logo.png",
            item_type=ITEM_IMAGE,
            content=b"logo",
            media_type="image/png",
        )
        cover = FakeEpubItem(
            item_id="img_cover",
            file_name="OPS/Images/cover.jpg",
            item_type=ITEM_IMAGE,
            content=b"cover",
            media_type="image/jpeg",
        )
        book = FakeEpubBook(
            items=[logo, cover],
            metadata={
                ("OPF", "meta"): [
                    (None, {"name": "cover", "content": "img_cover"}),
                ]
            },
        )

        selected = service._find_cover_item(book)
        self.assertIs(selected, cover)

    def test_find_cover_item_from_titlepage_img_when_no_cover_meta(self):
        service = _make_service()

        titlepage = FakeEpubItem(
            item_id="titlepage",
            file_name="OPS/Text/titlepage.xhtml",
            item_type=ITEM_DOCUMENT,
            content=b'<html><body><img src="../Images/NineteenEightyFour.jpg" /></body></html>',
            media_type="application/xhtml+xml",
        )
        cover = FakeEpubItem(
            item_id="img_1984",
            file_name="OPS/Images/NineteenEightyFour.jpg",
            item_type=ITEM_IMAGE,
            content=b"cover-bytes",
            media_type="image/jpeg",
        )
        another_image = FakeEpubItem(
            item_id="img_logo",
            file_name="OPS/Images/logo.png",
            item_type=ITEM_IMAGE,
            content=b"logo",
            media_type="image/png",
        )
        book = FakeEpubBook(
            items=[titlepage, cover, another_image],
            spine=[("yes", "titlepage")],
        )

        selected = service._find_cover_item(book)
        self.assertIs(selected, cover)


if __name__ == "__main__":
    unittest.main()
