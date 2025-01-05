from homeassistant import config_entries
import voluptuous as vol

class SpyderConfigFlow(config_entries.ConfigFlow, domain="spyder_thermostat"):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Validate the user input here
            return self.async_create_entry(
                title="Spyder Thermostat",
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
            }),
            errors=errors
        )
