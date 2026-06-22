#!/usr/bin/env python3
"""
cpu_monitor.py
--------------
Robotaksi yarismasi - Gorev 5 (Ahmet): EKF'nin agir SLAM/point-cloud
isleminden izole, sabit dusuk CPU'da calistigini SAYISAL olarak
olcup kanitlayan script.

Bu bir ROS node'u DEGIL, bagimsiz bir izleme aracidir - calisan
sureclerin (process) CPU kullanimini isim eslestirmesiyle bulup
psutil ile periyodik olarak orneklemden olusur.

KULLANIM SIRASI:
  1) ros2 launch robotaxi_sim sim_teknofest.launch.py     (Terminal 1)
  2) ros2 launch localization_pkg localization.launch.py  (Terminal 2)
     (veya ekf_priority.launch.py - yuksek oncelikli surum)
  3) ros2 launch robotaxi_slam slam.launch.py              (Terminal 3)
     (CPU yukunu artirmak icin SLAM da calisirken olcum yapiyoruz -
     asil amac bu: "EKF, SLAM calisirken de etkilenmiyor mu?")
  4) python3 cpu_monitor.py --duration 60                  (Terminal 4)

CIKTI:
  - cpu_usage.csv   : ham olcum verisi (zaman, surec, %CPU, %RAM)
  - cpu_usage.png    : EKF vs SLAM/point-cloud CPU kullanim grafigi
                        (matplotlib kuruluysa otomatik uretilir)
  - Konsola ozet istatistik (ortalama/maksimum/std sapma) basilir -
    bu sayilar rapor 7.9'daki paragrafa DOGRUDAN konulabilir.

GEREKEN PAKETLER (konteynerde yoksa):
  pip install psutil matplotlib --break-system-packages
"""
import argparse
import csv
import time
import statistics

try:
    import psutil
except ImportError:
    print("HATA: psutil kurulu degil. Once sunu calistirin:")
    print("  pip install psutil --break-system-packages")
    raise SystemExit(1)

# Izlenecek surecler: (gosterim adi, process cmdline'inda aranacak anahtar kelime)
TARGETS = [
    ("EKF (ekf_node)", "ekf_node"),
    ("navsat_transform_node", "navsat_transform_node"),
    ("SLAM (async_slam_toolbox_node)", "async_slam_toolbox_node"),
    ("pointcloud_to_laserscan", "pointcloud_to_laserscan_node"),
]


def find_process(keyword):
    """
    Onemli duzeltme: 'ros2 run <pkg> ekf_node ...' komutu, ICINDE
    calistirdigi gercek ikili dosyayi (orn. /opt/ros/foxy/lib/.../ekf_node)
    AYRI bir alt surec olarak baslatir. Ikisinin de cmdline'inda 'ekf_node'
    geciyor, ama 'ros2 run' sarmalayicisi neredeyse hic CPU kullanmaz
    (sadece bekler) - olcum YANLISLIKLA bunu secerse hep ~%0 cikar.
    Bu yuzden ONCE cmdline[0]'in (calistirilan asil komutun) keyword ile
    BITTIGI gercek ikili dosyayi ariyoruz; bulamazsak genel eslesmeye
    geri donuyoruz (fallback).
    """
    fallback = None
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline_list = p.info['cmdline'] or []
            cmdline = ' '.join(cmdline_list)
            if keyword not in cmdline:
                continue
            # Tercih edilen: asil calistirilabilir dosya (cmdline[0]) keyword
            # ile bitiyor mu? (orn. ".../lib/robot_localization/ekf_node")
            if cmdline_list and cmdline_list[0].rstrip('/').endswith(keyword):
                return p
            if fallback is None:
                fallback = p
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return fallback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=int, default=60,
                         help='Olcum suresi (saniye), varsayilan 60')
    parser.add_argument('--interval', type=float, default=1.0,
                         help='Ornekleme araligi (saniye), varsayilan 1.0')
    parser.add_argument('--out-csv', default='cpu_usage.csv')
    parser.add_argument('--out-png', default='cpu_usage.png')
    args = parser.parse_args()

    print(f"CPU izleme baslatildi: {args.duration} sn, {args.interval} sn araliklarla")
    print("Izlenen surecler:")
    procs = {}
    for label, keyword in TARGETS:
        p = find_process(keyword)
        if p is None:
            print(f"  [BULUNAMADI] {label} ('{keyword}' icermeyen bir komut satiri "
                  f"yok - bu node calismiyor olabilir, atlaniyor)")
        else:
            print(f"  [OK] {label} -> PID {p.pid}")
            procs[label] = p
            p.cpu_percent()  # ilk cagri referans alir, gercek deger sonrakinde gelir

    if not procs:
        print("\nHICBIR hedef surec bulunamadi. Once Gazebo/EKF/SLAM'i baslatip "
              "tekrar deneyin.")
        return

    rows = []
    samples = {label: [] for label in procs}

    start = time.time()
    n_steps = int(args.duration / args.interval)
    for step in range(n_steps):
        time.sleep(args.interval)
        t = time.time() - start
        for label, p in list(procs.items()):
            try:
                cpu = p.cpu_percent()
                ram = p.memory_percent()
                samples[label].append(cpu)
                rows.append([f"{t:.1f}", label, f"{cpu:.2f}", f"{ram:.2f}"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"  [UYARI] {label} sureci kayboldu (PID kapanmis olabilir)")
                del procs[label]

    with open(args.out_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['saniye', 'surec', 'cpu_yuzde', 'ram_yuzde'])
        writer.writerows(rows)
    print(f"\nHam veri kaydedildi: {args.out_csv}")

    print("\n=== OZET ISTATISTIK (rapor 7.9 paragrafina kopyalanabilir) ===")
    for label, vals in samples.items():
        if not vals:
            continue
        avg = statistics.mean(vals)
        mx = max(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        print(f"  {label:35s} ortalama: {avg:6.2f}%  maks: {mx:6.2f}%  std: {sd:5.2f}%")

    # Grafik (matplotlib varsa)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 5))
        for label, vals in samples.items():
            xs = [i * args.interval for i in range(len(vals))]
            plt.plot(xs, vals, label=label, linewidth=1.5)
        plt.xlabel('Zaman (sn)')
        plt.ylabel('CPU Kullanimi (%)')
        plt.title('EKF vs SLAM/Point-Cloud CPU Kullanimi - Izolasyon Kaniti (Gorev 5)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(args.out_png, dpi=150)
        print(f"\nGrafik kaydedildi: {args.out_png}")
    except ImportError:
        print("\n(matplotlib kurulu degil, grafik uretilmedi - sadece CSV var. "
              "Grafik icin: pip install matplotlib --break-system-packages)")


if __name__ == '__main__':
    main()
