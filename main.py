import customtkinter as ctk
import cv2
from PIL import Image, ImageTk
import os
from dbManager import DBManager # Import class dari file terpisah
import pandas as pd # Pastikan sudah install: pip install pandas openpyxl
from tkinter import filedialog, messagebox
from datetime import datetime
import win32print
import textwrap



# --- 1. PAGE: LANDING PAGE (LAYAR AWAL / MENU UTAMA & PRESENSI) ---
class PageLanding(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Menggunakan grid row/column weight untuk menengahkan konten secara otomatis
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1) # Ubah ke 7 karena jumlah baris bertambah
        self.grid_columnconfigure(0, weight=1)

        # --- JUDUL ---
        ctk.CTkLabel(self, text="SELAMAT DATANG DI", font=("Arial", 22)).grid(row=1, column=0, pady=(0, 5))
        ctk.CTkLabel(self, text="SMART LIBRARY SYSTEM", font=("Arial", 40, "bold"), text_color="#3498db").grid(row=2, column=0, pady=(0, 10))
        
        # --- INFO PRESENSI ---
        ctk.CTkLabel(self, text="Silakan Tap Kartu Pelajar Anda untuk Presensi Kunjungan", font=("Arial", 16), text_color="gray").grid(row=3, column=0, pady=(0, 20))

        # --- INPUT RFID PRESENSI ---
        self.ent_rfid = ctk.CTkEntry(self, placeholder_text="Tap RFID di sini...", width=300, height=45, font=("Arial", 18), justify="center")
        self.ent_rfid.grid(row=4, column=0, pady=(0, 10))
        self.ent_rfid.bind("<Return>", self.proses_presensi)

        # --- AREA STATUS PRESENSI ---
        self.lbl_status = ctk.CTkLabel(self, text="", font=("Arial", 20, "bold"))
        self.lbl_status.grid(row=5, column=0, pady=(0, 30))

        # --- FRAME TOMBOL MASUK/AKTIVASI ---
        frame_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_btn.grid(row=6, column=0)

        # Tombol Raksasa Modern (Menggunakan CTkButton dengan rounded corners)
        btn_login = ctk.CTkButton(frame_btn, text="LOGIN ANGGOTA\n(Masuk)", font=("Arial", 18, "bold"), 
                                  width=250, height=90, corner_radius=20, 
                                  command=lambda: self.controller.show_frame("PageLogin"))
        btn_login.pack(side="left", padx=20)

        btn_aktivasi = ctk.CTkButton(frame_btn, text="AKTIVASI AKUN\n(Pendaftaran)", font=("Arial", 18, "bold"), 
                                     width=250, height=90, corner_radius=20, fg_color="#27ae60", hover_color="#2ecc71",
                                     command=lambda: self.controller.show_frame("PageAktivasi"))
        btn_aktivasi.pack(side="left", padx=20)

    def on_show(self):
        """Reset halaman saat muncul, dan paksa kursor standby di kotak RFID"""
        self.ent_rfid.delete(0, 'end')
        self.lbl_status.configure(text="")
        self.ent_rfid.focus_force()
        
    def proses_presensi(self, event=None):
        rfid = self.ent_rfid.get().strip()
        self.ent_rfid.delete(0, 'end')

        if not rfid:
            return

        # Cek apakah dia siswa sekolah ini (Cek tabel master_siswa)
        nama_siswa = self.cek_master_siswa(rfid)
        
        if nama_siswa:
            # Gunakan fungsi catat_presensi yang ada di dbManager
            status = self.controller.db.catat_presensi(rfid, nama_siswa)
            if status == "SUKSES" or status == True:
                self.lbl_status.configure(text=f"✅ Selamat Datang, {nama_siswa}!", text_color="#2ecc71")
            elif status == "SUDAH_ABSEN":
                self.lbl_status.configure(text=f"👋 Halo lagi, {nama_siswa}!\n(Kamu sudah presensi hari ini)", text_color="#f39c12")
            else:
                self.lbl_status.configure(text="❌ Gagal mencatat ke database.", text_color="red")
        else:
            self.lbl_status.configure(text="❌ Kartu Tidak Dikenali! Harap Lapor Petugas.", text_color="#e74c3c")

        self.ent_rfid.focus_force()
        self.after(4000, lambda: self.lbl_status.configure(text=""))
        
    def cek_master_siswa(self, rfid):
        """Fungsi mengambil nama siswa dari data center sekolah"""
        import sqlite3
        try:
            conn = sqlite3.connect(self.controller.db.db_path, timeout=10)
            cursor = conn.cursor()
            # Kita cek master_siswa agar SEMUA anak sekolah bisa presensi membaca
            cursor.execute("SELECT nama FROM master_siswa WHERE rfid_id = ?", (rfid,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else None
        except Exception as e:
            print(f"Error Cek Master: {e}")
            return None

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

    def proses_rfid(self, event=None):
        rfid_data = self.entry_rfid.get().strip()
        if not rfid_data:
            return

        # Ambil data dari DB berdasarkan RFID
        user_data = self.controller.db.get_anggota_by_rfid(rfid_data)

        if user_data:
            # 1. Simpan data user yang sedang login
            self.controller.current_user = user_data
            self.entry_rfid.delete(0, 'end')
            
            # 2. Ambil ROLE dari database (Indeks ke-3)
            role = user_data[3] 
            
            # 3. PERCABANGAN LOGIKA LOGIN
            if role == "ADMIN":
                # Jika Admin, langsung tembak ke Dashboard Admin
                # (Pastikan "PageAdmin" ini sesuai dengan nama class halaman admin kamu)
                self.controller.show_frame("PageMenu") 
            else:
                # Jika USER biasa, wajib masuk ke 2FA (Scan Wajah)
                self.controller.show_frame("PageFaceAuth")
        else:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Error", "Kartu RFID tidak dikenali atau belum aktif!")
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
        self.controller.show_frame("PageMenu")

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
                    # 1. Ambil data wajah dari database
                    user_wajah = self.controller.db.get_anggota_by_id(id_hasil)
                    
                    # 2. Ambil data kartu RFID yang di-scan di halaman sebelumnya
                    # (Asumsinya kamu menyimpan data user dari RFID ke self.controller.current_user saat scan kartu)
                    user_kartu = self.controller.current_user 
                    
                    if user_wajah and user_kartu:
                        # 3. VERIFIKASI 2FA: Apakah RFID_ID Wajah == RFID_ID Kartu?
                        if user_wajah[0] == user_kartu[0]:
                            nama_user = user_wajah[1]
                            cv2.putText(frame, "VERIFIKASI BERHASIL:", (x, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            cv2.putText(frame, f"{nama_user}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                            
                            self.login_berhasil = True 
                            self.tampilkan_ke_layar(frame)
                            self.after(2000, lambda: self.sukses_login(user_wajah))
                            return 
                        else:
                            # JIKA KARTU DAN WAJAH BEDA ORANG!
                            cv2.putText(frame, "AKSES DITOLAK!", (x, y-35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            cv2.putText(frame, "Wajah & Kartu Tidak Cocok", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, "Wajah Tidak Dikenali", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            self.tampilkan_ke_layar(frame)

        if not self.login_berhasil:
            self.after(50, self.scan_wajah) # Pakai 50ms biar tidak lag

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

class PageMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # --- HEADER (Bisa Berubah Sesuai Role) ---
        self.lbl_welcome = ctk.CTkLabel(self, text="MEMUAT...", font=("Arial", 28, "bold"))
        self.lbl_welcome.pack(pady=(20, 10))

        # ==========================================
        # 1. BUNGKUSAN KHUSUS ADMIN (DASHBOARD)
        # ==========================================
        self.frame_admin = ctk.CTkFrame(self, fg_color="transparent")
        
        # Hero Metrics (Atas)
        self.frame_hero = ctk.CTkFrame(self.frame_admin, fg_color="transparent")
        self.frame_hero.pack(fill="x", padx=40, pady=10)
        
        self.stats_cards = {}
        metrics = [
            ("TOTAL STOK", "stok"), ("TOTAL JUDUL", "judul"), 
            ("ANGGOTA", "anggota"), ("DIPINJAM", "pinjam")
        ]
        for label, key in metrics:
            # Menggunakan warna Deep Muted yang kamu minta sebelumnya
            card = ctk.CTkFrame(self.frame_hero, fg_color="#1a2a3a", border_width=2, corner_radius=20, border_color="#2980b9", height=90)
            card.pack(side="left", expand=True, fill="both", padx=8)
            card.pack_propagate(False)
            
            ctk.CTkLabel(card, text=label, font=("Arial", 11, "bold"), text_color="#bdc3c7").pack(pady=(12, 0))
            self.stats_cards[key] = ctk.CTkLabel(card, text="0", font=("Arial", 30, "bold"), text_color="#ffffff")
            self.stats_cards[key].pack(expand=True)

        # Actionable Cards (Bawah)
        self.frame_actions = ctk.CTkFrame(self.frame_admin, fg_color="transparent")
        self.frame_actions.pack(expand=True, fill="both", padx=40, pady=(10, 10))
        self.frame_actions.grid_columnconfigure((0, 1, 2), weight=1, pad=15)
        self.frame_actions.grid_rowconfigure((0, 1), weight=1, pad=15)

        menu_items = [
            ("Aktivasi Anggota", "👥", "#2980b9", "PageAktivasi", "aktivasi"),      
            ("Kelola Denda", "🚨", "#c0392b", "PageAdminDenda", "blokir"),        
            ("Verifikasi Buku", "⏳", "#f39c12", "PageVerifikasi", "verifikasi"),   
            ("Kelola Buku", "📚", "#27ae60", "PageAdminBuku", None),               
            ("Pengembalian", "📥", "#8e44ad", "PagePengembalianAdmin", None),      
            ("Pusat Laporan", "📊", "#16a085", "PageAdminLaporanPresensi", None)   
        ]

        self.menu_badges = {}
        for i, (title, icon, color, page, badge_key) in enumerate(menu_items):
            row, col = divmod(i, 3)
            
            card = ctk.CTkFrame(self.frame_actions, fg_color=color, corner_radius=20, cursor="hand2")
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=8)
            
            card.bind("<Enter>", lambda e, c=card: c.configure(border_width=3, border_color="white"))
            card.bind("<Leave>", lambda e, c=card: c.configure(border_width=0))
            card.bind("<Button-1>", lambda e, p=page: self.controller.show_frame(p))
            
            lbl_icon = ctk.CTkLabel(card, text=icon, font=("Arial", 45), text_color="white")
            lbl_icon.place(relx=0.5, rely=0.4, anchor="center")
            lbl_icon.bind("<Button-1>", lambda e, p=page: self.controller.show_frame(p))

            lbl_text = ctk.CTkLabel(card, text=title.upper(), font=("Arial", 14, "bold"), text_color="white")
            lbl_text.place(relx=0.5, rely=0.75, anchor="center")
            lbl_text.bind("<Button-1>", lambda e, p=page: self.controller.show_frame(p))
            
            if badge_key:
                badge_frame = ctk.CTkFrame(card, fg_color="white", corner_radius=10)
                badge_frame.place(relx=0.95, rely=0.08, anchor="ne")
                
                self.menu_badges[badge_key] = ctk.CTkLabel(
                    badge_frame, text="...", text_color="black", 
                    font=("Arial", 10, "bold"), padx=10, pady=2
                )
                self.menu_badges[badge_key].pack()

        # ==========================================
        # 2. BUNGKUSAN KHUSUS USER / SISWA
        # ==========================================
        self.frame_user = ctk.CTkFrame(self, fg_color="transparent")
        
        # Tombol-tombol untuk siswa (Dibuat besar dan di tengah)
        ctk.CTkButton(self.frame_user, text="📥 Pinjam Buku Baru", width=300, height=80, font=("Arial", 20, "bold"),
                      command=lambda: self.controller.show_frame("PagePeminjaman")).pack(pady=15)
                      
        ctk.CTkButton(self.frame_user, text="📖 Riwayat Peminjaman", width=300, height=80, font=("Arial", 20, "bold"), 
                      fg_color="#8e44ad", hover_color="#9b59b6",
                      command=lambda: self.controller.show_frame("PageRiwayatUser")).pack(pady=15)
                      
        ctk.CTkButton(self.frame_user, text="❓ Cara Mengembalikan", width=300, height=80, font=("Arial", 20, "bold"), 
                      fg_color="#f39c12", hover_color="#e67e22",
                      command=self.tutorial_pengembalian).pack(pady=15)

        # ==========================================
        # 3. TOMBOL LOGOUT (UMUM UNTUK SEMUA)
        # ==========================================
        # Menggunakan pack(side="bottom") agar dia SELALU menempel di dasar layar dan tidak tertimpa menu
        self.btn_logout = ctk.CTkButton(self, text="LOGOUT SISTEM", fg_color="#34495e", hover_color="#2c3e50", 
                                        height=45, width=200, font=("Arial", 14, "bold"),
                                        command=self.logout)
        self.btn_logout.pack(side="bottom", pady=(0, 30))

    def tutorial_pengembalian(self):
        from tkinter import messagebox
        messagebox.showinfo("Informasi Pengembalian", "Silakan bawa buku yang ingin dikembalikan langsung ke Meja Petugas Perpustakaan untuk diinspeksi fisiknya.")

    def logout(self):
        self.controller.current_user = None
        self.controller.show_frame("PageLanding") # Arahkan kembali ke layar depan/presensi

    def on_show(self):
        if not self.controller.current_user:
            return

        user_name = self.controller.current_user[1]
        role = str(self.controller.current_user[-1]).strip().upper()

        # --- LOGIKA PENAMPILAN SESUAI ROLE ---
        if role == "ADMIN":
            self.lbl_welcome.configure(text=f"PANEL ADMINISTRATOR: {user_name.upper()}", text_color="#ecf0f1")
            
            # Sembunyikan frame user, munculkan frame admin
            self.frame_user.pack_forget()
            self.frame_admin.pack(expand=True, fill="both")

            # Update Data Dashboard
            stats = self.controller.db.get_dashboard_stats()
            for key in ["stok", "judul", "anggota", "pinjam"]:
                if key in self.stats_cards:
                    self.stats_cards[key].configure(text=str(stats[key]))
                
            for key in ["aktivasi", "blokir", "verifikasi"]:
                if key in self.menu_badges:
                    val = stats[key]
                    if key == "aktivasi":
                        self.menu_badges[key].configure(text=f"📢 {val} ANTRIAN" if val > 0 else "BERSIH ✅")
                    elif key == "blokir":
                        self.menu_badges[key].configure(text=f"🚨 {val} BLOKIR" if val > 0 else "AMAN ✅")
                    elif key == "verifikasi":
                        self.menu_badges[key].configure(text=f"⏳ {val} VERIF" if val > 0 else "DONE ✅")
                        
        else: # JIKA ROLE ADALAH USER/SISWA
            self.lbl_welcome.configure(text=f"Selamat Datang, {user_name}!", text_color="#3498db")
            
            # Sembunyikan frame admin, munculkan frame user
            self.frame_admin.pack_forget()
            self.frame_user.pack(expand=True, fill="both", pady=40)

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
        
        # --- TAMBAHAN BARU: INPUT DURASI PINJAM ---
        frame_durasi = ctk.CTkFrame(form_frame, fg_color="transparent")
        frame_durasi.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_durasi, text="Batas Pinjam:").pack(side="left")

        self.var_durasi = ctk.StringVar(value="7") # Default 7 hari
        self.input_durasi = ctk.CTkOptionMenu(
            frame_durasi, values=["7", "3"], 
            variable=self.var_durasi, width=70
        )
        self.input_durasi.pack(side="left", padx=5)

        ctk.CTkLabel(frame_durasi, text="Hari").pack(side="left")

        # Tombol Info "!"
        ctk.CTkButton(
            frame_durasi, text="!", width=25, height=25, corner_radius=12,
            fg_color="#f39c12", hover_color="#e67e22", font=("Arial", 12, "bold"),
            command=self.info_durasi_pinjam
        ).pack(side="left", padx=5)

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
        # --- TAMBAHAN BARU DI POPUP: EDIT DURASI ---
        ctk.CTkLabel(popup, text="Batas Pinjam:").pack(anchor="w", padx=40, pady=(10,0))
        var_durasi_edit = ctk.StringVar(value="7") # Nanti bisa disesuaikan ambil dari DB
        sel_durasi = ctk.CTkOptionMenu(popup, values=["7", "3"], variable=var_durasi_edit, width=100)
        sel_durasi.pack(pady=5)

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
            d_baru = var_durasi_edit.get() # Ambil nilai durasi baru dari popup
            try:
                s_baru = int(ent_stok.get())
            except ValueError:
                s_baru = 1 
                
            if j_baru:
                sukses = self.controller.db.update_buku(barcode, j_baru, p_baru, s_baru, d_baru) # Pastikan fungsi update_buku di dbManager menerima parameter durasi
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
        durasi = self.var_durasi.get() # Ambil nilai dari dropdown durasi

        if barcode and judul and stok:
            sukses = self.controller.db.add_buku(barcode, judul, penulis, penerbit, stok, durasi) # Pastikan fungsi add_buku di dbManager menerima parameter durasi
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
            
    def info_durasi_pinjam(self):
        import tkinter.messagebox as messagebox
        pesan = (
            "KRITERIA BATAS PINJAM BUKU:\n\n"
            "📚 7 Hari (Reguler):\n"
            "- Buku teks standar\n"
            "- Stok lebih dari 3 eksemplar\n"
            "- Peminatnya normal/sedang\n\n"
            "🔥 3 Hari (Langka/High-Demand):\n"
            "- Buku edisi terbatas / mahal\n"
            "- Stok tinggal 1-2 eksemplar\n"
            "- Sering diantre oleh banyak siswa"
        )
        messagebox.showinfo("Info Durasi Pinjam", pesan)         

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
        self.var_kondisi = ctk.StringVar(value="Baik")

        self.dropdown_kondisi = ctk.CTkOptionMenu(
            self,
            values=["Baik", "Rusak"],
            variable=self.var_kondisi
        )
        self.dropdown_kondisi.pack(pady=5)
        
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
            
        # 🛡️ JURUS ANTI-DOUBLE CLICK: Bekukan tombol sesaat
        self.btn_pinjam.configure(state="disabled", text="Memproses... ⏳")
        self.update() # Paksa UI untuk me-refresh tulisan tombol
        
        try:
            rfid_user = self.controller.current_user[0] 
            barcode = self.buku_aktif[0] 
            kondisi = self.var_kondisi.get()

            # Panggil fungsi database
            hasil = self.controller.db.pinjam_buku(
                rfid_user,
                barcode,
                kondisi,
                ""
            )
            
            # --- LOGIKA TAMPILAN SESUAI HASIL ---
            # --- LOGIKA TAMPILAN SESUAI HASIL ---
            if hasil == "SUKSES":
                self.lbl_info.configure(text=f"BERHASIL MEMINJAM:\n{self.buku_aktif[1]}", text_color="green")
                self.btn_pinjam.pack_forget()
                self.ent_barcode.delete(0, 'end')
                
                # =========================================================
                from datetime import datetime, timedelta
                
                tgl_sekarang = datetime.now().strftime("%d-%b-%Y %H:%M")
                tgl_kembali = (datetime.now() + timedelta(days=7)).strftime("%d-%b-%Y") # Asumsi 7 hari
                
                nama_siswa = self.controller.current_user[1]
                judul_buku = self.buku_aktif[1]
                id_trx = "AUTO" 
                
                # 1. Panggil fungsi perakit teks dari CONTROLLER
                teks = self.controller.buat_teks_struk(
                    tipe="PINJAM",
                    id=id_trx,
                    nama=nama_siswa,
                    judul=judul_buku,
                    tgl=tgl_sekarang,
                    tgl_kembali=tgl_kembali
                )
                
                # 2. Munculkan Jendela Virtual Printer
                DialogStruk(self, teks)
                # =========================================================
                
                self.buku_aktif = None
                
            elif hasil == "PENDING":
                self.lbl_info.configure(
                    text="Buku dalam kondisi rusak.\nMenunggu verifikasi admin.",
                    text_color="orange"
                )
                self.btn_pinjam.pack_forget()
                self.ent_barcode.delete(0, 'end')
                self.buku_aktif = None
                
            elif hasil == "DIBLOKIR":
                self.lbl_info.configure(text="AKSES DITOLAK!\nAkun Anda diblokir.\nSilakan hubungi Admin.", text_color="red")
                self.btn_pinjam.pack_forget()
                
            elif hasil == "LIMIT":
                self.lbl_info.configure(text="MAAF, BATAS MAKSIMAL TERCAPAI!\nAnda sudah meminjam 3 buku.\nKembalikan buku terlebih dahulu.", text_color="orange")
                self.btn_pinjam.pack_forget()
                
            elif hasil == "HABIS":
                self.lbl_info.configure(text="STOK BUKU HABIS!\nMaaf, buku ini sedang tidak tersedia.", text_color="red")
                self.btn_pinjam.pack_forget()
                
            else:
                self.lbl_info.configure(text="TERJADI KESALAHAN SISTEM!", text_color="red")

        except Exception as e:
            # Jika ada error tidak terduga, tampilkan di layar
            self.lbl_info.configure(text=f"ERROR: {e}", text_color="red")
            
        finally:
            # 🛡️ KEMBALIKAN TOMBOL KE NORMAL
            # Apapun yang terjadi (sukses/error), tombol harus bisa diklik lagi nanti
            self.btn_pinjam.configure(state="normal", text="Simpan Peminjaman")

    def go_back(self):
        self.ent_barcode.delete(0, 'end')
        self.lbl_info.configure(text="Silahkan scan barcode buku yang ingin dipinjam.", text_color="white")
        self.btn_pinjam.pack_forget()
        self.buku_aktif = None
        self.controller.show_frame("PageMenu")
        
    # --- 7. PAGE: PENGEMBALIAN BUKU ---
class PagePengembalianAdmin(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        ctk.CTkLabel(self, text="SISTEM PENGEMBALIAN & INSPEKSI BUKU", font=("Arial", 24, "bold")).pack(pady=(20, 10))
        
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(pady=10)
        
        self.ent_rfid = ctk.CTkEntry(search_frame, placeholder_text="Scan RFID Siswa...", width=250)
        self.ent_rfid.pack(side="left", padx=10)
        ctk.CTkButton(search_frame, text="Cari Pinjaman", command=self.cari_data).pack(side="left")
        
        self.container_buku = ctk.CTkScrollableFrame(self)
        self.container_buku.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Di dalam __init__ PagePengembalianAdmin
        ctk.CTkButton(self, text="Kembali ke Menu", fg_color="#e74c3c", hover_color="#c0392b",
                    command=lambda: self.controller.show_frame("PageMenu")).pack(pady=20)
# Perhatikan di atas: tujuannya adalah "PageMenu"

    def cari_data(self):
        for widget in self.container_buku.winfo_children(): widget.destroy()
        rfid = self.ent_rfid.get().strip()
        if not rfid: return
            
        data = self.controller.db.get_pinjaman_aktif_by_rfid(rfid)
        if not data:
            ctk.CTkLabel(self.container_buku, text="Tidak ada buku yang sedang dipinjam.", font=("Arial", 14, "italic")).pack(pady=40)
            return

        for id_trans, judul, tgl_pinjam, j_tempo, k_awal, cat in data:
            card = ctk.CTkFrame(self.container_buku, fg_color="gray15")
            card.pack(fill="x", padx=10, pady=5)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(info_frame, text=judul, font=("Arial", 16, "bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"Jatuh Tempo: {j_tempo}", font=("Arial", 12), text_color="yellow", anchor="w").pack(fill="x")
            ctk.CTkLabel(info_frame, text=f"Kondisi Awal: {k_awal} ({cat if cat else '-'})", font=("Arial", 12), anchor="w").pack(fill="x")
                        # Tambahkan j=judul agar judulnya ikut terbawa ke form
            ctk.CTkButton(card, text="🔍 Inspeksi", command=lambda i=id_trans, c=card, j=judul: self.tampilkan_form(i, c, j)).pack(side="right", padx=10)

    # Tambahkan parameter 'judul' di sini
    def tampilkan_form(self, id_trans, parent_card, judul):
        for w in parent_card.winfo_children():
            if isinstance(w, ctk.CTkButton): 
                w.destroy()
            
        form_frame = ctk.CTkFrame(parent_card, fg_color="gray20")
        form_frame.pack(side="right", padx=10, pady=10)
        
        # --- BLOK KONDISI ---
        frame_kondisi = ctk.CTkFrame(form_frame, fg_color="transparent")
        frame_kondisi.pack(side="left", padx=5)
        ctk.CTkLabel(frame_kondisi, text="Kondisi Akhir:", font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w")
        var_k = ctk.StringVar(value="Sesuai Awal")
        combo_kondisi = ctk.CTkOptionMenu(frame_kondisi, values=["Sesuai Awal", "Kerusakan Baru", "Hilang"], variable=var_k, width=130)
        combo_kondisi.pack()
        
        # --- BLOK DENDA ---
        frame_denda = ctk.CTkFrame(form_frame, fg_color="transparent")
        frame_denda.pack(side="left", padx=5)
        ctk.CTkLabel(frame_denda, text="Denda Fisik (Rp):", font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w")
        ent_denda = ctk.CTkEntry(frame_denda, placeholder_text="Misal: 10000", width=110)
        ent_denda.pack()
        ent_denda.insert(0, "0")
        
        def on_kondisi_change(choice):
            if choice == "Sesuai Awal":
                ent_denda.delete(0, 'end')
                ent_denda.insert(0, "0")
                ent_denda.configure(state="disabled")
            elif choice == "Kerusakan Baru":
                ent_denda.configure(state="normal")
                ent_denda.delete(0, 'end')
                ent_denda.insert(0, "0")
            elif choice == "Hilang":
                ent_denda.configure(state="normal")
                ent_denda.delete(0, 'end')
                ent_denda.insert(0, "50000") 
                
        combo_kondisi.configure(command=on_kondisi_change)
        on_kondisi_change("Sesuai Awal")
        
        # --- TOMBOL KONFIRMASI ---
        ctk.CTkButton(
            form_frame, text="✅ Konfirmasi", fg_color="green", hover_color="#1e8449", width=100,
            command=lambda: self.proses(id_trans, var_k.get(), ent_denda.get(), judul) # Oper judul ke proses
        ).pack(side="left", padx=10, pady=(15, 0))

    # Fungsi proses yang baru (sudah cetak struk)
    def proses(self, id_trans, kondisi, denda_str, judul):
        from datetime import datetime
        denda = int(denda_str) if denda_str.isdigit() else 0
        sukses, total = self.controller.db.proses_kembali_admin(id_trans, kondisi, denda)
        
        if sukses:
            # 1. CETAK STRUK PENGEMBALIAN
            tgl_sekarang = datetime.now().strftime("%d-%b-%Y %H:%M")
            rfid_siswa = self.ent_rfid.get() # Ambil dari kotak pencarian
            
            teks = self.controller.buat_teks_struk(
                tipe="KEMBALI",
                id=id_trans,
                tgl=tgl_sekarang,
                nama=rfid_siswa,
                judul=judul,
                status_waktu="Selesai", 
                kondisi=kondisi,
                denda=total
            )
            DialogStruk(self, teks)
            
            # 2. Refresh UI
            self.ent_rfid.delete(0, 'end')
            for widget in self.container_buku.winfo_children(): 
                widget.destroy()
        
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
            
            # Ubah lambda agar mengirimkan rfid, nama, dan total_denda
            ctk.CTkButton(row, text="Lunasi (Unblock)", fg_color="green", width=120,
                          command=lambda r=rfid, n=nama, d=total_denda: self.proses_lunasi(r, n, d)).grid(row=0, column=3, padx=5)

    def proses_lunasi(self, rfid, nama, total_denda):
        from datetime import datetime
        sukses = self.controller.db.lunasi_denda(rfid)
        
        if sukses:
            # 1. CETAK STRUK PELUNASAN
            tgl_sekarang = datetime.now().strftime("%d-%b-%Y %H:%M")
            
            teks = self.controller.buat_teks_struk(
                tipe="DENDA",
                tgl=tgl_sekarang,
                nama=nama,
                keterangan="Pelunasan Tunggakan & Unblock",
                bayar=total_denda,
                sisa=0
            )
            DialogStruk(self, teks)
            
            # 2. Refresh UI
            self.refresh_data()
            
class PageVerifikasi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- BAGIAN ATAS (TOMBOL KEMBALI & JUDUL) ---
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkButton(top_frame, text="⬅ Kembali", width=80, fg_color="#e74c3c", hover_color="#c0392b",
                      command=lambda: self.controller.show_frame("PageMenu")).pack(side="left")
        
        ctk.CTkLabel(top_frame, text="VERIFIKASI PEMINJAMAN BUKU RUSAK", font=("Arial", 20, "bold")).pack(side="left", padx=20)
        
        ctk.CTkButton(top_frame, text="🔄 Segarkan", width=100, fg_color="#3498db", hover_color="#2980b9",
                      command=self.load_data).pack(side="right")

        # --- CONTAINER TABEL (Header & Data masuk sini semua) ---
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Kunci Ukuran Grid Kolom (Biar rapi abadi)
        self.table_frame.grid_columnconfigure(0, weight=0, minsize=50)   # Kolom ID
        self.table_frame.grid_columnconfigure(1, weight=1, minsize=150)  # Kolom Nama
        self.table_frame.grid_columnconfigure(2, weight=1, minsize=200)  # Kolom Judul
        self.table_frame.grid_columnconfigure(3, weight=0, minsize=160)  # Kolom Aksi

    def on_show(self):
        self.load_data()

    def load_data(self):
        # Bersihkan tabel lama (termasuk header, biar di-refresh ulang)
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # 1. BIKIN HEADER TABEL DI BARIS KE-0
        headers = ["ID", "Nama Siswa", "Judul Buku", "Aksi (Admin)"]
        for col, text in enumerate(headers):
            header_lbl = ctk.CTkLabel(self.table_frame, text=text, font=("Arial", 14, "bold"),
                                      fg_color="gray25", corner_radius=0, pady=10, padx=10, 
                                      anchor="w" if col != 3 else "center")
            header_lbl.grid(row=0, column=col, sticky="ew", padx=1, pady=(0, 5))

        # 2. AMBIL DATA DARI DATABASE
        data_pending = self.controller.db.get_transaksi_pending()

        if not data_pending:
            ctk.CTkLabel(self.table_frame, text="Tidak ada antrean verifikasi saat ini.", 
                         font=("Arial", 14, "italic")).grid(row=1, column=0, columnspan=4, pady=40)
            return

        # 3. MASUKKAN DATA KE BARIS SELANJUTNYA
        for row_idx, (id_trans, nama, judul) in enumerate(data_pending):
            current_row = row_idx + 1
            bg_color = "gray15" if current_row % 2 == 0 else "gray18" # Warna belang-belang

            # Sel ID
            ctk.CTkLabel(self.table_frame, text=str(id_trans), fg_color=bg_color, corner_radius=0, 
                         padx=10, anchor="w").grid(row=current_row, column=0, sticky="nsew", padx=1, pady=1)
            # Sel Nama
            ctk.CTkLabel(self.table_frame, text=nama, fg_color=bg_color, corner_radius=0, 
                         padx=10, anchor="w").grid(row=current_row, column=1, sticky="nsew", padx=1, pady=1)
            # Sel Judul
            ctk.CTkLabel(self.table_frame, text=judul, fg_color=bg_color, corner_radius=0, 
                         padx=10, anchor="w", wraplength=250).grid(row=current_row, column=2, sticky="nsew", padx=1, pady=1)

            # Sel Aksi (Berisi 2 Tombol)
            action_frame = ctk.CTkFrame(self.table_frame, fg_color=bg_color, corner_radius=0)
            action_frame.grid(row=current_row, column=3, sticky="nsew", padx=1, pady=1)
            action_frame.grid_columnconfigure(0, weight=1)
            action_frame.grid_columnconfigure(1, weight=1)

            btn_acc = ctk.CTkButton(action_frame, text="✅ Setuju", width=60, height=28, 
                                    fg_color="#27ae60", hover_color="#2ecc71",
                                    command=lambda i=id_trans: self.approve_peminjaman(i))
            btn_acc.grid(row=0, column=0, padx=2, pady=5)

            btn_rej = ctk.CTkButton(action_frame, text="❌ Tolak", width=60, height=28, 
                                    fg_color="#c0392b", hover_color="#e74c3c",
                                    command=lambda i=id_trans: self.reject_peminjaman(i))
            btn_rej.grid(row=0, column=1, padx=2, pady=5)

    def approve_peminjaman(self, id_trans):
        dialog = ctk.CTkInputDialog(text="Tulis Detail Kerusakan (Contoh: Hal 10 Sobek):", title="Konfirmasi Kerusakan")
        catatan_admin = dialog.get_input()
        
        if catatan_admin: 
            if self.controller.db.verifikasi_buku(id_trans, 'APPROVED', catatan_admin):
                self.load_data() # Refresh tabel

    def reject_peminjaman(self, id_trans):
        if self.controller.db.verifikasi_buku(id_trans, 'REJECTED'):
            self.load_data() # Refresh tabel
            
# 14. Page admin untuk melihat laporan presensi dan export ke Excel
class PageAdminLaporanPresensi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        ctk.CTkLabel(self, text="📊 LAPORAN KUNJUNGAN PERPUSTAKAAN", font=("Arial", 24, "bold")).pack(pady=20)

        # Frame Tombol Atas
        frame_top = ctk.CTkFrame(self, fg_color="transparent")
        frame_top.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(frame_top, text="⬅ Kembali", width=100, command=lambda: self.controller.show_frame("PageMenu")).pack(side="left")
        ctk.CTkButton(frame_top, text="📥 Export ke Excel (.xlsx)", fg_color="#27ae60", hover_color="#2ecc71", 
                      command=self.export_ke_excel).pack(side="right")

        # Area Tabel (Gunakan Scrollable Frame)
        self.table_frame = ctk.CTkScrollableFrame(self, fg_color="gray15")
        self.table_frame.pack(expand=True, fill="both", padx=20, pady=20)

    def on_show(self):
        self.refresh_table()

    def refresh_table(self):
        # Bersihkan tabel lama
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Header Tabel
        headers = ["RFID ID", "Nama Siswa", "Waktu Masuk", "Keperluan"]
        for i, h in enumerate(headers):
            lbl = ctk.CTkLabel(self.table_frame, text=h, font=("Arial", 13, "bold"), text_color="#3498db")
            lbl.grid(row=0, column=i, padx=10, pady=5, sticky="w")

        # Ambil Data MENGGUNAKAN FUNGSI YANG SUDAH ADA
        data = self.controller.db.get_log_presensi()
        
        for r_idx, row_data in enumerate(data, start=1):
            # row_data isinya: (id, rfid, nama, waktu, keperluan)
            # Kita potong mulai dari index 1 (mengabaikan index 0 / id_presensi)
            data_tampil = row_data[1:] 
            
            for c_idx, value in enumerate(data_tampil):
                lbl = ctk.CTkLabel(self.table_frame, text=str(value))
                lbl.grid(row=r_idx, column=c_idx, padx=10, pady=2, sticky="w")

    def export_ke_excel(self):
        data_mentah = self.controller.db.get_log_presensi()
        if not data_mentah:
            messagebox.showwarning("Kosong", "Tidak ada data untuk di-export!")
            return

        # Buang id_presensi untuk Excel
        data_bersih = [row[1:] for row in data_mentah]

        # Tanya lokasi simpan
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            title="Simpan Laporan Presensi"
        )

        if file_path:
            try:
                # Convert ke DataFrame Pandas
                df = pd.DataFrame(data_bersih, columns=["RFID_ID", "Nama_Siswa", "Waktu_Masuk", "Keperluan"])
                # Simpan ke Excel
                df.to_excel(file_path, index=False)
                messagebox.showinfo("Berhasil", f"Laporan berhasil disimpan di:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan file: {e}")
                
class DialogStruk(ctk.CTkToplevel):
    def __init__(self, parent, teks_struk):
        super().__init__(parent)
        self.title("Preview Struk Thermal")

        # 📐 Sesuaikan Tinggi Jendela agar muat Logo + Teks
        self.geometry("350x620") 
        self.resizable(False, False)

        self.attributes("-topmost", True)
        self.grab_set()

        # Label Judul Pop-up
        ctk.CTkLabel(self, text="📜 PREVIEW CETAK (58mm)", font=("Arial", 14, "bold")).pack(pady=10)

        # =============================================================
        # 🔥 BAGIAN 1: LOGO VIRTUAL (CUSTOMTKINTER)
        # =============================================================
        try:
            # Cari path file logo.png yang sudah Hitam Putih
            base_dir = os.path.dirname(os.path.abspath(__file__))
            path_logo = os.path.join(base_dir, 'assets', 'revisi logo smart e library-2.png') 

            if os.path.exists(path_logo):
                # Load gambar menggunakan PIL
                img_pil = Image.open(path_logo)

                # Buat objek CTkImage, tentukan ukurannya (misal lebar 250px)
                # Tinggi disesuaikan otomatis (Pillow akan menjaga aspect ratio)
                img_width = 250
                wpercent = (img_width/float(img_pil.size[0]))
                hsize = int((float(img_pil.size[1])*float(wpercent)))

                logo_ctk = ctk.CTkImage(
                    light_image=img_pil, 
                    dark_image=img_pil, # Di dark mode pun tetap gambar Hitam-Putih
                    size=(img_width, hsize)
                )

                # Tampilkan di Label
                lbl_logo = ctk.CTkLabel(self, image=logo_ctk, text="")
                lbl_logo.pack(pady=(0, 10))
            else:
                # Jika file tidak ada, jangan crash, tampilkan teks saja
                ctk.CTkLabel(self, text="[ Logo Tidak Ditemukan ]", text_color="gray").pack()

        except Exception as e:
            print(f"Gagal memuat logo virtual: {e}")
        # =============================================================

        # Kotak Teks Struk (Jangan diubah)
        self.textbox = ctk.CTkTextbox(self, width=310, height=400, font=("Courier New", 12))
        self.textbox.pack(padx=20, pady=5)
        self.textbox.insert("0.0", teks_struk)
        self.textbox.configure(state="disabled")

        # Frame Tombol Aksi (Jangan diubah)
        frame_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_btn.pack(pady=10)
        self.btn_tutup = ctk.CTkButton(frame_btn, text="Tutup & Selesai", width=120, fg_color="gray", command=self.destroy)
        self.btn_tutup.pack(side="left", padx=5)
        self.btn_cetak = ctk.CTkButton(frame_btn, text="🖨️ Cetak Fisik", width=120, fg_color="#27ae60", command=self.cetak_ke_printer)
        self.btn_cetak.pack(side="left", padx=5)

    def cetak_ke_printer(self):
        import win32print
        from tkinter import messagebox
        
        # Ubah tombol jadi "Mencetak..." biar user tahu sistem sedang bekerja
        self.btn_cetak.configure(state="disabled", text="Mencetak... ⏳")
        self.update()
        
        try:
            # 1. Cari printer default yang terhubung ke Windows
            printer_name = win32print.GetDefaultPrinter()
            hPrinter = win32print.OpenPrinter(printer_name)
            
            try:
                # 2. Mulai kirim dokumen ke mesin printer
                win32print.StartDocPrinter(hPrinter, 1, ("Struk Smart Library", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                
                # Tambahkan 5 baris kosong di bawah agar kertas naik ke atas (mudah disobek)
                teks_print = self.teks_struk + "\n\n\n\n\n"
                
                # 3. Tembakkan teks ke mesin
                win32print.WritePrinter(hPrinter, teks_print.encode('utf-8'))
                
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
                
                messagebox.showinfo("Sukses", f"Struk berhasil dicetak!\nPrinter: {printer_name}")
                
            finally:
                # 4. Wajib tutup koneksi agar printer tidak error
                win32print.ClosePrinter(hPrinter)
                
        except Exception as e:
            messagebox.showerror("Error Printer", f"Gagal mencetak!\nPastikan printer menyala.\nError: {e}")
            self.btn_cetak.configure(state="normal", text="🖨️ Coba Cetak Lagi")
                
#
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
        for F in (PageLanding, PageLogin, PageAktivasi, PageFaceAuth, PageMenu, PageAdminBuku,  PagePeminjaman, PageRiwayatUser, PageAdminLaporan, PageAdminDenda, PageVerifikasi, PagePengembalianAdmin, PageAdminLaporanPresensi):
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
            
    def buat_teks_struk(self, tipe="PINJAM", **data):
        import textwrap
        lebar = 32
        garis = "=" * lebar
        garis_tipis = "-" * lebar
        
        struk = f"{garis}\n"
        struk += "Akses Belajar".center(lebar) + "\n"
        struk += "Masa Depan Bersinar".center(lebar) + "\n"
        struk += f"{garis}\n"
        
        if tipe == "PINJAM":
            struk += f"JENIS: PEMINJAMAN\n"
            struk += f"ID TRX : {data.get('id', 'AUTO')}\n"
            struk += f"Waktu  : {data.get('tgl')}\n"
            struk += f"Siswa  : {data.get('nama')[:22]}\n"
            struk += f"{garis_tipis}\n"
            struk += "BUKU:\n"
            for line in textwrap.wrap(data.get('judul', '-'), width=lebar):
                struk += f"{line}\n"
            struk += f"\nJATUH TEMPO:\n> {data.get('tgl_kembali')} <\n"

        elif tipe == "KEMBALI":
            struk += f"JENIS: PENGEMBALIAN\n"
            struk += f"ID TRX : {data.get('id', 'AUTO')}\n"
            struk += f"Waktu  : {data.get('tgl')}\n"
            struk += f"Siswa  : {data.get('nama')[:22]}\n"
            struk += f"{garis_tipis}\n"
            struk += "BUKU DIKEMBALIKAN:\n"
            for line in textwrap.wrap(data.get('judul', '-'), width=lebar):
                struk += f"{line}\n"
            struk += f"{garis_tipis}\n"
            struk += f"Status : {data.get('status_waktu', 'Tepat Waktu')}\n"
            struk += f"Kondisi: {data.get('kondisi', 'Baik')}\n"
            if data.get('denda', 0) > 0:
                struk += f"DENDA  : Rp{data.get('denda'):,}\n"

        elif tipe == "DENDA":
            struk += f"BUKTI PEMBAYARAN DENDA\n"
            struk += f"{garis_tipis}\n"
            struk += f"Waktu  : {data.get('tgl')}\n"
            struk += f"Siswa  : {data.get('nama')[:22]}\n"
            struk += f"{garis_tipis}\n"
            struk += f"Ket: {data.get('keterangan', 'Denda Keterlambatan')}\n"
            struk += f"TOTAL BAYAR : Rp{data.get('bayar'):,}\n"
            struk += f"SISA TUNGGAKAN: Rp{data.get('sisa'):,}\n"

        struk += f"{garis_tipis}\n"
        if tipe == "PINJAM":
            struk += "Harap kembalikan tepat waktu.\n"
        elif tipe == "KEMBALI" and data.get('denda', 0) > 0:
            struk += "Segera lunasi denda Anda.\n"
        else:
            struk += "Terima kasih sudah menjaga\naset perpustakaan.\n"
            
        struk += f"{garis}\n"
        struk += "Terima Kasih".center(lebar) + "\n\n\n"
        
        return struk

if __name__ == "__main__":
    app = SmartLibraryApp()
    app.mainloop()