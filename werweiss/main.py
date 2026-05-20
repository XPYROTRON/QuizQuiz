import gi
import random
import re
from pathlib import Path

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, Gdk

from werweiss.game.database import init_db, get_categories, get_questions, save_score, top_scores
from werweiss.game.sound import play, set_muted

APP_ID = "io.github.XPYROTRON.QuizQuiz"
ASSET_DIR = Path(__file__).resolve().parent / "assets"
DEFAULT_ROUND_LIMIT = 10
VERSION = "2.1.0"
QUESTION_SECONDS = 25


class QuizApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_activate(self):
        init_db()
        Gtk.Window.set_default_icon_name(APP_ID)
        win = QuizWindow(self)
        win.present()


class QuizWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Quiz? Quiz")
        self.set_default_size(1240, 720)
        self.set_resizable(True)
        self.player_name = "Spieler"
        self.sound_muted = False
        self.quiz_length = DEFAULT_ROUND_LIMIT
        self.score = 0
        self.index = 0
        self.questions = []
        self.current_answers = []
        self.seconds_left = QUESTION_SECONDS
        self.timer_id = None
        self.answer_buttons = []
        self.used_fifty = False
        self.used_vote = False
        self.used_switch = False
        self.load_css()
        self.show_start()

    def load_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_path(str(Path(__file__).resolve().parent / "style.css"))
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def clear_timer(self):
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

    def set_screen(self, widget):
        self.clear_timer()
        self.set_child(widget)

    def stage(self, content, dark=False):
        overlay = Gtk.Overlay()
        overlay.set_hexpand(True)
        overlay.set_vexpand(True)

        # Use the user-provided FHD neon studio background directly.
        # CONTAIN keeps the full image visible when the window is maximized
        # or resized instead of cropping important parts of the stage.
        bg = Gtk.Picture.new_for_filename(str(ASSET_DIR / "backgrounds" / "quizquiz_neon_studio.png"))
        bg.set_content_fit(Gtk.ContentFit.CONTAIN)
        bg.set_hexpand(True)
        bg.set_vexpand(True)
        overlay.set_child(bg)

        shade = Gtk.Box()
        shade.add_css_class("screen-shade" if not dark else "screen-shade-dark")
        overlay.add_overlay(shade)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(content)
        scroll.set_hexpand(True)
        scroll.set_vexpand(True)
        overlay.add_overlay(scroll)
        return overlay

    def root_box(self, spacing=14, tight=False):
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
        root.add_css_class("screen-pad-tight" if tight else "screen-pad")
        root.set_hexpand(True)
        root.set_vexpand(True)
        return root

    def settings_button(self):
        btn = Gtk.Button(label="⚙  Einstellungen")
        btn.add_css_class("top-pill")
        btn.connect("clicked", lambda _btn: self.show_settings())
        return btn

    def sound_toggle(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.add_css_class("top-pill")
        label = Gtk.Label(label="🔊  Sounds stummschalten")
        box.append(label)
        check = Gtk.CheckButton()
        check.set_active(self.sound_muted)
        check.connect("toggled", self.on_mute_toggled)
        box.append(check)
        return box

    def back_button(self):
        btn = Gtk.Button(label="←")
        btn.add_css_class("back-square")
        btn.connect("clicked", lambda _btn: self.show_start())
        return btn

    def top_bar(self, mode="menu"):
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        top.set_hexpand(True)
        if mode == "menu":
            top.append(self.settings_button())
        else:
            top.append(self.back_button())
        spacer = Gtk.Box(); spacer.set_hexpand(True); top.append(spacer)
        return top

    def on_mute_toggled(self, button):
        self.sound_muted = button.get_active()
        set_muted(self.sound_muted)
        if not self.sound_muted:
            play("click")

    def show_logo(self):
        wrap = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        wrap.add_css_class("qq-logo-sign")
        line1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        line1.set_halign(Gtk.Align.CENTER)
        q1 = Gtk.Label(label="QUIZ?")
        q1.add_css_class("qq-logo-orange")
        line2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        line2.set_halign(Gtk.Align.CENTER)
        q2 = Gtk.Label(label="QUIZ")
        q2.add_css_class("qq-logo-blue")
        line1.append(q1)
        line2.append(q2)
        wrap.append(line1)
        wrap.append(line2)
        return wrap

    def menu_tile(self, icon, text, callback, css="tile-purple"):
        btn = Gtk.Button()
        btn.add_css_class("menu-tile")
        btn.add_css_class(css)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        i = Gtk.Label(label=icon); i.add_css_class("menu-tile-icon")
        t = Gtk.Label(label=text); t.add_css_class("menu-tile-text")
        box.append(i); box.append(t)
        btn.set_child(box)
        btn.connect("clicked", callback)
        return btn

    def show_start(self):
        root = self.root_box(8, tight=True)
        root.append(self.top_bar("menu"))
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        center.set_halign(Gtk.Align.CENTER)
        center.set_valign(Gtk.Align.CENTER)
        center.set_hexpand(True)
        center.set_vexpand(True)
        center.append(self.show_logo())

        start = Gtk.Button(label="▶   SPIEL STARTEN")
        start.add_css_class("mega-start")
        start.connect("clicked", lambda _btn: self.show_category_select(self.player_name))
        center.append(start)


        tiles = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=26)
        tiles.set_halign(Gtk.Align.CENTER)
        tiles.append(self.menu_tile("🧠", "KATEGORIEN", lambda _b: self.show_category_select(self.player_name), "tile-green"))
        tiles.append(self.menu_tile("☆", "STATISTIKEN", lambda _b: self.show_highscores(), "tile-purple"))
        tiles.append(self.menu_tile("?", "SO GEHT’S", lambda _b: self.show_message("SO GEHT’S", "Wähle eine Kategorie, beantworte Fragen und nutze Joker nur einmal pro Runde."), "tile-blue"))
        tiles.append(self.menu_tile("ⓘ", "ÜBER", lambda _b: self.show_message("ÜBER", "Quiz? Quiz · Linux Quizspiel · Version 2.1.0"), "tile-orange"))
        center.append(tiles)
        version = Gtk.Label(label="Version 2.1.0")
        version.add_css_class("version")
        center.append(version)
        root.append(center)
        self.set_screen(self.stage(root))

    def category_icon(self, category):
        return {
            "Alle Kategorien": "🎓", "Allgemeinwissen": "🎓", "Deutsche Sprache": "📝",
            "Unter Wasser": "🌊", "Total Genial": "🧠", "Neuheit": "✨",
            "Typisch deutsch": "🇩🇪", "Mann & Frau": "🚻", "Clever!": "💡",
            "Tierisch tierisch": "🐾", "?": "❓", "Einspruch": "⚖️",
            "Beim Zahnarzt": "🦷", "Fremdwörter": "🔤", "Wie ticken wir?": "🧭",
            "Genies": "🧬", "Auto": "🚗", "Technik": "⚙️",
            "Essen & Trinken": "🍽️", "Im Grünen": "🌿", "Karibik": "🏝️",
            "Vögel": "🦜", "Im Labor": "🧪", "Königshäuser": "👑",
            "Naturwunder": "🏔️", "HundKatzeMaus": "🐶", "Brisant": "📰",
            "Kochen": "🍳", "Erfinder": "🛠️", "Rekorde": "🏆",
            "Staatsgeheimnis": "🕵️", "Familie": "👨‍👩‍👧", "Royals": "💎",
            "Wunder der Natur": "🌈", "Afrika": "🦁", "Feiertage": "🎉",
            "In aller Kürze": "⚡", "Damals": "⏳", "Fußball": "⚽",
            "Mode": "👗", "Büro": "💼", "Linux": "🐧",
            "Geografie": "🌐", "Wissenschaft": "⚛️", "Geschichte": "🏛️",
            "Sport": "🏅", "Kultur": "🎭", "Filme & Serien": "🎬",
            "Gaming": "🎮", "Musik": "🎵", "Tiere": "🐾",
        }.get(category, "❓")

    def display_category_name(self, category):
        return "Allgemeinwissen" if category == "Alle Kategorien" else category

    def show_category_select(self, player):
        self.player_name = player.strip() if player and player.strip() else "Spieler"
        play("click")
        root = self.root_box(16)
        root.append(self.top_bar("back"))
        title = Gtk.Label(label="WÄHLE EINE KATEGORIE")
        title.add_css_class("page-title")
        root.append(title)

        wrap = Gtk.FlowBox()
        wrap.set_halign(Gtk.Align.CENTER)
        wrap.set_valign(Gtk.Align.CENTER)
        wrap.set_max_children_per_line(5)
        wrap.set_min_children_per_line(2)
        wrap.set_selection_mode(Gtk.SelectionMode.NONE)
        wrap.set_column_spacing(22)
        wrap.set_row_spacing(22)
        categories = ["Alle Kategorien"] + get_categories()
        for idx, cat in enumerate(categories):
            btn = Gtk.Button()
            btn.add_css_class("category-card")
            btn.add_css_class(f"cat-{idx % 8}")
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            card.set_halign(Gtk.Align.CENTER); card.set_valign(Gtk.Align.CENTER)
            emoji = Gtk.Label(label=self.category_icon(cat)); emoji.add_css_class("category-emoji")
            name = Gtk.Label(label=self.display_category_name(cat), wrap=True, justify=Gtk.Justification.CENTER); name.add_css_class("category-name")
            card.append(emoji); card.append(name)
            btn.set_child(card)
            btn.connect("clicked", lambda _btn, c=cat: self.start_game(self.player_name, c))
            wrap.append(btn)
        root.append(wrap)
        self.set_screen(self.stage(root, dark=True))

    def start_game(self, player, category):
        play("start")
        self.player_name = player.strip() or "Spieler"
        self.score = 0
        self.index = 0
        self.used_fifty = False
        self.used_vote = False
        self.used_switch = False
        self.questions = get_questions(category, self.quiz_length)
        random.shuffle(self.questions)
        if not self.questions:
            self.show_message("Keine Fragen gefunden", "Bitte füge Fragen zur Datenbank hinzu.")
            return
        self.show_question()

    def clean_question_text(self, text):
        return re.sub(r"^\s*#\s*\d+[\s:.)\-–—]+", "", text or "").strip()

    def show_question(self):
        if self.index >= len(self.questions):
            save_score(self.player_name, self.score)
            play("finish")
            self.show_end()
            return
        self.seconds_left = QUESTION_SECONDS
        q = self.questions[self.index]
        self.current_answers = list(q["answers"])
        random.shuffle(self.current_answers)

        root = self.root_box(12, tight=True)
        top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        top.set_hexpand(True)
        top.append(self.back_button())
        info = Gtk.Label(label=f"{self.display_category_name(q['category'])}\nFrage {self.index + 1} / {len(self.questions)}")
        info.add_css_class("info-card")
        top.append(info)
        spacer = Gtk.Box(); spacer.set_hexpand(True); top.append(spacer)
        self.timer_label = Gtk.Label(label=str(self.seconds_left))
        self.timer_label.add_css_class("timer-orb")
        top.append(self.timer_label)
        spacer2 = Gtk.Box(); spacer2.set_hexpand(True); top.append(spacer2)
        self.score_label = Gtk.Label(label=f"Punkte\n{self.score:,}".replace(",", "."))
        self.score_label.add_css_class("score-card")
        top.append(self.score_label)
        root.append(top)

        qcard = Gtk.Label(label=self.clean_question_text(q["question"]), wrap=True, justify=Gtk.Justification.CENTER)
        qcard.add_css_class("question-panel")
        qcard.set_halign(Gtk.Align.CENTER)
        qcard.set_max_width_chars(58)
        root.append(qcard)

        grid = Gtk.Grid(column_spacing=18, row_spacing=14)
        grid.set_halign(Gtk.Align.CENTER)
        letters = ["A", "B", "C", "D"]
        self.answer_buttons = []
        for i, answer in enumerate(self.current_answers):
            btn = Gtk.Button()
            btn.add_css_class("answer-card")
            btn.add_css_class(f"answer-{i}")
            inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
            inner.set_valign(Gtk.Align.CENTER)
            badge = Gtk.Label(label=letters[i]); badge.add_css_class("answer-letter")
            txt = Gtk.Label(label=answer["text"], wrap=True, xalign=0); txt.add_css_class("answer-text")
            inner.append(badge); inner.append(txt)
            btn.set_child(inner)
            btn.connect("clicked", self.answer_clicked, answer)
            self.answer_buttons.append(btn)
            grid.attach(btn, i % 2, i // 2, 1, 1)
        root.append(grid)

        jokers = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=28)
        jokers.set_halign(Gtk.Align.CENTER)
        fifty = Gtk.Button(label="50:50"); fifty.add_css_class("joker"); fifty.set_sensitive(not self.used_fifty); fifty.connect("clicked", self.use_fifty_fifty); jokers.append(fifty)
        vote = Gtk.Button(label="👥"); vote.add_css_class("joker"); vote.set_sensitive(not self.used_vote); vote.connect("clicked", self.use_audience_vote); jokers.append(vote)
        switch = Gtk.Button(label="⟳"); switch.add_css_class("joker"); switch.set_sensitive(not self.used_switch and self.index < len(self.questions)-1); switch.connect("clicked", self.use_switch_question); jokers.append(switch)
        root.append(jokers)
        self.set_screen(self.stage(root))
        self.timer_id = GLib.timeout_add_seconds(1, self.tick)

    def show_settings(self):
        play("click")
        root = self.root_box(18)
        root.append(self.top_bar("back"))
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        panel.add_css_class("glass-panel")
        panel.set_halign(Gtk.Align.CENTER); panel.set_valign(Gtk.Align.CENTER); panel.set_vexpand(True)
        title = Gtk.Label(label="EINSTELLUNGEN"); title.add_css_class("page-title"); panel.append(title)
        mute = Gtk.CheckButton(label="🔇  Sounds stummschalten")
        mute.set_active(self.sound_muted); mute.add_css_class("settings-check"); mute.connect("toggled", self.on_mute_toggled); panel.append(mute)
        length_label = Gtk.Label(label="Fragen pro Quiz"); length_label.add_css_class("settings-label"); panel.append(length_label)
        combo = Gtk.ComboBoxText(); combo.add_css_class("settings-combo")
        for value in (10,25,50,100): combo.append_text(str(value))
        combo.set_active({10:0,25:1,50:2,100:3}.get(self.quiz_length,0)); combo.connect("changed", self.on_quiz_length_changed); panel.append(combo)
        back = Gtk.Button(label="←  ZURÜCK"); back.add_css_class("compact-back"); back.set_halign(Gtk.Align.CENTER); back.connect("clicked", lambda _b: self.show_start()); panel.append(back)
        root.append(panel)
        self.set_screen(self.stage(root, dark=True))

    def on_quiz_length_changed(self, combo):
        try: self.quiz_length = int(combo.get_active_text())
        except Exception: self.quiz_length = DEFAULT_ROUND_LIMIT
        play("click")

    def use_fifty_fifty(self, button):
        if self.used_fifty: return
        self.used_fifty = True; play("click")
        wrong = [(btn, ans) for btn, ans in zip(self.answer_buttons, self.current_answers) if not ans["correct"] and btn.get_sensitive()]
        random.shuffle(wrong)
        for btn, _ in wrong[:2]:
            btn.set_sensitive(False); btn.add_css_class("joker-disabled-answer")
            btn.set_child(Gtk.Label(label="—"))
        button.set_sensitive(False)

    def set_answer_label_with_vote(self, btn, letter, text, pct):
        inner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        badge = Gtk.Label(label=letter); badge.add_css_class("answer-letter")
        label = Gtk.Label(label=f"{text}     👥 {pct}%", wrap=True, xalign=0); label.add_css_class("answer-text")
        inner.append(badge); inner.append(label); btn.set_child(inner)

    def use_audience_vote(self, button):
        if self.used_vote: return
        self.used_vote = True; play("click")
        correct_index = next((i for i, ans in enumerate(self.current_answers) if ans["correct"]), 0)
        correct_vote = random.randint(55, 78)
        remaining = 100 - correct_vote
        shares = [random.randint(4, max(5, remaining//2)), random.randint(3, max(4, remaining//3)), 0]
        shares[2] = max(0, remaining - shares[0] - shares[1]); random.shuffle(shares)
        wrong_iter = iter(shares); letters = ["A","B","C","D"]
        for i, (btn, ans) in enumerate(zip(self.answer_buttons, self.current_answers)):
            pct = correct_vote if i == correct_index else next(wrong_iter)
            self.set_answer_label_with_vote(btn, letters[i], ans["text"], pct)
        button.set_sensitive(False)

    def use_switch_question(self, button):
        if self.used_switch or self.index >= len(self.questions)-1: return
        self.used_switch = True; play("click")
        current = self.questions.pop(self.index); self.questions.append(current)
        self.show_question()

    def tick(self):
        self.seconds_left -= 1
        self.timer_label.set_text(str(self.seconds_left))
        if self.seconds_left in (5,4,3,2,1): play("tick")
        if self.seconds_left <= 0:
            self.lock_answers(None); return False
        return True

    def answer_clicked(self, button, answer):
        self.lock_answers(button, answer)

    def lock_answers(self, clicked, answer=None):
        self.clear_timer()
        correct = bool(answer and answer["correct"])
        if correct:
            self.score += 100 + max(self.seconds_left,0)*5; play("right")
        else:
            play("wrong")
        for btn, ans in zip(self.answer_buttons, self.current_answers):
            btn.set_sensitive(False)
            if ans["correct"]: btn.add_css_class("correct")
            elif clicked is btn: btn.add_css_class("wrong")
        GLib.timeout_add_seconds(2, self.next_question)

    def next_question(self):
        self.index += 1
        self.show_question()
        return False

    def show_end(self):
        root = self.root_box(18)
        root.append(self.top_bar("back"))
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        panel.add_css_class("glass-panel"); panel.set_halign(Gtk.Align.CENTER); panel.set_valign(Gtk.Align.CENTER); panel.set_vexpand(True)
        title = Gtk.Label(label="SPIEL BEENDET!"); title.add_css_class("page-title")
        score = Gtk.Label(label=f"{self.player_name}: {self.score:,} Punkte".replace(",", ".")); score.add_css_class("big-score")
        again = Gtk.Button(label="▶  NOCHMAL SPIELEN"); again.add_css_class("compact-back"); again.connect("clicked", lambda _b: self.show_start())
        panel.append(title); panel.append(score); panel.append(again); root.append(panel)
        self.set_screen(self.stage(root, dark=True))

    def show_highscores(self):
        root = self.root_box(16)
        root.append(self.top_bar("back"))
        title = Gtk.Label(label="HIGHSCORES"); title.add_css_class("page-title"); root.append(title)
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        panel.add_css_class("score-table"); panel.set_halign(Gtk.Align.CENTER)
        rows = top_scores()
        if not rows:
            empty = Gtk.Label(label="Noch keine Highscores vorhanden."); empty.add_css_class("subtitle"); panel.append(empty)
        else:
            for i,(player,points,played_at) in enumerate(rows,1):
                lbl = Gtk.Label(label=f"{i:>2}.  {player:<18}  {points:>6} Punkte   {played_at}"); lbl.add_css_class("score-row"); panel.append(lbl)
        root.append(panel)
        back = Gtk.Button(label="←  ZURÜCK"); back.add_css_class("compact-back"); back.set_halign(Gtk.Align.CENTER); back.connect("clicked", lambda _b: self.show_start()); root.append(back)
        self.set_screen(self.stage(root, dark=True))

    def show_message(self, title_text, body):
        root = self.root_box(18)
        root.append(self.top_bar("back"))
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        panel.add_css_class("glass-panel"); panel.set_halign(Gtk.Align.CENTER); panel.set_valign(Gtk.Align.CENTER); panel.set_vexpand(True)
        title = Gtk.Label(label=title_text); title.add_css_class("page-title")
        msg = Gtk.Label(label=body, wrap=True, justify=Gtk.Justification.CENTER); msg.add_css_class("subtitle")
        panel.append(title); panel.append(msg); root.append(panel)
        self.set_screen(self.stage(root, dark=True))


def main():
    app = QuizApp()
    return app.run(None)


if __name__ == "__main__":
    main()
