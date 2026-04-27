import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import os
from dbManager import DBManager # Import class dari file terpisah

# --- 1. PAGE: LANDING PAGE (LAYAR AWAL / MENU UTAMA) ---
class PageLanding(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Menggunakan grid row/column weight untuk menengahkan konten secara otomatis
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="SELAMAT DATANG DI", font=("Arial", 22)).grid(row=1, column=0, pady=(0, 5))
        ctk.CTkLabel(self, text="SMART LIBRARY SYSTEM", font=("Arial", 40, "bold"), text_color="#3498db").grid(row=2, column=0, pady=(0, 50))

        frame_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_btn.grid(row=3, column=0)

        # Tombol Raksasa Modern (Menggunakan CTkButton dengan rounded corners)
        btn_login = ctk.CTkButton(frame_btn, text="LOGIN ANGGOTA\n(Masuk)", font=("Arial", 18, "bold"), 
                                  width=250, height=90, corner_radius=15, 
                                  command=lambda: self.controller.show_frame("PageLogin"))
        btn_login.pack(side="left", padx=20)

        btn_aktivasi = ctk.CTkButton(frame_btn, text="AKTIVASI AKUN\n(Pendaftaran)", font=("Arial", 18, "bold"), 
                                     width=250, height=90, corner_radius=15, fg_color="#27ae60", hover_color="#2ecc71",
                                     command=lambda: self.controller.show_frame("PageAktivasi"))
        btn_aktivasi.pack(side="left", padx=20)

# --- 2. PAGE: LOGIN (PENGGANTI PageStandby Lama) ---
class PageLogin(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="LOGIN ANGGOTA", font=("Arial", 30, "bold")).grid(row=1, column=0, pady=20)
        
        self.status_label = ctk.CTkLabel(self, text="Silakan Tempelkan Kartu Anda di Scanner", font=("Arial", 18))
        self.status_label.grid(row=2, column=0, pady=20)

        # Entry untuk RFID (Didesain lebih elegan seperti search bar)
        self.entry_rfid = ctk.CTkEntry(self, placeholder_text="Fokus di sini untuk Tap Kartu...", width=300, height=45, font=("Arial", 16), justify="center")
        self.entry_rfid.grid(row=3, column=0, pady=10)
        self.entry_rfid.bind("<Return>", self.proses_rfid)

        ctk.CTkButton(self, text="Kembali", fg_color="transparent", border_width=2, border_color="red", text_color="red", hover_color="#330000",
                      width=150, height=40, command=self.go_back).grid(row=4, column=0, pady=40)

    def on_show(self):
        # INI SANGAT PENTING: Memaksa kursor berkedip otomatis di form RFID saat halaman dibuka
        self.entry_rfid.focus_set()
        self.status_label.configure(text="Silakan Tempelkan Kartu Anda di Scanner", text_color="white")

    def proses_rfid(self, event):
        rfid_input = self.entry_rfid.get().strip()
        user = self.controller.db.get_member(rfid_input)
        
        if user:
            self.controller.current_user = user
            role = str(user[-1]).strip().upper() 
            self.entry_rfid.delete(0, 'end') # Bersihkan sebelum pindah
            
            if role == "ADMIN":
                self.controller.show_frame("PageMenu")
            else:
                self.controller.show_frame("PageFaceAuth")
        else:
            self.status_label.configure(text="KARTU TIDAK TERDAFTAR! Silakan Aktivasi Akun.", text_color="red")
            self.entry_rfid.delete(0, 'end') 

    def go_back(self):
        self.entry_rfid.delete(0, 'end')
        self.controller.show_frame("PageLanding")

# --- 3. PAGE: AKTIVASI AKUN (FORM GUEST BARU) ---
class PageAktivasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=1, column=0)

        ctk.CTkLabel(main_container, text="AKTIVASI AKUN PERPUSTAKAAN", font=("Arial", 26, "bold")).pack(pady=(0, 5))
        self.status_label = ctk.CTkLabel(main_container, text="Tap Kartu Pelajar untuk Auto-Fill, atau ketik manual.", font=("Arial", 16))
        self.status_label.pack(pady=10)

        # Frame khusus untuk menampung form input
        form_frame = ctk.CTkFrame(main_container, fg_color="gray20", corner_radius=15)
        form_frame.pack(pady=10, padx=20, ipadx=20, ipady=20)

        # Kolom Auto-fill trigger
        self.entry_rfid = ctk.CTkEntry(form_frame, placeholder_text="Fokus kursor disini untuk Tap Kartu...", width=350, justify="center")
        self.entry_rfid.pack(pady=(10, 20))
        self.entry_rfid.bind("<Return>", self.proses_scan_kartu)

        # Form Manual
        self.ent_nis = ctk.CTkEntry(form_frame, placeholder_text="Nomor Induk Siswa (NIS)", width=350, height=40, font=("Arial", 14))
        self.ent_nis.pack(pady=10)

        self.ent_nama = ctk.CTkEntry(form_frame, placeholder_text="Nama Lengkap", width=350, height=40, font=("Arial", 14))
        self.ent_nama.pack(pady=10)

        self.ent_prodi = ctk.CTkEntry(form_frame, placeholder_text="Program Studi / Jurusan", width=350, height=40, font=("Arial", 14))
        self.ent_prodi.pack(pady=10)

        # Tombol Aksi
        btn_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Kembali", fg_color="transparent", border_width=2, border_color="red", text_color="red", hover_color="#330000", width=150, height=45, font=("Arial", 14, "bold"), command=self.go_back).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Konfirmasi Aktivasi", fg_color="green", hover_color="#27ae60", width=200, height=45, font=("Arial", 14, "bold"), command=self.simpan_aktivasi).grid(row=0, column=1, padx=10)

    def on_show(self):
        # Selalu arahkan fokus ke entry RFID agar siap ditap kartu
        self.entry_rfid.focus_set()
        self.status_label.configure(text="Tap Kartu Pelajar untuk Auto-Fill, atau ketik manual.", text_color="white")

    def proses_scan_kartu(self, event):
        rfid_scan = self.entry_rfid.get().strip()
        if not rfid_scan: return

        # Panggil fungsi pencarian ke data center dummy yang kita buat di dbManager
        hasil = self.controller.db.cari_di_master(rfid_scan)
        
        # Bersihkan form lama
        self.ent_nis.delete(0, 'end')
        self.ent_nama.delete(0, 'end')
        self.ent_prodi.delete(0, 'end')

        if hasil:
            # Isi kolom dengan data: hasil[0]=nis, hasil[1]=nama, hasil[2]=prodi
            self.ent_nis.insert(0, hasil[0])
            self.ent_nama.insert(0, hasil[1])
            self.ent_prodi.insert(0, hasil[2])
            self.status_label.configure(text="✅ Data ditemukan! Silakan cek dan klik Konfirmasi.", text_color="#2ecc71")
        else:
            self.status_label.configure(text="❌ Kartu belum terdaftar di Pusat. Silakan isi manual.", text_color="#e74c3c")
        
        self.entry_rfid.delete(0, 'end')

    def simpan_aktivasi(self):
        nis = self.ent_nis.get().strip()
        nama = self.ent_nama.get().strip()
        prodi = self.ent_prodi.get().strip()

        if not nis or not nama or not prodi:
            self.status_label.configure(text="⚠️ Semua kolom wajib diisi!", text_color="orange")
            return
        
        # Simpan ke tabel calon_anggota via dbManager
        status = self.controller.db.simpan_calon_anggota(nis, nama, prodi)
        
        if status == "SUKSES":
            self.status_label.configure(text="✅ Berhasil! Silakan temui Admin untuk aktivasi foto.", text_color="#2ecc71")
            # Kembali ke menu awal otomatis setelah 3 detik
            self.after(3000, self.go_back) 
        elif status == "SUDAH_AKTIF":
            self.status_label.configure(text="⚠️ NIS ini sudah terdaftar & aktif! Silakan Login.", text_color="orange")
        elif status == "SUDAH_ANTRE":
            self.status_label.configure(text="⚠️ Anda sudah mendaftar. Silakan temui Admin.", text_color="orange")
        else:
            self.status_label.configure(text="❌ Terjadi kesalahan sistem.", text_color="red")

    def go_back(self):
        self.entry_rfid.delete(0, 'end')
        self.ent_nis.delete(0, 'end')
        self.ent_nama.delete(0, 'end')
        self.ent_prodi.delete(0, 'end')
        self.controller.show_frame("PageLanding")

# --- 2. PAGE: FACE AUTH ---
class PageFaceAuth(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- FLAG BARU --- 
        # Untuk mengunci deteksi agar tidak berulang saat delay berjalan
        self.login_berhasil = False 
        
        ctk.CTkLabel(self, text="SCAN WAJAH UNTUK LOGIN", font=("Arial", 24, "bold")).pack(pady=20)
        
        self.video_label = ctk.CTkLabel(self, text="")
        self.video_label.pack(pady=10)
        
        ctk.CTkButton(self, text="Kembali ke Menu", command=self.batal_login).pack(pady=10)

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists('trainer.yml'):
            self.recognizer.read('trainer.yml')
        
        self.cap = None

    def on_show(self):
        # Reset status tiap kali halaman ini dibuka ulang
        self.login_berhasil = False 
        
        if not os.path.exists('trainer.yml'):
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", "Sistem belum ditraining! Hubungi Admin.")
            self.controller.show_frame("PageLanding")
            return
            
        self.cap = cv2.VideoCapture(0)
        self.scan_wajah()

    def tampilkan_ke_layar(self, frame):
        """Fungsi pembantu untuk update gambar ke UI"""
        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_img)
        imgtk = ctk.CTkImage(light_image=img, dark_image=img, size=(640, 480))
        self.video_label.configure(image=imgtk)
        self.video_label.image = imgtk

    def scan_wajah(self):
        if self.cap is None or not self.cap.isOpened():
            return

        # Jika sudah login, stop looping kamera, biarkan gambar terakhir membeku
        if self.login_berhasil:
            return

        ret, frame = self.cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.controller.face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                id_hasil, confidence = self.recognizer.predict(gray[y:y+h, x:x+w])
                
                if confidence < 65: 
                    user_data = self.controller.db.get_anggota_by_id(id_hasil)
                    
                    if user_data:
                        nama_user = user_data[1]
                        
                        # Tulis teks yang keren
                        cv2.putText(frame, f"Akses Diberikan:", (x, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                        cv2.putText(frame, f"{nama_user}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        
                        # 1. Kunci sistem agar tidak scan wajah ini berkali-kali
                        self.login_berhasil = True 
                        
                        # 2. Update UI dengan frame yang ada tulisan "Akses Diberikan"-nya
                        self.tampilkan_ke_layar(frame)
                        
                        # 3. Beri jeda 2 detik (2000 ms), BARU jalankan sukses_login
                        self.after(2000, lambda: self.sukses_login(user_data))
                        return 
                else:
                    cv2.putText(frame, "Tidak Dikenali", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # Update UI jika belum berhasil login
            self.tampilkan_ke_layar(frame)

        # Ulangi fungsi setiap 10ms jika belum berhasil login
        if not self.login_berhasil:
            self.after(10, self.scan_wajah)

    def sukses_login(self, user_data):
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        self.controller.current_user = user_data
        self.controller.show_frame("PageMenu") 

    def batal_login(self):
        self.login_berhasil = True # Hentikan loop kamera
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        self.controller.show_frame("PageLanding")

# --- PAGE: MENU UTAMA (BERBAGI UNTUK ADMIN & USER) ---
class PageMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.welcome_label = ctk.CTkLabel(self, text="Memuat...", font=("Arial", 26, "bold"))
        self.welcome_label.pack(pady=(30, 10))

        # --- Frame Stats (Sekarang Konfigurasi 5 Kolom) ---
        self.frame_stats = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_stats.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1) # Tambah kolom ke-5

        # Buat 6 Kartu
        self.lbl_tot_stok = self.buat_kartu(self.frame_stats, "Total Stok", "0", "#3498db", 0)
        self.lbl_tot_judul = self.buat_kartu(self.frame_stats, "Total Judul", "0", "#9b59b6", 1) # Baru! Ungu
        self.lbl_tot_anggota = self.buat_kartu(self.frame_stats, "Anggota", "0", "#2ecc71", 2)
        self.lbl_dipinjam = self.buat_kartu(self.frame_stats, "Dipinjam", "0", "#f39c12", 3)
        self.lbl_terblokir = self.buat_kartu(self.frame_stats, "Terblokir", "0", "#e74c3c", 4)
        self.lbl_antrean = self.buat_kartu(self.frame_stats, "Antrean_Aktivasi", "0", "#16a085", 5)

        # ... (Sisa kode frame_nav dan tombol-tombol tetap sama seperti sebelumnya) ...
        self.frame_nav = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_nav.pack(pady=10)
        self.btn_admin_buku = ctk.CTkButton(self.frame_nav, text="📚 Kelola Buku", width=160, height=40, command=lambda: self.controller.show_frame("PageAdminBuku"))
        self.btn_admin_anggota = ctk.CTkButton(self.frame_nav, text="👥 Aktivasi Anggota", width=160, height=40, command=lambda: self.controller.show_frame("PageAdminDaftar"))
        self.btn_admin_laporan = ctk.CTkButton(self.frame_nav, text="📊 Laporan", width=160, height=40, command=lambda: self.controller.show_frame("PageAdminLaporan"))
        self.btn_admin_denda = ctk.CTkButton(self.frame_nav, text="💸 Kelola Denda", width=160, height=40, command=lambda: self.controller.show_frame("PageAdminDenda"))
        self.btn_pinjam = ctk.CTkButton(self.frame_nav, text="📥 Pinjam Buku", width=180, height=40, command=lambda: self.controller.show_frame("PagePeminjaman"))
        self.btn_kembali = ctk.CTkButton(self.frame_nav, text="📤 Kembalikan Buku", width=180, height=40, command=lambda: self.controller.show_frame("PagePengembalian"))
        self.btn_riwayat_user = ctk.CTkButton(self.frame_nav, text="📖 Riwayat Saya", width=180, height=40, command=lambda: self.controller.show_frame("PageRiwayatUser"))
        self.btn_logout = ctk.CTkButton(self.frame_nav, text="Keluar (Log Out)", fg_color="#E82626", hover_color="#A90000", width=140, command=self.logout)

    def buat_kartu(self, parent, judul, nilai, warna, kolom):
        card = ctk.CTkFrame(parent, fg_color="gray20", border_width=2, border_color=warna, corner_radius=10)
        card.grid(row=0, column=kolom, padx=5, pady=10, sticky="nsew") # Jarak padx dikurangi sedikit agar muat 5
        ctk.CTkLabel(card, text=judul, font=("Arial", 13, "bold"), text_color="gray70").pack(pady=(15, 0))
        lbl_nilai = ctk.CTkLabel(card, text=nilai, font=("Arial", 28, "bold"), text_color=warna)
        lbl_nilai.pack(pady=(5, 15))
        return lbl_nilai

    def on_show(self):
        if self.controller.current_user:
            user_name = self.controller.current_user[1]
            role = str(self.controller.current_user[-1]).strip().upper()

            # Sembunyikan semua navigasi dulu
            self.btn_admin_buku.grid_forget()
            self.btn_admin_anggota.grid_forget()
            self.btn_admin_laporan.grid_forget()
            self.btn_admin_denda.grid_forget()
            self.btn_pinjam.grid_forget()
            self.btn_kembali.grid_forget()
            self.btn_riwayat_user.grid_forget()

            if role == "ADMIN":
                self.welcome_label.configure(text=f"Panel Admin: {user_name}")
                self.frame_stats.pack(after=self.welcome_label, pady=20, padx=10, fill="x")

                # Ambil data dari database (5 nilai)
                stats = self.controller.db.get_dashboard_stats()
                if stats:
                    stok, judul, anggota, pinjam, blokir, antrean_aktivasi = stats
                    self.lbl_tot_stok.configure(text=str(stok))
                    self.lbl_tot_judul.configure(text=str(judul))
                    self.lbl_tot_anggota.configure(text=str(anggota))
                    self.lbl_dipinjam.configure(text=str(pinjam))
                    self.lbl_terblokir.configure(text=str(blokir))
                    self.lbl_antrean.configure(text=str(antrean_aktivasi))

                self.btn_admin_buku.grid(row=0, column=0, padx=5, pady=10)
                self.btn_admin_anggota.grid(row=0, column=1, padx=5, pady=10)
                self.btn_admin_laporan.grid(row=0, column=2, padx=5, pady=10) 
                self.btn_admin_denda.grid(row=0, column=3, padx=5, pady=10)
                self.btn_logout.grid(row=1, column=0, columnspan=4, padx=10, pady=30) 
            else:
                self.welcome_label.configure(text=f"Selamat Datang, {user_name}!")
                self.frame_stats.pack_forget()
                self.btn_pinjam.grid(row=0, column=0, padx=10, pady=10)
                self.btn_kembali.grid(row=0, column=1, padx=10, pady=10)
                self.btn_riwayat_user.grid(row=0, column=2, padx=10, pady=10)
                self.btn_logout.grid(row=1, column=0, columnspan=3, padx=10, pady=30)

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame("PageLanding")

# --- 4. PAGE: ADMIN DAFTAR ANGGOTA ---
class PageAdminDaftar(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="VERIFIKASI & AKTIVASI WAJAH", font=("Arial", 24, "bold")).pack(pady=20)
        
        # --- TABEL ANTRIAN ---
        self.label_info = ctk.CTkLabel(self, text="Daftar Siswa yang Menunggu Aktivasi:", font=("Arial", 14))
        self.label_info.pack(pady=5)

        # Frame untuk menampung list/tabel
        self.table_frame = ctk.CTkScrollableFrame(self, width=800, height=300)
        self.table_frame.pack(pady=10, padx=20)

        # Tombol Aksi
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="Kembali ke Menu", fg_color="gray", command=lambda: self.controller.show_frame("PageMenu")).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Refresh Daftar", fg_color="blue", command=self.refresh_daftar).grid(row=0, column=1, padx=10)
        # Tambahkan di bagian bawah __init__ PageAdminDaftar
        ctk.CTkButton(self, text="Mulai Training Sistem", fg_color="orange", text_color="black",
                      command=self.klik_training).pack(pady=10)

    def on_show(self):
        """Dipanggil otomatis saat halaman dibuka"""
        self.refresh_daftar()

    def refresh_daftar(self):
        # Bersihkan tabel lama
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Header Tabel
        headers = ["NIS", "Nama", "Prodi", "Aksi"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(self.table_frame, text=h, font=("Arial", 12, "bold")).grid(row=0, column=i, padx=20, pady=10)

        # Ambil data dari calon_anggota
        antrean = self.controller.db.get_semua_calon()
        
        if not antrean:
            ctk.CTkLabel(self.table_frame, text="Tidak ada antrean pendaftaran.").grid(row=1, column=0, columnspan=4, pady=20)
            return

        for idx, (id_calon, nis, nama, prodi) in enumerate(antrean):
            ctk.CTkLabel(self.table_frame, text=nis).grid(row=idx+1, column=0, padx=20, pady=5)
            ctk.CTkLabel(self.table_frame, text=nama).grid(row=idx+1, column=1, padx=20, pady=5)
            ctk.CTkLabel(self.table_frame, text=prodi).grid(row=idx+1, column=2, padx=20, pady=5)
            
            # Tombol untuk lanjut ke Scan Wajah
            btn_foto = ctk.CTkButton(self.table_frame, text="Ambil Foto & Aktifkan", width=150, height=30,
                                     command=lambda n=nis, nm=nama, p=prodi: self.mulai_aktivasi_wajah(n, nm, p))
            btn_foto.grid(row=idx+1, column=3, padx=20, pady=5)

    def mulai_aktivasi_wajah(self, nis, nama, prodi):
        import tkinter.messagebox as messagebox
        # Tanya dulu, biar admin siap
        if messagebox.askyesno("Konfirmasi", f"Mulai proses aktivasi untuk {nama}?\n\nAdmin harus menyiapkan kartu RFID baru."):
            self.proses_training_dan_aktifkan(nis, nama, prodi)

    def proses_training_dan_aktifkan(self, nis, nama, prodi):
        import tkinter.messagebox as messagebox
        
        # 1. Minta Admin Scan Kartu RFID fisik siswa
        rfid_baru = ctk.CTkInputDialog(text=f"Scan Kartu RFID untuk {nama}:", title="Link RFID").get_input()
        
        if not rfid_baru:
            return

        # 2. UPDATE DATABASE DULU untuk mendapatkan User ID (Angka)
        # Pastikan fungsi aktivasi_anggota_baru di dbManager sudah mengembalikan cursor.lastrowid
        user_id = self.controller.db.aktivasi_anggota_baru(nis, rfid_baru)
        
        if user_id:
            # 3. Buka Kamera untuk ambil dataset wajah
            cap = cv2.VideoCapture(0)
            count = 0
            
            if not os.path.exists("dataset"):
                os.makedirs("dataset")

            messagebox.showinfo("Instruksi", f"Data berhasil diaktifkan dengan ID: {user_id}.\nKamera akan terbuka, mohon hadap kamera.")

            while True:
                ret, frame = cap.read()
                if not ret: break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.controller.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    count += 1
                    
                    # --- OPTIMASI: RESIZE WAJAH AGAR RINGAN ---
                    # Kita potong area wajah saja dan perkecil ukurannya (misal 200x200)
                    roi_gray = gray[y:y+h, x:x+w]
                    roi_gray = cv2.resize(roi_gray, (200, 200)) 
                    
                    # Simpan menggunakan format: User.[ID_ANGKA].[COUNT].jpg
                    file_path = f"dataset/User.{user_id}.{count}.jpg"
                    cv2.imwrite(file_path, roi_gray)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.putText(frame, f"Foto: {count}/20", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow("Aktivasi Wajah - " + nama, frame)
                
                # Kita ambil 20 foto (bisa dikurangi ke 15 jika mau lebih cepat)
                if cv2.waitKey(1) & 0xFF == ord('q') or count >= 20:
                    break
            
            cap.release()
            cv2.destroyAllWindows()

            if count >= 20:
                messagebox.showinfo("Berhasil", f"Wajah {nama} berhasil direkam!\n\nPENTING: Klik tombol 'Mulai Training Sistem' agar siswa bisa login.")
                self.refresh_daftar()
            else:
                messagebox.showwarning("Peringatan", "Foto kurang dari 20, mungkin pengenalan wajah akan kurang akurat.")
                self.refresh_daftar()
        else:
            messagebox.showerror("Error", "Gagal mengaktifkan data di Database.")
            
    def klik_training(self):
        hasil = self.controller.jalankan_training_wajah()
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Info Training", hasil)
        
# --- 4.1 PAGE: ADMIN KELOLA BUKU ---
class PageAdminBuku(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Grid Layout: Kolom 0 untuk Form, Kolom 1 untuk Tabel
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- LEFT FRAME: FORM INPUT ---
        form_frame = ctk.CTkFrame(self, width=300)
        form_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(form_frame, text="TAMBAH BUKU BARU", font=("Arial", 18, "bold")).pack(pady=10)

        self.ent_barcode = ctk.CTkEntry(form_frame, placeholder_text="Barcode / Kode Buku")
        self.ent_barcode.pack(fill="x", padx=20, pady=5)

        self.ent_judul = ctk.CTkEntry(form_frame, placeholder_text="Judul Buku")
        self.ent_judul.pack(fill="x", padx=20, pady=5)

        self.ent_penulis = ctk.CTkEntry(form_frame, placeholder_text="Penulis")
        self.ent_penulis.pack(fill="x", padx=20, pady=5)

        self.ent_penerbit = ctk.CTkEntry(form_frame, placeholder_text="Penerbit")
        self.ent_penerbit.pack(fill="x", padx=20, pady=5)

        self.ent_stok = ctk.CTkEntry(form_frame, placeholder_text="Jumlah Stok")
        self.ent_stok.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(form_frame, text="Simpan Buku", fg_color="green", 
                      command=self.simpan_buku).pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(form_frame, text="Kembali ke Menu", fg_color="gray", 
                      command=lambda: controller.show_frame("PageMenu")).pack(fill="x", padx=20, pady=5)

        # --- RIGHT FRAME: DAFTAR BUKU ---
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(list_frame, text="DAFTAR KOLEKSI BUKU", font=("Arial", 18, "bold")).pack(pady=10)

        # Area Scroll untuk "Tabel"
        self.scroll_table = ctk.CTkScrollableFrame(list_frame)
        self.scroll_table.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Header Tabel
        header = ctk.CTkFrame(self.scroll_table, fg_color="gray30")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Barcode", width=100).grid(row=0, column=0)
        ctk.CTkLabel(header, text="Judul", width=200).grid(row=0, column=1)
        ctk.CTkLabel(header, text="Stok", width=50).grid(row=0, column=2)

    def on_show(self):
        """Dipanggil setiap kali halaman dibuka"""
        self.refresh_tabel()

    def refresh_tabel(self):
        """Mengosongkan dan mengisi ulang daftar buku dari DB"""
        for widget in self.scroll_table.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "gray30":
                widget.destroy()

        semua_buku = self.controller.db.get_all_buku()
        for buku in semua_buku:
            row = ctk.CTkFrame(self.scroll_table)
            row.pack(fill="x", pady=1)
            
            barcode = buku[0]
            judul = buku[1]
            penulis = buku[2] if len(buku) > 2 else "" 
            stok = buku[4] if len(buku) > 4 else 1     

            ctk.CTkLabel(row, text=barcode, width=100).grid(row=0, column=0) 
            ctk.CTkLabel(row, text=judul, width=200).grid(row=0, column=1) 
            ctk.CTkLabel(row, text=str(stok), width=50).grid(row=0, column=2) 
            
            # --- INI DIA FRAME TOMBOL EDIT & HAPUS ---
            frame_aksi = ctk.CTkFrame(row, fg_color="transparent")
            frame_aksi.grid(row=0, column=3, padx=5)

            ctk.CTkButton(frame_aksi, text="Edit", fg_color="#E5B800", text_color="black", hover_color="#C49A00", width=40,
                          command=lambda b=barcode, j=judul, p=penulis, s=stok: self.popup_edit_buku(b, j, p, s)).pack(side="left", padx=2)

            ctk.CTkButton(frame_aksi, text="X", width=30, fg_color="red", 
                          command=lambda b=barcode: self.hapus_buku(b)).pack(side="left", padx=2)

    # --- INI FUNGSI POPUP ---
    def popup_edit_buku(self, barcode, judul_lama, penulis_lama, stok_lama):
        popup = ctk.CTkToplevel(self)
        popup.title("Edit Data Buku")
        popup.geometry("400x420")
        popup.attributes("-topmost", True) 
        popup.grab_set() 

        ctk.CTkLabel(popup, text=f"Edit Buku: {barcode}", font=("Arial", 18, "bold")).pack(pady=20)

        ctk.CTkLabel(popup, text="Judul Buku:").pack(anchor="w", padx=40)
        ent_judul = ctk.CTkEntry(popup, width=320)
        ent_judul.pack(pady=5)
        ent_judul.insert(0, judul_lama) 

        # PERBAIKAN: Ganti top=10 menjadi pady=(10, 0)
        ctk.CTkLabel(popup, text="Penulis:").pack(anchor="w", padx=40, pady=(10, 0))
        ent_penulis = ctk.CTkEntry(popup, width=320)
        ent_penulis.pack(pady=5)
        ent_penulis.insert(0, penulis_lama)

        # PERBAIKAN: Ganti top=10 menjadi pady=(10, 0)
        ctk.CTkLabel(popup, text="Jumlah Stok:").pack(anchor="w", padx=40, pady=(10, 0))
        ent_stok = ctk.CTkEntry(popup, width=320)
        ent_stok.pack(pady=5)
        ent_stok.insert(0, str(stok_lama))

        def simpan_perubahan():
            j_baru = ent_judul.get()
            p_baru = ent_penulis.get()
            try:
                s_baru = int(ent_stok.get())
            except ValueError:
                s_baru = 1 
                
            if j_baru:
                sukses = self.controller.db.update_buku(barcode, j_baru, p_baru, s_baru)
                if sukses:
                    popup.destroy() 
                    self.refresh_tabel() 
            else:
                ctk.CTkLabel(popup, text="Judul tidak boleh kosong!", text_color="red").pack()

        ctk.CTkButton(popup, text="Simpan Perubahan", fg_color="green", command=simpan_perubahan).pack(pady=30)

        def simpan_perubahan():
            j_baru = ent_judul.get()
            p_baru = ent_penulis.get()
            try:
                s_baru = int(ent_stok.get())
            except ValueError:
                s_baru = 1 
                
            if j_baru:
                sukses = self.controller.db.update_buku(barcode, j_baru, p_baru, s_baru)
                if sukses:
                    popup.destroy() 
                    self.refresh_tabel() 
            else:
                ctk.CTkLabel(popup, text="Judul tidak boleh kosong!", text_color="red").pack()

        ctk.CTkButton(popup, text="Simpan Perubahan", fg_color="green", command=simpan_perubahan).pack(pady=30)

    def simpan_buku(self):
        barcode = self.ent_barcode.get()
        judul = self.ent_judul.get()
        penulis = self.ent_penulis.get()
        penerbit = self.ent_penerbit.get()
        stok = self.ent_stok.get()

        if barcode and judul and stok:
            sukses = self.controller.db.add_buku(barcode, judul, penulis, penerbit, stok)
            if sukses:
                # Bersihkan input
                self.ent_barcode.delete(0, 'end')
                self.ent_judul.delete(0, 'end')
                self.ent_stok.delete(0, 'end')
                self.refresh_tabel()
                print("Buku Berhasil Ditambah!")
        else:
            print("Lengkapi data!")

    def hapus_buku(self, barcode):
        if self.controller.db.delete_buku(barcode):
            self.refresh_tabel()               

# --- 6. PAGE: PEMINJAMAN BUKU ---
class PagePeminjaman(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.buku_aktif = None # Menyimpan data buku yang sedang di-scan
        
        ctk.CTkLabel(self, text="SISTEM PEMINJAMAN BUKU", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Frame Pencarian
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(pady=10)
        
        self.ent_barcode = ctk.CTkEntry(search_frame, placeholder_text="Scan/Ketik Barcode Buku", width=250)
        self.ent_barcode.grid(row=0, column=0, padx=10, pady=10)
        
        btn_cari = ctk.CTkButton(search_frame, text="Cari Buku", command=self.cari_buku)
        btn_cari.grid(row=0, column=1, padx=10, pady=10)
        
        # Label Info Buku
        self.lbl_info = ctk.CTkLabel(self, text="Silahkan scan barcode buku yang ingin dipinjam.", font=("Arial", 16))
        self.lbl_info.pack(pady=20)
        
        # Tombol Aksi
        self.btn_pinjam = ctk.CTkButton(self, text="Konfirmasi Pinjam", fg_color="green", font=("Arial", 16, "bold"),
                                        command=self.proses_pinjam)
        # Tombol pinjam disembunyikan sampai buku ditemukan
        self.btn_pinjam.pack_forget() 
        
        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="red", 
                      command=self.go_back).pack(pady=20)

    def cari_buku(self):
        barcode = self.ent_barcode.get().strip()
        buku = self.controller.db.get_buku_by_barcode(barcode)
        
        if buku:
            self.buku_aktif = buku
            stok = int(buku[4]) # Sesuai index stok di tabel buku
            
            info_text = f"Judul: {buku[1]}\nPenulis: {buku[2]}\nPenerbit: {buku[3]}\nStok Tersedia: {stok}"
            self.lbl_info.configure(text=info_text, text_color="white")
            
            if stok > 0:
                self.btn_pinjam.pack(pady=10) # Munculkan tombol jika stok ada
            else:
                self.lbl_info.configure(text=info_text + "\n\nMAAF, STOK BUKU HABIS!", text_color="orange")
                self.btn_pinjam.pack_forget()
        else:
            self.buku_aktif = None
            self.lbl_info.configure(text="BUKU TIDAK DITEMUKAN!", text_color="red")
            self.btn_pinjam.pack_forget()

    def proses_pinjam(self):
        if not self.controller.current_user or not self.buku_aktif:
            return
            
        rfid_user = self.controller.current_user[0] 
        barcode = self.buku_aktif[0] 
        
        # Panggil fungsi yang baru diupdate
        hasil = self.controller.db.pinjam_buku(rfid_user, barcode)
        
        if hasil == "SUKSES":
            self.lbl_info.configure(text=f"BERHASIL MEMINJAM:\n{self.buku_aktif[1]}", text_color="green")
            self.btn_pinjam.pack_forget()
            self.ent_barcode.delete(0, 'end')
            self.buku_aktif = None
            
        elif hasil == "DIBLOKIR":
            self.lbl_info.configure(text="AKSES DITOLAK!\nAkun Anda diblokir.\nSilakan hubungi Admin.", text_color="red")
            self.btn_pinjam.pack_forget()
            
        # INI UNTUK LIMIT BUKU 
        elif hasil == "LIMIT":
            self.lbl_info.configure(text="MAAF, BATAS MAKSIMAL TERCAPAI!\nAnda sudah meminjam 3 buku.\nKembalikan buku terlebih dahulu.", text_color="orange")
            self.btn_pinjam.pack_forget()
            
        # INI KHUSUS UNTUK STOK HABIS 
        elif hasil == "HABIS":
            self.lbl_info.configure(text="STOK BUKU HABIS!\nMaaf, buku ini sedang tidak tersedia.", text_color="red")
            self.btn_pinjam.pack_forget()
            
        else:
            self.lbl_info.configure(text="TERJADI KESALAHAN SISTEM!", text_color="red")

    def go_back(self):
        self.ent_barcode.delete(0, 'end')
        self.lbl_info.configure(text="Silahkan scan barcode buku yang ingin dipinjam.", text_color="white")
        self.btn_pinjam.pack_forget()
        self.buku_aktif = None
        self.controller.show_frame("PageMenu")
        
    # --- 7. PAGE: PENGEMBALIAN BUKU ---
class PagePengembalian(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.transaksi_aktif = None # Menyimpan data transaksi yang sedang dicek
        self.buku_aktif = None
        
        ctk.CTkLabel(self, text="SISTEM PENGEMBALIAN BUKU", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Frame Pencarian
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(pady=10)
        
        self.ent_barcode = ctk.CTkEntry(search_frame, placeholder_text="Scan/Ketik Barcode Buku", width=250)
        self.ent_barcode.grid(row=0, column=0, padx=10, pady=10)
        
        btn_cari = ctk.CTkButton(search_frame, text="Cek Buku", command=self.cek_buku)
        btn_cari.grid(row=0, column=1, padx=10, pady=10)
        
        # Label Info
        self.lbl_info = ctk.CTkLabel(self, text="Silahkan scan barcode buku yang ingin dikembalikan.", font=("Arial", 16))
        self.lbl_info.pack(pady=20)
        
        # Tombol Aksi
        self.btn_kembali = ctk.CTkButton(self, text="Konfirmasi Pengembalian", fg_color="green", font=("Arial", 16, "bold"),
                                        command=self.proses_kembali)
        self.btn_kembali.pack_forget() 
        
        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="red", 
                      command=self.go_back).pack(pady=20)

    def cek_buku(self):
        if not self.controller.current_user:
            return
        
        barcode = self.ent_barcode.get().strip()
        rfid_user = self.controller.current_user[0]
        
        # Cek apakah buku ini beneran dipinjam oleh user tersebut
        transaksi = self.controller.db.get_transaksi_aktif(rfid_user, barcode)
        
        if transaksi:
            buku = self.controller.db.get_buku_by_barcode(barcode)
            self.transaksi_aktif = transaksi
            self.buku_aktif = buku
            
            info_text = f"Buku Ditemukan!\nJudul: {buku[1]}\nTanggal Pinjam: {transaksi[1]}"
            self.lbl_info.configure(text=info_text, text_color="white")
            self.btn_kembali.pack(pady=10)
        else:
            self.transaksi_aktif = None
            self.buku_aktif = None
            self.lbl_info.configure(text="TIDAK ADA DATA PEMINJAMAN AKTIF UNTUK BUKU INI!", text_color="red")
            self.btn_kembali.pack_forget()

    def proses_kembali(self):
        if not self.controller.current_user or not self.transaksi_aktif:
            return
            
        rfid_user = self.controller.current_user[0]
        barcode = self.buku_aktif[0]
        id_transaksi = self.transaksi_aktif[0]
        tgl_pinjam_str = self.transaksi_aktif[1] # Ambil tanggal pinjam dari data transaksi aktif
        
        # Jalankan fungsi dan ambil 3 outputnya (status_sukses, jumlah_denda, selisih_hari)
        sukses, denda, lama_pinjam = self.controller.db.kembalikan_buku(rfid_user, barcode, id_transaksi, tgl_pinjam_str)
        
        if sukses:
            # Teks default jika tidak ada denda
            pesan_sukses = f"BERHASIL MENGEMBALIKAN:\n{self.buku_aktif[1]}\nLama Pinjam: {lama_pinjam} hari"
            warna_teks = "green"
            
            # Jika ternyata ada denda, ubah pesan dan warnanya!
            if denda > 0:
                pesan_sukses += f"\n\nTERLAMBAT MENGEMBALIKAN!\nTotal Denda Anda: Rp {denda:,}"
                warna_teks = "orange" # Warna peringatan
                
            self.lbl_info.configure(text=pesan_sukses, text_color=warna_teks)
            self.btn_kembali.pack_forget()
            self.ent_barcode.delete(0, 'end')
            self.transaksi_aktif = None
            self.buku_aktif = None
        else:
            self.lbl_info.configure(text="GAGAL MENGEMBALIKAN BUKU!", text_color="red")

    def go_back(self):
        self.ent_barcode.delete(0, 'end')
        self.lbl_info.configure(text="Silahkan scan barcode buku yang ingin dikembalikan.", text_color="white")
        self.btn_kembali.pack_forget()
        self.transaksi_aktif = None
        self.buku_aktif = None
        self.controller.show_frame("PageMenu")
        
# --- 8. PAGE: RIWAYAT USER ---
class PageRiwayatUser(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="RIWAYAT PEMINJAMAN SAYA", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Area Scroll untuk "Tabel" Riwayat
        self.scroll_table = ctk.CTkScrollableFrame(self, width=700, height=350)
        self.scroll_table.pack(pady=10)
        
        # Header Tabel
        header = ctk.CTkFrame(self.scroll_table, fg_color="gray30")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Judul Buku", width=300, anchor="w").grid(row=0, column=0, padx=10)
        ctk.CTkLabel(header, text="Tgl Pinjam", width=150).grid(row=0, column=1)
        ctk.CTkLabel(header, text="Status / Tgl Kembali", width=150).grid(row=0, column=2)

        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="red", 
                      command=lambda: self.controller.show_frame("PageMenu")).pack(pady=20)

    def on_show(self):
        """Dipanggil setiap kali halaman riwayat dibuka untuk refresh data"""
        # Hapus data lama yang ada di tampilan
        for widget in self.scroll_table.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "gray30":
                widget.destroy()

        # Ambil data user yang sedang login
        if not self.controller.current_user:
            return
            
        rfid_user = self.controller.current_user[0]
        riwayat = self.controller.db.get_riwayat_user(rfid_user)
        
        # Tampilkan data ke dalam tabel
        for baris in riwayat:
            row = ctk.CTkFrame(self.scroll_table)
            row.pack(fill="x", pady=1)
            
            judul = baris[0]
            tgl_pinjam = baris[1][:10] if baris[1] else "-" # Ambil tanggalnya saja (YYYY-MM-DD)
            tgl_kembali = baris[2]
            
            # Cek status: Kalau tgl_kembali kosong (None), berarti masih dipinjam
            if tgl_kembali is None:
                status_text = "SEDANG DIPINJAM"
                warna_status = "orange"
            else:
                status_text = tgl_kembali[:10] # Tampilkan tanggal kembalinya
                warna_status = "green"
            
            ctk.CTkLabel(row, text=judul, width=300, anchor="w").grid(row=0, column=0, padx=10)
            ctk.CTkLabel(row, text=tgl_pinjam, width=150).grid(row=0, column=1)
            ctk.CTkLabel(row, text=status_text, width=150, text_color=warna_status).grid(row=0, column=2)

# --- 9. PAGE: ADMIN LAPORAN TRANSAKSI ---
class PageAdminLaporan(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="LAPORAN SEMUA TRANSAKSI", font=("Arial", 24, "bold")).pack(pady=20)
        
        # Area Scroll untuk "Tabel" Laporan
        self.scroll_table = ctk.CTkScrollableFrame(self, width=800, height=350)
        self.scroll_table.pack(pady=10)
        
        # Header Tabel
        header = ctk.CTkFrame(self.scroll_table, fg_color="gray30")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Nama Peminjam", width=200, anchor="w").grid(row=0, column=0, padx=5)
        ctk.CTkLabel(header, text="Judul Buku", width=250, anchor="w").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(header, text="Tgl Pinjam", width=120).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(header, text="Status", width=120).grid(row=0, column=3, padx=5)

        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="red", 
                      command=lambda: self.controller.show_frame("PageMenu")).pack(pady=20)

    # --- INI FUNGSI YANG HARUS ADA DI DALAM KELAS INI ---
    def on_show(self):
        for widget in self.scroll_table.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "gray30":
                widget.destroy()

        laporan = self.controller.db.get_semua_laporan()
        if not laporan: return
        
        for baris in laporan:
            row = ctk.CTkFrame(self.scroll_table)
            row.pack(fill="x", pady=1)
            
            nama = baris[0]
            judul = baris[1]
            tgl_pinjam = baris[2][:10] if baris[2] else "-"
            tgl_kembali = baris[3]
            
            # --- STATUS SUDAH DIPERBAIKI ---
            if tgl_kembali is None:
                status_text = "DIPINJAM"
                warna_status = "orange"
            else:
                status_text = "DIKEMBALIKAN" # <-- Tidak lagi pakai tanggal
                warna_status = "green"
            
            ctk.CTkLabel(row, text=nama, width=200, anchor="w").grid(row=0, column=0, padx=5)
            ctk.CTkLabel(row, text=judul, width=250, anchor="w").grid(row=0, column=1, padx=5)
            ctk.CTkLabel(row, text=tgl_pinjam, width=120).grid(row=0, column=2, padx=5)
            ctk.CTkLabel(row, text=status_text, width=120, text_color=warna_status).grid(row=0, column=3, padx=5)
        
# --- 9. PAGE: ADMIN LAPORAN TRANSAKSI ---
class PageAdminLaporan(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="LAPORAN SEMUA TRANSAKSI", font=("Arial", 24, "bold")).pack(pady=20)
        
        self.scroll_table = ctk.CTkScrollableFrame(self, width=800, height=350)
        self.scroll_table.pack(pady=10)
        
        header = ctk.CTkFrame(self.scroll_table, fg_color="gray30")
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Nama Peminjam", width=200, anchor="w").grid(row=0, column=0, padx=5)
        ctk.CTkLabel(header, text="Judul Buku", width=250, anchor="w").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(header, text="Tgl Pinjam", width=120).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(header, text="Status", width=120).grid(row=0, column=3, padx=5)

        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="red", 
                      command=lambda: self.controller.show_frame("PageMenu")).pack(pady=20)

    # on_show LAPORAN sekarang BERADA DI TEMPAT YANG BENAR
    def on_show(self):
        for widget in self.scroll_table.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("fg_color") != "gray30":
                widget.destroy()

        laporan = self.controller.db.get_semua_laporan()
        if not laporan: return
        
        for baris in laporan:
            row = ctk.CTkFrame(self.scroll_table)
            row.pack(fill="x", pady=1)
            
            nama = baris[0]
            judul = baris[1]
            tgl_pinjam = baris[2][:10] if baris[2] else "-"
            tgl_kembali = baris[3]
            
            # --- STATUS SUDAH DIPERBAIKI --- 
            if tgl_kembali is None:
                status_text = "DIPINJAM"
                warna_status = "orange"
            else:
                status_text = "DIKEMBALIKAN" # <-- Tidak lagi pakai tanggal
                warna_status = "green"
            
            ctk.CTkLabel(row, text=nama, width=200, anchor="w").grid(row=0, column=0, padx=5)
            ctk.CTkLabel(row, text=judul, width=250, anchor="w").grid(row=0, column=1, padx=5)
            ctk.CTkLabel(row, text=tgl_pinjam, width=120).grid(row=0, column=2, padx=5)
            ctk.CTkLabel(row, text=status_text, width=120, text_color=warna_status).grid(row=0, column=3, padx=5)


# --- 10. PAGE: ADMIN KELOLA DENDA ---
class PageAdminDenda(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="KELOLA DENDA & BLOKIR ANGGOTA", font=("Arial", 24, "bold"), text_color="red").pack(pady=20)
        
        self.scroll_table = ctk.CTkScrollableFrame(self, width=700, height=350)
        self.scroll_table.pack(pady=10)
        
        # PERBAIKAN 1: Jadikan header sebagai self.header
        self.header = ctk.CTkFrame(self.scroll_table, fg_color="gray30")
        self.header.pack(fill="x", pady=2)
        ctk.CTkLabel(self.header, text="RFID / NISN", width=150).grid(row=0, column=0, padx=5)
        ctk.CTkLabel(self.header, text="Nama Anggota", width=250, anchor="w").grid(row=0, column=1, padx=5)
        ctk.CTkLabel(self.header, text="Total Denda", width=150).grid(row=0, column=2, padx=5)
        ctk.CTkLabel(self.header, text="Aksi", width=120).grid(row=0, column=3, padx=5)

        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="gray", 
                      command=lambda: self.controller.show_frame("PageMenu")).pack(pady=20)

    def on_show(self):
        self.refresh_data()

    def refresh_data(self):
        # PERBAIKAN 2: Sapu bersih SEMUA widget (Label maupun Frame) KECUALI self.header
        for widget in self.scroll_table.winfo_children():
            if widget != self.header:
                widget.destroy()

        data_terblokir = self.controller.db.get_user_terblokir()
        
        if not data_terblokir:
            kosong = ctk.CTkLabel(self.scroll_table, text="Sistem Aman. Tidak ada anggota yang diblokir.")
            kosong.pack(pady=20)
            return

        for baris in data_terblokir:
            row = ctk.CTkFrame(self.scroll_table)
            row.pack(fill="x", pady=1)
            
            rfid = baris[0]
            nama = baris[1]
            total_denda = baris[2]
            
            ctk.CTkLabel(row, text=rfid, width=150).grid(row=0, column=0, padx=5)
            ctk.CTkLabel(row, text=nama, width=250, anchor="w").grid(row=0, column=1, padx=5)
            ctk.CTkLabel(row, text=f"Rp {total_denda:,}", width=150, text_color="orange").grid(row=0, column=2, padx=5)
            
            ctk.CTkButton(row, text="Lunasi (Unblock)", fg_color="green", width=120,
                          command=lambda r=rfid: self.proses_lunasi(r)).grid(row=0, column=3, padx=5)

    def proses_lunasi(self, rfid):
        sukses = self.controller.db.lunasi_denda(rfid)
        if sukses:
            self.refresh_data()

# --- 5. MAIN CONTROLLER ---
class SmartLibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Smart Self-Library System")
        self.geometry("1024x600")
        
        self.db = DBManager() # Inisialisasi DBManager
        self.face_cascade = cv2.CascadeClassifier("face_ref.xml")
        self.current_user = None 
        
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # masukkan PageLanding, PageLogin, dan PageAktivasi
        for F in (PageLanding, PageLogin, PageAktivasi, PageFaceAuth, PageMenu, PageAdminDaftar, PageAdminBuku,  PagePeminjaman, PagePengembalian, PageRiwayatUser, PageAdminLaporan, PageAdminDenda):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Set layar pertama yang muncul adalah PageLanding (Screensaver)
        self.show_frame("PageLanding")
        
    def jalankan_training_wajah(self):
        import numpy as np
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        # Kita tidak butuh detector lagi di sini karena gambar di dataset sudah berbentuk wajah (hasil crop)
        
        path = 'dataset'
        if not os.path.exists(path):
            return "Folder dataset tidak ditemukan!"

        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        faceSamples = []
        ids = []

        for imagePath in imagePaths:
            try:
                # Buka gambar dan pastikan dalam mode L (Grayscale)
                PIL_img = Image.open(imagePath).convert('L') 
                img_numpy = np.array(PIL_img, 'uint8')
                
                # Format file baru: User.[USER_ID].[COUNT].jpg
                # Ambil bagian USER_ID (indeks ke-1)
                user_id = int(os.path.split(imagePath)[-1].split(".")[1])

                faceSamples.append(img_numpy)
                ids.append(user_id)
            except Exception as e:
                print(f"Gagal memproses {imagePath}: {e}")
                continue

        if len(faceSamples) > 0:
            recognizer.train(faceSamples, np.array(ids))
            # Simpan hasil belajar ke file trainer.yml
            recognizer.write('trainer.yml') 
            return f"Sukses! {len(set(ids))} wajah anggota telah dikenali sistem."  
        return "Gagal: Tidak ada data wajah yang valid."

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        
        # Jika halaman memiliki fungsi 'on_show', jalankan (untuk auto-focus rfid)
        if hasattr(frame, "on_show"):
            frame.on_show()

if __name__ == "__main__":
    app = SmartLibraryApp()
    app.mainloop()