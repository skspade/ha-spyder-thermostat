"""Support for Spyder sensors."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

# Use the newer location for async_timeout
from async_timeout import timeout

import aiohttp

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    TEMP_FAHRENHEIT,
    PERCENTAGE,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, SCAN_INTERVAL
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Spyder sensors based on a config entry."""
    host = entry.data[CONF_HOST]

    async def async_update_data():
        """Fetch data from API endpoint."""
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{host}/rawstatus") as resp:
                    return await resp.json()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="spyder_sensor",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Add sensors for each active output
    data = coordinator.data
    for i in range(1, data["system"]["numberofoutputs"] + 1):
        output_key = f"output{i}"
        if data[output_key]["outputmode"] != "Disabled":
            entities.extend([
                SpyderTemperatureSensor(coordinator, output_key),
                SpyderPowerSensor(coordinator, output_key),
                SpyderHighAlarmSensor(coordinator, output_key),
                SpyderLowAlarmSensor(coordinator, output_key),
            ])

    # Add system sensors
    entities.extend([
        SpyderInternalTempSensor(coordinator),
        SpyderPowerResetsSensor(coordinator),
        SpyderSafetyRelaySensor(coordinator),
    ])

    async_add_entities(entities)


class SpyderTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spyder temperature sensor."""

    def __init__(self, coordinator, output):
        super().__init__(coordinator)
        self._output = output
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = TEMP_FAHRENHEIT
        self._attr_unique_id = f"spyder_{output}_temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Spyder {self.coordinator.data[self._output]['outputnickname']} Temperature"

    @property
    def native_value(self):
        """Return the temperature."""
        return self.coordinator.data[self._output]["probereadingTEMP"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "max_temp": self.coordinator.data[self._output]["probereadingTEMPMAX"],
            "min_temp": self.coordinator.data[self._output]["probereadingTEMPMIN"],
            "current_setting": self.coordinator.data[self._output]["currentsetting"],
            "error_code": self.coordinator.data[self._output]["errorcode"],
            "error_description": self.coordinator.data[self._output]["errorcodedescription"],
        }


class SpyderPowerSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spyder power output sensor."""

    def __init__(self, coordinator, output):
        super().__init__(coordinator)
        self._output = output
        self._attr_device_class = SensorDeviceClass.POWER
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_unique_id = f"spyder_{output}_power"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Spyder {self.coordinator.data[self._output]['outputnickname']} Power"

    @property
    def native_value(self):
        """Return the power output."""
        return self.coordinator.data[self._output]["poweroutput"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "power_limit": self.coordinator.data[self._output]["poweroutputLIMIT"],
            "mode": self.coordinator.data[self._output]["outputmode"],
        }


class SpyderInternalTempSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Spyder internal temperature sensor."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = TEMP_FAHRENHEIT
        self._attr_unique_id = "spyder_internal_temperature"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Spyder Internal Temperature"

    @property
    def native_value(self):
        """Return the internal temperature."""
        return self.coordinator.data["system"]["internaltemp"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "max_temp": self.coordinator.data["system"]["internaltempmax"],
        }


class SpyderHighAlarmSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spyder high alarm temperature sensor."""

    def __init__(self, coordinator, output):
        super().__init__(coordinator)
        self._output = output
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = TEMP_FAHRENHEIT
        self._attr_unique_id = f"spyder_{output}_high_alarm"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Spyder {self.coordinator.data[self._output]['outputnickname']} High Alarm"

    @property
    def native_value(self):
        """Return the high alarm temperature."""
        return self.coordinator.data[self._output]["highalarm"]


class SpyderLowAlarmSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spyder low alarm temperature sensor."""

    def __init__(self, coordinator, output):
        super().__init__(coordinator)
        self._output = output
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = TEMP_FAHRENHEIT
        self._attr_unique_id = f"spyder_{output}_low_alarm"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Spyder {self.coordinator.data[self._output]['outputnickname']} Low Alarm"

    @property
    def native_value(self):
        """Return the low alarm temperature."""
        return self.coordinator.data[self._output]["lowalarm"]


class SpyderPowerResetsSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Spyder power resets sensor."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_state_class = SensorStateClass.TOTAL
        self._attr_unique_id = "spyder_power_resets"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Spyder Power Resets"

    @property
    def native_value(self):
        """Return the number of power resets."""
        return self.coordinator.data["system"]["powerresets"]


class SpyderSafetyRelaySensor(CoordinatorEntity, SensorEntity):
    """Representation of the Spyder safety relay sensor."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = "spyder_safety_relay"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Spyder Safety Relay"

    @property
    def native_value(self):
        """Return the safety relay status."""
        return self.coordinator.data["system"]["safetyrelay"]
