import subprocess
import time
import json
import sys

# Customization settings (easy to modify)
GLYPH_FONT_FAMILY="Symbols Nerd Font Mono" # Set to your desired symbols font
# Those are glyphs that will be always visible at left side of module.
GLYPHS = {
    "paused": "",
    "playing": "",
    "stopped": ""
}
DEFAULT_GLYPH = ""  # Glyph when status is unknown or default
TEXT_WHEN_STOPPED = "Nothing playing right now"  # Text to display when nothing is playing
SCROLL_TEXT_LENGTH = 20  # Length of the song title part (excludes glyph and space)
REFRESH_INTERVAL = 0.3 # How often the script updates (in seconds)
PLAYERCTL_PATH = "/usr/bin/playerctl" # Path to playerctl, use which playerctl to find yours.

# Function to get player status using playerctl
def get_player_status():
    try:
        result = subprocess.run([PLAYERCTL_PATH, 'status'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        status = result.stdout.decode('utf-8').strip().lower()
        if result.returncode != 0 or not status:
            return "stopped"  # Default to stopped if no status
        return status
    except Exception as e:
        return "stopped"

# Function to get currently playing song using playerctl
def get_current_song():
    try:
        result = subprocess.run([PLAYERCTL_PATH, 'metadata', 'title'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        song_title = result.stdout.decode('utf-8').strip()
        if result.returncode != 0 or not song_title:
            return None  # Return None if no song is playing or an error occurred
        return song_title
    except Exception as e:
        return None

def get_current_artist():
    try:
        result = subprocess.run([PLAYERCTL_PATH, 'metadata', 'artist'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        song_artist = result.stdout.decode('utf-8').strip()
        if result.returncode != 0 or not song_artist:
            return None  # Return None if no song is playing or an error occurred
        return song_artist
    except Exception as e:
        return None

# Function to generate scrolling text with fixed length
def scroll_text(text, length=SCROLL_TEXT_LENGTH):
    text = text.ljust(length)  # Ensure the text is padded to the desired length
    scrolling_text = text + ' ' + text[:length]  # Add space and repeat start for scrolling effect
    
    for i in range(len(scrolling_text) - length):
        yield scrolling_text[i:i + length]  # Use a generator to yield scrolling parts

def marquee(text, width=SCROLL_TEXT_LENGTH, delay=REFRESH_INTERVAL):
    padded_text = text + " " * width
    for i in range(len(padded_text) - width + 1):
        display_text = padded_text[i:i + width]
        yield display_text

if __name__ == "__main__":
    scroll_generator = None
    haveReset = True
    last = ""
    combined = ""
    scrolled_text = TEXT_WHEN_STOPPED

    while True:
        output = {}
        
        try:
            # Get the player status and song title
            status = get_player_status()
            song = get_current_song()
            artist = get_current_artist()
            if isinstance(song, str) and isinstance(artist, str):
                combined = song + " -- " + artist

            if status == "paused":
                scrolled_text = combined[:SCROLL_TEXT_LENGTH]

            # Get the glyph based on player status
            glyph = GLYPHS.get(status, DEFAULT_GLYPH)

            if combined and status != "paused":
                if len(combined) > SCROLL_TEXT_LENGTH:  # Adjusted for fixed glyph space
                    if scroll_generator is None:
                        scroll_generator = marquee(combined)  # Initialize the generator
                    try:
                        scrolled_text = next(scroll_generator)
                    except StopIteration:
                        haveReset = True
                        scroll_generator = marquee(combined)
                        scrolled_text = next(scroll_generator)
                else:
                    scrolled_text = combined.ljust(SCROLL_TEXT_LENGTH)  # Ensure the song title is padded
                    scroll_generator = None
            # else:
                # scrolled_text = TEXT_WHEN_STOPPED.ljust(SCROLL_TEXT_LENGTH)  # Ensure fixed length when stopped

            # Combine glyph and song text with a fixed space
            output['text'] = f"<span font_family='{GLYPH_FONT_FAMILY}'>{glyph}</span> {scrolled_text}"

        except Exception as e:
            output['text'] = f" Error: {str(e)}".ljust(SCROLL_TEXT_LENGTH + 2)  # Show error with stop symbol

        # Print the JSON-like output
        print(json.dumps(output), end='\n')
        if haveReset:
            time.sleep(REFRESH_INTERVAL * 5)
            haveReset = False

        time.sleep(REFRESH_INTERVAL)

