import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import threading
import time
import shutil

class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片格式转换工具")
        
        # 设置窗口大小为屏幕的40%宽度和50%高度
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.4)
        window_height = int(screen_height * 0.5)
        self.root.geometry(f"{window_width}x{window_height}")
        
        self.files = []
        self.output_format = tk.StringVar()
        self.processing = False
        self.paused = False
        self.stop_requested = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # 拖放区域
        self.drop_frame = tk.LabelFrame(self.root, text="拖放图片到这里 (0 个文件)", padx=10, pady=10)
        self.drop_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        self.file_list = tk.Listbox(self.drop_frame, selectmode=tk.EXTENDED)
        self.file_list.pack(fill=tk.BOTH, expand=True)
        
        # 绑定拖放事件
        self.file_list.bind("<Button-1>", self.on_drag_start)
        self.file_list.bind("<B1-Motion>", self.on_drag_motion)
        self.file_list.bind("<ButtonRelease-1>", self.on_drop)
        
        # 添加手动选择文件按钮
        add_file_btn = tk.Button(self.drop_frame, text="添加文件", command=self.add_files)
        add_file_btn.pack(pady=5)
        
        # 格式选择
        format_frame = tk.Frame(self.root)
        format_frame.pack(pady=5, padx=20, fill=tk.X)
        
        tk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT)
        self.format_menu = ttk.Combobox(
            format_frame, 
            textvariable=self.output_format,
            values=["png", "jpg", "gif", "bmp", "webp", "tiff", "ico"],
            state="readonly"
        )
        self.format_menu.pack(side=tk.LEFT, padx=10)
        
        # 进度条
        self.progress_frame = tk.Frame(self.root)
        self.progress_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.progress_label = tk.Label(self.progress_frame, text="等待处理...")
        self.progress_label.pack()
        
        self.progress = ttk.Progressbar(
            self.progress_frame, 
            orient=tk.HORIZONTAL, 
            mode="determinate"
        )
        self.progress.pack(fill=tk.X)
        
        # 按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.start_btn = tk.Button(
            button_frame, 
            text="开始处理", 
            command=self.start_processing
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = tk.Button(
            button_frame, 
            text="暂停处理", 
            command=self.toggle_pause,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            button_frame, 
            text="强制停止", 
            command=self.request_stop,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
    def on_drag_start(self, event):
        self.drag_data = {"x": event.x, "y": event.y}
        
    def on_drag_motion(self, event):
        # 计算移动距离
        delta_x = abs(event.x - self.drag_data["x"])
        delta_y = abs(event.y - self.drag_data["y"])
        
        # 如果移动距离足够大，认为是拖拽操作
        if delta_x > 5 or delta_y > 5:
            self.file_list.config(bg="#e0e0ff")
        
    def on_drop(self, event):
        self.file_list.config(bg="white")
        
        # 获取选中的文件路径
        try:
            files = filedialog.askopenfilenames(
                title="选择图片文件",
                filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.tiff;*.tif;*.ico")]
            )
            
            if files:
                self.add_files_to_list(files)
        except Exception as e:
            messagebox.showerror("错误", f"无法获取文件: {str(e)}")
    
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.webp;*.tiff;*.tif;*.ico")]
        )
        
        if files:
            self.add_files_to_list(files)
    
    def add_files_to_list(self, files):
        # 过滤出支持的图片格式
        supported_formats = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".tif", ".ico")
        for file_path in files:
            if os.path.isfile(file_path) and file_path.lower().endswith(supported_formats):
                if file_path not in self.files:
                    self.files.append(file_path)
                    self.file_list.insert(tk.END, os.path.basename(file_path))
        
        self.update_file_count()
    
    def update_file_count(self):
        count = len(self.files)
        self.drop_frame.config(text=f"拖放图片到这里 (共 {count} 个文件)")
        
    def start_processing(self):
        if not self.files:
            messagebox.showwarning("警告", "请先添加要转换的图片文件")
            return
            
        if not self.output_format.get():
            messagebox.showwarning("警告", "请选择输出格式")
            return
            
        # 创建输出目录
        output_dir = os.path.join(os.getcwd(), "output")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        self.processing = True
        self.paused = False
        self.stop_requested = False
        
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        # 在新线程中处理图片
        threading.Thread(target=self.process_images, daemon=True).start()
        
    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="继续处理" if self.paused else "暂停处理")
        
    def request_stop(self):
        self.stop_requested = True
        
    def process_images(self):
        total_files = len(self.files)
        processed = 0
        
        for i, file_path in enumerate(self.files):
            if self.stop_requested:
                break
                
            while self.paused and not self.stop_requested:
                time.sleep(0.1)
                
            if self.stop_requested:
                break
                
            try:
                # 更新进度
                processed += 1
                progress = (processed / total_files) * 100
                
                self.root.after(0, self.update_progress, processed, total_files, progress)
                
                # 转换图片
                img = Image.open(file_path)
                filename = os.path.splitext(os.path.basename(file_path))[0]
                output_path = os.path.join("output", f"{filename}.{self.output_format.get()}")
                
                # 处理透明背景转换为JPG的情况
                if self.output_format.get() == "jpg" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                img.save(output_path)
                
            except Exception as e:
                self.root.after(0, messagebox.showerror, "错误", f"处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")
                
        # 处理完成
        self.root.after(0, self.processing_complete)
        
    def update_progress(self, processed, total, progress):
        self.progress_label.config(text=f"已处理 {processed}/{total} 个文件")
        self.progress["value"] = progress
        
    def processing_complete(self):
        self.processing = False
        self.paused = False
        self.stop_requested = False
        
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        
        if not self.stop_requested:
            messagebox.showinfo("完成", "所有图片转换完成！")
        else:
            messagebox.showinfo("停止", "处理已停止")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageConverterApp(root)
    root.mainloop()
