
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import threading
import time
import math

class KnifeOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes("-transparentcolor", "red")
        self.root.configure(bg='red')  # Color que se hará transparente

        # Posicionar al centro inferior
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.center_x = screen_width // 2
        self.center_y = screen_height // 2 

        self.canvas = tk.Canvas(self.root, width=40, height=80, bg='red', highlightthickness=0)
        self.canvas.pack()

        self.overlay_window()

    def run(self):
        self.root.mainloop()

    def overlay_window(self):
        self.root.geometry(f"+{self.center_x - 20}+{self.center_y - 20}")  # Centrado 120x120
        img = Image.open("cuchillo.png").resize(size=(40,40))
       
        self.knife_tk = ImageTk.PhotoImage(img)
        self.icon = self.canvas.create_image(20, 60, image=self.knife_tk)

        self.arc = None
        self.loading = False



    def start_loading(self, *args):
        self.loading = True
        self.arc = self.canvas.create_arc(6, 6, 34, 34, start=90, extent=0, width=4, outline='green', style='arc')
        threading.Thread(target=self.update_arc, daemon=True).start()

    def update_arc(self):
        duration = 5
        start_time = time.time()

        while time.time() - start_time < duration:
            elapsed = time.time() - start_time
            extent = min((elapsed / duration) * 360, 360)
            self.canvas.after(0, self.canvas.itemconfig, self.arc, {"extent": extent})
            time.sleep(0.05)

        self.canvas.create_text(35, 20, text="✔️", font=("Arial", 16), fill="green")
        time.sleep(2)
        self.canvas.after(0, self.canvas.itemconfig, self.icon, {"image": self.knife_tk})
        self.loading = False
