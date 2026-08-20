import { useToastStore } from "../store/toast";
import { CloseIcon } from "./icons";

export function ToastStack() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-stack">
      {toasts.map((toast) => (
        <div key={toast.id} className={`toast ${toast.kind}`}>
          <div className="toast-content">
            <div className="toast-title">{toast.title}</div>
            {toast.body && <div className="toast-body">{toast.body}</div>}
          </div>
          <button className="toast-close" onClick={() => dismiss(toast.id)} aria-label="Dismiss">
            <CloseIcon width={12} height={12} />
          </button>
        </div>
      ))}
    </div>
  );
}
