import arcade
import time
import os
import zipfile
import shutil

# --- [ 설정값 ] ---
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
HIT_LINE_Y = 100
NOTE_RADIUS = 30
LANE_WIDTH = 100
LANE_START_X = 100
NOTE_SPEED = 1800 

# 요청하신 키 설정: S, D, L, ; (세미콜론)
KEYS = [arcade.key.S, arcade.key.D, arcade.key.L, arcade.key.SEMICOLON]

# 초기 오프셋 설정 (단위: 초)
# 에어팟 지연시간에 맞춰 0.200 ~ 0.300 사이에서 시작해보세요.
INITIAL_OFFSET = 0.275 

class ManiaGame(arcade.Window):
    def __init__(self, osz_path):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Arcade 3.0 - AirPods Mania")
        self.osz_path = osz_path
        self.extract_path = "temp_map"
        
        self.notes_to_spawn = []
        self.active_notes = arcade.SpriteList()
        self.audio_file = None
        self.score = 0
        self.combo = 0
        self.start_time = None
        self.music_player = None
        
        # 오프셋 변수
        self.offset = INITIAL_OFFSET

    def setup(self):
        arcade.set_background_color(arcade.color.BLACK_OLIVE)
        
        # 1. OSZ 압축 풀기
        if os.path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        with zipfile.ZipFile(self.osz_path, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)
        
        # 2. 파일들 찾기
        osu_file = None
        for file in os.listdir(self.extract_path):
            if file.endswith(".osu"):
                osu_file = os.path.join(self.extract_path, file)
            if file.lower().endswith((".mp3", ".ogg")):
                self.audio_file = os.path.join(self.extract_path, file)
        
        if not osu_file:
            print("채보 파일을 찾을 수 없습니다.")
            return

        # 3. 파싱
        self.parse_osu(osu_file)
        
        # 4. 음악 재생 및 타이머 시작
        if self.audio_file:
            music = arcade.load_sound(self.audio_file)
            self.music_player = arcade.play_sound(music)
        
        self.start_time = time.time()

    def parse_osu(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        objects_section = content.split("[HitObjects]")[-1].strip()
        for line in objects_section.split('\n'):
            if ',' in line:
                parts = line.split(',')
                x = int(parts[0])
                lane = min(3, x // 128)
                hit_time = int(parts[2]) / 1000.0
                
                tex = arcade.make_circle_texture(NOTE_RADIUS * 2, arcade.color.ELECTRIC_BLUE)
                note = arcade.Sprite(tex)
                note.lane = lane
                note.hit_time = hit_time
                note.center_x = LANE_START_X + (lane * LANE_WIDTH)
                self.notes_to_spawn.append(note)
        
        self.notes_to_spawn.sort(key=lambda n: n.hit_time)

    def on_update(self, delta_time):
        if not self.start_time: return
        
        # [핵심] 현재 경과 시간에서 오프셋을 뺍니다.
        elapsed = (time.time() - self.start_time) - self.offset

        # 노트 생성 (현재 시간 + 미리보기 시간)
        look_ahead = SCREEN_HEIGHT / NOTE_SPEED
        while self.notes_to_spawn and self.notes_to_spawn[0].hit_time <= elapsed + look_ahead:
            note = self.notes_to_spawn.pop(0)
            self.active_notes.append(note)

        # 노트 위치 업데이트
        for note in self.active_notes:
            note.center_y = HIT_LINE_Y + (note.hit_time - elapsed) * NOTE_SPEED

        # Miss 처리
        for note in self.active_notes:
            if note.center_y < -50:
                note.remove_from_sprite_lists()
                self.combo = 0

    def on_draw(self):
        self.clear()
        
        # 레인 가이드
        for i in range(4):
            x = LANE_START_X + (i * LANE_WIDTH)
            arcade.draw_circle_outline(x, HIT_LINE_Y, NOTE_RADIUS + 5, arcade.color.GRAY, 2)
            
        self.active_notes.draw()
        
        # UI 레이아웃
        arcade.draw_text(f"Score: {self.score}", 20, SCREEN_HEIGHT - 40, arcade.color.WHITE, 18)
        arcade.draw_text(f"Combo: {self.combo}", 20, SCREEN_HEIGHT - 70, arcade.color.GOLD, 18)
        arcade.draw_text(f"Offset: {int(self.offset * 1000)}ms (UP/DOWN to adj)", 20, 20, arcade.color.GRAY, 12)

    def on_key_press(self, key, modifiers):
        if key in KEYS:
            lane = KEYS.index(key)
            self.check_hit(lane)
        
        # 실시간 오프셋 조정 (10ms 단위)
        elif key == arcade.key.UP:
            self.offset += 0.010
        elif key == arcade.key.DOWN:
            self.offset -= 0.010

    def check_hit(self, lane):
        # 판정 시에도 오프셋 보정된 시간 사용
        elapsed = (time.time() - self.start_time) - self.offset
        
        for note in self.active_notes:
            if note.lane == lane:
                diff = abs(note.hit_time - elapsed)
                if diff < 0.15: # 150ms 판정 범위
                    if diff < 0.05:
                        self.score += 300
                    else:
                        self.score += 100
                    self.combo += 1
                    note.remove_from_sprite_lists()
                    break

if __name__ == "__main__":
    osz_files = [f for f in os.listdir() if f.endswith('.osz')]
    if osz_files:
        game = ManiaGame(osz_files[0])
        game.setup()
        arcade.run()
    else:
        print(".osz 파일을 찾을 수 없습니다.")