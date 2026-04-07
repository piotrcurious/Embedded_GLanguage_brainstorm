# Bandwidth and Performance Analysis - EGL Version 1.0

EGL was designed to be compact for transmission over constrained serial lines while being powerful enough for complex remote execution.

## Byte Count Analysis

| Script | EGL Size (Bytes) | Equivalent Simple Command Stream (Est. Bytes) | Ratio |
|--------|------------------|-----------------------------------------------|-------|
| `dog_example.egl` | 1,183 | ~2,500 (Individual lines/shapes) | 2.1x reduction |
| `test_sierpinski.egl` (Depth 4) | 459 | ~4,200 (81 triangles * ~50 bytes/tri) | 9.1x reduction |
| `test_fib.egl` (6th fib) | 291 | N/A (Algorithmic) | N/A |

## Efficiency Gains
- **Algorithmic Compression**: By defining functions (like `sierpinski`) once, we can generate complex fractals with a few hundred bytes, whereas a static command list would grow exponentially with recursion depth.
- **State Management**: The `[` and `]` stack operations allow for context saving without re-transmitting colors or widths, saving significant bytes in complex drawings.
- **Variable Reuse**: Coordinate math performed on the host reduces the number of literal coordinate values transmitted.

## Advanced Bandwidth Techniques (v1.7)
- **Partial Updates (`LD`)**: For high-resolution sprites or bitmaps generated on-the-fly, EGL supports partial updates. Instead of re-sending a 64x64 bitmap (4096 pixels), a microcontroller can update a single 8x8 block (64 pixels) or a scanline.
- **Progressive Refinement via LFSR**: Microcontrollers can use a Linear Feedback Shift Register (LFSR) to determine which scanline or tile to update next. This ensures that the entire image is refined evenly over time, maintaining a high perceived responsiveness while working within narrow baud rate limits.
- **Dynamic Hit Zones**: By updating only hit zones and high-priority UI elements (like axis labels) every frame, and background bitmaps progressively, interactive latency remains low (<16ms) even if the background takes multiple frames to fully resolve.

## Conclusion
EGL effectively minimizes serial bandwidth by shifting computational logic to the terminal/host. For repetitive or recursive graphics, the compression ratio exceeds 10x compared to primitive-only protocols like standard ReGIS or raw VGA streams.
