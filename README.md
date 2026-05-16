# ⛩ AniméStream v2

Website nonton anime subtitle Indonesia — Flask + Sanka Vollerei API.

## Jalankan Lokal
```bash
pip install -r requirements.txt
python app.py
# Buka: http://localhost:5000
```

## Deploy Vercel
```bash
npm i -g vercel
vercel login
vercel --prod
```
Atau push ke GitHub → import di vercel.com/new → Deploy.

## Fitur
- Beranda: ongoing + completed + jadwal hari ini
- Jadwal mingguan (per hari)
- Detail anime: info lengkap + sinopsis + daftar episode
- Halaman nonton: player + pilih server + download
- Search live
- Genre filter + pagination
- Desain light/blog responsif mobile
