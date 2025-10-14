## 🖼️ Screenshots

<img width="379" height="250" alt="Screenshot1" src="https://github.com/user-attachments/assets/bf9c8cf9-b241-48cd-ab1f-b15bc971ceb5" /><br>

<img width="379" height="251" alt="Screenshot2" src="https://github.com/user-attachments/assets/3914115b-68d1-4d80-b9af-3c92c2a50a2d" /><br>

<img width="380" height="249" alt="Screenshot3" src="https://github.com/user-attachments/assets/fff870aa-c5d0-4724-b6e7-a277ca407216" /><br>

<img width="375" height="289" alt="Screenshot 2025-10-14 124014" src="https://github.com/user-attachments/assets/74754068-6957-4bc8-87b8-12523b8f2aae" />



# What Is SoundTap
SoundTap records your desktop's internal audio by clicking "start" & "stop" buttons. It's clean, lightweight, and handy.

# How It Works
SoundTap saves what you capture as a WAV file to a folder that it creates on your desktop called "SoundTap Recordings".

Great for musicians who do a lot of sampling, podcasters, journalists, YouTubers, influencers, posters, or anyone who just wants to save some sound clips for later without hassle.

It's a single python scrpit that utilizes the pyaudio library, and tkinter for its GUI. It uses multi-threading & redunancy techniques to ensure stability.

It's also the first program I have created which I use regularly.

# Installation
Downloading and double clicking the SoundTap.py file runs the program in terminal mode.

However, for ease of use SoundTap is best used as an .exe application

Until I make a release version you have to do it manually:

1. Download SoundTap.py from this page to your downloads folder
2. open your computer's terminal
3. enter -> pip install pyinstaller
4. enter -> cd downloads
6. enter -> pyinstaller SoundTap.py --onefile --windowed
5. SoundTap.exe will be in the user\downloads\dist
6. Drag to desktop, delete uneeded SoundTap.py file & dist folder
