#!/usr/env/bin python

from sys import exit as _exit
from math import ceil, log10
from pathlib import Path

from pygame import (display, draw, event, font, key, mouse, time, transform,
                    BUTTON_LEFT, BUTTON_WHEELDOWN, BUTTON_WHEELUP,
                    FINGERDOWN, QUIT, MOUSEBUTTONDOWN,
                    Color, Surface, Vector2,
                    init, quit as squit,
                    K_ESCAPE)
from pyndustric import Compiler

from mlog_lib import setup, get_command_color, mlog_to_python, TextInputManager, TextInputVisualizer, ColorValue, app_path


font.init()

init()
setup()
WIN: Surface = display.set_mode()
SC_RES: Vector2 = Vector2(WIN.get_size())
WIDTH, HEIGHT = SC_RES
FONT: font.Font = font.SysFont('Monospace', 12, bold=True)
CLOCK: time.Clock = time.Clock()
COMPILER = Compiler()

save_path: Path = app_path
font_width: float = FONT.size("ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # font not monospaced...
                              "abcdefghijklmnopqrstuvwxyz"
                              "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
                              "абвгдеёжзийклмнопрстуфхцчшщъыьэюя")[0]/118
font_height: int = 12

Cbg: ColorValue = Color(18, 18, 18)
Cfg: ColorValue = Color(36, 36, 36)
Ctxt: ColorValue = Color(207, 212, 218)
Ctxt2: ColorValue = Color(164, 161, 171)
Coutline: ColorValue = Color(255, 255, 255)
Cerror: ColorValue = Color(255, 15, 15)
Cwarn: ColorValue = Color(240, 255, 0)

delta: float = 1/60
mouse_pos: Vector2 = Vector2()
mouse_pressed: tuple[bool, bool, bool]
keys_pressed: key.ScancodeWrapper
events: list[event.Event]

key.set_repeat(200, 100)
key.start_text_input()

code_textarea: TextInputVisualizer = TextInputVisualizer(TextInputManager().open(save_path/"pyexa.py"),
                                                         FONT, True, Ctxt,
                                                         500, 2)


def queuit() -> None:
    "Save and exit"
    code_textarea.save()
    squit()
    _exit()


linelog10: int = ceil(log10(len(code_textarea.value)+1))
processor_width: int = 1
processor_color: ColorValue = (0, 0, 0)
processor_surface: Surface = Surface((176, 176))
processor_speed: float = 1/120
processor_counter: int = 0
processor_textbuffer: str = ""
processor_cursor_pos: list[int | float] = [0, 0]
processor_vertical_offset: float = 0

display1: Surface = Surface(processor_surface.get_size())
text_surface: Surface
cell1: list[str] = ["" for _ in range(64)]
decoded: list[str] = ["" for _ in range(len(code_textarea.value))]
excepp = list[Exception]()
mlython_str: list[str] = []
len_decoded: int = 0
timer: float = 0

processor_surface.fill(Cbg)


while True:
    timer += delta
    WIN.fill(Cbg)

    mouse_pos.update(mouse.get_pos())
    mouse_pressed = mouse.get_pressed()
    keys_pressed = key.get_pressed()
    events = event.get()

    for e in events:
        if e.type == QUIT or keys_pressed[K_ESCAPE]:
            queuit()
        elif e.type == FINGERDOWN:
            key.start_text_input()
        elif e.type == MOUSEBUTTONDOWN:
            if e.button == BUTTON_WHEELDOWN and processor_vertical_offset > -font_height*(len(code_textarea.value)-1):
                processor_vertical_offset -= font_height * 2
            elif e.button == BUTTON_WHEELUP and processor_vertical_offset < 0:
                processor_vertical_offset += font_height * 2
            elif e.button == BUTTON_LEFT:
                code_textarea.manager.cursor_pos.y = min(int(mouse_pos.y-processor_vertical_offset)//font_height, len(code_textarea.manager)-1)
                code_textarea.manager.cursor_pos.x = int(mouse_pos.x//font_width-linelog10)

    code_textarea.update(events)
    processor_cursor_pos[0] = FONT.size(code_textarea.manager.left[-1])[0]/font_width
    processor_cursor_pos[1] = code_textarea.manager.cursor_pos.y

    try:
        excepp.clear()
        mlython_str = COMPILER.compile(str(code_textarea)).splitlines()
        len_decoded = len(mlython_str)
    except Exception as e:
        excepp.append(e)
        mlython_str = []
        len_decoded = 0

    linelog10 = ceil(log10(len(code_textarea)))
    if len_decoded:
        while len(decoded) != len_decoded:
            if len(decoded) < len_decoded:
                decoded.append("")
            elif len(decoded) > len_decoded:
                decoded.pop()

        while timer >= processor_speed:
            timer -= processor_speed
            processor_textbuffer += str(processor_counter)

            try:
                raw_line: str = mlython_str[processor_counter]
                decoded[processor_counter] = ""
                if raw_line:  # if not empty
                    k = raw_line.split()
                    if k[0] == "op" and k[2] not in globals():
                        exec(f"if \"{k[2]}\" not in dir(): global {k[2]}\n{k[2]} = 0")
                    _ = mlog_to_python(raw_line)
                    decoded[processor_counter] = _
                    exec(_)
            except Exception as e:
                decoded[processor_counter] = ""
                excepp.append(e)
            processor_counter = processor_counter + 1 if processor_counter < len_decoded else 0

    WIN.blit(transform.flip(display1, False, True), (WIDTH/2-176, 0))

    for i in excepp:
        lineno: int = i.args[1][1] - 1 if len(i.args) > 1 else 0
        draw.rect(WIN, Cerror, (WIDTH-font_width, lineno*font_height+processor_vertical_offset, font_width, font_height))
        draw.rect(WIN, (Cerror[0]//4, Cerror[1]//4, Cerror[2]//4),
                  (0, lineno*font_height+processor_vertical_offset, WIDTH-font_width, font_height))
        if mouse_pos.x >= WIDTH-font_width and len(i.args) >= 1:
            WIN.blit(FONT.render(i.args[0], True, Cerror),
                     (WIDTH-FONT.size(i.args[0])[0]-font_width, font_height*lineno+processor_vertical_offset))

    for j, i in enumerate(decoded):
        if i == "NotImplemented":
            draw.rect(WIN, Cwarn, (WIDTH-font_width, j*font_height+processor_vertical_offset, font_width, font_height))
            draw.rect(WIN, (Cwarn[0]//4, Cwarn[1]//4, Cwarn[2]//4),
                           (0, j*font_height+processor_vertical_offset, WIDTH-font_width, font_height))
        if mouse_pos.x <= font_width:
            WIN.blit(FONT.render(f"{i!r}", True, Ctxt2),
                     (WIDTH-FONT.size(f"{i!r}")[0]-font_width, font_height*j+processor_vertical_offset))

    for j, i in enumerate(code_textarea.value):
        command_color: Color = Color(Cbg if not i else get_command_color(i.split(maxsplit=1)[0]))
        draw.rect(WIN, command_color,
                  (0, j*font_height+processor_vertical_offset, font_width*(linelog10), font_height))

        WIN.blit(FONT.render(f"{j+1}", True, (((command_color[0]+128) % 256)//2,
                                              ((command_color[1]+128) % 256)//2,
                                              ((command_color[2]+128) % 256)//2)), (0, font_height*j+processor_vertical_offset))

        WIN.blit(FONT.render(i, True, Ctxt),
                 (font_width*(linelog10+0.5), font_height*j+processor_vertical_offset))

    for j, i in enumerate(processor_textbuffer):
        text_surface = FONT.render(i, True, (127, 255, 127))
        WIN.blit(text_surface, text_surface.get_rect(bottomright=SC_RES/2+(0, font_height*j+processor_vertical_offset)))
    processor_textbuffer = ""

    draw.aaline(WIN, Coutline, (font_width*linelog10, 0), (font_width*linelog10, HEIGHT))
    if code_textarea.cursor_visible:
        draw.rect(WIN, (255, 255, 255),
                  ((processor_cursor_pos[0]+(linelog10+0.5))*font_width, (processor_cursor_pos[1])*font_height+processor_vertical_offset,
                   code_textarea.cursor_width, font_height))

    display.set_caption(f"{code_textarea.filename} | {len(excepp)} error{'s' if len(excepp) != 1 else ''}")
    WIN.blits([(FONT.render(var, True, Ctxt2), (WIDTH/2, font_height*(y+1)))
               for y, var in enumerate((f"{i[0]} = {i[1]!r}"
                                        for i in globals().items()
                                        if i[0] not in ("__name__", "__doc__", "__package__", "__loader__", "__spec__", "__annotations__", "__builtins__", "__file__", "__cached__",
                                                        "mlog_to_python", "TextInputManager", "TextInputVisualizer", "display", "draw", "event", "font", "key", "mouse", "time", "Surface",
                                                        "Vector2", "Color", "init", "squit", "K_ESCAPE", "QUIT", "list", "tuple", "ceil", "log10", "Path", "exit", "raw2d")))])

    display.flip()
    delta = CLOCK.tick(60)/1000
