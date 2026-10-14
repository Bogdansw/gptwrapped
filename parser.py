"""
parser.py - Resilient parser for ChatGPT data exports (ZIP archives or unzipped folders).

Locates and extracts conversations from ChatGPT data export ZIP archives or extracted folders,
handling:
- Partitioned / sharded exports: 'conversations-000.json', 'conversations-001.json', etc.
- Single 'conversations.json' files in root or nested subdirectories
- Tree mapping DAGs with parent-child structures
- Legacy linear message lists
- Missing timestamps, malformed records, and arbitrary nesting
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import zipfile

logger = logging.getLogger("gpt_wrapped.parser")


@dataclass
class Message:
    """Represents a single message in a conversation."""
    id: str
    role: str  # 'user', 'assistant', 'system', 'tool', etc.
    text: str
    timestamp: Optional[datetime] = None
    word_count: int = 0
    char_count: int = 0

    def __post_init__(self):
        if self.text:
            self.word_count = len(self.text.split())
            self.char_count = len(self.text)


@dataclass
class Conversation:
    """Represents a full conversation."""
    id: str
    title: str
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    messages: List[Message] = field(default_factory=list)
    user_message_count: int = 0
    assistant_message_count: int = 0
    total_message_count: int = 0
    total_words: int = 0
    total_chars: int = 0

    def compute_summary(self):
        """Precomputes summary metrics for quick retrieval."""
        self.user_message_count = sum(1 for m in self.messages if m.role == "user")
        self.assistant_message_count = sum(1 for m in self.messages if m.role == "assistant")
        self.total_message_count = len(self.messages)
        self.total_words = sum(m.word_count for m in self.messages)
        self.total_chars = sum(m.char_count for m in self.messages)


@dataclass
class ParsedExport:
    """Container for parsed export results."""
    conversations: List[Conversation]
    corrupted_count: int = 0
    source_path: Optional[str] = None
    available_years: List[int] = field(default_factory=list)


def parse_timestamp(val: Any) -> Optional[datetime]:
    """Safely parse epoch float/int or ISO string into a timezone-aware datetime."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(float(val), tz=timezone.utc)
        if isinstance(val, str):
            clean_str = val.replace("Z", "+00:00")
            return datetime.fromisoformat(clean_str)
    except Exception as e:
        logger.debug(f"Could not parse timestamp {val}: {e}")
    return None


def extract_message_text(content: Any) -> str:
    """
    Extract readable text from a message content object.
    Handles content_type 'text', 'multimodal_text', 'code', etc.
    """
    if not isinstance(content, dict):
        if isinstance(content, str):
            return content.strip()
        return ""

    if "text" in content and isinstance(content["text"], str):
        return content["text"].strip()

    parts = content.get("parts")
    if isinstance(parts, list):
        text_fragments = []
        for part in parts:
            if isinstance(part, str):
                text_fragments.append(part)
            elif isinstance(part, dict):
                if "text" in part and isinstance(part["text"], str):
                    text_fragments.append(part["text"])
                elif "code" in part and isinstance(part["code"], str):
                    text_fragments.append(part["code"])
                elif "name" in part and isinstance(part["name"], str):
                    text_fragments.append(f"[{part.get('name')}]")
        return "\n".join(t for t in text_fragments if t).strip()

    return ""


def parse_mapping_messages(mapping: Dict[str, Any], fallback_time: Optional[datetime]) -> List[Message]:
    """
    Extract messages from ChatGPT's node mapping DAG.
    Sorts messages chronologically by timestamp when available.
    """
    raw_nodes = []
    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        msg_obj = node.get("message")
        if not isinstance(msg_obj, dict):
            continue

        author = msg_obj.get("author", {})
        role = author.get("role", "unknown") if isinstance(author, dict) else "unknown"

        if role in ("system", "tool", "critic"):
            continue

        raw_text = extract_message_text(msg_obj.get("content"))
        msg_time = parse_timestamp(msg_obj.get("create_time")) or fallback_time
        msg_id = msg_obj.get("id") or node_id

        raw_nodes.append((msg_time, Message(
            id=str(msg_id),
            role=str(role).lower(),
            text=raw_text,
            timestamp=msg_time
        )))

    def sort_key(item):
        t, _ = item
        return (t.timestamp() if t else 0.0)

    raw_nodes.sort(key=sort_key)
    return [msg for _, msg in raw_nodes]


def parse_single_conversation(raw_conv: Dict[str, Any]) -> Optional[Conversation]:
    """Parse one conversation dictionary with complete fault tolerance."""
    if not isinstance(raw_conv, dict):
        return None

    conv_id = str(raw_conv.get("id", raw_conv.get("conversation_id", "unknown_id")))
    title = str(raw_conv.get("title") or "Untitled Conversation").strip()
    create_time = parse_timestamp(raw_conv.get("create_time"))
    update_time = parse_timestamp(raw_conv.get("update_time"))

    messages: List[Message] = []

    if "mapping" in raw_conv and isinstance(raw_conv["mapping"], dict):
        messages = parse_mapping_messages(raw_conv["mapping"], create_time)

    elif "messages" in raw_conv and isinstance(raw_conv["messages"], list):
        for idx, m in enumerate(raw_conv["messages"]):
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or m.get("author", {}).get("role") or "unknown").lower()
            if role in ("system", "tool", "critic"):
                continue
            text = extract_message_text(m.get("content") or m.get("text", ""))
            m_time = parse_timestamp(m.get("create_time") or m.get("timestamp")) or create_time
            m_id = str(m.get("id") or f"msg_{idx}")
            messages.append(Message(id=m_id, role=role, text=text, timestamp=m_time))

    if create_time is None:
        msg_times = [m.timestamp for m in messages if m.timestamp is not None]
        if msg_times:
            create_time = min(msg_times)

    conv = Conversation(
        id=conv_id,
        title=title,
        create_time=create_time,
        update_time=update_time,
        messages=messages
    )
    conv.compute_summary()
    return conv


def is_conversation_filename(filename: str) -> bool:
    """Check if a filename is conversations.json or a shard like conversations-000.json."""
    base = Path(filename).name.lower()
    return bool(re.match(r"^conversations(-\d+)?\.json$", base))


def parse_export_data(source_path: str) -> ParsedExport:
    """
    Main parser entrypoint.
    Supports either a ZIP archive (.zip) or an extracted directory.
    Finds all 'conversations.json' or 'conversations-*.json' files.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Export source not found at path: {source_path}")

    raw_conversations: List[Dict[str, Any]] = []

    if path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, "r") as z:
            conv_entries = [e for e in z.namelist() if is_conversation_filename(e)]
            if not conv_entries:
                conv_entries = [e for e in z.namelist() if "conversation" in e.lower() and e.endswith(".json") and "asset" not in e.lower()]

            if not conv_entries:
                raise KeyError(f"Could not find any 'conversations.json' or 'conversations-*.json' inside {path.name}.")

            conv_entries.sort()
            logger.info(f"Found {len(conv_entries)} conversation files in ZIP: {conv_entries}")

            for entry in conv_entries:
                with z.open(entry) as f:
                    try:
                        content = json.load(f)
                        if isinstance(content, list):
                            raw_conversations.extend(content)
                        elif isinstance(content, dict) and "conversations" in content:
                            raw_conversations.extend(content["conversations"])
                        elif isinstance(content, dict):
                            raw_conversations.append(content)
                    except Exception as e:
                        logger.warning(f"Error reading JSON from {entry}: {e}")

    elif path.is_dir():
        json_files = [f for f in path.rglob("*.json") if is_conversation_filename(f.name)]
        if not json_files:
            json_files = [f for f in path.rglob("*.json") if "conversation" in f.name.lower() and "asset" not in f.name.lower()]

        if not json_files:
            raise KeyError(f"Could not find any 'conversations.json' or 'conversations-*.json' inside folder '{path.name}'.")

        json_files.sort()
        logger.info(f"Found {len(json_files)} conversation files in directory: {[f.name for f in json_files]}")

        for jf in json_files:
            with open(jf, "r", encoding="utf-8", errors="replace") as f:
                try:
                    content = json.load(f)
                    if isinstance(content, list):
                        raw_conversations.extend(content)
                    elif isinstance(content, dict) and "conversations" in content:
                        raw_conversations.extend(content["conversations"])
                    elif isinstance(content, dict):
                        raw_conversations.append(content)
                except Exception as e:
                    logger.warning(f"Error reading JSON from {jf.name}: {e}")
    else:
        raise ValueError(f"Path at {source_path} is neither a valid ZIP archive nor a directory.")

    if not raw_conversations:
        raise ValueError(f"No conversation records could be extracted from {source_path}.")

    conversations: List[Conversation] = []
    corrupted = 0
    years_set = set()

    for item in raw_conversations:
        try:
            conv = parse_single_conversation(item)
            if conv:
                conversations.append(conv)
                if conv.create_time:
                    years_set.add(conv.create_time.year)
            else:
                corrupted += 1
        except Exception as e:
            logger.warning(f"Skipping malformed conversation due to error: {e}")
            corrupted += 1

    available_years = sorted(list(years_set), reverse=True)

    return ParsedExport(
        conversations=conversations,
        corrupted_count=corrupted,
        source_path=str(path),
        available_years=available_years
    )


parse_export_zip = parse_export_data
