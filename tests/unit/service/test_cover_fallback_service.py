import unittest

from app.application.service.cover_fallback_service import build_fallback_cover_svg


class CoverFallbackServiceTestCase(unittest.TestCase):
    def test_build_fallback_cover_svg_contains_core_fields(self):
        payload = build_fallback_cover_svg("Nineteen Eighty-Four", "George Orwell")
        rendered = payload.decode("utf-8")

        self.assertIn("<svg", rendered)
        self.assertIn("Nineteen", rendered)
        self.assertIn("George Orwell", rendered)
        self.assertIn("Book", rendered)

    def test_build_fallback_cover_svg_uses_defaults_for_empty_values(self):
        payload = build_fallback_cover_svg("", "")
        rendered = payload.decode("utf-8")

        self.assertIn("Untitled", rendered)
        self.assertIn("Unknown Author", rendered)


if __name__ == "__main__":
    unittest.main()

