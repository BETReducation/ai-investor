# Podcast intro: prompt template

10 second sting played at the start of every episode. Edit the VARIABLES block, paste the whole prompt into the video generator, and change one variable at a time so you can tell what made the difference.

AI video tools garble logos and small text. Attach the real PNGs from `static/logos/` (Green Square, GCT Square, GCE Square, Arena Square, Green Full) as reference images, and plan on a second pass in CapCut where the real logo is laid over the generated background if the logo comes out wrong.

## Prompt

```
Create a 10 second, 16:9, 4K broadcast-style intro sting for a finance education podcast called "Growth Capital Group". Professional, premium, modern fintech look. Not flashy, not crypto-hype, not stock-footage cliché.

VARIABLES
- Palette: near-black navy background (#060812), brand green (#00d4aa), brand purple (#7c3aed with #a78bfa highlights). Candle red (#ff4d5e) used only inside the charts.
- Pace: [medium / fast]
- Camera: [slow push-in / gentle orbit / locked-off]
- Motion style: [smooth glass UI panels / 3D parallax / flat vector]
- Chart style: [candlesticks / line + area / both]
- Closing frame: [GCG logo centred / GCG logo + tagline "Learn to invest with confidence and clarity"]
- Audio: [rising synth swell and soft tick hits / minimal bass pulse / light percussion + chime]

TIMELINE
0.0-1.5s  Dark navy background with a faint grid and soft green glow. The green GCG logo (from the attached reference) fades in at centre with a subtle light sweep.
1.5-4.0s  The GCG logo morphs in place into the GCT logo, then the GCE logo, then the Arena logo (all attached), about 0.8s each, each transition a clean liquid or particle dissolve in brand colours. Keep every logo exactly as supplied, no redrawn lettering.
2.0-8.0s  Behind and around the logos, green and red candlestick charts draw themselves in smoothly, with thin glowing line overlays, volume bars and faint axis ticks. Green candles up, red candles down, mixed and realistic, no number labels.
3.0-8.0s  Floating glass panels of the platform's data visualisation and tool pages (use the attached screenshots) drift across at different depths, slightly blurred at the edges, gently rotating, never covering the logo.
8.0-9.0s  Everything pulls together toward the centre and the charts fade down to a soft glow.
9.0-10.0s Resolve on the [closing frame]. Hold the last half second still for a clean cut into the episode.

STYLE
Soft depth of field, subtle film grain, rounded modern sans-serif, clean negative space, high contrast, no clutter. Everything stays inside the safe margins.

AVOID
Photographs of people, money, coins, rockets, bull or bear imagery, arrows promising gains, readable price figures, buy or sell language, stock tickers, lens flares, glitch effects, cartoon styling, watermarks, any added text apart from the closing tagline.
```

## Variations to test

1. Pace: fast, with the logo morph compressed into 2.5s and the charts starting earlier.
2. Chart style: candlesticks only vs line + area only.
3. Closing frame: logo only vs logo + tagline.
4. Light version: swap the background for #f5f7ff and use the darker brand greens (#00a882) and purples (#6d28d9).
5. Audio: generate the video silent and add the sound in CapCut, so you can swap music without regenerating.

## Notes

- Keep the charts abstract. No real tickers or readable prices, so the intro stays educational and never reads as a call to buy or sell.
- Once a version works, save the exact prompt and the variable values next to the exported file so the intro can be reproduced.
