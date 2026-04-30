import sqlite3
import os
from datetime import datetime # unuk tgl jatuh tempo dan perhitungan denda

class DBManager:
    def __init__(self):
        # 1. Dapatkan lokasi folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, 'database', 'perpustakaan_smart.db')
        print(f"Database aktif di: {self.db_path}")
        
        # ==========================================
        # 2. SCRIPT AUTO-PATCH DATABASE ANTI-GAGAL
        # ==========================================
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Daftar semua kolom yang mau ditambahkan
            patch_queries = [
                "ALTER TABLE transaksi ADD COLUMN status_denda TEXT DEFAULT 'LUNAS'",
                "ALTER TABLE buku ADD COLUMN durasi_pinjam INTEGER DEFAULT 7",
                "ALTER TABLE transaksi ADD COLUMN kondisi_awal TEXT DEFAULT 'Baik'",
                "ALTER TABLE transaksi ADD COLUMN kondisi_akhir TEXT",
                "ALTER TABLE transaksi ADD COLUMN denda_telat INTEGER DEFAULT 0",
                "ALTER TABLE transaksi ADD COLUMN denda_rusak INTEGER DEFAULT 0",
                "ALTER TABLE transaksi ADD COLUMN catatan_kerusakan TEXT",
                "ALTER TABLE transaksi ADD COLUMN jatuh_tempo DATETIME",
                "ALTER TABLE transaksi ADD COLUMN status_verifikasi TEXT DEFAULT 'AUTO'",
            ]
            
            # Eksekusi satu-satu
            for q in patch_queries:
                try:
                    conn.execute(q)
                except:
                    pass # Abaikan jika kolomnya memang sudah ada
                    
            conn.commit()
            conn.close()
            print("Auto-Patch Database Selesai dicek.")
        except Exception as e:
            print(f"Gagal koneksi patch: {e}")
        # ==========================================
        
        # Lanjut ke kode inisialisasi lainnya di bawah sini (kalau ada) ...

    def get_member(self, rfid_id):
        """Mengambil data anggota berdasarkan RFID ID, termasuk kolom role"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Menggunakan SELECT * memastikan kolom role ikut terbawa
        cursor.execute("SELECT * FROM anggota WHERE rfid_id = ?", (rfid_id,))
        res = cursor.fetchone()
        conn.close()
        return res
    
    def cari_di_master(self, rfid_scan):
        """Mencari data siswa di Master Data berdasarkan RFID saat tap kartu di layar Guest"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT nis, nama, prodi FROM master_siswa WHERE rfid_id = ?", (rfid_scan,))
            hasil = cursor.fetchone()
            conn.close()
            return hasil  # Mengembalikan tuple (nis, nama, prodi) atau None jika tidak terdaftar
        except Exception as e:
            print(f"Error Cari Master: {e}")
            return None

    def simpan_calon_anggota(self, nis, nama, prodi):
        """Menyimpan data pendaftaran mandiri dari Halaman Guest ke tabel antrean"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Cek apakah NIS sudah ada di tabel anggota utama (sudah aktif)
            cursor.execute("SELECT rfid_id FROM anggota WHERE rfid_id IN (SELECT rfid_id FROM master_siswa WHERE nis = ?)", (nis,))
            if cursor.fetchone():
                conn.close()
                return "SUDAH_AKTIF"
                
            # Cek apakah NIS sudah ada di antrean (biar tidak dobel daftar)
            cursor.execute("SELECT id_calon FROM calon_anggota WHERE nis = ?", (nis,))
            if cursor.fetchone():
                conn.close()
                return "SUDAH_ANTRE"

            # Simpan data ke tabel antrean
            cursor.execute("""
                INSERT INTO calon_anggota (nis, nama, prodi) 
                VALUES (?, ?, ?)
            """, (nis, nama, prodi))
            
            conn.commit()
            conn.close()
            return "SUKSES"
            
        except Exception as e:
            print(f"🚨 Error Simpan Calon Anggota: {e}")
            return "ERROR"

    def get_all_members(self):
        """Mengambil daftar semua anggota (untuk keperluan admin/list)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT rfid_id, foto_path FROM anggota")
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def get_semua_calon(self):
        """Mengambil semua daftar siswa yang sudah daftar mandiri tapi belum difoto"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id_calon, nis, nama, prodi FROM calon_anggota")
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            print(f"Error Get Calon: {e}")
            return []
            
    def hapus_calon_setelah_aktif(self, nis):
        """Menghapus data dari antrean setelah resmi jadi anggota"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM calon_anggota WHERE nis = ?", (nis,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error Hapus Calon: {e}")
            
    def aktivasi_anggota_baru(self, nis, rfid_id):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT nama, prodi FROM calon_anggota WHERE nis = ?", (nis,))
            data = cursor.fetchone()
            
            if data:
                nama, prodi = data
                # Simpan ke tabel anggota
                cursor.execute("""
                    INSERT INTO anggota (rfid_id, nama, prodi, role) 
                    VALUES (?, ?, ?, 'USER')
                """, (rfid_id, nama, prodi))
                
                # AMBIL ID BARU (Angka)
                user_id = cursor.lastrowid 
                
                cursor.execute("DELETE FROM calon_anggota WHERE nis = ?", (nis,))
                conn.commit()
                conn.close()
                return user_id # Mengembalikan angka ID
            return None
        except Exception as e:
            print(f"Error Aktivasi: {e}")
            return None

    def add_member(self, rfid, nama, prodi, foto_path):
        """Menambah anggota baru dengan default role USER"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Perhatikan: kita tambahkan 'USER' di akhir query INSERT
            cursor.execute(
                "INSERT INTO anggota (rfid_id, nama, prodi, foto_path, status, role) VALUES (?, ?, ?, ?, 'AKTIF', 'USER')", 
                (rfid, nama, prodi, foto_path)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error DB: {e}")
            return False

    def check_denda(self, rfid_id):
        """Logika Cek Denda dari tabel transaksi"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(denda) FROM transaksi WHERE rfid_id = ?", (rfid_id,))
        total = cursor.fetchone()[0]
        conn.close()
        return total if total else 0
    
    # ==========================================
    # CRUD BUKU (FUNGSI UNTUK ADMIN & USER)
    # ==========================================
    def add_buku(self, barcode, judul, penulis, penerbit, stok, durasi):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # PERHATIKAN: Nama kolom di sini harus durasi_pinjam, BUKAN durasi
            query = """
                INSERT INTO buku (barcode_id, judul, penulis, penerbit, stok, durasi_pinjam) 
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            # Di sini variabel parameter tetap menggunakan 'durasi' (tidak masalah karena ini variabel Python)
            cursor.execute(query, (barcode, judul, penulis, penerbit, stok, durasi))
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            # Tetap pertahankan print error ini agar kita tahu kalau ada masalah lain
            print(f"Error DB Tambah Buku: {e}") 
            return False

    def get_all_buku(self):
        """Mengambil semua daftar buku untuk ditampilkan di tabel Admin/User"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT barcode_id, judul, penulis, penerbit, stok FROM buku")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def update_buku(self, barcode_id, judul_baru, penulis_baru, stok_baru):
        """Memperbarui data buku berdasarkan Barcode ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update data buku termasuk stoknya
            cursor.execute("""
                UPDATE buku 
                SET judul = ?, penulis = ?, stok = ? 
                WHERE barcode_id = ?
            """, (judul_baru, penulis_baru, stok_baru, barcode_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error Update Buku: {e}")
            return False

    def delete_buku(self, barcode_id):
        """Menghapus buku berdasarkan barcode_id"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM buku WHERE barcode_id = ?", (barcode_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error DB Hapus Buku: {e}")
            return False
        
    def get_buku_by_barcode(self, barcode_id):
        """Mencari satu buku spesifik berdasarkan barcode"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM buku WHERE barcode_id=?", (barcode_id,))
        res = cursor.fetchone()
        conn.close()
        return res

    def pinjam_buku(self, rfid_id, barcode_id, kondisi="Baik", catatan=""):
        conn = None
        MAX_PINJAM = 3 # Batas maksimal buku yang bisa dipinjam sekaligus
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. CEK STATUS BLOKIR USER
            cursor.execute("SELECT status FROM anggota WHERE rfid_id=?", (rfid_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return "ERROR"
                
            if user_data[0] == 'DIBLOKIR':
                conn.close()
                return "DIBLOKIR"
                
            # 2. HITUNG JUMLAH BUKU YANG SEDANG DIPINJAM (LIMIT OTOMATIS)
            cursor.execute("SELECT COUNT(*) FROM transaksi WHERE rfid_id=? AND tgl_kembali IS NULL", (rfid_id,))
            sedang_dipinjam = cursor.fetchone()[0]
            
            if sedang_dipinjam >= MAX_PINJAM:
                conn.close()
                return "LIMIT"
                
            # 3. CEK STOK & DURASI PINJAM BUKU
            cursor.execute("SELECT stok, durasi_pinjam FROM buku WHERE barcode_id=?", (barcode_id,))
            buku = cursor.fetchone()
            
            if buku and int(buku[0]) > 0:

                # 🔥 CEK KONDISI BUKU DULU
                if kondisi == "Rusak":
                    cursor.execute("""
                        INSERT INTO transaksi 
                        (rfid_id, barcode_id, status_denda, tgl_pinjam, kondisi_awal, catatan_kerusakan, status_verifikasi)
                        VALUES (?, ?, 'LUNAS', datetime('now','localtime'), ?, ?, 'PENDING')
                    """, (rfid_id, barcode_id, kondisi, catatan))
                    
                    conn.commit()
                    conn.close()
                    return "PENDING"

                # 🟢 KONDISI NORMAL (BAIK)
                cursor.execute("UPDATE buku SET stok = stok - 1 WHERE barcode_id=?", (barcode_id,))
                
                durasi = int(buku[1]) if buku[1] is not None else 7

                cursor.execute(f"""
                INSERT INTO transaksi 
                (rfid_id, barcode_id, status_denda, tgl_pinjam, jatuh_tempo, kondisi_awal, status_verifikasi) 
                VALUES (?, ?, 'LUNAS', datetime('now', 'localtime'), datetime('now', 'localtime', '+{durasi} days'), ?, 'AUTO')
            """, (rfid_id, barcode_id, kondisi))


                conn.commit() 
                conn.close()
                return "SUKSES"
            
            else:
                conn.close()
                return "HABIS"
        
        except Exception as e:
            print(f"Error pinjam buku: {e}")
            if conn:
                conn.close()
            return "ERROR"
        
    def get_transaksi_aktif(self, rfid_id, barcode_id):
        """Mengecek apakah user sedang meminjam buku ini (belum dikembalikan)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # tgl_kembali IS NULL berarti buku masih dipinjam
        cursor.execute("""
            SELECT id_transaksi, tgl_pinjam FROM transaksi 
            WHERE rfid_id=? AND barcode_id=? AND tgl_kembali IS NULL
        """, (rfid_id, barcode_id))
        res = cursor.fetchone()
        conn.close()
        return res

        
    def get_riwayat_user(self, rfid_id):
        """Mengambil riwayat peminjaman buku berdasarkan rfid_id user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Gabungkan tabel transaksi dan buku untuk mendapatkan judul buku
            cursor.execute("""
                SELECT b.judul, t.tgl_pinjam, t.tgl_kembali 
                FROM transaksi t
                JOIN buku b ON t.barcode_id = b.barcode_id
                WHERE t.rfid_id = ?
                ORDER BY t.tgl_pinjam DESC
            """, (rfid_id,))
            
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error Database Riwayat: {e}")
            return []
        
    def get_semua_laporan(self):
        """Mengambil semua data transaksi untuk laporan Admin"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Menggabungkan 3 tabel sekaligus (transaksi, anggota, buku)
            cursor.execute("""
                SELECT a.nama, b.judul, t.tgl_pinjam, t.tgl_kembali 
                FROM transaksi t
                JOIN anggota a ON t.rfid_id = a.rfid_id
                JOIN buku b ON t.barcode_id = b.barcode_id
                ORDER BY t.tgl_pinjam DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error Database Laporan: {e}")
            return []
        
        
    def get_user_terblokir(self):
        """Mengambil daftar anggota yang diblokir ATAU memiliki denda belum lunas"""
        conn = None 
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Perbaikan Query: Menambahkan kondisi OR t.status_denda = 'BELUM LUNAS'
            cursor.execute("""
                SELECT a.rfid_id, a.nama, COALESCE(SUM(t.denda), 0) as total_denda
                FROM anggota a 
                LEFT JOIN transaksi t ON a.rfid_id = t.rfid_id AND t.status_denda = 'BELUM LUNAS'
                WHERE a.status = 'DIBLOKIR' OR t.status_denda = 'BELUM LUNAS'
                GROUP BY a.rfid_id
            """)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error Get Terblokir: {e}")
            if conn:
                conn.close()
            return []

    def lunasi_denda(self, rfid_id):
        """Membuka blokir user dan melunasi semua dendanya"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # 1. Update transaksi jadi LUNAS
            cursor.execute("UPDATE transaksi SET status_denda = 'LUNAS' WHERE rfid_id = ? AND status_denda = 'BELUM LUNAS'", (rfid_id,))
            # 2. Buka blokir anggota
            cursor.execute("UPDATE anggota SET status = 'AKTIF' WHERE rfid_id = ?", (rfid_id,))
            conn.commit() # Wajib commit karena ini mengubah (UPDATE) data
            conn.close()
            return True
        except Exception as e:
            print(f"Error Pelunasan: {e}")
            # Tutup koneksi secara paksa jika gagal di tengah jalan
            if conn:
                conn.close()
            return False
        
    def get_dashboard_stats(self):
        """Mengambil rekapitulasi data (Sekarang 6 Statistik)"""
        total_stok = 0
        total_judul = 0
        total_anggota = 0
        buku_dipinjam = 0
        anggota_terblokir = 0
        antrean_aktivasi = 0 # <-- 1. Variabel Baru Disiapkan

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Hitung Stok & Judul sekaligus
        try:
            cursor.execute("SELECT SUM(stok), COUNT(*) FROM buku")
            res = cursor.fetchone()
            total_stok = res[0] if res[0] is not None else 0
            total_judul = res[1] if res[1] is not None else 0
        except Exception as e:
            print(f"Error Hitung Buku: {e}")

        # 2. Total Anggota
        try:
            cursor.execute("SELECT COUNT(*) FROM anggota WHERE role != 'ADMIN'")
            total_anggota = cursor.fetchone()[0]
        except Exception as e:
            print(f"Error Hitung Anggota: {e}")

        # 3. Buku Dipinjam
        try:
            cursor.execute("SELECT COUNT(*) FROM transaksi WHERE tgl_kembali IS NULL")
            buku_dipinjam = cursor.fetchone()[0]
        except Exception as e:
            print(f"Error Hitung Dipinjam: {e}")

        # 5. Hitung Antrean Aktivasi
        try:
            cursor.execute("SELECT COUNT(*) FROM calon_anggota")
            antrean_aktivasi = cursor.fetchone()[0]
        except Exception as e:
            print(f"Error Hitung Antrean: {e}")

        conn.close() # <-- Pastikan tambahan baru di atas baris ini

        # 6. Anggota Terblokir (dari halaman denda)
        try:
            data_terblokir = self.get_user_terblokir()
            anggota_terblokir = len(data_terblokir) if data_terblokir else 0
        except Exception as e:
            print(f"Error Hitung Terblokir: {e}")
            
        # --- RETURN 6 NILAI SEKARANG ---
        return (total_stok, total_judul, total_anggota, buku_dipinjam, anggota_terblokir, antrean_aktivasi)  
  
    #fitur deteksi wajah login berdasarkan ID Angka (ROWID) yang otomatis di-generate SQLite saat insert anggota baru
    def get_anggota_by_rfid(self, rfid_id):
        """Mengecek data asli di database berdasarkan RFID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT rfid_id, nama, prodi, role FROM anggota WHERE rfid_id = ?", (rfid_id,))
            data = cursor.fetchone()
            conn.close()
            return data
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    def get_transaksi_pending(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # JOIN agar dapat Nama dan Judul
            cursor.execute("""
                SELECT t.id_transaksi, a.nama, b.judul 
                FROM transaksi t
                JOIN anggota a ON t.rfid_id = a.rfid_id
                JOIN buku b ON t.barcode_id = b.barcode_id
                WHERE t.status_verifikasi='PENDING'
            """)
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            print(f"Error Get Pending: {e}")
            return []

    def verifikasi_buku(self, id_transaksi, status_baru, catatan=""):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if status_baru == 'APPROVED':
                cursor.execute("""
                    UPDATE transaksi SET status_verifikasi = 'APPROVED', catatan_kerusakan = ? 
                    WHERE id_transaksi = ?
                """, (catatan, id_transaksi))
            elif status_baru == 'REJECTED':
                # Kembalikan stok jika ditolak
                cursor.execute("SELECT barcode_id FROM transaksi WHERE id_transaksi = ?", (id_transaksi,))
                barcode_id = cursor.fetchone()[0]
                cursor.execute("UPDATE buku SET stok = stok + 1 WHERE barcode_id = ?", (barcode_id,))
                cursor.execute("UPDATE transaksi SET status_verifikasi = 'REJECTED' WHERE id_transaksi = ?", (id_transaksi,))
                
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error Verifikasi: {e}")
            return False
        
    def get_pinjaman_aktif_by_rfid(self, rfid_id):
        """Mengambil maksimal 3 buku yang sedang dipinjam (FIX: Handle NULL & Empty String)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Perhatikan penambahan (t.tgl_kembali IS NULL OR t.tgl_kembali = '')
            cursor.execute("""
                SELECT t.id_transaksi, b.judul, t.tgl_pinjam, t.jatuh_tempo, t.kondisi_awal, t.catatan_kerusakan
                FROM transaksi t
                JOIN buku b ON t.barcode_id = b.barcode_id
                WHERE t.rfid_id = ? AND (t.tgl_kembali IS NULL OR t.tgl_kembali = '')
            """, (str(rfid_id).strip(),))
            
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            print(f"Error Get Pinjaman Aktif: {e}")
            return []

    def proses_kembali_admin(self, id_transaksi, kondisi_akhir, denda_tambahan=0):
        from datetime import datetime # Pastikan ini ada di atas dbManager.py
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Ambil data untuk cek keterlambatan
            cursor.execute("SELECT barcode_id, jatuh_tempo FROM transaksi WHERE id_transaksi = ?", (id_transaksi,))
            row = cursor.fetchone()
            if not row: return False, 0
            barcode_id, jatuh_tempo_str = row
            
            # 2. Hitung Denda Telat
            denda_telat = 0
            if jatuh_tempo_str:
                jatuh_tempo = datetime.strptime(jatuh_tempo_str, "%Y-%m-%d %H:%M:%S")
                sekarang = datetime.now()
                if sekarang > jatuh_tempo:
                    denda_telat = (sekarang - jatuh_tempo).days * 1000 # Rp 1000/hari
            
            # 3. Total Denda & Status
            denda_rusak = int(denda_tambahan)
            total_denda = denda_telat + denda_rusak
            status_denda = 'BELUM LUNAS' if total_denda > 0 else 'LUNAS'
            tgl_kembali = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 4. UPDATE Tabel Transaksi
            cursor.execute("""
                UPDATE transaksi 
                SET tgl_kembali = ?, 
                    kondisi_akhir = ?, 
                    denda_telat = ?, 
                    denda_rusak = ?, 
                    denda = ?, 
                    status_denda = ?,
                    status_verifikasi = 'VERIFIED'
                WHERE id_transaksi = ?
            """, (tgl_kembali, kondisi_akhir, denda_telat, denda_rusak, total_denda, status_denda, id_transaksi))
            
            # 5. UPDATE STOK BUKU (Logika Penting!)
            # Jika kondisi BUKAN 'Hilang', stok kembali ke rak (+1)
            if kondisi_akhir != "Hilang":
                cursor.execute("UPDATE buku SET stok = stok + 1 WHERE barcode_id = ?", (barcode_id,))
            
            conn.commit()
            conn.close()
            return True, total_denda
        except Exception as e:
            print(f"Error Proses Pengembalian: {e}")
            return False, 0
        
    def get_anggota_by_id(self, user_id):
        """Dipanggil oleh Face Recognition untuk mengambil data berdasarkan ID (angka)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Face Recognition menggunakan ID berupa angka (1, 2, 3...). 
            # Di SQLite, angka urutan ini otomatis tersimpan di kolom ROWID
            cursor.execute("SELECT rfid_id, nama, prodi, role FROM anggota WHERE ROWID = ?", (user_id,))
            data = cursor.fetchone()
            conn.close()
            
            return data
        except Exception as e:
            print(f"Error Get Anggota by ID: {e}")
            return None
        
    def catat_presensi(self, rfid_id, nama, keperluan="Membaca/Belajar"):
        try:
            from datetime import datetime
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            query = """
                INSERT INTO presensi (rfid_id, nama, waktu_masuk, keperluan)
                VALUES (?, ?, ?, ?)
            """
            cursor.execute(query, (rfid_id, nama, waktu_sekarang, keperluan))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error Simpan Presensi: {e}")
            return False

    def get_log_presensi(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ambil data terbaru di urutan paling atas
            cursor.execute("SELECT * FROM presensi ORDER BY waktu_masuk DESC")
            rows = cursor.fetchall()
            
            conn.close()
            return rows
        except Exception as e:
            print(f"Error Get Log Presensi: {e}")
            return []