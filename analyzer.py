"""
analyzer.py - Core statistics and awards engine for GPT Wrapped.

Computes overall counts, temporal distributions, outlier records,
topic frequencies, and data-backed awards for a selected year or all-time.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import statistics
from typing import Any, Dict, List, Optional, Tuple

from parser import Conversation
from topics import (
    CATEGORIES,
    classify_conversation,
    extract_meaningful_words,
    extract_revisited_subjects
)


@dataclass
class Award:
    """Represents a data-backed fun award."""
    id: str
    title: str
    badge_icon: str
    description: str
    metric_value: str
    extra_detail: str


@dataclass
class ConversationHighlight:
    """Represents a notable conversation."""
    id: str
    title: str
    message_count: int
    user_message_count: int
    assistant_message_count: int
    word_count: int
    date_str: str


@dataclass
class WrappedStats:
    """Comprehensive container for all analyzed Wrapped statistics."""
    year: Optional[int]
    total_conversations: int
    total_user_messages: int
    total_assistant_messages: int
    total_messages: int
    avg_messages_per_conv: float
    median_messages_per_conv: float
    first_conversation_date: Optional[str]
    latest_conversation_date: Optional[str]
    active_days_count: int
    most_active_day: Optional[str]
    most_active_day_count: int
    most_active_month: Optional[str]
    most_active_month_count: int
    most_active_year: Optional[int]
    longest_streak_days: int

    # Time distributions
    conversations_by_month: Dict[int, int]  # 1..12 -> count
    messages_by_month: Dict[int, int]        # 1..12 -> count
    conversations_by_weekday: Dict[int, int]  # 0 (Mon) .. 6 (Sun) -> count
    messages_by_weekday: Dict[int, int]      # 0 (Mon) .. 6 (Sun) -> count
    messages_by_hour: Dict[int, int]         # 0..23 -> count
    peak_hour: int
    peak_hour_count: int

    # Topic distribution
    topic_distribution: Dict[str, int]       # category -> conversation count
    topic_percentages: Dict[str, float]
    top_topics: List[Tuple[str, int, float]]

    # Highlights
    rabbit_hole: Optional[ConversationHighlight]
    longest_by_messages: List[ConversationHighlight]
    longest_by_words: List[ConversationHighlight]
    one_question_wonders_count: int
    one_question_wonders_pct: float

    # Word & recurring subjects
    top_words: List[Tuple[str, int]]
    revisited_subjects: List[Tuple[str, int]]

    # Awards
    awards: List[Award] = field(default_factory=list)


def analyze_export(conversations: List[Conversation], selected_year: Optional[int] = None) -> WrappedStats:
    """
    Perform complete statistical and topic analysis on conversations,
    filtering by selected_year if provided.
    """
    filtered: List[Conversation] = []
    for c in conversations:
        if c.create_time:
            if selected_year is None or c.create_time.year == selected_year:
                filtered.append(c)
        else:
            if selected_year is None:
                filtered.append(c)

    total_convs = len(filtered)
    if total_convs == 0:
        return WrappedStats(
            year=selected_year,
            total_conversations=0,
            total_user_messages=0,
            total_assistant_messages=0,
            total_messages=0,
            avg_messages_per_conv=0.0,
            median_messages_per_conv=0.0,
            first_conversation_date=None,
            latest_conversation_date=None,
            active_days_count=0,
            most_active_day=None,
            most_active_day_count=0,
            most_active_month=None,
            most_active_month_count=0,
            most_active_year=None,
            longest_streak_days=0,
            conversations_by_month={m: 0 for m in range(1, 13)},
            messages_by_month={m: 0 for m in range(1, 13)},
            conversations_by_weekday={w: 0 for w in range(7)},
            messages_by_weekday={w: 0 for w in range(7)},
            messages_by_hour={h: 0 for h in range(24)},
            peak_hour=0,
            peak_hour_count=0,
            topic_distribution={cat: 0 for cat in CATEGORIES},
            topic_percentages={cat: 0.0 for cat in CATEGORIES},
            top_topics=[],
            rabbit_hole=None,
            longest_by_messages=[],
            longest_by_words=[],
            one_question_wonders_count=0,
            one_question_wonders_pct=0.0,
            top_words=[],
            revisited_subjects=[],
            awards=[]
        )

    # Message counts
    total_user_msgs = sum(c.user_message_count for c in filtered)
    total_asst_msgs = sum(c.assistant_message_count for c in filtered)
    total_msgs = sum(c.total_message_count for c in filtered)

    msg_counts = [c.total_message_count for c in filtered]
    avg_msgs = round(sum(msg_counts) / total_convs, 1) if total_convs else 0.0
    med_msgs = float(statistics.median(msg_counts)) if msg_counts else 0.0

    # Date calculations
    valid_conv_dates = [c.create_time for c in filtered if c.create_time]
    first_date_str = min(valid_conv_dates).strftime("%B %d, %Y") if valid_conv_dates else None
    latest_date_str = max(valid_conv_dates).strftime("%B %d, %Y") if valid_conv_dates else None

    # Temporal breakdowns
    convs_by_month = {m: 0 for m in range(1, 13)}
    msgs_by_month = {m: 0 for m in range(1, 13)}
    convs_by_weekday = {w: 0 for w in range(7)}  # 0: Mon, 6: Sun
    msgs_by_weekday = {w: 0 for w in range(7)}
    msgs_by_hour = {h: 0 for h in range(24)}

    daily_msgs: Dict[str, int] = defaultdict(int)
    monthly_msgs: Dict[str, int] = defaultdict(int)
    yearly_msgs: Dict[int, int] = defaultdict(int)
    active_dates_set = set()

    for c in filtered:
        if c.create_time:
            m = c.create_time.month
            w = c.create_time.weekday()
            y = c.create_time.year
            convs_by_month[m] += 1
            convs_by_weekday[w] += 1
            yearly_msgs[y] += c.total_message_count

        for msg in c.messages:
            t = msg.timestamp or c.create_time
            if t:
                m = t.month
                w = t.weekday()
                h = t.hour
                d_key = t.strftime("%Y-%m-%d")
                mo_key = t.strftime("%B %Y")
                msgs_by_month[m] += 1
                msgs_by_weekday[w] += 1
                msgs_by_hour[h] += 1
                daily_msgs[d_key] += 1
                monthly_msgs[mo_key] += 1
                active_dates_set.add(t.date())

    active_days_count = len(active_dates_set)

    # Most active day & month
    most_act_day = None
    most_act_day_count = 0
    if daily_msgs:
        best_d, best_c = max(daily_msgs.items(), key=lambda x: x[1])
        try:
            parsed_d = datetime.strptime(best_d, "%Y-%m-%d")
            most_act_day = parsed_d.strftime("%B %d, %Y")
        except Exception:
            most_act_day = best_d
        most_act_day_count = best_c

    most_act_month = None
    most_act_month_count = 0
    if monthly_msgs:
        most_act_month, most_act_month_count = max(monthly_msgs.items(), key=lambda x: x[1])

    most_act_year = None
    if yearly_msgs:
        most_act_year, _ = max(yearly_msgs.items(), key=lambda x: x[1])

    # Longest streak of consecutive active days
    longest_streak = 0
    if active_dates_set:
        sorted_dates = sorted(list(active_dates_set))
        current_streak = 1
        longest_streak = 1
        for i in range(1, len(sorted_dates)):
            diff = (sorted_dates[i] - sorted_dates[i - 1]).days
            if diff == 1:
                current_streak += 1
                if current_streak > longest_streak:
                    longest_streak = current_streak
            elif diff > 1:
                current_streak = 1

    # Peak hour
    peak_h = 0
    peak_h_count = 0
    if msgs_by_hour:
        peak_h, peak_h_count = max(msgs_by_hour.items(), key=lambda x: x[1])

    # Topic classification
    topic_counts = {cat: 0 for cat in CATEGORIES}
    all_user_prompts: List[str] = []
    all_titles: List[str] = []

    for c in filtered:
        user_texts = [m.text for m in c.messages if m.role == "user" and m.text]
        all_user_prompts.extend(user_texts)
        all_titles.append(c.title)
        best_cat, _ = classify_conversation(c.title, user_texts)
        topic_counts[best_cat] += 1

    topic_percentages = {
        cat: round((cnt / total_convs) * 100, 1) for cat, cnt in topic_counts.items()
    }
    # Sorted topics by count
    top_topics = sorted(
        [(cat, cnt, topic_percentages[cat]) for cat, cnt in topic_counts.items() if cnt > 0],
        key=lambda x: x[1],
        reverse=True
    )

    # Word frequencies & repeated subjects
    top_words = extract_meaningful_words(all_user_prompts + all_titles, top_n=20)
    revisited_subjects = extract_revisited_subjects(all_titles, top_n=10)

    # Conversation outliers
    def make_highlight(conv: Conversation) -> ConversationHighlight:
        d_str = conv.create_time.strftime("%B %d, %Y") if conv.create_time else "Unknown Date"
        return ConversationHighlight(
            id=conv.id,
            title=conv.title,
            message_count=conv.total_message_count,
            user_message_count=conv.user_message_count,
            assistant_message_count=conv.assistant_message_count,
            word_count=conv.total_words,
            date_str=d_str
        )

    by_msgs = sorted(filtered, key=lambda c: c.total_message_count, reverse=True)
    by_words = sorted(filtered, key=lambda c: c.total_words, reverse=True)

    rabbit_hole = make_highlight(by_msgs[0]) if by_msgs else None
    longest_by_messages = [make_highlight(c) for c in by_msgs[:5]]
    longest_by_words = [make_highlight(c) for c in by_words[:5]]

    # One-question wonders (<= 2 messages: typically 1 user question + 1 assistant reply)
    one_q_wonders = [c for c in filtered if c.total_message_count <= 2]
    one_q_count = len(one_q_wonders)
    one_q_pct = round((one_q_count / total_convs) * 100, 1) if total_convs else 0.0

    # Fun Awards based purely on measurable data
    awards: List[Award] = []

    # 1. The Rabbit Hole Award (longest conversation)
    if rabbit_hole:
        awards.append(Award(
            id="rabbit_hole",
            title="The Rabbit Hole Award",
            badge_icon="hole",
            description="Deepest dive into a single conversation thread.",
            metric_value=f"{rabbit_hole.message_count} messages",
            extra_detail=f"Topic: \"{rabbit_hole.title}\""
        ))

    # 2. Night Owl vs Early Bird
    night_msgs = sum(msgs_by_hour[h] for h in range(0, 5))
    morning_msgs = sum(msgs_by_hour[h] for h in range(5, 9))
    if night_msgs >= morning_msgs and night_msgs > 0:
        awards.append(Award(
            id="night_owl",
            title="The Night Owl Award",
            badge_icon="moon",
            description="Peak midnight oil burned between 12:00 AM and 5:00 AM.",
            metric_value=f"{night_msgs} late-night messages",
            extra_detail=f"{round((night_msgs / max(total_msgs, 1)) * 100, 1)}% of all message activity"
        ))
    elif morning_msgs > 0:
        awards.append(Award(
            id="early_bird",
            title="The Early Bird Award",
            badge_icon="sunrise",
            description="High productivity between 5:00 AM and 9:00 AM.",
            metric_value=f"{morning_msgs} morning messages",
            extra_detail=f"{round((morning_msgs / max(total_msgs, 1)) * 100, 1)}% of all message activity"
        ))

    # 3. The Regular Award (top revisited topic or category)
    if top_topics:
        fav_cat, fav_count, fav_pct = top_topics[0]
        awards.append(Award(
            id="the_regular",
            title="The Regular",
            badge_icon="target",
            description="Your most dominant recurring subject area.",
            metric_value=f"{fav_count} conversations",
            extra_detail=f"Category: {fav_cat} ({fav_pct}% of total)"
        ))

    # 4. The Busy Month
    if most_act_month:
        awards.append(Award(
            id="busy_month",
            title="The Busy Month",
            badge_icon="bars",
            description="The most intense ChatGPT month of the year.",
            metric_value=f"{most_act_month_count} messages",
            extra_detail=f"Record set in {most_act_month}"
        ))

    # 5. The One-Question Wonder
    awards.append(Award(
        id="quick_draw",
            title="The One-Question Wonder",
            badge_icon="zap",
        description="Quick, laser-focused chats with 2 or fewer messages.",
        metric_value=f"{one_q_count} quick chats",
        extra_detail=f"{one_q_pct}% of conversations were instant lookups"
    ))

    # 6. The Streak Master (if streak >= 2)
    if longest_streak >= 2:
        awards.append(Award(
            id="streak_master",
            title="The Streak Master",
            badge_icon="trend",
            description="Longest uninterrupted consecutive daily usage streak.",
            metric_value=f"{longest_streak} consecutive days",
            extra_detail="Consistent daily problem solving"
        ))

    return WrappedStats(
        year=selected_year,
        total_conversations=total_convs,
        total_user_messages=total_user_msgs,
        total_assistant_messages=total_asst_msgs,
        total_messages=total_msgs,
        avg_messages_per_conv=avg_msgs,
        median_messages_per_conv=med_msgs,
        first_conversation_date=first_date_str,
        latest_conversation_date=latest_date_str,
        active_days_count=active_days_count,
        most_active_day=most_act_day,
        most_active_day_count=most_act_day_count,
        most_active_month=most_act_month,
        most_active_month_count=most_act_month_count,
        most_active_year=most_act_year,
        longest_streak_days=longest_streak,
        conversations_by_month=convs_by_month,
        messages_by_month=msgs_by_month,
        conversations_by_weekday=convs_by_weekday,
        messages_by_weekday=msgs_by_weekday,
        messages_by_hour=msgs_by_hour,
        peak_hour=peak_h,
        peak_hour_count=peak_h_count,
        topic_distribution=topic_counts,
        topic_percentages=topic_percentages,
        top_topics=top_topics,
        rabbit_hole=rabbit_hole,
        longest_by_messages=longest_by_messages,
        longest_by_words=longest_by_words,
        one_question_wonders_count=one_q_count,
        one_question_wonders_pct=one_q_pct,
        top_words=top_words,
        revisited_subjects=revisited_subjects,
        awards=awards
    )
