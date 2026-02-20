"""
Fetches the Wellness, Actually RSS feed and adds any new episodes
to the top of episodes.html.
"""

import urllib.request
import xml.etree.ElementTree as ET
import re
import html as html_lib
from email.utils import parsedate_to_datetime

RSS_URL = (
    "https://www.omnycontent.com/d/playlist/"
    "e73c998e-6e60-432f-8610-ae210140c5b1/"
    "dceb4817-4846-442b-83bb-b3d801515725/"
    "13edb26a-7d1d-4f1c-b241-b3d801515735/podcast.rss"
)
EPISODES_HTML = "episodes.html"
ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"


def strip_html(text):
    """Strip HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", text)
    return html_lib.unescape(text).strip()


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
            formatted_date = pub_date.strftime("%-d %B %Y")  # e.g. "19 February 2026"
            # Reformat to match existing style: "February 19, 2026"
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


def make_episode_card(ep):
    if ep["episode_type"] == "trailer":
        label = "Trailer"
    elif ep["episode_num"]:
        label = f"Episode {ep['episode_num']}"
    else:
        label = "Episode"

    desc = ep["description"]
    if len(desc) > 400:
        desc = desc[:397] + "..."

    title_safe = html_lib.escape(ep["title"])
    desc_safe = html_lib.escape(desc)
    audio_url_safe = html_lib.escape(ep["audio_url"])

    return f"""        <article class="episode-card">
            <div class="episode-header">
                <span class="episode-number">{label}</span>
                <span class="episode-date">{ep['date']}</span>
            </div>
            <h2>{title_safe}</h2>
            <p class="episode-description">{desc_safe}</p>
            <div class="episode-player">
                <audio controls style="width:100%; margin-top:8px;">
                    <source src="{audio_url_safe}" type="audio/mpeg">
                </audio>
            </div>
        </article>"""


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

    # RSS feed is newest-first, so new_episodes preserves that order
    new_cards = "\n\n".join(make_episode_card(ep) for ep in new_episodes)

    insert_marker = '    <main class="episodes">\n'
    if insert_marker not in html_content:
        raise RuntimeError("Could not find insertion point in episodes.html")

    updated = html_content.replace(
        insert_marker,
        f"{insert_marker}{new_cards}\n\n",
    )

    with open(EPISODES_HTML, "w", encoding="utf-8") as f:
        f.write(updated)

    print("Done.")


if __name__ == "__main__":
    main()
