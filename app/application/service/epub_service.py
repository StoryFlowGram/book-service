import asyncio
import html
import re
from pathlib import PurePosixPath
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup
from ebooklib import ITEM_COVER, ITEM_DOCUMENT, ITEM_IMAGE, epub


ALLOWED_CHAPTER_TAGS = ("h1", "h2", "h3", "p")
MIN_CHAPTER_TEXT_LENGTH = 100
_COVER_KEYWORDS = ("cover", "front", "jacket", "titlepage", "title-page")
_NON_COVER_KEYWORDS = ("logo", "icon", "sprite", "thumb")
_EXPLICIT_COVER_IDS = ("cover", "cover-image", "coverimage", "cover_img", "jacket")


class EpubService:
    def __init__(self):
        self.loop = asyncio.get_running_loop()

    async def read_metadata(self, epub_path: str) -> dict:
        book = await self.loop.run_in_executor(None, epub.read_epub, epub_path)

        title = (
            book.get_metadata("DC", "title")[0][0]
            if book.get_metadata("DC", "title")
            else "Unknown Title"
        )
        author = (
            book.get_metadata("DC", "creator")[0][0]
            if book.get_metadata("DC", "creator")
            else "Unknown Author"
        )
        description = (
            book.get_metadata("DC", "description")[0][0]
            if book.get_metadata("DC", "description")
            else "No description"
        )

        cover_content = None
        cover_content_type = None
        cover_file_name = None
        cover_item = self._find_cover_item(book)

        if cover_item:
            cover_content = await self.loop.run_in_executor(None, cover_item.get_content)
            cover_content_type = getattr(cover_item, "media_type", None)
            cover_file_name = getattr(cover_item, "file_name", None)

        return {
            "title": title,
            "author": author,
            "description": description,
            "cover_content": cover_content,
            "cover_content_type": cover_content_type,
            "cover_file_name": cover_file_name,
            "book_obj": book,
        }

    def _find_cover_item(self, book):
        finders = (
            self._find_cover_by_explicit_item_id,
            self._find_cover_from_meta_reference,
            self._find_cover_by_manifest_properties,
            self._find_cover_from_guide_reference,
            self._find_cover_from_cover_document,
            self._find_cover_by_scored_images,
        )

        for finder in finders:
            item = finder(book)
            if item is not None:
                return item

        return None

    def _find_cover_by_explicit_item_id(self, book):
        for item_id in _EXPLICIT_COVER_IDS:
            item = book.get_item_with_id(item_id)
            if item and self._is_image_like_item(item):
                return item
        return None

    def _find_cover_from_meta_reference(self, book):
        opf_meta = book.get_metadata("OPF", "meta") or []
        for value, attrs in opf_meta:
            if not isinstance(attrs, dict):
                continue

            name = (attrs.get("name") or "").lower()
            content = (attrs.get("content") or "").strip()
            if name == "cover" and content:
                item = book.get_item_with_id(content)
                if item and self._is_image_like_item(item):
                    return item

            # EPUB 3 may use property="cover-image" with itemref in "content" for some generators.
            prop = (attrs.get("property") or "").lower()
            if prop == "cover-image" and content:
                item = book.get_item_with_id(content)
                if item and self._is_image_like_item(item):
                    return item

            if isinstance(value, str):
                raw_value = value.strip()
                if name == "cover" and raw_value:
                    item = book.get_item_with_id(raw_value)
                    if item and self._is_image_like_item(item):
                        return item

        return None

    def _find_cover_by_manifest_properties(self, book):
        for item in self._iter_image_like_items(book):
            raw_properties = getattr(item, "properties", None)
            properties: set[str] = set()

            if isinstance(raw_properties, str):
                properties = {prop.strip().lower() for prop in raw_properties.split() if prop.strip()}
            elif raw_properties:
                properties = {str(prop).strip().lower() for prop in raw_properties if str(prop).strip()}

            if "cover-image" in properties or "cover" in properties:
                return item

        return None

    def _find_cover_from_guide_reference(self, book):
        guide = getattr(book, "guide", None) or []
        for guide_entry in guide:
            entry_type = ""
            href = ""

            if isinstance(guide_entry, dict):
                entry_type = str(guide_entry.get("type") or "")
                href = str(guide_entry.get("href") or "")
            elif isinstance(guide_entry, (tuple, list)):
                if len(guide_entry) >= 1:
                    entry_type = str(guide_entry[0] or "")
                if len(guide_entry) >= 3:
                    href = str(guide_entry[2] or "")

            if "cover" not in entry_type.lower() or not href:
                continue

            item = self._get_item_by_href(book, href)
            if item is None:
                continue

            if self._is_image_like_item(item):
                return item
            if item.get_type() == ITEM_DOCUMENT:
                doc_image = self._find_first_image_in_document(book, item)
                if doc_image is not None:
                    return doc_image

        return None

    def _find_cover_from_cover_document(self, book):
        document_items = list(self._iter_document_items(book))
        if not document_items:
            return None

        scored_documents: list[tuple[int, object]] = []
        for index, item in enumerate(document_items):
            descriptor = (
                f"{(getattr(item, 'file_name', '') or '').lower()} "
                f"{(self._extract_item_id(item) or '').lower()}"
            )
            score = 0
            if index == 0:
                score += 20
            if any(keyword in descriptor for keyword in _COVER_KEYWORDS):
                score += 100
            scored_documents.append((score, item))

        scored_documents.sort(key=lambda pair: pair[0], reverse=True)
        for score, document_item in scored_documents[:5]:
            if score <= 0:
                continue
            image_item = self._find_first_image_in_document(book, document_item)
            if image_item is not None:
                return image_item

        return None

    def _find_first_image_in_document(self, book, document_item):
        try:
            content = document_item.get_content()
            source_html = content.decode("utf-8", errors="ignore")
        except Exception:
            return None

        soup = BeautifulSoup(source_html, "html.parser")
        href_candidates: list[str] = []

        for tag in soup.find_all("img"):
            src = (tag.get("src") or "").strip()
            if src:
                href_candidates.append(src)

        for tag in soup.find_all("image"):
            href = (tag.get("href") or tag.get("xlink:href") or "").strip()
            if href:
                href_candidates.append(href)

        base_file_name = getattr(document_item, "file_name", "") or ""
        for raw_href in href_candidates:
            resolved_href = self._resolve_relative_href(base_file_name, raw_href)
            if not resolved_href:
                continue
            image_item = self._find_image_item_by_href(book, resolved_href)
            if image_item is not None:
                return image_item

        return None

    def _find_cover_by_scored_images(self, book):
        images = list(self._iter_image_like_items(book))
        if not images:
            return None

        scored = [(self._score_image_candidate(item), item) for item in images]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[0][1]

    def _score_image_candidate(self, item) -> tuple[int, int]:
        descriptor = (
            f"{(getattr(item, 'file_name', '') or '').lower()} "
            f"{(self._extract_item_id(item) or '').lower()}"
        )
        score = 0
        if "cover" in descriptor:
            score += 200
        if "front" in descriptor:
            score += 80
        if "jacket" in descriptor:
            score += 80
        if "titlepage" in descriptor or "title-page" in descriptor:
            score += 70

        if any(keyword in descriptor for keyword in _NON_COVER_KEYWORDS):
            score -= 40

        media_type = (getattr(item, "media_type", "") or "").lower()
        if media_type.startswith("image/"):
            score += 10

        size = 0
        try:
            size = len(item.get_content() or b"")
        except Exception:
            size = 0

        return (score, size)

    def _get_item_by_href(self, book, href: str):
        clean_href = (href or "").split("#", 1)[0].strip()
        if not clean_href:
            return None

        normalized_clean_href = self._normalize_path(clean_href)
        if hasattr(book, "get_item_with_href"):
            item = book.get_item_with_href(clean_href) or book.get_item_with_href(normalized_clean_href)
            if item is not None:
                return item

        get_items = getattr(book, "get_items", None)
        if not callable(get_items):
            return None

        for item in get_items():
            file_name = getattr(item, "file_name", "")
            if self._normalize_path(file_name) == normalized_clean_href:
                return item

        return None

    def _find_image_item_by_href(self, book, href: str):
        normalized_href = self._normalize_path(href)
        if not normalized_href:
            return None

        # Fast path when get_item_with_href is available.
        if hasattr(book, "get_item_with_href"):
            item = book.get_item_with_href(href) or book.get_item_with_href(normalized_href)
            if item is not None and self._is_image_like_item(item):
                return item

        target_name = PurePosixPath(normalized_href).name
        basename_match = None
        for item in self._iter_image_like_items(book):
            item_path = self._normalize_path(getattr(item, "file_name", ""))
            if item_path == normalized_href:
                return item
            if PurePosixPath(item_path).name == target_name and basename_match is None:
                basename_match = item

        return basename_match

    def _resolve_relative_href(self, base_file_name: str, href: str) -> Optional[str]:
        clean_href = (href or "").split("#", 1)[0].split("?", 1)[0].strip()
        if not clean_href:
            return None
        if clean_href.startswith(("http://", "https://", "data:")):
            return None

        clean_href = clean_href.replace("\\", "/")
        if clean_href.startswith("/"):
            return clean_href.lstrip("/")

        base_path = PurePosixPath((base_file_name or "").replace("\\", "/"))
        base_dir = base_path.parent if base_path.name else base_path
        return (base_dir / clean_href).as_posix()

    def _normalize_path(self, value: str) -> str:
        if not value:
            return ""
        return PurePosixPath(value.replace("\\", "/").lstrip("/")).as_posix().lower()

    def _extract_item_id(self, item) -> str:
        if hasattr(item, "get_id"):
            return item.get_id() or ""
        return getattr(item, "id", "") or ""

    def _is_image_like_item(self, item) -> bool:
        if item is None:
            return False

        item_type = item.get_type()
        if item_type in {ITEM_IMAGE, ITEM_COVER}:
            return True

        media_type = (getattr(item, "media_type", "") or "").lower()
        return media_type.startswith("image/")

    def _iter_image_like_items(self, book) -> Iterable:
        get_items = getattr(book, "get_items", None)
        if callable(get_items):
            for item in get_items():
                if self._is_image_like_item(item):
                    yield item
            return

        for item in book.get_items_of_type(ITEM_IMAGE):
            yield item
        for item in book.get_items_of_type(ITEM_COVER):
            yield item

    async def extract_chapters(self, book_obj) -> List[dict]:
        chapters: List[dict] = []
        order_number = 1

        for item in self._iter_document_items(book_obj):
            raw_html = await self.loop.run_in_executor(None, item.get_content)
            cleaned_html = self._build_clean_chapter_html(raw_html.decode("utf-8", errors="ignore"))
            plain_text = self._html_to_plain_text(cleaned_html)

            if len(plain_text) < MIN_CHAPTER_TEXT_LENGTH:
                continue

            chapter_title = self._extract_chapter_title(cleaned_html, order_number)
            chapters.append(
                {
                    "title": chapter_title,
                    "content_html": cleaned_html,
                    "word_count": len(plain_text.split()),
                    "order_number": order_number,
                }
            )
            order_number += 1

        return chapters

    def _iter_document_items(self, book_obj) -> Iterable:
        yielded_ids: set[str] = set()

        for _, item_id in getattr(book_obj, "spine", []):
            item = book_obj.get_item_with_id(item_id)
            if item and item.get_type() == ITEM_DOCUMENT:
                item_key = self._extract_item_id(item) or self._normalize_path(
                    getattr(item, "file_name", "") or ""
                )
                yielded_ids.add(item_key)
                yield item

        for item in book_obj.get_items_of_type(ITEM_DOCUMENT):
            item_key = self._extract_item_id(item) or self._normalize_path(
                getattr(item, "file_name", "") or ""
            )
            if item_key not in yielded_ids:
                yield item

    def _build_clean_chapter_html(self, source_html: str) -> str:
        soup = BeautifulSoup(source_html, "html.parser")
        body = soup.body or soup

        for removable in body.find_all(["script", "style", "noscript"]):
            removable.decompose()

        blocks: list[str] = []
        for tag in body.find_all(ALLOWED_CHAPTER_TAGS):
            normalized_text = self._normalize_text(tag.get_text(" ", strip=True))
            if not normalized_text:
                continue

            tag_name = tag.name.lower()
            blocks.append(f"<{tag_name}>{html.escape(normalized_text)}</{tag_name}>")

        return "\n".join(blocks)

    def _extract_chapter_title(self, chapter_html: str, order_number: int) -> str:
        soup = BeautifulSoup(chapter_html, "html.parser")
        heading = soup.find(["h1", "h2", "h3"])
        if heading:
            title = self._normalize_text(heading.get_text(" ", strip=True))
            if title:
                return title
        return f"Chapter {order_number}"

    def _html_to_plain_text(self, chapter_html: str) -> str:
        soup = BeautifulSoup(chapter_html, "html.parser")
        return self._normalize_text(soup.get_text(" ", strip=True))

    def _normalize_text(self, text: str) -> str:
        normalized = (
            text.replace("\u00ad", "")
            .replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\ufeff", "")
        )
        normalized = re.sub(r"[\r\n\t]+", " ", normalized)
        normalized = re.sub(r"(\w)[\u2010\u2011-]\s+(\w)", r"\1\2", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()
