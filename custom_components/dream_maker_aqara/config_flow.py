"""Select the Aqara Devices account that owns the monitors."""

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow

from .const import CONF_SOURCE_ENTRY_ID, DOMAIN, SOURCE_DOMAIN


class DreamMakerConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        sources = {
            entry.entry_id: entry.title
            for entry in self.hass.config_entries.async_entries(SOURCE_DOMAIN)
            if entry.disabled_by is None
        }
        if not sources:
            return self.async_abort(reason="no_source")

        if user_input is not None and (source_id := user_input[CONF_SOURCE_ENTRY_ID]) in sources:
            await self.async_set_unique_id(source_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=sources[source_id], data={CONF_SOURCE_ENTRY_ID: source_id})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_SOURCE_ENTRY_ID): vol.In(sources)}),
        )
