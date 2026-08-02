# Gemini — default keymap (draft 2)

Design goal: **every key on a full-size (104-key) keyboard is typeable**,
and the common ones fall in comfortable places. This is the recommended
default — once the board runs QMK/VIA every layer is user-remappable.

Four layers:

| Layer  | Activation                          | Contents                          |
|--------|-------------------------------------|-----------------------------------|
| Base   | —                                   | alphas, core punctuation, mods    |
| Raise  | hold right `Fn`                     | digits, symbols, arrows, Del      |
| Lower  | hold left `Space`                   | F-keys, nav, media, PrtSc cluster |
| Adjust | hold both (`Fn` + left `Space`)     | numpad, RGB, bootloader           |

Dual-role keys (QMK mod-tap / layer-tap):

| Key (base position)   | Tap     | Hold      |
|-----------------------|---------|-----------|
| R2 leftmost           | Esc     | Ctrl      |
| Left Space (2.75u)    | Space   | Lower     |
| Right `Fn` (1.25u)    | —       | Raise     |

## Base

```
| Tab  | Q | W | E | R | T ‖ Y | U | I | O | P | Bksp |
| Esc⌃ | A | S | D | F | G ‖ H | J | K | L | ; | Ent  |
| Shift  | Z | X | C | V | B ‖ N | M | , | . | Shift |
| Ctl |Gui|Alt |  Spc/Lwr  ‖   Space  | Fn | Alt |Ctl |
```

## Raise (hold `Fn`) — digits, symbols, arrows

```
|  `   | 1 | 2 | 3 | 4 | 5 ‖ 6 | 7 | 8 | 9 | 0 | Del |
| Ctrl | - | = | [ | ] | \ ‖ ← | ↓ | ↑ | → | ' | Ent |
| Shift  |   |   |   |   |  ‖   |   |   | / | Shift |
| Ctl |Gui|Alt |   Space   ‖   Space  |(Fn)| Alt |Ctl |
```

- Digits mirror the standard number-row split (1–5 left, 6–0 right).
- Arrows vim-style on `HJKL`; `'` stays on the pinky where a 60% has it.
- `/` on `.` — so `?` is naturally `Raise+Shift+.`.
- Symbols `-=[]\` on the left home row in number-row order.

## Lower (hold left `Space`) — F-keys, nav, media

```
| F12  |F1 |F2 |F3 |F4 |F5 ‖ F6 | F7 | F8 | F9 |F10| F11 |
| Caps |Ins|PSc|SLk|Pse|   ‖ Hom|PgD |PgU |End |   | Ent  |
| Shift  |   |   |   |   |  ‖ Prv|Vo- |Vo+ |Nxt | Play  |
| Ctl |Gui|Alt | (held)    ‖   Space  | App|RGui|Ctl |
```

- F1–F10 mirror the digit positions; F11/F12 close the row ends.
- Nav cluster (Home/PgDn/PgUp/End) sits under the Raise arrows — same
  fingers, one layer over.
- Ins / PrtSc / ScrLk / Pause across the left home row.
- `App` (menu) and right `GUI` on the right thumb keys.

## Adjust (hold `Fn` + left `Space`) — numpad, board controls

```
| Boot |RGB|Hue|Sat|Val|   ‖NmLk| P7 | P8 | P9 | P- | Del  |
| Ctrl |   |   |   |   |   ‖ P/ | P4 | P5 | P6 | P+ | PEnt |
| Shift  |   |   |   |   |  ‖ P* | P1 | P2 | P3 | Shift |
| Ctl |Gui|Alt | (held)    ‖    P0    |(Fn)| P. |Ctl |
```

- Numpad digits as a 3×3 grid on `UIO`/`JKL`/`M,.` matching a real numpad;
  `P0` big on the right spacebar, `P.` beside it.
- `Boot` = QK_BOOT (flash mode) — needs three keys held plus the far
  corner, effectively impossible to hit by accident.

## Coverage audit — full-size (104-key) parity

| Full-size key group                     | Where it lives on Gemini            |
|-----------------------------------------|-------------------------------------|
| A–Z, `,` `.` `;`, Tab, Enter, Space     | Base                                |
| Shift ×2, Ctrl ×2, Alt ×2, GUI (L)      | Base                                |
| Esc                                     | Base (tap of Esc/Ctrl)              |
| 1–0, `` ` `` `-` `=` `[` `]` `\` `'` `/`| Raise                               |
| Arrows, Delete                          | Raise                               |
| F1–F12, Caps Lock                       | Lower                               |
| Ins, PrtSc, ScrLk, Pause                | Lower                               |
| Home, End, PgUp, PgDn                   | Lower                               |
| App/Menu, GUI (R)                       | Lower                               |
| Numpad 0–9, `.` `/` `*` `-` `+`, Enter  | Adjust                              |
| Num Lock                                | Adjust                              |
| Media (not on 104, bonus)               | Lower                               |

Every 104-key legend is reachable; nothing requires more than two held
keys (Adjust = both thumbs, then the target).

## Open items

- [ ] Left-hand-only shortcuts layer for mouse-in-right-hand use?
- [ ] Home-row mods as an alternate keymap once the board exists — easy to
      A/B in firmware, no hardware impact.
- [ ] Split-mode niceties: swap which thumb triggers Raise/Lower per user
      preference in VIA.
