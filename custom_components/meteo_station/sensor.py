from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorEntityDescription
from homeassistant.const import UnitOfTemperature, UnitOfPressure, CONCENTRATION_MICROGRAMS_PER_CUBIC_METER, PERCENTAGE
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import math

sensors = [
    (
        SensorEntityDescription(
            key="ds18b20_temperature",
            name="Temperature DS18B20",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class="measurement",
            translation_key="ds18b20_temperature"),
        "ds18b20", "temperature"
    ),
    (
        SensorEntityDescription(
            key="bme280_temperature",
            name="Temperature BME280",
            device_class=SensorDeviceClass.TEMPERATURE,
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class="measurement",
            translation_key="bme280_temperature"),
        "bme280", "temperature"
    ),
    (
        SensorEntityDescription(
            key="bme280_humidity",
            name="Humidity BME280",
            device_class=SensorDeviceClass.HUMIDITY,
            native_unit_of_measurement=PERCENTAGE,
            state_class="measurement",
            translation_key="bme280_humidity"),
        "bme280", "humidity"
    ),
    (
        SensorEntityDescription(
            key="bme280_pressure",
            name="Pressure BME280",
            device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
            native_unit_of_measurement=UnitOfPressure.HPA,
            state_class="measurement",
            translation_key="bme280_pressure"),
        "bme280", "pressure"
    ),
    (
        SensorEntityDescription(
            key="pms5003_pm1",
            name="PM 1.0 PMS5003",
            device_class=SensorDeviceClass.PM1,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class="measurement",
            translation_key="pms5003_pm1"),
        "pms5003", "pm1.0"
    ),
    (
        SensorEntityDescription(
            key="pms5003_pm25",
            name="PM 2.5 PMS5003",
            device_class=SensorDeviceClass.PM25,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class="measurement",
            translation_key="pms5003_pm25"),
        "pms5003", "pm2.5"),
    (
        SensorEntityDescription(
            key="pms5003_pm10",
            name="PM 10 PMS5003",
            device_class=SensorDeviceClass.PM10,
            native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            state_class="measurement",
            translation_key="pms5003_pm10"),
        "pms5003", "pm10"
    )
]

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        MeteoSensor(coordinator, description, sensor_name, reading_name)
        for description, sensor_name, reading_name in sensors
    ]
    entities.append(DewPointSensor(coordinator, "Dew Point BME280", "bme280", "bme280_dewpoint"))
    entities.append(DewPointSensor(coordinator, "Dew Point DS18B20 + BME280", "ds18b20", "ds18b20_dewpoint"))
    entities.append(AQISensor(coordinator, "AQI PMS5003", "pms5003", "pms5003_aqi"))

    async_add_entities(entities)


class MeteoSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, description: SensorEntityDescription, sensor_name, reading_name):
        super().__init__(coordinator)

        self._coordinator = coordinator
        self._sensor_name = sensor_name
        self._reading_name = reading_name
        self.entity_description = description

        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_state_class = description.state_class
        self._attr_should_poll = False

        self._attr_translation_key = description.translation_key
        self._attr_has_entity_name = True

    @property
    def unique_id(self):
        return f"{self._coordinator.name2}_{self.entity_description.key}"

    @property
    def state(self):
        data = self._coordinator.data
        sensor_data = data.get(self._sensor_name, {})
        value = sensor_data.get(self._reading_name)
        if isinstance(value, (int, float)):
            return round(value, 2)
        return None

    @property
    def available(self):
        return self._coordinator.last_update_success

    async def async_update(self):
        await self._coordinator.async_request_refresh()

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._coordinator.url)},
            name=self._coordinator.entry.data.get("name", self._coordinator.url),
            manufacturer="bartekl1",
            model="Meteo Station",
            configuration_url=self._coordinator.url,
        )


class DewPointSensor(MeteoSensor):
    def __init__(self, coordinator, name, temperature_sensor, translation_key):
        super().__init__(coordinator,
                         SensorEntityDescription(
                            key=translation_key,
                            name=name,
                            device_class=SensorDeviceClass.TEMPERATURE,
                            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                            state_class="measurement",
                            translation_key=translation_key
                         ), temperature_sensor, "dewpoint")
        self._temperature_sensor = temperature_sensor

    @property
    def state(self):
        t = self._coordinator.data[self._temperature_sensor]["temperature"]
        rh = self._coordinator.data["bme280"]["humidity"]

        e = 6.112 * math.exp((17.67 * t) / (t + 243.5))
        e_d = e * (rh / 100)
        T_d = (243.5 * math.log(e_d / 6.112)) / (17.67 - math.log(e_d / 6.112))

        return round(T_d, 2)


class AQISensor(MeteoSensor):
    def __init__(self, coordinator, name, pm_sensor, translation_key):
        super().__init__(coordinator,
                         SensorEntityDescription(
                            key=translation_key,
                            name=name,
                            device_class=SensorDeviceClass.AQI,
                            native_unit_of_measurement=PERCENTAGE,
                            state_class="measurement",
                            translation_key=translation_key
                         ), pm_sensor, "aqi")
        self._pm_sensor = pm_sensor

    @property
    def state(self):
        pm10 = self._coordinator.data[self._pm_sensor]["pm10"]
        pm25 = self._coordinator.data[self._pm_sensor]["pm2.5"]

        aqi = ((pm10 / 1.8) + (pm25 / 1.1)) / 2
        return round(aqi, 2)
