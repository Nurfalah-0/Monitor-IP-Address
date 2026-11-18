'use client';
import { useEffect, useState } from 'react';

// URL backend Django (dijalankan di http://localhost:8000)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [info, setInfo] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const STORAGE_KEY = 'ip-monitor-recorded';

    // Catat pengunjung maksimal satu kali per sesi tab: mencegah catatan
    // dobel dari React StrictMode (development) maupun refresh halaman.
    if (sessionStorage.getItem(STORAGE_KEY)) return;
    sessionStorage.setItem(STORAGE_KEY, '1');

    fetch(`${API_URL}/api/visitor/`, { method: 'POST' })
      .then((r) => r.json())
      .then((data) => {
        if (data.error) throw new Error(data.error);
        setInfo(data);
      })
      .catch((e) => {
        // Gagal mencatat: hapus tanda agar sesi berikutnya bisa mencoba lagi.
        sessionStorage.removeItem(STORAGE_KEY);
        setError(e.message);
      });
  }, []);

  return (
    <main style={{ fontFamily: 'Arial, sans-serif', maxWidth: 600, margin: '0 auto', padding: 20 }}>
      <h1>Info Pengunjung</h1>
      {!info && !error && <p>Memuat informasi...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {info && (
        <div style={{ background: '#f4f4f4', padding: 20, borderRadius: 5 }}>
          <p><strong>IP:</strong> {info.ip}</p>
          <p><strong>Lokasi:</strong> {info.city || info.country ? `${info.city}, ${info.country}` : 'Tidak diketahui'}</p>
          <p><strong>ISP:</strong> {info.org || 'Tidak diketahui'}</p>
          <p><small>Data ini disimpan untuk keperluan administrasi</small></p>
        </div>
      )}
    </main>
  );
}
