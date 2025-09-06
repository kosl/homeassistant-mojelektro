import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .moj_elektro_api import MojElektroApi
from .const import DOMAIN, CONF_TOKEN, CONF_METER_ID, CONF_DECIMAL, CONF_SHOW_ET_ONLY

class MojeElektroFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            decimal = user_input.get(CONF_DECIMAL)  # This returns None if CONF_DECIMAL is not in user_input                         
            show_et_only = user_input.get(CONF_SHOW_ET_ONLY, False)  # Default to False if not provided                              
            api = MojElektroApi(user_input[CONF_TOKEN], user_input[CONF_METER_ID], decimal, show_et_only, session)
            valid = await api.validate_token()
            if valid:
                return self.async_create_entry(title="Moj Elektro", data=user_input)
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_METER_ID): str,
                vol.Optional(CONF_DECIMAL): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
                vol.Optional(CONF_SHOW_ET_ONLY, default=False): bool
            }),
            errors=errors,
        )
    
    async def async_step_reconfigure(self, user_input=None):
        """Initiate reconfiguration."""
        # Get the existing config entry
        entry_id = self.context["entry_id"]
        entry = self.hass.config_entries.async_get_entry(entry_id)
        
        errors = {}
        
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            decimal = user_input.get(CONF_DECIMAL)
            show_et_only = user_input.get(CONF_SHOW_ET_ONLY, False)
            api = MojElektroApi(user_input[CONF_TOKEN], user_input[CONF_METER_ID], decimal, show_et_only, session)
            valid = await api.validate_token()
            
            if valid:
                # Update the existing entry
                self.hass.config_entries.async_update_entry(
                    entry, data=user_input
                )
                # Reload the entry to apply changes
                await self.hass.config_entries.async_reload(entry_id)
                return self.async_abort(reason="reconfigure_successful")
            else:
                errors["base"] = "invalid_auth"
        
        # Pre-fill form with current values
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_TOKEN, 
                    default=entry.data.get(CONF_TOKEN)
                ): str,
                vol.Required(
                    CONF_METER_ID, 
                    default=entry.data.get(CONF_METER_ID)
                ): str,
                vol.Optional(
                    CONF_DECIMAL, 
                    default=entry.data.get(CONF_DECIMAL)
                ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
                vol.Optional(
                    CONF_SHOW_ET_ONLY, 
                    default=entry.data.get(CONF_SHOW_ET_ONLY, False)
                ): bool
            }),
            errors=errors,
        )
