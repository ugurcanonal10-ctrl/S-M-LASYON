# Görev 5 — EKF'nin SLAM/Point-Cloud İşleminden İzolasyonu (Ahmet)

Bu klasör, **7.9'un sonuna eklenecek paragrafı** ve bu paragrafı
**sayısal olarak destekleyen ölçüm aracını** içerir.

## İçerik

- `ekf_priority.launch.py` — EKF (`ekf_node`) ve `navsat_transform_node`'u
  Linux `nice` ile yüksek zamanlayıcı önceliğiyle (`-10`) başlatan launch
  dosyası. SLAM/point-cloud node'ları varsayılan öncelikte kalır.
- `cpu_monitor.py` — Çalışan `ekf_node`, `navsat_transform_node`,
  `async_slam_toolbox_node`, `pointcloud_to_laserscan_node`
  süreçlerinin CPU kullanımını periyodik örnekleyip CSV + grafik (PNG)
  üreten bağımsız izleme scripti (ROS node'u değil, salt psutil tabanlı).

## Nasıl çalıştırılır (gerçek ölçüm için)

```bash
pip install psutil matplotlib --break-system-packages   # bir kerelik kurulum

# Terminal 1
ros2 launch robotaxi_sim sim_teknofest.launch.py

# Terminal 2 - normal EKF yerine YÜKSEK ÖNCELİKLİ sürümü kullanın
ROS_WS=~/arac_ws ros2 launch ekf_isolation/ekf_priority.launch.py

# Terminal 3 - CPU yükünü artırmak için SLAM'i de aynı anda çalıştırın
# (asıl test budur: SLAM çalışırken EKF etkileniyor mu?)
ros2 launch robotaxi_slam slam.launch.py

# Terminal 4 - aracı sürün (gerçekçi yük için, durağan değil hareketli ölçüm)
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: -1.5}, angular: {z: 0.2}}" -r 10

# Terminal 5 - ölçümü başlatın (60 saniye)
python3 ekf_isolation/cpu_monitor.py --duration 60
```

Script bitince **konsola bastığı özet istatistiği** (ortalama/maks/std
CPU%) ve ürettiği `cpu_usage.png` grafiğini doğrudan rapora/slayta
ekleyebilirsiniz.

## 7.9'a eklenecek paragraf (taslak — ölçüm sonrası [X], [Y] yerlerini gerçek sayılarla doldurun)

> **EKF'nin SLAM/Point-Cloud İşleminden İzolasyonu.** Lokalizasyon
> alt sisteminin kalbi olan EKF (`robot_localization/ekf_node`),
> ROS2'nin süreç (process) mimarisi gereği SLAM (`slam_toolbox`) ve
> point-cloud dönüştürme (`pointcloud_to_laserscan`) düğümlerinden
> **bağımsız bir işletim sistemi sürecinde** çalışır; bu, Linux
> çekirdeğinin EKF'yi SLAM'in CPU yoğun tarama eşleştirme (scan
> matching) ve döngü kapatma (loop closure) işlemlerinden bağımsız
> olarak zamanlamasını sağlar. Bu izolasyonu güçlendirmek amacıyla
> EKF ve `navsat_transform_node`, `nice -n -10` ile yükseltilmiş
> Linux zamanlayıcı önceliğiyle başlatılmaktadır; SLAM/point-cloud
> düğümleri varsayılan öncelikte kalmaya devam eder. Bu sayede CPU
> rekabeti oluştuğunda çekirdek EKF'ye öncelik tanır.
>
> Bu iddiayı doğrulamak için, araç hareket halindeyken ve SLAM eşzamanlı
> çalışırken 60 saniyelik bir CPU kullanım ölçümü yapılmıştır
> (`cpu_monitor.py`). Sonuçlar: EKF süreci ortalama **[X]%** CPU
> kullanımıyla (std sapma **[X2]%**) **sabit ve düşük** bir profil
> sergilerken, SLAM süreci ortalama **[Y]%** CPU kullanımıyla, özellikle
> döngü kapatma anlarında belirgin **dalgalanmalar (spike)** göstermiştir
> (bkz. Şekil [N], `cpu_usage.png`). EKF'nin CPU profilinin SLAM'deki bu
> dalgalanmalardan etkilenmeyip sabit kalması, izolasyonun pratikte de
> başarılı olduğunu doğrulamaktadır.

## Notlar / dürüstlük

- `ekf.yaml`'da `frequency: 30.0` tanımlı — orijinal görev metninde
  geçen "100 Hz" rakamı bu projede gerçekleşmiş değil. Paragrafta veya
  slaytta "100 Hz" demek istiyorsanız, önce Yasemin ile birlikte
  `ekf.yaml`'daki `frequency` değerini 100'e çıkarıp donanımın
  (CPU) bunu gerçekten karşılayıp karşılamadığını test etmeniz gerekir
  — aksi halde rapor gerçek ölçümle çelişir.
- `nice -10` için root yetkisi gerekir; konteynerde zaten root
  olduğunuz için sorun çıkmaz, ama gerçek araç bilgisayarında
  (Advantech) bu komutu çalıştıran kullanıcının yetkisini kontrol edin.
- Bu script ve launch dosyası **doğrudan test edilmedi** (gerçek
  node'lar gerektiriyor, sizin konteynerinizde çalıştırmanız lazım) —
  sadece syntax/mantık doğrulaması yapıldı. İlk çalıştırmada küçük
  bir hata çıkarsa (örn. yol/PATH sorunu) şaşırmayın, birlikte
  düzeltiriz.
