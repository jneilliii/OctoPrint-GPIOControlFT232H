# coding=utf-8
from __future__ import absolute_import, print_function
from octoprint.server import user_permission

import octoprint.plugin
import flask
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
        pass

    def on_startup(self, *args, **kwargs):
        pass

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
        return {"gpio_configurations": []}

    def on_settings_save(self, data):
        for configuration in self._settings.get(["gpio_configurations"]):
            pin = configuration["pin"]

            if pin != "":
                processing_pin = digitalio.DigitalInOut(getattr(board, pin))
                processing_pin.direction = digitalio.Direction.OUTPUT
                processing_pin.deinit()
                self._logger.info(
                    "Cleaned GPIO{}: {},{} ({})".format(
                        configuration["pin"],
                        configuration["active_mode"],
                        configuration["default_state"],
                        configuration["name"],
                    )
                )

        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        for configuration in self._settings.get(["gpio_configurations"]):
            pin = configuration["pin"]

            if pin != "":
                self._logger.info(
                    "Reconfigured GPIO{}: {},{} ({})".format(
                        configuration["pin"],
                        configuration["active_mode"],
                        configuration["default_state"],
                        configuration["name"],
                    )
                )
                processing_pin = digitalio.DigitalInOut(getattr(board, pin))
                processing_pin.direction = digitalio.Direction.OUTPUT

                if configuration["active_mode"] == "active_low":
                    if configuration["default_state"] == "default_on":
                        processing_pin.value = False
                    elif configuration["default_state"] == "default_off":
                        processing_pin.value = True
                elif configuration["active_mode"] == "active_high":
                    if configuration["default_state"] == "default_on":
                        processing_pin.value = True
                    elif configuration["default_state"] == "default_off":
                        processing_pin.value = False

    def on_after_startup(self):
        for configuration in self._settings.get(["gpio_configurations"]):
            self._logger.info(
                "Configured GPIO{}: {},{} ({})".format(
                    configuration["pin"],
                    configuration["active_mode"],
                    configuration["default_state"],
                    configuration["name"],
                )
            )

            pin = configuration["pin"]

            if pin != "":
                processing_pin = digitalio.DigitalInOut(getattr(board, pin))
                processing_pin.direction = digitalio.Direction.OUTPUT
                if configuration["active_mode"] == "active_low":
                    if configuration["default_state"] == "default_on":
                        processing_pin.value = False
                    elif configuration["default_state"] == "default_off":
                        processing_pin.value = True
                elif configuration["active_mode"] == "active_high":
                    if configuration["default_state"] == "default_on":
                        processing_pin.value = True
                    elif configuration["default_state"] == "default_off":
                        processing_pin.value = False

    def get_api_commands(self):
        return dict(turnGpioOn=["id"], turnGpioOff=["id"], getGpioState=["id"])

    def on_api_command(self, command, data):
        if not user_permission.can():
            return flask.make_response("Insufficient rights", 403)

        configuration = self._settings.get(["gpio_configurations"])[int(data["id"])]
        processing_pin = None
        pin = configuration["pin"]

        if pin != "":
            processing_pin = digitalio.DigitalInOut(getattr(board, pin))
            processing_pin.direction = digitalio.Direction.OUTPUT

        if command == "getGpioState" and processing_pin:
            if configuration["active_mode"] == "active_low":
                return flask.jsonify("off" if processing_pin.value is False else "on")
            elif configuration["active_mode"] == "active_high":
                return flask.jsonify("on" if processing_pin.value is False else "off")
        elif command == "turnGpioOn" and processing_pin:
            self._logger.info("Turned on GPIO{}".format(configuration["pin"]))

            if configuration["active_mode"] == "active_low":
                processing_pin.value = False
            elif configuration["active_mode"] == "active_high":
                processing_pin.value = True
        elif command == "turnGpioOff" and processing_pin:
            self._logger.info("Turned off GPIO{}".format(configuration["pin"]))

            if configuration["active_mode"] == "active_low":
                processing_pin.value = True
            elif configuration["active_mode"] == "active_high":
                processing_pin.value = False

    def on_api_get(self, request):
        states = []

        for configuration in self._settings.get(["gpio_configurations"]):
            pin = configuration["pin"]

            if pin == "":
                states.append("")
            else:
                processing_pin = digitalio.DigitalInOut(getattr(board, pin))
                processing_pin.direction = digitalio.Direction.OUTPUT
                if configuration["active_mode"] == "active_low":
                    states.append("off" if processing_pin.value is False else "on")
                elif configuration["active_mode"] == "active_high":
                    states.append("on" if processing_pin.value is False else "off")

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
