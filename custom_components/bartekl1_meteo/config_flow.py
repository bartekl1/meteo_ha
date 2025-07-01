from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class MeteoStationConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input["url"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("url"): str,
                vol.Required("name"): str,
                vol.Optional("verify_ssl", default=True): bool,
                vol.Optional("update_interval", default=60): int
            })
        )
