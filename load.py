"""
Example EDMC plugin.

It adds a single button to the EDMC interface that displays the number of times it has been clicked.
"""
from __future__ import annotations

import datetime
import logging
import time
import tkinter as tk
from tkinter import ttk
import os
from tkinter import Frame
from typing import Optional

import myNotebook as nb  # noqa: N813

from discord_messages import DiscordMessages
import threading
from chronos import Chronos

from ttkHyperlinkLabel import HyperlinkLabel
from config import appname, config

# This **MUST** match the name of the folder the plugin is in.
plugin_name = os.path.basename(os.path.dirname(__file__))

logger = logging.getLogger(f"{appname}.{plugin_name}")


class FleetCarrierTracker:
    """
    Fleet Carrier Tracker is a plugin for notify a discord chanel about fleet carrier jumps

    its use Discord integration via a webhook
    and optionally the inara link for your carrier
    """

    def __init__(self) -> None:

        # Development mode:
        # self.fct_is_dev_mode = True
        # self.fct_dev_webhook_url = "https://discord.com/api/webhooks/1335559907910488167/1hYslXMgBnAk4AqFda-0X0kqP74naXQP5mVur3Fjtsbe_sVI0MND4eWjZkWW7A0VTz8-"

        # Settings
        self.fct_discord_webhook_url = tk.StringVar(value=str(config.get_str('fct_discord_webhook_url')))
        self.fct_carrier_inara_url = tk.StringVar(value=str(config.get_str('fct_carrier_inara_url')))

        # Internal Variables
        self.fct_carrier_last_known_location = tk.StringVar()
        self.fct_is_jump_active = tk.BooleanVar(value=bool(config.get_bool('fct_is_jump_active')))

        self.fct_jump_destination = tk.StringVar(value=str(config.get_str('fct_jump_destination')))
        self.fct_jump_destination_id = tk.StringVar(value=str(config.get_str('fct_jump_destination_id')))
        self.fct_time_of_departure = tk.StringVar(value=str(config.get_str('fct_time_of_departure')))

        ### DM Instance
        if not self.fct_is_dev_mode:
            self.dm = DiscordMessages(self.fct_discord_webhook_url.get(), self.fct_carrier_inara_url.get())
            logger.info("Fleet Carrier Tracker - initiated")
        else:
            self.dm = DiscordMessages(self.fct_dev_webhook_url, self.fct_carrier_inara_url.get())
            logger.info("Fleet Carrier Tracker - initiated in development mode ")

        # Chronos instance
        self.ui_frame = None
        self.chronos = Chronos()

        # Tkinter variables for time tracking
        self.formated_remaining_time_for_departure = tk.StringVar(value="00:00:00")
        # self.seconds_remaining_for_departure = tk.IntVar(value=0)
        self.formated_remaining_time_for_lockdown = tk.StringVar(value="00:00:00")
        # self.seconds_remaining_for_lockdown = tk.IntVar(value=0)

        # Start Chronos without blocking
        if self.fct_is_jump_active.get():
            self.chronos.start(self.fct_time_of_departure.get())
        else:
            self.chronos.stop()

    def on_load(self) -> str:
        """
        on_load is called by plugin_start3 below.

        It is the first point EDMC interacts with our code after loading our module.

        :return: The name of the plugin, which will be used by EDMC for logging and for the settings window
        """

        return plugin_name

    def on_unload(self) -> None:
        """
        on_unload is called by plugin_stop below.

        It is the last thing called before EDMC shuts down. Note that blocking code here will hold the shutdown process.
        """

        # todo: turn of the threads if any running
        self.chronos.stop()
        self.on_preferences_closed("", False)  # Save our prefs

    def setup_preferences(self, parent: nb.Notebook, cmdr: str, is_beta: bool) -> nb.Frame | None:
        """
        setup_preferences is called by plugin_prefs below.

        It is where we can setup our own settings page in EDMC's settings window. Our tab is defined for us.

        :param parent: the tkinter parent that our returned Frame will want to inherit from
        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        :return: The frame to add to the settings window
        """

        PADX = 10  # noqa: N806
        BUTTONX = 12  # noqa: N806
        PADY = 1  # noqa: N806
        BOXY = 2  # noqa: N806
        SEPY = 10  # noqa: N806

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        current_row = 0

        HyperlinkLabel(
            frame,
            text='Fleet Carrier Tracker ',
            background=nb.Label().cget('background'),
            url='https://github.com/gaboreszaki/FleetCarrierTracker',
            underline=True
        ).grid(row=current_row, columnspan=2, padx=PADX, pady=PADY, sticky=tk.W)
        current_row += 1

        def test_discord_url(users_input):
            test_dm = DiscordMessages(users_input)
            test_dm.send_test_messages()

        nb.Label(frame, text='Discord Webhook URL:').grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        discord_input = nb.EntryMenu(frame, textvariable=self.fct_discord_webhook_url, show="*", width=30)
        discord_input.grid(row=current_row, column=1, padx=PADX, pady=BOXY, sticky=tk.EW)
        test_btn = ttk.Button(frame, command=lambda: test_discord_url(discord_input.get()), text="Send TEST message")
        test_btn.grid(row=current_row, column=2, padx=PADX, pady=BOXY, sticky=tk.EW)

        current_row += 1  # Always increment our row counter, makes for far easier tkinter design.

        nb.Label(frame, text='Inara Link for your carrier').grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.EntryMenu(frame, textvariable=self.fct_carrier_inara_url).grid(row=current_row, column=1, padx=PADX, pady=BOXY, sticky=tk.EW)
        current_row += 1

        return frame

    def on_preferences_closed(self, cmdr: str, is_beta: bool) -> None:
        """
        on_preferences_closed is called by prefs_changed below.

        It is called when the preferences dialog is dismissed by the user.

        :param cmdr: The current ED Commander
        :param is_beta: Whether or not EDMC is currently marked as in beta mode
        """
        # You need to cast to `int` here to store *as* an `int`, so that
        # `config.get_int()` will work for re-loading the value.

        config.set('fct_discord_webhook_url', str(self.fct_discord_webhook_url.get()))
        config.set('fct_carrier_inara_url', str(self.fct_carrier_inara_url.get()))

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        """
        Create our entry on the main EDMC UI.

        This is called by plugin_app below.

        :param parent: EDMC main window Tk
        :return: Our frame
        """
        PADX = 10  # noqa: N806
        BUTTONX = 12  # noqa: N806
        PADY = 1  # noqa: N806
        BOXY = 2  # noqa: N806
        SEPY = 10  # noqa: N806

        frame = nb.Frame(parent)
        frame.columnconfigure(1, weight=1)
        current_row = 0

        ttk.Label(frame, text="--- Fleet Carrier Tracker ---", anchor=tk.CENTER).grid(row=current_row, columnspan=2, sticky=tk.EW)
        current_row += 1

        # # Carrier ID
        # ttk.Label(frame, text="Carrier ID:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        # ttk.Label(frame, textvariable=self.fct_carrier_id).grid(row=current_row, column=1, sticky=tk.EW)
        # current_row += 1
        #
        # # Carrier Name
        # ttk.Label(frame, text="Carrier Name:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        # # ttk.Label(frame, textvariable=self.fct_carrier_name).grid(row=current_row, column=1, sticky=tk.EW)
        # HyperlinkLabel(frame, text=str(self.fct_carrier_name.get()), url=str(self.fct_carrier_inara_url.get()), background=nb.Label().cget('background'), underline=False).grid(row=current_row, column=1, sticky=tk.EW)
        # current_row += 1
        #
        # # Last known location
        # inara_search_url = "https://inara.cz/elite/starsystem/?search="
        # destination_link = str(f'{inara_search_url}{self.fct_jump_destination_id.get()}')
        #
        # ttk.Label(frame, text="Last known Location:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        # HyperlinkLabel(frame, textvariable=self.fct_jump_destination, url=destination_link, background=nb.Label().cget('background'), underline=False).grid(row=current_row, column=1, sticky=tk.EW)
        # current_row += 1
        #
        ttk.Label(frame, text="Time of departure:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        ttk.Label(frame, textvariable=self.fct_time_of_departure).grid(row=current_row, column=1, sticky=tk.EW)
        current_row += 1

        ### Displays:
        # is jump active
        ttk.Label(frame, text="is jump active:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        ttk.Label(frame, textvariable=self.fct_is_jump_active).grid(row=current_row, column=1, sticky=tk.EW)
        current_row += 1

        # time remaining until lockdown
        ttk.Label(frame, text="Time until lockdown:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        ttk.Label(frame, textvariable=self.formated_remaining_time_for_lockdown).grid(row=current_row, column=1, sticky=tk.EW)
        current_row += 1

        # time remaining until jump
        ttk.Label(frame, text="Time until jump:", anchor=tk.W).grid(row=current_row, column=0, sticky=tk.EW)
        ttk.Label(frame, textvariable=self.formated_remaining_time_for_departure).grid(row=current_row, column=1, sticky=tk.EW)
        current_row += 1

        # Start the time tracker
        self.ui_frame = frame  # Store reference AFTER creating frame
        return frame

    def update_config(self):
        # Update config
        try:
            if self.fct_jump_destination.get():
                config.set('fct_jump_destination', str(self.fct_jump_destination.get()))
            if self.fct_jump_destination_id.get():
                config.set('fct_jump_destination_id', str(self.fct_jump_destination_id.get()))
            if self.fct_time_of_departure.get():
                config.set('fct_time_of_departure', str(self.fct_time_of_departure.get()))

            config.set('fct_is_jump_active', self.fct_is_jump_active.get())

        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")

    def start_tracking_time(self):

        logger.info(self.chronos.formated_remaining_time_for_departure)
        logger.info(self.chronos.formated_remaining_time_for_lockdown)

        self.formated_remaining_time_for_departure.set(self.chronos.formated_remaining_time_for_departure)
        # self.seconds_remaining_for_departure.set(self.chronos.seconds_remaining_for_departure)
        self.formated_remaining_time_for_lockdown.set(self.chronos.formated_remaining_time_for_lockdown)
        # self.seconds_remaining_for_lockdown.set(self.chronos.seconds_remaining_for_lockdown)

        if self.fct_is_jump_active.get():
            # Schedule the next update in 1 second
            self.ui_frame.after(1000, self.start_tracking_time)
        else:
            logger.info("chronos stopped")
            self.chronos.stop()


fct = FleetCarrierTracker()


# Note that all of these could be simply replaced with something like:
# plugin_start3 = cc.on_load
def plugin_start3(plugin_dir: str) -> str:
    """
    Handle start up of the plugin.

    See PLUGINS.md#startup
    """
    return fct.on_load()


def plugin_stop() -> None:
    """
    Handle shutdown of the plugin.

    See PLUGINS.md#shutdown
    """
    return fct.on_unload()


def plugin_prefs(parent: nb.Notebook, cmdr: str, is_beta: bool) -> nb.Frame | None:
    """
    Handle preferences tab for the plugin.

    See PLUGINS.md#configuration
    """
    return fct.setup_preferences(parent, cmdr, is_beta)


def prefs_changed(cmdr: str, is_beta: bool) -> None:
    """
    Handle any changed preferences for the plugin.

    See PLUGINS.md#configuration
    """
    return fct.on_preferences_closed(cmdr, is_beta)


def plugin_app(parent: tk.Frame) -> tk.Frame | None:
    """
    Set up the UI of the plugin.

    See PLUGINS.md#display
    """
    frame = fct.setup_main_ui(parent)
    fct.start_tracking_time()
    return frame


def journal_entry(cmdrname: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> None:
    if entry['event'] == 'CarrierJumpRequest':

        # # Assuming only the carriers owner can set a jump, we can safely store the carrier id for later usage
        # carrier_id = entry['CarrierID']
        # config.set('fct_carrier_id', str(carrier_id))
        #
        # Store the jump params
        fct.fct_jump_destination.set(str(entry["SystemName"]))
        fct.fct_jump_destination_id.set(str(entry['SystemAddress']))
        fct.fct_time_of_departure.set(str(entry['DepartureTime']))

        fct.fct_is_jump_active.set(bool(True))

        # store in config for long term
        fct.update_config()

        # Ensure existing timers are stopped before starting a new one
        fct.chronos.stop()

        # start timer
        logger.info(str(entry['DepartureTime']))
        fct.chronos.start(str(entry['DepartureTime']))
        fct.start_tracking_time()

        # entry['Body'] is only exists when the destination body is the primary star or a pre-set planet
        if 'Body' in entry.keys():
            destination_body = entry['Body']
        else:
            destination_body = None

        # Send Discord Message
        fct.dm.jump_request_message(entry["SystemName"], entry['DepartureTime'], destination_body, entry['SystemAddress'])

    if entry['event'] == 'CarrierJumpCancelled':
        fct.fct_is_jump_active.set(bool(False))
        fct.chronos.stop()
        fct.update_config()
        fct.dm.jump_canceled()

    if entry['event'] == 'CarrierJump':
        ...
    if entry['event'] == 'CarrierStats':
        ...
