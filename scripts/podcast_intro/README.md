# Podcast intro (10s)

Source for the GCG podcast sting. Edit `CFG` at the top of `intro.html` (logo order, timings, wordmark, tagline), and `FLIPS` in `audio.py` if the logo timings change.

```
npm i puppeteer-core            # once, anywhere; point NODE_PATH at its node_modules
node render.js frames 1         # 1 = 1080p, 2 = 4K; writes 300 PNG frames at 30fps
python3 audio.py intro.wav
ffmpeg -framerate 30 -i frames/%04d.png -i intro.wav -c:v libx264 -crf 14 -pix_fmt yuv420p -c:a aac -b:a 256k -shortest intro.mp4
```

`node render.js out 1 2.4,5.5` renders single stills at those times for quick checks. Exports go in `Podcast Recording/Intro/` (git-ignored).

The `shots/` folder (page screenshots used as panels) is git-ignored to keep the repo light. Re-capture them with Puppeteer or drop your own PNGs in, named as in `SHOTS` at the top of `intro.html`.
