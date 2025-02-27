from time import time as unixtime
from pathlib import Path

from pygame import (event, font, time,
                    Color, Surface,
                    KEYDOWN, KMOD_NONE, KMOD_CTRL)


__all__ = ["logf", "setup", "get_command_color", "mlog_to_python",
           "TextInputManager", "TextInputVisualizer",
           "ColorValue",
           "app_path"]


ColorValue = Color | int | str | tuple[int, int, int] | tuple[int, int, int, int]

app_path: Path = Path(__file__).parent


class Vector2i:
    """
    Pair os `int`s
    """

    x: int
    y: int

    def __init__(self, x: int | tuple[int, int], y: int | None = None):
        """Just 2d vector with int as axes\n
        Vector2i(6, 9)\n
        Vector2i([6, 9])"""
        if isinstance(x, tuple):
            self.x, self.y = x
        elif isinstance(y, int):
            self.x = x
            self.y = y
        else:
            raise TypeError('Wrong types')

    def __getitem__(self, i: int) -> int:
        return (self.x, self.y)[i]

    @property
    def xy(self) -> tuple[int, int]:
        return (self.x, self.y)

    @xy.setter
    def xy(self, a: tuple[int, int]):
        self.x, self.y = a

    @property
    def yx(self) -> tuple[int, int]:
        return (self.y, self.x)

    @yx.setter
    def yx(self, a: tuple[int, int]):
        self.y, self.x = a

    def update(self, x: int, y: int):
        "Set new position"
        self.x = x
        self.y = y


class TextInputManager:
    """
    Class that holds cursor position, file data and other stuff for writing text
    """

    value: list[str]
    cursor_pos: Vector2i
    filename: str | Path | None

    def __init__(self,
                 initial: list[str] | None = None):
        self.value = initial if initial is not None else [""]
        self.cursor_pos = Vector2i(len(self.value[-1]), len(self)-1)

    def __str__(self) -> str:
        return "\n".join(self.value)

    def __len__(self):
        return len(self.value)

    @property
    def cur_line(self):
        "Current cursor vertical position"
        return self.value[self.cursor_pos.y]

    @cur_line.setter
    def cur_line(self, a: str):
        self.value[self.cursor_pos.y] = a

    @property
    def left(self) -> list[str]:
        "Everything to the left of the cursor"
        return [*self.value[:self.cursor_pos.y],
                self.cur_line[:self.cursor_pos.x]]

    @left.setter
    def left(self, a: list[str]) -> None:
        self.value = [*a[:-1],
                      a[-1] + self.right[0],
                      *self.right[1:]]

    @property
    def right(self) -> list[str]:
        "Everything to the right of the cursor"
        return [self.cur_line[self.cursor_pos.x:],
                *self.value[self.cursor_pos.y+1:]]

    @right.setter
    def right(self, a: list[str]) -> None:
        self.value = [*self.left[:-1],
                      self.left[-1] + a[0],
                      *a[1:]]

    def open(self, file: str | Path):
        self.filename = file
        with open(file, "r", encoding="utf-8") as f:
            self.value = f.read().splitlines()
            self.cursor_pos.update(0, 0)
        return self

    def save(self, file: str | Path | None = None) -> "TextInputManager":
        if file is None:
            if self.filename is None:
                raise TypeError('There must be either valid `file` argument or `filename` variable set')
            file = self.filename

        with open(file, "w", encoding="utf-8") as f:
            f.write("\n".join(self.value))
        return self

    def update(self, events: list[event.Event]) -> None:
        "Processes events"
        for e in events:
            if e.type == KEYDOWN:
                self._process_keydown(e)

    def _process_keydown(self, e: event.Event) -> None:
        if e.mod & KMOD_CTRL:
            match e.key:
                case 115:  # K_S
                    self.save()
                # case 111:  # K_O
                #     self.open(self.filename)
                case _:
                    pass
        elif e.mod != KMOD_NONE:
            pass

        match e.key:
            case 8:                      # K_BACKSPACE
                if self.cursor_pos.x > 0:
                    self.cur_line = self.cur_line[:self.cursor_pos.x][:-1] + self.cur_line[self.cursor_pos.x:]
                    self.cursor_pos.x -= 1
                elif self.cursor_pos.y > 0:
                    right_part: str = self.cur_line
                    self.value.pop(self.cursor_pos.y)
                    next_cursor_pos: tuple[int, int] = (len(self.value[self.cursor_pos.y-1]), self.cursor_pos.y-1)
                    self.value[self.cursor_pos.y-1] += right_part
                    self.cursor_pos.update(*next_cursor_pos)
            case 127:                    # K_DELETE
                if self.cursor_pos.x < len(self.cur_line):
                    self.cur_line = self.cur_line[:self.cursor_pos.x] + self.cur_line[self.cursor_pos.x:][1:]
                elif self.cursor_pos.y < len(self)-1:
                    left_part: str = self.value[self.cursor_pos.y+1]
                    self.value.pop(self.cursor_pos.y+1)
                    self.cur_line += left_part
            case 1073741904:             # K_LEFT
                if self.cursor_pos.x > 0:
                    self.cursor_pos.x = min(self.cursor_pos.x, len(self.cur_line))
                    self.cursor_pos.x -= 1
                elif self.cursor_pos.y > 0:
                    self.cursor_pos.update(len(self.value[self.cursor_pos.y-1]), self.cursor_pos.y-1)
            case 1073741903:             # K_RIGHT
                if self.cursor_pos.x < len(self.cur_line):
                    self.cursor_pos.x = min(self.cursor_pos.x, len(self.cur_line))
                    self.cursor_pos.x += 1
                elif self.cursor_pos.y < len(self)-1:
                    self.cursor_pos.update(0, self.cursor_pos.y+1)
            case 1073741906:             # K_UP
                if self.cursor_pos.y > 0:
                    self.cursor_pos.y -= 1
                elif self.cursor_pos.x > 0:
                    self.cursor_pos.update(0, 0)
            case 1073741905:             # K_DOWN
                if self.cursor_pos.y < len(self)-1:
                    self.cursor_pos.y = min(self.cursor_pos.y, len(self)-1)
                    self.cursor_pos.y += 1
                elif self.cursor_pos.x < len(self.cur_line):
                    self.cursor_pos.update(len(self.value[-1]), len(self)-1)
            case 1073741901:             # K_END
                self.cursor_pos.update(len(self.value[-1]), len(self)-1)
            case 1073741898:             # K_HOME
                self.cursor_pos.update(0, 0)
            case 13:                     # K_RETURN
                next_line: str = self.cur_line[self.cursor_pos.x:]
                self.cur_line = self.cur_line[:self.cursor_pos.x]
                self.value.insert(self.cursor_pos.y+1, next_line)
                self.cursor_pos.update(0, self.cursor_pos.y+1)
            case _:
                if e.unicode.isprintable() and e.unicode:  # UNICODE
                    self.cur_line = self.cur_line[:self.cursor_pos.x] + e.unicode + self.cur_line[self.cursor_pos.x:]
                    self.cursor_pos.x += 1
                elif e.key in (1073742048, 1073742049, 1073742050, 1073742051,
                               1073742052, 1073742053, 1073742054, 1073742055,
                               27,):  # ESC key and keymods
                    pass
                else:
                    print(f"Unknown key {event.event_name(e.key)}[{e.key}] with repr {e.unicode}")


class TextInputVisualizer:
    """
    Visual interface for Textinput instance
    """

    cursor_blink_interval: int

    def __init__(self,
                 manager: TextInputManager | None = None,
                 font_object: font.Font | None = None,
                 antialias: bool = True,
                 font_color: ColorValue = 0,
                 cursor_blink_interval: int = 300,
                 cursor_width: int = 3,
                 cursor_color: ColorValue = 0):

        self.manager: TextInputManager = TextInputManager() if manager is None else manager
        self._font_object: font.Font = font.Font(font.get_default_font(), 25) if font_object is None else font_object
        self._antialias: bool = antialias
        self._font_color: ColorValue = font_color

        self._clock: time.Clock = time.Clock()
        self.cursor_blink_interval = cursor_blink_interval
        self._cursor_visible: bool = False
        self._last_blink_toggle: float = 0

        self._cursor_width: int = cursor_width
        self._cursor_color: ColorValue = cursor_color

        self._surface: Surface = Surface((self._cursor_width, self._font_object.get_height()))
        self._rerender_required: bool = True

    def __str__(self) -> str:
        return str(self.manager)

    def __len__(self) -> int:
        return len(self.manager)

    @property
    def value(self) -> list[str]:
        return self.manager.value

    @value.setter
    def value(self, a: list[str]):
        self.manager.value = a

    @property
    def antialias(self):
        return self._antialias

    @antialias.setter
    def antialias(self, a: bool):
        self._antialias = a
        self._require_rerender()

    @property
    def font_color(self):
        return self._font_color

    @font_color.setter
    def font_color(self, a: ColorValue):
        self._font_color = a
        self._require_rerender()

    @property
    def font_object(self):
        return self._font_object

    @font_object.setter
    def font_object(self, a: font.Font):
        self._font_object = a
        self._require_rerender()

    @property
    def cursor(self):
        return self.manager.cursor_pos

    @cursor.setter
    def cursor(self, a: Vector2i):
        self.manager.cursor_pos = a

    @property
    def cursor_visible(self):
        return self._cursor_visible

    @cursor_visible.setter
    def cursor_visible(self, a: bool):
        self._cursor_visible = a
        self._last_blink_toggle = 0
        self._require_rerender()

    @property
    def cursor_width(self):
        return self._cursor_width

    @cursor_width.setter
    def cursor_width(self, a: int):
        self._cursor_width = a
        self._require_rerender()

    @property
    def cursor_color(self):
        return self._cursor_color

    @cursor_color.setter
    def cursor_color(self, a: ColorValue):
        self._cursor_color = a
        self._require_rerender()

    @property
    def filename(self):
        return self.manager.filename

    @filename.setter
    def filename(self, a: str | Path):
        self.manager.filename = a

    def open(self, file: str | Path) -> "TextInputVisualizer":
        self.manager.open(file)
        return self

    def save(self, file: str | Path | None = None) -> "TextInputVisualizer":
        self.manager.save(file)
        return self

    def update(self, events: list[event.Event]):
        value_before = self.manager.value
        self.manager.update(events)
        if self.manager.value != value_before:
            self._require_rerender()

        self._clock.tick()
        self._last_blink_toggle += self._clock.get_time()
        if self._last_blink_toggle > self.cursor_blink_interval:
            self._last_blink_toggle %= self.cursor_blink_interval
            self._cursor_visible = not self._cursor_visible

            self._require_rerender()

        if [event for event in events if event.type == KEYDOWN]:
            self._last_blink_toggle = 0
            self._cursor_visible = True
            self._require_rerender()

    def _require_rerender(self):
        self._rerender_required = True

    def _render(self):
        for i in range(len(self.value)):
            self._surface.blit(self._font_object.render(f"{i+1}", True, Ctxt), (self._h_offset, font_height*i+self._v_offset))


def logf(err: str | Exception, warn: int = 0):
    """Log.
    `txt` - error text.
    `warn` - warning level (0 - info, 1 - warning, >1 - error).
    """

    warn_level = "IWE"[warn]
    with open(app_path/'log.txt', 'a', encoding='utf-8') as f:
        f.write(f'[{warn_level}]-{str(unixtime())}:\n{err}\n\n')


def dot(g: tuple[int, int], x: float, y: float):
    "Dot product"
    return g[0] * x + g[1] * y


def perm(seed: int, x: int) -> int:
    "like hash"
    x = ((x//0xffff) ^ x)*0x45d9f3b
    x = ((x//0xffff) ^ x)*(0x45d9f3b+seed)
    return ((x//0xffff) ^ x) & 0xff


def raw2d(seed: int, x: float, y: float) -> float:
    "idk how i translated this from java but it works"

    s: float = (x + y) * 0.3660254037844386
    i: int = int(x + s)
    j: int = int(y + s)

    t: float = (i + j) * 0.21132486540518713

    X0: float = i - t
    Y0: float = j - t

    x0: float = x - X0
    y0: float = y - Y0

    i1 = x0 > y0
    j1 = not i1

    x1: float = x0 - i1 + 0.21132486540518713
    y1: float = y0 - j1 + 0.21132486540518713
    x2: float = x0 - 1 + 2 * 0.21132486540518713
    y2: float = y0 - 1 + 2 * 0.21132486540518713

    ii: int = i & 255
    jj: int = j & 255

    t0: float = 0.5 - x0**2 - y0**2
    t1: float = 0.5 - x1**2 - y1**2
    t2: float = 0.5 - x2**2 - y2**2

    return 70*sum(((0 if t0 < 0 else t0**4 * dot(((1, 1), (-1, 1), (1, -1), (-1, -1),
                                                  (1, 0), (-1, 0), (1,  0), (-1,  0),
                                                  (0, 1), (0, -1), (0,  1), (0,  -1)
                                                  )[perm(seed, ii + perm(seed, jj)) % 12],           x0, y0)),
                   (0 if t1 < 0 else t1**4 * dot(((1, 1), (-1, 1), (1, -1), (-1, -1),
                                                  (1, 0), (-1, 0), (1,  0), (-1,  0),
                                                  (0, 1), (0, -1), (0,  1), (0,  -1)
                                                  )[perm(seed, ii + i1 + perm(seed, jj + j1)) % 12], x1, y1)),
                   (0 if t2 < 0 else t2**4 * dot(((1, 1), (-1, 1), (1, -1), (-1, -1),
                                                  (1, 0), (-1, 0), (1,  0), (-1,  0),
                                                  (0, 1), (0, -1), (0,  1), (0,  -1)
                                                  )[perm(seed, ii + 1 + perm(seed, jj + 1)) % 12],   x2, y2))))


def setup():
    "Imports everything for correct translation to mlog"

    exec("""from math import (log, log10, floor, ceil, sqrt,
                              asin, acos, atan, atan2,
                              sin, cos, tan, pi)\
            \nfrom random import random\
            \nfrom pygame import draw\
            \nfrom mlog_lib import raw2d""")
    with open(app_path/'log.txt', 'w', encoding="utf-8") as f:
        f.write('')


def get_command_color(word: str) -> tuple[int, int, int]:
    """return color of command\n
    I/O - #a08a8a\n
    flush - #d4816b\n
    operations - #877bad\n
    system - #6bb2b2\n
    unknown - #4c4c4c"""

    return (160, 138, 138) if word in ("read", "write", "draw", "print") else\
           (212, 129, 107) if word in ("drawflush", "printflush") else\
           (135, 123, 173) if word in ("set", "op") else\
           (107, 178, 178) if word in ("wait", "stop", "end", "jump") else\
           (76, 76, 76)


def mlog_to_python(code: str) -> str:
    """Transforms Mlog code to Python code.\n
    args[0] is the name of command\n
    args[1] is the type of command if command is draw or op, else it is first arg\n
    other args is just args"""

    args: list[str] = code.split()

    match args[0]:
        case "read":
            return f"{args[1]} = {args[2]}[{args[3]}]"
        case "write":
            return f"{args[2]}[{args[3]}] = {args[1]}"
        case "draw":
            match args[1]:
                case "clear":
                    return f"processor_surface.fill(({int(args[2])}, {int(args[3])}, {int(args[4])}))"
                case "color":
                    return f"processor_color = ({args[2]}, {args[3]}, {args[4]}, {args[5]})"
                case "col":
                    return f"processor_color = ({int(args[2][1:3], base=16)}, {int(args[2][3:5], base=16)}, {int(args[2][5:7], base=16)})"
                case "stroke":
                    return f"processor_width = {args[2]}"
                case "line":
                    return f"draw.line(processor_surface, processor_color, ({args[2]}, {args[3]}), ({args[4]}, {args[5]}), processor_width)"
                case "rect":
                    return f"draw.rect(processor_surface, processor_color, ({args[2]}, {args[3]}, {args[4]}, {args[5]}))"
                case "lineRect":
                    return f"draw.rect(processor_surface, processor_color, ({args[2]}, {args[3]}, {args[4]}, {args[5]}), processor_width)"
                case "poly":
                    return f"draw.polygon(processor_surface, processor_color, [({args[2]}+cos(pi*2/{args[4]}*j+{args[6]})*{args[5]}, {args[3]}+sin(pi*2/{args[4]}*j+{args[6]})*{args[5]}) for j in range({args[4]})])"
                case "linePoly":
                    return f"draw.polygon(processor_surface, processor_color, [({args[2]}+cos(pi*2/{args[4]}*j+{args[6]})*{args[5]}, {args[3]}+sin(pi*2/{args[4]}*j+{args[6]})*{args[5]}) for j in range({args[4]})], processor_width)"
                case "triangle":
                    return f"draw.polygon(processor_surface, processor_color, (({args[2]}, {args[3]}), ({args[4]}, {args[5]}), ({args[6]}, {args[7]})))"
                case "image":
                    return "NotImplemented"
                case _:
                    return "NotImplemented"
        case "print":
            return f"processor_textbuffer += str({args[1]})"

        case "drawflush":
            return f"{args[1]}.blit(processor_surface, (0, 0))"
        case "printflush":
            return ''

        case "set":
            return f"global {args[1]};{args[1]} = {args[2]}"
        case "op":
            opeq: str = "0"
            args[3], args[4] = f'float({args[3]})', f'float({args[4]})'
            match args[1]:
                case "add":
                    opeq = f"{args[3]} + {args[4]}"
                case "sub":
                    opeq = f"{args[3]} - {args[4]}"
                case "mul":
                    opeq = f"{args[3]} * {args[4]}"
                case "div":
                    opeq = f"{args[3]} / {args[4]}"
                case "idiv":
                    opeq = f"{args[3]} // {args[4]}"
                case "mod":
                    opeq = f"{args[3]} % {args[4]}"
                case "pow":
                    opeq = f"{args[3]} ** {args[4]}"

                case "equal":
                    opeq = f"abs({args[3]} - {args[4]}) < 0.000001"
                case "notEqual":
                    opeq = f"abs({args[3]} - {args[4]}) >= 0.000001"
                case "land":
                    opeq = f"{args[3]} != 0 && {args[4]} != 0"
                case "lessThan":
                    opeq = f"{args[3]} < {args[4]}"
                case "lessThanEq":
                    opeq = f"{args[3]} <= {args[4]}"
                case "greaterThan":
                    opeq = f"{args[3]} > {args[4]}"
                case "greaterThanEq":
                    opeq = f"{args[3]} >= {args[4]}"
                case "strictEqual":
                    opeq = "0"

                case "shl":
                    opeq = f"{args[3]} << {args[4]}"
                case "shr":
                    opeq = f"{args[3]} >> {args[4]}"
                case "or":
                    opeq = f"{args[3]} | {args[4]}"
                case "and":
                    opeq = f"{args[3]} & {args[4]}"
                case "xor":
                    opeq = f"{args[3]} ^ {args[4]}"
                case "not":
                    opeq = f"~{args[3]}"

                case "max":
                    opeq = f"max({args[3]}, {args[4]})"
                case "min":
                    opeq = f"min({args[3]}, {args[4]})"
                case "angle":
                    opeq = f"(atan2({args[4]}, {args[3]}) * 180/pi) % 360"
                case "angleDiff":
                    opeq = f"min(({args[4]} - {args[3]})%360, ({args[3]} - {args[4]})%360)"
                case "len":
                    opeq = f"abs({args[3]} - {args[4]})"
                case "noise":
                    opeq = f"raw2d(0, {args[3]}, {args[4]})"
                case "abs":
                    opeq = f"abs({args[3]})"
                case "log":
                    opeq = f"log({args[3]})"
                case "log10":
                    opeq = f"log({args[3]}, 10)"
                case "floor":
                    opeq = f"int({args[3]})"
                case "ceil":
                    opeq = f"ceil({args[3]})"
                case "sqrt":
                    opeq = f"{args[3]} ** 0.5"
                case "rand":
                    opeq = f"random() * {args[3]}"

                case "sin":
                    opeq = f"sin({args[3]} / 180*pi)"
                case "cos":
                    opeq = f"cos({args[3]} / 180*pi)"
                case "tan":
                    opeq = f"tan({args[3]} / 180*pi)"

                case "asin":
                    opeq = f"asin({args[3]}) / 180*pi)"
                case "acos":
                    opeq = f"acos({args[3]}) / 180*pi)"
                case "atan":
                    opeq = f"atan({args[3]}) / 180*pi)"
                case _:
                    return "NotImplemented"
            return f"{args[2]} = {opeq}"

        case "wait":
            return f"sleep({args[1]})"
        case "stop":
            return "1/0"
        case "end":
            return "processor_counter = 0"
        case "jump":
            match args[2]:
                case "equal":
                    cond = f"{args[3]} == {args[4]}"
                case "notEqual":
                    cond = f"{args[3]} != {args[4]}"
                case "lessThan":
                    cond = f"float({args[3]}) < float({args[4]})"
                case "lessThanEq":
                    cond = f"float({args[3]}) <= float({args[4]})"
                case "greaterThan":
                    cond = f"float({args[3]}) > float({args[4]})"
                case "greaterThanEq":
                    cond = f"float({args[3]}) >= float({args[4]})"
                case "strictEqual":
                    cond = "False"
                case "always":
                    cond = "True"
                case _:
                    return "NotImplemented"
            return f"processor_counter = {args[1]}-1 if {cond} else processor_counter"

        case _:
            return "NotImplemented"
