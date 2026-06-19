# gps_loss_zone

Robotaksi yarışması — Konumlandırma alt sistemi
**Ahmet, Görev 1**: GPS-kaybı bölgesi (tünel) + GPS kesme/bozma node'u.

## ÖNEMLİ — repo incelemesi sonrası güncelleme

İlk taslakta varsayımsal değerler kullanılmıştı. `ugurcanonal10-ctrl/S-M-LASYON`
reposu incelendikten sonra şunlar düzeltildi:

| Konu | İlk taslak (yanlış) | Gerçek / düzeltilmiş |
|---|---|---|
| Araç model adı | `robotaksi` | `robotaxi` |
| Ham GPS topic'i | `/gps/fix_raw` (URDF değişikliği gerektiriyordu) | `/gps` (URDF zaten bunu yayınlıyor, **değişiklik gerekmiyor**) |
| Tünel | Yeni `gps_tunnel` modeli eklenecekti | **`worlds/teknofest_pist.world` içinde zaten var** (x:49-61, y:±4.3) — ayrı model eklenmedi |
| `/gazebo/model_states` | Var sayılmıştı | **Hiçbir world'de yoktu** → `gazebo_ros_state` plugin'i eklendi |
| Pist entegrasyonu | — | `teknofest_pist.world` pakete dahil değildi, `robotaxi_sim` içine taşındı + yeni launch dosyası eklendi |

## Bu pakette ne var

1. **`gps_loss_simulator`** node'u — aracın gerçek konumunu
   (`/gazebo/model_states`) izler, **mevcut tünel** bölgesine (x:[49,61],
   y:[-4.3,4.3]) girince `/gps` üzerindeki ham `NavSatFix` mesajlarını
   keser (`mode: drop`) ve `/gps/fix`'e hiç yazmaz. Bölge dışında
   pass-through yapar.
2. `/gps_loss/active` (Bool) ve `/gps_loss/status_text` (String) yayınlar
   — **Görev 4 FSM ve RViz text overlay bunu doğrudan kullanabilir.**
3. `force_loss` parametresiyle tünele girmeden test imkânı.

`gps_loss_zone.zip` İÇİNDE BULUNMAYAN, ayrıca `repo_patch.zip` içinde
verilen iki dosya:

- `robotaxi_sim/worlds/teknofest_pist.world` — orijinal pist + eklenen
  `gazebo_ros_state` plugin'i (sizin mevcut `worlds/teknofest_pist.world`
  dosyanızın YERİNE robotaxi_sim PAKETİNİN İÇİNE konacak kopyası).
- `robotaxi_sim/launch/sim_teknofest.launch.py` — tüneli içeren pisti
  açan, `robotaxi`yı doğru spawn eden ve `gps_loss_simulator`'ı otomatik
  başlatan YENİ launch dosyası. **Mevcut `sim.launch.py`'ye dokunulmadı.**

## Kurulum adımları

```bash
# 1) Bu paketi workspace'e ekleyin
cp -r gps_loss_zone ~/ros2_ws/src/

# 2) Patch dosyalarını yerleştirin
#    (üst dizindeki worlds/teknofest_pist.world'ün YERİNE, robotaxi_sim
#    paketinin worlds/ klasörüne kopyalanmış, state-plugin eklenmiş hali)
cp repo_patch/robotaxi_sim/worlds/teknofest_pist.world \
   ~/ros2_ws/src/S-M-LASYON/robotaxi_sim/worlds/teknofest_pist.world
cp repo_patch/robotaxi_sim/launch/sim_teknofest.launch.py \
   ~/ros2_ws/src/S-M-LASYON/robotaxi_sim/launch/sim_teknofest.launch.py

# 3) Build
cd ~/ros2_ws
colcon build --packages-select robotaxi_sim gps_loss_zone
source install/setup.bash
```

## Test

```bash
ros2 launch robotaxi_sim sim_teknofest.launch.py
```

Başka bir terminalde:

```bash
ros2 topic list
# /gazebo/model_states, /gps, /gps/fix, /gps_loss/active, /gps_loss/status_text görmelisiniz

# /gazebo/model_states GERÇEKTEN "/gazebo/model_states" mi yayınlıyor kontrol edin -
# eğer farklıysa (ör. sadece /model_states), config/gps_loss_zone.yaml içindeki
# model_states_topic değerini ona göre güncelleyin.
ros2 topic echo /gazebo/model_states --once

# Aracı +x yönünde sürün (basit test):
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 2.0}}" -r 10

ros2 topic echo /gps_loss/status_text
# x=49 civarına gelince "Mod: DEAD RECKONING (GPS YOK)" görmelisiniz
# x=61'i geçince "Mod: NORMAL (GPS VAR)" görmelisiniz
```

Tünele sürmeden manuel test:

```bash
ros2 param set /gps_loss_simulator force_loss true
ros2 topic hz /gps/fix     # force_loss true iken YAYIN DURMALI
ros2 param set /gps_loss_simulator force_loss false
ros2 topic hz /gps/fix     # tekrar akmalı
```

## Yasemin'in EKF kurulumuyla entegrasyon

`navsat_transform_node`, GPS girişi olarak **`/gps/fix`**'i dinlemeli
(ham `/gps`'i DEĞİL). Akış:

```
[URDF: gazebo_ros_gps_sensor] --/gps--> [gps_loss_simulator] --/gps/fix--> [navsat_transform_node]
                                                |
                                                +--/gps_loss/active------> [Görev 4: FSM node'u]
                                                +--/gps_loss/status_text-> [RViz text overlay]
```

## Bilinen belirsizlikler — sahada doğrulayın

- `gazebo_ros_state` plugin'inin varsayılan `/gazebo/model_states` topic
  adını üretip üretmediğini `ros2 topic list` ile MUTLAKA doğrulayın;
  farklıysa `model_states_topic` parametresini güncelleyin.
- `degraded_covariance` değerinin Yasemin'in EKF R matrisiyle tutarlı
  olup olmadığını (yalnızca `mode: degrade` kullanırsanız) birlikte
  gözden geçirin.
