import sqlite3
import os

def inisialisasi_folder():
    # Membuat folder yang dibutuhkan jika belum ada
    folders = ['database', 'foto_anggota']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Folder '{folder}' berhasil dibuat.")

def buat_koneksi():
    # Koneksi ke file DB di dalam folder database
    return sqlite3.connect('database/perpustakaan_smart.db')

def buat_tabel_lengkap():
    conn = buat_koneksi()
    cursor = conn.cursor()

    print("Sedang membangun tabel sistem...")

    # 1. Tabel Anggota (Simpan ID RFID dan Path Foto Wajah)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anggota (
            rfid_id TEXT PRIMARY KEY,
            nama TEXT NOT NULL,
            prodi TEXT,
            foto_path TEXT,
            status TEXT DEFAULT 'AKTIF'
        )
    ''')

    # 2. Tabel Buku (Simpan ID Barcode)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buku (
            barcode_id TEXT PRIMARY KEY,
            judul TEXT NOT NULL,
            penulis TEXT,
            status_buku TEXT DEFAULT 'TERSEDIA'
        )
    ''')

    # 3. Tabel Transaksi (Riwayat Pinjam)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id_transaksi INTEGER PRIMARY KEY AUTOINCREMENT,
            rfid_id TEXT,
            barcode_id TEXT,
            tgl_pinjam TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tgl_kembali TEXT,
            denda INTEGER DEFAULT 0,
            FOREIGN KEY(rfid_id) REFERENCES anggota(rfid_id),
            FOREIGN KEY(barcode_id) REFERENCES buku(barcode_id)
        )
    ''')
    
    # ==========================================
    # 1. TAMBAH TABEL ANTREAN GUEST
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calon_anggota (
            id_calon INTEGER PRIMARY KEY AUTOINCREMENT,
            nis TEXT NOT NULL,
            nama TEXT NOT NULL,
            prodi TEXT NOT NULL,
            waktu_daftar DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ==========================================
    # 2. TAMBAH TABEL DATA CENTER SEKOLAH
    # ==========================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS master_siswa (
            rfid_id TEXT PRIMARY KEY,
            nis TEXT NOT NULL,
            nama TEXT NOT NULL,
            prodi TEXT NOT NULL
        )
    """)

    # Masukkan data dummy jika tabelnya masih kosong
    data_dummy = [
        ('12345678', '22001', 'Budi Santoso', 'RPL'),
        ('87654321', '22002', 'Siti Aminah', 'Pemasaran'),
        ('A1B2C3D4', '22003', 'Rudi Tabuti', 'Teknik Elektro')
    ]
    cursor.executemany("INSERT OR IGNORE INTO master_siswa VALUES (?,?,?,?)", data_dummy)


    # Tambahkan Data Contoh (Dummy Data)
    cursor.execute("INSERT OR IGNORE INTO buku (barcode_id, judul, penulis) VALUES ('B001', 'Belajar Python AI', 'Gemini AI')")
    cursor.execute("INSERT OR IGNORE INTO buku (barcode_id, judul, penulis) VALUES ('B002', 'Dasar Arduino', 'Robotika')")
    
    conn.commit()
    conn.close()
    print("Fase 1 Berhasil: Database dan Tabel siap digunakan!")

if __name__ == "__main__":
    inisialisasi_folder()
    buat_tabel_lengkap()