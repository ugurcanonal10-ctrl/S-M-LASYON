# robotaxi_rviz

Robotaksi yarışması — **Görev 3 (Ahmet)**: ground truth / EKF tahmini /
ham GPS path'lerini farklı renklerde, kovaryans elipsleriyle ve TF
ağacıyla (map→odom→base_link) aynı ekranda gösteren RViz konfigürasyonu.

## ⚠️ PLACEHOLDER UYARISI — ekiple konuşulmalı

Yasemin'in mevcut `localization_pkg` (master branch) kurulumu **tek bir
yerel EKF** (`world_frame: odom`) içeriyor — sadece `odom→base_link`
TF'i yayınlanıyor. Orijinal plandaki **ikinci/global EKF** (`map→odom`)
henüz kurulmadı, yani `map` frame'i şu an gerçekte hiçbir yerde
üretilmiyor.

Bu paket, `map` frame'inin RViz'de görünüp TF ağacının tam görsel
olarak çalışması için **geçici bir `static_transform_publisher`**
(`map→odom`, kimlik dönüşümü — yani `map` ve `odom` aynı noktada
varsayılıyor) ekliyor. **Bu gerçek bir global lokalizasyon DEĞİLDİR**,
sadece görselleştirme altyapısının şimdiden hazır olması içindir.

**Yasemin'in global EKF'si eklendiğinde:**
`launch/rviz_view.launch.py` içindeki `map_to_odom_PLACEHOLDER` node'u
**silinmeli**, `map→odom` TF'i o EKF'den gelmelidir. RViz konfigürasyonunun
geri kalanı (renkler, kovaryans ayarları) aynı kalabilir.

## Bu pakette ne var

- **`ground_truth_odom_publisher`** node'u — `/gazebo/model_states`
  içinden `robotaxi`'nin gerçek pozunu çekip `nav_msgs/Odometry` olarak
  `/ground_truth/odom`'da yeniden yayınlar (RViz'in yerleşik Odometry
  display'i ile gösterilebilmesi için; ham `ModelStates` array'i RViz'de
  doğrudan çizilemez).
- **`rviz_view.launch.py`** — placeholder TF + ground truth köprüsü +
  RViz'i birlikte başlatır.
- **`localization_view.rviz`** — üç renkli path + TF + RobotModel +
  (varsa) SLAM haritası aynı ekranda:
  - 🟢 **Yeşil** — EKF tahmini (`/odometry/filtered`), kovaryans elipsi açık
  - 🔵 **Mavi** — Ham GPS (`/odometry/gps`, navsat_transform çıktısı), kovaryans elipsi açık
  - ⚪ **Beyaz** — Ground truth (`/ground_truth/odom`)

## Kurulum

```bash
cp -r robotaxi_rviz ~/arac_ws/src/S-M-LASYON/robotaxi_rviz
cd ~/arac_ws
colcon build --packages-select robotaxi_rviz
source install/setup.bash
```

## Çalıştırma sırası (3 ayrı terminal + bu paket)

```bash
# Terminal 1 - sahne
ros2 launch robotaxi_sim sim_teknofest.launch.py

# Terminal 2 - Yasemin'in EKF kurulumu (master branch'te)
ros2 launch localization_pkg localization.launch.py

# Terminal 3 - bu paket: placeholder TF + ground truth + RViz
ros2 launch robotaxi_rviz rviz_view.launch.py
```

İsteğe bağlı, haritanın da görünmesi için (Görev 2):
```bash
# Terminal 4
ros2 launch robotaxi_slam slam.launch.py
```
(Bu durumda RViz'i iki kere açmamak için `robotaxi_slam/slam.launch.py`
içindeki `rviz2` node'unu yorum satırına alabilir, sadece
`pointcloud_to_laserscan` + `slam_toolbox`'ı çalıştırabilirsiniz —
harita zaten `/map` topic'i üzerinden bu paketin RViz'ine de akar.)

## Doğrulanması gerekenler (henüz test edilmedi — sıradaki test oturumunda)

- [ ] `/odometry/filtered` ve `/odometry/gps` gerçekten kovaryans
      içeriyor mu (`ros2 topic echo /odometry/filtered` ile
      `pose.covariance` alanına bakın) — sıfırsa RViz'de elips
      görünmez, Yasemin'in `ekf.yaml`'ında kovaryans çıktısı kontrolü
      gerekebilir.
- [ ] Araç hareket ettikçe üç path'in (yeşil/mavi/beyaz) görsel olarak
      birbirinden ayrışıp ayrışmadığı (GPS gürültüsü varsa mavi/yeşil
      arasında fark görünmeli).
- [ ] `gps_loss_zone` (Görev 1) ile Yasemin'in `gps_dropout.py`'ının
      AYNI ANDA çalıştırılmaması — ikisi de farklı topic'lere yazıyor
      olsa da kafa karıştırabilir, demo öncesi ekiple netleştirin.
