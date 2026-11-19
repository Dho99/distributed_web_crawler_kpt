import { useState } from "react";
import { Check, Copy, Eye, EyeOff, KeyRound, ScrollText, TerminalSquare } from "lucide-react";
import { Panel } from "../components/Panel";
import { PhaseGate } from "../components/PhaseGate";
import { useCluster } from "../lib/cluster-context";
import { formatClock, maskToken } from "../lib/format";

const CONFIG = [
  ["heartbeat interval", "5 s"],
  ["offline threshold", "15 s"],
  ["task retry limit", "3 ×"],
  ["discovery probe port", "5599 / udp"],
  ["master http port", "8000 / tcp"],
  ["task lease grace", "request_timeout × batch + 60 s"],
  ["result dedupe key", "(job_id, url_hash)"],
];

export function SettingsPage() {
  const { overview } = useCluster();
  const cluster = overview?.cluster ?? null;
  const [revealed, setRevealed] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [shell, setShell] = useState<"windows" | "linux">("windows");

  const copy = async (label: string, value: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(label);
      window.setTimeout(() => setCopied(null), 1500);
    } catch {
      setCopied(null);
    }
  };

  const token = cluster?.pairing_token ?? "";
  const masterUrl = cluster?.master_url ?? "http://<master-ip>:8000";
  const command =
    shell === "windows"
      ? `.\\.venv\\Scripts\\python.exe -m worker.agent \`
  --master ${masterUrl} \`
  --token=${revealed ? token : "<pairing-token>"} \`
  --port 8010 \`
  --pool-size 4`
      : `python -m worker.agent \\
  --master ${masterUrl} \\
  --token=${revealed ? token : "<pairing-token>"} \\
  --port 8010 \\
  --pool-size 4`;

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <div className="flex flex-col gap-4">
        <Panel
          eyebrow="cluster identity"
          title={cluster?.name ?? "Belum diinisialisasi"}
          actions={
            cluster ? (
              <span className="chip border-[#3c5220] bg-[#141f0c] text-[#cdf98a]">active</span>
            ) : null
          }
          bodyClassName="p-4"
        >
          <dl className="space-y-2 font-mono text-[0.7rem]">
            <Row label="cluster id" value={cluster?.cluster_id ?? "—"} />
            <Row label="master url" value={masterUrl} />
            <Row label="created" value={cluster ? formatClock(cluster.created_at) : "—"} />
            <Row label="discovery port" value={String(cluster?.discovery_port ?? 5599)} />
          </dl>

          <div className="mt-4 rounded-lg border border-ink-700 bg-ink-900 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="eyebrow inline-flex items-center gap-1.5">
                <KeyRound className="size-3" /> pairing token
              </span>
              <div className="flex items-center gap-1.5">
                <button className="btn btn-ghost !px-2 !py-1" onClick={() => setRevealed((v) => !v)}>
                  {revealed ? <EyeOff className="size-3.5" /> : <Eye className="size-3.5" />}
                </button>
                <button
                  className="btn btn-ghost !px-2 !py-1"
                  onClick={() => copy("token", token)}
                  disabled={!token}
                >
                  {copied === "token" ? <Check className="size-3.5 text-signal" /> : <Copy className="size-3.5" />}
                </button>
              </div>
            </div>
            <div className="mt-1.5 break-all font-mono text-[0.72rem] text-mist-200">
              {token ? (revealed ? token : maskToken(token)) : "token tersedia setelah master diinisialisasi"}
            </div>
          </div>
        </Panel>

        <Panel eyebrow="runtime config" title="Cluster parameters" bodyClassName="p-0">
          <dl className="divide-y divide-ink-800">
            {CONFIG.map(([label, value]) => (
              <div key={label} className="flex items-center justify-between gap-4 px-4 py-2.5">
                <dt className="font-mono text-[0.68rem] text-mist-500">{label}</dt>
                <dd className="font-mono text-[0.68rem] text-mist-200">{value}</dd>
              </div>
            ))}
          </dl>
        </Panel>

        <Panel eyebrow="safety" title="Crawler guardrails" bodyClassName="p-4">
          <ul className="space-y-1.5 font-mono text-[0.66rem] text-mist-400">
            <li>• private / loopback / link-local target diblokir secara default</li>
            <li>• robots.txt dihormati, domain delay diterapkan per host</li>
            <li>• token cluster wajib pada semua endpoint worker→master</li>
            <li>• tidak ada bypass CAPTCHA / autentikasi pihak ketiga</li>
          </ul>
        </Panel>
      </div>

      <div className="flex flex-col gap-4">
        <Panel
          eyebrow="worker onboarding"
          title="Agent command"
          actions={
            <div className="flex gap-1">
              <button
                className={shell === "windows" ? "btn !px-2 !py-1 !border-signal-dim !text-signal" : "btn btn-ghost !px-2 !py-1"}
                onClick={() => setShell("windows")}
              >
                windows
              </button>
              <button
                className={shell === "linux" ? "btn !px-2 !py-1 !border-signal-dim !text-signal" : "btn btn-ghost !px-2 !py-1"}
                onClick={() => setShell("linux")}
              >
                linux
              </button>
            </div>
          }
          bodyClassName="p-4"
        >
          <div className="flex items-start gap-2">
            <TerminalSquare className="mt-1 size-4 shrink-0 text-ice" />
            <pre className="min-w-0 flex-1 overflow-x-auto rounded border border-ink-700 bg-ink-900 p-3 font-mono text-[0.66rem] leading-relaxed text-mist-300">
{command}
            </pre>
            <button className="btn btn-ghost !px-2 !py-1" onClick={() => copy("cmd", command)}>
              {copied === "cmd" ? <Check className="size-3.5 text-signal" /> : <Copy className="size-3.5" />}
            </button>
          </div>
          <p className="mt-2 font-mono text-[0.62rem] leading-relaxed text-mist-500">
            Agent hanya membuka koneksi keluar ke master dan satu port HTTP untuk onboarding. Setelah
            terdaftar, worker muncul di Discovery dengan status <span className="text-mist-300">pending</span>{" "}
            sampai di-assign.
          </p>
        </Panel>

        <Panel eyebrow="deployment" title="Service installation" bodyClassName="p-4">
          <div className="space-y-2 font-mono text-[0.66rem] leading-relaxed text-mist-400">
            <p>
              <span className="text-mist-200">Windows</span> — jalankan{" "}
              <span className="text-ice">scripts/install_agent_windows.ps1</span> sebagai Administrator.
              Task Scheduler akan menjalankan agent saat boot dan restart otomatis saat gagal.
            </p>
            <p>
              <span className="text-mist-200">Linux</span> — jalankan{" "}
              <span className="text-ice">scripts/install_agent_linux.sh</span> untuk memasang unit systemd{" "}
              <span className="text-mist-300">crawlmesh-agent.service</span>.
            </p>
            <p className="text-mist-500">
              Token disimpan pada file konfigurasi agent; jangan commit ke repository.
            </p>
          </div>
        </Panel>

        <PhaseGate phase="phase 1+" title="Node onboarding checklist" acceptance="AC-02 · AC-04">
          Target UAS: 9 Worker terdaftar. Saat ini{" "}
          <span className="text-mist-200">{overview?.active_workers ?? 0}</span> worker aktif dari{" "}
          <span className="text-mist-200">{overview?.total_nodes ?? 0}</span> node.
        </PhaseGate>

        <Panel eyebrow="audit" title="Data locations" bodyClassName="p-4">
          <dl className="space-y-2 font-mono text-[0.68rem]">
            <Row label="database" value="data/crawlmesh.db (SQLite WAL)" />
            <Row label="exports" value="data/exports/" />
            <Row label="agent state" value=".crawlmesh-agent/worker-id" />
          </dl>
          <div className="mt-2 inline-flex items-center gap-1.5 font-mono text-[0.62rem] text-mist-500">
            <ScrollText className="size-3" /> semua timestamp disimpan UTC ISO-8601
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
      <dd className="min-w-0 break-all text-right text-mist-200">{value}</dd>
    </div>
  );
}
