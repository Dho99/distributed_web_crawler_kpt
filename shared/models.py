from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NodeRole(str, Enum):
    MASTER = "master"
    WORKER = "worker"


class NodeStatus(str, Enum):
    # Role lifecycle: agent is up but not assigned by an operator yet.
    DISCOVERED = "discovered"
    PENDING = "pending"
    ONLINE = "online"
    BUSY = "busy"
    IDLE = "idle"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    REMOVED = "removed"


class SchedulingMode(str, Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    LEASED = "leased"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"
    CANCELLED = "cancelled"


class ExperimentType(str, Enum):
    SEQUENTIAL = "sequential"
    LOCAL_PARALLEL = "local_parallel"
    DISTRIBUTED = "distributed"
    SCALABILITY = "scalability"
    LOAD_BALANCING = "load_balancing"
    FAULT_TOLERANCE = "fault_tolerance"


# --------------------------------------------------------------------------
# Cluster / nodes
# --------------------------------------------------------------------------


class ClusterInfo(BaseModel):
    cluster_id: str
    name: str
    pairing_token: str
    master_url: str
    created_at: datetime
    discovery_port: int = 5599


class DiscoveredNode(BaseModel):
    worker_id: str
    hostname: str
    ip_address: str
    port: int
    cpu_cores: int
    memory_total: int
    os_name: str
    python_version: str = ""
    agent_version: str = "0.1.0"
    cluster_id: str | None = None
    reachable: bool = True
    already_known: bool = False


class NodeOut(BaseModel):
    worker_id: str
    hostname: str
    ip_address: str
    port: int
    role: NodeRole
    status: NodeStatus
    cpu_cores: int
    memory_total: int
    os_name: str
    python_version: str
    pool_size: int
    agent_version: str
    last_heartbeat: datetime | None = None
    registered_at: datetime | None = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    child_processes: int = 0
    inflight: int = 0
    capacity: int = 0
    throughput: float = 0.0


# --------------------------------------------------------------------------
# Worker registration / heartbeat
# --------------------------------------------------------------------------


class WorkerMetrics(BaseModel):
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_used: int = 0
    active_processes: int = 0
    child_processes: int = 0
    active_tasks: int = 0
    pending_tasks: int = 0
    inflight: int = 0
    capacity: int = 1
    throughput: float = 0.0
    avg_processing_ms: float = 0.0


class RegisterRequest(BaseModel):
    worker_id: str | None = None
    hostname: str
    ip_address: str = ""
    port: int = 8010
    cpu_cores: int = 1
    memory_total: int = 0
    os_name: str = ""
    python_version: str = ""
    agent_version: str = "0.1.0"
    pool_size: int = 1
    capacity: int = 1
    cluster_id: str | None = None


class RegisterResponse(BaseModel):
    worker_id: str
    cluster_id: str
    status: NodeStatus
    accepted: bool
    heartbeat_interval: int = 5
    offline_threshold: int = 15
    message: str = ""


class WorkerControl(BaseModel):
    pause_all: bool = False
    paused_job_ids: list[str] = Field(default_factory=list)
    cancelled_job_ids: list[str] = Field(default_factory=list)
    server_time: datetime = Field(default_factory=utcnow)


class HeartbeatRequest(BaseModel):
    worker_id: str
    metrics: WorkerMetrics = Field(default_factory=WorkerMetrics)
    status: str = "idle"
    current_job_ids: list[str] = Field(default_factory=list)


class HeartbeatResponse(BaseModel):
    acknowledged: bool = True
    assigned: bool = False
    status: NodeStatus = NodeStatus.PENDING
    control: WorkerControl = Field(default_factory=WorkerControl)
    message: str = ""


# --------------------------------------------------------------------------
# Task leasing
# --------------------------------------------------------------------------


class LeaseRequest(BaseModel):
    worker_id: str
    free_slots: int = 1


class LeaseTask(BaseModel):
    task_id: str
    job_id: str
    urls: list[str]
    depth: int
    attempt: int = 1
    request_timeout: float = 15.0
    domain_delay: float = 0.5
    respect_robots: bool = True
    user_agent: str = "CrawlMesh/0.1"
    max_links_per_page: int = 50
    allow_private_targets: bool = False


class LeaseResponse(BaseModel):
    tasks: list[LeaseTask] = Field(default_factory=list)
    control: WorkerControl = Field(default_factory=WorkerControl)


class LinkRef(BaseModel):
    url: str
    depth: int


class CrawlResultItem(BaseModel):
    url: str
    final_url: str = ""
    http_status: int = 0
    title: str = ""
    extracted_text: str = ""
    links: list[str] = Field(default_factory=list)
    content_hash: str = ""
    response_time_ms: float = 0.0
    size_bytes: int = 0
    content_type: str = ""
    error: str | None = None


class TaskResultRequest(BaseModel):
    worker_id: str
    results: list[CrawlResultItem] = Field(default_factory=list)
    links: list[LinkRef] = Field(default_factory=list)
    processing_ms: float = 0.0


class TaskResultResponse(BaseModel):
    accepted: int = 0
    duplicates: int = 0
    failed: int = 0
    links_accepted: int = 0
    job_completed: bool = False


class TaskFailRequest(BaseModel):
    worker_id: str
    error: str = ""
    retriable: bool = True


class TaskFailResponse(BaseModel):
    requeued: bool = False
    attempt: int = 0


# --------------------------------------------------------------------------
# Crawl jobs
# --------------------------------------------------------------------------


class CrawlJobConfig(BaseModel):
    job_name: str = Field(min_length=1, max_length=120)
    seed_urls: list[str] = Field(min_length=1)
    allowed_domains: list[str] = Field(default_factory=list)
    maximum_pages: int = Field(default=100, ge=1, le=1_000_000)
    maximum_depth: int = Field(default=3, ge=0, le=50)
    batch_size: int = Field(default=10, ge=1, le=1000)
    request_timeout: float = Field(default=15.0, gt=0, le=120)
    domain_delay: float = Field(default=0.5, ge=0, le=60)
    respect_robots: bool = True
    user_agent: str = "CrawlMesh/0.1 (+academic-project)"
    scheduling_mode: SchedulingMode = SchedulingMode.DYNAMIC
    include_subdomains: bool = False
    allow_private_targets: bool = False


class CrawlJobOut(BaseModel):
    job_id: str
    job_name: str
    seed_urls: list[str]
    allowed_domains: list[str]
    maximum_pages: int
    maximum_depth: int
    batch_size: int
    request_timeout: float
    domain_delay: float
    respect_robots: bool
    scheduling_mode: SchedulingMode
    status: JobStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    pages_crawled: int = 0
    pages_failed: int = 0
    pages_pending: int = 0
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    throughput: float = 0.0


class OverviewOut(BaseModel):
    cluster: ClusterInfo | None = None
    total_nodes: int
    active_workers: int
    offline_workers: int
    total_cpu_cores: int
    total_memory: int
    running_jobs: int
    pages_crawled: int
    failed_tasks: int
    current_throughput: float
    nodes: list[NodeOut] = Field(default_factory=list)
