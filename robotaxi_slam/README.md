# robotaxi_slam

Robotaksi yarışması — **Görev 2 (Ahmet)**: Velodyne VLP-16 point cloud
ile `slam_toolbox` entegrasyonu, RViz'de canlı harita.

## Test sürecinde bulunup düzeltilen 2 gerçek hata

1. **slam_toolbox parametre override sorunu** — `slam_toolbox` paketinin
   kendi `online_async_launch.py`'si (sürüm 2.4.1, Foxy) `slam_params_file`
   argümanını desteklemiyor; `IncludeLaunchDescription` ile özel config
   vermeye çalıştığımızda sessizce yok sayılıp kendi varsayılan config'ini
   kullanıyordu (`base_frame: base_footprint` hatası buradan geliyordu,
   URDF'imizde böyle bir frame yok). **Çözüm:** `slam_toolbox` node'u
   `slam.launch.py` içinde doğrudan `Node(...)` olarak başlatılıyor,
   paketin kendi launch dosyası hiç include edilmiyor — bu garanti
   şekilde bizim `config/slam_toolbox_params.yaml`'ımızı yüklüyor.
2. **LiDAR kendi aracın tavanını görüyordu (self-hit)** — VLP-16, URDF'te
   `z=0.35`'te monteli; araç gövdesinin tavanı `z=0.25`'te bitiyor.
   Aradaki 10cm boşluk, sensörün -15° (en alt katman) ışını tarafından
   neredeyse anında görülüp `/scan`'de sabit `~0.37m` sahte engel olarak
   çıkıyordu, gerçek çevreyi bastırıyordu. **Çözüm:**
   `config/pointcloud_to_laserscan.yaml` içindeki `min_height` değeri
   `-0.2`'den `-0.05`'e çekildi — kendi-vuruş noktaları (`z≈-0.10`)
   artık elden geçiyor, gerçek (sensöre yakın yükseklikteki) engeller
   görünür kalıyor. **Doğrulandı:** araç durağanken `/scan` artık tüm
   `.inf` (sahte 0.37m vuruşu tamamen kayboldu).

## Doğrulanan kısım ✅

- `/velodyne_points` ~8.5 Hz ile akıyor (16 katman, performans sorunsuz)
- `/scan` (2D dilim) ~9 Hz ile akıyor, sahte self-hit'siz
- `slam_toolbox` doğru `base_link`/`odom`/`map` frame'leriyle başlıyor,
  sensörü kaydediyor ("Registering sensor"), harita oluşturmaya
  başlıyor ("Trying to create a map...")
- RViz'de Map/LaserScan/PointCloud2/RobotModel display'leri sorunsuz
  yükleniyor

## HENÜZ DOĞRULANMAMIŞ — bir sonraki test oturumunda yapılmalı ⚠️

Aracı gerçekten sürüp haritanın **canlı büyüdüğünü görsel olarak**
doğrulayamadık — test sırasında konteynerde **birden fazla eski
`cmd_vel` yayıncısı** (önceki oturumlardan kapatılmamış,
`ros2 topic pub -r 10` ile sürekli açık kalmış) üst üste binince
`/odom` pozisyonu anlamsız bir değere savruldu (`x ≈ -39000`).
Bu bir kod hatası DEĞİL, oturum hijyeni sorunu. Bir sonraki testte:

1. Yeni bir test oturumuna başlamadan önce **mutlaka** şunu çalıştırıp
   temiz olduğunu doğrulayın:
   ```bash
   ps aux | grep -E "cmd_vel|gazebo|gzserver|ros2 launch" | grep -v grep
   ```
   Bir şey çıkarsa `kill -9 <pid>` ile temizleyin.
2. Sürüş komutunu **sürekli** (`-r 10`, sonsuza kadar açık) değil,
   **sınırlı sayıda** mesajla verin, örn:
   ```bash
   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -1.5}}" -1
   ```
   (`-1` = tek mesaj gönderip çıkar, terminali açık bırakmaz, unutma
   riski olmaz).
3. **Bilinen ayrı bir hata:** `differential_drive` plugin'i ters yönde
   çalışıyor — pozitif `linear.x` aracı GERİYE (negatif x) sürüyor.
   Tüneli pozitif x yönünde bulduğumuz için, tünele gitmek isterseniz
   `linear.x` **negatif** verin (örn. `-1.5`). Bu Görev 2'nin kapsamı
   dışında, URDF'teki `differential_drive` plugin/teker tanımında ayrı
   bir düzeltme gerektiriyor (henüz yapılmadı).
4. Yön + süre doğru ayarlanınca: `ros2 topic hz /map` ile haritanın
   yayınlanmaya başladığını, RViz'de görsel olarak büyüdüğünü teyit edin.

## Kurulum — gerekli paketler (DOĞRULANDI, kuruldu)

```bash
apt install -y ros-foxy-slam-toolbox ros-foxy-pointcloud-to-laserscan
```

## Kurulum — dosyaları yerleştirme

```bash
cp -r robotaxi_slam ~/arac_ws/src/S-M-LASYON/robotaxi_slam
cp robotaxi_urdf_patch/robotaxi.urdf \
   ~/arac_ws/src/S-M-LASYON/robotaxi_sim/models/robotaxi/robotaxi.urdf
cd ~/arac_ws
colcon build --packages-select robotaxi_sim robotaxi_slam
source install/setup.bash
```

## Test sırası

```bash
# Terminal 1 - sahneyi aç
ros2 launch robotaxi_sim sim_teknofest.launch.py

# Terminal 2 - point cloud'un aktığını doğrula
ros2 topic hz /velodyne_points

# Terminal 3 - SLAM zincirini başlat
ros2 launch robotaxi_slam slam.launch.py

# Terminal 4 - araci SINIRLI sayida mesajla sur (yon: negatif x = tunele dogru)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -1.5}}" -1
# (Birkac saniyede bir tekrarlayin, surekli -r 10 birakmayin)

# Terminal 5 - haritayi izle
ros2 topic hz /map
```
