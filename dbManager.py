import sqlite3
import os
from datetime import datetime # unuk tgl jatuh tempo dan perhitungan denda

class DBManager:
    def __init__(self):
        # 1. Dapatkan lokasi folder di mana file dbManager.py ini berada
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Gabungkan secara absolut ke folder database
        # Ini menjamin Python selalu menunjuk ke folder yang benar
        self.db_path = os.path.join(base_dir, 'database', 'perpustakaan_smart.db')
        
        # Debug: Print ini untuk memastikan jalur yang dibaca aplikasi sudah benar
        print(f"Database aktif di: {self.db_path}")
        
        self.conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            # Patch lama: Tambah status denda
            conn.execute("ALTER TABLE transaksi ADD COLUMN status_denda TEXT DEFAULT 'LUNAS'")
            conn.commit()
        except:
            pass 

        try:
            if conn is None:
                conn = sqlite3.connect(self.db_path)
            # PATCH BARU: Tambah durasi pinjam di tabel buku (Default 7 Hari)
            conn.execute("ALTER TABLE buku ADD COLUMN durasi_pinjam INTEGER DEFAULT 7")
            conn.commit()
        except:
            pass # Abaikan jika kolom durasi_pinjam sudah berhasil dibuat sebelumnya
        finally:
            if conn:
                conn.close()

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
    def add_buku(self, barcode_id, judul, penulis, penerbit, stok):
        """Menambah buku baru ke database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO buku (barcode_id, judul, penulis, penerbit, stok) VALUES (?, ?, ?, ?, ?)",
                (barcode_id, judul, penulis, penerbit, int(stok))
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            print("Error: Barcode/Kode Buku sudah terdaftar di sistem!")
            return False
        except Exception as e:
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

    def pinjam_buku(self, rfid_id, barcode_id):
        """Mencatat transaksi pinjam dengan limit otomatis dari tabel transaksi"""
        conn = None
        
        # --- ATUR BATAS MAKSIMAL PINJAM DI SINI ---
        MAX_PINJAM = 3 
        
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
            # Menghitung transaksi user ini yang tgl_kembali-nya belum ada
            cursor.execute("SELECT COUNT(*) FROM transaksi WHERE rfid_id=? AND tgl_kembali IS NULL", (rfid_id,))
            sedang_dipinjam = cursor.fetchone()[0]
            
            # Tolak jika sudah meminjam 3 buku atau lebih
            if sedang_dipinjam >= MAX_PINJAM:
                conn.close()
                return "LIMIT" # Kita buat status tolakan baru: "LIMIT"
                
            # 3. CEK STOK & DURASI PINJAM BUKU
            cursor.execute("SELECT stok, durasi_pinjam FROM buku WHERE barcode_id=?", (barcode_id,))
            buku = cursor.fetchone()
            
            if buku and int(buku[0]) > 0:
                # Ambil durasi pinjam. Jika kosong, otomatis 7 hari.
                durasi = int(buku[1]) if buku[1] is not None else 7
                
                # Kurangi stok buku
                cursor.execute("UPDATE buku SET stok = stok - 1 WHERE barcode_id=?", (barcode_id,))
                
                # CATAT TRANSAKSI DENGAN JATUH TEMPO
                try:
                    query_insert = f"""
                        INSERT INTO transaksi (rfid_id, barcode_id, status_denda, tgl_pinjam, jatuh_tempo) 
                        VALUES (?, ?, 'LUNAS', datetime('now', 'localtime'), datetime('now', 'localtime', '+{durasi} days'))
                    """
                    cursor.execute(query_insert, (rfid_id, barcode_id))
                except sqlite3.OperationalError:
                    # Fallback jika kolom jatuh_tempo belum ada
                    cursor.execute("INSERT INTO transaksi (rfid_id, barcode_id, status_denda) VALUES (?, ?, 'LUNAS')", (rfid_id, barcode_id))
                
                conn.commit() 
                conn.close()
                return "SUKSES"
                
            conn.close()
            return "HABIS" # Gagal jika stok buku 0
            
        except Exception as e:
            print(f"🚨 Error Database Peminjaman: {e}")
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

    def kembalikan_buku(self, rfid_id, barcode_id, id_transaksi, tgl_pinjam_str):
        """Memproses pengembalian, cek denda otomatis, dan blokir jika telat"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. AMBIL DURASI MAKSIMAL BUKU INI (Default 7 hari jika kosong)
            cursor.execute("SELECT durasi_pinjam FROM buku WHERE barcode_id=?", (barcode_id,))
            buku_data = cursor.fetchone()
            durasi_maksimal = int(buku_data[0]) if buku_data and buku_data[0] is not None else 7
            
            # 👇 TAMBAHKAN BARIS INI UNTUK TESTING 👇
            # durasi_maksimal = -1  
            # ⚠️ JANGAN LUPA DIHAPUS KALAU APLIKASI MAU DIPAKAI ASLI!
            
            # 2. HITUNG SELISIH HARI (Pastikan format tanggal tidak error)
            try:
                tgl_pinjam = datetime.strptime(tgl_pinjam_str[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # Fallback kalau format di DB cuma YYYY-MM-DD
                tgl_pinjam = datetime.strptime(tgl_pinjam_str[:10], "%Y-%m-%d")
                
            tgl_sekarang = datetime.now()
            selisih_hari = (tgl_sekarang - tgl_pinjam).days
            
            tarif_denda = 1000 
            total_denda = 0
            status_denda_val = 'LUNAS'
            hari_telat = 0
            
            # 3. JIKA TELAT (Kena Denda & Blokir)
            if selisih_hari > durasi_maksimal:
                hari_telat = selisih_hari - durasi_maksimal
                total_denda = hari_telat * tarif_denda
                status_denda_val = 'BELUM LUNAS'
                
                # BLOKIR AKUN USER KARENA DENDA
                cursor.execute("UPDATE anggota SET status = 'DIBLOKIR' WHERE rfid_id = ?", (rfid_id,))
                
            # 4. UPDATE TABEL TRANSAKSI
            waktu_kembali_str = tgl_sekarang.strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                UPDATE transaksi 
                SET tgl_kembali = ?, denda = ?, status_denda = ? 
                WHERE id_transaksi = ?
            """, (waktu_kembali_str, total_denda, status_denda_val, id_transaksi))
            
            # 5. KEMBALIKAN STOK BUKU (+1)
            cursor.execute("UPDATE buku SET stok = stok + 1 WHERE barcode_id=?", (barcode_id,))
            
            conn.commit()
            conn.close()
            
            # Return hari_telat agar bisa dimunculkan di notif UI nanti
            return True, total_denda, hari_telat 
            
        except Exception as e:
            print(f"🚨 Error Database Pengembalian: {e}")
            return False, 0, 0
        
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
        """Mengambil daftar anggota yang diblokir beserta total dendanya (walau denda 0)"""
        conn = None 
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Perbaikan: Menggunakan LEFT JOIN dan COALESCE
            cursor.execute("""
                SELECT a.rfid_id, a.nama, COALESCE(SUM(t.denda), 0) 
                FROM anggota a 
                LEFT JOIN transaksi t ON a.rfid_id = t.rfid_id AND t.status_denda = 'BELUM LUNAS'
                WHERE a.status = 'DIBLOKIR'
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
    def get_anggota_by_id(self, id_user):
        """Mengambil data anggota berdasarkan ID Angka dari deteksi wajah"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Catatan: Sesuaikan 'id_user' dengan nama kolom Primary Key di tabel anggota kamu.
            # Jika tidak ada kolom khusus, SQLite punya kolom bawaan bernama ROWID.
            cursor.execute("SELECT rfid_id, nama, prodi, role FROM anggota WHERE ROWID = ?", (id_user,))
            data = cursor.fetchone()
            
            conn.close()
            return data # Mengembalikan tuple (rfid_id, nama, prodi, role)
        except Exception as e:
            print(f"Error Get Anggota by ID: {e}")
            return None