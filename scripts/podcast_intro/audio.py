"""Synthesise the 10s intro sting: trap/gangster-rap drums + 808, spaghetti-western guitar and whistle.
No samples. Usage: python3 audio.py out.wav
Beat grid: 133.33 BPM (beat = .45s) starting at t=.2s, so logo flips (2.0/2.9/3.8/4.7) and the boom (7.4) land on beats."""
import math, random, struct, sys, wave

SR, DUR = 44100, 10.0
FLIPS = [2.0, 2.9, 3.8, 4.7]          # keep in sync with CFG.flips in intro.html
T_BOOM = 7.4                          # keep in sync with T_BOOM
BEAT, G0 = .45, .2
N = int(SR * DUR)
random.seed(4)
L = [0.0] * N; R = [0.0] * N
TAU = 2 * math.pi

def put(t0, samples, gain=1.0, pan=0.0):
    i0 = int(t0 * SR); gl, gr = gain * (1 - max(0, pan)), gain * (1 + min(0, pan))
    for i, v in enumerate(samples):
        j = i0 + i
        if j >= N: break
        L[j] += v * gl; R[j] += v * gr

def gen(dur, fn): return [fn(i / SR) for i in range(int(dur * SR))]
def env(t, a, d): return min(1, t / a) * math.exp(-t / d)
def beat(n): return G0 + n * BEAT

# ---- drums ---------------------------------------------------------------
def kick808(t0, note, dur=.9, gain=.8):                       # sub with a quick pitch drop, soft-clipped
    ph = [0.0]
    def f(t):
        hz = note * (1 + 1.6 * math.exp(-t / .035)); ph[0] += TAU * hz / SR
        return math.tanh(1.8 * math.sin(ph[0])) * env(t, .003, dur * .45)
    put(t0, gen(dur, f), gain)
def snare(t0, gain=.5, pan=0):
    put(t0, gen(.35, lambda t: ((random.random() * 2 - 1) * env(t, .001, .07) + math.sin(TAU * 190 * t) * env(t, .001, .05) * .5)), gain, pan)
def clap(t0, gain=.45):
    for d in (0, .012, .024):
        put(t0 + d, gen(.22, lambda t: (random.random() * 2 - 1) * env(t, .001, .05)), gain * .6)
def hat(t0, gain=.14, open_=False, pan=0):
    prev = [0.0]
    def f(t):
        x = random.random() * 2 - 1; y = x - prev[0]; prev[0] = x                  # crude high-pass
        return y * env(t, .0008, .18 if open_ else .022)
    put(t0, gen(.3 if open_ else .06, f), gain, pan)

# ---- plucked guitar (Karplus-Strong) with slapback delay ------------------
def pluck(hz, dur=.9, bright=.5, decay=.9965):
    n = max(2, int(SR / hz)); buf = [(random.random() * 2 - 1) * (1 - bright) + (random.random() * 2 - 1) * bright for _ in range(n)]
    out = []; k = 0
    for _ in range(int(dur * SR)):
        a = buf[k]; b = buf[(k + 1) % n]; v = (a + b) * .5 * decay; buf[k] = v; out.append(a); k = (k + 1) % n
    return [x * min(1, i / 60) * max(0, 1 - i / (dur * SR)) ** .6 for i, x in enumerate(out)]
def guitar(t0, hz, dur=.7, gain=.32, pan=-.35):
    s = pluck(hz, dur)
    put(t0, s, gain, pan); put(t0 + .15, s, gain * .35, -pan); put(t0 + .30, s, gain * .14, pan)   # slapback echo
def strum(t0, notes, gain=.3, spread=.022, dur=1.4):
    for k, hz in enumerate(notes): guitar(t0 + k * spread, hz, dur, gain, pan=-.2 + .1 * k)

# ---- whistle lead ---------------------------------------------------------
def whistle(t0, hz, dur, gain=.16):
    f = lambda t: (math.sin(TAU * hz * t + 3.5 * math.sin(TAU * 5.5 * t) * min(1, t / .25)) * .85 + math.sin(TAU * hz * 2 * t) * .12) * min(1, t / .04) * min(1, (dur - t) / .08) * (1 + .1 * math.sin(TAU * 5.5 * t))
    put(t0, gen(dur, f), gain, .25)

A2, C3, D3, E3, G3, A3, C4, E4 = 110.0, 130.81, 146.83, 164.81, 196.0, 220.0, 261.63, 329.63
CS4 = 277.18

# ---- arrangement -----------------------------------------------------------
# intro bar (0.2 - 2.0): lone twangy guitar, a single 808 on the downbeat
guitar(beat(0), A2, 1.2, .38); guitar(beat(1.5), E3, .6); guitar(beat(2), A3, .6); guitar(beat(3), G3, .7)
kick808(beat(0), 55, 1.4, .55)

RIFF = [  # eighth-note steps per bar: (step, hz)
    [(0, A2), (2, C3), (3, D3), (4, E3), (6, D3), (7, C3)],
    [(0, A2), (2, C3), (4, E3), (5, G3), (6, E3), (7, D3)],
    [(0, A2), (1, A2), (2, C3), (3, D3), (4, E3), (5, G3), (6, A3), (7, G3)],
]
for bar in range(3):                                           # three main bars: 2.0, 3.8, 5.6
    b0 = 4 + bar * 4
    for st, hz in RIFF[bar]: guitar(beat(b0) + st * BEAT / 2, hz, .5, .30)
    kick808(beat(b0), 55, 1.0); kick808(beat(b0 + 2.5), 55, .5, .7); kick808(beat(b0 + 3.25), 65.4, .45, .7)
    clap(beat(b0 + 2)); snare(beat(b0 + 2), .35)
    for h in range(8):                                         # trap hats with a roll on the last beat
        hat(beat(b0) + h * BEAT / 2, .12 if h % 2 else .16, pan=-.2 if h % 2 else .2)
    for r in range(4): hat(beat(b0 + 3.5) + r * BEAT / 8, .09 + .02 * r)
    hat(beat(b0 + 1.5), .14, True)
# last bar builds: snare roll into the boom
for r in range(14): snare(beat(12) + r * (BEAT / 4) * (1 - r * .03), .12 + .03 * r)

# whistle melody
for t, hz, d in [(4.25, 659.3, .5), (4.8, 587.3, .3), (5.15, 523.3, .3), (5.5, 440.0, .9), (6.55, 659.3, .4), (7.0, 880.0, .38)]:
    whistle(t, hz, d)

# flip ticks (softer than before; the beat carries the rhythm now)
for k, f in enumerate(FLIPS):
    put(f, gen(.25, lambda t, hz=660 * 1.25 ** k: env(t, .002, .05) * math.sin(TAU * hz * t)), .14, -.3 if k % 2 else .3)

# riser noise into the boom
def riser(t):
    k = t / 2.8; return k * k * (math.sin(TAU * (300 + 1500 * k * k) * t) * .05 + (random.random() * 2 - 1) * .05)
put(4.6, gen(2.8, riser))

# boom + fireworks
kick808(T_BOOM, 49, 1.8, 1.0)
put(T_BOOM, gen(.6, lambda t: (random.random() * 2 - 1) * env(t, .002, .14)), .55)             # crash
strum(T_BOOM, [A2, E3, A3, C4], .34, .018, 1.2)                                                # big open-A hit
for bt in (7.62, 7.8, 8.0, 8.2, 8.45, 8.6, 8.75):
    put(bt, gen(.6, lambda t: (random.random() * 2 - 1) * env(t, .002, .09)), .2, random.uniform(-.7, .7))
    put(bt, gen(.4, lambda t, hz=2200 + 900 * random.random(): math.sin(TAU * hz * t) * env(t, .002, .05)), .09, random.uniform(-.5, .5))
# outro groove (half-bar) and final western strum on the wordmark
kick808(beat(18), 55, .6, .7); clap(beat(20)); kick808(beat(21.5), 55, .5, .6)
for h in range(6): hat(beat(18) + h * BEAT / 2, .1)
strum(8.95, [A2, E3, A3, CS4, E4], .36, .03, 1.5)
whistle(9.1, 880.0, .8, .12)

# fade in/out, soft limiter, normalise
for i in range(N):
    t = i / SR; g = min(1, t / .15) * (1 - min(1, max(0, (t - 9.55) / .45)))
    L[i] = math.tanh(L[i] * 1.2) * g; R[i] = math.tanh(R[i] * 1.2) * g
pk = max(max(map(abs, L)), max(map(abs, R))) or 1; s = .85 / pk
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<hh', int(L[i] * s * 32767), int(R[i] * s * 32767)) for i in range(N)))
