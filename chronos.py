
from threading import Thread
from time import sleep
from datetime import datetime, timezone, timedelta


import tkinter as tk


class Chronos:
    def __init__(self):

        # Convert timestamp once instead of repeatedly parsing it
        self.departure_timestamp = "2025-01-01T12:00:10Z"
        self.departure_time = datetime.strptime(self.departure_timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        self.countdown_departure = True
        self.countdown_lockdown = True

        # Start both threads once
        self.departure_thread = Thread(target=self.time_till_departure, daemon=True)
        self.lockdown_thread = Thread(target=self.time_till_lockdown, daemon=True)

        # Debug Mode
        self.debug_mode = False

        # Data storage
        self.formated_remaining_time_for_departure = str("00:00:00")
        self.seconds_remaining_for_departure = int(0)
        self.formated_remaining_time_for_lockdown = str("00:00:00")
        self.seconds_remaining_for_lockdown = int(0)


    @staticmethod
    def time_diff(timestamp):
        now = datetime.now(timezone.utc)
        remaining_time = timestamp - now
        return remaining_time

    @staticmethod
    def convert_to_readable_time(total_seconds: int):
        if total_seconds < 0:
            return "00:00:00"
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def reset_data_storage(self):
        # Data storage
        self.formated_remaining_time_for_departure = str("00:00:00")
        self.seconds_remaining_for_departure = int(0)
        self.formated_remaining_time_for_lockdown = str("00:00:00")
        self.seconds_remaining_for_lockdown = int(0)

    def time_till_departure(self):
        while self.countdown_departure:
            time_diff_for_departure = self.time_diff(self.departure_time)
            diff_in_seconds = time_diff_for_departure.total_seconds()
            if diff_in_seconds <= 0:
                if self.debug_mode:
                    print('Departure time reached!\n')
                self.countdown_departure = False
                break

            readable_time = self.convert_to_readable_time(int(diff_in_seconds))
            self.formated_remaining_time_for_departure = str(readable_time)
            self.seconds_remaining_for_departure = int(diff_in_seconds)
            if self.debug_mode:
                print(f"Jump in: {readable_time}")
            sleep(1)

    def time_till_lockdown(self):
        lockdown_time = self.departure_time - timedelta(minutes=3, seconds=20)
        while self.countdown_lockdown:
            time_diff_for_lockdown = self.time_diff(lockdown_time)
            diff_in_seconds = time_diff_for_lockdown.total_seconds()
            if diff_in_seconds <= 0:
                if self.debug_mode:
                    print('Lockdown time reached!\n')
                self.countdown_lockdown = False
                break

            readable_time = self.convert_to_readable_time(int(diff_in_seconds))
            self.formated_remaining_time_for_lockdown = str(readable_time)
            self.seconds_remaining_for_lockdown = int(diff_in_seconds)
            if self.debug_mode:
                print(f"Lockdown in: {readable_time}")
            sleep(1)

    def start(self, timestamp):
        self.departure_timestamp = timestamp
        self.departure_thread.start()
        self.lockdown_thread.start()

    def stop(self):
        """Stops both countdowns and waits for threads to finish."""
        self.countdown_departure = False
        self.countdown_lockdown = False
        if self.departure_thread.is_alive():
            self.departure_thread.join()
            if self.debug_mode:
                print("departure_thread killed")
        if self.lockdown_thread.is_alive():
            self.lockdown_thread.join()
            if self.debug_mode:
                print("lockdown_thread killed")

        self.reset_data_storage()


        if self.debug_mode:
            print("Countdown stopped.")


if __name__ == "__main__":
    chronos = Chronos()
    chronos.debug_mode = False
    chronos.start()

    try:
        while chronos.countdown_departure or chronos.countdown_lockdown:
            sleep(1)  # Keep the main thread alive
            print(f'value: {chronos.formated_remaining_time_for_departure}')
            print(f'value: {chronos.formated_remaining_time_for_lockdown}')
    except KeyboardInterrupt:
        if chronos.debug_mode:
            print("\nStopping countdown...")
        chronos.stop()
