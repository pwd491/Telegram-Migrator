import flet as ft

from ..database import SQLite


class Settings(ft.AlertDialog):
    """Class of settings."""
    def __init__(self, page: ft.Page, _) -> None:
        super().__init__()
        self.database: SQLite = SQLite()
        self.page: ft.Page = page

        """!!!"""
        self.options: list[int] = self.database.get_options()
        self.options = self.options[1:] if self.options is not None else \
            [False for __ in range(20)]

        self.c1 = ft.Checkbox(
            label=_("Synchronize my favorite messages"),
            value=bool(self.options[0]),
            disabled=False,
        )
        self.c2 = ft.Checkbox(
            label=_("Synchronize my profile first name, last name and biography."),
            value=bool(self.options[1]),
            disabled=False
        )
        self.c3 = ft.Checkbox(
            label=_("Synchronize my profile photos and videos avatars."),
            value=bool(self.options[2]),
            disabled=False
        )
        self.c4 = ft.Checkbox(
            label=_("Synchronize my public channels and groups."),
            value=bool(self.options[3]),
            disabled=False
        )
        self.c5 = ft.Checkbox(
            label=_("Synchronize my privacy settings."),
            value=bool(self.options[4]),
            disabled=False
        )
        self.c6 = ft.Checkbox(
            label=_("Synchronize my secure settings."),
            value=bool(self.options[5]),
            disabled=False
        )
        self.c7 = ft.Checkbox(
            label=_("Synchronize my stickers, emojis and gifs."),
            value=bool(self.options[6]),
            disabled=False
        )
        self.c8 = ft.Checkbox(
            label=_("Synchronize my bots."),
            value=bool(self.options[7]),
            disabled=False
        )
        """!!!"""

        x = [
            self.c1,
            self.c2,
            self.c3,
            self.c4,
            self.c5,
            self.c6,
            self.c7,
            self.c8
        ]
        x.sort(key=lambda x: x.disabled is True)

        self.column = ft.Container()
        self.column.content = ft.Column(x)
        self.column.content.scroll = ft.ScrollMode.AUTO
        self.column.height = 350

        self.wrapper = ft.Container()
        self.wrapper.content = self.column

        self.modal = True
        self.title = ft.Row([
            ft.Icon(ft.icons.SETTINGS),
            ft.Text(_("Settings"))
        ])
        self.content = self.wrapper
        self.actions = [
            ft.TextButton(_("Cancel"), on_click=self.close),
            ft.FilledButton(_("Save"), on_click=self.save),
        ]
        self.actions_alignment = ft.MainAxisAlignment.SPACE_BETWEEN

    async def close(self, e) -> None:
        """Close dialog."""
        self.open = False
        self.page.dialog.clean()
        self.update()

    async def save(self, e) -> None:
        """Save options for primary user."""
        self.database.set_options(
            int(self.c1.value),
            int(self.c2.value),
            int(self.c3.value),
            int(self.c4.value),
            int(self.c5.value),
            int(self.c6.value),
            int(self.c7.value),
            int(self.c8.value),
        )
        self.page.pubsub.send_all("update")
        self.page.dialog.clean()
        self.open = False
        self.update()
