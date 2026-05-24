import requests
import xbmc
import xbmcaddon
import json
import os
from utils.logging import notify_error, notify_info
import urllib.parse
addon = xbmcaddon.Addon()
monitor = xbmc.Monitor()


#TODO improve logic
def main_loop():
    wait_time = 10
    while not monitor.abortRequested():
      hostname = addon.getSetting('ntfy_url')
      topic = addon.getSetting('ntfy_topic')
      enable_notifications = addon.getSettingBool('ntfy_enable')
      if not enable_notifications:
         if monitor.waitForAbort(wait_time):
            break
         continue
      if not topic:
         notify_error("No ntfiy.sh topic was provided")
         if monitor.waitForAbort(wait_time):
            break
         continue
      try:
        resp = requests.get(f"{hostname}/{urllib.parse.quote(topic)}/json", stream=True)
        resp.raise_for_status()
        for line in resp.iter_lines():
            enable_notifications = addon.getSettingBool('ntfy_enable')
            if not enable_notifications:
               break
            if monitor.waitForAbort(1):
               return
            notif = json.loads(line)
            os.linesep.join([s for s in text.splitlines() if s.strip()])
            if notif.get("event") == "message":
                text = notif.get("message")
                message= os.linesep.join([s for s in text.splitlines() if s.strip()])
                notify_info(message)
      except Exception as e:
         pass
         #notify_error("An error occured while connecting to the ntfy instance. Trying again in 1 minute.")
      if monitor.waitForAbort(wait_time):
         break
      
if __name__ == '__main__':
    main_loop()
