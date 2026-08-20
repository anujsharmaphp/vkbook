import { wsBaseUrl } from "./httpClient";
import type { WsMessage } from "../types/api";

type MessageHandler = (message: WsMessage) => void;

interface ManagedSocket {
  ws: WebSocket | null;
  handlers: Set<MessageHandler>;
  reconnectAttempts: number;
  reconnectTimer: ReturnType<typeof setTimeout> | null;
  heartbeatTimer: ReturnType<typeof setInterval> | null;
  closedIntentionally: boolean;
}

const sockets = new Map<string, ManagedSocket>();

const HEARTBEAT_INTERVAL_MS = 20_000;
const MAX_BACKOFF_MS = 15_000;

function openSocket(path: string, entry: ManagedSocket): void {
  const ws = new WebSocket(`${wsBaseUrl()}${path}`);
  entry.ws = ws;
  entry.closedIntentionally = false;

  ws.onopen = () => {
    entry.reconnectAttempts = 0;
    entry.heartbeatTimer = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) ws.send("ping");
    }, HEARTBEAT_INTERVAL_MS);
  };

  ws.onmessage = (event) => {
    if (event.data === "pong") return;
    try {
      const data = JSON.parse(event.data) as WsMessage;
      entry.handlers.forEach((handler) => handler(data));
    } catch {
      /* ignore malformed frames */
    }
  };

  ws.onclose = () => {
    if (entry.heartbeatTimer) clearInterval(entry.heartbeatTimer);
    entry.heartbeatTimer = null;
    if (entry.closedIntentionally || entry.handlers.size === 0) return;

    const delay = Math.min(1000 * 2 ** entry.reconnectAttempts, MAX_BACKOFF_MS);
    entry.reconnectAttempts += 1;
    entry.reconnectTimer = setTimeout(() => openSocket(path, entry), delay);
  };

  ws.onerror = () => {
    ws.close();
  };
}

function ensureSocket(path: string): ManagedSocket {
  let entry = sockets.get(path);
  if (!entry) {
    entry = {
      ws: null,
      handlers: new Set(),
      reconnectAttempts: 0,
      reconnectTimer: null,
      heartbeatTimer: null,
      closedIntentionally: false,
    };
    sockets.set(path, entry);
  }
  if (!entry.ws || entry.ws.readyState === WebSocket.CLOSED) {
    openSocket(path, entry);
  }
  return entry;
}

/** Subscribes to a topic path (e.g. `/ws/markets/{id}`, `/ws/user?token=...`).
 * Multiple subscribers to the same path share one socket. Returns an
 * unsubscribe function; the socket closes once the last subscriber leaves. */
export function subscribeTopic(path: string, handler: MessageHandler): () => void {
  const entry = ensureSocket(path);
  entry.handlers.add(handler);

  return () => {
    entry.handlers.delete(handler);
    if (entry.handlers.size === 0) {
      entry.closedIntentionally = true;
      if (entry.reconnectTimer) clearTimeout(entry.reconnectTimer);
      if (entry.heartbeatTimer) clearInterval(entry.heartbeatTimer);
      entry.ws?.close();
      sockets.delete(path);
    }
  };
}
