import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AlertTriangle, Cpu, HardDrive, Network, RotateCcw, Server, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { formatAgo, formatBytes } from "../lib/format";
import type { NodeInfo } from "../lib/types";
import { Panel, EmptyState } from "../components/Panel";
import { StatusPill } from "../components/StatusPill";
import { NodeCard } from "../components/NodeCard";

export function TopologyPage() {
  const { overview } = useCluster();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<NodeInfo | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["overview"] });

  const failureMutation = useMutation({
    mutationFn: api.simulateFailure,
    onSuccess: (node) => {
      setSelected(node);
      invalidate();
    },
  });
  const recoverMutation = useMutation({
    mutationFn: api.recoverNode,
    onSuccess: (node) => {
      setSelected(node);
      invalidate();
    },
  });
  const removeMutation = useMutation({
    mutationFn: api.removeNode,
    onSuccess: () => {
      setSelected(null);
      invalidate();
    },
  });

  const nodes = overview?.nodes ?? [];
  const master = nodes.find((node) => node.role === "master") ?? null;
  const workers = nodes.filter((node) => node.role === "worker");

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
      <Panel
        eyebrow="master → worker"
        title="Cluster Topology"
        actions={<span className="chip"><Network className="size-3" /> {workers.length} workers</span>}
        bodyClassName="p-6"
      >
        {!master && !workers.length ? (
          <EmptyState
            icon={<Network className="size-6" />}
            title="Topology kosong"
            body="Inisialisasi Master dan daftarkan Worker untuk melihat hubungan antar-node."
          />
        ) : (
          <div className="flex flex-col items-center">
            {master ? (
              <div className="w-full max-w-[280px]">
                <div className="mb-2 text-center font-mono text-[0.6rem] uppercase tracking-[0.2em] text-mist-500">
                  coordinator
                </div>
                <NodeCard node={master} onSelect={setSelected} selected={selected?.worker_id === master.worker_id} />
              </div>
            ) : null}

            <div className="h-7 w-px bg-ink-600" />
            {workers.length ? (
              <>
                <div className="relative h-px w-[86%] bg-ink-600">
                  <span className="absolute inset-y-0 left-0 w-px bg-ink-600" />
                  <span className="absolute inset-y-0 right-0 w-px bg-ink-600" />
                </div>
                <div className="grid w-full gap-3 pt-6 sm:grid-cols-2 lg:grid-cols-3">
                  {workers.map((node) => (
                    <div key={node.worker_id} className="relative">
                      <span className="absolute -top-6 left-1/2 h-6 w-px bg-ink-600" />
                      <NodeCard
                        node={node}
                        onSelect={setSelected}
                        selected={selected?.worker_id === node.worker_id}
                        compact
                      />
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="mt-4 font-mono text-[0.7rem] text-mist-500">
                belum ada worker terhubung ke master
              </div>
            )}
          </div>
        )}
      </Panel>

      <div className="flex flex-col gap-4">
        <Panel eyebrow="node inspector" title={selected ? selected.hostname : "Select a node"} bodyClassName="p-4">
          {selected ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <StatusPill status={selected.status} />
                <span className="chip">{selected.role}</span>
              </div>
              <dl className="space-y-1.5 font-mono text-[0.68rem]">
                <Row label="worker id" value={selected.worker_id} />
                <Row label="address" value={`${selected.ip_address}:${selected.port}`} />
                <Row label="os" value={selected.os_name} />
                <Row label="cpu cores" value={`${selected.cpu_cores}`} />
                <Row label="pool" value={`${selected.pool_size} processes`} />
                <Row label="memory" value={formatBytes(selected.memory_total)} />
                <Row label="heartbeat" value={formatAgo(selected.last_heartbeat)} />
                <Row label="inflight" value={`${selected.inflight}/${selected.capacity}`} />
                <Row label="completed" value={`${selected.completed_tasks}`} />
                <Row label="failed" value={`${selected.failed_tasks}`} />
                <Row label="child procs" value={`${selected.child_processes}`} />
              </dl>

              {selected.role === "worker" ? (
                <div className="flex flex-col gap-2 border-t border-ink-800 pt-3">
                  <button
                    className="btn"
                    onClick={() => failureMutation.mutate(selected.worker_id)}
                    disabled={failureMutation.isPending}
                  >
                    <AlertTriangle className="size-3.5 text-amber" /> simulate failure
                  </button>
                  <button
                    className="btn"
                    onClick={() => recoverMutation.mutate(selected.worker_id)}
                    disabled={recoverMutation.isPending}
                  >
                    <RotateCcw className="size-3.5 text-ice" /> recover worker
                  </button>
                  <button
                    className="btn"
                    onClick={() => removeMutation.mutate(selected.worker_id)}
                    disabled={removeMutation.isPending}
                  >
                    <Trash2 className="size-3.5 text-danger" /> remove from cluster
                  </button>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="font-mono text-[0.68rem] leading-relaxed text-mist-500">
              Klik salah satu kartu node untuk melihat IP, CPU, memory, process count, task, dan status
              koneksi.
            </p>
          )}
        </Panel>

        <Panel eyebrow="legend" title="Node states" bodyClassName="p-4">
          <div className="grid gap-2">
            {(
              [
                ["online", "heartbeat diterima, siap menerima task"],
                ["busy", "sedang mengeksekusi task crawling"],
                ["idle", "terhubung, tidak ada task aktif"],
                ["pending", "terdaftar, menunggu assignment operator"],
                ["offline", "heartbeat melewati threshold 15s"],
              ] as const
            ).map(([status, hint]) => (
              <div key={status} className="flex items-center gap-2">
                <StatusPill status={status} />
                <span className="font-mono text-[0.62rem] text-mist-500">{hint}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel eyebrow="hardware" title="Aggregate resources" bodyClassName="p-4">
          <div className="grid gap-2 font-mono text-[0.7rem]">
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-mist-500">
                <Cpu className="size-3.5" /> total cores
              </span>
              <span>{overview?.total_cpu_cores ?? 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-mist-500">
                <HardDrive className="size-3.5" /> total memory
              </span>
              <span>{formatBytes(overview?.total_memory ?? 0)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="inline-flex items-center gap-1.5 text-mist-500">
                <Server className="size-3.5" /> nodes
              </span>
              <span>{overview?.total_nodes ?? 0}</span>
            </div>
          </div>
        </Panel>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="shrink-0 text-mist-500">{label}</dt>
      <dd className="min-w-0 truncate text-right text-mist-200">{value}</dd>
    </div>
  );
}
