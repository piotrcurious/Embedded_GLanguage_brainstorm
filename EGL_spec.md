# EGL (Embedded Graphics Language) Specification v1.2

EGL is a compact, stack-based graphics language designed for serial execution (SPI/I2C/UART) between a host (e.g., Microcontroller) and a display processor. It is Turing-complete and optimized for state management and UI/game graphics.

## Data Types
- **Numbers:** Floating-point or integers.
- **Strings:** Double or single quoted.
- **Variables:** Prefixed with `$`. Global or local (within functions).
- **Arrays:** Dynamically allocated.

## Control Flow
- **Variables:** `$var = expr;`
- **Functions:** `:name(p1, p2) { body }` - Define; `!name(a1, a2);` - Call.
- **Conditionals:** `?(expr) { if_true } : { if_false }`
- **Loops:** `@($var, start, end, step) { body }` (For-loop)
- **Loops:** `WH(expr) { body }` (While-loop)

## Array Commands
- `AA(id, size)`: Allocate array `id` with `size` elements.
- `AV(id, idx, val)`: Set array `id` at `idx` to `val`.
- `AG(id, idx)`: Get array `id` at `idx` and store in `$result`.

## Graphics Commands
- `S(w, h, [bg])`: Initialize main surface.
- `P(id, [w, h])`: Define or switch to an off-screen buffer.
- `D(id, x, y)`: Basic blit.
- `DX(id, x, y, [rot], [scale], [alpha], [sx, sy, sw, sh])`: Advanced blit.
- `B(x, y, w, h, c1, c2, [dir])`: Gradient Bar.
- `BX(x, y, w, h)`: Fill rectangle at current position using `F` and `K` styles.
- `K(color, [width])`: Set stroke color/width.
- `F(color)`: Set fill color.
- `M(x, y)`, `R(dx, dy)`: Move (Absolute/Relative).
- `L(x, y)`, `V(dx, dy)`: Line (Absolute/Relative).
- `C(r)`, `O(rx, ry)`: Circle/Ellipse.
- `G(x1, y1, ...)`: Polygon.
- `T(text)`: Text.
- `Z(x, y, w, h)`: Clipping zone.
- `WN(id, x, y, w, h, title)`: UI Window frame.
- `UB(id, label, x, y, w, h)`, `UX(id, label, x, y)`: UI Buttons/Labels.
- `[` / `]`: Push/Pop graphics state.

## Serial & System
- `>(expr)`: Serial Output. If `expr` is a `$var`, outputs `[EGL:VAR:NAME:VAL]`.
- `<($var)`: Serial Input. Reads next value from host input buffer into `$var`.
- `*(func, args...)`: Remote Procedure Call to host.

## Built-in Math & Operators
Supports: `sin(x)`, `cos(x)`, `tan(x)`, `sqrt(x)`, `abs(x)`, `min(a, b)`, `max(a, b)`, `pi`, `e`, `int(x)`, `float(x)`, `pow(a, b)`, `round(x)`.
Bitwise operators supported in expressions: `&` (AND), `|` (OR), `^` (XOR), `~` (NOT), `<<` (LSHIFT), `>>` (RSHIFT).

## Host Integration
The interpreter can be pre-loaded with host variables using `--vars key=val,key2=val2` and serial input using `--serial-in v1,v2,v3`.
