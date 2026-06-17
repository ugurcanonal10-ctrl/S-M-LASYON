"""
Atlas Takimi - Tur 1 Senaryo Testi (v4)
"""

import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32

GREEN  = '\033[92m'
RED    = '\033[91m'
YELLOW = '\033[93m'
BLUE   = '\033[94m'
RESET  = '\033[0m'
BOLD   = '\033[1m'


class Tur1TestNode(Node):

    def __init__(self):
        super().__init__('tur1_test_node')

        self._pub_obstacle  = self.create_publisher(String,  '/perception/obstacle', 10)
        self._pub_mission   = self.create_publisher(String,  '/mission/event', 10)
        self._pub_dist      = self.create_publisher(Float32, '/localization/distance_to_target', 10)
        self._pub_dwa       = self.create_publisher(String,  '/planning/dwa_result', 10)
        self._pub_park_spot = self.create_publisher(Bool,    '/perception/parking_spot', 10)
        self._pub_park_done = self.create_publisher(Bool,    '/planning/parking_complete', 10)

        self._current_state = 'BILINMIYOR'
        self._state_history = []

        self.create_subscription(
            String, '/planning/current_state', self._cb_state, 10)

        print(f'\n{BOLD}{"="*55}')
        print(f'   ATLAS TAKIMI — TUR 1 SENARYO TESTI v4')
        print(f'{"="*55}{RESET}')
        print(f'{YELLOW}Kosullar : Trafik lambasi YOK, Tabela YOK{RESET}')
        print(f'{YELLOW}Gorevler : 3x Yolcu Alma + Statik Engel + Park{RESET}\n')

    def _cb_state(self, msg: String):
        if msg.data != self._current_state:
            self._current_state = msg.data
            self._state_history.append(msg.data)

    def _spin(self, saniye: float):
        end = time.time() + saniye
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.05)

    def _bekle_state(self, beklenen: str, timeout: float = 5.0) -> bool:
        end = time.time() + timeout
        while time.time() < end:
            rclpy.spin_once(self, timeout_sec=0.05)
            if self._current_state == beklenen:
                return True
        return False

    def _temizle(self):
        """Tum sinyalleri sifirla."""
        m = String(); m.data = 'none'
        self._pub_mission.publish(m)
        self._pub_obstacle.publish(m)
        m2 = Float32(); m2.data = 999.0
        self._pub_dist.publish(m2)
        m3 = String(); m3.data = ''
        self._pub_dwa.publish(m3)
        self._spin(0.3)

    def _adim(self, no: int, aciklama: str):
        print(f'{BLUE}[Adim {no:2}]{RESET} {aciklama}')

    def _kontrol(self, beklenen: str, aciklama: str) -> bool:
        if self._current_state == beklenen:
            print(f'         {GREEN}✓ GECTI{RESET} — '
                  f'{self._current_state} ({aciklama})')
            return True
        else:
            print(f'         {RED}✗ KALDI{RESET} — '
                  f'Beklenen: {beklenen} | '
                  f'Gerceklesen: {self._current_state}')
            return False

    def calistir(self):

        # ADIM 1 — Baslangic
        self._adim(1, 'UMS-2 (Go) — arac harekete geciyor')
        self._temizle()
        self._bekle_state('LANE_FOLLOW')
        self._kontrol('LANE_FOLLOW', 'Normal suruş')

        # ADIM 2 — Statik engel
        self._adim(2, 'LIDAR statik engel tespit etti')
        m = String(); m.data = 'static'
        self._pub_obstacle.publish(m)
        self._bekle_state('STATIC_OBSTACLE')
        self._kontrol('STATIC_OBSTACLE', 'DWA baslatildi')

        # ADIM 3 — Engel gecildi
        self._adim(3, 'DWA basarili — serite don')
        m = String(); m.data = 'none'
        self._pub_obstacle.publish(m)
        m2 = String(); m2.data = 'cleared'
        self._pub_dwa.publish(m2)
        self._bekle_state('LANE_FOLLOW')
        self._kontrol('LANE_FOLLOW', 'Engel gecildi')

        # ADIM 4-9 — 3x Yolcu Alma
        for i in range(1, 4):
            # Onceki noktadan uzaklas
            self._temizle()
            self._bekle_state('LANE_FOLLOW', timeout=3.0)

            adim_no = 2 + (i * 2)
            self._adim(adim_no,
                       f'{i}. yolcu noktasina yaklasiliyor (<=1 m)')
            m = String(); m.data = 'pickup'
            self._pub_mission.publish(m)
            m2 = Float32(); m2.data = 0.5
            self._pub_dist.publish(m2)

            self._bekle_state('PASSENGER_PICKUP', timeout=3.0)
            self._kontrol('PASSENGER_PICKUP',
                          f'{i}. yolcu bekleniyor (17 sn)')

            print(f'         {YELLOW}⏱  17 saniye bekleniyor...{RESET}',
                  end='', flush=True)

            # 17 saniye beklerken sinyalleri koru
            end_time = time.time() + 17.5
            while time.time() < end_time:
                m = String(); m.data = 'pickup'
                self._pub_mission.publish(m)
                m2 = Float32(); m2.data = 0.5
                self._pub_dist.publish(m2)
                self._spin(0.5)
            print(f' {GREEN}Tamam!{RESET}')

            # Uzaklas — FSM'nin sure bitince LANE_FOLLOW'a gecmesini bekle
            self._adim(adim_no + 1,
                       f'{i}. yolcu alindi — serite don')
            self._temizle()
            self._bekle_state('LANE_FOLLOW', timeout=5.0)
            self._kontrol('LANE_FOLLOW', 'Sure doldu')

        # ADIM 10 — Park
        self._adim(10, 'Park bolgesine yaklasiliyor (<=5 m)')
        m = String(); m.data = 'park'
        self._pub_mission.publish(m)
        m2 = Float32(); m2.data = 4.0
        self._pub_dist.publish(m2)
        self._bekle_state('PARKING_SEARCH', timeout=5.0)
        self._kontrol('PARKING_SEARCH', 'Park yeri aranıyor')

        # ADIM 11
        self._adim(11, 'Uygun park yeri bulundu')
        m = Bool(); m.data = True
        self._pub_park_spot.publish(m)
        self._bekle_state('PARKING_MANEUVER', timeout=5.0)
        self._kontrol('PARKING_MANEUVER', 'Manuvraya basla')

        # ADIM 12
        self._adim(12, 'Park tamamlandi')
        m = Bool(); m.data = True
        self._pub_park_done.publish(m)
        self._bekle_state('MISSION_COMPLETE', timeout=5.0)
        self._kontrol('MISSION_COMPLETE', 'Gorev tamamlandi!')

        self._sonuc()

    def _sonuc(self):
        beklenen = [
            'LANE_FOLLOW',
            'STATIC_OBSTACLE', 'LANE_FOLLOW',
            'PASSENGER_PICKUP', 'LANE_FOLLOW',
            'PASSENGER_PICKUP', 'LANE_FOLLOW',
            'PASSENGER_PICKUP', 'LANE_FOLLOW',
            'PARKING_SEARCH', 'PARKING_MANEUVER', 'MISSION_COMPLETE',
        ]

        print(f'\n{BOLD}{"="*55}')
        print(f'   TUR 1 SONUCU')
        print(f'{"="*55}{RESET}')
        print(f'\nState gecis sirasi:')
        for i, s in enumerate(self._state_history):
            if i < len(beklenen):
                isaret = f'{GREEN}✓{RESET}' if s == beklenen[i] \
                         else f'{RED}✗{RESET}'
            else:
                isaret = f'{RED}+{RESET}'
            print(f'  {isaret} {i+1:3}. {s}')

        dogru = sum(1 for a, b in zip(self._state_history, beklenen)
                    if a == b)
        toplam = len(beklenen)

        print(f'\nDogru gecis : {GREEN}{dogru}{RESET}/{toplam}')

        if dogru == toplam and len(self._state_history) == toplam:
            print(f'\n{GREEN}{BOLD}✓ TUR 1 TESTI TAMAMEN BASARILI! 12/12{RESET}')
        else:
            print(f'\n{YELLOW}⚠ {toplam - dogru} adim eksik{RESET}')
        print(f'{"="*55}\n')


def main(args=None):
    rclpy.init(args=args)
    node = Tur1TestNode()
    try:
        node.calistir()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
