import time
import threading
import random
import mido
from mido import Message
from .output_adapter import OutputAdapter

CHORDS = {
    "calm": [[60, 64, 67], [60, 64, 67], [57, 60, 64], [57, 60, 64]],
    "warning": [[64, 67, 71], [65, 69, 72], [64, 67, 71], [57, 60, 64]],
    "alert": "atonal"
}

CHORD_CHANNEL = 2
MELODY_CHANNEL = 1

class MusicOutputAdapter(OutputAdapter):
    def __init__(self):
        try:
            output_names = mido.get_output_names()
            if not output_names:
                raise RuntimeError("No MIDI output ports found!")
            self.port_name = output_names[0]
            self.midi_out = mido.open_output(self.port_name)
            print(f"[MusicOutputAdapter] Opened MIDI output on port: {self.port_name}")
        except Exception as e:
            print("[MusicOutputAdapter] Failed to open MIDI output port:", e)
            self.midi_out = None

        self._stop_event = threading.Event()
        self.lock = threading.Lock()
        self.active_notes = {CHORD_CHANNEL: set(), MELODY_CHANNEL: set()}
        self.threads = []

    def handle_event(self, event):
        final_score = event.get("alert_score", 0)
        print(f"[MusicOutputAdapter] Received alert score: {final_score}")

        if self.midi_out is None:
            print("[MusicOutputAdapter] No MIDI output available.")
            return

        def playback():
            try:
                if final_score >= 9:
                    self.play_random_chords()
                    self.play_melody(severity=10)
                elif final_score >= 6:
                    self.play_chord_progression(CHORDS["warning"])
                    self.play_melody(severity=5)
                else:
                    self.play_chord_progression(CHORDS["calm"])
                    self.play_melody(severity=0)

            except Exception as e:
                print(f"[MusicOutputAdapter] Playback error: {e}")


        t = threading.Thread(target=playback)
        self.threads.append(t)
        t.start()

    def play_chord_progression(self, progression, chord_duration=2, channel=CHORD_CHANNEL):
        try:
            for chord in progression:
                if self._stop_event.is_set():
                    break
                with self.lock:
                    for note in chord:
                        self.midi_out.send(Message('note_on', note=note, velocity=80, channel=channel))
                        self.active_notes[channel].add(note)
                time.sleep(chord_duration)
                with self.lock:
                    for note in chord:
                        self.midi_out.send(Message('note_off', note=note, velocity=0, channel=channel))
                        self.active_notes[channel].discard(note)
                time.sleep(0.1)
        except Exception as e:
            print(f"[MusicOutputAdapter] Error playing chord progression: {e}")

    def play_random_chords(self, duration=6, channel=CHORD_CHANNEL):
        try:
            start = time.time()
            while time.time() - start < duration and not self._stop_event.is_set():
                chord = [random.randint(48, 84) for _ in range(random.choice([3, 4]))]
                with self.lock:
                    for note in chord:
                        self.midi_out.send(Message('note_on', note=note, velocity=100, channel=channel))
                        self.active_notes[channel].add(note)
                time.sleep(random.uniform(0.3, 0.7))
                with self.lock:
                    for note in chord:
                        self.midi_out.send(Message('note_off', note=note, velocity=0, channel=channel))
                        self.active_notes[channel].discard(note)
                time.sleep(0.05)
        except Exception as e:
            print(f"[MusicOutputAdapter] Error playing atonal chords: {e}")

    def play_melody(self, severity=0, duration=6, key_root=60, channel=MELODY_CHANNEL):
        scale_intervals = [0, 2, 4, 5, 7, 9, 11]
        start_time = time.time()

        try:
            while time.time() - start_time < duration and not self._stop_event.is_set():
                if severity <= 0:
                    pattern = [key_root + random.choice(scale_intervals) for _ in range(2)]
                    for note in pattern:
                        if self._stop_event.is_set():
                            break
                        with self.lock:
                            self.midi_out.send(Message('note_on', note=note, velocity=70, channel=channel))
                            self.active_notes[channel].add(note)
                        time.sleep(duration / (2 * len(pattern)))
                        with self.lock:
                            self.midi_out.send(Message('note_off', note=note, velocity=0, channel=channel))
                            self.active_notes[channel].discard(note)
                elif severity >= 10:
                    note = random.randint(48, 84)
                    with self.lock:
                        self.midi_out.send(Message('note_on', note=note, velocity=100, channel=channel))
                        self.active_notes[channel].add(note)
                    time.sleep(random.uniform(0.1, 0.3))
                    with self.lock:
                        self.midi_out.send(Message('note_off', note=note, velocity=0, channel=channel))
                        self.active_notes[channel].discard(note)
                else:
                    interval = random.choice(scale_intervals)
                    octave = random.randint(0, 2)
                    note = key_root + interval + 12 * octave
                    with self.lock:
                        self.midi_out.send(Message('note_on', note=note, velocity=85, channel=channel))
                        self.active_notes[channel].add(note)
                    time.sleep(random.uniform(0.2, 0.6))
                    with self.lock:
                        self.midi_out.send(Message('note_off', note=note, velocity=0, channel=channel))
                        self.active_notes[channel].discard(note)
                time.sleep(0.05)
        except Exception as e:
            print(f"[MusicOutputAdapter] Error playing melody: {e}")

    def stop(self):
        print("[MusicOutputAdapter] Stopping all playback and notes.")
        self._stop_event.set()
        time.sleep(0.1)
        with self.lock:
            for channel, notes in self.active_notes.items():
                for note in notes:
                    try:
                        self.midi_out.send(Message('note_off', note=note, velocity=0, channel=channel))
                    except Exception as e:
                        print(f"[MusicOutputAdapter] Error turning off note {note} on channel {channel}: {e}")
            self.active_notes = {CHORD_CHANNEL: set(), MELODY_CHANNEL: set()}

        for t in self.threads:
            if t.is_alive():
                t.join(timeout=1)
        self.threads.clear()
