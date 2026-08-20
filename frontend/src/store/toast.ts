import { create } from "zustand";

export interface Toast {
  id: number;
  kind: "error" | "success";
  title: string;
  body?: string;
}

interface ToastState {
  toasts: Toast[];
  push: (toast: Omit<Toast, "id">) => void;
  dismiss: (id: number) => void;
}

let nextId = 1;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => {
    const id = nextId++;
    set((state) => ({ toasts: [...state.toasts, { ...toast, id }] }));
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 5000);
  },
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));

export function pushErrorToast(title: string, body?: string) {
  useToastStore.getState().push({ kind: "error", title, body });
}

export function pushSuccessToast(title: string, body?: string) {
  useToastStore.getState().push({ kind: "success", title, body });
}
