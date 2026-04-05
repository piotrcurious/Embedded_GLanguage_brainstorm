import re
import math
import sys
import argparse
import time
from PIL import Image, ImageDraw, ImageFont, ImageChops

class EGLInterpreter:
    def __init__(self, initial_vars=None, serial_in=None):
        self.globals = {"$pi": math.pi, "$e": math.e}
        if initial_vars:
            for k, v in initial_vars.items():
                self.globals[k if k.startswith('$') else '$'+k] = v
        self.scopes = []
        self.functions = {}
        self.arrays = {}
        self.state_stack = []
        self.images = {"main": None}
        self.draws = {"main": None}
        self.front_buffer = None # Front-buffer for double buffering
        self.active_surface = "main"
        self.pos = (0, 0)
        self.stroke_color = "black"
        self.stroke_width = 1
        self.fill_color = None
        self.clip = None
        self.serial_in = serial_in if serial_in else []
        self.serial_out = []

    def set_var(self, name, val):
        if self.scopes: self.scopes[-1][name] = val
        else: self.globals[name] = val

    def get_var(self, name):
        for scope in reversed(self.scopes):
            if name in scope: return scope[name]
        return self.globals.get(name, 0)

    def eval_expr(self, expr):
        if isinstance(expr, (int, float)): return expr
        s = str(expr).strip()
        if not s: return 0
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")): return s[1:-1]

        all_vars = self.globals.copy()
        for scope in self.scopes: all_vars.update(scope)

        sorted_keys = sorted(all_vars.keys(), key=len, reverse=True)
        processed = s
        for k in sorted_keys:
            pattern = r'(?<![a-zA-Z0-9_])' + re.escape(k) + r'(?![a-zA-Z0-9_])'
            v = all_vars[k]
            repl = str(float(v)) if isinstance(v, (int, float)) else f"'{v}'"
            processed = re.sub(pattern, repl, processed)

        if re.match(r'^\(?-?\d+(\.\d+)?\)?$', processed.strip()):
            try:
                val_s = processed.strip('() ')
                f = float(val_s)
                return int(f) if f.is_integer() else f
            except: pass

        try:
            scope = {"__builtins__": None, "math": math, "cos": lambda x: math.cos(float(x)), "sin": lambda x: math.sin(float(x)),
                     "tan": lambda x: math.tan(float(x)), "sqrt": lambda x: math.sqrt(float(x)), "abs": abs, "min": min, "max": max, "pi": math.pi,
                     "int": int, "float": float, "pow": pow, "round": round}
            return eval(processed, scope)
        except: return s

    def parse_balanced(self, text, open_char, close_char):
        depth, start = 0, -1
        for i, char in enumerate(text):
            if char == open_char:
                if depth == 0: start = i
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0: return text[start+1:i], text[i+1:]
        return None, text

    def parse_args(self, args_str):
        if not args_str: return []
        args, depth, current = [], 0, ""
        for char in args_str:
            if char == '(': depth += 1
            elif char == ')': depth -= 1
            if (char == ',' or char == ';') and depth == 0:
                if current.strip(): args.append(self.eval_expr(current.strip()))
                current = ""
            else: current += char
        if current.strip(): args.append(self.eval_expr(current.strip()))
        return args

    def _get_rgba(self, c):
        if c is None or c == "None": return (0,0,0,0)
        if isinstance(c, tuple): return c
        if isinstance(c, str):
            if c.startswith('#'):
                if len(c) == 7: return tuple(int(c[i:i+2], 16) for i in (1, 3, 5)) + (255,)
                if len(c) == 9: return tuple(int(c[i:i+2], 16) for i in (1, 3, 5, 7))
            colors = {"red":(255,0,0,255), "blue":(0,0,255,255), "green":(0,255,0,255), "black":(0,0,0,255), "white":(255,255,255,255), "gray":(128,128,128,255), "lightgray":(211,211,211,255)}
            return colors.get(c.lower(), (0,0,0,255))
        return (0,0,0,255)

    def run_cmd(self, cmd, args):
        surface_id = self.active_surface
        draw = self.draws.get(surface_id)
        img = self.images.get(surface_id)

        try:
            if cmd == 'S':
                w, h = int(float(args[0])), int(float(args[1]))
                bg = args[2] if len(args) > 2 else "white"
                self.images["main"] = Image.new("RGBA", (w, h), self._get_rgba(bg))
                self.draws["main"] = ImageDraw.Draw(self.images["main"])
                self.front_buffer = Image.new("RGBA", (w, h), self._get_rgba(bg))
                self.active_surface = "main"; self.clip = None
            elif cmd == 'FB': # Flip Buffer (Front-Back flip)
                if "main" in self.images and self.front_buffer:
                    self.front_buffer.paste(self.images["main"])
            elif cmd == 'VS': # Wait Sync
                print("VSYNC WAIT") # In real emu: time.sleep(1/60)
            elif cmd == 'P':
                id = str(args[0])
                if len(args) >= 3:
                    w, h = int(float(args[1])), int(float(args[2]))
                    self.images[id] = Image.new("RGBA", (w, h), (0,0,0,0))
                    self.draws[id] = ImageDraw.Draw(self.images[id])
                self.active_surface = id; self.clip = None
            elif cmd == 'D':
                id, x, y = str(args[0]), float(args[1]), float(args[2])
                if id in self.images and img:
                    src = self.images[id]
                    img.paste(src, (int(x), int(y)), src)
            elif cmd == 'DX':
                id, dx, dy = str(args[0]), float(args[1]), float(args[2])
                angle = float(args[3]) if len(args) > 3 else 0
                scale = float(args[4]) if len(args) > 4 else 1.0
                alpha = float(args[5]) if len(args) > 5 else 1.0
                if id in self.images and img:
                    src = self.images[id]
                    if len(args) > 9:
                        sx, sy, sw, sh = map(int, map(float, args[6:10]))
                        src = src.crop((sx, sy, sx+sw, sy+sh))
                    if scale != 1.0:
                        nw, nh = int(src.width * scale), int(src.height * scale)
                        if nw > 0 and nh > 0: src = src.resize((nw, nh), Image.Resampling.LANCZOS)
                    if angle != 0:
                        src = src.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
                    if alpha < 1.0:
                        a = src.getchannel('A').point(lambda p: p * alpha)
                        src = src.copy(); src.putalpha(a)
                    img.paste(src, (int(dx - src.width/2), int(dy - src.height/2)), src)
            elif cmd == 'B':
                x, y, w, h = map(float, args[0:4])
                c1, c2 = args[4], args[5]
                dir = int(args[6]) if len(args) > 6 else 1
                if img:
                    base = Image.new('RGBA', (int(w), int(h)), (0,0,0,0))
                    d = ImageDraw.Draw(base)
                    rgb1, rgb2 = self._get_rgba(c1), self._get_rgba(c2)
                    steps = int(w if dir == 0 else h)
                    for i in range(steps):
                        ratio = i / max(1, steps-1)
                        curr_c = tuple(int(rgb1[j] + (rgb2[j] - rgb1[j]) * ratio) for j in range(4))
                        if dir == 0: d.line([(i, 0), (i, h)], fill=curr_c)
                        else: d.line([(0, i), (w, i)], fill=curr_c)
                    img.paste(base, (int(x), int(y)), base)
            elif cmd == 'BX':
                x, y, w, h = map(float, args[0:4])
                if draw: draw.rectangle([x, y, x+w, y+h], fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'Z':
                if len(args) >= 4: self.clip = (float(args[0]), float(args[1]), float(args[2]), float(args[3]))
                else: self.clip = None
            elif cmd == 'AA':
                id, sz = str(args[0]), int(float(args[1]))
                self.arrays[id] = [0] * sz
            elif cmd == 'AV':
                id, idx, val = str(args[0]), int(float(args[1])), args[2]
                if id in self.arrays: self.arrays[id][idx] = val
            elif cmd == 'AG':
                id, idx = str(args[0]), int(float(args[1]))
                if id in self.arrays: self.set_var("$result", self.arrays[id][idx])
            elif cmd == 'K':
                self.stroke_color = args[0]
                if len(args) > 1: self.stroke_width = int(float(args[1]))
            elif cmd == 'F': self.fill_color = args[0] if args[0] != "None" else None
            elif cmd == 'M' and len(args) >= 2: self.pos = (float(args[0]), float(args[1]))
            elif cmd == 'R' and len(args) >= 2: self.pos = (self.pos[0] + float(args[0]), self.pos[1] + float(args[1]))
            elif cmd == 'L' and len(args) >= 2:
                np = (float(args[0]), float(args[1]))
                if draw: draw.line([self.pos, np], fill=self._get_rgba(self.stroke_color), width=self.stroke_width)
                self.pos = np
            elif cmd == 'V' and len(args) >= 2:
                np = (self.pos[0] + float(args[0]), self.pos[1] + float(args[1]))
                if draw: draw.line([self.pos, np], fill=self._get_rgba(self.stroke_color), width=self.stroke_width)
                self.pos = np
            elif cmd == 'C' and len(args) >= 1:
                r = float(args[0]); box = [self.pos[0]-r, self.pos[1]-r, self.pos[0]+r, self.pos[1]+r]
                if draw: draw.ellipse(box, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'O' and len(args) >= 2:
                rx, ry = float(args[0]), float(args[1]); box = [self.pos[0]-rx, self.pos[1]-ry, self.pos[0]+rx, self.pos[1]+ry]
                if draw: draw.ellipse(box, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'G' and len(args) >= 4:
                pts = [(float(args[i]), float(args[i+1])) for i in range(0, len(args), 2)]
                if draw: draw.polygon(pts, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color))
            elif cmd == 'T' and len(args) >= 1:
                if draw:
                    try: f = ImageFont.load_default()
                    except: f = None
                    draw.text(self.pos, str(args[0]), fill=self._get_rgba(self.stroke_color), font=f)
            elif cmd == 'WN' and len(args) >= 6:
                id, x, y, w, h, title = args
                if draw:
                    draw.rectangle([float(x), float(y), float(x+w), float(y+h)], outline="gray", width=2); draw.rectangle([float(x), float(y), float(x+w), float(y+20)], fill="gray")
                    try: f = ImageFont.load_default(); draw.text((float(x+5), float(y+2)), str(title), fill="white", font=f)
                    except: pass
            elif cmd == 'UB' and len(args) >= 6:
                id, label, x, y, w, h = args[:6]
                if draw:
                    draw.rectangle([float(x), float(y), float(x+w), float(y+h)], fill="lightgray", outline="black")
                    try: f = ImageFont.load_default(); draw.text((float(x+5), float(y+5)), str(label), fill="black", font=f)
                    except: pass
            elif cmd == 'UX' and len(args) >= 4:
                id, label, x, y = args[:4]
                if draw:
                    try: f = ImageFont.load_default(); draw.text((float(x), float(y)), str(label), fill=self._get_rgba(self.stroke_color), font=f)
                    except: pass
            elif cmd == '>':
                v = args[0]
                msg = f"[EGL:VAR:{v}]" if isinstance(v, str) and v.startswith('$') else str(v)
                self.serial_out.append(msg); print(f"SERIAL OUT: {msg}")
            elif cmd == '<':
                vn = str(args[0]).strip('()$ ')
                val = self.serial_in.pop(0) if self.serial_in else 0
                self.set_var('$' + vn, val)
            elif cmd == '*': print(f"REMOTE CALL: {args[0]}({args[1:]})")
            elif cmd == '[': self.state_stack.append((self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface, self.clip))
            elif cmd == ']':
                if self.state_stack: self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface, self.clip = self.state_stack.pop()
        except Exception as e: pass

    def run_code(self, code):
        i = 0
        while i < len(code):
            if code[i].isspace() or code[i] == ';': i += 1; continue
            if code[i] == '#':
                while i < len(code) and code[i] != '\n': i += 1
                continue
            if code[i] == '$':
                m = re.match(r'(\$[a-zA-Z0-9_]+)\s*=\s*', code[i:])
                if m:
                    vn = m.group(1); i += m.end(); j = i
                    while j < len(code) and code[j] not in [';', '\n']: j += 1
                    self.set_var(vn, self.eval_expr(code[i:j])); i = j; continue
            if code[i] == ':':
                m = re.match(r':([a-zA-Z0-9_]+)', code[i:])
                if m:
                    name = m.group(1); i += m.end(); ps, rest = self.parse_balanced(code[i:], '(', ')')
                    params = [p.strip() for p in ps.split(',')] if ps else []; i = len(code) - len(rest)
                    while i < len(code) and code[i] != '{': i += 1
                    body, rest = self.parse_balanced(code[i:], '{', '}'); self.functions[name] = (params, body)
                    i = len(code) - len(rest); continue
            if code[i] == '?':
                i += 1; cond_s, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                while i < len(code) and code[i] != '{': i += 1
                body, rest = self.parse_balanced(code[i:], '{', '}'); next_i = len(code) - len(rest)
                eval_res = self.eval_expr(cond_s)
                if eval_res: self.run_code(body)
                k = 0
                while k < len(rest) and rest[k].isspace(): k += 1
                if k < len(rest) and rest[k] == ':':
                    k += 1
                    while k < len(rest) and rest[k].isspace(): k += 1
                    if k < len(rest) and rest[k] == '{':
                        eb, rest2 = self.parse_balanced(rest[k:], '{', '}')
                        if not eval_res: self.run_code(eb)
                        next_i = len(code) - len(rest2)
                i = next_i; continue
            if code[i:i+2] == 'WH':
                i += 2; cond_s, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                while i < len(code) and code[i] != '{': i += 1
                body, rest = self.parse_balanced(code[i:], '{', '}'); next_i = len(code) - len(rest)
                while self.eval_expr(cond_s):
                    self.run_code(body)
                i = next_i; continue
            if code[i] == '@':
                i += 1; args_s, rest = self.parse_balanced(code[i:], '(', ')')
                pts = args_s.split(','); vn = pts[0].strip(); start, end, step = self.eval_expr(pts[1]), self.eval_expr(pts[2]), self.eval_expr(pts[3])
                i = len(code) - len(rest)
                while i < len(code) and code[i] != '{': i += 1
                body, rest = self.parse_balanced(code[i:], '{', '}'); next_i = len(code) - len(rest); curr = start
                while (curr <= end if step > 0 else curr >= end):
                    self.set_var(vn, curr); self.run_code(body); curr += step
                i = next_i; continue
            if code[i] == '!':
                m = re.match(r'!([a-zA-Z0-9_]+)', code[i:])
                if m:
                    name = m.group(1); i += m.end(); args_r, rest = self.parse_balanced(code[i:], '(', ')')
                    i = len(code) - len(rest)
                    if name in self.functions:
                        params, body = self.functions[name]; vals = self.parse_args(args_r)
                        self.scopes.append({p: v for p, v in zip(params, vals)})
                        self.run_code(body)
                        local = self.scopes.pop()
                        if "$result" in local: self.set_var("$result", local["$result"])
                    continue
            m = re.match(r'([A-Z]{1,2})', code[i:])
            if m:
                cmd = m.group(1); i += m.end(); args_r = ""
                if i < len(code) and code[i] == '(':
                    args_r, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                if cmd == '<':
                    self.run_cmd('<', [args_r.strip('()$ ')])
                else: self.run_cmd(cmd, self.parse_args(args_r))
                continue
            if code[i] in ['[', ']', '>', '<', '*']:
                cmd = code[i]; i += 1; args_r = ""
                if i < len(code) and code[i] == '(':
                    args_r, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                self.run_cmd(cmd, self.parse_args(args_r))
                continue
            i += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="EGL script file")
    parser.add_argument("--vars", help="Initial variables in key=val,key2=val2 format")
    parser.add_argument("--serial-in", help="Serial input data (comma-separated list of values)")
    parser.add_argument("--output", default="output.png", help="Output PNG file")
    args = parser.parse_args()

    init_vars = {}
    if args.vars:
        for item in args.vars.split(','):
            k, v = item.split('=')
            try: init_vars[k] = float(v)
            except: init_vars[k] = v

    ser_in = []
    if args.serial_in:
        for val in args.serial_in.split(','):
            try: ser_in.append(float(val))
            except: ser_in.append(val)

    with open(args.file, 'r') as f: code = f.read()
    it = EGLInterpreter(initial_vars=init_vars, serial_in=ser_in)
    it.run_code(code)
    # Target front_buffer for final output if it exists
    out_img = it.front_buffer if it.front_buffer else it.images.get("main")
    if out_img:
        out_img.save(args.output)
        print(f"Saved to {args.output}")
    print("Done.")
