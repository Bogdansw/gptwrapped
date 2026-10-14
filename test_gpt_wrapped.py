"""
test_gpt_wrapped.py - Automated verification and test suite for GPT Wrapped.

Generates a realistic mock ChatGPT data export ZIP archive featuring:
- Tree mapping DAGs (ChatGPT modern format)
- Multi-year conversations (2025, 2026)
- Romanian & English language conversations
- Deep rabbit hole multi-turn threads
- Late-night chats (Night Owl award testing)
- One-question quick lookups
- Corrupted/malformed records and missing timestamps
- Legacy flat messages array format fallback

Runs end-to-end assertions on parser, analyzer, topic system, HTML generation,
and offline/privacy guarantees.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import unittest
import zipfile

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from analyzer import analyze_export
from gpt_wrapped import run_pipeline
from parser import parse_export_zip
from topics import classify_conversation, extract_meaningful_words, extract_revisited_subjects


def create_mock_export_zip(zip_path: str):
    """Generate a realistic mock ChatGPT export zip file."""
    p = Path(zip_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    # 1. Multi-turn Python / Web development conversation (2026)
    conv_python = {
        "id": "conv-py-001",
        "title": "FastAPI and React Docker Deployment",
        "create_time": 1774000000.0,  # March 2026
        "update_time": 1774003600.0,
        "mapping": {
            "root": {"id": "root", "parent": None, "message": None},
            "node_1": {
                "id": "node_1",
                "parent": "root",
                "message": {
                    "id": "msg_1",
                    "author": {"role": "user"},
                    "create_time": 1774000000.0,
                    "content": {"content_type": "text", "parts": ["How do I configure Docker compose with FastAPI and React?"]}
                }
            },
            "node_2": {
                "id": "node_2",
                "parent": "node_1",
                "message": {
                    "id": "msg_2",
                    "author": {"role": "assistant"},
                    "create_time": 1774000060.0,
                    "content": {"content_type": "text", "parts": ["Here is a docker-compose.yml file example for FastAPI and React..."]}
                }
            },
            "node_3": {
                "id": "node_3",
                "parent": "node_2",
                "message": {
                    "id": "msg_3",
                    "author": {"role": "user"},
                    "create_time": 1774000200.0,
                    "content": {"content_type": "text", "parts": ["How do I fix CORS error in FastAPI?"]}
                }
            },
            "node_4": {
                "id": "node_4",
                "parent": "node_3",
                "message": {
                    "id": "msg_4",
                    "author": {"role": "assistant"},
                    "create_time": 1774000260.0,
                    "content": {"content_type": "text", "parts": ["Use CORSMiddleware from fastapi.middleware.cors."]}
                }
            }
        }
    }

    # 2. Deep Rabbit Hole conversation: 24 messages about building a game engine
    # Set at 02:30 AM (UTC) to trigger Night Owl testing
    rh_time = datetime(2026, 5, 12, 2, 30, tzinfo=timezone.utc).timestamp()
    mapping_rh = {"root": {"id": "root", "parent": None, "message": None}}
    prev_id = "root"
    for i in range(1, 25):
        cur_id = f"node_rh_{i}"
        role = "user" if i % 2 == 1 else "assistant"
        msg_text = (
            f"Question {i}: How do I optimize OpenGL rendering shaders?" if role == "user"
            else f"Answer {i}: You can optimize vertex buffer objects and reduce draw calls."
        )
        mapping_rh[cur_id] = {
            "id": cur_id,
            "parent": prev_id,
            "message": {
                "id": f"msg_rh_{i}",
                "author": {"role": role},
                "create_time": rh_time + (i * 120),
                "content": {"content_type": "text", "parts": [msg_text]}
            }
        }
        prev_id = cur_id

    conv_rabbit_hole = {
        "id": "conv-rh-002",
        "title": "Custom 2D Game Engine in C++ and OpenGL",
        "create_time": rh_time,
        "update_time": rh_time + 3000,
        "mapping": mapping_rh
    }

    # 3. Romanian Language conversation (School / Education)
    conv_ro_school = {
        "id": "conv-ro-003",
        "title": "Pregatire Examen Facultate Algoritmi",
        "create_time": datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc).timestamp(),
        "update_time": datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc).timestamp(),
        "mapping": {
            "root": {"id": "root", "parent": None, "message": None},
            "node_ro_1": {
                "id": "node_ro_1",
                "parent": "root",
                "message": {
                    "id": "msg_ro_1",
                    "author": {"role": "user"},
                    "create_time": datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc).timestamp(),
                    "content": {"content_type": "text", "parts": ["Te rog ajuta-ma cu o problema pentru examenul de algoritmi la facultate."]}
                }
            },
            "node_ro_2": {
                "id": "node_ro_2",
                "parent": "node_ro_1",
                "message": {
                    "id": "msg_ro_2",
                    "author": {"role": "assistant"},
                    "create_time": datetime(2026, 6, 15, 14, 1, tzinfo=timezone.utc).timestamp(),
                    "content": {"content_type": "text", "parts": ["Sigur, prezinta problema de programare dinamica si o rezolvam impreuna."]}
                }
            }
        }
    }

    # 4. One-question wonder chat (Travel)
    conv_travel = {
        "id": "conv-tr-004",
        "title": "Flight ticket baggage allowance",
        "create_time": datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc).timestamp(),
        "update_time": datetime(2026, 7, 20, 10, 5, tzinfo=timezone.utc).timestamp(),
        "mapping": {
            "root": {"id": "root", "parent": None, "message": None},
            "node_tr_1": {
                "id": "node_tr_1",
                "parent": "root",
                "message": {
                    "id": "msg_tr_1",
                    "author": {"role": "user"},
                    "create_time": datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc).timestamp(),
                    "content": {"content_type": "text", "parts": ["What is the standard carry-on luggage dimension for European flights?"]}
                }
            },
            "node_tr_2": {
                "id": "node_tr_2",
                "parent": "node_tr_1",
                "message": {
                    "id": "msg_tr_2",
                    "author": {"role": "assistant"},
                    "create_time": datetime(2026, 7, 20, 10, 1, tzinfo=timezone.utc).timestamp(),
                    "content": {"content_type": "text", "parts": ["Usually 55 x 40 x 20 cm including handles and wheels."]}
                }
            }
        }
    }

    # 5. Legacy format conversation from 2025 (testing year filter and flat messages list)
    conv_2025_legacy = {
        "id": "conv-legacy-2025",
        "title": "Anime recommendations for fantasy lovers",
        "create_time": datetime(2025, 11, 10, 18, 0, tzinfo=timezone.utc).timestamp(),
        "messages": [
            {
                "id": "leg_1",
                "role": "user",
                "create_time": datetime(2025, 11, 10, 18, 0, tzinfo=timezone.utc).timestamp(),
                "text": "Can you recommend top anime series like Frieren and Fullmetal Alchemist?"
            },
            {
                "id": "leg_2",
                "role": "assistant",
                "create_time": datetime(2025, 11, 10, 18, 1, tzinfo=timezone.utc).timestamp(),
                "text": "I highly recommend Mushoku Tensei, Dungeon Meshi, and Vinland Saga."
            }
        ]
    }

    # 6. Corrupted/edge-case entries (missing messages, bad JSON format, empty mapping)
    conv_corrupted_1 = {"id": "bad-1"}  # Missing title, timestamps, and mapping
    conv_corrupted_2 = "completely invalid string inside array"

    export_list = [
        conv_python,
        conv_rabbit_hole,
        conv_ro_school,
        conv_travel,
        conv_2025_legacy,
        conv_corrupted_1,
        conv_corrupted_2
    ]

    # Write into ZIP archive under a nested folder structure to test path finding
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("chatgpt_export_2026/conversations.json", json.dumps(export_list, indent=2))
        zf.writestr("chatgpt_export_2026/user.json", json.dumps({"name": "Test User"}))


class TestGptWrapped(unittest.TestCase):
    """Test suite covering parser, analyzer, topics, and report generation."""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path("./test_temp")
        cls.test_dir.mkdir(parents=True, exist_ok=True)
        cls.mock_zip = str(cls.test_dir / "mock_export.zip")
        create_mock_export_zip(cls.mock_zip)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_parser_resilience(self):
        """Test ZIP archive parsing, nested path discovery, and corruption handling."""
        export = parse_export_zip(self.mock_zip)
        self.assertGreaterEqual(len(export.conversations), 5)
        self.assertGreaterEqual(export.corrupted_count, 1)
        self.assertIn(2026, export.available_years)
        self.assertIn(2025, export.available_years)

        # Check conversation summaries
        conv_map = {c.id: c for c in export.conversations}
        self.assertIn("conv-py-001", conv_map)
        py_conv = conv_map["conv-py-001"]
        self.assertEqual(py_conv.user_message_count, 2)
        self.assertEqual(py_conv.assistant_message_count, 2)
        self.assertEqual(py_conv.total_message_count, 4)

        # Check rabbit hole conversation
        rh_conv = conv_map["conv-rh-002"]
        self.assertEqual(rh_conv.total_message_count, 24)

    def test_02_topic_classifier_and_stopwords(self):
        """Test keyword classification and Romanian/English stopword removal."""
        # 1. Test programming
        cat1, _ = classify_conversation("FastAPI and React Docker Deployment", ["Docker compose config"])
        self.assertEqual(cat1, "Programming / Web Development")

        # 2. Test Romanian school
        cat2, _ = classify_conversation("Pregatire Examen Facultate Algoritmi", ["Ajuta-ma cu examenul de algoritmi"])
        self.assertIn(cat2, ["School / Education", "Programming / Web Development"])

        # 3. Test stopword filtering
        words = extract_meaningful_words([
            "Te rog ajuta-ma cu o problema pentru examenul de algoritmi la facultate.",
            "Can you please help me write code for my university homework?"
        ])
        extracted_dict = dict(words)
        # Verify Romanian and English stopwords were omitted
        self.assertNotIn("te", extracted_dict)
        self.assertNotIn("rog", extracted_dict)
        self.assertNotIn("please", extracted_dict)
        self.assertNotIn("help", extracted_dict)
        self.assertNotIn("for", extracted_dict)
        self.assertIn("algoritmi", extracted_dict)

    def test_03_analyzer_year_filter_and_stats(self):
        """Test statistical computations for year 2026."""
        export = parse_export_zip(self.mock_zip)
        stats_2026 = analyze_export(export.conversations, selected_year=2026)

        self.assertEqual(stats_2026.year, 2026)
        self.assertEqual(stats_2026.total_conversations, 4)
        # Rabbit hole: 24 msgs + py: 4 msgs + ro: 2 msgs + travel: 2 msgs = 32 msgs
        self.assertEqual(stats_2026.total_messages, 32)
        self.assertIsNotNone(stats_2026.rabbit_hole)
        self.assertEqual(stats_2026.rabbit_hole.message_count, 24)

        # Awards
        award_ids = [a.id for a in stats_2026.awards]
        self.assertIn("rabbit_hole", award_ids)
        self.assertIn("night_owl", award_ids)  # Since rh conversation was at 02:30 AM
        self.assertIn("quick_draw", award_ids) # One question wonders

    def test_04_end_to_end_pipeline_and_offline_guarantee(self):
        """Test full pipeline, HTML generation, and verify strict offline privacy (no CDN)."""
        output_dir = self.test_dir / "test_output"
        saved_file = run_pipeline(
            zip_path=self.mock_zip,
            year=2026,
            output_dir=str(output_dir),
            open_browser=False
        )

        self.assertTrue(Path(saved_file).exists())
        file_size = Path(saved_file).stat().st_size
        self.assertGreater(file_size, 15000, "HTML file should be richly populated (>15KB)")

        with open(saved_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify all chapters/sections exist in the HTML
        self.assertIn("Your GPT Wrapped", content)
        self.assertIn("The numbers", content)
        self.assertIn("Messages by month", content)
        self.assertIn("Top topics", content)
        self.assertIn("The rabbit hole", content)
        self.assertIn("Hourly activity", content)
        self.assertIn("Subjects you kept coming back to", content)
        self.assertIn("Awards", content)
        self.assertIn("Year in a snapshot", content)

        # STRICT PRIVACY & OFFLINE VERIFICATION:
        # No external script or stylesheet CDN tags (no http:// or https:// script/css tags)
        self.assertNotIn('<script src="http', content)
        self.assertNotIn('<link rel="stylesheet" href="http', content)
        self.assertIn("Local processing only", content)


if __name__ == "__main__":
    unittest.main()
