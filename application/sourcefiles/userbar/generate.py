from functools import partial
from typing import Any

import flet as ft

from .errors import ErrorAddAccount
from .authenticate import AuthenticationDialogProcedure
from ..database import SQLite


class UIGenerateAccounts(ft.UserControl):
    def __init__(self, page: ft.Page, *args, **kwargs) -> None:
        self.page: ft.Page = page
        self.database = SQLite()

        self.divider = ft.Container()
        self.divider.width = 200
        self.divider.height = 0.5
        self.divider.bgcolor = ft.colors.ON_SECONDARY_CONTAINER

        self.account_primary = ft.Column()
        self.account_primary.controls = [
            ft.Row([self.label("From:")]),
            ft.Row([self.divider]),
            ft.Row([self.add_button(True)]),
        ]

        self.account_secondary = ft.Column()
        self.account_secondary.controls = [
            ft.Row([self.label("Where:")]),
            ft.Row([self.divider]),
            ft.Row([self.add_button(False)]),
        ]

        self.wrapper_column = ft.Column()
        self.wrapper_column.controls = [self.account_primary, self.account_secondary]

        self.wrapper = ft.Container()
        self.wrapper.content = self.wrapper_column

        super().__init__()

    def account_button(self, account_id, account_name) -> ft.ElevatedButton:
        button = ft.ElevatedButton()
        button.width = 250
        button.height = 35
        button.text = account_name
        button.icon = ft.icons.ACCOUNT_CIRCLE
        button.bgcolor = ft.colors.SECONDARY_CONTAINER
        button.key = account_id
        button.on_click = ...
        return button

    def add_button(self, key: bool) -> ft.OutlinedButton:
        button = ft.OutlinedButton()
        button.height = 35
        button.text = "Add account"
        button.icon = ft.icons.ADD
        button.expand = True
        button.data = key
        button.on_click = partial(self.add_account, is_primary=button.data)
        return button

    def label(self, text: str) -> ft.Text:
        label = ft.Text()
        label.value = text
        label.size = 11
        label.opacity = 0.5
        return label


    async def add_account(self, e, is_primary: bool):
        accounts: list[Any] = self.database.get_users()
        for acc in accounts:
            if int(is_primary) == acc[2]:
                error = ErrorAddAccount()
                self.page.dialog = error
                error.open = True
                await self.generate()
                return await self.page.update_async()

        auth = AuthenticationDialogProcedure(self.page, self, is_primary)
        self.page.dialog = auth
        auth.open = True
        await self.page.update_async()


    async def generate(self) -> None:
        accounts: list[Any] = self.database.get_users()
        while len(self.account_primary.controls) > 3:
            self.account_primary.controls.pop(-2)
        while len(self.account_secondary.controls) > 3:
            self.account_secondary.controls.pop(-2)
        for account in accounts:
            if bool(account[2]):
                self.account_primary.controls.insert(
                    -1, self.account_button(account[0], account[1])
                )
            else:
                self.account_secondary.controls.insert(
                    -1, self.account_button(account[0], account[1])
                )
        await self.update_async()

    def build(self) -> ft.Container:
        return self.wrapper
