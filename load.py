"""
Example EDMC plugin.

It adds a single button to the EDMC interface that displays the number of times it has been clicked.
"""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk
import os
from tkinter import Frame
from typing import Optional

import myNotebook as nb  # noqa: N813

from discord_messages import DiscordMessages

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
        # Be sure to use names that wont collide in our config variables
        self.click_count = tk.StringVar(value=str(config.get_int('click_counter_count')))
        self.fct_discord_webhook_url = tk.StringVar(value=str(config.get_str('fct_discord_webhook_url')))
        self.fct_carriers_inara_url = tk.StringVar(value=str(config.get_str('fct_carriers_inara_url')))

        self.dm = DiscordMessages(self.fct_discord_webhook_url.get(), self.fct_carriers_inara_url.get())

        logger.info("Fleet carrier Tracker instantiated")

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

        nb.Label(frame, text='Discord Webhook URL:').grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.EntryMenu(frame, textvariable=self.fct_discord_webhook_url, show="*", width=30).grid(row=current_row, column=1, padx=PADX, pady=BOXY, sticky=tk.EW)
        current_row += 1  # Always increment our row counter, makes for far easier tkinter design.

        nb.Label(frame, text='Inara Link for your carrier').grid(row=current_row, padx=PADX, pady=PADY, sticky=tk.W)
        nb.EntryMenu(frame, textvariable=self.fct_carriers_inara_url).grid(row=current_row, column=1, padx=PADX, pady=BOXY, sticky=tk.EW)
        current_row += 1

        test_btn = ttk.Button(frame, command=self.dm.send_test_messages(), text="Send TEST message to discord" )
        test_btn.grid(row=current_row, columnspan=2, padx=PADX, pady=BOXY, sticky=tk.EW)

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
        config.set('fct_carriers_inara_url', str(self.fct_carriers_inara_url.get()))

    def setup_main_ui(self, parent: tk.Frame) -> tk.Frame:
        """
        Create our entry on the main EDMC UI.

        This is called by plugin_app below.

        :param parent: EDMC main window Tk
        :return: Our frame
        """
        current_row = 0
        frame = tk.Frame(parent)

        title = ttk.Label(frame, text="--- Fleet Carrier Tracker ---")
        title.grid(row=current_row, columnspan=2)

        current_row += 1

        # title = tk.Label(frame, text='Fleet Carrier Tracker', font=("Arial", 10, "underline"))
        # title.grid(columnspan=2, sticky=tk.E)
        # title.grid(row=current_row, columnspan=1, sticky=tk.EW, pady=10 )
        # title.columnconfigure(0, weight=1)
        #
        # current_row += 1
        #
        # carrier_id = config.get_str('fct_carrier_id')
        # tk.Label(frame, text='Carrier ID:').grid(row=current_row,  )
        # tk.Label(frame, text=carrier_id).grid(row=current_row, column=1,)
        # current_row += 1

        # if self.fct_discord_webhook_url.get() != None and self.fct_carriers_inara_url.get() != None:
        #     fct_status = "enabled"
        # else:
        #     fct_status = "need setup"
        #
        # tk.Label(frame, text="Fleet Carrier Tracker").grid(row=current_row, sticky=tk.W, pady=10)
        # tk.Label(frame, text=fct_status).grid(row=current_row, column=1, sticky=tk.W, padx=5)

        return frame


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
    return fct.setup_main_ui(parent)


def journal_entry(cmdrname: str, is_beta: bool, system: str, station: str, entry: dict, state: dict) -> None:
    if entry['event'] == 'CarrierJumpRequest':

        config.set('fct_carrier_id', str(entry['CarrierID']))
        # entry['Body'] is only exists when the destination body is the primary star or a pre-set planet
        if 'Body' in entry.keys():
            destination_body = entry['Body']
        else:
            destination_body = None

        fct.dm.jump_request_message(entry["SystemName"], entry['DepartureTime'], destination_body)

    if entry['event'] == 'CarrierJumpCancelled':
        fct.dm.jump_canceled()

    if entry['event'] == 'CarrierJump':
        ...
    if entry['event'] == 'CarrierStats':
        ...
