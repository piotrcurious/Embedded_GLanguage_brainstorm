# EGL (Embedded Graphics Language) Specification v1.5

EGL is a compact, stack-based graphics language designed for high-performance serial execution. It is Turing-complete and optimized for interactive UI, demoscene effects, and tile-based games.

## Game-Centric Commands (New in v1.5)
- `CL(color)`: **Clear**: Fill the active surface with `color`.
- `TM(tid, aid, cols, rows, tw, th, [ox, oy])`: **Tilemap**: Render a tilemap using texture buffer `tid` and array `aid`. `cols/rows` are dimensions, `tw/th` are tile size. Optional `ox/oy` for scrolling.
- `HC(x1, y1, w1, h1, x2, y2, w2, h2)`: **Hit Collision**: Returns 1 in `$result` if two AABB rectangles collide, 0 otherwise.
- `DB()`: **Debug**: Dump current variable state and array names to Serial.

## Interactivity & Events
- `HZ(id, x, y, w, h, func)`: Define a clickable hit zone.
- `MC(x, y, btn)`, `KC(src, key)`: Inject Mouse/Key events.
- `DE()`: Dispatch events and trigger callbacks (e.g., `:ON_KEY`).
- `SA()`: Check if serial input is available (returns in `$result`).

## Graphics & Rendering
- `S(w, h, [bg])`: Initialize main surface (Double Buffered).
- `FB()` / `VS()`: Flip Buffer and Wait Sync.
- `P(id, [w, h])`: Define/switch to an off-screen buffer (supports Nesting).
- `DX(id, x, y, [rot], [scale], [alpha], [sx, sy, sw, sh])`: Advanced blit.
- `B(x, y, w, h, c1, c2, [dir])`, `BX(x, y, w, h)`: Gradient/Fast Rectangle.
- `K(color, [width])`, `F(color)`: Style settings.
- `M(x, y)`, `L(x, y)`, `C(r)`, `O(rx, ry)`, `G(x1, y1, ...)`, `T(text)`: Primitives.
- `Z(x, y, w, h)`: Clipping zone.
- `[` / `]`: Push/Pop graphics state.

## Control Flow & Logic
- **Variables:** `$var = expr;` (Global/Local scoping).
- **Functions:** `:name(p1, p2) { body }` / `!name(a1, a2);`.
- **Arrays:** `AA(id, size)`, `AV(id, idx, val)`, `AG(id, idx)`.
- **Loops:** `@($v, s, e, step) { body }` (For); `WH(expr) { body }` (While).
- **Conditionals:** `?(expr) { t } : { f }`.

## Syntax & Errors
EGL v1.5 includes line-context error reporting. Every command must end with a semicolon `;` or newline. Comments start with `#`.
