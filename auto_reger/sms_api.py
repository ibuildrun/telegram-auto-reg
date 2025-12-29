from smsactivate.api import SMSActivateAPI
from datetime import datetime
import logging
import os
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, List

from .utils import PROJECT_ROOT, LOG_FILE


logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
    encoding="utf-8",
)

# File used to track active SMS activations
ACTIVATIONS_FILE: Path = PROJECT_ROOT / "activations.json"


# ---------------------------------------------------------------------------
# Helpers for tracking activations locally
# ---------------------------------------------------------------------------

def _load_activations() -> List[Dict[str, Any]]:
    """
    Load the list of tracked activations from ACTIVATIONS_FILE.

    If the file does not exist or is invalid, an empty list is returned.
    """
    if not ACTIVATIONS_FILE.exists():
        return []
    try:
        with open(ACTIVATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        logging.exception("Failed to read activations file %s", ACTIVATIONS_FILE)
    return []


def _save_activations(data: List[Dict[str, Any]]) -> None:
    """
    Persist the given list of activations to ACTIVATIONS_FILE.
    """
    try:
        ACTIVATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ACTIVATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        logging.exception("Failed to write activations file %s", ACTIVATIONS_FILE)


def save_activation_to_json(activation_id: str, phone_number: str) -> None:
    """
    Append a new activation to the activations.json registry.

    This file is used to track which activations can later be safely cancelled
    (status=8) if they are no longer needed.

    :param activation_id: Provider activation id.
    :param phone_number: Phone number that was reserved.
    """
    data = _load_activations()
    now = datetime.utcnow().isoformat()
    data.append(
        {
            "activation_id": str(activation_id),
            "phone_number": str(phone_number),
            "created_at": now,
        }
    )
    _save_activations(data)
    logging.info("Tracked activation %s for phone %s", activation_id, phone_number)


def remove_activation_from_json(activation_id: str) -> None:
    """
    Remove an activation from the local activations.json registry.

    :param activation_id: Provider activation id to remove.
    """
    data = _load_activations()
    before = len(data)
    data = [row for row in data if str(row.get("activation_id")) != str(activation_id)]
    after = len(data)
    _save_activations(data)
    logging.info(
        "Removed activation %s from registry (before=%s, after=%s)",
        activation_id,
        before,
        after,
    )


def can_set_status_8(activation_id: str, min_age_seconds: int = 120) -> bool:
    """
    Determine whether we can safely set status=8 (cancel) for the given activation.

    Some providers do not allow cancelling an activation immediately after
    reservation. To avoid API errors, we only return True if the activation
    is at least ``min_age_seconds`` old.

    :param activation_id: Provider activation id.
    :param min_age_seconds: Minimal age in seconds to allow cancellation.
    :return: True if the activation is old enough, False otherwise.
    """
    data = _load_activations()
    for row in data:
        if str(row.get("activation_id")) != str(activation_id):
            continue
        created_at = row.get("created_at")
        if not created_at:
            return True  # if timestamp is missing, be optimistic
        try:
            created_dt = datetime.fromisoformat(created_at)
        except ValueError:
            return True
        age = (datetime.utcnow() - created_dt).total_seconds()
        return age >= min_age_seconds
    # Not found → nothing to cancel
    return False


# ---------------------------------------------------------------------------
# SMS API wrapper
# ---------------------------------------------------------------------------

class SmsApi(SMSActivateAPI):
    """
    Thin wrapper around `smsactivate.api.SMSActivateAPI` with a few convenience
    helpers used by this project.

    Features:
      * Read API key from a local file.
      * Support multiple compatible providers (e.g. sms-activate, grizzly-sms).
      * Helper methods for country lookup, number rental and status polling.
    """

    def __init__(self, service: str, api_key_path: str) -> None:
        """
        :param service: Provider identifier. Currently supported:
                        ``"sms-activate"`` and ``"grizzly-sms"``.
        :param api_key_path: Path to a file containing API key (single line).
        """
        api_key_path = os.path.expanduser(api_key_path)
        if not os.path.exists(api_key_path):
            raise FileNotFoundError(f"API key file not found: {api_key_path}")

        with open(api_key_path, "r", encoding="utf-8") as f:
            api_key = f.read().strip()

        if not api_key:
            raise ValueError(f"API key file {api_key_path} is empty")

        super().__init__(api_key)

        self.service_name = service.lower().strip()

        if self.service_name == "sms-activate":
            # Default SMS-Activate handler API
            self.api_url = "https://api.sms-activate.org/stubs/handler_api.php"
        elif self.service_name == "grizzly-sms":
            # GrizzlySMS implements the same handler API interface
            self.api_url = "https://api.grizzlysms.com/stubs/handler_api.php"
        else:
            raise ValueError(f"Unsupported SMS service: {service}")

        logging.info("SmsApi initialised for %s using key file %s", service, api_key_path)

    # ------------------------------------------------------------------ utils

    def _get_country_id(self, country_name: str) -> int:
        """
        Resolve a human-readable country name to provider country id.

        The method queries the provider using ``getCountries()`` and matches
        against the English name (``eng``) or Russian name (``rus``) from
        the response.

        :param country_name: Country name in English (e.g. "USA", "Canada")
                             or Russian (as returned by provider).
        :return: Integer country id used by the provider.
        :raises ValueError: If the country cannot be resolved.
        """
        countries = self.getCountries()
        country_name_norm = country_name.strip().lower()

        for cid, info in countries.items():
            eng = str(info.get("eng", "")).strip().lower()
            rus = str(info.get("rus", "")).strip().lower()
            if country_name_norm in (eng, rus):
                return int(cid)

        raise ValueError(f"Unknown country for SMS provider: {country_name!r}")

    # ----------------------------------------------------------------- public

    def get_numbers_status(self, service: str, country: str) -> Dict[str, Any]:
        """
        Get numbers availability status for a given service and country.

        This is a small convenience wrapper around ``getNumbersStatus`` that
        resolves country name to id and returns only one service entry.

        :param service: Service short name (e.g. "tg" for Telegram).
        :param country: Country name in English/Russian as understood by provider.
        :return: Dict with provider-specific status information for the service.
        """
        country_id = self._get_country_id(country)
        numbers_status = self.getNumbersStatus(country_id)
        return numbers_status.get(service, {})

    def verification_number(
        self,
        service: str,
        country: str,
        max_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Rent a phone number for SMS verification.

        This wraps the provider's ``getNumberV2`` endpoint and normalises the
        response into a dictionary with the following typical keys:

            - ``phoneNumber``    – allocated phone number as string
            - ``activationId``   – activation id to be used with status methods
            - ``activationCost`` – price of the activation, if provided
            - ``error``          – error message (if any)

        :param service: Service short name (e.g. "tg" for Telegram).
        :param country: Country name in English/Russian as understood by provider.
        :param max_price: Optional maximum price filter.
        :return: Response dictionary from provider (possibly containing 'error').
        """
        country_id = self._get_country_id(country)

        kwargs: Dict[str, Any] = {"service": service, "country": int(country_id)}
        if max_price is not None:
            kwargs["maxPrice"] = max_price

        logging.info(
            "Requesting number: service=%s country=%s (id=%s) max_price=%s",
            service,
            country,
            country_id,
            max_price,
        )

        try:
            resp: Dict[str, Any] = self.getNumberV2(**kwargs)
        except Exception as e:
            logging.exception("Error requesting number from SMS API: %s", e)
            return {"error": str(e)}

        # Ensure the returned structure has consistent keys.
        if "phoneNumber" not in resp and "number" in resp:
            resp["phoneNumber"] = resp["number"]

        if "activationId" not in resp and "id" in resp:
            resp["activationId"] = resp["id"]

        return resp

    def get_price(self, service: str, country: str) -> Dict[str, Any]:
        """
        Get current prices for a given service/country pair.

        Used in statistic collector to compare SMS costs between providers.

        :param service: Service short name (e.g. "tg").
        :param country: Country name in English/Russian.
        :return: Raw provider response from ``getPrices``.
        """
        country_id = self._get_country_id(country)
        try:
            resp = self.getPrices(service, country_id)
            return resp
        except Exception as e:
            logging.exception(
                "Error getting prices for service=%s country=%s (id=%s): %s",
                service,
                country,
                country_id,
                e,
            )
            return {}

    def check_verif_status(
        self,
        activation_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> str:
        """
        Poll the provider until an SMS code is received or timeout is reached.

        For most compatible services, this uses ``getStatusV2`` which usually
        returns a dict or a status string. If the code is successfully obtained,
        the activation is marked as finished (status=6).

        On timeout, the activation is cancelled with status=8 when possible.

        :param activation_id: Provider activation id to check.
        :param timeout: Maximum wait time in seconds.
        :param poll_interval: Delay between polling attempts in seconds.
        :return: SMS code as string if received, or an empty string otherwise.
        """
        deadline = time.time() + timeout

        logging.info(
            "Waiting for SMS code, activation_id=%s (timeout=%ss)",
            activation_id,
            timeout,
        )

        while time.time() < deadline:
            try:
                status = self.getStatusV2(activation_id=activation_id)
            except TypeError:
                # some versions of the library expect positional argument only
                status = self.getStatusV2(activation_id)
            except Exception as e:
                logging.exception("Error calling getStatusV2 for %s: %s", activation_id, e)
                time.sleep(poll_interval)
                continue

            if not status:
                time.sleep(poll_interval)
                continue

            code: Optional[str] = None

            # Try to normalise various possible response formats
            if isinstance(status, dict):
                code = (
                    status.get("smsCode")
                    or status.get("code")
                    or status.get("codeNumber")
                )
                current_status = status.get("status") or status.get("statusText")
            else:
                text = str(status)
                current_status = text
                if "STATUS_OK" in text and ":" in text:
                    _, _, maybe_code = text.partition(":")
                    code = maybe_code.strip()

            logging.debug("Activation %s status: %s", activation_id, current_status)

            if code:
                logging.info("Received SMS code for activation %s", activation_id)
                # Attempt to mark as successfully finished
                try:
                    self.setStatus(activation_id, status=6)
                except Exception:
                    logging.exception(
                        "Failed to set status=6 for activation %s",
                        activation_id,
                    )
                return code

            time.sleep(poll_interval)

        # Timeout reached – try to cancel the activation
        logging.warning(
            "No SMS code received for activation %s within %s seconds, cancelling",
            activation_id,
            timeout,
        )
        try:
            self.setStatus(activation_id, status=8)
        except Exception:
            logging.exception("Failed to set status=8 for activation %s", activation_id)

        print("SMS code was not received within the timeout")
        return ""


if __name__ == "__main__":
    # Small manual test stub; replace path/service with your own if needed.
    api_key_file = os.environ.get("SMS_API_KEY_FILE", "sms_activate_api.txt")
    sms = SmsApi(service="sms-activate", api_key_path=api_key_file)
    print("Balance:", sms.getBalance())
