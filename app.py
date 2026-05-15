import arcade
import time
import os

# --- 설정 ---
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
HIT_LINE_Y = 100
NOTE_RADIUS = 35
LANE_WIDTH = 100
LANE_START_X = 100
NOTE_SPEED = 500 # 픽셀/초

# 키 바인딩 (4K)
KEYS = [arcade.key.D, arcade.key.F, arcade.key.J, arcade.key.K]

class Note(arcade.Sprite):
    def __init__(self, lane, hit_time):
        # 원형 텍스처 생성
        texture = arcade.make_circle_texture(NOTE_RADIUS * 2, arcade.color.WHITE)
        super().__init__(texture)
        self.lane = lane
        self.hit_time = hit_time # ms 단위
        self.center_x = LANE_START_X + (lane * LANE_WIDTH)
        self.center_y = -1000 # 초기 위치는 화면 밖

class ManiaGame(arcade.Window):
    def __init__(self, osu_file):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Arcade 3.0 osu!mania")
        self.osu_file = osu_file
        self.notes_to_spawn = []
        self.active_notes = arcade.SpriteList()
        self.score = 0
        self.start_time = None
        self.music = None
        self.player = None

    def parse_osu(self):
        """ .osu 파일을 파싱하여 노트 데이터를 추출합니다. """
        with open(self.osu_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        is_hit_objects = False
        for line in lines:
            if "[HitObjects]" in line:
                is_hit_objects = True
                continue
            if is_hit_objects and "," in line:
                parts = line.split(',')
                # x좌표로 레인 판별 (0~512 범위를 4등분)
                x = int(parts[0])
                lane = min(3, x // 128)
                hit_time = int(parts[2]) / 1000.0 # 초 단위 변환
                self.notes_to_spawn.append((hit_time, lane))
        
        # 시간순 정렬
        self.notes_to_spawn.sort()

    def setup(self):
        arcade.set_background_color(arcade.color.BLACK_OLIVE)
        self.parse_osu()
        # 음악 로드 (파일 경로가 있다면)
        # self.music = arcade.load_sound("audio.mp3")
        # self.player = arcade.play_sound(self.music)
        self.start_time = time.time()

    def on_update(self, delta_time):
        elapsed = time.time() - self.start_time

        # 1. 생성 타이밍 확인
        while self.notes_to_spawn and elapsed >= (self.notes_to_spawn[0][0] - (SCREEN_HEIGHT / NOTE_SPEED)):
            hit_time, lane = self.notes_to_spawn.pop(0)
            note = Note(lane, hit_time)
            self.active_notes.append(note)

        # 2. 노트 위치 업데이트 (음악 시간 동기화)
        for note in self.active_notes:
            # 판정선 위치 + (목표시간 - 현재시간) * 속도
            note.center_y = HIT_LINE_Y + (note.hit_time - elapsed) * NOTE_SPEED

            # 화면 아래로 완전히 지나간 경우 (Miss)
            if note.center_y < -50:
                note.remove_from_sprite_lists()

    def on_draw(self):
        self.clear()
        
        # 레인 배경
        arcade.draw_rect_filled(SCREEN_WIDTH/2, SCREEN_HEIGHT/2, LANE_WIDTH*4, SCREEN_HEIGHT, (30, 30, 30))
        
        # 판정선 (서클 가이드)
        for i in range(4):
            x = LANE_START_X + (i * LANE_WIDTH)
            arcade.draw_circle_outline(x, HIT_LINE_Y, NOTE_RADIUS, arcade.color.GRAY, 2)

        # 노트 그리기
        self.active_notes.draw()

        # UI
        arcade.draw_text(f"Score: {self.score}", 20, SCREEN_HEIGHT - 40, arcade.color.WHITE, 15)

    def on_key_press(self, key, modifiers):
        if key in KEYS:
            lane = KEYS.index(key)
            self.check_hit(lane)

    def check_hit(self, lane):
        elapsed = time.time() - self.start_time
        # 해당 레인의 가장 낮은 노트를 검색
        best_note = None
        min_diff = 1.0
        
        for note in self.active_notes:
            if note.lane == lane:
                diff = abs(note.hit_time - elapsed)
                if diff < 0.15: # 150ms 이내 판정 범위
                    best_note = note
                    min_diff = diff
                    break
        
        if best_note:
            if min_diff < 0.05: self.score += 300
            elif min_diff < 0.1: self.score += 100
            else: self.score += 50
            best_note.remove_from_sprite_lists()

if __name__ == "__main__":
    # 실행 전 같은 폴더에 .osu 파일이 있는지 확인하세요.
    # 예: "test_map.osu"
    osu_files = [f for f in os.listdir() if f.endswith('.osu')]
    if osu_files:
        game = ManiaGame(osu_files[0])
        game.setup()
        arcade.run()
    else:
        print("에러: .osu 파일을 찾을 수 없습니다!")