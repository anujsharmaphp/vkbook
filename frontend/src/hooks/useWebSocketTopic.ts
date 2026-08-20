import { useEffect } from "react";
import { subscribeTopic } from "../services/websocket";
import type { WsMessage } from "../types/api";

/** Subscribes to a WS topic path for the lifetime of the component. Pass
 * `null` to skip subscribing (e.g. while an id isn't known yet). */
export function useWebSocketTopic(path: string | null, onMessage: (message: WsMessage) => void) {
  useEffect(() => {
    if (!path) return;
    const unsubscribe = subscribeTopic(path, onMessage);
    return unsubscribe;
    // Intentionally re-subscribing only when the topic path itself changes —
    // `onMessage` closures are expected to change every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path]);
}
