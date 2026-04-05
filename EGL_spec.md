# EGL (Embedded Graphics Language) Specification v1.6

EGL is a compact, stack-based graphics language designed for high-performance serial execution. It is Turing-complete and optimized for interactive UI, demoscene effects, and games.

## System & Utility (New in v1.6)
- `RN(min, max)`: **Random**: Returns a random integer between `min` and `max` in `$result`.
- `SR(seed)`: **Seed**: Set the seed for the random number generator.
- `MS()`: **Millis**: Returns current system milliseconds in `$result`.
- `LI(id, path)`: **Load Image**: Load an external PNG/JPEG/etc. file into buffer `id`.
- `ST(str, start, [len])`: **Substring**: Extracts a substring from `str` starting at `start`. Store in `$result`.

## Game Engine Primitives
- `CL(color)`: **Clear**: Fill the active surface with `color`.
- `TM(tid, aid, cols, rows, tw, th, [ox, oy])`: **Tilemap**: Render tiles using buffer `tid` and map array `aid`.
- `HC(x1, y1, w1, h1, x2, y2, w2, h2)`: **Hit Collision**: Returns 1 in `$result` if AABBs collide.
- `DB()`: **Debug**: Dump current state to Serial.

## Interactivity & Events
- `HZ(id, x, y, w, h, func)`: Define a clickable hit zone.
- `MC(x, y, btn)`, `KC(src, key)`: Inject events.
- `DE()`: Dispatch events and trigger callbacks (e.g., `:ON_KEY`).
- `SA()`: Check if serial input is available.

## Graphics & Rendering
- `S(w, h, [bg])`: Initialize main surface (Double Buffered).
- `FB()` / `VS()`: Flip Buffer and Wait Sync.
- `P(id, [w, h])`: Define/switch to an off-screen buffer.
- `DX(id, x, y, [rot], [scale], [alpha], [sx, sy, sw, sh])`: Advanced blit.
- `B(x, y, w, h, c1, c2, [dir])`, `BX(x, y, w, h)`: Gradient/Fast Rectangle.
- `K(color, [width])`, `F(color)`: Style settings.
- `M(x, y)`, `L(x, y)`, `C(r)`, `O(rx, ry)`, `G(x1, y1, ...)`, `T(text)`: Primitives.
- `Z(x, y, w, h)`: Clipping zone.
- `[` / `]`: Push/Pop graphics state.

## Control Flow & Logic
- **Variables:** `$var = expr;`.
- **Functions:** `:name(p1) { body }` / `!name(a1);`.
- **Arrays:** `AA(id, size)`, `AV(id, idx, val)`, `AG(id, idx)`.
- **Loops:** `@($v, s, e, step) { body }` (For); `WH(expr) { body }` (While).
- **Conditionals:** `?(expr) { t } : { f }`.
