# coding=utf-8
from __future__ import absolute_import, print_function
from octoprint.server import user_permission

import octoprint.plugin
import flask
import os
import board
import digitalio


class GpioControlPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.RestartNeedingPlugin,
):

    def __init__(self):
        self.board = None
        self.PIN_MAPPINGS = None
        self.pinin = None
        self.pinout = None
        self.mode = None

    def on_startup(self, *args, **kwargs):
        self.mode = None

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True),
            dict(
                type="sidebar",
                custom_bindings=True,
                template="gpiocontrol_sidebar.jinja2",
                icon="map-signs",
            ),
        ]

    def get_assets(self):
        return dict(
            js=["js/gpiocontrol.js", "js/fontawesome-iconpicker.min.js"],
            css=["css/gpiocontrol.css", "css/fontawesome-iconpicker.min.css"],
        )

    def get_settings_defaults(self):
        return dict(gpio_configurations=[],
                    outpin=["C6"],
                    inpin="C7")

    def get_pin_number(self, pin):
        self.PIN_MAPPINGS = {4: "D4", 5: "D5", 6: "D6", 7: "D7", 8: "C0", 9: "C1", 10: "C2", 11: "C3", 12: "C4", 13: "C5", 14: "C6", 15: "C7"}
        if self.mode is None:
            return self.PIN_MAPPINGS[pin]

        return -1

    def on_settings_save(self, data):
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Cleaned GPIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )
            pin = self.get_pin_number(str(configuration["pin"]))

            if pin > 0:
                self.mode = None
#               GPIO.cleanup(pin)

        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Reconfigured GPIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            pin = pin = configuration["pin"]

            if pin > 0:
                self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                self.pinout.direction = digitalio.Direction.OUTPUT
#               GPIO.setup(pin, GPIO.OUT)

                if configuration["active_mode"] == "active_low":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                elif configuration["active_mode"] == "active_high":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)

    def on_after_startup(self):
        self.pinin = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
        self.pinin.direction = digitalio.Direction.INPUT
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Configured GPIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            pin = self.get_pin_number(int(configuration["pin"]))

            if pin != -1:
                self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                self.pinout.direction = digitalio.Direction.OUTPUT
#               GPIO.setup(pin, GPIO.OUT)

                if configuration["active_mode"] == "active_low":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                elif configuration["active_mode"] == "active_high":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)

    def get_api_commands(self):
        return dict(turnGpioOn=["id"], turnGpioOff=["id"], getGpioState=["id"])

    def on_api_command(self, command, data):

        if not user_permission.can():
            return flask.make_response("Insufficient rights", 403)

        configuration = self._settings.get(["gpio_configurations"])[int(data["id"])]
        pin = self.get_pin_number(int(configuration["pin"]))

        if command == "getGpioState":
            if pin < 0:
                return flask.jsonify("")
            elif configuration["active_mode"] == "active_low":
                return flask.jsonify("off" if self.pinin.value is False else "on")
            elif configuration["active_mode"] == "active_high":
                return flask.jsonify("on" if self.pinin.value is False else "off")
        elif command == "turnGpioOn":
            if pin > 0:
                self._logger.info("Turned on GPIO{}".format(configuration["pin"]))

                if configuration["active_mode"] == "active_low":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = False
#                   GPIO.output(pin, GPIO.LOW)
                elif configuration["active_mode"] == "active_high":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = True
#                   GPIO.output(pin, GPIO.HIGH)
        elif command == "turnGpioOff":
            if pin > 0:
                self._logger.info("Turned off GPIO{}".format(configuration["pin"]))

                if configuration["active_mode"] == "active_low":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = True
#                   GPIO.output(pin, GPIO.HIGH)
                elif configuration["active_mode"] == "active_high":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self.get_pin_number(["pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = False
#                   GPIO.output(pin, GPIO.LOW)

    def on_api_get(self, request):
        states = []

        for configuration in self._settings.get(["gpio_configurations"]):
            pin = self.get_pin_number(int(configuration["pin"]))

            if pin < 0:
                states.append("")
            elif configuration["active_mode"] == "active_low":
                states.append("off" if self.pinin.value is False else "on")
            elif configuration["active_mode"] == "active_high":
                states.append("on" if self.pinin.value is False else "off")

        return flask.jsonify(states)

    def get_update_information(self):
        return dict(
            gpiocontrol=dict(
                displayName="GPIO Control",
                displayVersion=self._plugin_version,
                type="github_release",
                user="catgiggle",
                repo="OctoPrint-GpioControl",
                current=self._plugin_version,
                stable_branch=dict(
                    name="Stable",
                    branch="master",
                    comittish=["master"],
                ),
                prerelease_branches=[
                    dict(
                        name="Prerelease",
                        branch="development",
                        comittish=["development", "master"],
                    )
                ],
                pip="https://github.com/catgiggle/OctoPrint-GpioControl/archive/{target_version}.zip",
            )
        )


__plugin_name__ = "GPIO Control"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = GpioControlPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
