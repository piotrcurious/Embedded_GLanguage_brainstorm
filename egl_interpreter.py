import re
import math
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageChops

class EGLValue:
    def __init__(self, val):
        if isinstance(val, EGLValue): self.val = val.val
        else: self.val = val
    def __add__(self, other):
        v1, v2 = self.val, getattr(other, 'val', other)
        if isinstance(v1, str) or isinstance(v2, str): return EGLValue(str(v1) + str(v2))
        return EGLValue(v1 + v2)
    def __radd__(self, other):
        v1, v2 = getattr(other, 'val', other), self.val
        if isinstance(v1, str) or isinstance(v2, str): return EGLValue(str(v1) + str(v2))
        return EGLValue(v1 + v2)
    def __sub__(self, other): return EGLValue(self.val - getattr(other, 'val', other))
    def __rsub__(self, other): return EGLValue(getattr(other, 'val', other) - self.val)
    def __mul__(self, other): return EGLValue(self.val * getattr(other, 'val', other))
    def __rmul__(self, other): return EGLValue(getattr(other, 'val', other) * self.val)
    def __truediv__(self, other): return EGLValue(self.val / getattr(other, 'val', other))
    def __rtruediv__(self, other): return EGLValue(getattr(other, 'val', other) / self.val)
    def __mod__(self, other): return EGLValue(self.val % getattr(other, 'val', other))
    def __rmod__(self, other): return EGLValue(getattr(other, 'val', other) % self.val)
    def __xor__(self, other): return EGLValue(int(self.val) ^ int(getattr(other, 'val', other)))
    def __and__(self, other): return EGLValue(int(self.val) & int(getattr(other, 'val', other)))
    def __or__(self, other): return EGLValue(int(self.val) | int(getattr(other, 'val', other)))
    def __lt__(self, other): return self.val < getattr(other, 'val', other)
    def __le__(self, other): return self.val <= getattr(other, 'val', other)
    def __gt__(self, other): return self.val > getattr(other, 'val', other)
    def __ge__(self, other): return self.val >= getattr(other, 'val', other)
    def __eq__(self, other): return self.val == getattr(other, 'val', other)
    def __ne__(self, other): return self.val != getattr(other, 'val', other)
    def __str__(self): return str(self.val)
    def __repr__(self): return repr(self.val)
    def __int__(self): return int(float(self.val))
    def __float__(self): return float(self.val)

class EGLInterpreter:
    def __init__(self, initial_vars=None, serial_in=None):
        self.globals = {"$pi": math.pi, "$e": math.e, "$last_key": "", "$last_key_src": ""}
        if initial_vars:
            for k, v in initial_vars.items():
                self.globals[k if k.startswith('$') else '$'+k] = v
        self.scopes = []
        self.functions = {}
        self.arrays = {}
        self.hit_zones = []
        self.event_queue = []
        self.state_stack = []
        self.images = {"main": None}
        self.draws = {"main": None}
        self.front_buffer = None
        self.active_surface = "main"
        self.pos = (0, 0)
        self.stroke_color = "black"
        self.stroke_width = 1
        self.fill_color = None
        self.clip = None
        self.serial_in = serial_in if serial_in else []
        self.serial_out = []

    def set_var(self, name, val):
        target_val = val.val if isinstance(val, EGLValue) else val
        if name in self.globals: self.globals[name] = target_val
        elif self.scopes: self.scopes[-1][name] = target_val
        else: self.globals[name] = target_val

    def get_var(self, name):
        for scope in reversed(self.scopes):
            if name in scope: return scope[name]
        return self.globals.get(name, 0)

    def eval_expr(self, expr):
        if isinstance(expr, (int, float, EGLValue)): return EGLValue(expr)
        s = str(expr).strip()
        if not s: return EGLValue(0)
        if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")): return EGLValue(s[1:-1])

        all_vars = self.globals.copy()
        for scope in self.scopes: all_vars.update(scope)

        eval_scope = {
            "__builtins__": None, "math": math,
            "cos": lambda x: math.cos(float(getattr(x, 'val', x))), "sin": lambda x: math.sin(float(getattr(x, 'val', x))),
            "tan": lambda x: math.tan(float(getattr(x, 'val', x))), "sqrt": lambda x: math.sqrt(float(getattr(x, 'val', x))),
            "abs": lambda x: abs(getattr(x, 'val', x)), "min": lambda a, b: min(getattr(a, 'val', a), getattr(b, 'val', b)),
            "max": lambda a, b: max(getattr(a, 'val', a), getattr(b, 'val', b)), "pi": math.pi,
            "int": lambda x: int(float(getattr(x, 'val', x))), "float": lambda x: float(getattr(x, 'val', x)),
            "pow": lambda a, b: pow(getattr(a, 'val', a), getattr(b, 'val', b)),
            "round": lambda x: round(float(getattr(x, 'val', x))), "len": lambda x: len(str(getattr(x, 'val', x))), "str": str
        }

        processed = s
        vars_found = re.findall(r'\$[a-zA-Z0-9_]+', s)
        for i, vname in enumerate(set(vars_found)):
            safe_name = f"_egl_v_{i}"
            val = all_vars.get(vname, 0)
            eval_scope[safe_name] = EGLValue(val)
            pattern = r'(?<![a-zA-Z0-9_])' + re.escape(vname) + r'(?![a-zA-Z0-9_])'
            processed = re.sub(pattern, safe_name, processed)

        try:
            res = eval(processed, eval_scope)
            return res if isinstance(res, EGLValue) else EGLValue(res)
        except: return EGLValue(s)

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
                if current.strip(): args.append(current.strip())
                current = ""
            else: current += char
        if current.strip(): args.append(current.strip())
        return args

    def _get_rgba(self, c):
        cv = str(c)
        if cv == "None": return (0,0,0,0)
        if cv.startswith('#'):
            if len(cv) == 7: return tuple(int(cv[i:i+2], 16) for i in (1, 3, 5)) + (255,)
            if len(cv) == 9: return tuple(int(cv[i:i+2], 16) for i in (1, 3, 5, 7))
        colors = {"red":(255,0,0,255), "blue":(0,0,255,255), "green":(0,255,0,255), "black":(0,0,0,255), "white":(255,255,255,255), "gray":(128,128,128,255), "lightgray":(211,211,211,255)}
        return colors.get(cv.lower(), (0,0,0,255))

    def run_cmd(self, cmd, raw_args):
        args = [self.eval_expr(a).val for a in raw_args]
        sid = self.active_surface; draw = self.draws.get(sid); img = self.images.get(sid)
        try:
            if cmd == 'S':
                w, h = int(float(args[0])), int(float(args[1])); bg = args[2] if len(args) > 2 else "white"
                self.images["main"] = Image.new("RGBA", (w, h), self._get_rgba(bg)); self.draws["main"] = ImageDraw.Draw(self.images["main"])
                self.front_buffer = Image.new("RGBA", (w, h), self._get_rgba(bg)); self.active_surface = "main"; self.clip = None
            elif cmd == 'CL':
                if img: img.paste(self._get_rgba(args[0]), [0, 0, img.width, img.height])
            elif cmd == 'FB':
                if "main" in self.images and self.front_buffer: self.front_buffer.paste(self.images["main"])
            elif cmd == 'P':
                id = str(args[0])
                if len(args) >= 3:
                    w, h = int(float(args[1])), int(float(args[2]))
                    self.images[id] = Image.new("RGBA", (w, h), (0,0,0,0)); self.draws[id] = ImageDraw.Draw(self.images[id])
                self.active_surface = id; self.clip = None
            elif cmd == 'DX':
                id, dx, dy = str(args[0]), float(args[1]), float(args[2])
                angle, scale, alpha = (float(args[i]) if len(args) > i else d for i, d in [(3,0), (4,1.0), (5,1.0)])
                if id in self.images and img:
                    src = self.images[id]
                    if len(args) > 9:
                        sx, sy, sw, sh = map(int, map(float, args[6:10])); src = src.crop((sx, sy, sx+sw, sy+sh))
                    if scale != 1.0:
                        nw, nh = int(src.width * scale), int(src.height * scale)
                        if nw > 0 and nh > 0: src = src.resize((nw, nh), Image.Resampling.LANCZOS)
                    if angle != 0: src = src.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
                    if alpha < 1.0:
                        a = src.getchannel('A').point(lambda p: p * alpha); src = src.copy(); src.putalpha(a)
                    img.paste(src, (int(dx - src.width/2), int(dy - src.height/2)), src)
            elif cmd == 'TM':
                tid, aid, cols, rows, tw, th = str(args[0]), str(args[1]), int(args[2]), int(args[3]), int(args[4]), int(args[5])
                ox, oy = (float(args[i]) if len(args) > i else 0 for i in (6, 7))
                if tid in self.images and aid in self.arrays and img:
                    ts = self.images[tid]; arr = self.arrays[aid]; ts_cols = ts.width // tw
                    for r in range(rows):
                        for c in range(cols):
                            idx = r * cols + c
                            if idx < len(arr):
                                tile_idx = int(float(arr[idx]))
                                if tile_idx >= 0:
                                    sx = (tile_idx % ts_cols) * tw; sy = (tile_idx // ts_cols) * th
                                    img.paste(ts.crop((sx, sy, sx+tw, sy+th)), (int(c*tw - ox), int(r*th - oy)))
            elif cmd == 'HC':
                x1, y1, w1, h1, x2, y2, w2, h2 = map(float, args[:8])
                res = 1 if (x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2) else 0
                self.set_var("$result", res)
            elif cmd == 'DB':
                print(f"DEBUG DUMP: Globals: {self.globals}\nArrays: {self.arrays.keys()}")
            elif cmd == 'HZ': self.hit_zones.append((float(args[1]), float(args[2]), float(args[3]), float(args[4]), str(args[5])))
            elif cmd == 'MC': self.event_queue.append(('MC', float(args[0]), float(args[1]), float(args[2])))
            elif cmd == 'KC': self.event_queue.append(('KC', str(args[0]), str(args[1])))
            elif cmd == 'DE':
                q = self.event_queue; self.event_queue = []
                for ev in q:
                    if ev[0] == 'MC':
                        ex, ey, eb = ev[1:]
                        for hz in reversed(self.hit_zones):
                            hx, hy, hw, hh, hf = hz
                            if hx <= ex <= hx+hw and hy <= ey <= hy+hh:
                                if hf in self.functions:
                                    self.set_var("$last_click_x", ex); self.set_var("$last_click_y", ey); self.set_var("$last_click_btn", eb)
                                    self.run_code(self.functions[hf][1]); break
                    elif ev[0] == 'KC':
                        esrc, ek = ev[1:]; self.set_var("$last_key", ek); self.set_var("$last_key_src", esrc)
                        if "ON_KEY" in self.functions: self.run_code(self.functions["ON_KEY"][1])
            elif cmd == '>':
                if args:
                    v = args[0]; msg = f"[EGL:VAR:{v}]" if isinstance(v, str) and v.startswith('$') else str(v)
                    self.serial_out.append(msg); print(f"SERIAL OUT: {msg}")
            elif cmd == 'SA': self.set_var("$result", 1 if self.serial_in else 0)
            elif cmd == 'B':
                x, y, w, h = map(float, args[0:4]); c1, c2 = args[4], args[5]; dr = int(args[6]) if len(args) > 6 else 1
                if img:
                    base = Image.new('RGBA', (int(w), int(h)), (0,0,0,0)); d = ImageDraw.Draw(base); rgb1, rgb2 = self._get_rgba(c1), self._get_rgba(c2)
                    steps = int(w if dr == 0 else h)
                    for i in range(steps):
                        ratio = i / max(1, steps-1); curr_c = tuple(int(rgb1[j] + (rgb2[j] - rgb1[j]) * ratio) for j in range(4))
                        if dr == 0: d.line([(i, 0), (i, h)], fill=curr_c)
                        else: d.line([(0, i), (w, i)], fill=curr_c)
                    img.paste(base, (int(x), int(y)), base)
            elif cmd == 'BX':
                x, y, w, h = map(float, args[0:4])
                if draw: draw.rectangle([x, y, x+w, y+h], fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'AA': self.arrays[str(args[0])] = [0] * int(float(args[1]))
            elif cmd == 'AV':
                if str(args[0]) in self.arrays: self.arrays[str(args[0])][int(float(args[1]))] = args[2]
            elif cmd == 'AG':
                if str(args[0]) in self.arrays: self.set_var("$result", self.arrays[str(args[0])][int(float(args[1]))])
            elif cmd == 'K':
                self.stroke_color = args[0]
                if len(args) > 1: self.stroke_width = int(float(args[1]))
            elif cmd == 'F': self.fill_color = args[0] if args[0] != "None" else None
            elif cmd == 'M': self.pos = (float(args[0]), float(args[1]))
            elif cmd == 'L':
                np = (float(args[0]), float(args[1]))
                if draw: draw.line([self.pos, np], fill=self._get_rgba(self.stroke_color), width=self.stroke_width)
                self.pos = np
            elif cmd == 'C':
                if args:
                    r = float(args[0]); b = [self.pos[0]-r, self.pos[1]-r, self.pos[0]+r, self.pos[1]+r]
                    if draw: draw.ellipse(b, fill=self._get_rgba(self.fill_color), outline=self._get_rgba(self.stroke_color), width=self.stroke_width)
            elif cmd == 'T':
                if draw:
                    try: f = ImageFont.load_default(); draw.text(self.pos, str(args[0]), fill=self._get_rgba(self.stroke_color), font=f)
                    except: pass
            elif cmd == '<':
                vn = str(args[0]).strip('()$ '); val = self.serial_in.pop(0) if self.serial_in else 0; self.set_var('$' + vn, val)
            elif cmd == '[': self.state_stack.append((self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface, self.clip))
            elif cmd == ']':
                if self.state_stack: self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface, self.clip = self.state_stack.pop()
        except Exception as e:
             print(f"ERROR executing {cmd} with {args}: {e}")

    def run_code(self, code):
        i = 0
        while i < len(code):
            try:
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
                        body, rest = self.parse_balanced(code[i:], '{', '}'); self.functions[name] = (params, body); i = len(code) - len(rest); continue
                if code[i] == '?':
                    i += 1; cond_s, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                    while i < len(code) and code[i] != '{': i += 1
                    body, rest = self.parse_balanced(code[i:], '{', '}'); next_i = len(code) - len(rest); eval_res = self.eval_expr(cond_s).val
                    if eval_res: self.run_code(body)
                    k = 0
                    while k < len(rest) and rest[k].isspace(): k += 1
                    if k < len(rest) and rest[k] == ':':
                        k += 1
                        while k < len(rest) and rest[k].isspace(): k += 1
                        if k < len(rest) and rest[k] == '{':
                            eb, rest2 = self.parse_balanced(rest[k:], '{', '}'); next_i = len(code) - len(rest2)
                            if not eval_res: self.run_code(eb)
                    i = next_i; continue
                if code[i:i+2] == 'WH':
                    i += 2; cond_s, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                    while i < len(code) and code[i] != '{': i += 1
                    body, rest = self.parse_balanced(code[i:], '{', '}'); next_i = len(code) - len(rest)
                    while self.eval_expr(cond_s).val: self.run_code(body)
                    i = next_i; continue
                if code[i] == '@':
                    i += 1; args_s, rest = self.parse_balanced(code[i:], '(', ')')
                    pts = args_s.split(','); vn = pts[0].strip(); start, end, step = [float(self.eval_expr(x).val) for x in pts[1:]]
                    i = len(code) - len(rest)
                    while i < len(code) and code[i] != '{': i += 1
                    body, rest = self.parse_balanced(code[i:], '{', '}'); next_i = len(code) - len(rest); curr = start
                    while (curr <= end if step > 0 else curr >= end): self.set_var(vn, curr); self.run_code(body); curr += step
                    i = next_i; continue
                if code[i] == '!':
                    m = re.match(r'!([a-zA-Z0-9_]+)', code[i:])
                    if m:
                        name = m.group(1); i += m.end(); args_r, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                        if name in self.functions:
                            params, body = self.functions[name]; vals = self.parse_args(args_r); self.scopes.append({p: self.eval_expr(v).val for p, v in zip(params, vals)})
                            self.run_code(body); local = self.scopes.pop()
                            if "$result" in local: self.set_var("$result", local["$result"])
                        continue
                m = re.match(r'([A-Z]{1,2})', code[i:])
                if m:
                    cmd = m.group(1); i += m.end(); args_r = ""
                    if i < len(code) and code[i] == '(': args_r, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                    if cmd == '<': self.run_cmd('<', [args_r.strip('()$ ')])
                    else: self.run_cmd(cmd, self.parse_args(args_r))
                    continue
                if code[i] in ['[', ']', '>', '<', '*']:
                    cmd = code[i]; i += 1; args_r = ""
                    if i < len(code) and code[i] == '(':
                        args_r, rest = self.parse_balanced(code[i:], '(', ')')
                        i = len(code) - len(rest)
                        self.run_cmd(cmd, self.parse_args(args_r))
                    else:
                        self.run_cmd(cmd, [])
                    continue
                i += 1
            except Exception as e:
                line_no = code[:i].count('\n') + 1
                ctx = code[max(0, i-20):min(len(code), i+20)].replace('\n', ' ')
                print(f"SYNTAX ERROR on line {line_no}: {e}\nContext: ...{ctx}...")
                i += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="EGL script file")
    parser.add_argument("--vars", help="Initial variables")
    parser.add_argument("--serial-in", help="Serial input data")
    parser.add_argument("--events", help="Pre-load events")
    parser.add_argument("--output", default="output.png", help="Output PNG file")
    args = parser.parse_args()

    init_vars = {}
    if args.vars:
        for item in args.vars.split(','):
            try:
                k, v = item.split('=');
                try: init_vars[k] = float(v)
                except: init_vars[k] = v
            except: pass

    ser_in = []
    if args.serial_in:
        for val in args.serial_in.split(','):
            try: ser_in.append(float(val))
            except: ser_in.append(val)

    it = EGLInterpreter(initial_vars=init_vars, serial_in=ser_in)
    if args.events:
        for ev_s in args.events.split(';'):
            pts = ev_s.split(',')
            if pts[0] == 'MC': it.event_queue.append(('MC', float(pts[1]), float(pts[2]), float(pts[3])))
            elif pts[0] == 'KC': it.event_queue.append(('KC', str(pts[1]), str(pts[2])))

    try:
        with open(args.file, 'r') as f: code = f.read()
        it.run_code(code)
    except Exception as e:
        print(f"INTERPRETER CRASH: {e}")

    out_img = it.front_buffer if it.front_buffer else it.images.get("main")
    if out_img: out_img.save(args.output); print(f"Saved to {args.output}")
    print("Done.")
