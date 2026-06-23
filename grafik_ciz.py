import numpy as np
import matplotlib.pyplot as plt
import csv
import os

# --- 1. GERÇEK VERİLERİ (CSV) OKUMA ---
dosya_yolu = 'pid_verileri.csv'

# Dosya var mı diye kontrol et
if not os.path.exists(dosya_yolu):
    print(f"HATA: '{dosya_yolu}' bulunamadı!")
    print("Lütfen önce ROS 2 otonom kontrolcüsünü çalıştırıp aracı biraz sür.")
    exit()

zaman = []
hata = []
direksiyon = []

# CSV dosyasını aç ve satır satır oku
with open(dosya_yolu, 'r') as dosya:
    okuyucu = csv.reader(dosya)
    next(okuyucu)  # İlk satırdaki başlıkları (Zaman_s, Serit_Hatasi vb.) atla
    
    for satir in okuyucu:
        if satir:  # Boş satır değilse listeye ekle
            zaman.append(float(satir[0]))
            hata.append(float(satir[1]))
            direksiyon.append(float(satir[2]))

# Çizim kolaylığı için listeleri Numpy dizisine çevir
t = np.array(zaman)
lane_error = np.array(hata)
steering_cmd = np.array(direksiyon)

# --- 2. GRAFİKLERİ ÇİZME ---
plt.style.use('bmh')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
fig.suptitle('Atlas Takımı - Gerçek Sürüş PID Analizi', fontsize=16, fontweight='bold')

# Üst Tablo: Şerit Hatası
ax1.plot(t, lane_error, color='red', linewidth=2, label='Şerit Sapması (m)')
ax1.axhline(0, color='black', linestyle='--', linewidth=1.5, label='İdeal Şerit Merkezi')
ax1.set_title('Zamana Göre Şerit Hatası (Lane Error)', fontsize=12)
ax1.set_ylabel('Hata Miktarı')
ax1.grid(True)
ax1.legend()

# Alt Tablo: Direksiyon Tepkisi
ax2.plot(t, steering_cmd, color='blue', linewidth=2, label='Direksiyon Açısı (rad/s)')
ax2.axhline(0, color='black', linestyle='--', linewidth=1.5, label='Düz Konum')
ax2.set_title('Zamana Göre Direksiyon Tepkisi (Steering Command)', fontsize=12)
ax2.set_xlabel('Zaman (saniye)')
ax2.set_ylabel('Açı (rad/s)')
ax2.grid(True)
ax2.legend()

# Grafikleri Ekranda Göster
plt.tight_layout()
plt.show()

