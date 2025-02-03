import logging
import os
import json
from time import sleep

import requests
from datetime import datetime
from config import appname, config

# This **MUST** match the name of the folder the plugin is in.
plugin_name = os.path.basename(os.path.dirname(__file__))

logger = logging.getLogger(f"{appname}.{plugin_name}")


class DiscordMessages:

    def __init__(self, discord_webhook_url=None, carrier_inara_url=None) -> None:
        self.discord_webhook_url = discord_webhook_url
        self.carrier_inara_url = carrier_inara_url

    def jump_request_message(self, destination_system_name: str, departure_iso_time: str, destination_body: str) -> None:

        data = {
            "content": "Fleet Carrier Tracker plugin (FCT) detected a carrier jump request:",
            "embeds": [
                {
                    "title": f"Carrier jump scheduled to {destination_system_name}",
                    "color": 2335683,
                    "fields": []
                }
            ]
        }

        # Add fields to the data based on the optional arguments
        if destination_system_name is not None:
            data["embeds"][0]["fields"].append({
                "name": "Destination system:",
                "value": destination_system_name,
                "inline": True
            })
        else:
            logger.error("Missing Destination system")

        if destination_body is not None:
            data["embeds"][0]["fields"].append({
                "name": "Destination body:",
                "value": destination_body,
                "inline": True
            })

        if departure_iso_time is not None:

            departure_time = self.convert_iso_time_to_readable_string(departure_iso_time)

            data["embeds"][0]["fields"].append({
                "name": "Time of departure from the current system:",
                "value": departure_time
            })
        else:
            logger.error('Missing Departure Time')

        data = self.add_carrier_url(data)

        self.send(data)

    def jump_canceled(self) -> None:
        data = {
            "embeds": [
                {
                    "title": "Jump request canceled",
                    "description": "Apologies, the scheduled jump is canceled.\nPlease ignore our previous notification about the jump, we are staying in the same system.",
                    "color": 13507612,
                    "fields": []
                }
            ]
        }

        data = self.add_carrier_url(data)
        self.send(data)

    def add_carrier_url(self, data: dict) -> dict:

        # Deal with default None or empty line.
        if self.carrier_inara_url is not None and not self.carrier_inara_url.strip() == '':
            data["embeds"][0]["fields"].append({
                "name": "Inara.cz Link for the carrier:",
                "value": self.carrier_inara_url
            })
        return data

    @staticmethod
    def convert_iso_time_to_readable_string(departure_iso_time: str) -> str:
        try:
            # convert to datetime object from string
            date_object_from_departure_time = datetime.strptime(departure_iso_time, "%Y-%m-%dT%H:%M:%SZ")
            # convert to formated string
            departure_time = date_object_from_departure_time.strftime("%Y-%m-%d, %H:%M")

        except ValueError as exc:
            raise ValueError('Bad datetime:', departure_iso_time) from exc

        return departure_time

    def send_test_messages(self):
        destination_system_name = "TEST - SYSTEM NAME"
        departure_iso_time = "2025-01-01T12:00:00Z"
        destination_body = "TEST - BODY"

        self.jump_request_message(destination_system_name, departure_iso_time, destination_body)
        sleep(1)
        self.jump_canceled()

    def send(self, payload: dict) -> None:
        # Webhook
        logger.info('---------------------- SENDING message to DISCORD ----------------------\n')
        # logger.debug(f'sending data to: {self.discord_webhook_url}\n\n' )
        # logger.debug(f'payload: {payload}' )
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        r = requests.post(self.discord_webhook_url, data=json.dumps(payload), headers=headers, timeout=(1, 1))

        if r.status_code == 204:
            logger.info('Discord message sent successfully')
        else:
            logger.error('Discord message failed')

        r.close()
        logger.info('---------------------- End of communication with discord ----------------------\n')
