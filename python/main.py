from collections import OrderedDict, deque
from threading import Lock, Thread
from time import sleep
from uuid import uuid4

from arduino.app_bricks.web_ui import WebUI
from arduino.app_utils import App, Bridge
from fastapi import HTTPException
from pydantic import BaseModel

from pixels import BLANK, ICONS, render

ui = WebUI()
lock = Lock()
waiting = deque()
messages = OrderedDict()
online = False


class Submission(BaseModel):
    kind: str
    value: str


def preview(body: Submission):
    try:
        label, frames, interval = render(body.kind, body.value)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error
    return {"label": label, "frames": frames, "interval": interval}


def submit(body: Submission):
    animation = preview(body)
    with lock:
        if not online:
            raise HTTPException(503, "The matrix is reconnecting.")
        if len(waiting) >= 8:
            raise HTTPException(429, "The queue is full. Try again in a moment.")
        message_id = uuid4().hex
        messages[message_id] = {"id": message_id, "label": animation["label"], "state": "Queued"}
        waiting.append((message_id, animation))
        if len(messages) > 64:
            messages.popitem(last=False)
    return {"id": message_id}


def status():
    with lock:
        positions = {key: index for index, (key, _) in enumerate(waiting, 1)}
        return {
            "online": online,
            "waiting": len(waiting),
            "messages": [dict(item, position=positions.get(key)) for key, item in messages.items()],
        }


def draw(frame):
    if Bridge.call("bloop_frame", frame) is not True:
        raise RuntimeError("Matrix did not acknowledge the frame")


def playback():
    global online
    while True:
        job = None
        with lock:
            if online and waiting:
                job = waiting.popleft()
                messages[job[0]]["state"] = "Starting"
        if job is None:
            if not online:
                try:
                    draw(BLANK)
                    with lock:
                        online = True
                except Exception as error:
                    print(f"Bloop waiting for matrix: {error}", flush=True)
                    sleep(2)
            else:
                sleep(0.1)
            continue

        message_id, animation = job
        try:
            for index, frame in enumerate(animation["frames"]):
                draw(frame)
                if index == 0:
                    with lock:
                        messages[message_id]["state"] = "Displaying"
                sleep(animation["interval"] / 1000)
            draw(BLANK)
            with lock:
                messages[message_id]["state"] = "Done"
        except Exception as error:
            print(f"Bloop playback failed: {error}", flush=True)
            with lock:
                online = False
                messages[message_id]["state"] = "Interrupted"


ui.expose_api("GET", "/api/icons", lambda: {key: icon[0] for key, icon in ICONS.items()})
ui.expose_api("GET", "/api/status", status)
ui.expose_api("POST", "/api/preview", preview)
ui.expose_api("POST", "/api/messages", submit)

if __name__ == "__main__":
    Thread(target=playback, daemon=True).start()
    App.run()
