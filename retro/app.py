import asyncio
import logging
from io import StringIO
from time import time

from prompt_toolkit import Application, HTML
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.formatted_text import to_formatted_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, WindowAlign
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout

from retro.persistence import Category, RetroStore, InMemoryStore

logger = logging.getLogger(__name__)


def start_app(store: RetroStore, connection_string: str = ""):
    kb = KeyBindings()

    @kb.add("c-q")
    def exit_(event):
        event.app.exit()

    @kb.add("c-r")
    def refresh_(event):
        refresh()

    def refresh():
        items = store.list()

        texts = {
            Category.GOOD: StringIO(),
            Category.NEUTRAL: StringIO(),
            Category.BAD: StringIO(),
        }
        for item in items:
            if item.done:
                texts[item.category].write(f"{item.key}. ✅ <s>{item.text}</s>\n")
            else:
                texts[item.category].write(f"{item.key}. {item.text}\n")

        good_buffer.text = to_formatted_text(HTML(texts[Category.GOOD].getvalue()))
        neutral_buffer.text = to_formatted_text(
            HTML(texts[Category.NEUTRAL].getvalue())
        )
        bad_buffer.text = to_formatted_text(HTML(texts[Category.BAD].getvalue()))

    @kb.add("c-m")
    def enter_(event):
        text = input_buffer.text

        if text.startswith("+"):
            input_buffer.reset()
            store.add_item(text[1:].strip(), Category.GOOD)
        elif text.startswith("."):
            input_buffer.reset()
            store.add_item(text[1:].strip(), Category.NEUTRAL)
        elif text.startswith("-"):
            input_buffer.reset()
            store.add_item(text[1:].strip(), Category.BAD)
        elif text.startswith("!"):
            input_buffer.reset()
            store.toggle(int(text[1:].strip()))

        elif text.startswith("mv "):
            cmd, key, column = text.split()

            categories = {
                "+": Category.GOOD,
                ".": Category.NEUTRAL,
                "-": Category.BAD,
            }

            input_buffer.reset()
            store.move_item(int(key), categories[column])

        elif text.startswith("rm "):
            cmd, key = text.split()

            input_buffer.reset()
            store.remove(int(key))

        refresh()

    @kb.add("c-p")
    def ping_(event):
        start = time()
        store.list(Category.GOOD)
        app.print_text(f"latency: {time() - start:.3f}")

    good_buffer = FormattedTextControl()
    neutral_buffer = FormattedTextControl()
    bad_buffer = FormattedTextControl()

    input_buffer = Buffer()
    input = Window(content=BufferControl(buffer=input_buffer), height=1)

    root_container = HSplit(
        [
            VSplit(
                [
                    HSplit(
                        [
                            Window(
                                content=FormattedTextControl(text=":)"),
                                height=1,
                                align=WindowAlign.CENTER,
                            ),
                            Window(height=1, char="-"),
                            Window(content=good_buffer),
                        ],
                        style="fg:white bold bg:ansigreen",
                    ),
                    Window(width=2, char="|"),
                    HSplit(
                        [
                            Window(
                                content=FormattedTextControl(text=":|"),
                                height=1,
                                align=WindowAlign.CENTER,
                            ),
                            Window(height=1, char="-"),
                            Window(content=neutral_buffer),
                        ],
                        style="fg:white bold bg:ansiyellow",
                    ),
                    Window(width=2, char="|"),
                    HSplit(
                        [
                            Window(
                                content=FormattedTextControl(text=":("),
                                height=1,
                                align=WindowAlign.CENTER,
                            ),
                            Window(height=1, char="-"),
                            Window(content=bad_buffer),
                        ],
                        style="fg:white bold bg:ansired",
                    ),
                ]
            ),
            Window(
                content=FormattedTextControl(text=f"Invite: {connection_string}"),
                height=1,
                align=WindowAlign.CENTER,
            ),
            input,
        ],
        style="bg:grey",
    )

    layout = Layout(root_container)
    layout.focus(input)

    app = Application(layout=layout, key_bindings=kb, full_screen=True)

    async def active_refresh():
        counter = 0
        while counter < 5:
            try:
                refresh()
                await asyncio.sleep(2)
            except:
                counter += 1
                logger.exception(f"Refresh failed for the {counter}. time")

        logger.error(f"Refresh failed too often, fallback tu manual refresh.")

    app.create_background_task(active_refresh())

    app.run()


if __name__ == "__main__":
    start_app(InMemoryStore())
