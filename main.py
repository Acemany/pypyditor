#!/usr/env/bin python

from pathlib import Path
from typing import TypedDict

from pygame import (display, draw, event, key, mouse, time, transform,
                    QUIT,
                    Surface, Vector2,
                    init,
                    K_ESCAPE)
from pyndustric import Compiler

from mlog_lib import setup, mlog_to_python, \
    TextInputManager, TextInputVisualizer, ColorValue, \
    FONT, \
    app_path, Cbg, Ctxt, Ctxt2, Cerror, Cwarn, font_width, font_height


init()
setup()
WIN: Surface = display.set_mode()
SC_RES: Vector2 = Vector2(WIN.get_size())
WIDTH, HEIGHT = SC_RES
CLOCK: time.Clock = time.Clock()
COMPILER = Compiler()

save_path: Path = app_path

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

ProcType = TypedDict('ProcType', {
    'processor_counter': int,
    'processor_width': int,
    'processor_color': ColorValue,
    'processor_textbuffer': str,
    'processor_surface': Surface,
    'cell1': list[str],
})

processor_speed: float = 1/240
processor_context: ProcType = {
    "processor_counter": 0,
    "processor_width": 1,
    "processor_color": 0,
    "processor_textbuffer": "",
    "processor_surface": Surface((176, 176)),
    "cell1": ["" for _ in range(64)],
}


class Processor:
    @property
    def counter(self) -> int:
        return processor_context["processor_counter"]

    @counter.setter
    def counter(self, a: int):
        processor_context["processor_counter"] = a

    @property
    def textbuffer(self) -> str:
        return processor_context["processor_textbuffer"]

    @textbuffer.setter
    def textbuffer(self, a: str):
        processor_context["processor_textbuffer"] = a

    @property
    def surface(self) -> Surface:
        return processor_context["processor_surface"]


processor = Processor()
display1: Surface = Surface(processor.surface.get_size())
text_surface: Surface
decoded: list[str] = ["" for _ in range(len(code_textarea.value))]
excepp = list[Exception]()
mlython_str: list[str] = []
len_decoded: int = 0
timer: float = 0

processor.surface.fill(Cbg)


while True:
    timer += delta
    WIN.fill(Cbg)

    mouse_pos.update(mouse.get_pos())
    mouse_pressed = mouse.get_pressed()
    keys_pressed = key.get_pressed()
    events = event.get()

    for e in events:
        if e.type == QUIT or keys_pressed[K_ESCAPE]:
            code_textarea.close()

    code_textarea.update(events)

    try:
        excepp.clear()
        decoded.clear()
        mlython_str = COMPILER.compile(str(code_textarea)).splitlines()
        len_decoded = len(mlython_str)
    except Exception as e:
        excepp.append(e)
        mlython_str = []
        len_decoded = 0

    if len_decoded:
        while timer >= processor_speed:
            processor.counter %= len_decoded
            timer -= processor_speed

            if raw_line := mlython_str[processor.counter]:  # if not empty
                k = raw_line.split()
                decoded.append(tr := mlog_to_python(raw_line))
                if k[0] == "op" and k[2] not in globals():
                    tr = f"if \"{k[2]}\" not in dir(): global {k[2]}\n{k[2]} = 0\n{tr}"

                try:
                    exec(tr, processor_context)  # type: ignore
                except Exception as e:
                    excepp.append(e)

            processor.counter = processor.counter + 1

    WIN.blit(transform.flip(display1, False, True), (WIDTH/2-176, 0))

    for j, i in enumerate(excepp):
        lineno: int = i.args[1][1] - 1 if len(i.args) > 1 else j
        draw.rect(WIN, Cerror, (WIDTH-font_width, lineno*font_height+code_textarea.v_offset, font_width, font_height))
        if mouse_pos.x >= WIDTH-font_width and len(i.args) >= 1:
            draw.rect(WIN, (Cerror[0]//4, Cerror[1]//4, Cerror[2]//4),
                      (0, lineno*font_height+code_textarea.v_offset, WIDTH-font_width, font_height))
            WIN.blit(FONT.render(i.args[0], True, Cerror),
                     (WIDTH-FONT.size(i.args[0])[0]-font_width, font_height*lineno+code_textarea.v_offset))

    for j, i in enumerate(decoded):
        if i == "NotImplemented":
            draw.rect(WIN, Cwarn, (WIDTH-font_width, j*font_height+code_textarea.v_offset, font_width, font_height))
            if mouse_pos.x >= WIDTH-font_width:
                draw.rect(WIN, (Cwarn[0]//4, Cwarn[1]//4, Cwarn[2]//4),
                               (0, j*font_height+code_textarea.v_offset, WIDTH-font_width, font_height))
        if mouse_pos.x <= font_width:
            WIN.blit(FONT.render(f"{i!r}", True, Ctxt2),
                     (WIDTH-FONT.size(f"{i!r}")[0]-font_width, font_height*j+code_textarea.v_offset))

    WIN.blit(code_textarea.surface, (0, 0))

    for j, i in enumerate(processor.textbuffer.split('\n')):
        text_surface = FONT.render(i, True, (127, 255, 127))
        WIN.blit(text_surface, text_surface.get_rect(bottomright=SC_RES/2+(0, font_height*j+code_textarea.v_offset)))
    processor.textbuffer = ""

    display.set_caption(f"{code_textarea.filename} - {len(excepp)} error{'s' if len(excepp) != 1 else ''}")
    if False:
        WIN.blits([(FONT.render(var, True, Ctxt2), (WIDTH/2, font_height*(y+1)))
                   for y, var in enumerate((f"{i[0]} = {i[1]!r}"
                                            for i in globals().items()
                                            if i[0] not in ("__name__", "__doc__", "__package__", "__loader__", "__spec__", "__annotations__", "__builtins__", "__file__", "__cached__",
                                                            "_exit", "Path", "display", "draw", "event", "key", "mouse", "time", "transform", "copyright",
                                                            "QUIT", "Surface", "Vector2", "init", "squit", "K_ESCAPE", "Compiler", "setup", "mlog_to_python", "TextInputManager", "TextInputVisualizer", "FONT",
                                                            "app_path", "Cbg", "Ctxt", "Ctxt2", "Cerror", "Cwarn", "font_width", "font_height", "processor_context")))])

    display.flip()
    delta = CLOCK.tick(60)/1000
