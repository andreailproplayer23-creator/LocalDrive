import customtkinter as ctk
from utils import get_ip, generate_qr
import uvicorn
import threading
import os
import webbrowser
import pyperclip
from PIL import ImageTk, Image

# Configurazione Design System
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue") 

class LocalDriveDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LocalDrive Console")
        self.geometry("480x720")
        self.minsize(420, 680)
        
        self.ip = get_ip()
        self.url = f"http://{self.ip}:8000"
        self.storage_path = "storage"
        
        # Layout a griglia principale
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) 
        
        self.setup_ui()
        self.update_stats()

    def setup_ui(self):
        # --- TOP NAV / STATUS BAR ---
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.nav_frame.grid(row=0, column=0, padx=30, pady=(30, 20), sticky="ew")
        
        self.brand_label = ctk.CTkLabel(self.nav_frame, text="LOCALDRIVE", 
                                        font=("Inter", 22, "bold"), text_color="#E1E1E1")
        self.brand_label.pack(side="left")
        
        self.status_dot = ctk.CTkLabel(self.nav_frame, text="● ONLINE", 
                                       font=("Inter", 10, "bold"), text_color="#10b981")
        self.status_dot.pack(side="right")

        # --- CENTRAL CONTENT AREA ---
        self.content_canvas = ctk.CTkFrame(self, fg_color="transparent")
        self.content_canvas.grid(row=1, column=0, padx=30, sticky="nsew")
        self.content_canvas.grid_columnconfigure(0, weight=1)

        # QR CARD (Elegance & Focus)
        self.qr_card = ctk.CTkFrame(self.content_canvas, fg_color="#1A1A1A", 
                                    corner_radius=24, border_width=1, border_color="#2A2A2A")
        self.qr_card.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        qr_img = generate_qr(self.url).resize((180, 180))
        self.photo = ImageTk.PhotoImage(qr_img)
        
        self.qr_display = ctk.CTkLabel(self.qr_card, image=self.photo, text="")
        self.qr_display.pack(pady=(35, 20))
        
        # Pill-style URL Bar
        self.url_bar = ctk.CTkFrame(self.qr_card, fg_color="#0F0F0F", corner_radius=12)
        self.url_bar.pack(padx=30, pady=(0, 30), fill="x")
        
        self.url_text = ctk.CTkEntry(self.url_bar, justify="center", border_width=0, 
                                     fg_color="transparent", font=("JetBrains Mono", 12),
                                     text_color="#888")
        self.url_text.insert(0, self.url)
        self.url_text.configure(state="readonly")
        self.url_text.pack(side="left", expand=True, fill="x", padx=(15, 0))
        
        self.copy_action = ctk.CTkButton(self.url_bar, text="COPY", width=60, height=28, 
                                         fg_color="#222", hover_color="#333", corner_radius=8,
                                         font=("Inter", 10, "bold"), command=self.copy_url)
        self.copy_action.pack(side="right", padx=6, pady=6)

        # STATS GRID (Minimalist)
        self.stats_grid = ctk.CTkFrame(self.content_canvas, fg_color="transparent")
        self.stats_grid.grid(row=1, column=0, sticky="ew")
        self.stats_grid.grid_columnconfigure((0, 1), weight=1)

        self.create_stat_widget(self.stats_grid, "STORAGE USAGE", "0.00 MB", 0)
        self.create_stat_widget(self.stats_grid, "TOTAL FILES", "0", 1)

        # --- ACTIONS FOOTER ---
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=2, column=0, padx=30, pady=(20, 40), sticky="ew")
        
        self.primary_btn = ctk.CTkButton(self.footer, text="LAUNCH DASHBOARD", 
                                         height=54, corner_radius=12,
                                         font=("Inter", 13, "bold"),
                                         fg_color="#FFFFFF", text_color="#000000",
                                         hover_color="#E0E0E0",
                                         command=self.open_browser)
        self.primary_btn.pack(fill="x", pady=(0, 12))
        
        self.secondary_btn = ctk.CTkButton(self.footer, text="OPEN DIRECTORY", 
                                           height=54, corner_radius=12,
                                           font=("Inter", 13, "bold"),
                                           fg_color="transparent", border_width=1,
                                           border_color="#333", hover_color="#1A1A1A",
                                           command=self.open_storage)
        self.secondary_btn.pack(fill="x")

    def create_stat_widget(self, parent, title, value, col):
        frame = ctk.CTkFrame(parent, fg_color="#141414", corner_radius=16, 
                             border_width=1, border_color="#222")
        frame.grid(row=0, column=col, padx=5 if col == 0 else (5, 0), sticky="nsew")
        
        title_lbl = ctk.CTkLabel(frame, text=title, font=("Inter", 9, "bold"), text_color="#555")
        title_lbl.pack(pady=(15, 2))
        
        val_lbl = ctk.CTkLabel(frame, text=value, font=("Inter", 16, "bold"), text_color="#FFF")
        val_lbl.pack(pady=(0, 15))
        
        if col == 0: self.size_val = val_lbl
        else: self.files_val = val_lbl

    def update_stats(self):
        try:
            f_count = 0
            t_size = 0
            for r, d, f_names in os.walk(self.storage_path):
                f_count += len(f_names)
                t_size += sum(os.path.getsize(os.path.join(r, n)) for n in f_names)
            
            self.files_val.configure(text=str(f_count))
            self.size_val.configure(text=f"{t_size / (1024*1024):.2f} MB")
        except: pass
        self.after(3000, self.update_stats)

    def copy_url(self):
        pyperclip.copy(self.url)
        self.copy_action.configure(text="DONE", fg_color="#10b981")
        self.after(1500, lambda: self.copy_action.configure(text="COPY", fg_color="#222"))

    def open_storage(self): os.startfile(os.path.abspath(self.storage_path))
    def open_browser(self): webbrowser.open(self.url)

def start_api():
    from server import app
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

if __name__ == "__main__":
    for d in ["storage", "trash"]: 
        if not os.path.exists(d): os.makedirs(d)
    threading.Thread(target=start_api, daemon=True).start()
    app = LocalDriveDashboard()
    app.mainloop()