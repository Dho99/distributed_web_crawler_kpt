from __future__ import annotations

import ipaddress
import re
import socket
import sys

import psutil

# Interfaces created by hypervisors/VPNs are reachable only locally or tunnel
# over another network, so they should not be advertised as the cluster address.
VIRTUAL_IFACE = re.compile(
    r"vethernet|hyper-v|wsl|docker|virtualbox|vmware|loopback|tailscale|zerotier|"
    r"npcap|bluetooth|vpn|tun|tap",
    re.IGNORECASE,
)


def _is_usable(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    if addr.version != 4 or addr.is_loopback or addr.is_link_local or addr.is_multicast:
        return False
    if addr in ipaddress.ip_network("100.64.0.0/10"):
        return False
    return True


def _collect(include_virtual: bool) -> list[str]:
    candidates: list[str] = []
    for name, addrs in psutil.net_if_addrs().items():
        if not include_virtual and VIRTUAL_IFACE.search(name):
            continue
        for item in addrs:
            if item.family == socket.AF_INET and item.address:
                candidates.append(item.address)
    return candidates


def local_ip() -> str:
    """Best LAN address of this host, preferring real lab-class interfaces."""
    for include_virtual in (False, True):
        candidates = _collect(include_virtual)
        for prefix in ("192.168.", "10.", "172."):
            for ip in candidates:
                if ip.startswith(prefix) and _is_usable(ip):
                    return ip
        for ip in candidates:
            if _is_usable(ip):
                return ip

    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def disable_udp_connreset(sock: socket.socket) -> None:
    """Windows: ignore ICMP port-unreachable on a UDP socket.

    A single reply to an already-closed client port otherwise makes the next
    recvfrom fail with WSAECONNRESET, which asyncio treats as fatal and the
    listener goes silent for good. Python's socket.ioctl rejects this control
    code, so WSAIoctl is called directly. Best-effort on every other platform.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        ws2 = ctypes.WinDLL("ws2_32", use_last_error=True)
        disabled = wintypes.BOOL(False)
        returned = wintypes.DWORD(0)
        ws2.WSAIoctl(
            ctypes.c_size_t(sock.fileno()),
            0x9800000C,  # SIO_UDP_CONNRESET
            ctypes.byref(disabled),
            ctypes.sizeof(disabled),
            None,
            0,
            ctypes.byref(returned),
            None,
            None,
        )
    except Exception:  # noqa: BLE001 - hardening is optional
        pass
