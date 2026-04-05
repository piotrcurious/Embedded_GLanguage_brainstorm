import re
import math
import sys
from PIL import Image, ImageDraw, ImageFont

class EGLInterpreter:
    def __init__(self):
        self.globals = {"$pi": math.pi, "$e": math.e}
        self.scopes = [] # Stack of dicts for truly local vars
        self.functions = {}
        self.state_stack = []
        self.images = {"main": None}
        self.draws = {"main": None}
        self.active_surface = "main"
        self.pos = (0, 0)
        self.stroke_color = "black"
        self.stroke_width = 1
        self.fill_color = None

    def set_var(self, name, val):
        # We'll treat all variables starting with $ as global unless we're in a function
        # But for robust recursion, if we're in a function, EVERYTHING is local unless it's a known global.
        # Actually, let's keep it simple: if there are scopes, it's local.
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

        # Collect all accessible variables
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
                     "tan": lambda x: math.tan(float(x)), "sqrt": lambda x: math.sqrt(float(x)), "abs": abs, "min": min, "max": max, "pi": math.pi}
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

    def run_cmd(self, cmd, args):
        draw = self.draws.get(self.active_surface)
        try:
            if cmd == 'S':
                w, h = int(float(args[0])), int(float(args[1]))
                bg = args[2] if len(args) > 2 else "white"
                self.images["main"] = Image.new("RGBA", (w, h), bg); self.draws["main"] = ImageDraw.Draw(self.images["main"]); self.active_surface = "main"
            elif cmd == 'P':
                id, w, h = str(args[0]), int(float(args[1])), int(float(args[2]))
                self.images[id] = Image.new("RGBA", (w, h), (0,0,0,0)); self.draws[id] = ImageDraw.Draw(self.images[id]); self.active_surface = id
            elif cmd == 'D':
                id, x, y = str(args[0]), float(args[1]), float(args[2])
                if id in self.images and self.images[self.active_surface]: self.images[self.active_surface].paste(self.images[id], (int(x), int(y)), self.images[id])
            elif cmd == 'K':
                self.stroke_color = args[0]
                if len(args) > 1: self.stroke_width = int(float(args[1]))
            elif cmd == 'F': self.fill_color = args[0] if args[0] != "None" else None
            elif cmd == 'M' and len(args) >= 2: self.pos = (float(args[0]), float(args[1]))
            elif cmd == 'R' and len(args) >= 2: self.pos = (self.pos[0] + float(args[0]), self.pos[1] + float(args[1]))
            elif cmd == 'L' and len(args) >= 2:
                np = (float(args[0]), float(args[1]))
                if draw: draw.line([self.pos, np], fill=self.stroke_color, width=self.stroke_width)
                self.pos = np
            elif cmd == 'V' and len(args) >= 2:
                np = (self.pos[0] + float(args[0]), self.pos[1] + float(args[1]))
                if draw: draw.line([self.pos, np], fill=self.stroke_color, width=self.stroke_width)
                self.pos = np
            elif cmd == 'C' and len(args) >= 1:
                r = float(args[0]); box = [self.pos[0]-r, self.pos[1]-r, self.pos[0]+r, self.pos[1]+r]
                if draw: draw.ellipse(box, fill=self.fill_color, outline=self.stroke_color, width=self.stroke_width)
            elif cmd == 'O' and len(args) >= 2:
                rx, ry = float(args[0]), float(args[1]); box = [self.pos[0]-rx, self.pos[1]-ry, self.pos[0]+rx, self.pos[1]+ry]
                if draw: draw.ellipse(box, fill=self.fill_color, outline=self.stroke_color, width=self.stroke_width)
            elif cmd == 'G' and len(args) >= 4:
                pts = [(float(args[i]), float(args[i+1])) for i in range(0, len(args), 2)]
                if draw: draw.polygon(pts, fill=self.fill_color, outline=self.stroke_color)
            elif cmd == 'T' and len(args) >= 1:
                if draw:
                    try: f = ImageFont.load_default()
                    except: f = None
                    draw.text(self.pos, str(args[0]), fill=self.stroke_color, font=f)
            elif cmd == 'W' and len(args) >= 6:
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
                    try: f = ImageFont.load_default(); draw.text((float(x), float(y)), str(label), fill=self.stroke_color, font=f)
                    except: pass
            elif cmd == '>': print(f"SERIAL OUT: {args[0]}")
            elif cmd == '*': print(f"REMOTE CALL: {args[0]}({args[1:]})")
            elif cmd == '[': self.state_stack.append((self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface))
            elif cmd == ']':
                if self.state_stack: self.pos, self.stroke_color, self.stroke_width, self.fill_color, self.active_surface = self.state_stack.pop()
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
                        # Pop scope and handle $result propagation
                        local = self.scopes.pop()
                        if "$result" in local: self.set_var("$result", local["$result"])
                    continue
            m = re.match(r'([A-Z\[\]><\*])', code[i:])
            if m:
                cmd = m.group(1); i += m.end(); args_r = ""
                if i < len(code) and code[i] == '(':
                    args_r, rest = self.parse_balanced(code[i:], '(', ')'); i = len(code) - len(rest)
                if cmd == '<':
                    vn = args_r.strip('()$ '); self.set_var('$' + vn if not vn.startswith('$') else vn, 42)
                else: self.run_cmd(cmd, self.parse_args(args_r))
                continue
            i += 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f: code = f.read()
        it = EGLInterpreter(); it.run_code(code)
        if it.images["main"]: it.images["main"].save("output.png")
        print("Done.")
