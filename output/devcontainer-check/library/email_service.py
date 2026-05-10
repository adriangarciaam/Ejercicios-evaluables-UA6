import json
import logging
import socket
from urllib import error, request

from django.conf import settings


logger = logging.getLogger(__name__)


class ExternalServiceUnavailableError(Exception):
    pass


class ExternalServiceError(Exception):
    pass


class EmailConfigurationError(ExternalServiceError):
    pass


class EmailService:
    def __init__(
        self,
        *,
        api_url=None,
        api_token=None,
        from_address=None,
        from_name=None,
        timeout=None,
    ):
        self.api_url = api_url if api_url is not None else settings.MAILEROO_API_URL
        self.api_token = (
            api_token if api_token is not None else settings.MAILEROO_API_TOKEN
        )
        self.from_address = (
            from_address
            if from_address is not None
            else settings.MAILEROO_FROM_ADDRESS
        )
        self.from_name = (
            from_name if from_name is not None else settings.MAILEROO_FROM_NAME
        )
        self.timeout = timeout if timeout is not None else settings.MAILEROO_TIMEOUT

    def send_email(
        self,
        to,
        subject,
        text,
        html=None,
        *,
        action="send_email",
        user=None,
    ):
        context = self._build_context(action=action, to=to, user=user)
        logger.info(self._format_log("email_send_attempt", context))

        try:
            self._ensure_configured()
            payload = self._build_payload(
                to=to,
                subject=subject,
                text=text,
                html=html,
            )
            raw_response = self._perform_request(payload)
            parsed_response = self._parse_response(raw_response)
            if parsed_response.get("success") is not True:
                raise ExternalServiceError("invalid_response")
        except ExternalServiceUnavailableError as exc:
            logger.warning(
                self._format_log(
                    "email_send_unavailable",
                    context,
                    result="error",
                    error_type="external_service_unavailable",
                    reason=self._safe_reason(exc),
                )
            )
            raise
        except ExternalServiceError as exc:
            logger.error(
                self._format_log(
                    "email_send_provider_error",
                    context,
                    result="error",
                    error_type="external_service_error",
                    reason=self._safe_reason(exc),
                )
            )
            raise

        logger.info(
            self._format_log(
                "email_send_ok",
                context,
                result="ok",
            )
        )
        return parsed_response

    def _ensure_configured(self):
        if not self.api_token or not self.from_address:
            raise EmailConfigurationError("missing_configuration")

    def _build_payload(self, *, to, subject, text, html=None):
        payload = {
            "from": {"address": self.from_address},
            "to": {"address": to},
            "subject": subject,
            "plain": text,
        }
        if self.from_name:
            payload["from"]["display_name"] = self.from_name
        if html is not None:
            payload["html"] = html
        return payload

    def _perform_request(self, payload):
        data = json.dumps(payload).encode("utf-8")
        email_request = request.Request(
            self.api_url,
            data=data,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self.api_token,
            },
        )

        try:
            with request.urlopen(email_request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise ExternalServiceError(f"http_{exc.code}") from exc
        except (error.URLError, socket.timeout, TimeoutError) as exc:
            raise ExternalServiceUnavailableError(exc.__class__.__name__) from exc

    def _parse_response(self, raw_response):
        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ExternalServiceError("invalid_json_response") from exc

        if not isinstance(data, dict):
            raise ExternalServiceError("invalid_response_type")

        return data

    def _build_context(self, *, action, to, user):
        return {
            "action": action,
            "to": to,
            "user_id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
        }

    def _format_log(self, event, context, **extra):
        values = {
            "event": event,
            "action": context["action"],
            "user_id": context["user_id"] if context["user_id"] is not None else "-",
            "username": context["username"] if context["username"] else "-",
            "to": context["to"],
        }
        values.update(extra)
        return " ".join(f"{key}={value}" for key, value in values.items())

    def _safe_reason(self, exc):
        message = str(exc).strip()
        if not message:
            return exc.__class__.__name__
        return message.replace(" ", "_")
