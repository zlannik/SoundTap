import pyaudio
import wave
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime

class AudioRecorder:
    def __init__(self):
        self.recording = False
        self.frames = []
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 2
        self.rate = 44100
        
        # Default save folder
        self.save_folder = os.path.join(os.path.expanduser("~"), "Desktop", "SoundTap Recordings")
        os.makedirs(self.save_folder, exist_ok=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("SoundTap")
        self.root.geometry("300x125")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=10, pady=10, bg="#1e1e1e")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Recording status
        self.status_label = tk.Label(main_frame, text="READY", 
                                    font=("Segoe UI", 12),
                                    bg="#1e1e1e", fg="#87CEEB")
        self.status_label.pack(pady=(0, 15))
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#1e1e1e")
        button_frame.pack(pady=(0, 20))
        
        self.start_btn = tk.Button(button_frame, text="START", 
                                  command=self.start_recording,
                                  bg="#4CAF50", fg="white", 
                                  font=("Segoe UI", 12, "bold"),
                                  width=12, height=2,
                                  relief="flat", bd=0,
                                  activebackground="#45a049",
                                  highlightthickness=0,
                                  borderwidth=2)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = tk.Button(button_frame, text="STOP", 
                                 command=self.stop_recording,
                                 bg="#f44336", fg="white", 
                                 font=("Segoe UI", 12, "bold"),
                                 width=12, height=2, state=tk.DISABLED,
                                 relief="flat", bd=0,
                                 activebackground="#d32f2f",
                                 activeforeground="white",
                                 disabledforeground="white",
                                 highlightthickness=0,
                                 borderwidth=2)
        self.stop_btn.pack(side=tk.LEFT)
    
    def start_recording(self):
        if self.recording:
            return
            
        try:
            # Find stereo mix or default input device
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
            
            # Update UI
            self.status_label.config(text="RECORDING...", fg="#ff4444")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start recording thread
            self.record_thread = threading.Thread(target=self.record_audio)
            self.record_thread.start()
            
        except Exception as e:
            messagebox.showerror("ERROR", f"COULD NOT START RECORDING: {str(e)}\n\n"
                               "MAKE SURE 'STEREO MIX' IS ENABLED IN YOUR SOUND SETTINGS.")
    
    def find_stereo_mix(self):
        """Find Stereo Mix device or return default input"""
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if "stereo mix" in info['name'].lower() or "what u hear" in info['name'].lower():
                return i
        
        # If no stereo mix found, try default input
        default_input = self.audio.get_default_input_device_info()
        return default_input['index']
    
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
        
        # Wait for recording thread to finish
        if hasattr(self, 'record_thread'):
            self.record_thread.join()
        
        # Stop and close stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Save the recording
        self.save_recording()
        
        # Update UI
        self.status_label.config(text="RECORDING SAVED!", fg="#4CAF50")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # Reset status after 3 seconds
        self.root.after(3000, lambda: self.status_label.config(text="READY", fg="#87CEEB"))
    
    def save_recording(self):
        if not self.frames:
            messagebox.showwarning("WARNING", "NO AUDIO DATA TO SAVE.")
            return
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}.wav"
        filepath = os.path.join(self.save_folder, filename)
        
        # Save as WAV file
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
        
        print(f"Recording saved: {filepath}")
    
    def change_folder(self):
        folder = filedialog.askdirectory(initialdir=self.save_folder)
        if folder:
            self.save_folder = folder
            self.folder_label.config(text=folder)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        if self.recording:
            self.stop_recording()
        self.audio.terminate()
        self.root.destroy()

if __name__ == "__main__":
    # Install required packages first:
    # pip install pyaudio
    
    recorder = AudioRecorder()
    recorder.run()