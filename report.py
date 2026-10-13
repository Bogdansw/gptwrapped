"""
report.py - Standalone, offline HTML report generator for GPT Wrapped.

Generates a plain, dark-mode HTML report with:
- Zero external CDN dependencies (works completely offline).
- Pure vector SVG charts embedded directly into HTML.
- Two view modes: 'Full Report' scrollable mode and 'Story Mode'.
- Local-only processing and safe HTML escaping.
"""

from html import escape
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from analyzer import Award, ConversationHighlight, WrappedStats

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def generate_monthly_svg_chart(msgs_by_month: Dict[int, int], convs_by_month: Dict[int, int]) -> str:
    """Generate a plain SVG bar chart for monthly activity."""
    max_msgs = max(list(msgs_by_month.values()) + [1])
    width = 760
    height = 240
    padding_left = 50
    padding_right = 20
    padding_top = 30
    padding_bottom = 40
    chart_w = width - padding_left - padding_right
    chart_h = height - padding_top - padding_bottom

    bars = []
    slot_w = chart_w / 12
    bar_w = min(slot_w * 0.55, 34)

    grid_lines = []
    for step in [0.25, 0.5, 0.75, 1.0]:
        val = int(max_msgs * step)
        y = padding_top + chart_h * (1 - step)
        grid_lines.append(
            f'<line x1="{padding_left}" y1="{y:.1f}" x2="{width - padding_right}" y2="{y:.1f}" '
            f'stroke="rgba(255,255,255,0.07)" stroke-dasharray="4,4" />'
            f'<text x="{padding_left - 10}" y="{y + 4:.1f}" fill="rgba(255,255,255,0.4)" '
            f'font-size="11" text-anchor="end" font-family="system-ui">{val}</text>'
        )

    for m in range(1, 13):
        m_count = msgs_by_month.get(m, 0)
        c_count = convs_by_month.get(m, 0)
        fraction = m_count / max_msgs if max_msgs > 0 else 0
        bar_height = max(fraction * chart_h, 3 if m_count > 0 else 0)
        x = padding_left + (m - 1) * slot_w + (slot_w - bar_w) / 2
        y = padding_top + (chart_h - bar_height)
        month_label = MONTH_NAMES[m - 1]

        val_text = f'<text x="{x + bar_w / 2:.1f}" y="{max(y - 8, 14):.1f}" fill="#a8a8a8" font-size="11" font-weight="600" text-anchor="middle" font-family="system-ui">{m_count}</text>' if m_count > 0 else ''
        bars.append(f"""
        <g class="chart-bar-group" tabindex="0">
            <title>{month_label}: {m_count:,} messages ({c_count:,} chats)</title>
            <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_height:.1f}" rx="2"
                  fill="#4f8fd0" class="chart-bar" />
            <text x="{x + bar_w / 2:.1f}" y="{height - 12}" fill="rgba(255,255,255,0.6)"
                  font-size="12" text-anchor="middle" font-family="system-ui">{month_label}</text>
            {val_text}
        </g>
        """)

    svg = f"""
    <svg viewBox="0 0 {width} {height}" class="wrapped-chart-svg" xmlns="http://www.w3.org/2000/svg">
        {''.join(grid_lines)}
        {''.join(bars)}
    </svg>
    """
    return svg


def generate_hourly_svg_chart(msgs_by_hour: Dict[int, int], peak_hour: int) -> str:
    """Generate a 24-hour activity distribution chart."""
    max_msgs = max(list(msgs_by_hour.values()) + [1])
    width = 760
    height = 220
    padding_left = 50
    padding_right = 20
    padding_top = 25
    padding_bottom = 40
    chart_w = width - padding_left - padding_right
    chart_h = height - padding_top - padding_bottom

    bars = []
    slot_w = chart_w / 24
    bar_w = min(slot_w * 0.72, 22)

    for h in range(24):
        count = msgs_by_hour.get(h, 0)
        fraction = count / max_msgs if max_msgs > 0 else 0
        bar_height = max(fraction * chart_h, 3 if count > 0 else 0)
        x = padding_left + h * slot_w + (slot_w - bar_w) / 2
        y = padding_top + (chart_h - bar_height)

        is_peak = (h == peak_hour and count > 0)
        bar_fill = "#cfa65a" if is_peak else "#4f8fd0"

        h_label = f"{h:02d}" if h % 3 == 0 else ""
        label_text = f'<text x="{x + bar_w / 2:.1f}" y="{height - 12}" fill="rgba(255,255,255,0.5)" font-size="11" text-anchor="middle" font-family="system-ui">{h_label}</text>' if h_label else ''
        peak_label = f'<text x="{x + bar_w / 2:.1f}" y="{max(y - 6, 12):.1f}" fill="#cfa65a" font-size="10" font-weight="700" text-anchor="middle" font-family="system-ui">peak</text>' if is_peak else ''

        bars.append(f"""
        <g class="chart-bar-group" tabindex="0">
            <title>{h:02d}:00 to {h:02d}:59: {count:,} messages</title>
            <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bar_height:.1f}" rx="2"
                  fill="{bar_fill}" class="chart-bar" />
            {label_text}
            {peak_label}
        </g>
        """)

    svg = f"""
    <svg viewBox="0 0 {width} {height}" class="wrapped-chart-svg" xmlns="http://www.w3.org/2000/svg">
        {''.join(bars)}
    </svg>
    """
    return svg


CSS_STYLES = """
:root {
    --bg: #141414;
    --bg-surface: #1c1c1c;
    --bg-surface-2: #222222;
    --border: #333333;
    --text: #dcdcdc;
    --text-secondary: #a8a8a8;
    --text-muted: #808080;
    --accent: #4f8fd0;
    --accent-soft: #6f9fcb;
    --green: #8fbf8f;
    --red: #c96f6f;
    --amber: #cfa65a;
    --radius: 4px;
    --font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    background-color: var(--bg);
    color: var(--text);
    font-family: var(--font-family);
    line-height: 1.6;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* Header */
.top-nav {
    width: 100%;
    max-width: 1000px;
    padding: 1rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 100;
}

.brand-badge {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
}

.mode-toggle-group {
    display: flex;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
}

.mode-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    padding: 0.4rem 0.9rem;
    font-size: 0.85rem;
    font-family: inherit;
    cursor: pointer;
    border-radius: 0;
}

.mode-btn + .mode-btn {
    border-left: 1px solid var(--border);
}

.mode-btn.active {
    background: var(--bg-surface-2);
    color: #ffffff;
}

/* Container */
.main-container {
    width: 100%;
    max-width: 1000px;
    padding: 2rem 1.5rem 4rem 1.5rem;
}

/* Story Controls */
.story-controls {
    display: none;
    width: 100%;
    max-width: 760px;
    margin: 0 auto 1.5rem auto;
    flex-direction: column;
    gap: 0.8rem;
}

.story-progress-bar {
    display: flex;
    gap: 6px;
    width: 100%;
}

.story-progress-segment {
    flex: 1;
    height: 4px;
    background: rgba(255, 255, 255, 0.12);
    overflow: hidden;
}

.story-progress-fill {
    width: 0%;
    height: 100%;
    background: #ffffff;
    transition: width 0.3s ease;
}

.story-progress-segment.passed .story-progress-fill {
    width: 100%;
}

.story-nav-buttons {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.story-nav-btn {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.45rem 1rem;
    border-radius: var(--radius);
    cursor: pointer;
    font-weight: 500;
    font-size: 0.9rem;
    font-family: inherit;
}

.story-nav-btn:hover {
    background: var(--bg-surface-2);
}

.story-slide-counter {
    font-size: 0.85rem;
    color: var(--text-muted);
}

/* Section Layout */
.wrapped-section {
    margin-bottom: 3rem;
    scroll-margin-top: 5rem;
}

.section-header {
    margin-bottom: 1.2rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.6rem;
}

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    line-height: 1.3;
}

.section-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-top: 0.2rem;
}

/* Hero */
.hero-banner {
    text-align: left;
    padding: 2.5rem 2rem;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    margin-bottom: 2.5rem;
}

.hero-year {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.6rem;
}

.hero-title {
    font-size: clamp(2rem, 5vw, 3rem);
    font-weight: 800;
    line-height: 1.15;
    margin-bottom: 0.8rem;
    color: #ffffff;
}

.hero-tagline {
    font-size: 1.05rem;
    color: var(--text-secondary);
    max-width: 620px;
}

/* Stats Grid */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.stat-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem;
}

.stat-big {
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1.1;
    color: #ffffff;
    margin-bottom: 0.3rem;
}

.stat-label {
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-secondary);
}

.stat-subtext {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 0.4rem;
}

/* Chart Card */
.chart-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.5rem;
}

.wrapped-chart-svg {
    width: 100%;
    height: auto;
    overflow: visible;
}

.chart-bar {
    transition: opacity 0.2s;
    cursor: pointer;
}

.chart-bar:hover {
    opacity: 0.75;
}

/* Topic List */
.topic-container {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.topic-row {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
}

.topic-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.95rem;
    font-weight: 600;
}

.topic-name {
    color: var(--text);
}

.topic-stat {
    color: var(--text-secondary);
}

.topic-pct {
    color: var(--text-muted);
    font-size: 0.85rem;
}

.topic-bar-track {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.07);
    overflow: hidden;
}

.topic-bar-fill {
    height: 100%;
    transition: width 0.6s ease;
}

.note-box {
    margin-top: 1.2rem;
    padding: 0.7rem 1rem;
    background: var(--bg-surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 0.8rem;
    color: var(--text-muted);
}

.empty-note {
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Rabbit Hole Card */
.rabbit-hole-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--red);
    border-radius: var(--radius);
    padding: 1.8rem;
}

.rabbit-label {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--red);
    font-weight: 700;
    margin-bottom: 0.8rem;
}

.rabbit-title {
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 1.4rem;
    color: #ffffff;
    line-height: 1.35;
}

.rabbit-stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 1rem;
    margin-bottom: 1.2rem;
}

.rabbit-stat-box {
    background: var(--bg-surface-2);
    padding: 0.9rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

.stat-num {
    display: block;
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
}

.stat-sub {
    font-size: 0.75rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.rabbit-date {
    font-size: 0.85rem;
    color: var(--text-muted);
}

/* Repeated Subjects */
.revisited-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-top: 0.6rem;
}

.revisited-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: var(--bg-surface-2);
    border: 1px solid var(--border);
    padding: 0.45rem 0.8rem;
    border-radius: var(--radius);
    font-size: 0.9rem;
}

.tag-word {
    color: var(--text);
    font-weight: 600;
}

.tag-count {
    color: var(--text-muted);
    font-size: 0.8rem;
}

.word-cloud-container {
    margin-top: 0.6rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.word-bubble {
    background: var(--bg-surface-2);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 0.35rem 0.7rem;
    border-radius: var(--radius);
    font-size: 0.85rem;
}

.sub-head {
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 0.4rem;
}

.sub-head.spaced {
    margin-top: 1.6rem;
}

/* Awards */
.awards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
}

.award-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.4rem;
}

.award-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.3rem;
}

.award-metric {
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--amber);
    margin-bottom: 0.35rem;
}

.award-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 0.35rem;
}

.award-detail {
    font-size: 0.78rem;
    color: var(--text-muted);
}

/* Summary */
.summary-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    max-width: 680px;
    margin: 0 auto;
}

.summary-header {
    font-size: 1.4rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
    color: #ffffff;
}

.summary-subtitle {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
}

.summary-stats-row {
    display: flex;
    justify-content: space-between;
    padding: 1.2rem 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}

.summary-item-num {
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
}

.summary-item-lbl {
    font-size: 0.72rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.summary-list {
    margin-bottom: 1.2rem;
}

.summary-list p {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 0.4rem;
}

.summary-list strong {
    color: var(--text);
}

.summary-footer {
    font-size: 0.82rem;
    color: var(--text-muted);
    border-top: 1px solid var(--border);
    padding-top: 0.9rem;
}

/* Footer */
.page-footer {
    width: 100%;
    max-width: 1000px;
    padding: 2rem 1.5rem;
    text-align: center;
    border-top: 1px solid var(--border);
    font-size: 0.82rem;
    color: var(--text-muted);
}

.footer-note {
    color: var(--green);
    font-weight: 600;
    margin-bottom: 0.4rem;
}

/* Responsive */
@media (max-width: 768px) {
    .section-title { font-size: 1.3rem; }
    .stats-grid { grid-template-columns: 1fr 1fr; }
    .summary-card { padding: 1.4rem 1.1rem; }
    .top-nav { padding: 0.9rem 1rem; }
}

@media (max-width: 480px) {
    .stats-grid { grid-template-columns: 1fr; }
    .summary-stats-row { flex-direction: column; gap: 1rem; }
}
"""

JS_SCRIPT = """
let currentMode = 'scroll';
let currentSlide = 0;
const totalSlides = 9;

function setViewMode(mode) {
    currentMode = mode;
    const btnScroll = document.getElementById('btnScrollMode');
    const btnStory = document.getElementById('btnStoryMode');
    const storyControls = document.getElementById('storyControls');

    if (mode === 'story') {
        btnScroll.classList.remove('active');
        btnStory.classList.add('active');
        storyControls.style.display = 'flex';
        showSlide(currentSlide);
    } else {
        btnStory.classList.remove('active');
        btnScroll.classList.add('active');
        storyControls.style.display = 'none';
        for (let i = 0; i < totalSlides; i++) {
            const slide = document.getElementById('slide-' + i);
            if (slide) slide.style.display = 'block';
        }
    }
}

function initStoryProgress() {
    const container = document.getElementById('storyProgressBar');
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < totalSlides; i++) {
        const seg = document.createElement('div');
        seg.className = 'story-progress-segment' + (i <= currentSlide ? ' passed' : '');
        seg.id = 'progress-seg-' + i;
        const fill = document.createElement('div');
        fill.className = 'story-progress-fill';
        seg.appendChild(fill);
        container.appendChild(seg);
    }
}

function showSlide(idx) {
    if (idx < 0) idx = 0;
    if (idx >= totalSlides) idx = totalSlides - 1;
    currentSlide = idx;

    for (let i = 0; i < totalSlides; i++) {
        const slide = document.getElementById('slide-' + i);
        if (slide) {
            slide.style.display = (i === currentSlide) ? 'block' : 'none';
        }
        const seg = document.getElementById('progress-seg-' + i);
        if (seg) {
            if (i <= currentSlide) {
                seg.classList.add('passed');
            } else {
                seg.classList.remove('passed');
            }
        }
    }

    const counter = document.getElementById('storySlideCounter');
    if (counter) counter.innerText = (currentSlide + 1) + ' of ' + totalSlides;
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function nextStorySlide() {
    if (currentSlide < totalSlides - 1) {
        showSlide(currentSlide + 1);
    }
}

function prevStorySlide() {
    if (currentSlide > 0) {
        showSlide(currentSlide - 1);
    }
}

document.addEventListener('keydown', function(e) {
    if (currentMode === 'story') {
        if (e.key === 'ArrowRight' || e.key === ' ') {
            nextStorySlide();
        } else if (e.key === 'ArrowLeft') {
            prevStorySlide();
        }
    }
});

document.addEventListener('DOMContentLoaded', function() {
    initStoryProgress();
});
"""


def render_html_report(
    stats: WrappedStats,
    available_years: List[int],
    output_filepath: str
) -> str:
    """Render the full GPT Wrapped HTML document and save to file."""
    year_display = str(stats.year) if stats.year else "All-Time"

    monthly_svg = generate_monthly_svg_chart(stats.messages_by_month, stats.conversations_by_month)
    hourly_svg = generate_hourly_svg_chart(stats.messages_by_hour, stats.peak_hour)

    # Topic bars, single accent colour with fading intensity
    topic_bars = []
    for idx, (cat, count, pct) in enumerate(stats.top_topics[:8]):
        opacity = max(1.0 - idx * 0.1, 0.3)
        topic_bars.append(f"""
        <div class="topic-row">
            <div class="topic-header">
                <span class="topic-name">{escape(cat)}</span>
                <span class="topic-stat">{count} chats <span class="topic-pct">({pct}%)</span></span>
            </div>
            <div class="topic-bar-track">
                <div class="topic-bar-fill" style="width: {max(pct, 3.0):.1f}%; background: rgba(79, 143, 208, {opacity:.2f});"></div>
            </div>
        </div>
        """)

    award_cards = []
    for award in stats.awards:
        award_cards.append(f"""
        <div class="award-card">
            <div class="award-title">{escape(award.title)}</div>
            <div class="award-metric">{escape(award.metric_value)}</div>
            <div class="award-desc">{escape(award.description)}</div>
            <div class="award-detail">{escape(award.extra_detail)}</div>
        </div>
        """)

    revisited_items = []
    for word, count in stats.revisited_subjects[:8]:
        revisited_items.append(f"""
        <div class="revisited-tag">
            <span class="tag-word">{escape(word)}</span>
            <span class="tag-count">{count} chats</span>
        </div>
        """)

    top_word_tags = []
    for word, count in stats.top_words[:12]:
        top_word_tags.append(f"""
        <span class="word-bubble"><strong>{escape(word)}</strong> <small>({count})</small></span>
        """)

    rabbit_hole_html = ""
    if stats.rabbit_hole:
        rh = stats.rabbit_hole
        rabbit_hole_html = f"""
        <div class="rabbit-hole-card">
            <div class="rabbit-label">Deepest conversation of {year_display}</div>
            <h3 class="rabbit-title">"{escape(rh.title)}"</h3>
            <div class="rabbit-stats-grid">
                <div class="rabbit-stat-box">
                    <span class="stat-num">{rh.message_count}</span>
                    <span class="stat-sub">Total messages</span>
                </div>
                <div class="rabbit-stat-box">
                    <span class="stat-num">{rh.user_message_count}</span>
                    <span class="stat-sub">Your prompts</span>
                </div>
                <div class="rabbit-stat-box">
                    <span class="stat-num">{rh.assistant_message_count}</span>
                    <span class="stat-sub">GPT answers</span>
                </div>
                <div class="rabbit-stat-box">
                    <span class="stat-num">{rh.word_count:,}</span>
                    <span class="stat-sub">Estimated words</span>
                </div>
            </div>
            <div class="rabbit-date">Created on {escape(rh.date_str)}</div>
        </div>
        """
    else:
        rabbit_hole_html = "<div class='empty-note'>No conversations recorded for this period.</div>"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GPT Wrapped - {year_display}</title>
    <style>
/*CSS_PLACEHOLDER*/
    </style>
</head>
<body>

    <header class="top-nav">
        <div class="brand-badge">GPT Wrapped</div>
        <div class="mode-toggle-group">
            <button class="mode-btn active" id="btnScrollMode" onclick="setViewMode('scroll')">Full Report</button>
            <button class="mode-btn" id="btnStoryMode" onclick="setViewMode('story')">Story Mode</button>
        </div>
    </header>

    <main class="main-container">

        <div class="story-controls" id="storyControls">
            <div class="story-progress-bar" id="storyProgressBar"></div>
            <div class="story-nav-buttons">
                <button class="story-nav-btn" onclick="prevStorySlide()">Previous</button>
                <span class="story-slide-counter" id="storySlideCounter">1 of 9</span>
                <button class="story-nav-btn" onclick="nextStorySlide()">Next</button>
            </div>
        </div>

        <section class="wrapped-section" id="slide-0">
            <div class="hero-banner">
                <div class="hero-year">{year_display} recap</div>
                <h1 class="hero-title">Your GPT Wrapped</h1>
                <p class="hero-tagline">
                    A local recap of the questions you asked and the threads you kept open.
                </p>
            </div>
        </section>

        <section class="wrapped-section" id="slide-1">
            <div class="section-header">
                <h2 class="section-title">The numbers</h2>
                <p class="section-subtitle">Your ChatGPT activity for this period.</p>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-big">{stats.total_conversations:,}</div>
                    <div class="stat-label">Conversations</div>
                    <div class="stat-subtext">Threads created in {year_display}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-big">{stats.total_messages:,}</div>
                    <div class="stat-label">Messages</div>
                    <div class="stat-subtext">{stats.total_user_messages:,} prompts and {stats.total_assistant_messages:,} answers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-big">{stats.active_days_count:,}</div>
                    <div class="stat-label">Active days</div>
                    <div class="stat-subtext">Days with at least one message</div>
                </div>
                <div class="stat-card">
                    <div class="stat-big">{stats.avg_messages_per_conv}</div>
                    <div class="stat-label">Avg messages / chat</div>
                    <div class="stat-subtext">Median: {stats.median_messages_per_conv} messages</div>
                </div>
            </div>
        </section>

        <section class="wrapped-section" id="slide-2">
            <div class="section-header">
                <h2 class="section-title">Messages by month</h2>
                <p class="section-subtitle">Message volume across each month of {year_display}.</p>
            </div>

            <div class="chart-card">
                {monthly_svg}
                <div class="note-box">
                    Busiest month: {escape(str(stats.most_active_month or "N/A"))} with {stats.most_active_month_count:,} messages.
                </div>
            </div>
        </section>

        <section class="wrapped-section" id="slide-3">
            <div class="section-header">
                <h2 class="section-title">Top topics</h2>
                <p class="section-subtitle">What you talked about most.</p>
            </div>

            <div class="chart-card">
                <div class="topic-container">
                    {''.join(topic_bars) if topic_bars else '<p class="empty-note">No topics recorded.</p>'}
                </div>
                <div class="note-box">
                    Approximate match on titles and your prompts. Nothing leaves your machine.
                </div>
            </div>
        </section>

        <section class="wrapped-section" id="slide-4">
            <div class="section-header">
                <h2 class="section-title">The rabbit hole</h2>
                <p class="section-subtitle">The one thread that went deeper than the rest.</p>
            </div>

            {rabbit_hole_html}
        </section>

        <section class="wrapped-section" id="slide-5">
            <div class="section-header">
                <h2 class="section-title">Hourly activity</h2>
                <p class="section-subtitle">When during the day you asked for help.</p>
            </div>

            <div class="chart-card">
                {hourly_svg}
                <div class="note-box">
                    Peak hour: {stats.peak_hour:02d}:00 to {stats.peak_hour:02d}:59 with {stats.peak_hour_count:,} messages.
                </div>
            </div>
        </section>

        <section class="wrapped-section" id="slide-6">
            <div class="section-header">
                <h2 class="section-title">Subjects you kept coming back to</h2>
                <p class="section-subtitle">Themes that kept reappearing in new conversations.</p>
            </div>

            <div class="chart-card">
                <p class="sub-head">Recurring subjects across conversation titles</p>
                <div class="revisited-grid">
                    {''.join(revisited_items) if revisited_items else '<span class="empty-note">No repeated subjects found.</span>'}
                </div>

                <p class="sub-head spaced">Frequent words (English and Romanian stopwords removed)</p>
                <div class="word-cloud-container">
                    {''.join(top_word_tags) if top_word_tags else '<span class="empty-note">No words extracted.</span>'}
                </div>
            </div>
        </section>

        <section class="wrapped-section" id="slide-7">
            <div class="section-header">
                <h2 class="section-title">Awards</h2>
                <p class="section-subtitle">Titles taken straight from the numbers.</p>
            </div>

            <div class="awards-grid">
                {''.join(award_cards) if award_cards else '<div class="empty-note">No awards generated.</div>'}
            </div>
        </section>

        <section class="wrapped-section" id="slide-8">
            <div class="section-header">
                <h2 class="section-title">Year in a snapshot</h2>
            </div>

            <div class="summary-card">
                <div class="summary-header">GPT Wrapped {year_display}</div>
                <div class="summary-subtitle">Built locally from your ChatGPT export</div>

                <div class="summary-stats-row">
                    <div>
                        <div class="summary-item-num">{stats.total_conversations:,}</div>
                        <div class="summary-item-lbl">Chats</div>
                    </div>
                    <div>
                        <div class="summary-item-num">{stats.total_messages:,}</div>
                        <div class="summary-item-lbl">Messages</div>
                    </div>
                    <div>
                        <div class="summary-item-num">{stats.active_days_count}</div>
                        <div class="summary-item-lbl">Active days</div>
                    </div>
                </div>

                <div class="summary-list">
                    <p><strong>Top category:</strong> {escape(stats.top_topics[0][0] if stats.top_topics else 'General')}</p>
                    <p><strong>Peak activity:</strong> {stats.peak_hour:02d}:00</p>
                    <p><strong>Longest streak:</strong> {stats.longest_streak_days} days</p>
                    {f'<p><strong>Deepest dive:</strong> "{escape(stats.rabbit_hole.title[:45])}..." ({stats.rabbit_hole.message_count} msgs)</p>' if stats.rabbit_hole else ''}
                </div>

                <div class="summary-footer">
                    Generated on this machine only. No data was sent anywhere.
                </div>
            </div>
        </section>

    </main>

    <footer class="page-footer">
        <div class="footer-note">Local processing only</div>
        <p>No external requests and no AI APIs were used to build this report.</p>
        <p style="margin-top: 0.4rem;">ChatGPT is a trademark of OpenAI. This project is independent.</p>
    </footer>

    <script>
/*JS_PLACEHOLDER*/
    </script>
</body>
</html>
"""

    html_content = html_content.replace("/*CSS_PLACEHOLDER*/", CSS_STYLES)
    html_content = html_content.replace("/*JS_PLACEHOLDER*/", JS_SCRIPT)

    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(out_path.resolve())
