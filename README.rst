Introduction
============

.. image:: https://readthedocs.org/projects/adafruit-circuitpython-ble_apple_media/badge/?version=latest
    :target: https://docs.circuitpython.org/projects/ble_apple_media/en/latest/
    :alt: Documentation Status

.. image:: https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_Bundle/main/badges/adafruit_discord.svg
    :target: https://adafru.it/discord
    :alt: Discord

.. image:: https://github.com/adafruit/Adafruit_CircuitPython_BLE_Apple_Media/workflows/Build%20CI/badge.svg
    :target: https://github.com/adafruit/Adafruit_CircuitPython_BLE_Apple_Media/actions
    :alt: Build Status

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Code Style: Ruff

Support for the Apple Media Service which provides media playback info and control.


Dependencies
=============
This driver depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_

Please ensure all dependencies are available on the CircuitPython filesystem.
This is easily achieved by downloading
`the Adafruit library and driver bundle <https://circuitpython.org/libraries>`_.

Installing from PyPI
=====================

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-ble_apple_media/>`_. To install for current user:

.. code-block:: shell

    pip3 install adafruit-circuitpython-ble-apple-media

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install adafruit-circuitpython-ble-apple-media

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install adafruit-circuitpython-ble-apple-media

Usage Example
=============

.. code-block:: python

    import adafruit_ble
    from adafruit_ble.advertising.standard import SolicitServicesAdvertisement
    from adafruit_ble_apple_media import AppleMediaService

    radio = adafruit_ble.BLERadio()
    a = SolicitServicesAdvertisement()
    a.solicited_services.append(AppleMediaService)
    radio.start_advertising(a)

    while not radio.connected:
        pass

    print("connected")

    known_notifications = set()

    i = 0
    while radio.connected:
        for connection in radio.connections:
            if not connection.paired:
                connection.pair()
                print("paired")

            ams = connection[AppleMediaService]
            print("App:", ams.player_name)
            print("Title:", ams.title)
            print("Album:", ams.album)
            print("Artist:", ams.artist)
            if ams.playing:
                print("Playing")
            elif ams.paused:
                print("Paused")

            if i > 3:
                ams.toggle_play_pause()
                i = 0
        print()
        time.sleep(3)
        i += 1

    print("disconnected")


Documentation
=============

API documentation for this library can be found on `Read the Docs <https://docs.circuitpython.org/projects/ble_apple_media/en/latest/>`_.

For information on building library documentation, please check out `this guide <https://learn.adafruit.com/creating-and-sharing-a-circuitpython-library/sharing-our-docs-on-readthedocs#sphinx-5-1>`_.

Contributing
============

Contributions are welcome! Please read our `Code of Conduct
<https://github.com/adafruit/Adafruit_CircuitPython_BLE_Apple_Media/blob/main/CODE_OF_CONDUCT.md>`_
before contributing to help this project stay welcoming.
