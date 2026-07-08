# base_api.py
"""
Base client for REST calls against Jira-based APIs.

All common functionalities (header handling, authentication,
optional proxy configuration, logging, HTTP methods) are encapsulated here,
so that derived classes (e.g. JiraAPI, XrayAPI) only need to care about their
business-specific endpoints.
"""

from __future__ import annotations
import json
import logging
from typing import Dict, Optional

import requests
from requests import Response, Session
from requests.auth import HTTPBasicAuth


class RestAPIClient:
    """Abstract base class for simple REST clients."""

    #: Default headers for all requests
    DEFAULT_HEADERS: Dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
    }

    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        *,
        proxies: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        logger: Optional[logging.Logger] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Parameters
        ----------
        base_url:
            Base URL of the Jira instance, e.g. ``https://jira.example.com/``
            (without *rest/api/...*).
        user / password:
            Jira user credentials.
        proxies:
            Optional proxy dictionary like in ``requests`` (e.g.
            ``{"http": "http://proxy:8080", "https": "http://proxy:8080"}``).
            Can be adjusted later via :meth:`set_proxies`.
        headers:
            Additional or overriding HTTP headers.
        logger:
            If *None*, a ``logging.getLogger(classname)`` is created.
        session:
            Custom ``requests.Session`` (for connection pooling, retry strategies,
            etc.). If *None*, a new session is created internally.
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.auth = HTTPBasicAuth(user, password)
        self._proxies = proxies  # can be None
        self.headers = {**self.DEFAULT_HEADERS, **(headers or {})}
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.session: Session = session or requests.Session()

    # ------------------------------------------------------------------ #
    # Public helper functions                                            #
    # ------------------------------------------------------------------ #

    def set_proxies(self, proxies: Optional[Dict[str, str]]) -> None:
        """Change proxy configuration retrospectively or deactivate it completely."""
        self.logger.debug("Proxy setting changed: %s", proxies)
        self._proxies = proxies

    # ------------------------------------------------------------------ #
    # HTTP methods                                                       #
    # ------------------------------------------------------------------ #

    def get(self, endpoint: str, **kwargs) -> Response:
        return self._request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, data=None, **kwargs) -> Response:
        if data is not None:
            kwargs['data'] = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return self._request("POST", endpoint, **kwargs)

    def put(self, endpoint: str, data=None, **kwargs) -> Response:
        if data is not None:
            kwargs['data'] = json.dumps(data, ensure_ascii=False).encode('utf-8')
        return self._request("PUT", endpoint, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> Response:
        return self._request("DELETE", endpoint, **kwargs)

    # ------------------------------------------------------------------ #
    # Internal implementation                                            #
    # ------------------------------------------------------------------ #

    def _request(self, method: str, endpoint: str, **kwargs) -> Response:
        """
        Executes an HTTP request and returns the ``Response`` object.
        A JSON payload is automatically serialized, headers & proxies are
        added.
        """
        url = endpoint if endpoint.startswith("http") else self.base_url + endpoint
        self.logger.debug("%s %s", method, url)

        # Default headers + any passed headers
        hdrs = {**self.headers, **kwargs.pop("headers", {})}
        
        resp = self.session.request(
            method,
            url,
            auth=self.auth,
            headers=hdrs,
            proxies=self._proxies,
            timeout=kwargs.pop("timeout", 30),
            **kwargs,
        )

        # Log error, but do not automatically raise an exception –
        # we leave that to the callers.
        if not resp.ok:
            try:
                error_payload = resp.json()
            except ValueError:
                error_payload = resp.text
            print(f"Error response {resp.status_code} for {method} {url} {error_payload}")
            self.logger.debug(f"Error response {resp.status_code} for {method} {url} {error_payload}")
        return resp

    # ------------------------------------------------------------------ #
    # Utility: Save response as JSON file (debugging)                    #
    # ------------------------------------------------------------------ #

    def save_response(self, response: Response, path: str = "response.json") -> None:
        """Write response content (JSON) to file – for debugging purposes."""
        try:
            data = response.json()
        except ValueError:
            self.logger.error("No valid JSON response → %s", path)
            data = {"raw": response.text}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info("Response saved under %s", path)
