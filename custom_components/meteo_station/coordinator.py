from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import datetime
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

class MeteoDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry):
        self.entry = entry
        self.name = entry.data["name"]
        self.name2 = self.name.replace(" ", "_").replace("-", "_").replace(".", "_").lower()
        self.url = entry.data["url"]
        self.api_url = f"{self.url}/api/current_reading"
        self.verify_ssl = entry.data.get("verify_ssl", True)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Meteo Station ({self.url})",
            update_interval=datetime.timedelta(seconds=60),
        )

    async def _async_update_data(self):
        try:
            connector = None
            if not self.verify_ssl:
                connector = aiohttp.TCPConnector(verify_ssl=False)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(self.api_url, timeout=10) as resp:
                    return await resp.json()
        except Exception as e:
            # _LOGGER.error("Error fetching data: %s", e)
            raise
