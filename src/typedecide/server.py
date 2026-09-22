"""Serve one typedecide backend over the System One HTTP API."""

from __future__ import annotations

import argparse
import hmac
import inspect
import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .base import DecisionBackend
from .registry import available_backends, load
from .wire import WireError, encode_system_one, parse_system_one

_MAX_BODY_BYTES = 8_000_000


class App:
    """One loaded backend and the HTTP behavior in front of it.

    Parameters
    ----------
    backend : DecisionBackend
        Model that answers every evaluation.
    model_name : str
        Model id reported by ``GET /v1/models``. This is the id chosen at
        startup, not a name sent by a client.
    api_key : str or None
        Bearer token required on ``/v1`` routes. ``None`` leaves those routes open.
    """

    def __init__(
        self, backend: DecisionBackend, model_name: str, api_key: str | None
    ) -> None:
        self.backend = backend
        self.model_name = model_name
        self.api_key = api_key
        self._predict_lock = threading.Lock()

    def models(self) -> dict[str, Any]:
        """Describe the single model this process serves.

        Returns
        -------
        dict
            Official list-models body with one entry.
        """
        return {
            "models": [
                {
                    "name": self.model_name,
                    "description": f"{self.backend.name} served by typedecide",
                    "release_date": "local",
                }
            ]
        }

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate one System One request on the loaded backend.

        Parameters
        ----------
        payload : dict
            Official request body. Its ``model`` field does not select a backend.

        Returns
        -------
        dict
            Official response body. ``model`` is the backend's resolved id.
        """
        state, questions = parse_system_one(payload)
        with self._predict_lock:
            response = self.backend.predict(state, questions)
        return encode_system_one(response, questions)

    def close(self) -> None:
        """Release the loaded backend."""
        self.backend.close()


def playground_html() -> str:
    """Read the server UI shipped with the package.

    Returns
    -------
    str
        Playground document served at ``GET /``.
    """
    resource = files("typedecide").joinpath("playground/index.html")
    try:
        return resource.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return (
            Path(__file__)
            .resolve()
            .parent.joinpath("playground/index.html")
            .read_text(encoding="utf-8")
        )


def playground_scoreboard() -> bytes:
    """Read the packaged benchmark scoreboard snapshot for the playground."""
    return files("typedecide").joinpath("playground/scoreboard.json").read_bytes()


def backend_config(backend: str, model: str | None, device: str) -> dict[str, Any]:
    """Build ``load`` kwargs for a serve command.

    Parameters
    ----------
    backend : str
        Backend name.
    model : str or None
        Optional model id. Omitted when the caller wants the backend default.
    device : str
        Requested device. Jev never receives it. Laya receives it only when
        it is not ``"auto"``.

    Returns
    -------
    dict
        Keyword arguments for :func:`typedecide.load`.
    """
    config: dict[str, Any] = {}
    if model:
        config["model"] = model
    if backend in {"thisthat", "semif"} or backend == "laya" and device != "auto":
        config["device"] = device
    return config


def model_name_for(backend: DecisionBackend, explicit: str | None) -> str:
    """Return the model id to advertise for a loaded backend.

    Parameters
    ----------
    backend : DecisionBackend
        Loaded backend. Its class ``from_config`` supplies the default id.
    explicit : str or None
        Model id passed on the command line, when the caller set one.

    Returns
    -------
    str
        ``explicit`` when it is set, otherwise the backend's default model id.
    """
    if explicit:
        return explicit
    default = inspect.signature(type(backend).from_config).parameters["model"].default
    if not isinstance(default, str):
        raise TypeError(f"{type(backend).__name__} has no string model default")
    return default


def parser() -> argparse.ArgumentParser:
    """Build the ``typedecide-serve`` argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser for backend, model, device, bind address, and API key.
    """
    command = argparse.ArgumentParser(
        description="Serve one typedecide backend over the System One HTTP API."
    )
    command.add_argument("--backend", choices=available_backends(), required=True)
    command.add_argument("--model", help="model id forwarded to the backend")
    command.add_argument("--device", default="auto")
    command.add_argument("--host", default="127.0.0.1")
    command.add_argument("--port", type=int, default=8000)
    command.add_argument("--api-key", help="require this bearer token on /v1 routes")
    return command


def bind(app: App, host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    """Bind a server for ``app`` without loading a backend.

    Parameters
    ----------
    app : App
        Request handler state.
    host : str, optional
        Bind address.
    port : int, optional
        Bind port. ``0`` asks the OS for a free port.

    Returns
    -------
    ThreadingHTTPServer
        A server that is listening and not yet serving.
    """
    return ThreadingHTTPServer((host, port), _handler(app))


def main() -> int:
    """Load one backend and serve until interrupted.

    Returns
    -------
    int
        Process status code. ``0`` means the server stopped cleanly.
    """
    args = parser().parse_args()
    backend = load(
        args.backend, **backend_config(args.backend, args.model, args.device)
    )
    app = App(backend, model_name_for(backend, args.model), args.api_key)
    server = bind(app, args.host, args.port)
    host, port = server.server_address[:2]
    print(f"serving {args.backend} ({app.model_name}) at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()
    return 0


def _handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                body = playground_html().encode()
                self._send(200, body, "text/html; charset=utf-8")
                return
            if path == "/playground/scoreboard.json":
                self._send(200, playground_scoreboard(), "application/json")
                return
            if path == "/v1/models":
                if not self._authorized():
                    return
                self._send_json(200, app.models())
                return
            self._send_json(404, _error("not found", None))

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path != "/v1/systemone":
                self._send_json(404, _error("not found", None))
                return
            if not self._authorized():
                return
            raw = self._read_body()
            if raw is None:
                return
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self._send_json(422, _error("request body must be JSON", None))
                return
            if not isinstance(payload, dict):
                self._send_json(422, _error("request body must be an object", None))
                return
            try:
                result = app.evaluate(payload)
            except WireError as error:
                self._send_json(422, _error(str(error), error.field))
                return
            except Exception as error:  # noqa: BLE001
                traceback.print_exc()
                self._send_json(500, _error(str(error) or "evaluation failed", None))
                return
            self._send_json(200, result)

        def _authorized(self) -> bool:
            if app.api_key is None:
                return True
            header = self.headers.get("Authorization", "")
            scheme, _, token = header.partition(" ")
            if scheme.lower() == "bearer" and hmac.compare_digest(
                app.api_key.encode(), token.encode()
            ):
                return True
            self._send_json(401, _error("Missing or invalid API key.", None))
            return False

        def _read_body(self) -> bytes | None:
            length = self.headers.get("Content-Length")
            if length is None or not length.isdigit():
                self._send_json(422, _error("Content-Length is required", None))
                return None
            size = int(length)
            if size > _MAX_BODY_BYTES:
                self._send_json(422, _error("request body is too large", None))
                return None
            return self.rfile.read(size)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode()
            self._send(status, body, "application/json; charset=utf-8")

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _error(message: str, field: str | None) -> dict[str, Any]:
    return {"error": {"message": message, "field": field}}


if __name__ == "__main__":
    raise SystemExit(main())
