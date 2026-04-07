import math
import time
import random
from egl_interpreter import EGLInterpreter

def generate_lfsr(bits):
    # Standard taps for LFSR
    taps = {
        4: 0b1001,
        6: 0b100001,
        8: 0b10111000,
        10: 0b1000000100,
        12: 0b100000101001,
        16: 0b1000110110000011
    }
    tap = taps.get(bits, 0b1)
    state = 0x1 # Initial state (cannot be 0)
    period = (1 << bits) - 1
    for _ in range(period):
        yield state - 1 # 0-indexed for our needs
        bit = 0
        for i in range(bits):
            if (tap >> i) & 1:
                bit ^= (state >> i) & 1
        state = ((state >> 1) | (bit << (bits - 1))) & period

class RotatingCubeMock:
    def __init__(self):
        self.interpreter = EGLInterpreter()
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.active_axis = None
        self.lfsr = generate_lfsr(6) # 64 positions for 8x8 blocks
        self.blocks = list(self.lfsr)
        self.block_idx = 0

    def setup(self):
        # Initialize screen and palette
        self.interpreter.run_code("""
            S(400, 400, "black")
            CP(0, "black")
            CP(1, "white")
            CP(2, "red")
            CP(3, "green")
            CP(4, "blue")
            P("cube", 128, 128)
            $rot_x = 0
            $rot_y = 0
            $rot_z = 0

            :SET_X() { $active = "X" }
            :SET_Y() { $active = "Y" }
            :SET_Z() { $active = "Z" }
        """)

    def loop_frame(self):
        # 1. Handle Input (Mock clicks)
        # If user clicked a zone, $active is set.
        active = self.interpreter.globals.get("$active")
        if active == "X": self.angle_x += 0.05
        elif active == "Y": self.angle_y += 0.05
        elif active == "Z": self.angle_z += 0.05

        # 2. Update High-Priority UI (Axis Labels & Hit Zones)
        # We blit the cube sprite at 200, 200
        cx, cy = 200, 200
        self.interpreter.run_code(f"""
            M(10, 10); K(1); T("Rotating Cube Demo")
            M(10, 30); K(2); T("X-Axis (Click)"); HZ("ax", 10, 30, 80, 20, "SET_X")
            M(10, 50); K(3); T("Y-Axis (Click)"); HZ("ay", 10, 50, 80, 20, "SET_Y")
            M(10, 70); K(4); T("Z-Axis (Click)"); HZ("az", 10, 70, 80, 20, "SET_Z")

            # Draw sprite
            DX("cube", {cx}, {cy})
            FB()
            CL(0)
            DE()
        """)

        # 3. Progressive Bitmap Update (LFSR scanlines/blocks)
        # Update 4 random blocks per frame to simulate low-bandwidth progressive refinement
        for _ in range(4):
            block_num = self.blocks[self.block_idx]
            self.block_idx = (self.block_idx + 1) % len(self.blocks)

            bx = (block_num % 8) * 16
            by = (block_num // 8) * 16

            # Generate dummy "cube" pixels based on rotation
            # In a real Arduino, this would be the results of 3D projection
            # Here we just use a mathematical pattern to simulate it
            data = ""
            for y in range(16):
                for x in range(16):
                    glob_x = bx + x - 64
                    glob_y = by + y - 64
                    # Simple 3D wireframe-ish logic simulator
                    val = 0
                    d = math.sqrt(glob_x**2 + glob_y**2)
                    if abs(d - 40 - 10*math.sin(self.angle_x)) < 2: val = 2 # Red
                    elif abs(d - 30 - 5*math.cos(self.angle_y)) < 2: val = 3 # Green

                    data += f"{val:02x}"

            self.interpreter.run_code(f'LD("cube", {bx}, {by}, 16, 16, "{data}")')

if __name__ == "__main__":
    demo = RotatingCubeMock()
    demo.setup()

    print("Simulating 64 frames of progressive refinement and interaction...")
    # Simulate some user interaction: click Y axis at frame 20
    for frame in range(64):
        if frame == 20:
            print("SIMULATING CLICK ON Y-AXIS")
            demo.interpreter.event_queue.append(('MC', 20, 55, 1))

        demo.loop_frame()
        if frame % 10 == 0:
            print(f"Frame {frame} processed...")

    # Final output
    out_img = demo.interpreter.front_buffer
    if out_img:
        out_img.save("progressive_demo.png")
        print("Demo complete. Final frame saved to progressive_demo.png")
