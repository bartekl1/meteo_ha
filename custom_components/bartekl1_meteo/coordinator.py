from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
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
        self.update_interval_seconds = entry.data.get("update_interval", 60)

        super().__init__(
            hass,
            _LOGGER,
            name=f"Meteo Station ({self.url})",
            update_interval=datetime.timedelta(seconds=self.update_interval_seconds)
        )

    async def _async_update_data(self):
        try:
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(self.api_url, timeout=10) as resp:
                    resp.raise_for_status()
                    return await resp.json()
        except Exception as e:
            _LOGGER.error("Error fetching data from %s: %s", self.api_url, e)
            raise UpdateFailed(f"Error fetching data: {e}")
