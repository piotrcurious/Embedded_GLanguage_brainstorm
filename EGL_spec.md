# EGL (Embedded Graphics Language) Specification v1.7

EGL is a compact, stack-based graphics language designed for high-performance serial execution. It is Turing-complete and optimized for interactive UI, demoscene effects, and games.

## System & Utility (Updated in v1.7)
- `RN(min, max)`: **Random**: Returns a random integer between `min` and `max` in `$result`.
- `SR(seed)`: **Seed**: Set the seed for the random number generator.
- `MS()`: **Millis**: Returns current system milliseconds in `$result`.
- `LI(id, path)`: **Load Image**: Load an external PNG/JPEG/etc. file into buffer `id`.
- `ST(str, start, [len])`: **Substring**: Extracts a substring from `str` starting at `start`. Store in `$result`.
- `FR(fps)`: **Frame Rate**: Set target frames per second for `FB()`.

## Game Engine Primitives
- `CL(color)`: **Clear**: Fill the active surface with `color`.
- `TM(tid, aid, cols, rows, tw, th, [ox, oy])`: **Tilemap**: Render tiles using buffer `tid` and map array `aid`.
- `HC(x1, y1, w1, h1, x2, y2, w2, h2)`: **Hit Collision**: Returns 1 in `$result` if AABBs collide.
- `CP(idx, color)`: **Color Palette**: Set color at `idx` (0-255). Supports HEX, RGB, or names.
- `DB()`: **Debug**: Dump current state to Serial.

## Interactivity & Events (Updated in v1.7)
- `HZ(id, x, y, w, h, func)`: Define a clickable hit zone.
- `KS(key)`: **Key State**: Returns 1 in `$result` if `key` is currently pressed.
- `KP(key, state)`: **Key Press**: Inject a key state (0 or 1). Useful for simulations.
- `MC(x, y, btn)`, `KC(src, key)`: Inject events.
- `DE()`: Dispatch events and trigger callbacks (e.g., `:ON_KEY`).
- `SA()`: Check if serial input is available.

## Graphics & Rendering
- `S(w, h, [bg])`: Initialize main surface (Double Buffered).
- `FB()` / `VS()`: Flip Buffer and Wait Sync.
- `P(id, [w, h])`: Define/switch to an off-screen buffer.
- `LD(id, x, y, w, h, data)`: **Load Data**: Update a sub-region of buffer `id` with hex-encoded palette indices (2 chars per pixel).
- `DX(id, x, y, [rot], [scale], [alpha], [sx, sy, sw, sh])`: Advanced blit.
- `B(x, y, w, h, c1, c2, [dir])`, `BX(x, y, w, h)`: Gradient/Fast Rectangle.
- `K(color, [width])`, `F(color)`: Style settings. Colors can be palette indices (0-255).
- `M(x, y)`, `L(x, y)`, `C(r)`, `O(rx, ry)`, `G(x1, y1, ...)`, `T(text)`: Primitives.
- `Z(x, y, w, h)`: Clipping zone.
- `[` / `]`: Push/Pop graphics state.

## Control Flow & Logic (Enhanced in v1.7)
- **Variables:** `$var = expr;`. Global variables start with `$`.
- **Functions:** `:name(p1) { body }` (Def); `!name(a1);` (Call). Functions use `$result` for returns.
- **Arrays:** `AA(id, size)` (Alloc); `AV(id, idx, val)` (Set); `AG(id, idx)` (Get).
- **Loops:** `@($v, s, e, step) { body }` (For); `WH(expr) { body }` (While).
- **Conditionals:** `?(expr) { true_block } : { false_block }`.
- **Operators:**
    - Arithmetic: `+`, `-`, `*`, `/`, `%`
    - Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
    - Bitwise: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT), `<<` (LShift), `>>` (RShift)
- **Built-in Functions:** `cos()`, `sin()`, `tan()`, `sqrt()`, `abs()`, `min()`, `max()`, `pow()`, `round()`, `len()`, `str()`, `hex()`, `int()`, `float()`, `zfill()`, `ST()`, `KS()`, `MS()`, `RN()`, `HC()`, `MPX()`, `MPY()`.
