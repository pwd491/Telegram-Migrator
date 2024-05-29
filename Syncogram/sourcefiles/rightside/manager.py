import asyncio
from datetime import datetime
from typing import Callable, Coroutine

import flet as ft
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.messages import ToggleDialogPinRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.custom.dialog import Dialog
from telethon.tl.patched import MessageService
from telethon.tl.types import UserFull, Message, Photo, Chat
from telethon.tl.types.account import PrivacyRules
from telethon.tl.functions.photos import (UploadProfilePhotoRequest)
from telethon.tl.functions.account import (
    UpdateProfileRequest,
    GetGlobalPrivacySettingsRequest,
    SetGlobalPrivacySettingsRequest,
    GetPrivacyRequest,
    SetPrivacyRequest,
)
from telethon.tl.types import (
    InputPrivacyKeyPhoneNumber,
    InputPrivacyKeyAddedByPhone,
    InputPrivacyKeyStatusTimestamp,
    InputPrivacyKeyProfilePhoto,
    InputPrivacyKeyAbout,
    InputPrivacyKeyBirthday,
    InputPrivacyKeyForwards,
    InputPrivacyKeyPhoneCall,
    InputPrivacyKeyPhoneP2P,
    InputPrivacyKeyChatInvite,
    InputPrivacyKeyVoiceMessages,

    InputPrivacyValueAllowAll,
    InputPrivacyValueAllowPremium,
    InputPrivacyValueAllowContacts,
    InputPrivacyValueAllowUsers,
    InputPrivacyValueDisallowUsers,
    InputPrivacyValueDisallowAll,
    InputPrivacyValueAllowCloseFriends,
    InputPrivacyValueDisallowContacts,
    InputPrivacyValueAllowChatParticipants,
    InputPrivacyValueDisallowChatParticipants,

    PrivacyValueAllowAll,
    PrivacyValueAllowUsers,
    PrivacyValueAllowPremium,
    PrivacyValueAllowContacts,
    PrivacyValueDisallowUsers,
    PrivacyValueDisallowAll,
    PrivacyValueAllowCloseFriends,
    PrivacyValueDisallowContacts,
    PrivacyValueAllowChatParticipants,
    PrivacyValueDisallowChatParticipants,

    TypeInputPrivacyKey,
    TypePrivacyRule,
    TypeGlobalPrivacySettings
)



from ..telegram import UserClient
from ..database import SQLite
from ..components import Task


class Manager:
    """The manager to control options UI and Coroutines."""
    def __init__(self, page: ft.Page, _) -> None:
        self.page: ft.Page = page
        self.database = SQLite()
        self.client = UserClient

        self.options = {
            "is_sync_fav": {
                "title": _("Synchronize my favorite messages between accounts."),
                "description": _(
                    "Sync messages in your favorite chat with the correct sequence, re-replies to messages and pinned messages. The program can synchronize up to 100 messages per clock cycle."
                ),
                "function": self.sync_favorite_messages,
                "status": bool(False),
                "ui": Task,
            },
            "is_sync_profile_name": {
                "title": _(
                    "Synchronize the first name, last name and biography of the profile."
                ),
                "description": _(
                    "Synchronization of the first name, last name and profile description. If you do not specify the data, it will be overwritten as empty fields."
                ),
                "function": self.sync_profile_first_name_and_second_name,
                "status": bool(False),
                "ui": Task,
            },
            "is_sync_profile_media": {
                "title": _("Synchronize account photos and videos avatars."),
                "description": _(
                    "Sync photo and video avatars in the correct sequence. If there are a lot of media files, the program sets an average limit between requests to the servers in order to circumvent the restrictions."
                ),
                "function": self.sync_profile_media,
                "status": bool(False),
                "ui": Task,
            },
            "is_sync_public_channels_and_groups": {
                "title": _("Synchronize public channels and groups."),
                "description": _(
                    "Synchronizes public channels ang groups. If the channel or groups was archived or pinned, the program will save these parameters."
                ),
                "function": self.sync_public_channels_and_groups,
                "status": bool(False),
                "ui": Task,
            },
            "is_sync_privacy": {
                "title": _("Synchronize privacy settings."),
                "description": _(
                    "Synchronizes the privacy settings for the account. If the sync account does not have Telegram Premium, then the corresponding premium settings will not be synchronized."
                ),
                "function": self.sync_privacy_settings,
                "status": bool(False),
                "ui": Task,
            },
        }
        self.callback()

    def update_options_dict(self):
        """Get options list and update dict variable."""
        list_of_options = self.database.get_options()
        if list_of_options is None:
            return
        list_of_options = list_of_options[1:]

        for n, option in enumerate(self.options.items()):
            option[1].update({"status": bool(list_of_options[n])})

        for option in self.options.items():
            if option[1].get("status"):
                title = option[1].get("title")
                desc = option[1].get("description")
                option[1].update({"ui": Task(title, desc)})

    def get_ui_tasks(self) -> list[Task]:
        """Return UI list of will be execute tasks."""
        lst = []
        for option in self.options.items():
            if option[1].get("status"):
                lst.append(option[1].get("ui"))
        return lst

    def get_tasks_coroutines(self) -> list[Coroutine]:
        """Return coroutines objects."""
        lst = []
        for option in self.options.items():
            if option[1].get("status"):
                lst.append(option[1].get("function"))
        return lst

    def get_coroutines_with_ui(self) -> list[Callable[[Task], None]]:
        """Return dict object."""
        lst = []
        for option in self.options.items():
            if option[1].get("status"):
                func = option[1].get("function")
                ui = option[1].get("ui")
                lst.append(func(ui))
        return lst

    def callback(self):
        """Callback"""
        self.update_options_dict()

    async def sync_favorite_messages(self, ui: Task):
        """
        An algorithm for forwarding messages to the recipient entity is
        implemented.
        """
        ui.default()
        sender = self.client(self.database.get_session_by_status(1))
        recepient = self.client(self.database.get_session_by_status(0))

        sender_username = self.database.get_username_by_status(1)
        recepient_username = self.database.get_username_by_status(0)

        if not (sender.is_connected() and recepient.is_connected()):
            await sender.connect()
            await recepient.connect()

        sender_entity = await recepient.get_input_entity(sender_username)
        recepient_entity = await sender.get_input_entity(recepient_username)

        # Getting messages from sender source
        source_messages = await sender.get_messages(
            sender_entity, min_id=0, max_id=0, reverse=True
        )

        is_grouped_id = None
        is_pinned = False
        is_replied = False
        group = []
        msg_ids = {}

        async def recepient_save_message(
            message_id, message_length, is_pin: bool, is_reply: None | Message
        ):
            data = await recepient.get_messages(sender_entity, limit=message_length)
            messages = [message for message in data]
            if is_reply:
                destination_message_id = msg_ids.get(is_reply.reply_to_msg_id)
                if messages[0].media:
                    await asyncio.sleep(3)
                    message = await recepient.send_message(
                        recepient_entity,
                        messages[-1].message,
                        file=messages,
                        reply_to=destination_message_id,
                    )
                    msg_ids[message_id] = message[0].id
                else:
                    await asyncio.sleep(3)
                    message = await recepient.send_message(
                        recepient_entity,
                        message=messages[0],
                        reply_to=destination_message_id,
                    )
                    msg_ids[message_id] = message.id
            else:
                message = await recepient.forward_messages(recepient_entity, messages)
                msg_ids[message_id] = message[0].id

            if is_pin:
                await asyncio.sleep(3)
                await recepient.pin_message(recepient_entity, message[0])
            await asyncio.sleep(3)
            await recepient.delete_messages(sender_entity, messages)

        try:
            ui.progress_counters.visible = True
            ui.total = source_messages.total
            for i, message in enumerate(source_messages, 1):
                ui.value = i
                if not isinstance(message, MessageService):
                    if message.grouped_id is not None:
                        if message.pinned:
                            is_pinned = True
                        if message.reply_to:
                            is_replied = message.reply_to
                        if is_grouped_id != message.grouped_id:
                            is_grouped_id = message.grouped_id
                            if group:
                                await asyncio.sleep(3)
                                await sender.forward_messages(
                                    recepient_entity, group, silent=True
                                )
                                await recepient_save_message(
                                    message.id, len(group), is_pinned, is_replied
                                )
                                is_pinned = False
                                is_replied = False
                                group.clear()
                        group.append(message)
                        continue
                    if group:
                        await asyncio.sleep(3)
                        await sender.forward_messages(
                            recepient_entity, group, silent=True
                        )
                        await recepient_save_message(
                            message.id, len(group), is_pinned, is_replied
                        )
                        is_pinned = False
                        is_replied = False
                        group.clear()

                    await asyncio.sleep(3)
                    await sender.forward_messages(
                        recepient_entity, message, silent=True
                    )
                    await recepient_save_message(
                        message.id, 1, message.pinned, message.reply_to
                    )

            if group:
                await asyncio.sleep(3)
                await sender.forward_messages(recepient_entity, group, silent=True)
                await recepient_save_message(
                    group[-1].id, len(group), is_pinned, is_replied
                )
                is_pinned = False
                is_replied = False
                group.clear()
        except Exception as e:
            ui.unsuccess(e)
            return
        ui.success()

    async def sync_profile_first_name_and_second_name(self, ui: Task):
        """
        Connecting accounts, getting profile data and sets.
        """
        ui.default()

        sender = self.client(self.database.get_session_by_status(1))
        recepient = self.client(self.database.get_session_by_status(0))

        if not (sender.is_connected() and recepient.is_connected()):
            await sender.connect()
            await recepient.connect()

        ui.progress_counters.visible = True
        ui.total = 3
        try:
            user: UserFull = await sender(GetFullUserRequest("me"))
            first_name = user.users[0].first_name
            first_name = "" if first_name is None else first_name
            ui.value = 1
            last_name = user.users[0].last_name
            last_name = "" if last_name is None else last_name
            ui.value = 2
            bio = user.full_user.about
            bio = "" if bio is None else bio
            ui.value = 3
            await recepient(UpdateProfileRequest(first_name, last_name, bio))
        except Exception as e:
            ui.unsuccess(e)
            return
        ui.success()

    async def sync_profile_media(self, ui: Task):
        """
        The algorithm for synchronizing profile photo and video avatars to 
        the recipient's essence.
        """
        ui.default()
        sender = self.client(self.database.get_session_by_status(1))
        recepient = self.client(self.database.get_session_by_status(0))

        if not (sender.is_connected() and recepient.is_connected()):
            await sender.connect()
            await recepient.connect()

        image_extension = ".jpeg"
        video_extension = ".mp4"
        photo: Photo
        try:
            photos = await sender.get_profile_photos("me")
            ui.progress_counters.visible = True
            ui.total = photos.total
            for i, photo in enumerate(reversed(photos), 1):
                ui.value = i
                await asyncio.sleep(3)
                blob = await sender.download_media(photo, bytes)
                name = "Syncogram_" + datetime.strftime(
                    photo.date, "%Y_%m_%d_%H_%M_%S"
                )
                if not photo.video_sizes:
                    file = await recepient.upload_file(
                        blob,
                        file_name=name + image_extension
                    )
                    await recepient(UploadProfilePhotoRequest(file=file))
                    continue
                file = await recepient.upload_file(
                    blob,
                    file_name=name + video_extension
                )
                await recepient(UploadProfilePhotoRequest(video=file))
        except Exception as e:
            ui.unsuccess(e)
            return
        ui.success()

    async def sync_public_channels_and_groups(self, ui: Task):
        """
        The algorithm for synchronizing public channels, 
        the status of pinning and archiving.
        """
        ui.default()

        sender = self.client(self.database.get_session_by_status(1))
        recepient = self.client(self.database.get_session_by_status(0))

        if not (sender.is_connected() and recepient.is_connected()):
            await sender.connect()
            await recepient.connect()

        source = await sender.get_dialogs()
        channels: list[Dialog] = []

        dialog: Dialog
        for dialog in source:
            if not isinstance(dialog.entity, Chat) \
                and not dialog.is_user \
                    and dialog.entity.username:
                channels.append(dialog)

        ui.progress_counters.visible = True
        ui.total = len(channels)

        channel: Dialog
        try:
            for i, channel in enumerate(channels, 1):
                await asyncio.sleep(12)
                await recepient(JoinChannelRequest(channel.entity.username))
                if channel.archived:
                    await asyncio.sleep(2.5)
                    await recepient.edit_folder(channel.entity.username, 1)
                if channel.pinned:
                    await asyncio.sleep(2.5)
                    await recepient(ToggleDialogPinRequest(
                        channel.entity.username,
                        True
                    ))
                ui.value = i
        except Exception as e:
            ui.unsuccess(e)
            return
        ui.success()


    async def sync_privacy_settings(self, ui: Task):
        """The algorithm for synchronizing privacy settings."""
        ui.default()

        sender = self.client(self.database.get_session_by_status(1))
        recepient = self.client(self.database.get_session_by_status(0))

        if not sender.is_connected() or not recepient.is_connected():
            await sender.connect()
            await recepient.connect()

        input_privacies: list[TypeInputPrivacyKey] = [
            InputPrivacyKeyPhoneNumber(),
            InputPrivacyKeyAddedByPhone(),
            InputPrivacyKeyStatusTimestamp(),
            InputPrivacyKeyProfilePhoto(),
            InputPrivacyKeyAbout(),
            InputPrivacyKeyBirthday(),
            InputPrivacyKeyForwards(),
            InputPrivacyKeyPhoneCall(),
            InputPrivacyKeyPhoneP2P(),
            InputPrivacyKeyChatInvite(),
            InputPrivacyKeyVoiceMessages(),
        ]

        try:
            ui.progress_counters.visible = True
            ui.total = len(input_privacies) + 1
            i: int
            for i, privacy in enumerate(input_privacies, 1):
                await asyncio.sleep(1)
                rules: list[TypePrivacyRule] = []
                request: PrivacyRules = await sender(
                    GetPrivacyRequest(
                        privacy
                    )
                )

                for rule in request.rules:
                    if isinstance(rule, PrivacyValueAllowAll):
                        rules.append(InputPrivacyValueAllowAll())

                    if isinstance(rule, PrivacyValueAllowUsers):
                        rules.append(InputPrivacyValueAllowUsers([]))

                    if isinstance(rule, PrivacyValueAllowPremium):
                        rules.append(InputPrivacyValueAllowPremium())

                    if isinstance(rule, PrivacyValueAllowContacts):
                        rules.append(InputPrivacyValueAllowContacts())

                    if isinstance(rule, PrivacyValueAllowCloseFriends):
                        rules.append(InputPrivacyValueAllowCloseFriends())

                    if isinstance(rule, PrivacyValueAllowChatParticipants):
                        rules.append(InputPrivacyValueAllowChatParticipants([]))

                    if isinstance(rule, PrivacyValueDisallowAll):
                        r = True
                        for k in rules:
                            if isinstance(k, InputPrivacyValueAllowContacts):
                                r = False
                                break
                        if r:
                            rules.append(InputPrivacyValueDisallowAll())

                    if isinstance(rule, PrivacyValueDisallowUsers):
                        rules.append(InputPrivacyValueDisallowUsers([]))

                    if isinstance(rule, PrivacyValueDisallowContacts):
                        rules.append(InputPrivacyValueDisallowContacts())

                    if isinstance(rule, PrivacyValueDisallowChatParticipants):
                        rules.append(InputPrivacyValueDisallowChatParticipants([]))

                await recepient(
                    SetPrivacyRequest(
                        key=privacy,
                        rules=rules
                    )
                )
                ui.value = i

            data: TypeGlobalPrivacySettings = await sender(
                GetGlobalPrivacySettingsRequest()
            )

            await recepient(
                SetGlobalPrivacySettingsRequest(
                    TypeGlobalPrivacySettings(
                        data.archive_and_mute_new_noncontact_peers,
                        data.keep_archived_unmuted,
                        data.keep_archived_folders,
                        data.hide_read_marks,
                        data.new_noncontact_peers_require_premium
                    )
                )
            )
            ui.value = i + 1
        except Exception as e:
            ui.unsuccess(e)
            return

        ui.success()
