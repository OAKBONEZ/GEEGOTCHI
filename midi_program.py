#!/usr/bin/env python3
"""
MIDI Program - Generate, compose, and export MIDI sequences.
Requires: mido (pip install mido)
Optional: python-rtmidi (pip install python-rtmidi) for live playback
"""

import argparse
import random
import sys
import time

try:
    import mido
    from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo
except ImportError:
    print("Error: mido not installed. Run: pip install mido")
    sys.exit(1)


# ── Music theory constants ─────────────────────────────────────────────────────

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

SCALES = {
    'major':        [0, 2, 4, 5, 7, 9, 11],
    'minor':        [0, 2, 3, 5, 7, 8, 10],
    'pentatonic':   [0, 2, 4, 7, 9],
    'blues':        [0, 3, 5, 6, 7, 10],
    'dorian':       [0, 2, 3, 5, 7, 9, 10],
    'chromatic':    list(range(12)),
}

CHORD_TYPES = {
    'maj':  [0, 4, 7],
    'min':  [0, 3, 7],
    'dim':  [0, 3, 6],
    'aug':  [0, 4, 8],
    'maj7': [0, 4, 7, 11],
    'min7': [0, 3, 7, 10],
    'dom7': [0, 4, 7, 10],
}

GM_INSTRUMENTS = {
    0:   'Acoustic Grand Piano',
    4:   'Electric Piano 1',
    24:  'Acoustic Guitar (nylon)',
    25:  'Acoustic Guitar (steel)',
    32:  'Acoustic Bass',
    40:  'Violin',
    48:  'String Ensemble 1',
    56:  'Trumpet',
    64:  'Soprano Sax',
    73:  'Flute',
    80:  'Square Wave Synth',
    81:  'Saw Wave Synth',
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def note_name_to_midi(name: str, octave: int = 4) -> int:
    """Convert note name + octave to MIDI number (middle C = C4 = 60)."""
    name = name.upper().replace('♭', 'b')
    semitone = NOTES.index(name)
    return (octave + 1) * 12 + semitone


def midi_to_note_name(midi_num: int) -> str:
    octave = (midi_num // 12) - 1
    name = NOTES[midi_num % 12]
    return f"{name}{octave}"


def build_scale(root_midi: int, scale: str, octaves: int = 2) -> list[int]:
    """Return MIDI note numbers for a scale starting at root_midi."""
    intervals = SCALES.get(scale, SCALES['major'])
    notes = []
    for oct_offset in range(octaves):
        for interval in intervals:
            n = root_midi + oct_offset * 12 + interval
            if n <= 127:
                notes.append(n)
    return notes


def build_chord(root_midi: int, chord_type: str = 'maj') -> list[int]:
    intervals = CHORD_TYPES.get(chord_type, CHORD_TYPES['maj'])
    return [root_midi + i for i in intervals if root_midi + i <= 127]


def ticks_per_beat(midi_file: MidiFile) -> int:
    return midi_file.ticks_per_beat


# ── Sequence builders ──────────────────────────────────────────────────────────

def add_melody(track: MidiTrack, notes: list[int], tpb: int,
               note_duration: float = 0.5, velocity: int = 80,
               channel: int = 0) -> None:
    """Append a monophonic melody to track. note_duration in beats."""
    ticks = int(tpb * note_duration)
    for note in notes:
        track.append(Message('note_on',  channel=channel, note=note, velocity=velocity, time=0))
        track.append(Message('note_off', channel=channel, note=note, velocity=0,        time=ticks))


def add_chord_progression(track: MidiTrack, chords: list[list[int]], tpb: int,
                           beats_per_chord: int = 4, velocity: int = 70,
                           channel: int = 0) -> None:
    """Append a chord progression (list of note lists) to track."""
    ticks = tpb * beats_per_chord
    for chord in chords:
        # Note-on for all notes simultaneously
        for i, note in enumerate(chord):
            track.append(Message('note_on', channel=channel, note=note,
                                 velocity=velocity, time=0))
        # Note-off: first note carries the time, rest are 0
        for i, note in enumerate(chord):
            track.append(Message('note_off', channel=channel, note=note,
                                 velocity=0, time=ticks if i == 0 else 0))


def add_drum_pattern(track: MidiTrack, tpb: int, bars: int = 4) -> None:
    """Add a basic 4/4 kick-snare-hihat pattern on MIDI ch 9."""
    kick, snare, hihat = 36, 38, 42
    step = tpb // 2  # eighth notes

    pattern = [
        (kick,  100, 0),
        (hihat,  60, 0),
        (hihat,  50, step),
        (snare,  90, 0),
        (hihat,  60, 0),
        (hihat,  50, step),
        (kick,  100, 0),
        (kick,   80, step),
        (hihat,  60, 0),
        (snare,  90, 0),
        (hihat,  60, 0),
        (hihat,  50, step),
    ]

    for _ in range(bars):
        first = True
        for note, vel, delay in pattern:
            t = delay if not first else 0
            first = False
            track.append(Message('note_on',  channel=9, note=note, velocity=vel,  time=t))
            track.append(Message('note_off', channel=9, note=note, velocity=0,    time=step))


# ── Random melody generator ────────────────────────────────────────────────────

def generate_random_melody(root: str, octave: int, scale: str,
                            length: int = 16, seed: int | None = None) -> list[int]:
    if seed is not None:
        random.seed(seed)
    root_midi = note_name_to_midi(root, octave)
    pool = build_scale(root_midi, scale, octaves=2)
    melody = []
    prev = random.choice(pool)
    for _ in range(length):
        # Weighted towards stepwise motion
        neighbors = [n for n in pool if abs(n - prev) <= 3] or pool
        prev = random.choice(neighbors)
        melody.append(prev)
    return melody


# ── MIDI file creators ─────────────────────────────────────────────────────────

def create_simple_song(output_path: str, bpm: int = 120, root: str = 'C',
                       octave: int = 4, scale: str = 'major',
                       instrument: int = 0, seed: int | None = None) -> None:
    mid = MidiFile(ticks_per_beat=480)
    tpb = mid.ticks_per_beat
    tempo = bpm2tempo(bpm)

    # Track 0 — tempo + time signature
    t0 = MidiTrack()
    mid.tracks.append(t0)
    t0.append(MetaMessage('set_tempo', tempo=tempo, time=0))
    t0.append(MetaMessage('time_signature', numerator=4, denominator=4,
                          clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
    t0.append(MetaMessage('track_name', name='Tempo', time=0))

    # Track 1 — melody
    t1 = MidiTrack()
    mid.tracks.append(t1)
    t1.append(MetaMessage('track_name', name='Melody', time=0))
    t1.append(Message('program_change', channel=0, program=instrument, time=0))
    melody = generate_random_melody(root, octave, scale, length=32, seed=seed)
    add_melody(t1, melody, tpb, note_duration=0.5, velocity=85)
    t1.append(MetaMessage('end_of_track', time=0))

    # Track 2 — chord backing
    t2 = MidiTrack()
    mid.tracks.append(t2)
    t2.append(MetaMessage('track_name', name='Chords', time=0))
    t2.append(Message('program_change', channel=1, program=48, time=0))  # strings
    root_midi = note_name_to_midi(root, octave - 1)
    chord_type = 'maj' if scale == 'major' else 'min'
    progression = [
        build_chord(root_midi, chord_type),
        build_chord(root_midi + 5, chord_type),
        build_chord(root_midi + 7, chord_type),
        build_chord(root_midi + 5, chord_type),
    ] * 2
    add_chord_progression(t2, progression, tpb, beats_per_chord=4, velocity=60, channel=1)
    t2.append(MetaMessage('end_of_track', time=0))

    # Track 3 — drums
    t3 = MidiTrack()
    mid.tracks.append(t3)
    t3.append(MetaMessage('track_name', name='Drums', time=0))
    add_drum_pattern(t3, tpb, bars=8)
    t3.append(MetaMessage('end_of_track', time=0))

    mid.save(output_path)
    print(f"Saved: {output_path}")
    _print_song_info(mid, bpm, root, scale, instrument, melody)


def create_scale_exercise(output_path: str, root: str = 'C', octave: int = 4,
                          scale: str = 'major', bpm: int = 100,
                          instrument: int = 0) -> None:
    mid = MidiFile(ticks_per_beat=480)
    tpb = mid.ticks_per_beat

    t0 = MidiTrack()
    mid.tracks.append(t0)
    t0.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))

    t1 = MidiTrack()
    mid.tracks.append(t1)
    t1.append(Message('program_change', channel=0, program=instrument, time=0))
    root_midi = note_name_to_midi(root, octave)
    scale_notes = build_scale(root_midi, scale, octaves=2)
    # Up then down
    add_melody(t1, scale_notes + list(reversed(scale_notes)), tpb,
               note_duration=0.5, velocity=80)
    t1.append(MetaMessage('end_of_track', time=0))

    mid.save(output_path)
    print(f"Saved scale exercise: {output_path}")


def create_chord_sheet(output_path: str, root: str = 'C', octave: int = 4,
                       bpm: int = 80, instrument: int = 0) -> None:
    mid = MidiFile(ticks_per_beat=480)
    tpb = mid.ticks_per_beat

    t0 = MidiTrack()
    mid.tracks.append(t0)
    t0.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))

    t1 = MidiTrack()
    mid.tracks.append(t1)
    t1.append(Message('program_change', channel=0, program=instrument, time=0))
    root_midi = note_name_to_midi(root, octave)
    chords = [build_chord(root_midi, ct) for ct in CHORD_TYPES]
    add_chord_progression(t1, chords, tpb, beats_per_chord=4, velocity=75)
    t1.append(MetaMessage('end_of_track', time=0))

    mid.save(output_path)
    print(f"Saved chord sheet: {output_path}")


# ── Live playback (optional) ───────────────────────────────────────────────────

def play_midi(path: str) -> None:
    try:
        import mido
        ports = mido.get_output_names()
    except Exception:
        print("No MIDI output ports available. Install python-rtmidi for playback.")
        return

    if not ports:
        print("No MIDI output ports found.")
        return

    port_name = ports[0]
    print(f"Playing via: {port_name}")
    mid = MidiFile(path)
    with mido.open_output(port_name) as port:
        for msg in mid.play():
            port.send(msg)


# ── Info display ───────────────────────────────────────────────────────────────

def _print_song_info(mid: MidiFile, bpm: int, root: str, scale: str,
                     instrument: int, melody: list[int]) -> None:
    inst_name = GM_INSTRUMENTS.get(instrument, f"Program {instrument}")
    print(f"  BPM       : {bpm}")
    print(f"  Key       : {root} {scale}")
    print(f"  Instrument: {inst_name}")
    print(f"  Melody    : {' '.join(midi_to_note_name(n) for n in melody[:8])} ...")
    print(f"  Tracks    : {len(mid.tracks)}")
    total_ticks = max(
        sum(m.time for m in t) for t in mid.tracks if t
    )
    seconds = mido.tick2second(total_ticks, mid.ticks_per_beat, bpm2tempo(bpm))
    print(f"  Duration  : {seconds:.1f}s")


def list_info() -> None:
    print("── Scales ─────────────────────────────────────────────────────")
    for name in SCALES:
        print(f"  {name}")
    print("\n── Chord types ────────────────────────────────────────────────")
    for name, intervals in CHORD_TYPES.items():
        print(f"  {name:6s}  {intervals}")
    print("\n── GM Instruments (sample) ────────────────────────────────────")
    for num, name in GM_INSTRUMENTS.items():
        print(f"  {num:3d}  {name}")
    print("\n── Note names ─────────────────────────────────────────────────")
    print(f"  {', '.join(NOTES)}")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description='MIDI Program — generate and export MIDI files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s song -o my_song.mid --bpm 130 --root A --scale minor
  %(prog)s scale -o c_major.mid --root C --scale major
  %(prog)s chords -o chords.mid --root G
  %(prog)s play my_song.mid
  %(prog)s info
""")

    sub = parser.add_subparsers(dest='command', required=True)

    # song
    p_song = sub.add_parser('song', help='Generate a full song (melody + chords + drums)')
    p_song.add_argument('-o', '--output',     default='song.mid')
    p_song.add_argument('--bpm',              type=int,   default=120)
    p_song.add_argument('--root',             default='C',  help='Root note (C, D, F#, …)')
    p_song.add_argument('--octave',           type=int,   default=4)
    p_song.add_argument('--scale',            default='major', choices=list(SCALES))
    p_song.add_argument('--instrument',       type=int,   default=0,   help='GM program number')
    p_song.add_argument('--seed',             type=int,   default=None, help='Random seed')

    # scale
    p_scale = sub.add_parser('scale', help='Generate a scale exercise')
    p_scale.add_argument('-o', '--output',    default='scale.mid')
    p_scale.add_argument('--bpm',             type=int,   default=100)
    p_scale.add_argument('--root',            default='C')
    p_scale.add_argument('--octave',          type=int,   default=4)
    p_scale.add_argument('--scale',           default='major', choices=list(SCALES))
    p_scale.add_argument('--instrument',      type=int,   default=0)

    # chords
    p_chords = sub.add_parser('chords', help='Generate all chord types for a root note')
    p_chords.add_argument('-o', '--output',   default='chords.mid')
    p_chords.add_argument('--bpm',            type=int,   default=80)
    p_chords.add_argument('--root',           default='C')
    p_chords.add_argument('--octave',         type=int,   default=4)
    p_chords.add_argument('--instrument',     type=int,   default=0)

    # play
    p_play = sub.add_parser('play', help='Play a MIDI file via a local MIDI port')
    p_play.add_argument('file', help='Path to .mid file')

    # info
    sub.add_parser('info', help='List available scales, chords, and GM instruments')

    args = parser.parse_args()

    if args.command == 'song':
        create_simple_song(
            args.output, bpm=args.bpm, root=args.root, octave=args.octave,
            scale=args.scale, instrument=args.instrument, seed=args.seed)
    elif args.command == 'scale':
        create_scale_exercise(
            args.output, root=args.root, octave=args.octave,
            scale=args.scale, bpm=args.bpm, instrument=args.instrument)
    elif args.command == 'chords':
        create_chord_sheet(
            args.output, root=args.root, octave=args.octave,
            bpm=args.bpm, instrument=args.instrument)
    elif args.command == 'play':
        play_midi(args.file)
    elif args.command == 'info':
        list_info()


if __name__ == '__main__':
    main()
