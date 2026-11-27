"""In-process API transport: no TCP listener, DNS, proxy or HTTP connection."""
import asyncio
from concurrent.futures import Future
import threading
from urllib.parse import urlsplit

import httpx


class AppService:
    # Start the local API worker thread and wait until its asynchronous transport is ready.
    def __init__(self):
        self.ready = Future()
        self.thread = threading.Thread(target=self._run, name="local-data", daemon=True)
        self.thread.start()
        self.ready.result(timeout=30)

    # Run the worker event loop and propagate startup failures to the waiting caller.
    def _run(self):
        try:
            asyncio.run(self._serve())
        except BaseException as exc:
            if not self.ready.done():
                self.ready.set_exception(exc)
            else:
                raise

    # Keep the FastAPI lifespan and in-memory HTTPX transport open until shutdown is requested.
    async def _serve(self):
        from backend import app

        self.loop = asyncio.get_running_loop()
        self.stopped = asyncio.Event()
        async with app.router.lifespan_context(app):
            # The URL is only an ASGI request scope; the transport never opens a socket.
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="http://desktop.invalid", trust_env=False) as client:
                self.client = client
                self.ready.set_result(True)
                await self.stopped.wait()

    # Validate a local request and dispatch it directly to ASGI without opening a network connection.
    async def _request(self, request):
        path = request.get("path", "")
        parsed = urlsplit(path)
        method = request.get("method", "GET").upper()
        if (not path.startswith("/") or path.startswith("//") or parsed.netloc
                or parsed.scheme or method not in {"GET", "POST", "PUT", "DELETE"}):
            return {"status": 400, "data": {"detail": "Requête locale invalide."}}
        response = await self.client.request(method, path, params=request.get("params"),
                                             headers=request.get("headers"), json=request.get("data"))
        return {"status": response.status_code, "data": response.json()}

    # Schedule an API request on the worker loop and return a thread-safe future.
    def submit(self, request):
        return asyncio.run_coroutine_threadsafe(self._request(request), self.loop)

    # Signal the worker to shut down and wait for its thread to finish.
    def close(self):
        self.loop.call_soon_threadsafe(self.stopped.set)
        self.thread.join(timeout=30)
