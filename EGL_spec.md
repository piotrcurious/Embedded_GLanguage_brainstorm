# EGL (Embedded Graphics Language) Specification v1.1

EGL is a compact, stack-based graphics language designed for serial execution (SPI/I2C/UART) between a host (e.g., Microcontroller) and a display processor. It is Turing-complete and optimized for state management and UI/game graphics.

## Data Types
- **Numbers:** Floating-point or integers.
- **Strings:** Double or single quoted.
- **Variables:** Prefixed with `$`. Global or local (within functions).

## Control Flow
- **Variables:** `$var = expr;`
- **Functions:** `:name(p1, p2) { body }` - Define; `!name(a1, a2);` - Call.
- **Conditionals:** `?(expr) { if_true } : { if_false }`
- **Loops:** `@($var, start, end, step) { body }`

## Core Commands
- `S(w, h, [bg])`: Initialize main surface with width `w`, height `h`.
- `P(id, [w, h])`: Define or switch to an off-screen buffer (sprite).
- `D(id, x, y)`: Basic blit: draw buffer `id` at `(x, y)`.
- `DX(id, x, y, [rot], [scale], [alpha], [sx, sy, sw, sh])`: Advanced blit: Draw buffer `id` at `(x, y)` with optional rotation, scaling, alpha transparency, and source sub-rectangle (cropping/tiling).
- `B(x, y, w, h, c1, c2, [dir])`: Gradient Bar: Draw a gradient from color `c1` to `c2` in direction `dir` (0=Horizontal, 1=Vertical).
- `K(color, [width])`: Set stroke color and width.
- `F(color)`: Set fill color ("None" for no fill).
- `M(x, y)`: Move cursor to absolute `(x, y)`.
- `R(dx, dy)`: Move cursor relative by `(dx, dy)`.
- `L(x, y)`: Draw line to absolute `(x, y)`.
- `V(dx, dy)`: Draw line to relative `(dx, dy)`.
- `C(r)`: Draw circle with radius `r` at current position.
- `O(rx, ry)`: Draw ellipse at current position.
- `G(x1, y1, x2, y2, ...)`: Draw closed polygon.
- `T(text)`: Render text at current position.
- `Z(x, y, w, h)`: Set clipping zone (viewport). Empty `Z()` to clear.
- `[`: Push graphics state (pos, colors, surface, clip) to stack.
- `]`: Pop graphics state from stack.
- `>(expr)`: Serial Output (for debugging or host feedback).
- `<($var)`: Serial Input (stubs to host input).
- `*(func, args...)`: Remote Procedure Call to host.

## Built-in Math
Supports: `sin(x)`, `cos(x)`, `tan(x)`, `sqrt(x)`, `abs(x)`, `min(a, b)`, `max(a, b)`, `pi`, `e`.

## Host Integration
The interpreter can be pre-loaded with host variables using `--vars key=val,key2=val2`. This allows the host to pass dynamic data (sensor readings, state) to an EGL script.
