import sys
import pyaudio
import wave
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import os
from datetime import datetime

# ── Theme ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ── Palette ────────────────────────────────────────────────────────────────────
BG          = "#0f0f12"
SURFACE     = "#1a1a20"
SURFACE2    = "#22222b"
ACCENT      = "#4a9eff"
REC_RED     = "#e05555"
REC_HOVER   = "#c94444"
GREEN       = "#3ecf8e"
TEXT_PRI    = "#eaeaf2"
TEXT_SEC    = "#5a5a72"
TEXT_DIM    = "#35354a"
# ───────────────────────────────────────────────────────────────────────────────


class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self._pulse_job = None
        self._btn_color = REC_RED
        self._btn_label = "REC"
        self._btn_photo = None   # holds ImageTk ref to prevent GC
        self._dot_photo = None   # holds dot ImageTk ref to prevent GC
        self._pulse_visible = True
        self._timer_seconds = 0
        self._timer_job = None

        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100

        # Save folder
        self.save_folder = os.path.join(
            os.path.expanduser("~"), "Desktop", "SoundTap Recordings"
        )
        os.makedirs(self.save_folder, exist_ok=True)

        self.setup_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def setup_ui(self):
        self.root = ctk.CTk()
        self.root.title("SoundTap")
        self.root.geometry("340x400")
        self.root.resizable(False, False)
        self.root.configure(fg_color=BG)

        # ── Header bar (dot indicator only) ───────────────────────────────
        header = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=0, height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        self.dot_canvas = ctk.CTkCanvas(
            header, width=14, height=14,
            bg=SURFACE, highlightthickness=0
        )
        self.dot_canvas.place(relx=1.0, rely=0.5, anchor="e", x=-14)
        self._draw_dot(TEXT_DIM)

        # ── Center area ────────────────────────────────────────────────────
        center_frame = ctk.CTkFrame(self.root, fg_color=BG)
        center_frame.pack(fill="x", padx=30, pady=(20, 0))

        # True circle button drawn on a Canvas — CTkButton cannot produce a
        # perfect circle due to its internal label padding.
        BTN_SIZE = 120
        self.btn_canvas = ctk.CTkCanvas(
            center_frame, width=BTN_SIZE, height=BTN_SIZE,
            bg=BG, highlightthickness=0
        )
        self.btn_canvas.pack(pady=(10, 0))
        self._draw_rec_btn(REC_RED, "REC")
        self.btn_canvas.bind("<Button-1>", lambda e: self.toggle_recording())
        self.btn_canvas.bind("<Enter>",    lambda e: self._draw_rec_btn(REC_HOVER, self._btn_label))
        self.btn_canvas.bind("<Leave>",    lambda e: self._draw_rec_btn(self._btn_color, self._btn_label))

        # Status text
        self.status_label = ctk.CTkLabel(
            center_frame,
            text="Ready",
            font=ctk.CTkFont(family="Helvetica Neue", size=12),
            text_color=TEXT_SEC
        )
        self.status_label.pack(pady=(20, 0))

        # Timer display
        self.timer_label = ctk.CTkLabel(
            center_frame,
            text="00:00",
            font=ctk.CTkFont(family="Helvetica Neue", size=32, weight="bold"),
            text_color=TEXT_DIM
        )
        self.timer_label.pack(pady=(4, 0))

        # ── Bottom card ────────────────────────────────────────────────────
        bottom = ctk.CTkFrame(self.root, fg_color=SURFACE, corner_radius=14)
        bottom.pack(fill="x", padx=20, pady=20)

        path_row = ctk.CTkFrame(bottom, fg_color="transparent")
        path_row.pack(fill="x", padx=14, pady=(6, 2))

        ctk.CTkLabel(
            path_row,
            text="Save to",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SEC,
            anchor="w"
        ).pack(side="left")

        self.folder_btn = ctk.CTkButton(
            path_row,
            text="Change",
            font=ctk.CTkFont(size=11),
            width=60, height=24,
            corner_radius=6,
            fg_color=SURFACE2,
            hover_color="#2c2c38",
            text_color=TEXT_SEC,
            command=self.change_folder
        )
        self.folder_btn.pack(side="right")

        self.path_label = ctk.CTkLabel(
            bottom,
            text=self._short_path(self.save_folder),
            font=ctk.CTkFont(size=13),
            text_color=TEXT_SEC,
            anchor="w",
            wraplength=280
        )
        self.path_label.pack(fill="x", padx=14, pady=(4, 14))

    # ── Circle button helper ─────────────────────────────────────────────────
    def _draw_rec_btn(self, color, label):
        self._btn_color = color
        self._btn_label = label
        s = 120
        scale = 4                          # supersample factor for smooth edges
        big = s * scale

        # Draw at 4x size on transparent background, then downscale
        img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Parse hex color to RGB
        c = color.lstrip("#")
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

        draw.ellipse((4, 4, big - 4, big - 4), fill=rgb + (255,))

        # Downscale with LANCZOS for smooth anti-aliased edge
        img = img.resize((s, s), Image.LANCZOS)

        # Composite onto the background color so transparency blends cleanly
        bg_c = BG.lstrip("#")
        bg_rgb = tuple(int(bg_c[i:i+2], 16) for i in (0, 2, 4))
        bg_img = Image.new("RGBA", (s, s), bg_rgb + (255,))
        bg_img.alpha_composite(img)
        final = bg_img.convert("RGB")

        self._btn_photo = ImageTk.PhotoImage(final)
        self.btn_canvas.delete("all")
        self.btn_canvas.create_image(0, 0, anchor="nw", image=self._btn_photo)
        self.btn_canvas.create_text(
            s // 2, s // 2, text=label,
            fill=TEXT_PRI,
            font=("Helvetica Neue", 20, "bold")
        )

    # ── Dot / ring helpers ────────────────────────────────────────────────────
    def _draw_dot(self, color):
        s = 14
        scale = 4
        big = s * scale

        img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        c = color.lstrip("#")
        rgb = tuple(int(c[i:i+2], 16) for i in (0, 2, 4))
        draw.ellipse((2, 2, big - 2, big - 2), fill=rgb + (255,))

        img = img.resize((s, s), Image.LANCZOS)

        bg_c = SURFACE.lstrip("#")
        bg_rgb = tuple(int(bg_c[i:i+2], 16) for i in (0, 2, 4))
        bg_img = Image.new("RGBA", (s, s), bg_rgb + (255,))
        bg_img.alpha_composite(img)

        self._dot_photo = ImageTk.PhotoImage(bg_img.convert("RGB"))
        self.dot_canvas.delete("all")
        self.dot_canvas.create_image(0, 0, anchor="nw", image=self._dot_photo)

    # ── Pulse animation ───────────────────────────────────────────────────────
    def _pulse(self):
        """Flash dot on, then schedule it off after 500ms — called once per tick."""
        self._draw_dot(REC_RED)
        self._pulse_job = self.root.after(500, self._pulse_off)

    def _pulse_off(self):
        if self.recording:
            self._draw_dot(BG)
        self._pulse_job = None

    def _stop_pulse(self):
        if self._pulse_job:
            self.root.after_cancel(self._pulse_job)
            self._pulse_job = None
        self._draw_dot(TEXT_DIM)

    # ── Timer ─────────────────────────────────────────────────────────────────
    def _tick(self):
        if not self.recording:
            return
        self._timer_seconds += 1
        m, s = divmod(self._timer_seconds, 60)
        self.timer_label.configure(text=f"{m:02d}:{s:02d}", text_color=REC_RED)
        self._pulse()
        self._timer_job = self.root.after(1000, self._tick)

    def _stop_timer(self):
        if self._timer_job:
            self.root.after_cancel(self._timer_job)
            self._timer_job = None

    def _reset_timer(self):
        self._timer_seconds = 0
        self.timer_label.configure(text="00:00", text_color=TEXT_DIM)

    # ── Recording logic ───────────────────────────────────────────────────────
    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        try:
            device_index = self.find_stereo_mix()
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk
            )
            self.recording = True
            self.frames = []

            self._draw_rec_btn(SURFACE2, "STOP")
            self.status_label.configure(text="Recording…", text_color=REC_RED)
            self._reset_timer()
            self._pulse()
            self._tick()

            self.record_thread = threading.Thread(target=self.record_audio, daemon=True)
            self.record_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Could not start recording:\n{str(e)}\n\n"
                                 "Make sure 'Stereo Mix' is enabled in Sound settings.")

    def find_stereo_mix(self):
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if "stereo mix" in info['name'].lower() or "what u hear" in info['name'].lower():
                return i
        return self.audio.get_default_input_device_info()['index']

    def record_audio(self):
        while self.recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False

        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self._stop_pulse()
        self._stop_timer()
        self.save_recording()

        self._draw_rec_btn(REC_RED, "REC")
        self.status_label.configure(text="Saved ✓", text_color=GREEN)
        self._draw_dot(GREEN)

        self.root.after(3000, self._reset_to_idle)

    def _reset_to_idle(self):
        self.status_label.configure(text="Ready", text_color=TEXT_SEC)
        self._reset_timer()
        self._draw_dot(TEXT_DIM)

    def save_recording(self):
        if not self.frames:
            messagebox.showwarning("Warning", "No audio data to save.")
            return
        timestamp = datetime.now().strftime("ST_%Y_%m_%d_%H_%M_%S")
        filename = f"{timestamp}.wav"
        filepath = os.path.join(self.save_folder, filename)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        print(f"Saved: {filepath}")

    # ── Folder picker ─────────────────────────────────────────────────────────
    def change_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_folder)
        if folder:
            self.save_folder = folder
            self.path_label.configure(text=self._short_path(folder))

    def _short_path(self, path):
        home = os.path.expanduser("~")
        return ("~" + path[len(home):]) if path.startswith(home) else path

    # ── Run ───────────────────────────────────────────────────────────────────
    def _set_icon(self):
        if hasattr(sys, "_MEIPASS"):
            # Running as a PyInstaller .exe
            icon_path = os.path.join(sys._MEIPASS, "soundtap.ico")
        else:
            # Running as a plain .py script
            icon_path = os.path.join(os.path.dirname(__file__), "soundtap.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(0, self._set_icon)
        self.root.mainloop()

    def on_closing(self):
        if self.recording:
            self.stop_recording()
        self.audio.terminate()
        self.root.destroy()


if __name__ == "__main__":
    # pip install customtkinter pyaudio
    recorder = AudioRecorder()
    recorder.run()
