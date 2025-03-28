import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import cn2an
from datetime import datetime
import openai
import threading
import shutil
import time

class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenAI Compatible API Translating Tools - Waltz1809")
        self.root.geometry("900x700")
        
        # Initialize variables
        self.parts = []
        self.translated_parts = []
        self.current_part_index = 0
        self.is_translating = False
        self.log_content = tk.StringVar()
        self.log_file_path = ""
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_input = ttk.Frame(self.notebook)
        self.tab_translate = ttk.Frame(self.notebook)
        self.tab_merge = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_input, text="Nhập & Tách")
        self.notebook.add(self.tab_translate, text="Dịch Thuật")
        self.notebook.add(self.tab_merge, text="Gộp & Xuất")
        
        # Text area for all tabs
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=100, height=20)
        self.text_area.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        # Setup tabs
        self.setup_input_tab()
        self.setup_translate_tab()
        self.setup_merge_tab()
    
    def setup_input_tab(self):
        # Input file section
        ttk.Label(self.tab_input, text="File đầu vào:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.input_file_var = tk.StringVar(value="input.txt")
        ttk.Entry(self.tab_input, textvariable=self.input_file_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.tab_input, text="Chọn file...", command=self.browse_input_file).grid(row=0, column=2, padx=5, pady=5)
        
        # Output split file section
        ttk.Label(self.tab_input, text="File đầu ra:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_split_var = tk.StringVar(value="output_split.txt")
        ttk.Entry(self.tab_input, textvariable=self.output_split_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        # Split parameters
        ttk.Label(self.tab_input, text="Số ký tự tối đa mỗi phần:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_chars_var = tk.IntVar(value=2000)
        ttk.Entry(self.tab_input, textvariable=self.max_chars_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self.tab_input, text="Số chương tối đa:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_chapter_var = tk.IntVar(value=1000)
        ttk.Entry(self.tab_input, textvariable=self.max_chapter_var, width=10).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        ttk.Button(self.tab_input, text="Tách văn bản", command=self.split_text).grid(row=4, column=0, columnspan=3, pady=10)
        ttk.Button(self.tab_input, text="Xem kết quả tách", command=self.view_split_result).grid(row=5, column=0, columnspan=3, pady=5)
        
        # Supported formats info
        ttk.Label(self.tab_input, text="Định dạng chương hỗ trợ: Chương X, 第X章, 第X章").grid(row=6, column=0, columnspan=3, pady=5)
    
    def setup_translate_tab(self):
        # API settings
        ttk.Label(self.tab_translate, text="API Key:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.api_key_var = tk.StringVar()
        ttk.Entry(self.tab_translate, textvariable=self.api_key_var, width=40, show="*").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.tab_translate, text="Base URL:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.base_url_var = tk.StringVar(value="https://openrouter.ai/api/v1")
        ttk.Entry(self.tab_translate, textvariable=self.base_url_var, width=40).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.tab_translate, text="Model:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_var = tk.StringVar(value="deepseek/deepseek-chat-v3-0324:free")
        ttk.Entry(self.tab_translate, textvariable=self.model_var, width=20).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Translation parameters
        ttk.Label(self.tab_translate, text="Temperature:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.temp_var = tk.DoubleVar(value=0.7)
        ttk.Entry(self.tab_translate, textvariable=self.temp_var, width=10).grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self.tab_translate, text="Max Tokens:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.max_tokens_var = tk.IntVar(value=4000)
        ttk.Entry(self.tab_translate, textvariable=self.max_tokens_var, width=10).grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self.tab_translate, text="Thời gian chờ (giây):").grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
        self.delay_var = tk.IntVar(value=15)
        ttk.Entry(self.tab_translate, textvariable=self.delay_var, width=10).grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(self.tab_translate, text="System Prompt:").grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
        self.system_prompt_var = tk.StringVar(value="system.txt")
        ttk.Entry(self.tab_translate, textvariable=self.system_prompt_var, width=30).grid(row=6, column=1, padx=5, pady=5)
        ttk.Button(self.tab_translate, text="Chọn file...", command=self.browse_system_prompt).grid(row=6, column=2, padx=5, pady=5)
        
        # Thêm phần chọn phạm vi dịch
        ttk.Label(self.tab_translate, text="Phạm vi dịch:").grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
    
        # Part bắt đầu
        ttk.Label(self.tab_translate, text="Part bắt đầu:").grid(row=8, column=0, padx=5, pady=2, sticky=tk.W)
        self.start_part_var = tk.IntVar(value=1)
        ttk.Entry(self.tab_translate, textvariable=self.start_part_var, width=5).grid(row=8, column=1, padx=5, pady=2, sticky=tk.W)
    
        # Part kết thúc
        ttk.Label(self.tab_translate, text="Part kết thúc:").grid(row=9, column=0, padx=5, pady=2, sticky=tk.W)
        self.end_part_var = tk.StringVar()
        ttk.Entry(self.tab_translate, textvariable=self.end_part_var, width=5).grid(row=9, column=1, padx=5, pady=2, sticky=tk.W)
        ttk.Label(self.tab_translate, text="(để trống nếu dịch đến cuối)").grid(row=9, column=2, padx=5, pady=2, sticky=tk.W)
    
        # Di chuyển các phần còn lại xuống dưới
        self.translation_progress_var = tk.StringVar(value="Tiến trình dịch: Chưa bắt đầu")
        ttk.Label(self.tab_translate, textvariable=self.translation_progress_var).grid(row=10, column=0, columnspan=3, pady=5)
    
        self.current_part_var = tk.StringVar(value="Phần hiện tại: Không")
        ttk.Label(self.tab_translate, textvariable=self.current_part_var).grid(row=11, column=0, columnspan=3, pady=5)
    
        # Buttons
        ttk.Button(self.tab_translate, text="Bắt đầu dịch", command=self.start_translation).grid(row=12, column=0, columnspan=3, pady=10)
    
        # Log viewer
        ttk.Label(self.tab_translate, text="Nhật ký dịch thuật:").grid(row=13, column=0, columnspan=3, pady=(10, 0), sticky=tk.W)

        self.log_viewer = scrolledtext.ScrolledText(
        self.tab_translate, 
        wrap=tk.WORD, 
        width=80, 
        height=10,
        state='disabled'
        )
        self.log_viewer.grid(row=14, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
    
        # Export log button
        ttk.Button(
        self.tab_translate, 
        text="Xuất nhật ký", 
        command=self.export_log
        ).grid(row=15, column=2, pady=5, sticky=tk.E)
    
        # Configure grid
        self.tab_translate.grid_rowconfigure(14, weight=1)
        self.tab_translate.grid_columnconfigure(0, weight=1)
    
    def setup_merge_tab(self):
        # Output file
        ttk.Label(self.tab_merge, text="File đầu ra:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_translated_var = tk.StringVar(value="output_translated.txt")
        ttk.Entry(self.tab_merge, textvariable=self.output_translated_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        
        # Merge options
        ttk.Label(self.tab_merge, text="Tùy chọn gộp:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.spacing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.tab_merge, text="Thêm dòng trống giữa các đoạn", variable=self.spacing_var).grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky=tk.W)
        
        self.compact_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.tab_merge, text="Gộp liền không cách (compact)", variable=self.compact_var).grid(row=3, column=0, columnspan=2, padx=5, pady=2, sticky=tk.W)
        
        # Buttons
        ttk.Button(self.tab_merge, text="Gộp chương", command=self.merge_chapters).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(self.tab_merge, text="Xuất ra file TXT", command=self.export_to_txt).grid(row=5, column=0, columnspan=2, pady=5)
    
    def browse_input_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Tệp văn bản", "*.txt")])
        if filename:
            self.input_file_var.set(filename)
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.text_area.delete(1.0, tk.END)
                    self.text_area.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file: {str(e)}")
    
    def browse_system_prompt(self):
        filename = filedialog.askopenfilename(filetypes=[("Tệp văn bản", "*.txt")])
        if filename:
            self.system_prompt_var.set(filename)
    
    def convert_chinese_number(self, chinese_num):
        """Convert Chinese numbers to Arabic"""
        try:
            return cn2an.cn2an(chinese_num, mode="smart")
        except ValueError:
            return None
    
    def is_valid_chapter(self, chapter_num, prev_chapter, max_chapter):
        """Check if chapter number is valid"""
        if chapter_num < 1 or chapter_num > max_chapter:
            return False
        if prev_chapter is None or chapter_num == prev_chapter + 1 or chapter_num == 1:
            return True
        return False
    
    def split_text(self):
        # Validate input
        if not self.validate_split_input():
            return

        # Disable UI during processing
        self.toggle_ui_state(False)
        self.status_var.set("Đang tách văn bản...")

        # Run in separate thread
        threading.Thread(target=self._split_text_thread, daemon=True).start()

    def validate_split_input(self):
        """Validate input before splitting"""
        if not os.path.exists(self.input_file_var.get()):
            messagebox.showerror("Lỗi", "File đầu vào không tồn tại!")
            return False
        return True

    def _split_text_thread(self):
        try:
            input_file = self.input_file_var.get()
            output_file = self.output_split_var.get()
            max_chars = self.max_chars_var.get()
            max_chapter = self.max_chapter_var.get()

            # Read and process file
            with open(input_file, 'r', encoding='utf-8') as file:
                content = file.read()

            # Process chapters
            chapters = self._process_chapters(content, max_chapter)

            # Split into parts
            self.parts = []
            part_id = 1
            
            for chapter_num, chapter_lines in chapters:
                title = chapter_lines[0]
                content = chapter_lines[1:]
                current_part = []
                current_length = 0
                
                for line in content:
                    line_length = len(re.sub(r'\s+', '', line))
                    if current_length + line_length > max_chars and current_part:
                        self._add_part(chapter_num, part_id, title, current_part)
                        part_id += 1
                        current_part = []
                        current_length = 0
                    
                    current_part.append(line)
                    current_length += line_length
                
                if current_part:
                    self._add_part(chapter_num, part_id, title, current_part)
                    part_id += 1

            # Save to file
            self._save_to_file(output_file)

            # Update UI
            self.root.after(0, lambda: [
                self.status_var.set(f"Đã tách: {len(self.parts)} phần"),
                messagebox.showinfo("Thành công", f"Đã tách thành {len(self.parts)} phần"),
                self.toggle_ui_state(True)
            ])

        except Exception as e:
            self.root.after(0, lambda: [
                messagebox.showerror("Lỗi", f"Không thể tách văn bản: {str(e)}"),
                self.status_var.set("Lỗi khi tách"),
                self.toggle_ui_state(True)
            ])

    def _process_chapters(self, content, max_chapter):
        """Process content and split into chapters"""
        lines = content.split('\n')
        chapters = []
        current_chapter = []
        prev_chapter = None
        seen_chapters = set()

        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect chapter headers
            new_format = re.match(r'^(\d{3})\s(.+)$', line)
            chinese_format = re.match(r'^第([一二三四五六七八九十百千]+)章', line)
            arabic_format = re.match(r'^第(\d{1,3})章', line)
            vietnamese_format = re.match(r'^[Cc]hương\s*(\d{1,3})[.:]?\s*(.*)$', line)
            loose_format = re.match(r'^(\d{1,3})([^\d].*)$', line)
            
            chapter_num = None
            title = None
            
            if new_format:
                chapter_num = int(new_format.group(1))
                title = new_format.group(2)
            elif chinese_format:
                chapter_num = self.convert_chinese_number(chinese_format.group(1))
                title = line
            elif arabic_format:
                chapter_num = int(arabic_format.group(1))
                title = line
            elif vietnamese_format:
                chapter_num = int(vietnamese_format.group(1))
                title = f"Chương {chapter_num}: {vietnamese_format.group(2)}"
            elif loose_format:
                chapter_num = int(loose_format.group(1))
                title = line
            
            # Validate chapter number
            if chapter_num and self.is_valid_chapter(chapter_num, prev_chapter, max_chapter):
                if chapter_num in seen_chapters:
                    continue
                seen_chapters.add(chapter_num)
                
                if current_chapter:
                    chapters.append((prev_chapter, current_chapter))
                    current_chapter = []
                
                prev_chapter = chapter_num
                current_chapter.append(title)
            else:
                if current_chapter is not None:
                    current_chapter.append(line)
        
        if current_chapter:
            chapters.append((prev_chapter, current_chapter))
        
        return chapters

    def _add_part(self, chapter_num, part_id, title, content):
        """Add part to cache and update progress"""
        self.parts.append({
            'id': f"Chap_{chapter_num}_Part_{part_id}",
            'title': title,
            'content': content.copy()
        })
        
        # Update progress (thread-safe)
        progress = (len(self.parts) / 50) * 100  # Assuming max 50 parts
        self.root.after(0, lambda p=progress: setattr(self.progress, 'value', p))

    def _save_to_file(self, output_file):
        """Save parts to file"""
        with open(output_file, 'w', encoding='utf-8') as out_file:
            for part in self.parts:
                out_file.write(f"{part['id']}\n")
                out_file.write(f"{part['title']}\n")
                out_file.write("\n".join(part['content']))
                out_file.write("\n\n")

    def toggle_ui_state(self, enabled):
        """Enable/disable UI controls during processing"""
        state = "normal" if enabled else "disabled"
        for tab in [self.tab_input, self.tab_translate, self.tab_merge]:
            for child in tab.winfo_children():
                if isinstance(child, (ttk.Button, ttk.Entry)):
                    child.configure(state=state)

    def view_split_result(self):
        if not self.parts:
            messagebox.showwarning("Cảnh báo", "Không có phần nào để hiển thị. Hãy tách văn bản trước.")
            return
            
        self.text_area.delete(1.0, tk.END)
        for part in self.parts:
            self.text_area.insert(tk.END, f"{part['id']}\n")
            self.text_area.insert(tk.END, f"{part['title']}\n")
            for line in part['content']:
                self.text_area.insert(tk.END, f"{line}\n")
            self.text_area.insert(tk.END, "\n")
    
    def start_translation(self):
        if not self.parts:
            messagebox.showwarning("Cảnh báo", "Không có phần nào để dịch. Hãy tách văn bản trước.")
            return
        
        if not self.api_key_var.get():
            messagebox.showwarning("Cảnh báo", "API key là bắt buộc")
            return
    
        # Lấy phạm vi part cần dịch
        start_part = self.start_part_var.get()
        end_part = self.end_part_var.get()
        end_part = int(end_part) if end_part else len(self.parts)
    
        # Validate phạm vi
        if start_part < 1 or start_part > len(self.parts):
            messagebox.showerror("Lỗi", f"Part bắt đầu phải từ 1 đến {len(self.parts)}")
            return
        if end_part < start_part or end_part > len(self.parts):
            messagebox.showerror("Lỗi", f"Part kết thúc phải từ {start_part} đến {len(self.parts)}")
            return
    
        # Initialize log file
        self.log_file_path = os.path.splitext(self.output_translated_var.get())[0] + ".log"
        self._init_log_file()
    
        self.translated_parts = []
        self.current_part_index = start_part - 1  # Bắt đầu từ part được chọn
        self.is_translating = True
    
        # Clear log viewer
        self.log_viewer.config(state='normal')
        self.log_viewer.delete(1.0, tk.END)
        self.log_viewer.config(state='disabled')
    
        # Hiển thị phạm vi dịch
        range_msg = f"Phạm vi dịch: Từ part {start_part} đến {end_part}\n"
        self._update_log_viewer(range_msg)
        self._write_to_log_file(range_msg)
    
        # Start translation in separate thread
        threading.Thread(target=lambda: self.translate_next_part(end_part), daemon=True).start()

    def _init_log_file(self):
        """Initialize log file with basic info"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write(f"--- BẮT ĐẦU LOG DỊCH {timestamp} ---\n")
            f.write(f"Input: {self.input_file_var.get()}\n")
            f.write(f"Output: {self.output_translated_var.get()}\n")
            f.write(f"Model: {self.model_var.get()}\n")
            f.write(f"Temperature: {self.temp_var.get()}, Max tokens: {self.max_tokens_var.get()}\n\n")
        
        # Display initial log info
        self._update_log_viewer(f"Bắt đầu quá trình dịch lúc {timestamp}\n")

    def _update_log_viewer(self, message):
        """Update log viewer widget"""
        self.log_viewer.config(state='normal')
        self.log_viewer.insert(tk.END, message)
        self.log_viewer.see(tk.END)
        self.log_viewer.config(state='disabled')
        self.log_viewer.update()

    def translate_next_part(self, end_part_index):
        if not self.is_translating or self.current_part_index >= end_part_index:
            self.is_translating = False
            self._finalize_log()
            return
        
        part = self.parts[self.current_part_index]
        part_num = self.current_part_index + 1  # Hiển thị số part bắt đầu từ 1
    
        # Cập nhật UI
        self.current_part_var.set(f"Phần hiện tại: {part['id']} (Part {part_num})")
        self.translation_progress_var.set(f"Tiến trình: Part {part_num}/{end_part_index}")
        self.progress['value'] = (part_num / end_part_index) * 100
    
        # Update log
        log_msg = f"\nĐang dịch {part['id']} (Part {part_num}/{end_part_index})...\n"
        self._update_log_viewer(log_msg)
        self._write_to_log_file(log_msg)

        try:
            # Initialize OpenAI client
            client = openai.OpenAI(
                api_key=self.api_key_var.get(),
                base_url=self.base_url_var.get()
            )
            
            # Load system prompt
            prompt = ""
            if os.path.exists(self.system_prompt_var.get()):
                with open(self.system_prompt_var.get(), 'r', encoding='utf-8') as f:
                    prompt = f.read().strip()
            
            # Translate current part
            full_content = f"{part['title']}\n\n{'\n'.join(part['content'])}"
            
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Dịch từ tiếng Trung sang tiếng Việt:\n\n{full_content}"}
                ],
                model=self.model_var.get(),
                temperature=self.temp_var.get(),
                max_tokens=self.max_tokens_var.get()
            )
            
            translated = response.choices[0].message.content
            if "\n\n" in translated:
                title, content = translated.split("\n\n", 1)
            else:
                title, content = translated, ""
                
            translated_part = {
                'id': part['id'],
                'title': title.strip(),
                'content': content.strip().split('\n')
            }
            
            self.translated_parts.append(translated_part)
            
            status_msg = f"✅ {part['id']} THÀNH CÔNG\n"
            self._update_log_viewer(status_msg)
            self._write_to_log_file(status_msg)
        
            self.current_part_index += 1
        
            # Delay trước khi dịch part tiếp theo
            delay = self.delay_var.get()
            if delay > 0 and self.current_part_index < end_part_index:
                time.sleep(delay)
                self.translate_next_part(end_part_index)
            else:
                self.translate_next_part(end_part_index)
            
        except Exception as e:
            error_msg = f"Lỗi nghiêm trọng: {str(e)}\n"
            self._update_log_viewer(error_msg)
            self._write_to_log_file(error_msg)
            self.is_translating = False
            self.root.after(0, lambda: [
                self.status_var.set("Dịch thất bại"),
                messagebox.showerror("Lỗi", f"Dịch thất bại: {str(e)}")
            ])

    def _write_to_log_file(self, message):
        """Write message to log file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}")

    def _finalize_log(self):
        """Finalize log when translation completes"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_msg = (
            f"\n--- KẾT THÚC LOG DỊCH {timestamp} ---\n"
            f"Tổng số phần đã xử lý: {len(self.translated_parts)}\n"
            f"Phần cuối cùng: {self.translated_parts[-1]['id'] if self.translated_parts else 'Không có'}\n"
        )
        
        self._update_log_viewer(final_msg)
        self._write_to_log_file(final_msg)
        
        self.root.after(0, lambda: [
            self.status_var.set("Dịch hoàn thành"),
            messagebox.showinfo("Thành công", "Đã dịch xong tất cả các phần!")
        ])

    def export_log(self):
        """Export log content to file"""
        if not self.log_file_path or not os.path.exists(self.log_file_path):
            messagebox.showwarning("Cảnh báo", "Không có nhật ký nào để xuất")
            return
            
        try:
            # Open save dialog
            save_path = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("All files", "*.*")],
                initialfile=os.path.basename(self.log_file_path)
            )
            
            if save_path:
                # Copy current log file to new location
                shutil.copy2(self.log_file_path, save_path)
                messagebox.showinfo("Thành công", f"Đã xuất nhật ký đến:\n{save_path}")
                
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất nhật ký thất bại: {str(e)}")

    def merge_chapters(self):
        if not self.translated_parts:
            messagebox.showwarning("Cảnh báo", "Không có phần nào đã dịch để gộp")
            return
        
        try:
            # Nhóm các phần theo chương
            chapters = {}
            for part in self.translated_parts:
                chap_num = part['id'].split('_')[1]
            
                if chap_num not in chapters:
                    chapters[chap_num] = {
                        'title': part['title'],
                        'content': []
                    }
            
                # Xử lý nội dung với tùy chọn cách dòng
                cleaned_content = self._clean_content(part['content'], self.spacing_var.get())
            
                # LUÔN thêm dòng trống giữa các part (quan trọng)
                if chapters[chap_num]['content']:
                    chapters[chap_num]['content'].append("")
            
                chapters[chap_num]['content'].extend(cleaned_content)
        
            # Ghép nội dung cuối cùng
            merged_content = []
            for chap_num in sorted(chapters.keys(), key=int):
                chapter = chapters[chap_num]
                merged_content.append(chapter['title'])
                merged_content.append("")  # Dòng trống sau tiêu đề
            
                # Nối nội dung đã xử lý
                merged_content.append("\n".join(chapter['content']))
                merged_content.append("")  # Dòng trống giữa các chương
        
            # Hiển thị trong khung văn bản
            self.text_area.delete(1.0, tk.END)
            final_content = "\n".join(merged_content).strip()
            self.text_area.insert(tk.END, final_content)
        
            self.status_var.set("Đã gộp chương thành công")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gộp chương thất bại: {str(e)}")
            self.status_var.set("Lỗi khi gộp chương")

    def _clean_content(self, content_lines, add_spacing):
        """Xử lý nội dung với tùy chọn cách dòng"""
        cleaned_lines = []
        for line in content_lines:
            line = line.strip()
            if not line:
                continue
            
            # Xóa khoảng trắng thừa trong dòng
            cleaned_line = " ".join(line.split())
            cleaned_lines.append(cleaned_line)
        
            # Thêm dòng trống giữa các dòng nếu được chọn
            if add_spacing:
                cleaned_lines.append("")
    
        # Xóa dòng trống cuối cùng nếu có
        if cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()
    
        return cleaned_lines
    
    def export_to_txt(self):
        if not self.text_area.get(1.0, tk.END).strip():
            messagebox.showwarning("Cảnh báo", "Không có nội dung để xuất")
            return
            
        output_file = self.output_translated_var.get()
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(self.text_area.get(1.0, tk.END))
            
            messagebox.showinfo("Thành công", f"Đã xuất ra file {output_file}")
            self.status_var.set(f"Đã xuất file: {output_file}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Xuất file thất bại: {str(e)}")
            self.status_var.set("Lỗi khi xuất file")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()