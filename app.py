"""
=============================================================
  Aplikasi Manajemen Data Mahasiswa
  Bahasa: Python (Flask)
  Fitur: OOP, File I/O, Sorting, Searching, Regex, Exception
  Author: Student Management System
  Time Complexity: Tercantum di setiap fungsi
=============================================================
"""

import json
import re
import os
import time
from flask import Flask, jsonify, request, render_template, session
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "mahasiswa_secret_key_2024"

# ─────────────────────────────────────────────────────────────
# KONSTANTA & KONFIGURASI
# ─────────────────────────────────────────────────────────────
DATA_FILE = "mahasiswa_data.json"
USERS_FILE = "users_data.json"

# ─────────────────────────────────────────────────────────────
# BASE CLASS — Enkapsulasi & Abstraksi
# ─────────────────────────────────────────────────────────────
class Person:
    """
    Base class (Pewarisan / Inheritance)
    Menyimpan atribut dasar seorang individu.
    """
    def __init__(self, nama: str, email: str, telepon: str):
        self._nama    = nama      # protected attribute
        self._email   = email
        self._telepon = telepon

    # ── Getter & Setter (Enkapsulasi) ──
    @property
    def nama(self):
        return self._nama

    @nama.setter
    def nama(self, value: str):
        if not value or len(value.strip()) < 2:
            raise ValueError("Nama minimal 2 karakter.")
        self._nama = value.strip()

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value: str):
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
        if not re.match(pattern, value):
            raise ValueError(f"Format email '{value}' tidak valid.")
        self._email = value.lower()

    @property
    def telepon(self):
        return self._telepon

    @telepon.setter
    def telepon(self, value: str):
        pattern = r'^(\+62|08)\d{8,12}$'
        if not re.match(pattern, value):
            raise ValueError("Nomor telepon harus diawali +62 atau 08, panjang 10-15 digit.")
        self._telepon = value

    def to_dict(self) -> dict:
        """Konversi objek ke dictionary."""
        return {
            "nama": self._nama,
            "email": self._email,
            "telepon": self._telepon,
        }

    def __repr__(self):
        return f"Person(nama={self._nama})"


# ─────────────────────────────────────────────────────────────
# MAHASISWA CLASS — Pewarisan dari Person
# ─────────────────────────────────────────────────────────────
class Mahasiswa(Person):
    """
    Kelas Mahasiswa — turunan dari Person (Inheritance).
    Menambahkan atribut spesifik mahasiswa: NIM, jurusan, angkatan, IPK.
    Polimorfisme: override to_dict() dari Person.
    """
    def __init__(self, nim: str, nama: str, email: str,
                 telepon: str, jurusan: str, angkatan: int, ipk: float):
        super().__init__(nama, email, telepon)   # panggil constructor parent
        self._nim      = nim
        self._jurusan  = jurusan
        self._angkatan = angkatan
        self._ipk      = ipk

    # ── Getter & Setter ──
    @property
    def nim(self):
        return self._nim

    @nim.setter
    def nim(self, value: str):
        pattern = r'^\d{8,12}$'
        if not re.match(pattern, value):
            raise ValueError("NIM harus terdiri dari 8–12 digit angka.")
        self._nim = value

    @property
    def jurusan(self):
        return self._jurusan

    @jurusan.setter
    def jurusan(self, value: str):
        if not value or len(value.strip()) < 3:
            raise ValueError("Nama jurusan minimal 3 karakter.")
        self._jurusan = value.strip()

    @property
    def angkatan(self):
        return self._angkatan

    @angkatan.setter
    def angkatan(self, value):
        year = int(value)
        current_year = datetime.now().year
        if year < 1990 or year > current_year:
            raise ValueError(f"Angkatan harus antara 1990 dan {current_year}.")
        self._angkatan = year

    @property
    def ipk(self):
        return self._ipk

    @ipk.setter
    def ipk(self, value):
        val = float(value)
        if val < 0.0 or val > 4.0:
            raise ValueError("IPK harus antara 0.00 dan 4.00.")
        self._ipk = round(val, 2)

    def to_dict(self) -> dict:
        """
        Polimorfisme: override to_dict() dari parent.
        Menambahkan field mahasiswa ke dict parent.
        """
        base = super().to_dict()
        base.update({
            "nim":      self._nim,
            "jurusan":  self._jurusan,
            "angkatan": self._angkatan,
            "ipk":      self._ipk,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "Mahasiswa":
        """Factory method: buat objek Mahasiswa dari dictionary."""
        return cls(
            nim=data["nim"],
            nama=data["nama"],
            email=data["email"],
            telepon=data["telepon"],
            jurusan=data["jurusan"],
            angkatan=int(data["angkatan"]),
            ipk=float(data["ipk"]),
        )

    def __repr__(self):
        return f"Mahasiswa(nim={self._nim}, nama={self._nama})"


# ─────────────────────────────────────────────────────────────
# VALIDASI INPUT — Regular Expression
# ─────────────────────────────────────────────────────────────
class Validator:
    """
    Kelas utilitas validasi menggunakan Regular Expression (Regex).
    Semua method bersifat static karena tidak butuh state instance.
    """

    @staticmethod
    def validate_nim(nim: str) -> bool:
        return bool(re.match(r'^\d{8,12}$', nim))

    @staticmethod
    def validate_nama(nama: str) -> bool:
        return bool(re.match(r'^[A-Za-z\s\'\.]{2,60}$', nama))

    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email))

    @staticmethod
    def validate_telepon(telepon: str) -> bool:
        return bool(re.match(r'^(\+62|08)\d{8,12}$', telepon))

    @staticmethod
    def validate_ipk(ipk_str: str) -> bool:
        try:
            val = float(ipk_str)
            return 0.0 <= val <= 4.0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_angkatan(angkatan_str: str) -> bool:
        try:
            year = int(angkatan_str)
            return 1990 <= year <= datetime.now().year
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_all(data: dict) -> list:
        """
        Validasi semua field sekaligus.
        Return list pesan error (kosong = valid).
        """
        errors = []
        if not Validator.validate_nim(data.get("nim", "")):
            errors.append("NIM harus terdiri dari 8–12 digit angka.")
        if not Validator.validate_nama(data.get("nama", "")):
            errors.append("Nama hanya boleh huruf, spasi, apostrof, titik (2–60 karakter).")
        if not Validator.validate_email(data.get("email", "")):
            errors.append("Format email tidak valid.")
        if not Validator.validate_telepon(data.get("telepon", "")):
            errors.append("Telepon harus diawali +62 atau 08, panjang 10-15 digit.")
        if not Validator.validate_ipk(data.get("ipk", "")):
            errors.append("IPK harus antara 0.00 – 4.00.")
        if not Validator.validate_angkatan(data.get("angkatan", "")):
            errors.append(f"Angkatan harus antara 1990 – {datetime.now().year}.")
        return errors


# ─────────────────────────────────────────────────────────────
# FILE I/O MANAGER
# ─────────────────────────────────────────────────────────────
class FileManager:
    """
    Mengelola penyimpanan & pembacaan data ke/dari file JSON.
    Try–Catch digunakan untuk penanganan error file.
    """

    @staticmethod
    def load(filepath: str) -> list:
        """
        Baca data dari file JSON.
        Time Complexity: O(n) — n = jumlah record
        """
        try:
            if not os.path.exists(filepath):
                return []
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError as e:
            raise RuntimeError(f"File JSON corrupt: {e}")
        except PermissionError:
            raise RuntimeError("Tidak ada izin membaca file.")
        except Exception as e:
            raise RuntimeError(f"Gagal membaca file: {e}")

    @staticmethod
    def save(filepath: str, data: list) -> None:
        """
        Tulis data ke file JSON.
        Time Complexity: O(n)
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except PermissionError:
            raise RuntimeError("Tidak ada izin menulis file.")
        except Exception as e:
            raise RuntimeError(f"Gagal menyimpan file: {e}")

    @staticmethod
    def load_users(filepath: str) -> dict:
        try:
            if not os.path.exists(filepath):
                # Default admin user
                default = {"admin": "admin123", "Eka Sri Rahayu": "test123"}
                FileManager.save_users(filepath, default)
                return default
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"admin": "admin123"}

    @staticmethod
    def save_users(filepath: str, users: dict) -> None:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Gagal menyimpan user: {e}")


# ─────────────────────────────────────────────────────────────
# ALGORITMA PENCARIAN
# ─────────────────────────────────────────────────────────────
class SearchEngine:
    """
    Kelas pencarian data mahasiswa.
    Mendukung: Linear Search, Binary Search, Sequential Search
    """

    @staticmethod
    def linear_search(data: list, keyword: str, field: str = "nama") -> list:
        """
        Linear Search: cari semua record yang mengandung keyword.
        Time Complexity: O(n) — selalu iterasi semua elemen
        Space Complexity: O(k) — k = jumlah hasil
        """
        keyword_lower = keyword.lower()
        results = []
        comparisons = 0
        for item in data:
            comparisons += 1
            if keyword_lower in str(item.get(field, "")).lower():
                results.append(item)
        return results, comparisons

    @staticmethod
    def binary_search(data: list, target: str, field: str = "nim") -> dict | None:
        """
        Binary Search: cari record exact match (data harus terurut).
        Time Complexity: O(log n)
        Space Complexity: O(1)
        Prasyarat: data sudah diurutkan berdasarkan field yang dicari
        """
        sorted_data = sorted(data, key=lambda x: str(x.get(field, "")).lower())
        low, high = 0, len(sorted_data) - 1
        comparisons = 0
        while low <= high:
            mid = (low + high) // 2
            comparisons += 1
            mid_val = str(sorted_data[mid].get(field, "")).lower()
            target_lower = target.lower()
            if mid_val == target_lower:
                return sorted_data[mid], comparisons
            elif mid_val < target_lower:
                low = mid + 1
            else:
                high = mid - 1
        return None, comparisons

    @staticmethod
    def sequential_search(data: list, keyword: str, fields: list = None) -> list:
        """
        Sequential Search: cari di beberapa field sekaligus.
        Time Complexity: O(n * f) — f = jumlah field
        Space Complexity: O(k)
        """
        if fields is None:
            fields = ["nim", "nama", "email", "jurusan"]
        keyword_lower = keyword.lower()
        results = []
        comparisons = 0
        seen_nims = set()
        for item in data:
            for field in fields:
                comparisons += 1
                if keyword_lower in str(item.get(field, "")).lower():
                    if item.get("nim") not in seen_nims:
                        results.append(item)
                        seen_nims.add(item.get("nim"))
                    break
        return results, comparisons


# ─────────────────────────────────────────────────────────────
# ALGORITMA PENGURUTAN
# ─────────────────────────────────────────────────────────────
class SortEngine:
    """
    Kelas pengurutan data mahasiswa.
    Mendukung: Bubble Sort, Selection Sort, Insertion Sort,
               Merge Sort, Shell Sort
    """

    @staticmethod
    def bubble_sort(data: list, key: str = "nama", ascending: bool = True) -> tuple:
        """
        Bubble Sort: bandingkan & tukar elemen bersebelahan.
        Time Complexity: O(n²) worst/average, O(n) best (sudah terurut)
        Space Complexity: O(1) — in-place
        """
        arr = data.copy()
        n = len(arr)
        swaps = 0
        for i in range(n - 1):
            swapped = False
            for j in range(n - i - 1):
                val_j = str(arr[j].get(key, "")).lower()
                val_next = str(arr[j + 1].get(key, "")).lower()
                # konversi numerik jika field angka
                if key in ("ipk", "angkatan"):
                    val_j = float(arr[j].get(key, 0))
                    val_next = float(arr[j + 1].get(key, 0))
                condition = val_j > val_next if ascending else val_j < val_next
                if condition:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    swaps += 1
                    swapped = True
            if not swapped:
                break
        return arr, swaps

    @staticmethod
    def selection_sort(data: list, key: str = "nama", ascending: bool = True) -> tuple:
        """
        Selection Sort: cari minimum/maksimum, taruh di posisi yang tepat.
        Time Complexity: O(n²) — selalu, tanpa terkecuali
        Space Complexity: O(1) — in-place
        """
        arr = data.copy()
        n = len(arr)
        comparisons = 0
        for i in range(n):
            idx = i
            for j in range(i + 1, n):
                comparisons += 1
                val_j = str(arr[j].get(key, "")).lower()
                val_idx = str(arr[idx].get(key, "")).lower()
                if key in ("ipk", "angkatan"):
                    val_j = float(arr[j].get(key, 0))
                    val_idx = float(arr[idx].get(key, 0))
                condition = val_j < val_idx if ascending else val_j > val_idx
                if condition:
                    idx = j
            arr[i], arr[idx] = arr[idx], arr[i]
        return arr, comparisons

    @staticmethod
    def insertion_sort(data: list, key: str = "nama", ascending: bool = True) -> tuple:
        """
        Insertion Sort: sisipkan elemen ke posisi yang tepat.
        Time Complexity: O(n²) worst, O(n) best
        Space Complexity: O(1) — in-place
        """
        arr = data.copy()
        comparisons = 0
        for i in range(1, len(arr)):
            current = arr[i]
            j = i - 1
            while j >= 0:
                comparisons += 1
                val_j = str(arr[j].get(key, "")).lower()
                val_cur = str(current.get(key, "")).lower()
                if key in ("ipk", "angkatan"):
                    val_j = float(arr[j].get(key, 0))
                    val_cur = float(current.get(key, 0))
                condition = val_j > val_cur if ascending else val_j < val_cur
                if condition:
                    arr[j + 1] = arr[j]
                    j -= 1
                else:
                    break
            arr[j + 1] = current
        return arr, comparisons

    @staticmethod
    def merge_sort(data: list, key: str = "nama", ascending: bool = True) -> tuple:
        """
        Merge Sort: divide & conquer — bagi, urutkan, gabungkan.
        Time Complexity: O(n log n) — selalu konsisten
        Space Complexity: O(n) — butuh array tambahan
        """
        comparisons = [0]  # pakai list agar bisa dimodifikasi di closure

        def _merge(arr):
            if len(arr) <= 1:
                return arr
            mid = len(arr) // 2
            left  = _merge(arr[:mid])
            right = _merge(arr[mid:])
            return _merge_two(left, right)

        def _merge_two(left, right):
            result = []
            i = j = 0
            while i < len(left) and j < len(right):
                comparisons[0] += 1
                lv = str(left[i].get(key, "")).lower()
                rv = str(right[j].get(key, "")).lower()
                if key in ("ipk", "angkatan"):
                    lv = float(left[i].get(key, 0))
                    rv = float(right[j].get(key, 0))
                condition = lv <= rv if ascending else lv >= rv
                if condition:
                    result.append(left[i]); i += 1
                else:
                    result.append(right[j]); j += 1
            result.extend(left[i:])
            result.extend(right[j:])
            return result

        sorted_arr = _merge(data.copy())
        return sorted_arr, comparisons[0]

    @staticmethod
    def shell_sort(data: list, key: str = "nama", ascending: bool = True) -> tuple:
        """
        Shell Sort: variasi insertion sort dengan gap berkurang.
        Time Complexity: O(n log²n) — tergantung sequence gap
        Space Complexity: O(1) — in-place
        """
        arr = data.copy()
        n = len(arr)
        gap = n // 2
        comparisons = 0
        while gap > 0:
            for i in range(gap, n):
                temp = arr[i]
                j = i
                while j >= gap:
                    comparisons += 1
                    val_j = str(arr[j - gap].get(key, "")).lower()
                    val_t = str(temp.get(key, "")).lower()
                    if key in ("ipk", "angkatan"):
                        val_j = float(arr[j - gap].get(key, 0))
                        val_t = float(temp.get(key, 0))
                    condition = val_j > val_t if ascending else val_j < val_t
                    if condition:
                        arr[j] = arr[j - gap]
                        j -= gap
                    else:
                        break
                arr[j] = temp
            gap //= 2
        return arr, comparisons


# ─────────────────────────────────────────────────────────────
# MANAJEMEN DATA MAHASISWA (CRUD)
# ─────────────────────────────────────────────────────────────
class MahasiswaManager:
    """
    Kelas utama untuk CRUD mahasiswa.
    Menggunakan array (list Python) + pointer (index).
    """

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._data: list[dict] = []   # array utama (pointer ke list)
        self._load()

    def _load(self):
        """Load data dari file ke memory."""
        try:
            self._data = FileManager.load(self._filepath)
        except RuntimeError as e:
            self._data = []
            print(f"[WARNING] {e}")

    def _save(self):
        """Simpan data dari memory ke file."""
        FileManager.save(self._filepath, self._data)

    def get_all(self) -> list:
        """
        Ambil semua data.
        Time Complexity: O(n)
        """
        return self._data.copy()

    def find_by_nim(self, nim: str) -> int:
        """
        Cari index mahasiswa berdasarkan NIM.
        Time Complexity: O(n) — Linear Search
        Return: index atau -1 jika tidak ditemukan
        """
        for idx, mhs in enumerate(self._data):
            if mhs.get("nim") == nim:
                return idx          # pointer / index
        return -1

    def add(self, data: dict) -> dict:
        """
        Tambah mahasiswa baru.
        Time Complexity: O(n) — validasi + cek duplikat NIM
        """
        # Validasi regex
        errors = Validator.validate_all(data)
        if errors:
            raise ValueError("; ".join(errors))

        # Cek NIM duplikat
        if self.find_by_nim(data["nim"]) != -1:
            raise ValueError(f"NIM {data['nim']} sudah terdaftar.")

        # Buat objek Mahasiswa (OOP)
        mhs = Mahasiswa(
            nim=data["nim"],
            nama=data["nama"],
            email=data["email"],
            telepon=data["telepon"],
            jurusan=data["jurusan"],
            angkatan=int(data["angkatan"]),
            ipk=float(data["ipk"]),
        )
        self._data.append(mhs.to_dict())
        self._save()
        return mhs.to_dict()

    def update(self, nim: str, data: dict) -> dict:
        """
        Update data mahasiswa berdasarkan NIM.
        Time Complexity: O(n) — cari dulu, lalu update
        """
        idx = self.find_by_nim(nim)
        if idx == -1:
            raise LookupError(f"Mahasiswa dengan NIM {nim} tidak ditemukan.")

        # Merge data lama + baru
        existing = self._data[idx].copy()
        existing.update(data)

        errors = Validator.validate_all(existing)
        if errors:
            raise ValueError("; ".join(errors))

        # Buat ulang objek untuk validasi setter
        mhs = Mahasiswa.from_dict(existing)
        self._data[idx] = mhs.to_dict()   # update via pointer/index
        self._save()
        return self._data[idx]

    def delete(self, nim: str) -> bool:
        """
        Hapus mahasiswa berdasarkan NIM.
        Time Complexity: O(n) — cari index, lalu hapus
        """
        idx = self.find_by_nim(nim)
        if idx == -1:
            raise LookupError(f"Mahasiswa dengan NIM {nim} tidak ditemukan.")
        self._data.pop(idx)   # hapus elemen dari array via pointer
        self._save()
        return True

    def get_stats(self) -> dict:
        """Statistik ringkasan data mahasiswa."""
        if not self._data:
            return {"total": 0, "avg_ipk": 0, "jurusan_count": {}}
        total = len(self._data)
        avg_ipk = round(sum(m["ipk"] for m in self._data) / total, 2)
        jurusan_count = {}
        for m in self._data:
            j = m["jurusan"]
            jurusan_count[j] = jurusan_count.get(j, 0) + 1
        return {"total": total, "avg_ipk": avg_ipk, "jurusan_count": jurusan_count}


# ─────────────────────────────────────────────────────────────
# INISIALISASI MANAGER (SINGLETON sederhana)
# ─────────────────────────────────────────────────────────────
manager = MahasiswaManager(DATA_FILE)


# ─────────────────────────────────────────────────────────────
# AUTH DECORATOR
# ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"success": False, "message": "Silakan login terlebih dahulu."}), 401
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────
# ROUTE — HALAMAN
# ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


# ─────────────────────────────────────────────────────────────
# ROUTE — AUTH
# ─────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def login():
    """Login endpoint."""
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password:
            return jsonify({"success": False, "message": "Username dan password wajib diisi."})
        users = FileManager.load_users(USERS_FILE)
        if users.get(username) == password:
            session["logged_in"] = True
            session["username"] = username
            return jsonify({"success": True, "message": f"Selamat datang, {username}!", "username": username})
        return jsonify({"success": False, "message": "Username atau password salah."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logout berhasil."})


@app.route("/api/session")
def check_session():
    return jsonify({
        "logged_in": session.get("logged_in", False),
        "username": session.get("username", "")
    })


# ─────────────────────────────────────────────────────────────
# ROUTE — CRUD MAHASISWA
# ─────────────────────────────────────────────────────────────
@app.route("/api/mahasiswa", methods=["GET"])
@login_required
def get_mahasiswa():
    """Ambil semua data mahasiswa. O(n)"""
    try:
        page     = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        data = manager.get_all()
        total = len(data)
        start = (page - 1) * per_page
        end   = start + per_page
        return jsonify({
            "success": True,
            "data": data[start:end],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total else 1
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/mahasiswa/<nim>", methods=["GET"])
@login_required
def get_mahasiswa_by_nim(nim):
    """Ambil satu mahasiswa berdasarkan NIM."""
    try:
        idx = manager.find_by_nim(nim)
        if idx == -1:
            return jsonify({"success": False, "message": f"NIM {nim} tidak ditemukan."}), 404
        return jsonify({"success": True, "data": manager.get_all()[idx]})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/mahasiswa", methods=["POST"])
@login_required
def add_mahasiswa():
    """Tambah mahasiswa baru."""
    try:
        data = request.get_json()
        result = manager.add(data)
        return jsonify({"success": True, "message": "Mahasiswa berhasil ditambahkan.", "data": result}), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/mahasiswa/<nim>", methods=["PUT"])
@login_required
def update_mahasiswa(nim):
    """Update data mahasiswa."""
    try:
        data = request.get_json()
        result = manager.update(nim, data)
        return jsonify({"success": True, "message": "Data berhasil diperbarui.", "data": result})
    except (ValueError, LookupError) as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/api/mahasiswa/<nim>", methods=["DELETE"])
@login_required
def delete_mahasiswa(nim):
    """Hapus mahasiswa berdasarkan NIM."""
    try:
        manager.delete(nim)
        return jsonify({"success": True, "message": f"Mahasiswa NIM {nim} berhasil dihapus."})
    except LookupError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# ROUTE — PENCARIAN
# ─────────────────────────────────────────────────────────────
@app.route("/api/search", methods=["GET"])
@login_required
def search():
    """
    Endpoint pencarian mahasiswa.
    Mendukung: linear, binary, sequential
    """
    try:
        keyword    = request.args.get("q", "").strip()
        method     = request.args.get("method", "sequential")
        field      = request.args.get("field", "nama")
        data       = manager.get_all()
        start_time = time.perf_counter()

        if not keyword:
            return jsonify({"success": False, "message": "Keyword pencarian wajib diisi."})

        if method == "linear":
            results, comparisons = SearchEngine.linear_search(data, keyword, field)
            algo_info = "Linear Search — O(n)"
        elif method == "binary":
            result, comparisons = SearchEngine.binary_search(data, keyword, field)
            results = [result] if result else []
            algo_info = "Binary Search — O(log n)"
        else:  # sequential (default)
            results, comparisons = SearchEngine.sequential_search(data, keyword)
            algo_info = "Sequential Search — O(n × f)"

        elapsed = round((time.perf_counter() - start_time) * 1000, 4)
        return jsonify({
            "success": True,
            "data": results,
            "total": len(results),
            "algorithm": algo_info,
            "comparisons": comparisons,
            "elapsed_ms": elapsed
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# ROUTE — PENGURUTAN
# ─────────────────────────────────────────────────────────────
@app.route("/api/sort", methods=["GET"])
@login_required
def sort_data():
    """
    Endpoint pengurutan mahasiswa.
    Mendukung: bubble, selection, insertion, merge, shell
    """
    try:
        method     = request.args.get("method", "merge")
        key        = request.args.get("key", "nama")
        ascending  = request.args.get("order", "asc") == "asc"
        data       = manager.get_all()
        start_time = time.perf_counter()

        sort_map = {
            "bubble":    (SortEngine.bubble_sort,    "Bubble Sort — O(n²)"),
            "selection": (SortEngine.selection_sort, "Selection Sort — O(n²)"),
            "insertion": (SortEngine.insertion_sort, "Insertion Sort — O(n²) / O(n) best"),
            "merge":     (SortEngine.merge_sort,     "Merge Sort — O(n log n)"),
            "shell":     (SortEngine.shell_sort,     "Shell Sort — O(n log²n)"),
        }

        if method not in sort_map:
            return jsonify({"success": False, "message": f"Metode '{method}' tidak dikenal."})

        func, algo_info = sort_map[method]
        sorted_data, ops = func(data, key, ascending)
        elapsed = round((time.perf_counter() - start_time) * 1000, 4)

        return jsonify({
            "success": True,
            "data": sorted_data,
            "total": len(sorted_data),
            "algorithm": algo_info,
            "operations": ops,
            "elapsed_ms": elapsed
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# ROUTE — STATISTIK
# ─────────────────────────────────────────────────────────────
@app.route("/api/stats", methods=["GET"])
@login_required
def get_stats():
    try:
        return jsonify({"success": True, "data": manager.get_stats()})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────
# SEED DATA (untuk demo)
# ─────────────────────────────────────────────────────────────
def seed_demo_data():
    """Isi data demo jika file kosong."""
    if manager.get_all():
        return
    demos = [
        {"nim":"12345678","nama":"Andi Pratama","email":"andi@student.ac.id","telepon":"081234567890","jurusan":"Teknik Informatika","angkatan":2022,"ipk":3.75},
        {"nim":"12345679","nama":"Budi Santoso","email":"budi@student.ac.id","telepon":"081234567891","jurusan":"Sistem Informasi","angkatan":2021,"ipk":3.45},
        {"nim":"12345680","nama":"Citra Dewi","email":"citra@student.ac.id","telepon":"081234567892","jurusan":"Teknik Informatika","angkatan":2022,"ipk":3.90},
        {"nim":"12345681","nama":"Dian Kusuma","email":"dian@student.ac.id","telepon":"081234567893","jurusan":"Manajemen Informatika","angkatan":2020,"ipk":3.20},
        {"nim":"12345682","nama":"Eka Putri","email":"eka@student.ac.id","telepon":"081234567894","jurusan":"Teknik Komputer","angkatan":2023,"ipk":3.60},
        {"nim":"12345683","nama":"Fajar Nugroho","email":"fajar@student.ac.id","telepon":"081234567895","jurusan":"Sistem Informasi","angkatan":2021,"ipk":3.10},
        {"nim":"12345684","nama":"Gita Rahayu","email":"gita@student.ac.id","telepon":"081234567896","jurusan":"Teknik Informatika","angkatan":2022,"ipk":3.85},
        {"nim":"12345685","nama":"Hendra Wijaya","email":"hendra@student.ac.id","telepon":"081234567897","jurusan":"Teknik Komputer","angkatan":2020,"ipk":2.95},
    ]
    for d in demos:
        try:
            manager.add(d)
        except Exception:
            pass


if __name__ == "__main__":
    seed_demo_data()
    app.run(debug=True, host="0.0.0.0", port=5000)
