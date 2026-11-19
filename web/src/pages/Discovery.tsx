import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Cpu, HardDrive, Loader2, Plus, Radar, ShieldCheck, Trash2, Wifi, Zap } from "lucide-react";
import { api } from "../lib/api";
import { useCluster } from "../lib/cluster-context";
import { formatBytes } from "../lib/format";
import type { DiscoveredNode, DiscoverResponse } from "../lib/types";
import { Panel, EmptyState } from "../components/Panel";
import { StatusPill } from "../components/StatusPill";

export function DiscoveryPage() {
  const { overview } = useCluster();
  const queryClient = useQueryClient();
  const [scan, setScan] = useState<DiscoverResponse | null>(null);
  const [ip, setIp] = useState("");
  const [port, setPort] = useState("8010");
  const [notice, setNotice] = useState<string | null>(null);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["overview"] });

  const scanMutation = useMutation({
    mutationFn: api.discover,
    onSuccess: (data) => {
      setScan(data);
      setNotice(null);
    },
  });

  const assignMutation = useMutation({
    mutationFn: (workerId: string) => api.assignNode(workerId),
    onSuccess: (node) => {
      setNotice(`Worker ${node.hostname} aktif dan menerima task.`);
      invalidate();
    },
  });

  const manualMutation = useMutation({
    mutationFn: () => api.addManual(ip.trim(), Number(port) || 8010),
    onSuccess: (node) => {
      setNotice(`Node ${node.hostname} (${node.ip_address}) ditambahkan manual. Tekan ASSIGN untuk mengaktifkan.`);
      invalidate();
      setIp("");
    },
  });

  const removeMutation = useMutation({
    mutationFn: (workerId: string) => api.removeNode(workerId),
    onSuccess: () => invalidate(),
  });

  const workers = (overview?.nodes ?? []).filter((node) => node.role === "worker");
  const statusById = new Map(workers.map((node) => [node.worker_id, node.status]));
  const discovered = (scan?.found ?? []).filter((node) => {
    const status = statusById.get(node.worker_id);
    return !status || status === "discovered";
  });

  return (
    <div className="space-y-4">
      <Panel
        eyebrow="local network · udp broadcast"
        title="Discover Worker Agent"
        actions={
          <button
            className="btn btn-primary"
            onClick={() => scanMutation.mutate()}
            disabled={scanMutation.isPending}
          >
            {scanMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : <Radar className="size-3.5" />}
            {scanMutation.isPending ? "scanning…" : "scan network"}
          </button>
        }
        bodyClassName="p-0"
      >
        <div className="relative overflow-hidden border-b border-ink-800 px-4 py-3">
          {scanMutation.isPending ? <div className="scan-sweep pointer-events-none absolute inset-0" /> : null}
          <p className="relative font-mono text-[0.68rem] leading-relaxed text-mist-500">
            Master mengirim probe UDP ke port <span className="text-mist-300">5599</span> dan menunggu
            balasan agent selama <span className="text-mist-300">{scan?.scanned_ms ?? 2500} ms</span>.
            Worker yang berbeda subnet dapat ditambahkan manual di bawah.
          </p>
        </div>

        <div className="p-4">
          {!scan && !scanMutation.isPending ? (
            <EmptyState
              icon={<Radar className="size-6" />}
              title="Belum ada hasil scan"
              body="Jalankan scan untuk menemukan agent yang aktif di LAN. Pastikan Worker Agent sudah berjalan dengan token cluster yang sama."
            />
          ) : null}

          {scanMutation.isPending ? (
            <div className="flex items-center gap-2 font-mono text-[0.7rem] text-mist-400">
              <Loader2 className="size-4 animate-spin text-signal" /> probing broadcast address…
            </div>
          ) : null}

          {scan && !scanMutation.isPending ? (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {discovered.length ? (
                discovered.map((node) => (
                  <DiscoveredCard
                    key={node.worker_id}
                    node={node}
                    busy={assignMutation.isPending}
                    onAssign={() => assignMutation.mutate(node.worker_id)}
                  />
                ))
              ) : (
                <div className="md:col-span-2 xl:col-span-3">
                  <EmptyState
                    icon={<Wifi className="size-6" />}
                    title="Tidak ada agent baru"
                    body={`${scan.found.length} agent merespons, ${scan.already_known.length} sudah terdaftar di cluster.`}
                  />
                </div>
              )}
            </div>
          ) : null}

          {scanMutation.error ? (
            <div className="mt-3 rounded border border-[#4d2525] bg-[#1c0d0d] px-3 py-2 font-mono text-[0.68rem] text-[#ffb3b3]">
              {String((scanMutation.error as Error).message)}
            </div>
          ) : null}
        </div>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.5fr)]">
        <Panel eyebrow="fallback" title="Add worker by IP" bodyClassName="p-4">
          <form
            className="space-y-3"
            onSubmit={(event) => {
              event.preventDefault();
              if (ip.trim()) manualMutation.mutate();
            }}
          >
            <label className="block space-y-1.5">
              <span className="eyebrow">agent ip address</span>
              <input
                className="field"
                placeholder="192.168.18.142"
                value={ip}
                onChange={(event) => setIp(event.target.value)}
                inputMode="decimal"
              />
            </label>
            <label className="block space-y-1.5">
              <span className="eyebrow">agent port</span>
              <input
                className="field"
                value={port}
                onChange={(event) => setPort(event.target.value)}
                inputMode="numeric"
              />
            </label>
            <button className="btn w-full" type="submit" disabled={!ip.trim() || manualMutation.isPending}>
              {manualMutation.isPending ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
              probe &amp; register
            </button>
            <p className="font-mono text-[0.62rem] leading-relaxed text-mist-500">
              Berguna lintas subnet. Master memanggil <span className="text-mist-300">/agent/info</span>{" "}
              dengan pairing token, lalu node masuk status <span className="text-mist-300">pending</span>{" "}
              sampai di-assign.
            </p>
            {manualMutation.error ? (
              <div className="rounded border border-[#4d2525] bg-[#1c0d0d] px-3 py-2 font-mono text-[0.66rem] text-[#ffb3b3]">
                {String((manualMutation.error as Error).message)}
              </div>
            ) : null}
          </form>
        </Panel>

        <Panel
          eyebrow={`${workers.length} registered`}
          title="Enrolled workers"
          bodyClassName="p-0"
        >
          <div className="divide-y divide-ink-800">
            {workers.length ? (
              workers.map((node) => (
                <div key={node.worker_id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-mono text-[0.78rem] text-mist-100">{node.hostname}</span>
                      <StatusPill status={node.status} />
                    </div>
                    <div className="mt-0.5 font-mono text-[0.62rem] text-mist-500">
                      {node.ip_address}:{node.port} · pool {node.pool_size} · {node.cpu_cores} cores
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {["pending", "offline", "discovered"].includes(node.status) ? (
                      <button
                        className="btn btn-primary"
                        onClick={() => assignMutation.mutate(node.worker_id)}
                        disabled={assignMutation.isPending}
                      >
                        <Zap className="size-3.5" /> assign
                      </button>
                    ) : (
                      <span className="chip border-[#3c5220] bg-[#141f0c] text-[#cdf98a]">
                        <ShieldCheck className="size-3" /> worker active
                      </span>
                    )}
                    <button
                      className="btn btn-ghost"
                      title="Remove worker from cluster"
                      onClick={() => removeMutation.mutate(node.worker_id)}
                      disabled={removeMutation.isPending}
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-4 py-8 text-center font-mono text-[0.68rem] text-mist-500">
                belum ada worker terdaftar
              </div>
            )}
          </div>
        </Panel>
      </div>

      {notice ? (
        <div className="panel border-signal/30 bg-[#0f1709] px-4 py-2.5 font-mono text-[0.68rem] text-[#cdf98a]">
          {notice}
        </div>
      ) : null}
    </div>
  );
}

function DiscoveredCard({
  node,
  onAssign,
  busy,
}: {
  node: DiscoveredNode;
  onAssign: () => void;
  busy: boolean;
}) {
  return (
    <div className="panel flex flex-col gap-3 border-ink-700 px-4 py-3.5">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate font-mono text-[0.8rem] font-semibold text-mist-100">{node.hostname}</div>
          <div className="mt-0.5 font-mono text-[0.64rem] text-mist-500">
            {node.ip_address}:{node.port}
          </div>
        </div>
        <span className="chip border-[#1d4450] bg-[#0b1a1f] text-[#a9eef5]">available</span>
      </div>
      <div className="grid grid-cols-2 gap-2 font-mono text-[0.66rem] text-mist-400">
        <span className="inline-flex items-center gap-1.5">
          <Cpu className="size-3.5 text-mist-500" /> {node.cpu_cores} cores
        </span>
        <span className="inline-flex items-center gap-1.5">
          <HardDrive className="size-3.5 text-mist-500" /> {formatBytes(node.memory_total)}
        </span>
      </div>
      <div className="font-mono text-[0.6rem] text-mist-500">
        {node.os_name} · agent v{node.agent_version}
      </div>
      <button className="btn btn-primary mt-auto w-full" onClick={onAssign} disabled={busy}>
        <Zap className="size-3.5" /> assign as worker
      </button>
    </div>
  );
}
