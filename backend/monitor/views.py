import ipaddress
import os

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from . import firebase_db

GEO_API_URL = "https://ipapi.co/{ip}/json/"
GEO_TIMEOUT = 5  # detik

# Proxy yang dipercaya (default: jaringan lokal/privat). X-Forwarded-For hanya
# dipercaya bila koneksi TCP langsung datang dari salah satu jaringan ini,
# sehingga klien tidak bisa memalsukan IP-nya lewat header sembarang.
_TRUSTED_PROXY_NETWORKS = []
for _cidr in os.environ.get(
    "DJANGO_TRUSTED_PROXIES",
    "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16",
).split(","):
    try:
        _TRUSTED_PROXY_NETWORKS.append(ipaddress.ip_network(_cidr.strip()))
    except ValueError:
        continue  # CIDR tidak valid di env: lewati, jangan gagalkan startup


def _parse_ip(value):
    """Ubah string menjadi objek IP, atau None bila tidak valid."""
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def _is_trusted_proxy(ip):
    """True bila IP termasuk salah satu jaringan proxy terpercaya."""
    parsed = _parse_ip(ip)
    if parsed is None:
        return False
    return any(
        parsed.version == network.version and parsed in network
        for network in _TRUSTED_PROXY_NETWORKS
    )


def _get_client_ip(request):
    """Ambil IP klien.

    Hanya memercayai X-Forwarded-For / X-Real-IP bila koneksi langsung
    (REMOTE_ADDR) berasal dari proxy terpercaya, dan memakai entri paling
    kanan XFF — yang ditambahkan oleh proxy milik kita sendiri — sehingga
    tidak bisa dipalsukan oleh klien.
    """
    remote = request.META.get("REMOTE_ADDR", "").strip() or "127.0.0.1"

    if not _is_trusted_proxy(remote):
        return remote

    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        candidate = _parse_ip(forwarded.split(",")[-1].strip())
        if candidate is not None:
            return str(candidate)

    candidate = _parse_ip(request.META.get("HTTP_X_REAL_IP", "").strip())
    if candidate is not None:
        return str(candidate)

    return remote


def _is_public_ip(ip):
    """True jika IP valid dan bukan alamat lokal/privat."""
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (parsed.is_private or parsed.is_loopback or parsed.is_unspecified)


def _lookup_geo(ip):
    """Ambil info geolokasi dari ipapi.co. Return (city, country, org)."""
    try:
        res = requests.get(GEO_API_URL.format(ip=ip), timeout=GEO_TIMEOUT)
        data = res.json()
    except (requests.RequestException, ValueError):
        return "", "", ""

    if not res.ok or data.get("error"):
        return "", "", ""

    return (
        data.get("city") or "",
        data.get("country_name") or "",
        data.get("org") or "",
    )


@csrf_exempt
@require_http_methods(["POST"])
def record_visitor(request):
    """Catat pengunjung baru: simpan IP + info geolokasi, lalu kembalikan datanya."""
    ip = _get_client_ip(request)

    if _is_public_ip(ip):
        city, country, org = _lookup_geo(ip)
    else:
        # IP lokal (mis. 127.0.0.1 saat development): tanpa info geolokasi
        city, country, org = "", "", ""

    try:
        visitor = firebase_db.save_visitor(
            ip=ip,
            city=city,
            country=country,
            org=org,
            location=f"{city}, {country}" if city and country else "",
        )
    except firebase_db.FirebaseNotConfigured as exc:
        return JsonResponse({"error": str(exc)}, status=503)

    return JsonResponse(
        {
            "ip": visitor["ip"],
            "city": visitor["city"],
            "country": visitor["country"],
            "org": visitor["org"],
        }
    )


@require_http_methods(["GET"])
def list_visitors(request):
    """Daftar seluruh pengunjung (terbaru dulu) untuk halaman admin."""
    try:
        data = firebase_db.get_recent_visitors(limit=200)
    except firebase_db.FirebaseNotConfigured as exc:
        return JsonResponse({"error": str(exc)}, status=503)

    # `timestamp` sudah berupa epoch milidetik agar mudah diformat di frontend
    return JsonResponse(data, safe=False)
