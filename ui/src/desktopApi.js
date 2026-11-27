// Same response/error shape as the original client, over Qt IPC only.
let channelPromise;
let nextId = 0;
const pending = new Map();

// Initialize and cache the Qt WebChannel connection used for local API requests.
function bridge() {
  if (!channelPromise) {
    channelPromise = new Promise((resolve, reject) => {
      // Require the desktop Qt transport and begin WebChannel initialization.
      if (!window.qt?.webChannelTransport || !window.QWebChannel) {
        reject(new Error("Lancez cette interface avec OSINT Graph Desktop."));
        return;
      }
      new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
        // Attach the response listener to the exposed desktop bridge and signal that it is ready.
        const api = channel.objects.desktop;
        api.response.connect((raw) => {
          // Match a bridge response to its pending request and resolve it or construct an API-style error.
          const result = JSON.parse(raw);
          const request = pending.get(result.id);
          if (!request) return;
          pending.delete(result.id);
          if (result.status >= 400) {
            const details = result.data?.detail;
            const message = Array.isArray(details)
              ? details.map(/* Extract each validation message for a readable combined error. */ (item) => item.msg).join(" ; ")
              : details || "Opération impossible.";
            const error = new Error(message);
            error.response = { status: result.status, data: { ...result.data, detail: message } };
            request.reject(error);
          } else {
            request.resolve({ status: result.status, data: result.data });
          }
        });
        resolve(api);
      });
    });
  }
  return channelPromise;
}

// Send a uniquely identified API request over Qt and resolve it when the matching response arrives.
async function request(method, path, data, config = {}) {
  const api = await bridge();
  const id = String(++nextId);
  return new Promise((resolve, reject) => {
    // Register the pending response handlers and send the serialized request to Python.
    pending.set(id, { resolve, reject });
    try {
      api.request(JSON.stringify({ id, method, path, data, params: config.params, headers: config.headers }));
    } catch (error) {
      pending.delete(id);
      reject(error);
    }
  });
}

// Save JSON through the native desktop dialog and return whether the user completed the export.
export async function saveJson(fileName, data) {
  const api = await bridge();
  return new Promise((resolve, reject) => {
    // Serialize the export data and invoke the native save dialog through Qt.
    api.saveJson(fileName, JSON.stringify(data, null, 2), (raw) => {
      // Resolve the native save result or reject the reported file error.
      const result = JSON.parse(raw);
      if (result.error) reject(new Error(result.error));
      else resolve(result.saved);
    });
  });
}

export default {
  get: /* Send a local GET request through the shared Qt transport. */ (path, config) => request("GET", path, undefined, config),
  post: /* Send a local POST request with its data through the shared Qt transport. */ (path, data, config) => request("POST", path, data, config),
  put: /* Send a local PUT request with its data through the shared Qt transport. */ (path, data, config) => request("PUT", path, data, config),
  delete: /* Send a local DELETE request through the shared Qt transport. */ (path, config) => request("DELETE", path, undefined, config),
};
