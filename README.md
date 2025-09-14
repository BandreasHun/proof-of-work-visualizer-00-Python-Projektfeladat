# Python Blockchain Mining Vizualizer

## Rövid leírás
Ez egy kis projekt, ami egy **Proof-of-Work** blokk lánc bányászatát szemlélteti.  
Tkinter alapú grafikus felületen látható, hogyan keres a rendszer nonce-okat amíg a hash megfelel a nehézségi feltételnek (vezető nullák száma).  

A programban lehet állítani:
- Nehézség (difficulty)
- Hash algorythm (SHA-256, BLAKE2b, PBKDF2)
- Nonce keresési stratégia (sorban, visszafelé, lépésekben, véletlen, kevert)

Blokkok automatikusan rajzolódnak a képernyőre, és a timestamp is kiiródik emberi idő formában.

---

## Hallgató
**Név:** Jánosházi András
**Szak:** Mérnökinformatikus BSc

---

## Modulok és funkciók

### Tanult modul
- `tkinter` → grafikus felület, Canvas, Button, Scale, Radiobutton, stb.

### Bemutatott modul
- `hashlib` → kriptográfiai hash függvények
  - `hashlib.sha256(data)`  
  - `hashlib.blake2b(data, digest_size=32)`  
  - `hashlib.pbkdf2_hmac('sha256', data, b"", rounds)`

### Saját modul
- `ja_pow.py` (JA monogram)  
  - `class JABlock` – blokk adatszerkezet  
  - `functon ja_make_header(prev, msg, ts, nonce)` – blokkfejléc összerakása  
  - `function ja_compute_hash(data, algorythm)` – hash kiszámítása  
  - `function ja_meets_difficulty(hash, zeros)` – ellenőrzés vezető nullákra  

---

## Osztályok
- `JABlock` (ja_pow.py) – blokk adatok (index, üzenet, hash, prev, nonce, timestamp)  
- `MinerController` (main.py) – GUI vezérlés, bányászat szálban, start/pause/reset logika
