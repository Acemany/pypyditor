from time import time as unixtime
from sys import exit as sysexit
from threading import Thread
from math import ceil, log10
from platform import system
from pathlib import Path

from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename

from pygame import (display, draw, event, font, key, mouse, time,
                    Color, Surface, quit as squit,
                    KEYDOWN, KMOD_CTRL, KMOD_SHIFT,
                    BUTTON_LEFT, BUTTON_WHEELDOWN, BUTTON_WHEELUP,
                    FINGERDOWN, MOUSEBUTTONDOWN,
                    SRCALPHA)

from pygments.token import Keyword, Name, Comment, String, Error, \
    Number, Operator, Generic, Whitespace, Punctuation, \
    _TokenType  # type: ignore
from pygments.lexers import guess_lexer, guess_lexer_for_filename, get_lexer_for_filename
from pygments.lexer import Lexer
from pygments import lex


__all__ = ["logf", "setup", "get_command_color", "mlog_to_python",
           "TextInputManager", "TextInputVisualizer",
           "ColorValue",
           "app_path"]


ColorValue = Color | int | str | tuple[int, int, int] | tuple[int, int, int, int]

app_path: Path = Path(__file__).parent


COLORS: dict[_TokenType | None, str] = {
    Whitespace:          '#ffffff',
    Comment.Single:      '#6a9955',
    Comment.Hashbang:    '#6a9955',

    Name:                '#9cdcfe',
    Name.Builtin:        '#dcdcaa',
    Name.Builtin.Pseudo: '#9cdcfe',
    Name.Namespace:      '#4ec9b0',
    Name.Class:          '#4ec9b0',
    Name.Exception:      '#4ec9b0',
    Name.Function:       '#dcdcaa',
    Name.Function.Magic: '#dcdcaa',
    Name.Decorator:      '#4ec9b0',
    Name.Variable.Magic: '#9cdcfe',
    Number.Integer:      '#b5cea8',
    Number.Float:        '#b5cea8',
    Number.Hex:          '#569cd6',
    Keyword:             '#c586c0',
    Keyword.Namespace:   '#c586c0',
    Keyword.Constant:    '#569cd6',

    Punctuation:         '#ffffff',
    Operator:            '#ffd700',
    Operator.Word:       '#569cd6',

    String:              '#ce9178',
    String.Single:       '#ce9178',
    String.Double:       '#ce9178',
    String.Escape:       '#d7ba7d',
    String.Interpol:     '#ffd700',
    String.Affix:        '#569cd6',
    String.Doc:          '#ce9178',

    Generic.Deleted:     '#f14c4c',
    Generic.Error:       '#f14c4c',
    Error:               '#f14c4c',
}

Cbg: Color = Color(18, 18, 18)
Cfg: Color = Color(36, 36, 36)
Ctxt: Color = Color(207, 212, 218)
Ctxt2: Color = Color(164, 161, 171)
Coutline: Color = Color(255, 255, 255)
Cerror: Color = Color(255, 15, 15)
Cwarn: Color = Color(240, 255, 0)

font.init()

font_height: int = 12
FONT: font.Font = font.SysFont('Monospace', font_height, bold=True)
font_width: float = FONT.size("ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # font is not monospaced...
                              "abcdefghijklmnopqrstuvwxyz"
                              "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
                              "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")[0]/118
font_height += 2


class Vector2i:
    """
    Pair os `int`s
    """

    _x: int
    _y: int

    def __init__(self, x: int | tuple[int, int], y: int | None = None):
        """
        Just 2d vector with int as axes\n
        `Vector2i(6, 9)`\n
        `Vector2i([6, 9])`
        """

        if isinstance(x, tuple):
            self._x, self.y = x
        elif isinstance(y, int):
            self._x = x
            self._y = y
        else:
            raise TypeError('Wrong types')

    def __getitem__(self, i: int) -> int:
        return (self.x, self.y)[i]

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, a: int):
        self._x = int(a)

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, a: int):
        self._y = int(a)

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
    _filename: str | Path | None

    def __init__(self,
                 initial: list[str] | None = None):
        self.value = initial if initial is not None else [""]
        self.cursor_pos = Vector2i(len(self.value[-1]), len(self)-1)

    def __str__(self) -> str:
        return "\n".join(self.value)

    def __len__(self):
        return len(self.value)

    def __repr__(self) -> str:
        return f"{len(self.value)}"

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

    @property
    def filename(self) -> Path | None:
        "File that is open currently(or to which text will save)"
        if self._filename is None:
            return
        return Path(self._filename)

    def open(self, file: str | Path | None = None):
        if file == '':
            file = askopenas()
        if not file:
            return
        self._filename = file
        with open(file, 'r', encoding='utf-8') as f:
            self.value = f.read().split('\n')
            self.cursor_pos.update(0, 0)
        return self

    def save(self, file: str | Path | None = None) -> "TextInputManager":
        if file == '':
            file = asksaveas()
        if not file:
            if self._filename is None:
                self._filename = asksaveas()
                if not self._filename:
                    return self
            file = self._filename

        with open(file, 'w', encoding='utf-8') as f:
            f.write(str(self))
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
                    if e.mod & KMOD_SHIFT:
                        Thread(target=self.save, args=('',)).start()
                        return
                    else:
                        self.save()
                case 111:  # K_O
                    Thread(target=self.open, args=('',)).start()
                    return
                case _:
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

    def __init__(self,
                 manager: TextInputManager | None = None,
                 font_object: font.Font | None = None,
                 antialias: bool = True,
                 font_color: ColorValue = 0,
                 cursor_blink_interval: int = 300,
                 cursor_width: int = 3,
                 cursor_color: ColorValue = 0):

        self._manager: TextInputManager = TextInputManager() if manager is None else manager
        self._lexer: Lexer | None = None
        self._font_object: font.Font = font.Font(font.get_default_font(), 25) if font_object is None else font_object
        self._antialias: bool = antialias
        self._font_color: ColorValue = font_color

        self._h_offset: float = 0
        self._v_offset: float = 0
        self._linelog: int = ceil(log10(len(self.value)+1))

        self._clock: time.Clock = time.Clock()
        self.cursor_blink_interval: int = cursor_blink_interval
        self._cursor_visible: bool = False
        self._last_blink_toggle: float = 0

        self._cursor_width: int = cursor_width
        self._cursor_color: ColorValue = cursor_color

        self._surface: Surface = Surface(display.get_window_size(), SRCALPHA)
        self._rerender_required: bool = True

        self._try_lint()

    def __str__(self) -> str:
        return str(self._manager)

    def __len__(self) -> int:
        return len(self._manager)

    @property
    def value(self) -> list[str]:
        return self._manager.value

    @value.setter
    def value(self, a: list[str]):
        self._manager.value = a

    @property
    def surface(self):
        if self._rerender_required:
            self._render()
            self._rerender_required = False
        return self._surface

    @property
    def linelog(self):
        return self._linelog

    @property
    def h_offset(self) -> float:
        return self._h_offset

    @h_offset.setter
    def h_offset(self, a: float):
        self._h_offset = a

    @property
    def v_offset(self) -> float:
        return self._v_offset

    @v_offset.setter
    def v_offset(self, a: float):
        self._v_offset = a

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
    def cursor(self) -> Vector2i:
        return self._manager.cursor_pos

    @cursor.setter
    def cursor(self, a: Vector2i):
        self._manager.cursor_pos.x = min(a[0], len(self._manager.cur_line)+1)
        self._manager.cursor_pos.y = a[1]

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
        return self._manager.filename

    def open(self, file: str | Path) -> "TextInputVisualizer":
        self._manager.open(file)
        self._require_rerender()
        return self

    def save(self, file: str | Path | None = None) -> "TextInputVisualizer":
        self._manager.save(file)
        return self

    def close(self, save: bool = True):
        if save:
            self.save()
        squit()
        sysexit()

    def _try_lint(self, file: str | Path | None = None):
        if file is None:
            self._lexer = guess_lexer(str(self)[:1000])
        else:
            if self.value:
                self._lexer = guess_lexer_for_filename(file, str(self)[:1000])()
            else:
                self._lexer = get_lexer_for_filename(file)
        self._require_rerender()

    def update(self, events: list[event.Event]):
        value_before = self.value
        self._manager.update(events)
        if self.value != value_before:
            self._linelog = ceil(log10(len(self.value)+1))
            self._require_rerender()

        self._clock.tick()
        self._last_blink_toggle += self._clock.get_time()
        if self._last_blink_toggle > self.cursor_blink_interval:
            self._last_blink_toggle %= self.cursor_blink_interval
            self._cursor_visible = not self._cursor_visible

            self._require_rerender()

        for e in events:
            if e.type == KEYDOWN:
                self._last_blink_toggle = 0
                self._cursor_visible = True
                self._require_rerender()
            elif e.type == FINGERDOWN:
                key.start_text_input()
            elif e.type == MOUSEBUTTONDOWN:
                if e.button == BUTTON_WHEELDOWN and self._v_offset > -font_height*(len(self.value)-1):
                    self._require_rerender()
                    self._v_offset -= font_height * 2
                elif e.button == BUTTON_WHEELUP and self._v_offset < 0:
                    self._require_rerender()
                    self._v_offset += font_height * 2
                elif e.button == BUTTON_LEFT:
                    self._require_rerender()
                    mouse_pos = mouse.get_pos()
                    self._manager.cursor_pos.y = max(0, min(int(mouse_pos[1]-self._v_offset)//font_height, len(self._manager)-1))
                    self._manager.cursor_pos.x = max(0, min(int(mouse_pos[0]//font_width-self._linelog), len(self._manager.cur_line)))

    def _require_rerender(self):
        self._rerender_required = True

    def _render(self):
        self._surface.fill((0, 0, 0, 0))

        for i in range(len(self.value)):
            self._surface.blit(self._font_object.render(f"{i+1}", True, Ctxt), (self._h_offset, font_height*i+self._v_offset))

        draw.aaline(self._surface, Coutline, (font_width*self._linelog, 0), (font_width*self._linelog, self._surface.height))

        if self._lexer is None:
            for j, i in enumerate(self.value):
                self._surface.blit(FONT.render(i, True, Ctxt),
                                   (font_width*(self._linelog+0.5), font_height*j+self._v_offset))
        else:
            tx = ty = 0
            for ttype, value in lex(str(self), self._lexer):
                if '\n' in value:
                    tx = 0
                    ty += value.count('\n')
                else:
                    if value.strip():
                        clr = get_command_color(ttype, value)
                        self._surface.blit(FONT.render(value, True, clr),
                                           (font_width*(self._linelog+0.5)+tx*font_width,
                                            ty*font_height+self._v_offset, font_width*(self._linelog), font_height))
                    tx += len(value)

        if self._cursor_visible:
            draw.rect(self._surface, (255, 255, 255),
                      ((self.cursor.x+self._linelog+0.5)*font_width, (self.cursor.y)*font_height+self._v_offset,
                       self._cursor_width, font_height))


def askopenas() -> str | None:
    "Ask the user to select a file to open"
    root = Tk()
    root.withdraw()
    # root.attributes("-topmost", 1)
    if system() == "Darwin":
        file_path = askopenfilename(parent=root)
    else:
        file_types = [("All files", "*")]
        file_path = askopenfilename(parent=root, filetypes=file_types)
    root.update()

    return file_path


def asksaveas() -> str | None:
    "Ask the user to select a file to save"
    root = Tk()
    root.withdraw()
    # root.attributes("-topmost", 1)
    if system() == "Darwin":
        file_path = asksaveasfilename(parent=root)
    else:
        file_types = [("All files", "*")]
        file_path = asksaveasfilename(parent=root, filetypes=file_types)
    root.update()
    return file_path


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


def get_command_color(token: _TokenType, v: str = 'None') -> tuple[int, int, int]:
    """return color of command\n
    I/O - #a08a8a\n
    flush - #d4816b\n
    operations - #877bad\n
    system - #6bb2b2\n
    unknown - #4c4c4c"""

    out = (lambda a: (a.r, a.g, a.b))(Color(COLORS.get(token, 0)))

    if out[0] == out[1] == out[2] == 0:
        print(token, f'\'{v}\'')

    return out


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
