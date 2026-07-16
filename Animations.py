import itertools
import time


def loading_animation(text="Starting",stop_animation=None):
    for dots in itertools.cycle(["", ".", "..", "..."]):
        if not stop_animation or stop_animation.is_set():
            break
        print(f"\r{text}{dots}   ", end="", flush=True)
        time.sleep(0.4)

    # Clear the line when finished
    print("\r" + " " * 30 + "\r", end="", flush=True)

