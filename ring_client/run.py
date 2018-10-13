import typing as t
import sys
import os

import audio_tools
import config
import ring_client
from effects import CircularFourierEffect
from profiler import Profiler

if config.MOCK_RING:
    from PyQt5.QtWidgets import QApplication
    import qt5_client


def qtmock_client_and_wait():
    application = QApplication(sys.argv)
    client = qt5_client.Qt5RingClient(60, 4)
    return client, application.exec_


def client_and_wait():
    config_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "tcp_to_led", "config.h"
    )
    client = ring_client.RingClient.from_config_header(config_file)

    def wait() -> int:
        input()
        return 0

    return client, wait


def main() -> None:
    if config.MOCK_RING:
        client, wait = qtmock_client_and_wait()
    else:
        client, wait = client_and_wait()

    if config.MOCK_AUDIO:
        audio_input = qt5_client.MockSinInput()
    else:
        audio_input = audio_tools.AudioInput()

    render_func = CircularFourierEffect(audio_input, client)

    loop = ring_client.RenderLoop(client, render_func)
    loop.start()

    return_code = wait()

    loop.stop()
    sys.exit(return_code)


if __name__ == "__main__":
    main()