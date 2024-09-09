#!/usr/bin/python3
# porssari.py - a porssari.fi API client to support fetching and control calls
# Note: This version supports single channel.

from datetime import datetime
import json
import requests
import threading
import time
import traceback

class Porssari:
    def __init__(self,
                 server="https://api.porssari.fi/getcontrols.php?",
                 device_mac=None,
                 client=None,
                 relay_cb=None, # usage relay_cb(relay_id, state)
                 update_interval = 5*60,
                 spot="https://api.spot-hinta.fi/TodayAndDayForward"):
        self.server = server
        self.spot = spot
        self.device_mac = device_mac
        self.client = client
        self.relay_cb = relay_cb
        self.update_interval = update_interval
        self.relay_timer = None
        self.relay_update_time = None
        self.fetcher_timer = None
        self.first = True
        self.response = {} # last response from server
        self.relays = {} # mirror the state of relays
        self.controls = {} # Last control part response from server for the first element
        self.controls_updated = 0
        self.spot_result = []

    def start(self):
        self.update_task()
        self.fetcher_timer = threading.Timer(self.update_interval, self.update_task)
        self.fetcher_timer.start()

    def call_relay(self, id, state):
        print("RELAY ", id, "TO", state)
        old = self.relays.get(id)
        self.relays[id] = state
        if self.relay_cb:
            self.relay_cb(id, state)

    def get_state(self, id):
        return self.relays.get(id)

    def get_time_to_relay_update(self):
        if self.relay_update_time:
            now = int(time.time())
            delta = self.relay_update_time - now
            minutes = int(delta/60)%60
            hours = int(delta/3600)
            if hours > 0:
                return f"{hours}h{minutes}m"
            return f"{minutes}m"
        return ""

    def get_spot_price(self):
        '''
        This method returns the spot prices in an array of dict for
        current and next day.
        '''
        return self.spot_result;

    def get_on_off_hours(self, accuracy=900):
        '''
        This method returns array of on/off state per hour in 15 minute segments starting
        from the latest start time of the control response.
        This method can be used to simplify GUI creation to display next 24h
        states.
        '''
        if not self.response:
            return {}
        metadata = self.response.get('metadata', {})
        schedules = self.controls['schedules']
        now = time.time()
        start_time = int(metadata.get('timestamp'))
        start_state = self.controls.get('state', "0")
        end_time = int(metadata.get('valid_until'))
        t = int(start_time / 3600)*3600
        hours = {}
        while t < end_time:
            state = start_state
            for schedule in schedules:
                schedule_timestamp = int(schedule['timestamp'])
                # As porssari may have the sceduled timestamp as +- 1 minute
                # round the value to next 3 minute
                if int((schedule_timestamp+180)/accuracy)*accuracy > t:
                    break
                state = schedule['state']
            hours[t] = state
            t += accuracy
        return hours

    def relay_update_task(self, id, schedule):
        try:
            self.call_relay(id, schedule['state'])
            # check the next schedule and assign a timer for it
            schedules = self.controls.get('schedules', [])
            now = int(time.time())
            # check which schedule to use next
            for schedule in schedules:
                if int(schedule['timestamp']) > now + 30:
                    relay_update_time = int(schedule['timestamp'])
                    delta = relay_update_time - now
                    print("Scheduled relay update to happen in delta: ", delta, " for state:", schedule['state'])
                    self.relay_timer = threading.Timer(delta, self.relay_update_task, args=[id, schedule])
                    self.relay_timer.start()
                    self.relay_update_time = relay_update_time
                    return
            print("Note: Did not find next schedule, forcing main update loop to set it up when available")
            self.first = True
        except Exception as e:
            print("Error in relay update:", e)
            
    def update_task(self):
        try:
            print("GET " + self.spot)
            spot_result = requests.get(self.spot)
            if spot_result.status_code == 200:
                self.spot_result = spot_result.json()
            else:
                print("Spot API failed with: ", spot_result.status_code)
        except Exception as e:
            print("Spot API failed with:", e)
        try:
            url = self.server + "device_mac=" + self.device_mac \
                + "&" + "last_request=0" + "&" \
                + "client=" + self.client + "&" \
                + "json_version=2"
            print("GET " + url)
            response = requests.get(url)
            if response.status_code != 200 and response.status_code != 304:
                print("Failed to call control server, response: ", response)
            else:
                if response.status_code == 304:
                    print("Server response 304, using cached result")
                    with open("porssari.json") as f:
                        response = json.load(f)
                else:
                    response = response.json()
                    with open("porssari.json", "w") as f:
                        json.dump(response, f)
                #print("#DEBUG: response", response)
                self.response = response
                controls = response.get('controls')[0]
                if not controls:
                    print("Error: Failed to get controls from control server")
                else:
                    # Parse the controls and prepare for next update
                    self.controls = controls
                    controls_updated = int(controls.get('updated'))
                    if controls_updated > 0:
                        # If configuration was updated reset the timer
                        if self.controls_updated != controls_updated:
                            self.controls_updated = controls_updated
                            if self.relay_timer:
                                self.relay_timer.cancel()
                                self.relay_update_time = None
                            self.first = True
                    if self.first:
                        # If this is called first time or we have schedules,
                        # then schedule next relay update
                        self.call_relay(controls['id'], controls['state'])
                        schedules = controls['schedules']
                        if len(schedules) > 0: # Note that schedules may empty if next day data is not yet available
                            schedule = controls['schedules'][0]
                            now = int(time.time())
                            self.relay_update_time = int(schedule['timestamp'])
                            delta = self.relay_update_time - now
                            print("Scheduled relay update to happen in delta: ", delta, " for state:", schedule['state'])
                            self.relay_timer = threading.Timer(delta, self.relay_update_task, args=[controls['id'], schedule])
                            self.relay_timer.start()
                            self.first = False                            
                    else:
                        # Check that we have changed the relay to correct state and if not then cancel the thread and force the relay
                        # to correct state
                        state = controls['state']
                        old_state = self.relays.get(controls['id'])
                        if old_state != state:
                            print("Warning: relay state was not updated or new relay was added, forcing update")
                            if self.relay_timer:
                                self.relay_timer.cancel()
                                self.relay_update_time = None
                            self.call_relay(controls['id'], state)
                

        except Exception as e:
            print("Error in update: ", e)
            print(traceback.format_exc())
        if self.fetcher_timer != None:
            self.fetcher_timer = threading.Timer(self.update_interval, self.update_task)
            self.fetcher_timer.start()

def test():
    relays = {}
    def test_cb(relay_id, state):
        print(int(time.time()), "set relay", relay_id, state)
        relays[relay_id] = state

    p = Porssari()
    p.response = {"metadata":{"mac":"ABCDEDFGHIJKLMNOPQRSTUFV","channels":"1","fetch_url":"https://api.porssari.fi/getcontrols.php","timestamp":"1717947639","timestamp_offset":"10800","valid_until":"1718052900"},"controls":[{"id":"1","name":"","updated":"0","state":"1","schedules":[{"timestamp":"1717959631","state":"0"},{"timestamp":"1717966803","state":"1"},{"timestamp":"1717995541","state":"0"},{"timestamp":"1718006442","state":"1"},{"timestamp":"1718010026","state":"0"},{"timestamp":"1718013528","state":"1"}]}]}
    p.controls = {"id":"1","name":"","updated":"0","state":"1"}
    p.schedules = [{"timestamp":"1717959631","state":"0"},{"timestamp":"1717966803","state":"1"},{"timestamp":"1717995541","state":"0"},{"timestamp":"1718006442","state":"1"},{"timestamp":"1718010026","state":"0"},{"timestamp":"1718013528","state":"1"}]
    h = p.get_on_off_hours()
    print(h)
            
def testrun():
    relays = {}
    def test_cb(relay_id, state):
        print(int(time.time()), "set relay", relay_id, state)
        relays[relay_id] = state
        
    p = Porssari(server="http://localhost:8000/getcontrols.php?",
                 device_mac="ABCDEFGHIJKLMN",
                 client="device",
                 relay_cb=test_cb,
                 update_interval=120)
    p.start()
    time.sleep(86400)
    
if __name__ == "__main__":
    test()
