import sys

from pygame import Rect

from .base import BaseScene


class PauseScene(BaseScene):
    def on_enter(self, ctx=None):
        self.btn_w, self.btn_h = 240, 60
        self.color_btn = (70, 70, 70)
        self.color_hover = (110, 110, 110)
        self.color_text = (255, 255, 255)
        self.hovered = None

        from pgzero import music
        from pgzero.loaders import images as pgz_images

        play_scene = self._manager._scenes.get("play")
        if play_scene and ctx:
            play_scene.show_pause_button = False
            play_scene.show_mute_button = False

            ctx.screen.clear()
            play_scene.draw(ctx)

            if not play_scene.music_muted:
                music.set_volume(music.get_volume() * 0.5)

        self.btn_mute_img = pgz_images.load("ui/mute")
        self.btn_unmute_img = pgz_images.load("ui/unmute")
        self.btn_size = 36
        self.btn_margin = 30

    def draw(self, ctx):
        sw, sh = ctx.screen.width, ctx.screen.height
        center_x = sw // 2
        center_y = sh // 2

        ctx.screen.draw.text(
            "Game Paused",
            center=(center_x, center_y - 160),
            fontsize=64,
            color=self.color_text,
            shadow=(2, 2),
        )
        play_scene = self._manager._scenes.get("play")
        if play_scene:
            btn_img = self.btn_unmute_img if play_scene.music_muted else self.btn_mute_img
            btn_x = ctx.screen.width - self.btn_size - self.btn_margin
            btn_y = self.btn_margin
            ctx.screen.blit(btn_img, (btn_x, btn_y))
            self.mute_button_rect = Rect(btn_x, btn_y, self.btn_size, self.btn_size)
        else:
            self.mute_button_rect = None
        spacing = 80
        start_y = center_y - 60
        buttons = {
            "resume": Rect(center_x - self.btn_w // 2, start_y, self.btn_w, self.btn_h),
            "restart": Rect(center_x - self.btn_w // 2, start_y + spacing, self.btn_w, self.btn_h),
            "menu": Rect(center_x - self.btn_w // 2, start_y + spacing * 2, self.btn_w, self.btn_h),
            "exit": Rect(center_x - self.btn_w // 2, start_y + spacing * 3, self.btn_w, self.btn_h),
        }
        self.buttons = buttons

        mouse_x, mouse_y = getattr(ctx, "mouse_pos", (0, 0))
        self.hovered = None

        for name, rect in self.buttons.items():
            is_hover = rect.collidepoint(mouse_x, mouse_y)
            if is_hover:
                self.hovered = name
            ctx.screen.draw.filled_rect(rect, self.color_hover if is_hover else self.color_btn)
            label = {
                "resume": "Resume",
                "restart": "Restart",
                "menu": "Back to main menu",
                "exit": "Exit Game",
            }[name]
            ctx.screen.draw.text(label, center=rect.center, fontsize=32, color=self.color_text)

    def on_mouse_down(self, pos, button, ctx):
        if button != 1:
            return
        if (
            hasattr(self, "mute_button_rect")
            and self.mute_button_rect
            and self.mute_button_rect.collidepoint(pos)
        ):
            play_scene = self._manager._scenes.get("play")
            if play_scene:
                play_scene.music_muted = not play_scene.music_muted
                from pgzero import music

                if play_scene.music_muted:
                    music.set_volume(0.0)
                else:
                    music.set_volume(
                        play_scene.BASE_VOLUME if hasattr(play_scene, "BASE_VOLUME") else 0.09
                    )
            return
        x, y = pos
        if not hasattr(self, "buttons"):
            return
        if self.buttons["resume"].collidepoint(x, y):
            self._manager.change("play", resume=True)
            return
        if self.buttons["restart"].collidepoint(x, y):

            play_scene = self._manager._scenes.get("play")
            was_muted = play_scene.music_muted if play_scene else False

            from pgzero import music

            music.stop()

            self._manager.change("play", muted=was_muted)
            return
        if self.buttons["menu"].collidepoint(x, y):
            from pgzero import music

            music.stop()

            play_scene = self._manager._scenes.get("play")
            if play_scene:
                play_scene._loop_music = False

            self._manager.change("menu")
            return
        if self.buttons["exit"].collidepoint(x, y):
            sys.exit(0)

    def update(self, dt, ctx):
        ctx.mouse_pos = getattr(ctx, "mouse_pos", (0, 0))
