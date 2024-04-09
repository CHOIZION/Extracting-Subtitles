import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pydub import AudioSegment
import auditok
import speech_recognition as sr
import threading
import tempfile
import wave

class AudioTranscriber:
    def __init__(self, master):
        self.master = master
        master.title("Audio Transcriber Application")
        

        master.geometry('350x450')


        self.frame_audio_transcriber = tk.LabelFrame(master, text="Audio Transcriber", padx=5, pady=5)
        self.frame_audio_transcriber.place(x=5, y=5, width=340, height=180)
        

        self.transcribe_folder_button = tk.Button(self.frame_audio_transcriber, text="Transcribe Folder", command=self.transcribe_folder)
        self.transcribe_folder_button.pack(pady=10)

        self.selected_folder_label = tk.Label(self.frame_audio_transcriber, text="Selected Folder: None", anchor='w')
        self.selected_folder_label.pack(fill='x', pady=10)

        self.progress = ttk.Progressbar(self.frame_audio_transcriber, orient="horizontal", length=400, mode="determinate")
        self.progress.pack()

        self.transcribe_log_label = tk.Label(self.frame_audio_transcriber, text="Transcribe log label", bg="white", anchor='w')
        self.transcribe_log_label.pack(fill='x', pady=10)

        # File Name Converter 프레임 구성
        self.frame_file_name_converter = tk.LabelFrame(master, text="File Name Converter", padx=5, pady=5)
        self.frame_file_name_converter.place(x=5, y=190, width=340, height=120)

        # File Name Converter 위젯
        self.converter_buttons_frame = tk.Frame(self.frame_file_name_converter)
        self.converter_buttons_frame.pack(pady=10)

        self.file_name_sorting_button = tk.Button(self.converter_buttons_frame, text="Sort", command=self.save_file_names)
        self.file_name_sorting_button.pack(side=tk.LEFT, padx=10)

        self.file_name_transport_button = tk.Button(self.converter_buttons_frame, text="Transfer", command=self.translate_file_names)
        self.file_name_transport_button.pack(side=tk.LEFT, padx=10)

        self.file_name_converter_log_label = tk.Label(self.frame_file_name_converter, text="FileName Converter log label", bg="white", anchor='w')
        self.file_name_converter_log_label.pack(fill='both', pady=10)

        # File Extension Converter 프레임 구성
        self.frame_file_extension_converter = tk.LabelFrame(master, text="File Extension Converter", padx=5, pady=5)
        self.frame_file_extension_converter.place(x=5, y=315, width=340, height=120)

        # File Extension Converter 위젯
        self.extension_buttons_frame = tk.Frame(self.frame_file_extension_converter)
        self.extension_buttons_frame.pack(pady=10)

        self.lrc_convert_button = tk.Button(self.extension_buttons_frame, text="*.txt -> *.lrc", command=self.convert_file_extensions)
        self.lrc_convert_button.pack(side=tk.LEFT, padx=10)

        self.wav_mp3_button = tk.Button(self.extension_buttons_frame, text="*.wav -> *.mp3", command=self.convert_wav_to_mp3)
        self.wav_mp3_button.pack(side=tk.LEFT, padx=10)

        self.file_extension_converter_log_label = tk.Label(self.frame_file_extension_converter, text="File Extension Converter log label", bg="white", anchor='w')
        self.file_extension_converter_log_label.pack(fill='both', pady=10)

    def convert_audio_to_wav(self, file_path):

        if file_path.lower().endswith(".mp3"):
            self.update_log("Converting MP3 to WAV...")
            sound = AudioSegment.from_mp3(file_path)
            wav_path = file_path.replace(".mp3", "_converted.wav")
            sound.export(wav_path, format="wav")
            return wav_path
        else:
            self.update_log("WAV File Selected...")
            sound = AudioSegment.from_wav(file_path)
            sound.export(file_path, format="wav")
            return file_path
    
    def Method_time(self, time_float):

        minutes = int(time_float // 60)
        seconds = int(time_float % 60)

        milliseconds = int((time_float - int(time_float)) * 100)
        return '{:02d}:{:02d}.{:02d}'.format(minutes, seconds, milliseconds)
    
    def process_audio(self, file_path):
        self.update_log("Converting audio file (if necessary)...", 10)

        wav_path = self.convert_audio_to_wav(file_path)
        self.update_log("Audio file conversion completed.", 20)


        self.update_log("Splitting audio file...", 30)
        audio_regions = auditok.split(
            wav_path,
            min_dur=0.2,  
            max_dur=4,    
            max_silence=1,  
            energy_threshold=10  
        )
        regions_count = sum(1 for _ in audio_regions)
        audio_regions = auditok.split(  
            wav_path,
            min_dur=0.2,
            max_dur=4,
            max_silence=1,
            energy_threshold=10
        )

        if regions_count == 0:
            self.update_log("오디오 세그먼트를 찾을 수 없습니다. 오디오 파일 또는 설정을 확인하세요.", 100)
            messagebox.showwarning("세그먼트가 없습니다.", "현재 설정에서 오디오 세그먼트를 찾을 수 없습니다.")
            return

        recognizer = sr.Recognizer()
        all_text = []

        
        for i, region in enumerate(audio_regions, start=1):
            progress = 30 + (70 * i // regions_count)  
            self.update_log(f"Transcribing segment {i}/{regions_count}...", progress)


            temp_audio_file_name = tempfile.mktemp(suffix=".wav")
            region.save(temp_audio_file_name)

            Sequence_time = self.Method_time(region.meta.start)

            Time_method = '['+Sequence_time+']'  

            with sr.AudioFile(temp_audio_file_name) as source:
                audio_data = recognizer.record(source)

            os.remove(temp_audio_file_name)  
            try:
                text = recognizer.recognize_google(audio_data, language='ja-JP')
                all_text.append(Time_method+' '+text)
            except sr.UnknownValueError:
                self.update_log(f"Segment {i}: Could not understand audio", progress)
            except sr.RequestError as e:
                self.update_log(f"Segment {i}: Could not request results; {e}", progress)

        full_text = '\n'.join(all_text)
        self.show_transcription(full_text, file_path)
        self.update_log("추출 완료! 출력 파일을 확인하세요.", 100)

        if file_path != wav_path:  
            os.remove(wav_path)
            self.update_log("임시 WAV 파일이 제거되었습니다.", 100)
    
    def transcribe_folder(self):

        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        self.update_log(folder_path, None, folder_path)

        supported_files = []
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.mp3', '.wav')):
                supported_files.append(os.path.join(folder_path, file))

        if not supported_files:
            messagebox.showinfo("No audio files", "선택된 폴더에 MP3 또는 WAV 파일이 존재하지 않습니다.")
            return


        for file_path in supported_files:
            self.update_log(f"Processing {os.path.basename(file_path)}...")
            threading.Thread(target=self.process_audio, args=(file_path,), daemon=True).start()

    def show_transcription(self, text, file_path):
        output_file_path = os.path.splitext(file_path)[0] + ".txt"
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(text)
        self.update_log("추출 완료!")
        messagebox.showinfo("Done", f"Transcribed text saved to {output_file_path}")

    def update_log(self, status, progress=None, filedir=None):
        if filedir is not None:
            self.selected_folder_label.config(text=filedir)
        else:
            self.transcribe_log_label.config(text=status)
            if progress is not None:
                self.progress["value"] = progress
        self.transcribe_log_label.update()
        self.selected_folder_label.update()
        self.progress.update()


    def save_file_names(self):
        folder_path = filedialog.askdirectory()
        name_text = []
        if not folder_path:
            return
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        for file_name in files:
            name_without_extension = '.'.join(file_name.split('.')[:-1])
            name_text.append(name_without_extension)
        full_text = '\n\n'.join(name_text)
        with open(os.path.join(folder_path, 'Sort.txt'), 'w', encoding='utf-8') as file:
            file.write(full_text)
        self.file_name_converter_log_label.config(text="Sort.txt saved!")
        self.file_name_converter_log_label.update()

    def translate_file_names(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        try:
            with open(os.path.join(folder_path, 'Sort_번역.txt'), 'r', encoding='utf-8') as file:
                lines = file.readlines()  # 파일의 모든 줄을 읽어옴


            for i in range(0, len(lines), 3):
                old_name_base = lines[i].strip()  # 원본 파일 기본 이름 (확장자 없음)
                new_name_base = lines[i+1].strip()  # 번역된 파일 기본 이름 (확장자 없음)


                full_old_name = next((f for f in os.listdir(folder_path) if f.startswith(old_name_base)), None)
                if full_old_name:

                    extension = '.' + full_old_name.split('.', 1)[1] if '.' in full_old_name else ''

                    old_path = os.path.join(folder_path, full_old_name)
                    new_path = os.path.join(folder_path, new_name_base + extension)  
                    if os.path.exists(old_path):
                        os.rename(old_path, new_path)
                        self.file_name_converter_log_label.config(text=f"{old_name_base} -> {new_name_base}{extension}")
                        self.file_name_converter_log_label.update()
                    else:
                        self.file_name_converter_log_label.config(text=f"No {old_name_base} file exists!")
                        self.file_name_converter_log_label.update()
                else:
                    self.file_name_converter_log_label.config(text=f"No file starting with {old_name_base} found!")
                    self.file_name_converter_log_label.update()
                self.file_name_converter_log_label.config(text="Task Finished!!")
                self.file_name_converter_log_label.update()
        except FileNotFoundError:
            messagebox.showerror("Error", "Sort_번역.txt 파일을 찾을 수 없습니다.")


### File Extension Converter
    def convert_file_extensions(self):
        file_count = 0
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return
        for file_name in os.listdir(folder_path):
            if file_name.endswith('_번역.txt') and file_name != 'Sort_번역.txt':
                original_name = file_name.replace('_번역.txt', '.txt')  
                new_name = file_name.replace('_번역.txt', '.lrc')  


                original_path = os.path.join(folder_path, original_name)
                if os.path.exists(original_path):
                    os.remove(original_path)
                    file_count += 1
                

                os.rename(os.path.join(folder_path, file_name), os.path.join(folder_path, new_name))
        self.file_extension_converter_log_label.config(text=f"{file_count} Files Converted to .lrc Extension")
        self.file_extension_converter_log_label.update()

    def convert_wav_to_mp3(self):
        self.file_extension_converter_log_label.config(text="Converting *.wav to *.mp3")
        self.file_extension_converter_log_label.update()
        folder_path = filedialog.askdirectory()
        if folder_path:
            for filename in os.listdir(folder_path):
                if filename.endswith(".wav"):
                    wav_path = os.path.join(folder_path, filename)
                    mp3_path = os.path.join(folder_path, filename[:-4] + ".mp3")
                    

                    audio = AudioSegment.from_wav(wav_path)
                    audio.export(mp3_path, format="mp3")
                    self.file_extension_converter_log_label.config(text=f"Converted {filename} to MP3")
                    self.file_extension_converter_log_label.update()
                    

                    os.remove(wav_path)
                    self.file_extension_converter_log_label.config(text=f"Deleted original WAV file: {filename}")
                    self.file_extension_converter_log_label.update()
            self.file_extension_converter_log_label.config(text="Task Finished!")
            self.file_extension_converter_log_label.update()
        else:
            self.file_extension_converter_log_label.config(text="폴더 선택이 취소되었습니다.")
            self.file_extension_converter_log_label.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioTranscriber(root)
    root.mainloop()
