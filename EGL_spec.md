# EGL (Embedded Graphics Language) Specification v1.4

EGL is a compact, stack-based graphics language designed for serial execution (SPI/I2C/UART). It is Turing-complete and optimized for interactive UI/game graphics.

## Control Flow & Logic
- **Variables:** `$var = expr;`
- **Functions:** `:name(p1, p2) { body }` - Define; `!name(a1, a2);` - Call.
- **Conditionals:** `?(expr) { if_true } : { if_false }`
- **Loops:** `@($var, start, end, step) { body }` (For); `WH(expr) { body }` (While).

## Interactivity & Events (New in v1.4)
- `HZ(id, x, y, w, h, func)`: Define a clickable hit zone that triggers EGL function `func`.
- `MC(x, y, btn)`: Inject a Mouse Click event.
- `KC(src, key)`: Inject a Key Click event from source `src`.
- `DE()`: **Dispatch Events**: Process injected events, check hit zones, and run callbacks.
- **Special Functions:** `:ON_KEY` is called automatically by `DE()` for every `KC` event.
- **Special Variables:** `$last_key` and `$last_key_src` hold the details of the most recent key event during `ON_KEY`.

## Data Handling
- `AA(id, size)`, `AV(id, idx, val)`, `AG(id, idx)`: Array management.
- `>(expr)`: Serial Output. If `$var`, outputs `[EGL:VAR:NAME:VAL]`.
- `<($var)`: Serial Input. Reads next value from input buffer.
- `SA()`: **Serial Available**: Returns 1 if input buffer has data, 0 otherwise.

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

## Built-in Math & Operators
Full expression support including bitwise: `&`, `|`, `^`, `~`, `<<`, `>>` and math functions: `sin`, `cos`, `tan`, `sqrt`, `abs`, `min`, `max`, `int`, `float`, `pow`, `round`, `len`.

## Double Buffering & Events Workflow
Interactive EGL scripts typically follow a loop:
1. `DE()` - Process any input events from the host.
2. Update game/UI logic based on variables and callbacks.
3. Draw current state to back-buffer.
4. `VS()` and `FB()` to update the display.
