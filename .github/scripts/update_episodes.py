"""
Fetches the Wellness, Actually RSS feed, adds any new episodes to the top
of episodes.html, and generates individual episode pages in episodes/.

Layout rules for episodes.html:
  - The newest episode card includes the embedded audio player.
  - All other cards show title, date, description, and a "View Episode" link.
Individual episode pages always include the audio player and a transcript
placeholder (to be filled in manually).
"""

import urllib.request
import xml.etree.ElementTree as ET
import re
import html as html_lib
import os
from email.utils import parsedate_to_datetime

RSS_URL = (
    "https://www.omnycontent.com/d/playlist/"
    "e73c998e-6e60-432f-8610-ae210140c5b1/"
    "dceb4817-4846-442b-83bb-b3d801515725/"
    "13edb26a-7d1d-4f1c-b241-b3d801515735/podcast.rss"
)
EPISODES_HTML = "episodes.html"
EPISODES_DIR = "episodes"
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def strip_html(text):
    """Strip HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", text)
    return html_lib.unescape(text).strip()


def make_slug(ep):
    """Generate a URL-friendly filename slug for an episode."""
    if ep["episode_type"] == "trailer":
        return "trailer"
    title = ep["title"].lower()
    slug = re.sub(r"[^a-z0-9]+", "-", title).strip("-")
    if ep["episode_num"]:
        return f"episode-{ep['episode_num']}-{slug}"
    return slug


def fetch_episodes():
    with urllib.request.urlopen(RSS_URL) as response:
        data = response.read()

    root = ET.fromstring(data)
    channel = root.find("channel")
    episodes = []

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        pub_date_str = item.findtext("pubDate") or ""
        episode_num = item.findtext(f"{{{ITUNES_NS}}}episode")
        episode_type = item.findtext(f"{{{ITUNES_NS}}}episodeType") or "full"
        description = strip_html(item.findtext("description") or "")

        enclosure = item.find("enclosure")
        audio_url = enclosure.get("url") if enclosure is not None else ""

        try:
            pub_date = parsedate_to_datetime(pub_date_str)
            formatted_date = pub_date.strftime("%B %-d, %Y")
        except Exception:
            formatted_date = pub_date_str

        episodes.append(
            {
                "title": title,
                "date": formatted_date,
                "episode_num": episode_num,
                "episode_type": episode_type,
                "description": description,
                "audio_url": audio_url,
            }
        )

    return episodes


def make_episode_label(ep):
    if ep["episode_type"] == "trailer":
        return "Trailer"
    if ep["episode_num"]:
        return f"Episode {ep['episode_num']}"
    return "Episode"


def make_episode_card(ep, include_player=False):
    """Build an episode card for episodes.html.

    If include_player is True the audio player is embedded (used for the
    newest episode only).  All cards include a "View Episode" link.
    """
    label = make_episode_label(ep)
    slug = make_slug(ep)

    desc = ep["description"]
    if len(desc) > 400:
        desc = desc[:397] + "..."

    title_safe = html_lib.escape(ep["title"])
    desc_safe = html_lib.escape(desc)
    audio_url_safe = html_lib.escape(ep["audio_url"])
    page_path = f"episodes/{slug}.html"

    player_html = ""
    if include_player:
        player_html = f"""
            <div class="episode-player">
                <audio controls style="width:100%; margin-top:8px;">
                    <source src="{audio_url_safe}" type="audio/mpeg">
                </audio>
            </div>"""

    return f"""        <article class="episode-card">
            <div class="episode-header">
                <span class="episode-number">{label}</span>
                <span class="episode-date">{ep['date']}</span>
            </div>
            <h2>{title_safe}</h2>
            <p class="episode-description">{desc_safe}</p>{player_html}
            <a href="{page_path}" class="view-episode-link">View Episode &#8594;</a>
        </article>"""


def make_episode_page(ep, slug):
    """Generate the full HTML for an individual episode page."""
    label = make_episode_label(ep)
    title_safe = html_lib.escape(ep["title"])
    desc_safe = html_lib.escape(ep["description"])
    audio_url_safe = html_lib.escape(ep["audio_url"])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_safe} | Wellness, Actually</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 0 20px;
        }}

        /* Navigation */
        nav {{
            background-color: #1e5f5f;
            padding: 15px 20px;
        }}

        nav .container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        nav a {{
            color: white;
            text-decoration: none;
            font-weight: 500;
        }}

        nav a:hover {{
            text-decoration: underline;
        }}

        .nav-brand {{
            font-size: 1.2rem;
            font-weight: 600;
        }}

        .nav-links a {{
            margin-left: 25px;
        }}

        /* Header */
        header {{
            background-color: #2a7a7a;
            padding: 50px 20px;
            text-align: center;
        }}

        .episode-meta {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .episode-number {{
            background-color: rgba(255,255,255,0.2);
            color: white;
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }}

        .episode-date {{
            color: rgba(255,255,255,0.8);
            font-size: 0.9rem;
            line-height: 1.8;
        }}

        header h1 {{
            color: white;
            font-size: 2rem;
            max-width: 700px;
            margin: 0 auto;
        }}

        /* Main content */
        main {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .episode-player {{
            background-color: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}

        .episode-description {{
            background-color: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}

        .episode-description h2 {{
            color: #2a7a7a;
            font-size: 1.3rem;
            margin-bottom: 15px;
        }}

        .episode-description p {{
            color: #555;
            font-size: 1rem;
        }}

        /* Transcript */
        .transcript {{
            background-color: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}

        .transcript h2 {{
            color: #2a7a7a;
            font-size: 1.3rem;
            margin-bottom: 20px;
        }}

        .transcript-placeholder {{
            background-color: #f9f9f9;
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            color: #888;
            font-size: 1rem;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 25px;
            color: #2a7a7a;
            text-decoration: none;
            font-weight: 500;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}

        /* Footer */
        footer {{
            background-color: #1e5f5f;
            padding: 20px;
            text-align: center;
            color: rgba(255,255,255,0.7);
            font-size: 0.9rem;
        }}

        /* Responsive */
        @media (max-width: 600px) {{
            header h1 {{ font-size: 1.5rem; }}
            nav .container {{ flex-direction: column; gap: 10px; }}
            .nav-links a {{ margin-left: 15px; }}
            .nav-links a:first-child {{ margin-left: 0; }}
        }}
    </style>
</head>
<body>
    <nav>
        <div class="container">
            <a href="../index.html" class="nav-brand">Wellness, Actually</a>
            <div class="nav-links">
                <a href="../index.html">Home</a>
                <a href="../episodes.html">Episodes</a>
            </div>
        </div>
    </nav>

    <header>
        <div class="container">
            <div class="episode-meta">
                <span class="episode-number">{label}</span>
                <span class="episode-date">{ep['date']}</span>
            </div>
            <h1>{title_safe}</h1>
        </div>
    </header>

    <main>
        <a href="../episodes.html" class="back-link">&larr; Back to all episodes</a>

        <div class="episode-player">
            <audio controls style="width:100%;">
                <source src="{audio_url_safe}" type="audio/mpeg">
            </audio>
        </div>

        <div class="episode-description">
            <h2>About This Episode</h2>
            <p>{desc_safe}</p>
        </div>

        <div class="transcript">
            <h2>Transcript</h2>
            <div class="transcript-placeholder">
                Transcript coming soon.
            </div>
        </div>
    </main>

    <footer>
        <p>&copy; 2026 Wellness, Actually. All rights reserved.</p>
    </footer>
</body>
</html>"""


def main():
    print("Fetching RSS feed...")
    episodes = fetch_episodes()
    print(f"Found {len(episodes)} episode(s) in feed.")

    with open(EPISODES_HTML, "r", encoding="utf-8") as f:
        html_content = f.read()

    # An episode is "new" if its title doesn't already appear in the HTML
    new_episodes = [ep for ep in episodes if ep["title"] not in html_content]

    if not new_episodes:
        print("No new episodes to add.")
        return

    print(f"Adding {len(new_episodes)} new episode(s):")
    for ep in new_episodes:
        print(f"  - {ep['title']} ({ep['date']})")

    os.makedirs(EPISODES_DIR, exist_ok=True)

    # Generate individual episode pages for new episodes
    for ep in new_episodes:
        slug = make_slug(ep)
        page_path = os.path.join(EPISODES_DIR, f"{slug}.html")
        if not os.path.exists(page_path):
            with open(page_path, "w", encoding="utf-8") as f:
                f.write(make_episode_page(ep, slug))
            print(f"  Created {page_path}")

    # RSS feed is newest-first.  The first new episode gets the player;
    # any additional new episodes added in the same run do not.
    # (The existing newest card in episodes.html already has no player since
    # it will be bumped down by the new episode.)
    new_cards = "\n\n".join(
        make_episode_card(ep, include_player=(i == 0))
        for i, ep in enumerate(new_episodes)
    )

    # Strip the player from the previously-newest card now that a newer one
    # is being prepended.  We identify it by the first <article> after the
    # opening <main class="episodes"> tag and remove its <div class="episode-player">
    # block if present.
    insert_marker = '    <main class="episodes">\n'
    if insert_marker not in html_content:
        raise RuntimeError("Could not find insertion point in episodes.html")

    # Remove the player div from the card that was previously newest
    html_content = re.sub(
        r'(\s*<div class="episode-player">.*?</div>)',
        "",
        html_content,
        count=1,
        flags=re.DOTALL,
    )

    updated = html_content.replace(
        insert_marker,
        f"{insert_marker}{new_cards}\n\n",
    )

    with open(EPISODES_HTML, "w", encoding="utf-8") as f:
        f.write(updated)

    print("Done.")


if __name__ == "__main__":
    main()
