'use client';
import { useEffect, useState } from 'react';

// URL backend Django (dijalankan di http://localhost:8000)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
// Interval auto-refresh (ms) sebagai pengganti realtime listener Firebase
const REFRESH_INTERVAL = 15000;

const formatDate = (ts) => {
  if (!ts) return 'Waktu tidak diketahui';
  return new Date(ts).toLocaleString('id-ID', {
    weekday: 'long', day: 'numeric', month: 'long',
    year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
};

export default function AdminPage() {
  const [visitors, setVisitors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const load = () =>
      fetch(`${API_URL}/api/visitors/`)
        .then((r) => {
          if (!r.ok) throw new Error('Gagal mengambil data pengunjung');
          return r.json();
        })
        .then((data) => {
          if (!active) return;
          setLoading(false);
          setError('');
          setVisitors(Array.isArray(data) ? data : []);
        })
        .catch((e) => {
          if (!active) return;
          setLoading(false);
          setError(e.message);
        });

    load();
    const interval = setInterval(load, REFRESH_INTERVAL);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <main style={{ fontFamily: 'Arial, sans-serif', margin: 0, padding: 20, background: '#f5f5f5', minHeight: '100vh' }}>
      <h1 style={{ color: '#333', borderBottom: '2px solid #333', paddingBottom: 10 }}>Data Pengunjung</h1>
      {loading && <div style={{ background: '#f39c12', color: 'white', padding: 10, borderRadius: 4 }}>Memuat data pengunjung...</div>}
      {error && <div style={{ background: '#e74c3c', color: 'white', padding: 10, borderRadius: 4 }}>Error: {error}</div>}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 15, marginTop: 20 }}>
        {visitors.length === 0 && !loading && <p>Tidak ada data pengunjung</p>}
        {visitors.map((entry) => (
          <div key={entry.id} style={{ background: 'white', padding: 15, borderRadius: 8, boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
            <div style={{ fontWeight: 'bold', color: '#2c3e50', fontSize: '1.1em' }}>IP: {entry.ip || 'Tidak diketahui'}</div>
            <div style={{ color: '#16a085' }}>Lokasi: {entry.location || [entry.city, entry.country].filter(Boolean).join(', ') || 'Tidak diketahui'}</div>
            <div style={{ color: '#7f8c8d' }}>ISP: {entry.org || 'Tidak diketahui'}</div>
            <div style={{ fontSize: '0.8em', color: '#95a5a6', marginTop: 10 }}>{formatDate(entry.timestamp)}</div>
          </div>
        ))}
      </div>
    </main>
  );
}
