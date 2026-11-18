"""Integrasi Firebase Realtime Database sebagai penyimpanan data pengunjung.

Menggantikan model Django `Visitor` (dulu SQLite lokal) agar data tersimpan
online. Konfigurasi lewat environment variables (lihat backend/.env.example):

- FIREBASE_SERVICE_ACCOUNT : path ke file JSON service account
                             (Firebase Console > Project settings >
                             Service accounts > Generate new private key).
                             Kosongkan untuk memakai kredensial default
                             (GOOGLE_APPLICATION_CREDENTIALS).
- FIREBASE_DATABASE_URL    : URL Realtime Database, mis.
                             https://<project-id>-default-rtdb.firebaseio.com
"""
import logging
import os
import threading
import time

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db as rtdb

logger = logging.getLogger(__name__)

# Node utama tempat semua catatan pengunjung disimpan
VISITORS_NODE = "visitors"

_init_lock = threading.Lock()
_app = None


class FirebaseNotConfigured(Exception):
    """Dilempar bila konfigurasi Firebase (env) belum lengkap."""


def _get_app():
    """Inisialisasi Firebase Admin SDK sekali saja (lazy & thread-safe)."""
    global _app
    if _app is not None:
        return _app

    with _init_lock:
        if _app is not None:
            return _app

        database_url = os.environ.get("FIREBASE_DATABASE_URL", "").strip()
        if not database_url:
            raise FirebaseNotConfigured(
                "FIREBASE_DATABASE_URL belum diisi di backend/.env "
                "(URL Firebase Realtime Database kamu)."
            )

        cred_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "").strip()
        cred = (
            credentials.Certificate(cred_path)
            if cred_path
            else credentials.ApplicationDefault()
        )

        _app = firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        return _app


def _visitors_ref():
    """Reference ke node `visitors` di Realtime Database."""
    return rtdb.reference(VISITORS_NODE, app=_get_app())


def save_visitor(ip, city, country, org, location):
    """Simpan satu catatan pengunjung. Return dict datanya (termasuk id)."""
    timestamp = int(time.time() * 1000)  # epoch milidetik (format frontend)
    data = {
        "ip": ip,
        "city": city,
        "country": country,
        "org": org,
        "location": location,
        # created_at dipakai sebagai kunci pengurutan (order_by_child)
        "created_at": timestamp,
    }

    ref = _visitors_ref().push(data)
    return {"id": ref.key, **data}


def get_recent_visitors(limit=200):
    """Ambil `limit` catatan pengunjung terbaru, terbaru lebih dulu."""
    try:
        snapshot = (
            _visitors_ref().order_by_child("created_at").limit_to_last(limit).get()
        )
    except rtdb.ApiCallError as exc:
        # Query order_by_child butuh ".indexOn": ["created_at"] pada rules.
        # Bila belum diatur, ambil semua lalu urutkan manual agar aplikasi
        # tetap jalan (dengan peringatan agar index segera ditambahkan).
        logger.warning(
            "Query Firebase gagal (%s); fallback ambil semua data. "
            'Tambahkan ".indexOn": ["created_at"] pada rules node visitors.',
            exc,
        )
        snapshot = _visitors_ref().get()

    visitors = [
        {
            "id": key,
            "ip": item.get("ip", ""),
            "city": item.get("city", ""),
            "country": item.get("country", ""),
            "org": item.get("org", ""),
            "location": item.get("location", ""),
            # epoch milidetik agar mudah diformat di frontend
            "timestamp": item.get("created_at"),
        }
        for key, item in (snapshot or {}).items()
        if isinstance(item, dict)
    ]

    visitors.sort(key=lambda v: v["timestamp"] or 0, reverse=True)
    return visitors[:limit]
