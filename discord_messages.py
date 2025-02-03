import logging
import os
import json
from time import sleep

import requests
from datetime import datetime, timedelta, timezone
from config import appname, config

# This **MUST** match the name of the folder the plugin is in.
plugin_name = os.path.basename(os.path.dirname(__file__))

logger = logging.getLogger(f"{appname}.{plugin_name}")


class DiscordMessages:

    def __init__(self, discord_webhook_url=None, carrier_inara_url=None) -> None:
        self.discord_webhook_url = discord_webhook_url
        self.carrier_inara_url = carrier_inara_url

        self.inara_search_url = "https://inara.cz/elite/starsystem/?search="
        logger.info("DiscordMessages instantiated")

    def jump_request_message(self, destination_system_name: str, departure_iso_time: str, destination_body: str, system_address: str) -> None:

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
                "value": f'```{destination_system_name}```',
                "inline": True
            })
        else:
            logger.error("Missing Destination system")

        if destination_body is not None:
            data["embeds"][0]["fields"].append({
                "name": "Destination body:",
                "value": f'```{destination_body}```',
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

        if system_address is not None:
            destination_link = str(f'{self.inara_search_url}{system_address}')

            data["embeds"][0]["description"] = f'[Detailed info about the system on inara.cz]({destination_link})'

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
            date_object_from_departure_time = datetime.strptime(departure_iso_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            # convert to epoch time
            departure_time = int(date_object_from_departure_time.timestamp())

        except ValueError as exc:
            raise ValueError('Bad datetime:', departure_iso_time) from exc

        return f"<t:{departure_time}:R>"



    def send_test_messages(self):
        logger.info(f'Sending TEST message to discord')

        #"SystemName":"Santy", "Body":"Santy A", "SystemAddress":7230678110938,
        destination_system_name = "Santy"
        destination_body = "Santy A"
        system_address = "7230678110938"

        time_now = datetime.now(timezone.utc)
        time_for_fake_departure = time_now + timedelta(minutes=16)

        departure_iso_time = f'{time_for_fake_departure:%Y-%m-%dT%H:%M:%SZ}'

        self.jump_request_message(destination_system_name, departure_iso_time, destination_body, system_address)
        sleep(1)
        self.jump_canceled()

    def send(self, payload: dict) -> None:
        # Webhook
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

        r = requests.post(self.discord_webhook_url, data=json.dumps(payload), headers=headers, timeout=(1, 1))

        logger.info('\n---------------------- SENDING message to DISCORD ----------------------')
        if r.status_code == 204:
            logger.info('Discord message sent successfully')
        else:
            logger.error('Discord message failed')
        logger.info('---------------------- End of communication with discord ----------------------')

        r.close()
