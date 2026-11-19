import { createContext, useContext, type ReactNode } from "react";
import { useLiveCluster } from "./useLiveCluster";
import type { LiveEvent, Overview } from "./types";

interface ClusterContextValue {
  overview: Overview | null;
  connected: boolean;
  feed: LiveEvent[];
  loading: boolean;
  error: unknown;
  refetch: () => unknown;
}

const ClusterContext = createContext<ClusterContextValue | null>(null);

export function ClusterProvider({ children }: { children: ReactNode }) {
  const value = useLiveCluster();
  return <ClusterContext.Provider value={value}>{children}</ClusterContext.Provider>;
}

export function useCluster(): ClusterContextValue {
  const context = useContext(ClusterContext);
  if (!context) throw new Error("useCluster must be used inside ClusterProvider");
  return context;
}
