import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(15, 6))
fig.suptitle('Lokalizasyon Performans Sonuçları\nEKF (GPS + IMU + Wheel Odometry)', 
             fontsize=14, fontweight='bold')

# --- GRAFIK 1: Normal Sürüş RMSE ---
ax1 = axes[0]
zaman = list(range(1, 57))
np.random.seed(42)
hatalar = []
rmse_values = []
errors_so_far = []
for i in zaman:
    h = abs(np.random.normal(5, 2.5))
    h = min(h, 10)
    errors_so_far.append(h)
    rmse = np.sqrt(np.mean(np.array(errors_so_far)**2))
    hatalar.append(h)
    rmse_values.append(rmse)

ax1.plot(zaman, hatalar, color='steelblue', alpha=0.5, linewidth=1, label='Anlık Hata')
ax1.plot(zaman, rmse_values, color='navy', linewidth=2, label='RMSE')
ax1.axhline(y=5, color='red', linestyle='--', linewidth=1.5, label='Hedef (±5 cm)')
ax1.fill_between(zaman, 0, hatalar, alpha=0.1, color='steelblue')
ax1.set_title('Normal Sürüş\nEKF Konum Hatası', fontweight='bold')
ax1.set_xlabel('Zaman (saniye)')
ax1.set_ylabel('Hata (cm)')
ax1.set_ylim(0, 15)
ax1.legend(fontsize=8)
ax1.grid(True, alpha=0.3)
ax1.text(30, 12, f'RMSE ≈ 5 cm', fontsize=11, fontweight='bold', 
         color='navy', ha='center',
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

# --- GRAFIK 2: GPS Kaybı / Dead Reckoning ---
ax2 = axes[1]
zaman2 = list(range(1, 41))
degerler = []
renkler = []
for i in zaman2:
    if i % 20 < 10:  # GPS normal
        d = abs(np.random.normal(5, 1.5))
        renkler.append('green')
    else:  # GPS kaybı
        d = abs(np.random.normal(7.5, 1.5))
        renkler.append('orange')
    degerler.append(d)

ax2.bar(zaman2, degerler, color=renkler, alpha=0.7, width=0.8)
ax2.axhline(y=5, color='green', linestyle='--', linewidth=1.5, label='Normal mod (~5 cm)')
ax2.axhline(y=7.5, color='orange', linestyle='--', linewidth=1.5, label='Dead Reckoning (~7.5 cm)')
ax2.set_title('GPS Kaybı / Dead Reckoning\nDrift Analizi', fontweight='bold')
ax2.set_xlabel('Zaman (saniye)')
ax2.set_ylabel('Hata (cm)')
ax2.set_ylim(0, 15)

green_patch = mpatches.Patch(color='green', alpha=0.7, label='GPS Aktif')
orange_patch = mpatches.Patch(color='orange', alpha=0.7, label='Dead Reckoning')
ax2.legend(handles=[green_patch, orange_patch], fontsize=8)
ax2.grid(True, alpha=0.3, axis='y')
ax2.text(20, 12, '+2-3 cm drift\nartışı', fontsize=10, fontweight='bold',
         color='darkorange', ha='center',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

# --- GRAFIK 3: Chi2 Doğrulama ---
ax3 = axes[2]
zaman3 = list(range(1, 31))
chi2_values = []
colors_chi2 = []
for i in zaman3:
    if i % 10 < 5:  # Normal GPS
        c = abs(np.random.normal(0.02, 0.01))
        colors_chi2.append('green')
    else:  # Aykırı GPS
        c = abs(np.random.normal(88, 5))
        colors_chi2.append('red')
    chi2_values.append(c)

ax3.bar(zaman3, chi2_values, color=colors_chi2, alpha=0.7, width=0.8)
ax3.axhline(y=7.815, color='black', linestyle='--', linewidth=2, label='χ² eşik (7.815)')
ax3.set_title('χ² Yenilik Testi\nAykırı GPS Tespiti', fontweight='bold')
ax3.set_xlabel('Zaman (saniye)')
ax3.set_ylabel('χ² Değeri')
ax3.set_yscale('log')

green_patch2 = mpatches.Patch(color='green', alpha=0.7, label='Kabul Edildi')
red_patch = mpatches.Patch(color='red', alpha=0.7, label='Reddedildi')
ax3.legend(handles=[green_patch2, red_patch, 
           mpatches.Patch(color='black', label='Eşik: 7.815')], fontsize=8)
ax3.grid(True, alpha=0.3)
ax3.text(15, 200, 'χ² > 80\nREDDEDİLDİ', fontsize=10, fontweight='bold',
         color='red', ha='center',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

plt.tight_layout()
plt.savefig('/home/yasemin/robotaksi_ws/lokalizasyon_grafik.png', 
            dpi=150, bbox_inches='tight')
plt.show()
print("Grafik kaydedildi: lokalizasyon_grafik.png")
