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
    pinin = False
    pinout = False

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
                    light_pin="C6",
                    light_pin2="C7")

    def on_settings_save(self, data):
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Cleaned GPIO{}: {},{} ({})".format(
                    configuration["bpin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            bpin = self.get_pin_number(int(configuration["bpin"]))

            if bpin > 0:
                self.pinout.deinit()
#               GPIO.cleanup(pin)

        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Reconfigured GPIO{}: {},{} ({})".format(
                    configuration["bpin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            bpin = self.get_pin_number(int(configuration["bpin"]))

            if bpin > 0:
                self.pinout = digitalio.DigitalInOut(getattr(board, self.get_settings_get(["bpin"])))
                self.pinout.direction = digitalio.Direction.OUTPUT
#               GPIO.setup(pin, GPIO.OUT)

                if configuration["active_mode"] == "active_low":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                elif configuration["active_mode"] == "active_high":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)

    def on_after_startup(self):
        self.pinin = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
        self.pinin.direction = digitalio.Direction.INPUT
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Configured GPIO{}: {},{} ({})".format(
                    configuration["bpin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            bpin = self.get_pin_number(int(configuration["bpin"]))

            if bpin != -1:
                self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                self.pinout.direction = digitalio.Direction.OUTPUT
#               GPIO.setup(pin, GPIO.OUT)

                if configuration["active_mode"] == "active_low":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                elif configuration["active_mode"] == "active_high":
                    if configuration["default_state"] == "default_on":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = True
#                       GPIO.output(pin, GPIO.HIGH)
                    elif configuration["default_state"] == "default_off":
                        self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                        self.pinout.direction = digitalio.Direction.OUTPUT
                        self.pinout.value = False
#                       GPIO.output(pin, GPIO.LOW)

    def get_api_commands(self):
        return dict(turnGpioOn=["id"], turnGpioOff=["id"], getGpioState=["id"])

    def on_api_command(self, command, data):

        if not user_permission.can():
            return flask.make_response("Insufficient rights", 403)

        configuration = self._settings.get(["gpio_configurations"])[int(data["id"])]
        bpin = self.get_pin_number(int(configuration["bpin"]))

        if command == "getGpioState":
            if bpin < 0:
                return flask.jsonify("")
            elif configuration["active_mode"] == "active_low":
                return flask.jsonify("off" if self.pinin.value is False else "on")
            elif configuration["active_mode"] == "active_high":
                return flask.jsonify("on" if self.pinin.value is False else "off")
        elif command == "turnGpioOn":
            if bpin > 0:
                self._logger.info("Turned on GPIO{}".format(configuration["bpin"]))

                if configuration["active_mode"] == "active_low":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = False
#                   GPIO.output(pin, GPIO.LOW)
                elif configuration["active_mode"] == "active_high":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = True
#                   GPIO.output(pin, GPIO.HIGH)
        elif command == "turnGpioOff":
            if bpin > 0:
                self._logger.info("Turned off GPIO{}".format(configuration["bpin"]))

                if configuration["active_mode"] == "active_low":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = True
#                   GPIO.output(pin, GPIO.HIGH)
                elif configuration["active_mode"] == "active_high":
                    self.pinout = digitalio.DigitalInOut(getattr(board, self._settings.get(["light_pin"])))
                    self.pinout.direction = digitalio.Direction.OUTPUT
                    self.pinout.value = False
#                   GPIO.output(pin, GPIO.LOW)

    def on_api_get(self, request):
        states = []

        for configuration in self._settings.get(["gpio_configurations"]):
            bpin = self.get_pin_number(int(configuration["bpin"]))

            if bpin < 0:
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

    mode = None
    PIN_MAPPINGS = ["ZZ" "D4", "D5", "D6", "D7", "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7"]

    def get_pin_number(self, bpin):
        if self.mode is None:
            return self.PIN_MAPPINGS[bpin]

        return -1


__plugin_name__ = "GPIO Control"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = GpioControlPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
