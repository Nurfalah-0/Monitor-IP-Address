# Monitor-IP-Address

Aplikasi untuk mencatat & memantau IP address pengunjung, dibangun dengan arsitektur **React frontend + Django backend** dan penyimpanan data online via **Firebase Realtime Database**.

## 🏗️ Arsitektur

```text
┌──────────────────────┐   HTTP/JSON    ┌──────────────────────┐ firebase-admin ┌───────────────────────────┐
│  React (Next.js)     │ ─────────────▶ │  Django REST API     │ ─────────────▶ │ Firebase Realtime         │
│  monitor-ip/         │  CORS          │  backend/            │                │ Database (online/cloud)   │
│  localhost:3000      │ ◀───────────── │  localhost:8000      │                │                           │
└──────────────────────┘                └──────────────────────┘                └───────────────────────────┘
```

| Bagian | Teknologi | Lokasi |
| :--- | :--- | :--- |
| 🎨 **Frontend** | React 19 + Next.js 16 | [`monitor-ip/`](./monitor-ip) |
| 🐍 **Backend** | Django 5.2 + django-cors-headers + requests | [`backend/`](./backend) |
| 💾 **Database** | Firebase Realtime Database (online) | [Firebase Console](https://console.firebase.google.com/) |

## 📌 Fitur

- 🌐 **Pencatatan Pengunjung** — setiap kunjungan halaman utama mencatat IP, kota, negara, dan ISP (geolokasi via [ipapi.co](https://ipapi.co/)).
- 🛡️ **Halaman Admin** — daftar data pengunjung lengkap dengan lokasi & waktu, auto-refresh tiap 15 detik.
- 🔁 **Mendukung Proxy** — membaca `X-Forwarded-For` / `X-Real-IP` saat di-deploy di balik reverse proxy.
- 🧠 **Tahan Gangguan** — jika API geolokasi gagal, IP tetap tercatat tanpa menggagalkan halaman.
- 🔥 **Data Online** — data pengunjung tersimpan di Firebase Realtime Database, bukan database lokal.

## 🔥 Setup Firebase (wajib, sekali saja)

Data pengunjung disimpan di **Firebase Realtime Database**:

1. Buat project di [Firebase Console](https://console.firebase.google.com/), lalu buat **Realtime Database** (mode *locked*). Catat URL-nya, mis. `https://nama-project-default-rtdb.firebaseio.com`.
2. **Project settings → Service accounts → Python → Generate new private key**, simpan file JSON-nya sebagai `backend/serviceAccountKey.json`. File ini rahasia — sudah masuk `.gitignore`, jangan pernah di-commit.
3. Salin `backend/.env.example` menjadi `backend/.env`, lalu isi:

   ```env
   FIREBASE_SERVICE_ACCOUNT=serviceAccountKey.json
   FIREBASE_DATABASE_URL=https://nama-project-default-rtdb.firebaseio.com
   ```

4. Di **Realtime Database → Rules**, tambahkan index agar query urutan waktu efisien:

   ```json
   {
     "rules": {
       ".read": false,
       ".write": false,
       "visitors": {
         ".indexOn": ["created_at"]
       }
     }
   }
   ```

> Backend memakai **Admin SDK** (kredensial service account), jadi baca/tulis tidak bergantung pada rules publik — rules boleh tetap tertutup penuh. Yang penting hanya bagian `.indexOn`; tanpa itu aplikasi masih jalan (fallback ambil-semua + urut manual), hanya saja kurang efisien.

## 🗺️ API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Fungsi |
| :--- | :--- | :--- |
| `POST` | `/api/visitor/` | Catat kunjungan baru, kembalikan info IP pengunjung |
| `GET` | `/api/visitors/` | Daftar data pengunjung (maks. 200 terbaru) |
| `GET` | `/admin/` | Panel admin Django (kelola data langsung) |

## 🚀 Cara Menjalankan

### Deploy frontend ke Netlify

Deploy melalui repositori Git agar Netlify memasang dependensi dan membangun Next.js. Konfigurasi di `netlify.toml` menetapkan folder aplikasi `monitor-ip`, perintah `npm ci && npm run build`, dan folder hasil build `.next`. Langkah `npm ci` memasang dependensi sesuai lockfile sebelum build, termasuk saat deploy melalui CLI yang belum memasang dependensi aplikasi. Adapter Next.js Netlify menangani halaman dan routing secara otomatis.

Mengunggah folder kode sumber melalui drag-and-drop tidak menjalankan build Next.js dan dapat menghasilkan halaman **Page not found**. Setelah perubahan didorong ke branch `main`, periksa bahwa deploy terbaru berhasil, lalu buka URL situs atau `/admin`.

Konfigurasi ini men-deploy frontend. Backend Django di `backend/` tidak otomatis ikut berjalan. Agar fitur pencatatan dan daftar pengunjung berfungsi online, `NEXT_PUBLIC_API_URL` harus menunjuk ke URL backend HTTPS yang aktif sebelum frontend dibangun. Nilai bawaan `http://localhost:8000` hanya cocok untuk pengembangan lokal. Jika URL API berubah, lakukan deploy ulang.

### 1️⃣ Backend Django (port 8000)

```powershell
# Buat & aktifkan virtual environment (sekali saja)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r .\backend\requirements.txt

# Migrasi database lokal Django (hanya untuk tabel internal admin/session)
python .\backend\manage.py migrate

# Jalankan server
python .\backend\manage.py runserver
```

> 💾 SQLite lokal (`db.sqlite3`) kini hanya dipakai untuk tabel internal Django (admin/session). Seluruh data pengunjung tersimpan di Firebase Realtime Database — pastikan langkah **Setup Firebase** di atas sudah dilakukan.

### 2️⃣ Frontend React (port 3000)

```powershell
cd .\monitor-ip

# Install dependencies (sekali saja)
npm install

# Jalankan dev server
npm run dev
```

Buka:
- 🌐 **Halaman Pengunjung:** `http://localhost:3000`
- 📊 **Halaman Admin:** `http://localhost:3000/admin`

> ⚙️ Konfigurasi URL API ada di `monitor-ip/.env.local` (`NEXT_PUBLIC_API_URL=http://localhost:8000`).
> Origin frontend sudah diizinkan di backend lewat `CORS_ALLOWED_ORIGINS` (lihat `backend/.env.example`).
