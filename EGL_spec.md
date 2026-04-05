# EGL (Embedded Graphics Language) Specification - Version 1.1

EGL is a high-performance, compact graphics language designed for remote execution over serial links. It combines the brevity of ReGIS with the programmable power of PostScript.

## 1. Syntax & Core Concepts

- **Commands**: Single characters followed by optional arguments in parentheses. e.g., `L(100,100)`.
- **Arguments**: Comma-separated literal values or expressions.
- **Expressions**: Standard infix notation with support for variables and common math functions (`cos`, `sin`, `sqrt`, etc.).
- **Variables**: Prefixed with `$`. Global by default. e.g., `$x = 10`.
- **Blocks**: Enclosed in curly braces `{ }`.
- **Functions**: Defined with `:name(p1, p2...) { ... }` and called with `!name(a1, a2...)`.

## 2. Graphics State & Primitives

The interpreter maintains a "Graphics State" (current position, stroke color, fill color, font, line width, active surface).

### State Management
- `[` : Push current graphics state onto the stack.
- `]` : Pop and restore graphics state from the stack.
- `K(color, width)` : Set Stroke (color: hex `#RRGGBB` or name, width: pixels).
- `F(color)` : Set Fill color. Use `"None"` to disable filling.
- `M(x, y)` : Move pen to absolute `(x, y)`.
- `R(dx, dy)` : Move pen relative to current position.

### Drawing
- `L(x, y)` : Draw line to absolute `(x, y)`. Updates pen position.
- `V(dx, dy)` : Draw line to relative `(dx, dy)`. Updates pen position.
- `C(r)` : Draw circle with radius `r` centered at current position.
- `O(rx, ry)` : Draw oval with radii `rx`, `ry` centered at current position.
- `G(x1,y1, x2,y2, ...)` : Draw polygon.
- `T("text")` : Draw text at current position.

### Sprite & Surface Management
- `S(w, h, bg)` : Initialize the main screen and set as active surface.
- `P(id, w, h)` : Define an off-screen buffer (sprite) with unique ID and set as active surface.
- `D(id, x, y)` : Draw (blit) buffer `id` at `(x, y)` onto the active surface.

## 3. UI Framework (Host-Side Stubs)

- `W(id, x, y, w, h, "title")` : Define a window.
- `UB(id, "label", x, y, w, h, "callback")` : Button.
- `UX(id, "label", x, y, w, h)` : Label.

## 4. Programming & Control Flow

- `?(cond) { ... } [ : { ... } ]` : If-else conditional.
- `@($i, start, end, step) { ... }` : For loop.
- Recursive functions are supported.

## 5. Serial & Remote I/O
- `>(val)` : Write value to serial output.
- `<($var)` : Read value from serial input into variable.
- `*(func, args)` : Remote call to host.
