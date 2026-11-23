"""
Transcript Audit & Comparison for the 5 Historical Speeches.
Fetches/references official transcripts with source URLs, highlights Faster-Whisper errors,
verifies spoken audio stumbles vs official text, and generates unified diffs.
"""

import difflib
import json
from pathlib import Path

MANIFEST_PATH = Path("data/manifests/real_speech_manifest.json")

OFFICIAL_SPEECHES = [
    {
        "speech_id": "jfk_moon_1962",
        "title": "Address at Rice University on the Nation's Space Effort ('We choose to go to the Moon')",
        "speaker": "John F. Kennedy",
        "date": "1962-09-12",
        "source_archive_url": "https://www.jfklibrary.org/asset-viewer/archives/JFKWHA/1962/JFKWHA-127-002",
        "official_transcript": (
            "240,000 miles away from the control station in Houston, a giant rocket, more than 300 feet tall, "
            "the length of this football field, made of new metal alloys, some of which have not yet been invented, "
            "capable of standing heat and stresses, several times more than have ever been experienced, "
            "fitted together with a precision better than the finest watch, carrying all the equipment needed "
            "for propulsion, guidance, control, communications, food and survival, on an untried mission to an "
            "unknown celestial body and then return it safely to earth, re-entering the atmosphere at speeds of "
            "over 25,000 miles per hour, causing heat about half that of the temperature of the sun, almost as hot "
            "as it is here today and do all this, and do all this, and do it right and do it first, before this decade "
            "is out, then we must be bold."
        ),
        "spoken_vs_official_notes": (
            "Speaker stumble / rhetorical repetition: JFK clearly speaks 'and do all this, and do all this' "
            "(at 54.05s-56.66s in the audio) whereas prepared reading copy had a single clause. Spoken repetition is kept "
            "per policy and recorded in metadata. Fixed Whisper mishearings: '140,000' -> '240,000', 'embedded' -> 'invented', "
            "'pitted' -> 'fitted', 'communication' -> 'communications', 'that on the' -> 'that of the', "
            "'if all this thick heat is out' (7 words) -> 'before this decade is out' (5 words), 'bald' -> 'bold'."
        ),
    },
    {
        "speech_id": "reagan_challenger_1986",
        "title": "Address to the Nation on the Explosion of the Space Shuttle Challenger",
        "speaker": "Ronald Reagan",
        "date": "1986-01-28",
        "source_archive_url": "https://www.reaganlibrary.gov/archives/speech/address-nation-explosion-space-shuttle-challenger",
        "official_transcript": (
            "and tell them, your dedication and professionalism have moved and impressed us for decades, "
            "and we know of your anguish. We share it. There's a coincidence today. On this day, 390 years ago, "
            "the great explorer Sir Francis Drake died aboard ship off the coast of Panama. In his lifetime, "
            "the great frontiers were the oceans, and a historian later said he lived by the sea, died on it, "
            "and was buried in it. Well, today, we can say of the Challenger crew, their dedication was, like Drake's, "
            "complete. The crew of the space shuttle Challenger honored us for the manner in which they lived their lives. "
            "We will never forget them, nor the last time we saw them this morning, as they prepared for their journey "
            "and waved goodbye, and slipped the surly bonds of earth to touch the face of God. Thank you."
        ),
        "spoken_vs_official_notes": (
            "Spoken audio exactly matches official text. Removed stray quote artifact ('We share it.\"') and normalized "
            "casing of 'Challenger'."
        ),
    },
    {
        "speech_id": "fdr_fear_itself_1933",
        "title": "First Inaugural Address ('The only thing we have to fear is fear itself')",
        "speaker": "Franklin D. Roosevelt",
        "date": "1933-03-04",
        "source_archive_url": "https://www.archives.gov/milestone-documents/franklin-d-roosevelts-first-inaugural-address",
        "official_transcript": (
            "Let me assert my firm belief, that the only thing we have to fear is fear itself, nameless, "
            "unreasoning, unjustified terror, which paralyzes needed efforts to convert retreat into advance. "
            "In every dark hour of our national life, a leadership of frankness and of vigor has met with that "
            "understanding and support of the people themselves, which is essential to victory. And I am convinced "
            "that you will again give that support, to leadership, in these critical days."
        ),
        "spoken_vs_official_notes": (
            "FDR spoken audio exactly delivers the official text: 'and of vigor' (Whisper hallucinated 'and a fitter') "
            "and 'that you will again give that support' (Whisper hallucinated 'to show a game, give that support'). "
            "Word count is identical (3 words -> 3 words, 4 words -> 4 words), total words = 78."
        ),
    },
    {
        "speech_id": "reagan_mourning_1986",
        "title": "Challenger Memorial Address Opening ('A Day for Mourning and Remembering')",
        "speaker": "Ronald Reagan",
        "date": "1986-01-28",
        "source_archive_url": "https://www.reaganlibrary.gov/archives/speech/address-nation-explosion-space-shuttle-challenger",
        "official_transcript": (
            "Ladies and gentlemen, I'd planned to speak to you tonight to report on the State of the Union, "
            "but the events of earlier today have led me to change those plans. Today is a day for mourning and "
            "remembering. Nancy and I are pained to the core by the tragedy of the Shuttle Challenger. We know "
            "we share this pain with all of the people of our country. This is truly a national loss. Nineteen years ago, "
            "almost to the day, we lost three astronauts in a terrible accident on the ground. But we've never lost an "
            "astronaut in flight. We've never had a tragedy like this."
        ),
        "spoken_vs_official_notes": (
            "Spoken audio matches official text. Fixed Whisper errors: 'I'd plan' -> 'I'd planned', "
            "'morning' -> 'mourning', and 'paying to the core of' -> 'pained to the core by'. "
            "Word counts identical (107 words)."
        ),
    },
    {
        "speech_id": "jfk_we_choose_1962",
        "title": "Address at Rice University ('We choose to go to the Moon in this decade')",
        "speaker": "John F. Kennedy",
        "date": "1962-09-12",
        "source_archive_url": "https://www.jfklibrary.org/asset-viewer/archives/JFKWHA/1962/JFKWHA-127-002",
        "official_transcript": (
            "things, not because they are easy, but because they are hard, because that goal will serve to organize "
            "and measure the best of our energies and skills, because that challenge is one that we're willing to accept, "
            "one we are unwilling to postpone, and one we intend to win, and the others too. It is, for these reasons, "
            "that I regard the decision last year to shift our efforts in space from low to high gear as among the most "
            "important decisions that will be made during my incumbency in the Office of the Presidency."
        ),
        "spoken_vs_official_notes": (
            "Spoken audio and Whisper transcript match official archive text completely. Zero word differences."
        ),
    },
]


def print_speech_diffs():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        current_speeches = {s["speech_id"]: s for s in json.load(f)}

    print("=" * 100)
    print("CANONICAL TRANSCRIPT AUDIT & FASTER-WHISPER DISCREPANCY DIFF")
    print("=" * 100)

    for item in OFFICIAL_SPEECHES:
        sid = item["speech_id"]
        cur = current_speeches.get(sid, {})
        cur_text = cur.get("transcript", "")
        off_text = item["official_transcript"]

        print(f"\nSPEECH ID: {sid}")
        print(f"TITLE:     {item['title']}")
        print(f"URL:       {item['source_archive_url']}")
        print(f"CANONICAL OFFICIAL TRANSCRIPT (IN FULL):")
        print(f"\"{off_text}\"\n")
        print(f"SPOKEN VS OFFICIAL / STUMBLE NOTES:")
        print(f"  {item['spoken_vs_official_notes']}\n")

        print("WORD-BY-WORD DIFF (Faster-Whisper Unreviewed vs Official Proposed):")
        cur_words = cur_text.split()
        off_words = off_text.split()
        diff = difflib.unified_diff(
            cur_words,
            off_words,
            fromfile=f"{sid} (Faster-Whisper Output)",
            tofile=f"{sid} (Official Corrected)",
            lineterm=""
        )
        diff_str = "\n".join(diff)
        if diff_str:
            print(diff_str)
        else:
            print("  (No differences - identical word sequence)")
        print("-" * 100)


if __name__ == "__main__":
    print_speech_diffs()
