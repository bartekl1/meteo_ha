from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import datetime
import logging

_LOGGER = logging.getLogger(__name__)

class MeteoDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, name: str, host: str):
        self.name = name
        self.name2 = name.replace(" ", "_").replace("-", "_").replace(".", "_").lower()
        self.host = host
        self.api_url = f"http://{host}/api/current_reading"
        self.session = async_get_clientsession(hass)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Meteo Station ({host})",
            update_interval=datetime.timedelta(seconds=60),
        )

    async def _async_update_data(self):
        async with self.session.get(self.api_url, timeout=10) as resp:
            return await resp.json()
