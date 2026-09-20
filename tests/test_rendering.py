from __future__ import annotations

import unittest
from pathlib import Path

from harness.rendering import render_application
from pypdf import PdfReader
from support import scratch


def sample_application() -> dict:
    return {
        "company_name": "Example & Sons",
        "resume": {
            "summary": "Builds R&D workflows & reliable data systems.",
            "skills": [
                {
                    "label": "AI & Automation",
                    "value": "Python, SQL & production monitoring",
                }
            ],
            "experience": [
                {
                    "title": "Automation Engineer",
                    "company": "Research & Delivery GmbH",
                    "period": "2024 - Present",
                    "bullets": [
                        "Built approval workflows for operations & finance teams."
                    ],
                }
            ] + [
                {
                    "title": "Data Engineer",
                    "company": f"Example Employer {index}",
                    "period": f"{2023 - index} - {2024 - index}",
                    "bullets": ["Built tested data pipelines that reduced manual reporting work."],
                }
                for index in range(1, 4)
            ],
            "projects": [],
            "education": [
                {
                    "degree": "MSc Data Science",
                    "school": "Example Institute & University",
                    "year": "2024",
                },
                {
                    "degree": "BSc Computer Science",
                    "school": "Example College",
                    "year": "2020",
                },
            ],
        },
        "cover_letter": {
            "date": "20 September 2026",
            "company_address": "Example & Sons\nBerlin, Germany",
            "salutation": "Dear Hiring Team",
            "paragraphs": [
                "I build R&D workflows & production systems that remain readable."
            ],
        },
    }


class RenderApplicationTests(unittest.TestCase):
    def test_profile_drives_headers_and_plain_text_markup_is_escaped(self) -> None:
        """Catches stale constants or unescaped application/profile strings."""
        profile = {
            "name": "Ada Lovelace",
            "location": "Berlin & Remote",
            "phone": "+49 123 456",
            "email": "ada@example.test",
        }

        with scratch() as temporary_directory:
            result = render_application(
                sample_application(), profile, temporary_directory
            )

            self.assertEqual(
                {
                    "resume",
                    "cover_letter",
                    "page_counts",
                    "extracted_text",
                    "checks",
                },
                set(result),
            )
            self.assertTrue(Path(result["resume"]).is_file())
            self.assertTrue(Path(result["cover_letter"]).is_file())

            for document in ("resume", "cover_letter"):
                text = result["extracted_text"][document]
                self.assertIn("Ada Lovelace", text)
                self.assertIn("Berlin & Remote", text)
                self.assertIn("+49 123 456", text)
                self.assertIn("ada@example.test", text)
                self.assertNotIn("Lohith Burra", text)
                self.assertNotIn("burralohith01@gmail.com", text)

            resume_text = result["extracted_text"]["resume"]
            self.assertIn("R&D workflows & reliable data systems", resume_text)
            self.assertIn("AI & Automation", resume_text)
            self.assertNotIn("LinkedIn", resume_text)
            self.assertNotIn("GitHub", resume_text)
            self.assertEqual(1, result["page_counts"]["resume"])
            self.assertEqual(1, result["page_counts"]["cover_letter"])
            self.assertTrue(result["checks"]["resume_selectable_text"])
            self.assertTrue(result["checks"]["cover_letter_selectable_text"])
            self.assertTrue(result["checks"]["passed"])

            body_sizes = []

            def capture_body_size(text, _cm, _tm, _font, font_size):
                if "R&D workflows" in text or "Built approval workflows" in text:
                    body_sizes.append(float(font_size))

            PdfReader(result["resume"]).pages[0].extract_text(
                visitor_text=capture_body_size
            )
            self.assertGreaterEqual(len(body_sizes), 2)
            self.assertGreaterEqual(min(body_sizes), 10.0)

    def test_optional_links_are_rendered_only_when_supplied(self) -> None:
        """Catches dropping supplied links or injecting omitted contact values."""
        profile = {
            "name": "Ada Lovelace",
            "location": "Berlin",
            "phone": "+49 123 456",
            "linkedin": "https://www.linkedin.com/in/ada-example",
            "github": "https://github.com/ada-example",
        }

        with scratch() as temporary_directory:
            result = render_application(
                sample_application(), profile, temporary_directory
            )

            for document in ("resume", "cover_letter"):
                text = result["extracted_text"][document]
                self.assertIn("LinkedIn", text)
                self.assertIn("GitHub", text)
                self.assertNotIn("burralohith01@gmail.com", text)

    def test_oversized_resume_is_returned_with_failed_one_page_check(self) -> None:
        """Catches silent font shrinking or treating a multi-page resume as accepted."""
        application = sample_application()
        application["resume"]["experience"][0]["bullets"] = [
            (
                f"Evidence item {index}: designed and operated a production workflow "
                "with validation, monitoring, recovery, documentation, and stakeholder "
                "feedback across several business systems."
            )
            for index in range(40)
        ]
        profile = {"name": "Ada Lovelace", "location": "Berlin", "phone": "+49 1"}

        with scratch() as temporary_directory:
            result = render_application(
                application, profile, temporary_directory
            )

            self.assertGreater(result["page_counts"]["resume"], 1)
            self.assertFalse(result["checks"]["resume_one_page"])
            self.assertFalse(result["checks"]["passed"])
            self.assertEqual(10.0, result["checks"]["minimum_body_font_pt"])
            self.assertTrue(Path(result["resume"]).is_file())
            self.assertIn("Evidence item 39", result["extracted_text"]["resume"])

    def test_missing_required_application_field_is_a_clear_value_error(self) -> None:
        """Catches partial PDFs and raw KeyError leaks for malformed public JSON."""
        application = sample_application()
        del application["resume"]["summary"]

        with scratch() as temporary_directory:
            with self.assertRaisesRegex(ValueError, r"resume\.summary"):
                render_application(
                    application,
                    {"name": "Ada", "location": "Berlin", "phone": "+49 1"},
                    temporary_directory,
                )

            self.assertEqual([], list(temporary_directory.glob("*.pdf")))

    def test_missing_required_profile_field_is_a_clear_value_error(self) -> None:
        """Catches silently incomplete identity headers."""
        with scratch() as temporary_directory:
            with self.assertRaisesRegex(ValueError, r"profile\.phone"):
                render_application(
                    sample_application(),
                    {"name": "Ada", "location": "Berlin"},
                    temporary_directory,
                )


if __name__ == "__main__":
    unittest.main()
