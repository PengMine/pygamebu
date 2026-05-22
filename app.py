import arcade
import time
import os
import zipfile

# ==============================================================================
# 경로 고정 및 폴더 자동 생성
# ==============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SKIN_DIR = os.path.join(BASE_DIR, "note_skin")
os.makedirs(SKIN_DIR, exist_ok=True)

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800
NOTE_RADIUS = 40
LANE_WIDTH = 100
LANE_START_X = 100

HIT_LINE_Y = 100
BASE_SPEED_MULTIPLIER = 11.0
INITIAL_OFFSET = 0.26
MAX_SCORE = 1000000

# 글로벌 설정 (기본 스킨 목록 세분화)
GAME_CONFIG = {
    "KEYS": [arcade.key.S, arcade.key.D, arcade.key.L, arcade.key.SEMICOLON],
    "KEY_NAMES": ["S", "D", "L", ";"],
    "VOLUME": 50,          
    "SCROLL_SPEED": 5.0,   
    "SHOW_ACCURACY": True, 
    "HARD_JUDGE": False,   
    "PERFECT_MODE": False, 
    "AUTO_PLAY": False,     
    "INVINCIBLE_MODE": False, 
    "NOTE_SKIN": "Default_Bar", # 기본값을 세련된 바 노트로 지정
    "SELECTED_OSU": None,
    "SELECTED_AUDIO": None
}

AVAILABLE_SKINS = ["Default_Bar", "Default_Circle"]

def refresh_note_skins():
    global AVAILABLE_SKINS
    # 내장 스킨 2종 기본 등록
    AVAILABLE_SKINS = ["Default_Bar", "Default_Circle"]
    if os.path.exists(SKIN_DIR):
        for f in os.listdir(SKIN_DIR):
            if f.lower().endswith(".png"):
                AVAILABLE_SKINS.append(os.path.splitext(f)[0])

refresh_note_skins()


# ==============================================================================
# [0] HOW TO PLAY 화면
# ==============================================================================
class HowToPlayView(arcade.View):
    def on_show_view(self): arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
    def on_draw(self):
        self.clear()
        arcade.draw_text("HOW TO PLAY", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80, arcade.color.GOLD, font_size=32, anchor_x="center", bold=True)
        instructions = [
            "1. 플레이 방식 안내",
            "   위에서 떨어지는 노트를 판정선(가이드라인)에 맞춰 키를 누르세요.",
            "   롱노트는 타이밍에 맞춰 누른 뒤 끝날 때까지 유지해야 합니다.",
            "",
            "2. 가변형 라이프 시스템 및 무적모드",
            "   - 라이프 80~100: 판정이 좋을 때 게이지가 회복됩니다.",
            "   - 라이프 70 이하: 라이프가 낮아질수록 미스 데미지가 대폭 증가합니다.",
            "   - 무적모드(INVINCIBLE)가 켜져 있으면 폭사하지 않습니다.",
            "",
            "3. 기본 제공 노트 스킨 2종 [★NEW]",
            "   - Default_Bar : 화면을 꽉 채우는 가로 직사각형 형태의 세련된 스킨",
            "   - Default_Circle : 직관적이고 클래식한 원형 형태의 스킨",
            "   (SETTING -> GRAPHIC/AUDIO -> NOTE SKIN에서 변경 가능)",
            "",
            "4. 단축키 가이드",
            "   - [F5] : 인게임 도중 즉시 리스타트",
            "   - [ESC] : 플레이 중단 및 뒤로 가기",
            "   - 게임 중 [UP]/[DOWN] : 판정 싱크(오프셋) 미세 조절"
        ]
        start_y = SCREEN_HEIGHT - 130
        for line in instructions:
            color = arcade.color.CYAN if any(line.startswith(f"{num}.") for num in range(1, 5)) else arcade.color.WHITE
            arcade.draw_text(line, 40, start_y, color, font_size=12)
            start_y -= 22
        arcade.draw_text("Press ESC to return to Main Menu", SCREEN_WIDTH / 2, 40, arcade.color.LIGHT_GRAY, font_size=14, anchor_x="center", bold=True)
    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE: self.window.show_view(MainMenuView())


# ==============================================================================
# [1] 메인 메뉴 화면
# ==============================================================================
class MainMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected_index = 0
        self.menu_items = ["PLAY GAME", "SETTING", "HOW TO PLAY", "EXIT"]
        
        self.in_setting_menu = False
        self.current_tab = "GAMEPLAY"
        
        self.gameplay_items = ["TAB: GRAPHIC/AUDIO", "KEY SETTING", "AUTO PLAY", "INVINCIBLE MODE", "HARD JUDGE MODE", "PERFECT MODE", "BACK"]
        self.graphic_items = ["TAB: GAME PLAY", "NOTE SKIN", "SCROLL SPEED", "AUDIO VOLUME", "SHOW FAST/SLOW", "BACK"]
        
        self.setting_index = 0
        self.changing_key_idx = -1 
        self.error_message = ""      
        self.error_timer = 0.0       

        sound_path = os.path.join(BASE_DIR, "audio", "minecraft_click.mp3")
        self.click_sound = arcade.load_sound(sound_path) if os.path.exists(sound_path) else None

    def play_click(self):
        if self.click_sound: arcade.play_sound(self.click_sound, volume=GAME_CONFIG["VOLUME"] / 100.0)
    def on_show_view(self): arcade.set_background_color(arcade.color.DARK_BLUE_GRAY); refresh_note_skins()
    def on_update(self, delta_time: float):
        if self.error_timer > 0:
            self.error_timer -= delta_time
            if self.error_timer <= 0: self.error_message = ""

    def on_draw(self):
        self.clear()
        arcade.draw_text("DJMAX PYTHON", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 100, arcade.color.GOLD, font_size=36, anchor_x="center", bold=True)
        
        if not self.in_setting_menu:
            for i, item in enumerate(self.menu_items):
                color = arcade.color.WHITE if i == self.selected_index else arcade.color.GRAY
                arcade.draw_text(item, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30 - (i * 60), color, font_size=24 if i == self.selected_index else 20, anchor_x="center")
            if self.error_message and self.changing_key_idx == -1:
                arcade.draw_text(self.error_message, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 200, (255, 100, 100), font_size=14, anchor_x="center", bold=True)
            arcade.draw_text("UP/DOWN: Move | ENTER: Select", SCREEN_WIDTH / 2, 50, arcade.color.LIGHT_GRAY, font_size=12, anchor_x="center")
        
        elif self.in_setting_menu and self.changing_key_idx == -1:
            gp_tab_color = arcade.color.GOLD if self.current_tab == "GAMEPLAY" else arcade.color.GRAY
            ga_tab_color = arcade.color.GOLD if self.current_tab == "GRAPHIC_AUDIO" else arcade.color.GRAY
            arcade.draw_text("[ GAME PLAY ]", SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT - 170, gp_tab_color, font_size=16, anchor_x="center", bold=(self.current_tab == "GAMEPLAY"))
            arcade.draw_text("[ GRAPHIC/AUDIO ]", SCREEN_WIDTH / 2 + 100, SCREEN_HEIGHT - 170, ga_tab_color, font_size=16, anchor_x="center", bold=(self.current_tab == "GRAPHIC_AUDIO"))
            arcade.draw_line(40, SCREEN_HEIGHT - 190, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 190, arcade.color.DARK_GRAY, 2)

            active_items = self.gameplay_items if self.current_tab == "GAMEPLAY" else self.graphic_items
            for i, item in enumerate(active_items):
                color = arcade.color.WHITE if i == self.setting_index else arcade.color.GRAY
                size = 19 if i == self.setting_index else 16
                display_text = item
                
                if item.startswith("TAB:"):
                    display_text = f"▶ SWITCH TO {item.split(': ')[1]} ◀"
                    if i == self.setting_index: color = arcade.color.CYAN
                elif item == "KEY SETTING": display_text = "⚙ KEY CONFIGURATION"
                elif item == "AUTO PLAY": display_text = f"AUTO PLAY:  [ {'ON (자동)' if GAME_CONFIG['AUTO_PLAY'] else 'OFF'} ]"
                elif item == "INVINCIBLE MODE": display_text = f"INVINCIBLE MODE:  [ {'ON (무적)' if GAME_CONFIG['INVINCIBLE_MODE'] else 'OFF'} ]"
                elif item == "HARD JUDGE MODE": display_text = f"HARD JUDGE:  [ {'ON' if GAME_CONFIG['HARD_JUDGE'] else 'OFF'} ]"
                elif item == "PERFECT MODE": display_text = f"PERFECT MODE:  [ {'ON' if GAME_CONFIG['PERFECT_MODE'] else 'OFF'} ]"
                elif item == "NOTE SKIN": display_text = f"NOTE SKIN:  < [ {GAME_CONFIG['NOTE_SKIN']} ] >"
                elif item == "SCROLL SPEED": display_text = f"SCROLL SPEED:  < Speed {GAME_CONFIG['SCROLL_SPEED']:.1f} > (◀ / ▶)"
                elif item == "AUDIO VOLUME": display_text = f"AUDIO VOLUME:  < {GAME_CONFIG['VOLUME']}% > (◀ / ▶)"
                elif item == "SHOW FAST/SLOW": display_text = f"SHOW FAST/SLOW:  [ {'ON' if GAME_CONFIG['SHOW_ACCURACY'] else 'OFF'} ]"
                elif item == "BACK": display_text = "↩ Save & Return"
                
                arcade.draw_text(display_text, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 130 - (i * 38), color, font_size=size, anchor_x="center")
            arcade.draw_text("UP/DOWN: Move | ENTER: Click/Toggle | LEFT/RIGHT: Adjust Value", SCREEN_WIDTH / 2, 40, arcade.color.LIGHT_GRAY, font_size=12, anchor_x="center")
        else:
            arcade.draw_text("KEY CONFIGURATION", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 120, arcade.color.CYAN, font_size=24, anchor_x="center")
            for i in range(4):
                is_target = (i == self.changing_key_idx)
                arcade.draw_text(f"{'> ' if is_target else '  '}Lane {i+1}: {GAME_CONFIG['KEY_NAMES'][i] or 'EMPTY'}", SCREEN_WIDTH / 2 - 80, SCREEN_HEIGHT / 2 + 20 - (i * 40), arcade.color.YELLOW if is_target else arcade.color.WHITE, font_size=18)
            if self.error_message: arcade.draw_text(self.error_message, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 160, (255, 100, 100), font_size=14, anchor_x="center", bold=True)
            arcade.draw_text("Press ANY KEY to bind, or ESC to finish", SCREEN_WIDTH / 2, 50, arcade.color.LIGHT_GRAY, font_size=12, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if not self.in_setting_menu:
            if key == arcade.key.UP: self.selected_index = (self.selected_index - 1) % len(self.menu_items); self.play_click()
            elif key == arcade.key.DOWN: self.selected_index = (self.selected_index + 1) % len(self.menu_items); self.play_click()
            elif key == arcade.key.ENTER:
                self.play_click()
                if self.selected_index == 0:
                    if None in GAME_CONFIG["KEYS"]: self.error_message = "오류: 모든 레인의 키를 지정해야 합니다!"; self.error_timer = 2.0; return
                    self.window.show_view(SongSelectView())
                elif self.selected_index == 1: self.in_setting_menu = True; self.current_tab = "GAMEPLAY"; self.setting_index = 0
                elif self.selected_index == 2: self.window.show_view(HowToPlayView())
                elif self.selected_index == 3: arcade.exit()
        elif self.in_setting_menu and self.changing_key_idx == -1:
            if key == arcade.key.ESCAPE: self.play_click(); self.in_setting_menu = False; return
            active_items = self.gameplay_items if self.current_tab == "GAMEPLAY" else self.graphic_items
            if key == arcade.key.UP: self.setting_index = (self.setting_index - 1) % len(active_items); self.play_click()
            elif key == arcade.key.DOWN: self.setting_index = (self.setting_index + 1) % len(active_items); self.play_click()
            elif key == arcade.key.LEFT:
                active_item = active_items[self.setting_index]
                if active_item == "SCROLL SPEED": GAME_CONFIG["SCROLL_SPEED"] = round(max(1.0, GAME_CONFIG["SCROLL_SPEED"] - 0.1), 1); self.play_click()
                elif active_item == "AUDIO VOLUME": GAME_CONFIG["VOLUME"] = max(0, GAME_CONFIG["VOLUME"] - 10); self.play_click()
            elif key == arcade.key.RIGHT:
                active_item = active_items[self.setting_index]
                if active_item == "SCROLL SPEED": GAME_CONFIG["SCROLL_SPEED"] = round(min(10.0, GAME_CONFIG["SCROLL_SPEED"] + 0.1), 1); self.play_click()
                elif active_item == "AUDIO VOLUME": GAME_CONFIG["VOLUME"] = min(100, GAME_CONFIG["VOLUME"] + 10); self.play_click()
            elif key == arcade.key.ENTER:
                self.play_click()
                active_item = active_items[self.setting_index]
                if active_item.startswith("TAB:"): self.current_tab = "GRAPHIC_AUDIO" if self.current_tab == "GAMEPLAY" else "GAMEPLAY"; self.setting_index = 0
                elif active_item == "KEY SETTING": self.changing_key_idx = 0; self.error_message = ""
                elif active_item == "AUTO PLAY": GAME_CONFIG["AUTO_PLAY"] = not GAME_CONFIG["AUTO_PLAY"]
                elif active_item == "INVINCIBLE MODE": GAME_CONFIG["INVINCIBLE_MODE"] = not GAME_CONFIG["INVINCIBLE_MODE"]
                elif active_item == "HARD JUDGE MODE": GAME_CONFIG["HARD_JUDGE"] = not GAME_CONFIG["HARD_JUDGE"]
                elif active_item == "PERFECT MODE": GAME_CONFIG["PERFECT_MODE"] = not GAME_CONFIG["PERFECT_MODE"]
                elif active_item == "NOTE SKIN":
                    try: curr_idx = AVAILABLE_SKINS.index(GAME_CONFIG["NOTE_SKIN"])
                    except: curr_idx = 0
                    GAME_CONFIG["NOTE_SKIN"] = AVAILABLE_SKINS[(curr_idx + 1) % len(AVAILABLE_SKINS)]
                elif active_item == "SHOW FAST/SLOW": GAME_CONFIG["SHOW_ACCURACY"] = not GAME_CONFIG["SHOW_ACCURACY"]
                elif active_item == "BACK": self.in_setting_menu = False
        else:
            if key == arcade.key.ESCAPE: self.play_click(); self.changing_key_idx = -1; return
            for idx, existing_key in enumerate(GAME_CONFIG["KEYS"]):
                if existing_key is not None and existing_key == key:
                    if idx < self.changing_key_idx: self.error_message = f"오류: Lane {idx+1}과 중복!"; self.error_timer = 2.0; return
                    else: GAME_CONFIG["KEYS"][idx] = GAME_CONFIG["KEY_NAMES"][idx] = None
            self.play_click()
            GAME_CONFIG["KEYS"][self.changing_key_idx] = key
            GAME_CONFIG["KEY_NAMES"][self.changing_key_idx] = chr(key).upper() if key < 256 else f"K_{key}"
            if self.changing_key_idx < 3: self.changing_key_idx += 1
            else: self.changing_key_idx = -1


# ==============================================================================
# [2] 곡 선택 화면
# ==============================================================================
class SongSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        self.map_list = []
        self.base_extract_path = os.path.join(BASE_DIR, "temp_map")
        self.selected_index = 0
        self.load_all_osz_packages()

    def load_all_osz_packages(self):
        os.makedirs(self.base_extract_path, exist_ok=True)
        search_paths = [BASE_DIR, os.path.dirname(BASE_DIR), self.base_extract_path]
        osz_files = []
        for p in search_paths:
            if os.path.exists(p):
                for f in os.listdir(p):
                    if f.endswith('.osz') and os.path.join(p, f) not in [x[0] for x in osz_files]: osz_files.append((os.path.join(p, f), f))
        for full_path, osz in osz_files:
            sp_path = os.path.join(self.base_extract_path, osz.replace('.osz', ''))
            if not os.path.exists(sp_path) or len(os.listdir(sp_path)) == 0:
                try:
                    os.makedirs(sp_path, exist_ok=True)
                    with zipfile.ZipFile(full_path, 'r') as z: z.extractall(sp_path)
                except: pass
        if os.path.exists(self.base_extract_path):
            for sub in os.listdir(self.base_extract_path):
                fp = os.path.join(self.base_extract_path, sub)
                if os.path.isdir(fp):
                    audio = next((os.path.join(fp, f) for f in os.listdir(fp) if f.lower().endswith((".mp3", ".ogg"))), None)
                    for osu in [f for f in os.listdir(fp) if f.endswith(".osu")]:
                        self.map_list.append({"osu_path": os.path.join(fp, osu), "audio_path": audio, "display_name": osu.replace('.osu', '')})
        self.map_list.sort(key=lambda x: x['display_name'])

    def on_show_view(self): arcade.set_background_color(arcade.color.CHARCOAL)
    def on_draw(self):
        self.clear()
        arcade.draw_text("SELECT DIFFICULTY", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 80, arcade.color.WHITE, font_size=24, anchor_x="center", bold=True)
        if not self.map_list:
            arcade.draw_text("No .osu maps found! Put .osz here.", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, arcade.color.RED, font_size=16, anchor_x="center")
            return
        start = max(0, self.selected_index - 5)
        for i in range(start, min(len(self.map_list), start + 12)):
            name = self.map_list[i]["display_name"]
            arcade.draw_text(f"{'▶ ' if i == self.selected_index else '  '}{name[:32]+'...' if len(name)>35 else name}", 40, SCREEN_HEIGHT - 200 - ((i-start)*40), arcade.color.ELECTRIC_BLUE if i == self.selected_index else arcade.color.LIGHT_GRAY, font_size=13)
        arcade.draw_text("UP/DOWN: Move | ENTER: Start | ESC: Back", SCREEN_WIDTH / 2, 50, arcade.color.LIGHT_GRAY, font_size=12, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE: self.window.show_view(MainMenuView()); return
        if self.map_list:
            if key == arcade.key.UP: self.selected_index = (self.selected_index - 1) % len(self.map_list)
            elif key == arcade.key.DOWN: self.selected_index = (self.selected_index + 1) % len(self.map_list)
            elif key == arcade.key.ENTER:
                target = self.map_list[self.selected_index]
                GAME_CONFIG["SELECTED_OSU"], GAME_CONFIG["SELECTED_AUDIO"] = target["osu_path"], target["audio_path"]
                game_view = GameView()
                game_view.setup()
                self.window.show_view(game_view)


# ==============================================================================
# [3] 게임오버 화면
# ==============================================================================
class GameOverView(arcade.View):
    def __init__(self):
        super().__init__()
        self.selected_idx = 0
        self.choices = ["REPLAY (다시 시도)", "MAIN MENU (메인 메뉴)"]

    def on_show_view(self): arcade.set_background_color(arcade.color.BLACK)
    def on_draw(self):
        self.clear()
        arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 250, arcade.color.RED, font_size=40, anchor_x="center", bold=True)
        for i, choice in enumerate(self.choices):
            color = arcade.color.WHITE if i == self.selected_idx else arcade.color.DARK_GRAY
            arcade.draw_text(f"{'▶ ' if i == self.selected_idx else '  '}{choice}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - (i * 60), color, font_size=22 if i == self.selected_idx else 18, anchor_x="center", bold=(i == self.selected_idx))
        arcade.draw_text("UP/DOWN: Move | ENTER: Select", SCREEN_WIDTH / 2, 80, arcade.color.GRAY, font_size=12, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP: self.selected_idx = (self.selected_idx - 1) % len(self.choices)
        elif key == arcade.key.DOWN: self.selected_idx = (self.selected_idx + 1) % len(self.choices)
        elif key == arcade.key.ENTER:
            if self.selected_idx == 0:
                game_view = GameView()
                game_view.setup()
                self.window.show_view(game_view)
            else: self.window.show_view(MainMenuView())


# ==============================================================================
# [4] 인게임 구동 엔진 (★ 바 / 서클 기본 스킨 대응 통합 렌더러 적용)
# ==============================================================================
class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.notes_to_spawn = []
        self.active_notes = arcade.SpriteList()
        self.speed_timeline = [] 
        self.score = 0
        self.combo = 0
        self.start_time = None
        self.music_player = None
        self.total_notes_count = 0
        self.single_note_perfect_score = 0.0
        self.processed_judgements_count = 0
        self.offset = INITIAL_OFFSET
        self.holding_notes = [None, None, None, None]
        self.key_pressed_states = [False, False, False, False]
        self.life = 100.0 

        self.judgement_text = arcade.Text("", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60, arcade.color.WHITE, 28, align="center", anchor_x="center", bold=True)
        self.sub_timing_text = arcade.Text("", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 25, arcade.color.WHITE, 18, align="center", anchor_x="center", bold=True)
        self.rate_text = arcade.Text("100.00%", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 5, (255, 235, 150), 16, align="center", anchor_x="center")
        self.judgement_timer = 0.0
        self.score_text = arcade.Text("Score: 0", 20, SCREEN_HEIGHT - 40, arcade.color.WHITE, 18)
        self.combo_text = arcade.Text("0", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3 * 2, arcade.color.WHITE, 45, align="center", anchor_x="center")
        self.combo_label = arcade.Text("COMBO", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3 * 2 - 30, arcade.color.GRAY, 14, align="center", anchor_x="center")
        self.offset_text = arcade.Text("", 20, 20, arcade.color.GRAY, 12)
        self.mode_indicator_text = arcade.Text("", SCREEN_WIDTH - 20, 20, arcade.color.LIGHT_GRAY, 12, anchor_x="right")

    def setup(self):
        arcade.set_background_color(arcade.color.BLACK_OLIVE)
        self.parse_osu(GAME_CONFIG["SELECTED_OSU"])
        self.total_notes_count = sum(2 if note.is_ln else 1 for note in self.notes_to_spawn)
        self.single_note_perfect_score = MAX_SCORE / self.total_notes_count if self.total_notes_count > 0 else 0

        audio = GAME_CONFIG["SELECTED_AUDIO"]
        if audio and os.path.exists(audio):
            self.music_player = arcade.play_sound(arcade.load_sound(audio), volume=GAME_CONFIG["VOLUME"] / 100.0)
        self.start_time = time.perf_counter()
        
        modes = []
        if GAME_CONFIG["AUTO_PLAY"]: modes.append("AUTO")
        if GAME_CONFIG["INVINCIBLE_MODE"]: modes.append("INVINCIBLE")
        if GAME_CONFIG["HARD_JUDGE"]: modes.append("HARD")
        if GAME_CONFIG["PERFECT_MODE"]: modes.append("PERFECT")
        self.mode_indicator_text.text = " | ".join(modes) if modes else "NORMAL JUDGE"

    def trigger_restart(self):
        if self.music_player: arcade.stop_sound(self.music_player)
        new_game = GameView()
        new_game.setup()
        self.window.show_view(new_game)

    def parse_osu(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f: content = f.read()
        raw_timing_points = []
        if "[TimingPoints]" in content:
            timing_section = content.split("[TimingPoints]")[1].split("[")[0].strip()
            for line in timing_section.split('\n'):
                line = line.strip()
                if not line or ',' not in line: continue
                parts = line.split(',')
                try: raw_timing_points.append({'time': float(parts[0]) / 1000.0, 'value': float(parts[1]), 'inherited': int(parts[6]) if len(parts) >= 7 else 1})
                except: continue
        raw_timing_points.sort(key=lambda x: x['time'])

        speed_ratio = GAME_CONFIG["SCROLL_SPEED"] / 5.0
        calculated_base_multiplier = BASE_SPEED_MULTIPLIER * speed_ratio
        base_bpm = current_bpm = 120.0
        for tp in raw_timing_points:
            if tp['inherited'] == 1 and tp['value'] > 0:
                base_bpm = current_bpm = 60000.0 / tp['value']
                break

        accumulated_scroll = 0.0
        last_time = -100.0 
        current_speed = base_bpm * calculated_base_multiplier

        for tp in raw_timing_points:
            t = tp['time']
            duration = t - last_time
            if duration > 0:
                accumulated_scroll += duration * current_speed
                self.speed_timeline.append((last_time, t, current_speed, accumulated_scroll - duration * current_speed))
            if tp['inherited'] == 1 and tp['value'] > 0:
                current_bpm = 60000.0 / tp['value']
                current_speed = current_bpm * calculated_base_multiplier
            elif tp['inherited'] == 0 and tp['value'] < 0:
                current_speed = current_bpm * calculated_base_multiplier * (100.0 / abs(tp['value']))
            last_time = t
        self.speed_timeline.append((last_time, 9999.0, current_speed, accumulated_scroll))

        if "[HitObjects]" not in content: return
        objects_section = content.split("[HitObjects]")[-1].strip()
        
        skin_name = GAME_CONFIG["NOTE_SKIN"]
        custom_texture = None
        # 내장 스킨 2종이 아닌 외부 PNG 파일을 로드하려 할 때만 활성화
        if skin_name not in ["Default_Bar", "Default_Circle"] and os.path.exists(os.path.join(SKIN_DIR, f"{skin_name}.png")):
            custom_texture = arcade.load_texture(os.path.join(SKIN_DIR, f"{skin_name}.png"))

        for line in objects_section.split('\n'):
            line = line.strip()
            if not line or ',' not in line: continue
            parts = line.split(',')
            if len(parts) < 5: continue
            lane = min(3, int(parts[0]) // 128)
            hit_time = int(parts[2]) / 1000.0
            is_ln = bool(int(parts[3]) & 128)
            end_time = hit_time
            if is_ln and len(parts) >= 6:
                try: end_time = int(parts[5].split(':')[0]) / 1000.0
                except: is_ln = False

            note = arcade.Sprite()
            if custom_texture:
                note.texture = custom_texture
                note.width = note.height = NOTE_RADIUS * 2
            
            note.lane = lane
            note.hit_time = hit_time
            note.is_ln = is_ln
            note.end_time = end_time
            note.is_holding = False
            note.center_x = LANE_START_X + (lane * LANE_WIDTH)
            note.absolute_y = self.get_scroll_position(hit_time)
            if is_ln: note.absolute_end_y = self.get_scroll_position(end_time)
            self.notes_to_spawn.append(note)
        self.notes_to_spawn.sort(key=lambda n: n.hit_time)

    def get_scroll_position(self, target_time):
        for start_t, end_t, speed, start_scroll in self.speed_timeline:
            if start_t <= target_time <= end_t: return start_scroll + (target_time - start_t) * speed
        return target_time * 500.0 

    def calculate_judgement(self, diff, raw_diff=0.0):
        diff_ms = diff * 1000.0
        m = 0.5 if GAME_CONFIG["HARD_JUDGE"] else 1.0
        d = "FAST" if raw_diff < 0 else "SLOW"
        if diff_ms <= (41.6 * m): return "MAX 100%", 1.00, "" 
        elif diff_ms <= (83.2 * m): return "MAX 90%", 0.90, d
        elif diff_ms <= (124.8 * m): return "MAX 80%", 0.80, d
        elif diff_ms <= (166.4 * m): return "MAX 70%", 0.70, d
        elif diff_ms <= (208.0 * m): return "MAX 60%", 0.60, d
        elif diff_ms <= (249.6 * m): return "MAX 50%", 0.50, d
        elif diff_ms <= (291.2 * m): return "MAX 40%", 0.40, d
        elif diff_ms <= (332.8 * m): return "MAX 30%", 0.30, d
        elif diff_ms <= (374.4 * m): return "MAX 20%", 0.20, d
        elif diff_ms <= (416.0 * m): return "MAX 10%", 0.10, d
        elif diff_ms <= (457.6 * m): return "MAX 1%", 0.01, d
        return "BREAK", 0.00, ""

    def on_update(self, delta_time):
        if not self.start_time: return
        elapsed = (time.perf_counter() - self.start_time) - self.offset
        current_player_scroll = self.get_scroll_position(elapsed)
        if self.judgement_timer > 0: self.judgement_timer -= delta_time

        if GAME_CONFIG["AUTO_PLAY"]:
            for note in list(self.active_notes):
                if not getattr(note, 'is_holding', False) and elapsed >= note.hit_time:
                    self.key_pressed_states[note.lane] = True
                    self.trigger_judgement("MAX 100%", 1.00, "")
                    if note.is_ln:
                        note.is_holding = True
                        self.holding_notes[note.lane] = note
                    else: note.remove_from_sprite_lists()
            for lane in range(4):
                held_note = self.holding_notes[lane]
                if held_note and elapsed >= held_note.end_time:
                    self.key_pressed_states[lane] = False
                    self.trigger_judgement("MAX 100%", 1.00, "")
                    if held_note in self.active_notes: held_note.remove_from_sprite_lists()
                    self.holding_notes[lane] = None

        while self.notes_to_spawn and self.notes_to_spawn[0].hit_time <= elapsed + 2.0:
            self.active_notes.append(self.notes_to_spawn.pop(0))

        missed = []
        for note in self.active_notes:
            if getattr(note, 'is_holding', False):
                note.center_y = HIT_LINE_Y
                if not GAME_CONFIG["AUTO_PLAY"] and elapsed - note.end_time > 0.4992:
                    missed.append(note)
                    if self.holding_notes[note.lane] == note: self.holding_notes[note.lane] = None
            else:
                note.center_y = HIT_LINE_Y + (note.absolute_y - current_player_scroll)
                if not GAME_CONFIG["AUTO_PLAY"] and elapsed - note.hit_time > 0.4992: missed.append(note)

        for note in missed:
            if note in self.active_notes: note.remove_from_sprite_lists()
            self.trigger_judgement("BREAK")

        self.score_text.text = f"Score: {round(self.score)}"
        self.combo_text.text = f"{self.combo}"
        self.offset_text.text = f"Offset: {int(self.offset * 1000)}ms"

    def on_draw(self):
        self.clear()
        elapsed = (time.perf_counter() - self.start_time) - self.offset
        current_player_scroll = self.get_scroll_position(elapsed)
        skin_name = GAME_CONFIG["NOTE_SKIN"]
        
        # 1. 키 빔(Beam) 효과 그리기
        for i in range(4):
            x = LANE_START_X + (i * LANE_WIDTH)
            if self.key_pressed_states[i]:
                beam_height = int(SCREEN_HEIGHT / 4 * 3)
                segments = 50
                segment_height = beam_height / segments
                for j in range(segments):
                    current_y = (j * segment_height) + (segment_height / 2)
                    alpha = int(60 * ((1.0 - (j / segments)) ** 1.5))
                    if alpha > 0: 
                        arcade.draw_rect_filled(arcade.XYWH(x, current_y, LANE_WIDTH, segment_height), (255, 255, 255, alpha))
                arcade.draw_circle_filled(x, HIT_LINE_Y, NOTE_RADIUS + 8, (255, 255, 255, 90))

        # 2. 판정선 가이드라인 디자인 (스킨 종류에 맞춰 변화)
        for i in range(4):
            x_pos = LANE_START_X + (i * LANE_WIDTH)
            if skin_name == "Default_Bar":
                arcade.draw_rect_outline(arcade.XYWH(x_pos, HIT_LINE_Y, LANE_WIDTH - 4, 20), arcade.color.DARK_GRAY, 2)
            else:
                arcade.draw_circle_outline(x_pos, HIT_LINE_Y, NOTE_RADIUS + 5, arcade.color.GRAY, 2)
                
            if elapsed <= 2.0 and int(elapsed * 3.5) % 2 == 0:
                arcade.draw_text(GAME_CONFIG["KEY_NAMES"][i], x_pos, HIT_LINE_Y - 8, arcade.color.YELLOW, font_size=16, anchor_x="center", bold=True)

        # 3. 롱노트 바디(줄기) 그리기
        for note in self.active_notes:
            if getattr(note, 'is_ln', False):
                head_y = note.center_y
                tail_y = HIT_LINE_Y + (note.absolute_end_y - current_player_scroll)
                actual_head_y = max(head_y, HIT_LINE_Y)
                if tail_y > actual_head_y:
                    # 바 스킨일 때는 몸통을 넓게, 서클이나 이미지 스킨일 때는 약간 슬림하게 그리기
                    w_factor = LANE_WIDTH - 8 if skin_name == "Default_Bar" else NOTE_RADIUS * 1.5
                    arcade.draw_rect_filled(arcade.XYWH(note.center_x, actual_head_y + (tail_y - actual_head_y) / 2, w_factor, tail_y - actual_head_y), (255, 165, 0, 100))
                    
                    # 롱노트 꼬리(끝부분) 마감선 렌더링
                    if skin_name == "Default_Bar":
                        arcade.draw_rect_filled(arcade.XYWH(note.center_x, tail_y, LANE_WIDTH - 4, 16), arcade.color.ORANGE)
                    elif skin_name == "Default_Circle":
                        arcade.draw_circle_filled(note.center_x, tail_y, NOTE_RADIUS, arcade.color.ORANGE)

        # 4. 일반 단노트 & 롱노트 머리 렌더러
        for note in self.active_notes:
            note_color = arcade.color.ORANGE if note.is_ln else arcade.color.ELECTRIC_BLUE
            
            if skin_name == "Default_Bar":
                # [★스킨 1] 가로 바 형태
                arcade.draw_rect_filled(arcade.XYWH(note.center_x, note.center_y, LANE_WIDTH - 4, 20), note_color)
                arcade.draw_rect_filled(arcade.XYWH(note.center_x, note.center_y, LANE_WIDTH - 8, 4), arcade.color.WHITE)
            elif skin_name == "Default_Circle":
                # [★스킨 2] 전통적인 원형 형태
                arcade.draw_circle_filled(note.center_x, note.center_y, NOTE_RADIUS, note_color)
                arcade.draw_circle_filled(note.center_x, note.center_y, NOTE_RADIUS - 8, arcade.color.WHITE, num_segments=16)
                arcade.draw_circle_filled(note.center_x, note.center_y, NOTE_RADIUS - 14, note_color, num_segments=16)
            else:
                # [★스킨 3] 커스텀 외부 이미지 스프라이트 형태
                note.draw()
        
        # 5. UI 시스템 (라이프 바, 스코어, 판정 등)
        arcade.draw_rect_outline(arcade.XYWH(SCREEN_WIDTH - 35, SCREEN_HEIGHT / 2, 20, 400), arcade.color.DARK_GRAY, 2)
        life_bar_h = int(400 * (self.life / 100.0))
        if life_bar_h > 0:
            bar_color = arcade.color.GREEN if self.life >= 80 else (arcade.color.RED if self.life <= 70 else arcade.color.ORANGE)
            if GAME_CONFIG["INVINCIBLE_MODE"]: bar_color = arcade.color.CYAN 
            arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH - 35, (SCREEN_HEIGHT / 2 - 200) + (life_bar_h / 2), 18, life_bar_h), bar_color)
        arcade.draw_text(f"{int(self.life)}%", SCREEN_WIDTH - 35, SCREEN_HEIGHT / 2 + 215, arcade.color.WHITE, font_size=11, anchor_x="center")

        self.score_text.draw()
        if self.combo > 0:
            self.combo_text.draw()
            self.combo_label.draw()
        if self.judgement_timer > 0: 
            self.judgement_text.draw()
            if GAME_CONFIG["SHOW_ACCURACY"] and self.sub_timing_text.text: self.sub_timing_text.draw()
        self.rate_text.draw() 
        self.mode_indicator_text.draw()

    def trigger_judgement(self, type_str, weight=0.0, timing_dir=""):
        self.processed_judgements_count += 1
        if type_str == "BREAK":
            self.combo = 0
            self.judgement_text.color = arcade.color.RED
            self.sub_timing_text.text = ""
            if not GAME_CONFIG["INVINCIBLE_MODE"]:
                if self.life <= 70.0:
                    damage_factor = 1.0 + ((70.0 - self.life) / 70.0) * 1.5 
                    self.life = max(0.0, self.life - (8.0 * damage_factor))
                else: self.life = max(0.0, self.life - 6.0) 
        else:
            self.combo += 1
            self.score += self.single_note_perfect_score * weight
            if type_str == "MAX 100%": self.judgement_text.color = (255, 215, 0) 
            elif type_str == "MAX 90%": self.judgement_text.color = (255, 255, 200)
            elif type_str in ["MAX 80%", "MAX 70%", "MAX 60%", "MAX 50%"]: self.judgement_text.color = arcade.color.CYAN
            else: self.judgement_text.color = arcade.color.LIGHT_GRAY 
            
            self.sub_timing_text.text = timing_dir
            self.sub_timing_text.color = (255, 120, 120) if timing_dir == "FAST" else (120, 150, 255)

            if self.life >= 80.0 and weight >= 0.80: self.life = min(100.0, self.life + 1.2)
            elif self.life <= 70.0 and weight < 0.50:
                if not GAME_CONFIG["INVINCIBLE_MODE"]: self.life = max(0.0, self.life - 2.0)
                
        self.judgement_text.text = type_str
        max_possible = self.single_note_perfect_score * self.processed_judgements_count
        if max_possible > 0: self.rate_text.text = f"{(self.score / max_possible) * 100.0:.2f}%"
        self.judgement_timer = 0.45
        
        if self.life <= 0.0:
            if self.music_player: arcade.stop_sound(self.music_player)
            self.window.show_view(GameOverView())
            return

        if GAME_CONFIG["PERFECT_MODE"] and type_str != "MAX 100%": self.trigger_restart()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.F5: self.trigger_restart(); return
        if key == arcade.key.ESCAPE:
            if self.music_player: arcade.stop_sound(self.music_player)
            self.window.show_view(SongSelectView()); return

        if GAME_CONFIG["AUTO_PLAY"]:
            if key == arcade.key.UP: self.offset += 0.005 
            elif key == arcade.key.DOWN: self.offset -= 0.005
            return

        hit_timestamp = time.perf_counter()
        if key in GAME_CONFIG["KEYS"]:
            if None in GAME_CONFIG["KEYS"]: return 
            lane = GAME_CONFIG["KEYS"].index(key)
            self.key_pressed_states[lane] = True
            self.check_hit(lane, hit_timestamp)
        elif key == arcade.key.UP: self.offset += 0.005 
        elif key == arcade.key.DOWN: self.offset -= 0.005

    def on_key_release(self, key, modifiers):
        if GAME_CONFIG["AUTO_PLAY"]: return 
        if key in GAME_CONFIG["KEYS"]:
            if None in GAME_CONFIG["KEYS"]: return 
            lane = GAME_CONFIG["KEYS"].index(key)
            self.key_pressed_states[lane] = False
            held_note = self.holding_notes[lane]
            if held_note:
                elapsed = (time.perf_counter() - self.start_time) - self.offset
                judge, weight, timing_dir = self.calculate_judgement(abs(elapsed - held_note.end_time), elapsed - held_note.end_time)
                if judge and judge != "BREAK": self.trigger_judgement(judge, weight, timing_dir)
                else: self.trigger_judgement("BREAK")
                if held_note in self.active_notes: held_note.remove_from_sprite_lists()
                self.holding_notes[lane] = None

    def check_hit(self, lane, hit_timestamp):
        elapsed = (hit_timestamp - self.start_time) - self.offset
        target_note = None
        for note in self.active_notes:
            if note.lane == lane and not getattr(note, 'is_holding', False):
                target_note = note; break
        if target_note:
            judge, weight, timing_dir = self.calculate_judgement(abs(elapsed - target_note.hit_time), elapsed - target_note.hit_time)
            if judge and judge != "BREAK":
                self.trigger_judgement(judge, weight, timing_dir)
                if target_note.is_ln:
                    target_note.is_holding = True
                    self.holding_notes[lane] = target_note
                else: target_note.remove_from_sprite_lists()
            else:
                self.trigger_judgement("BREAK")
                target_note.remove_from_sprite_lists()

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "DJMAX PYTHON Workbench")
    window.show_view(MainMenuView())
    arcade.run()

if __name__ == "__main__":
    main()