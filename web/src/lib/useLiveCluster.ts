import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import type { LiveEvent, NodeInfo, Overview } from "./types";

function recompute(overview: Overview, nodes: NodeInfo[]): Overview {
  const workers = nodes.filter((n) => n.role === "worker");
  const active = workers.filter((n) => !["offline", "pending", "removed", "discovered"].includes(n.status));
  const offline = workers.filter((n) => n.status === "offline");
  return {
    ...overview,
    nodes,
    total_nodes: nodes.length,
    active_workers: active.length,
    offline_workers: offline.length,
    total_cpu_cores: nodes.reduce((sum, n) => sum + n.cpu_cores, 0),
    total_memory: nodes.reduce((sum, n) => sum + n.memory_total, 0),
  };
}

function mergeNode(overview: Overview, incoming: NodeInfo): Overview {
  const exists = overview.nodes.some((n) => n.worker_id === incoming.worker_id);
  const nodes = exists
    ? overview.nodes.map((n) => (n.worker_id === incoming.worker_id ? incoming : n))
    : [...overview.nodes, incoming];
  return recompute(overview, nodes);
}

const FEED_KINDS = new Set([
  "cluster.initialized",
  "node.updated",
  "node.offline",
  "node.removed",
  "failure.simulated",
  "job.updated",
  "job.completed",
  "task.completed",
  "task.requeued",
  "task.failed",
  "worker.failed",
  "experiment.updated",
]);

export function useLiveCluster() {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["overview"],
    queryFn: api.overview,
    refetchInterval: 20_000,
    retry: 2,
  });

  const [live, setLive] = useState<Overview | null>(null);
  const [connected, setConnected] = useState(false);
  const [feed, setFeed] = useState<LiveEvent[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  useEffect(() => {
    let closed = false;
    let timer: number | undefined;

    const connect = () => {
      const scheme = window.location.protocol === "https:" ? "wss" : "ws";
      const socket = new WebSocket(`${scheme}://${window.location.host}/ws`);
      socketRef.current = socket;

      socket.onopen = () => {
        retryRef.current = 0;
        setConnected(true);
      };

      socket.onmessage = (event) => {
        let message: LiveEvent;
        try {
          message = JSON.parse(event.data) as LiveEvent;
        } catch {
          return;
        }

        if (message.kind === "snapshot") {
          setLive(message.payload as Overview);
          return;
        }
        if (message.kind === "pong") return;

        if (FEED_KINDS.has(message.kind)) {
          setFeed((prev) => [message, ...prev].slice(0, 40));
        }

        if (message.kind === "node.updated") {
          const node = message.payload as NodeInfo;
          setLive((prev) => (prev ? mergeNode(prev, node) : prev));
        }
        if (message.kind === "node.offline" || message.kind === "node.removed") {
          const workerId = (message.payload as { worker_id: string }).worker_id;
          setLive((prev) => {
            if (!prev) return prev;
            const nodes = prev.nodes.map((n) =>
              n.worker_id === workerId
                ? { ...n, status: message.kind === "node.offline" ? ("offline" as const) : ("removed" as const) }
                : n,
            );
            return recompute(prev, nodes);
          });
        }
        if (message.kind === "cluster.initialized" || message.kind === "snapshot") {
          void queryClient.invalidateQueries({ queryKey: ["overview"] });
        }
        if (message.kind.startsWith("experiment.")) {
          void queryClient.invalidateQueries({ queryKey: ["experiments"] });
        }
        if (message.kind === "job.updated" || message.kind === "job.completed") {
          void queryClient.invalidateQueries({ queryKey: ["jobs"] });
        }
      };

      socket.onclose = () => {
        setConnected(false);
        if (closed) return;
        retryRef.current = Math.min(retryRef.current + 1, 6);
        timer = window.setTimeout(connect, 500 * 2 ** retryRef.current);
      };

      socket.onerror = () => socket.close();
    };

    connect();

    return () => {
      closed = true;
      if (timer) window.clearTimeout(timer);
      socketRef.current?.close();
    };
  }, [queryClient]);

  return {
    overview: live ?? query.data ?? null,
    connected,
    feed,
    loading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  };
}
