"""Synthesise the 10s intro sting (no samples needed). Usage: python3 audio.py out.wav"""
import math, random, struct, sys, wave

SR, DUR = 44100, 10.0
FLIPS = [2.0, 2.9, 3.8, 4.7]          # keep in sync with CFG.flips in intro.html
N = int(SR * DUR)
random.seed(4)
L = [0.0] * N; R = [0.0] * N

def add(t0, dur, fn, gain=1.0, pan=0.0):
    i0 = int(t0 * SR)
    for i in range(int(dur * SR)):
        if i0 + i >= N: break
        v = fn(i / SR) * gain
        L[i0 + i] += v * (1 - max(0, pan)); R[i0 + i] += v * (1 + min(0, pan))

def env(t, a, d):                       # fast attack, exponential decay
    return min(1, t / a) * math.exp(-t / d)

# warm pad: two detuned fifths rising in level, filtered by slow swell
def pad(t):
    swell = min(1, t / 8.0) ** 1.6 * (1 - min(1, max(0, (t - 9.3) / .7)))
    return swell * (math.sin(2*math.pi*98*t) + .6*math.sin(2*math.pi*147.3*t) + .4*math.sin(2*math.pi*196.4*t)) * .12
add(0, DUR, pad)

# soft tick on every logo change, pitched up each time
for k, f in enumerate(FLIPS):
    hz = 660 * (1.25 ** k)
    add(f, .35, lambda t, hz=hz: env(t, .002, .05) * math.sin(2*math.pi*hz*t) * .30, pan=(-.3 if k % 2 else .3))
    add(f, .08, lambda t: env(t, .001, .012) * (random.random() * 2 - 1) * .25)

# opening sparkle
add(.4, 1.4, lambda t: env(t, .01, .5) * math.sin(2*math.pi*1318.5*t) * .12, pan=.2)

# riser into the resolve
def riser(t):
    k = t / 3.0
    hz = 300 + 1500 * k * k
    return k * k * (math.sin(2*math.pi*hz*t) * .06 + (random.random() * 2 - 1) * .05)
add(5.4, 3.0, riser)

# resolve: low hit + major chord chime (C5 E5 G5 C6)
add(8.0, 1.6, lambda t: env(t, .004, .35) * math.sin(2*math.pi*55*t) * .55)
for hz in (523.25, 659.25, 783.99, 1046.5):
    add(8.95, 1.1, lambda t, hz=hz: env(t, .004, .45) * math.sin(2*math.pi*hz*t) * .13, pan=(hz % 3 - 1) * .2)

# fade in/out, normalise to -3 dB
for i in range(N):
    t = i / SR; g = min(1, t / .25) * (1 - min(1, max(0, (t - 9.6) / .4))); L[i] *= g; R[i] *= g
pk = max(max(map(abs, L)), max(map(abs, R))) or 1; s = .7 / pk
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(b''.join(struct.pack('<hh', int(L[i]*s*32767), int(R[i]*s*32767)) for i in range(N)))
