import asyncio
import flet as ft

from .leftside import Userbar
from .rightside import Taskbar

class TheScreensController:
    """The controls to view windows screens in application."""
    def __init__(self, page: ft.Page, _) -> None:
        self.page: ft.Page = page
        self._: str = _

        self.userbar: Userbar = Userbar(page, _)
        self.taskbar: Taskbar = Taskbar(page, _)

        self.row: ft.Row = ft.Row()
        self.row.controls = [self.userbar, self.taskbar]
        self.row.expand = True

        self.page.add(self.row)
        self.page.update()

        self.page.pubsub.subscribe(self.update)

    async def update(self, message):
        """Event handler to update some containers data."""
        await asyncio.gather(
            self.userbar.callback(),
            self.taskbar.callback(),
        )
