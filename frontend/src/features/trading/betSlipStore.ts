import { create } from "zustand";
import type { OrderSide, UUID } from "../../types/api";

export interface BetSlipSelection {
  marketId: UUID;
  marketName: string;
  selectionId: UUID;
  selectionName: string;
  side: OrderSide;
  price: number;
}

interface BetSlipState {
  selection: BetSlipSelection | null;
  stakeMinor: number;
  setSelection: (selection: BetSlipSelection) => void;
  setStakeMinor: (stakeMinor: number) => void;
  clear: () => void;
}

export const useBetSlipStore = create<BetSlipState>((set) => ({
  selection: null,
  stakeMinor: 100_00, // ₹100 default stake
  setSelection: (selection) => set({ selection }),
  setStakeMinor: (stakeMinor) => set({ stakeMinor: Math.max(0, stakeMinor) }),
  clear: () => set({ selection: null }),
}));
