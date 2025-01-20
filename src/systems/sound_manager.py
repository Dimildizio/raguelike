import pygame as pg
import random
from constants import *


class SoundManager:
    def __init__(self, sound_path):
        pg.mixer.init()
        self.music_folder = sound_path
        self.music_files = [f for f in self.music_folder.glob("*.mp3")]
        self.current_track = None
        self.normal_volume = 0.2  # 20% volume normally
        self.lowered_volume = 0.05  # 5% volume during narration
        self.is_narrating = False
        # Set up music channel
        pg.mixer.music.set_volume(self.normal_volume)
        # Create a channel for future TTS narration
        self.narration_queue = []
        self.narration_channel = pg.mixer.Channel(1)
        self.sfx_channel = pg.mixer.Channel(2)

        self.hit_sound = pg.mixer.Sound(SOUNDS["HIT"])
        self.hit_sound.set_volume(0.2)

        self.start_music()

    def start_music(self):
        """Start playing music tracks"""
        if not self.music_files:
            return

        # Shuffle the playlist
        random.shuffle(self.music_files)
        self.play_next_track()

    def play_next_track(self):
        """Play the next track in the playlist"""
        if not self.music_files:
            return

        # Get next track
        next_track = self.music_files.pop(0)
        # Add it back to the end of the playlist
        self.music_files.append(next_track)

        try:
            pg.mixer.music.load(str(next_track))
            pg.mixer.music.play(fade_ms=2000)  # 2 second fade in
            self.current_track = next_track

            # Set up event for track end
            pg.mixer.music.set_endevent(pg.USEREVENT + 1)

        except Exception as e:
            print(f"Error playing music track {next_track}: {e}")

    def update(self):
        """Check audio states and handle queued narrations"""
        # Check music
        if not pg.mixer.music.get_busy():
            self.play_next_track()

        # Check narration
        if self.is_narrating and not self.narration_channel.get_busy():
            self.is_narrating = False
            # Play next queued narration if any
            if self.narration_queue:
                next_sound = self.narration_queue.pop(0)
                self.play_narration(next_sound)
            else:
                self.stop_narration()

    def start_narration(self):
        """Prepare for TTS narration by lowering music volume"""
        self.is_narrating = True
        pg.mixer.music.set_volume(self.lowered_volume)

    def stop_narration(self):
        """Return music volume to normal after narration"""
        self.is_narrating = False
        pg.mixer.music.set_volume(self.normal_volume)

    def play_narration(self, sound):
        """Play a TTS narration sound"""
        if self.is_narrating:
            self.narration_queue.append(sound)
        else:
            self.start_narration()
            self.narration_channel.play(sound, loops=0)
            self.is_narrating = True

    def play_hit_sound(self):
        """Play the hit sound effect"""
        self.sfx_channel.play(self.hit_sound)

    def stop_all(self):
        """Stop all audio"""
        pg.mixer.music.stop()
        self.narration_channel.stop()
