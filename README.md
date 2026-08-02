# keyboards
Schematics, pcbs, layout files for all my keyboard projects

## Structure

- `design/` — original keyboard designs, one folder per board with
  `layout/` (KLE, keymap, VIA), `pcb/` (KiCad), `case/` (3DP CAD), and
  `firmware/` (QMK/VIA builds) inside
  - [`gemini/`](design/gemini/) — split staggered 40% that docks into a regular 40%
- `commissions/` — VIA/layout files for boards built for others
- `docs/` — GitHub Pages site with interactive design docs, deployed by
  [`.github/workflows/pages.yml`](.github/workflows/pages.yml) on every push
  to `main` that touches `docs/` (one-time setup: Settings → Pages → Source →
  GitHub Actions)
