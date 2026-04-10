import os
import tkinter as tk
from PIL import Image, ImageTk

LEAGUE_DIR = r"D:\H\League"  # <- Change this path as needed

class AnimatedImage:
    def __init__(self, path, max_width, max_height):
        self.path = path
        self.frames = []
        self.durations = []
        self.load_frames(max_width, max_height)
        self.index = 0

    def resize_frame(self, frame, max_width, max_height):
        w, h = frame.size
        scale_w = max_width / w
        scale_h = max_height / h
        scale = min(scale_w, scale_h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return frame.resize((new_w, new_h), Image.LANCZOS)

    def load_frames(self, max_width, max_height):
        img = Image.open(self.path)
        try:
            while True:
                frame = img.copy()
                frame = self.resize_frame(frame, max_width, max_height)
                self.frames.append(ImageTk.PhotoImage(frame))
                duration = img.info.get('duration', 100)  # default 100 ms
                self.durations.append(duration)
                img.seek(img.tell() + 1)
        except EOFError:
            pass

    def get_frame(self):
        frame = self.frames[self.index]
        duration = self.durations[self.index]
        self.index = (self.index + 1) % len(self.frames)
        return frame, duration


class LeagueUI:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.canvas = tk.Canvas(root, bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.week_folders = self.get_incomplete_weeks()
        self.week_index = 0
        self.match_index = 0
        self.view_index = 0  # 0=left, 1=right, 2=side-by-side
        self.score = ""
        self.images = [None, None]       # For static images or current frame
        self.char_names = ["", ""]
        self.image_paths = ["", ""]
        self.match_folder = ""
        self.match_path = ""

        self.animated_images = [None, None]  # For animated gifs

        self.showing_both = False
        self.animation_running = False

        self.root.bind("<Left>", lambda e: self.switch_view(0))
        self.root.bind("<Right>", lambda e: self.switch_view(1))
        self.root.bind("<Key>", self.key_input)
        self.root.bind("<BackSpace>", self.backspace_key)

        self.load_next_match()

    def get_incomplete_weeks(self):
        weeks = sorted([
            w for w in os.listdir(LEAGUE_DIR)
            if os.path.isdir(os.path.join(LEAGUE_DIR, w)) and w.lower().startswith("week ")
        ], key=lambda x: int(x.split()[1]))
        incomplete = []
        for w in weeks:
            week_path = os.path.join(LEAGUE_DIR, w)
            if any(" VS " in f for f in os.listdir(week_path)):
                incomplete.append(w)
        return incomplete

    def load_next_match(self):
        self.score = ""
        self.showing_both = False
        self.animation_running = False
        while self.week_index < len(self.week_folders):
            week_path = os.path.join(LEAGUE_DIR, self.week_folders[self.week_index])
            matches = sorted([
                f for f in os.listdir(week_path)
                if " VS " in f and f[0].isdigit()
            ], key=lambda x: int(x.split(".")[0]))

            next_match_index = None
            for i, match_folder in enumerate(matches):
                if " VS " in match_folder:
                    next_match_index = i
                    break

            if next_match_index is not None:
                self.match_index = next_match_index
                match_folder = matches[self.match_index]
                name_part = match_folder.split(". ", 1)[1] if ". " in match_folder else match_folder
                self.char_names = name_part.split(" VS ")
                self.match_path = os.path.join(week_path, match_folder)
                files = sorted([
                    f for f in os.listdir(self.match_path)
                    if os.path.isfile(os.path.join(self.match_path, f)) and not f.lower().endswith('.db')
                ])
                if len(files) == 2:
                    file_paths = [os.path.join(self.match_path, f) for f in files]
                    if "(A)" in files[0]:
                        self.image_paths = [file_paths[1], file_paths[0]]
                    else:
                        self.image_paths = [file_paths[0], file_paths[1]]
                    self.match_folder = match_folder
                    self.view_index = 0

                    self.load_images()
                    self.display_image()
                    return
                else:
                    self.match_index += 1
            else:
                self.week_index += 1
                self.match_index = 0

        self.canvas.delete("all")
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            self.root.winfo_screenheight() // 2,
            fill="white", font=("Helvetica", 40),
            text="✅ All matches complete!"
        )

    def load_images(self):
        self.animated_images = [None, None]
        self.images = [None, None]
        self.side_images = [None, None]

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        bar_height = 50
        max_height = screen_h - bar_height

        gap_w = 200  # gap between images for score display
        half_w = screen_w // 2

        # Calculate max side image width (half screen minus half the gap)
        max_side_w = half_w - gap_w // 2
        max_side_h = max_height - 50  # add some vertical padding (50 px)

        for i in range(2):
            ext = os.path.splitext(self.image_paths[i])[1].lower()
            if ext == ".gif":
                # Animated gif fullscreen only for single view, not side-by-side
                self.animated_images[i] = AnimatedImage(self.image_paths[i], screen_w, max_height)
                self.images[i] = self.animated_images[i].frames[0] if self.animated_images[i].frames else None

                # Prepare static first frame resized for side-by-side
                pil_img = Image.open(self.image_paths[i])
                pil_img = pil_img.convert("RGBA")
                w, h = pil_img.size
                scale = min(max_side_w / w, max_side_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
                self.side_images[i] = ImageTk.PhotoImage(pil_img)

            else:
                # Static fullscreen image
                img = Image.open(self.image_paths[i])
                img = self.resize_image(img, screen_w, max_height)
                self.images[i] = ImageTk.PhotoImage(img)

                # Prepare side image resized smaller
                pil_img = Image.open(self.image_paths[i])
                pil_img = pil_img.convert("RGBA")
                w, h = pil_img.size
                scale = min(max_side_w / w, max_side_h / h)
                new_w = int(w * scale)
                new_h = int(h * scale)
                pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
                self.side_images[i] = ImageTk.PhotoImage(pil_img)


    def resize_image(self, img, max_width, max_height):
        w, h = img.size
        scale_w = max_width / w
        scale_h = max_height / h
        scale = min(scale_w, scale_h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        return img.resize((new_w, new_h), Image.LANCZOS)

    def display_image(self):
        self.canvas.delete("all")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        bar_height = 50

        # Draw week label top-left on the bar
        current_week = self.week_folders[self.week_index] if self.week_index < len(self.week_folders) else ""
        self.canvas.create_rectangle(0, 0, screen_w, bar_height, fill="black")
        self.canvas.create_text(
            10, bar_height // 2,
            text=current_week,
            fill="white", font=("Arial", 20, "bold"),
            anchor="w"
        )

        if self.view_index in [0, 1]:
            # Fullscreen single char view (unchanged)
            self.animation_running = False
            # Draw char name next to week label but more centered horizontally
            self.canvas.create_text(
                screen_w // 2, bar_height // 2,
                text=self.char_names[self.view_index],
                fill="white", font=("Arial", 24, "bold")
            )
            if self.animated_images[self.view_index]:
                self.show_gif_frame(self.view_index)
            else:
                self.canvas.create_image(
                    screen_w // 2,
                    bar_height + (self.images[self.view_index].height() // 2),
                    image=self.images[self.view_index]
                )
        else:
            # Side-by-side view (no animation)
            self.animation_running = False
            gap_w = 200
            half_w = screen_w // 2
            max_h = screen_h - bar_height - 50

            max_side_w = half_w - gap_w // 2

            # X coordinates for images centered within their halves
            left_x = max_side_w // 2
            right_x = half_w + gap_w // 2 + max_side_w // 2

            imgs = self.side_images

            # Left image + name
            self.canvas.create_image(left_x, screen_h // 2, image=imgs[0])
            self.canvas.create_text(
                left_x, 30,
                text=self.char_names[0],
                fill="white", font=("Arial", 28, "bold")
            )

            # Right image + name
            self.canvas.create_image(right_x, screen_h // 2, image=imgs[1])
            self.canvas.create_text(
                right_x, 30,
                text=self.char_names[1],
                fill="white", font=("Arial", 28, "bold")
            )

            # Score text centered in the gap
            if len(self.score) > 0:
                score_display = f"{self.score[0]}"
                if len(self.score) == 2:
                    score_display += f"-{self.score[1]}"
                self.canvas.create_text(
                    screen_w // 2, screen_h // 2,
                    text=score_display,
                    fill="white", font=("Arial", 80, "bold")
                )


    def show_gif_frame(self, idx):
        if not self.animation_running:
            self.animation_running = True
        if self.view_index != idx:
            self.animation_running = False
            return
        if self.animated_images[idx]:
            frame, duration = self.animated_images[idx].get_frame()
            self.images[idx] = frame
            self.canvas.delete("all")
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            bar_height = 50

            # Draw week label top-left on the bar
            current_week = self.week_folders[self.week_index] if self.week_index < len(self.week_folders) else ""
            self.canvas.create_rectangle(0, 0, screen_w, bar_height, fill="black")
            self.canvas.create_text(
                10, bar_height // 2,
                text=current_week,
                fill="white", font=("Arial", 20, "bold"),
                anchor="w"
            )

            # Draw char name next to week label
            self.canvas.create_text(
                screen_w // 2, bar_height // 2,
                text=self.char_names[idx],
                fill="white", font=("Arial", 24, "bold")
            )
            self.canvas.create_image(
                screen_w // 2,
                bar_height + (frame.height() // 2),
                image=frame
            )
            # Schedule next frame
            self.root.after(duration, lambda: self.show_gif_frame(idx))

    def switch_view(self, index):
        if self.view_index == 2:
            if index in [0, 1]:
                self.view_index = index
                self.display_image()
        else:
            if index in [0, 1]:
                self.view_index = index
                self.display_image()

    def key_input(self, event):
        if self.view_index in [0, 1]:
            if event.keysym == "Return":
                self.view_index = 2
                self.score = ""
                self.display_image()
            elif event.keysym == "Escape":
                self.root.destroy()
        elif self.view_index == 2:
            if event.char.isdigit() and len(self.score) < 2:
                self.score += event.char
                self.display_image()
            elif event.keysym == "Return" and len(self.score) == 2:
                week_path = os.path.join(LEAGUE_DIR, self.week_folders[self.week_index])
                match_num = self.match_folder.split(". ")[0] if ". " in self.match_folder else ""
                new_name = f"{match_num}. {self.char_names[0]} {self.score[0]}-{self.score[1]} {self.char_names[1]}"
                old_path = os.path.join(week_path, self.match_folder)
                new_path = os.path.join(week_path, new_name)
                try:
                    os.rename(old_path, new_path)
                except Exception as e:
                    print(f"Error renaming folder: {e}")
                self.match_index += 1
                self.load_next_match()
            elif event.keysym == "Escape":
                self.root.destroy()

    def backspace_key(self, event):
        if self.view_index == 2 and len(self.score) > 0:
            self.score = self.score[:-1]
            self.display_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = LeagueUI(root)
    root.mainloop()
