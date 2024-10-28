import cv2
import numpy as np
import pytesseract
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime
import base64

# Set Tesseract location - MODIFY THIS PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class DrawingCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind('<Button-1>', self.start_drawing)
        self.bind('<B1-Motion>', self.draw)
        self.bind('<ButtonRelease-1>', self.stop_drawing)
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Create a numpy array to store the drawing
        self.drawing_array = np.ones((kwargs.get('height', 200), 
                                    kwargs.get('width', 400), 
                                    3), dtype=np.uint8) * 255
    
    def start_drawing(self, event):
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
        
    def draw(self, event):
        if self.drawing:
            # Draw on canvas
            self.create_line(self.last_x, self.last_y, event.x, event.y, 
                           width=2, fill='black', capstyle=tk.ROUND, 
                           smooth=True)
            
            # Draw on numpy array
            cv2.line(self.drawing_array, 
                    (self.last_x, self.last_y), 
                    (event.x, event.y), 
                    (0, 0, 0), 
                    2)
            
            self.last_x = event.x
            self.last_y = event.y
    
    def stop_drawing(self, event):
        self.drawing = False
        
    def clear(self):
        # Clear canvas
        self.delete("all")
        # Clear numpy array
        self.drawing_array.fill(255)
        
    def get_image(self):
        return self.drawing_array.copy()

# Only showing the modified methods - rest remains the same
class FlashcardSystem:
    def combine_images(self, screenshot, text):
        # Get dimensions of screenshot
        h, w = screenshot.shape[:2]
        
        # Create text image
        text_height = 100  # Height for text section
        text_img = np.ones((text_height, w, 3), dtype=np.uint8) * 255  # White background
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        font_color = (0, 0, 0)  # Black text
        
        # Calculate text size to center it
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
        text_x = (w - text_width) // 2  # Center horizontally
        text_y = 50  # Vertically centered in the text area
        
        cv2.putText(text_img, text, (text_x, text_y), font, font_scale, font_color, thickness)
        
        # Combine images vertically
        combined = np.vstack((screenshot, text_img))
        
        return combined

    def save_flashcard(self):
        if not hasattr(self, 'screenshot_image'):
            messagebox.showerror("Error", "Please capture a screenshot first!")
            return
        
        # Get the OCR text
        text = self.ocr_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showerror("Error", "Please process some text first!")
            return
        
        try:
            # Combine screenshot with OCR text
            combined_image = self.combine_images(self.screenshot_image, text)
            
            # Convert to base64 for storage
            _, img_encoded = cv2.imencode('.png', combined_image)
            img_base64 = base64.b64encode(img_encoded).decode('utf-8')
            
            # Create flashcard data
            flashcard = {
                'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'image': img_base64,
                'text': text,
                'created_at': datetime.now().isoformat()
            }
            
            # Load and update flashcards
            with open(os.path.join(self.data_dir, "cards.json"), 'r') as f:
                cards = json.load(f)
            cards.append(flashcard)
            with open(os.path.join(self.data_dir, "cards.json"), 'w') as f:
                json.dump(cards, f)
            
            messagebox.showinfo("Success", "Flashcard saved successfully!")
            self.setup_main_menu()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save flashcard: {str(e)}")

    def display_image(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # Get window width
        window_width = self.root.winfo_width() - 40  # Padding
        
        # Calculate resize dimensions while maintaining aspect ratio
        aspect_ratio = pil_image.width / pil_image.height
        
        if pil_image.width > window_width:
            new_width = window_width
            new_height = int(window_width / aspect_ratio)
        else:
            new_width = pil_image.width
            new_height = pil_image.height
        
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(image=pil_image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo  # Keep a reference!

    def display_flashcard(self):
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add a label showing current card number
        total_cards = len(self.cards)
        card_num_text = f"Card {self.current_card_index + 1} of {total_cards}"
        ttk.Label(frame, text=card_num_text).grid(row=0, column=0, columnspan=3, pady=5)
        
        card = self.cards[self.current_card_index]
        
        # Convert and display image
        img_data = base64.b64decode(card['image'])
        img_array = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        self.image_label = ttk.Label(frame)
        self.image_label.grid(row=1, column=0, columnspan=3, pady=5)
        self.display_image(image)
        
        # Navigation buttons
        nav_frame = ttk.Frame(frame)
        nav_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        ttk.Button(nav_frame, text="Previous", 
                  command=self.prev_card, 
                  state='disabled' if self.current_card_index == 0 else 'normal'
                  ).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(nav_frame, text="Back to Menu", 
                  command=self.setup_main_menu).pack(side=tk.LEFT, padx=5)
                  
        ttk.Button(nav_frame, text="Next", 
                  command=self.next_card,
                  state='disabled' if self.current_card_index == total_cards - 1 else 'normal'
                  ).pack(side=tk.LEFT, padx=5)
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flashcard OCR System")
        
        # Initialize data storage
        self.data_dir = "flashcards"
        self.ensure_data_directory()
        
        # Main menu
        self.setup_main_menu()
        
    def ensure_data_directory(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(os.path.join(self.data_dir, "cards.json")):
            with open(os.path.join(self.data_dir, "cards.json"), 'w') as f:
                json.dump([], f)

    def setup_main_menu(self):
        self.clear_window()
        frame = ttk.Frame(self.root, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(frame, text="Create New Flashcard", 
                  command=self.show_capture_screen).grid(row=0, column=0, pady=10)
        ttk.Button(frame, text="View Flashcards", 
                  command=self.show_flashcards).grid(row=1, column=0, pady=10)
        ttk.Button(frame, text="Exit", 
                  command=self.root.quit).grid(row=2, column=0, pady=10)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_capture_screen(self):
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Screenshot display area
        self.image_label = ttk.Label(frame)
        self.image_label.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Drawing canvas
        self.drawing_canvas = DrawingCanvas(frame, width=400, height=200, 
                                          bg='white', highlightthickness=1, 
                                          highlightbackground="gray")
        self.drawing_canvas.grid(row=1, column=0, columnspan=3, pady=10)
        
        # OCR text display
        self.ocr_text = tk.Text(frame, height=3, width=50)
        self.ocr_text.grid(row=2, column=0, columnspan=3, pady=5)
        
        # Buttons row 1
        btn_frame1 = ttk.Frame(frame)
        btn_frame1.grid(row=3, column=0, columnspan=3, pady=5)
        
        ttk.Button(btn_frame1, text="Capture Screenshot", 
                  command=self.capture_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame1, text="Clear Drawing", 
                  command=self.drawing_canvas.clear).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame1, text="Process Writing", 
                  command=self.process_drawing).pack(side=tk.LEFT, padx=5)
        
        # Buttons row 2
        btn_frame2 = ttk.Frame(frame)
        btn_frame2.grid(row=4, column=0, columnspan=3, pady=5)
        
        ttk.Button(btn_frame2, text="Save Flashcard", 
                  command=self.save_flashcard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="Back to Menu", 
                  command=self.setup_main_menu).pack(side=tk.LEFT, padx=5)

    def capture_screenshot(self):
        self.root.iconify()
        self.root.after(1000, self._perform_capture)

    def _perform_capture(self):
        import pyautogui
        screenshot = pyautogui.screenshot()
        self.screenshot_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        self.display_image(self.screenshot_image)
        self.root.deiconify()

    def process_drawing(self):
        # Get the drawing as an image
        drawing_image = self.drawing_canvas.get_image()
        
        # Preprocess the drawing
        processed = self.preprocess_image(drawing_image)
        
        # Perform OCR
        text = pytesseract.image_to_string(processed)
        
        # Update text display
        self.ocr_text.delete(1.0, tk.END)
        self.ocr_text.insert(tk.END, text)

    def preprocess_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        return binary

    def display_image(self, image):
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        
        # Resize to fit window
        display_width = 600
        ratio = display_width / pil_image.width
        display_height = int(pil_image.height * ratio)
        pil_image = pil_image.resize((display_width, display_height))
        
        photo = ImageTk.PhotoImage(image=pil_image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo

    def combine_images(self, screenshot, text):
        # Create a new image with space for the text
        text_height = 100  # Height for text area
        combined = np.zeros((screenshot.shape[0] + text_height, screenshot.shape[1], 3), dtype=np.uint8)
        combined[:screenshot.shape[0], :] = screenshot
        combined[screenshot.shape[0]:, :] = [255, 255, 255]  # White background for text
        
        # Add text to the image
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_color = (0, 0, 0)
        text_position = (10, screenshot.shape[0] + 30)
        
        cv2.putText(combined, text, text_position, font, font_scale, font_color, 2)
        
        return combined

    def save_flashcard(self):
        if not hasattr(self, 'screenshot_image'):
            messagebox.showerror("Error", "Please capture a screenshot first!")
            return
            
        # Get the OCR text
        text = self.ocr_text.get(1.0, tk.END).strip()
        
        # Combine screenshot with OCR text
        combined_image = self.combine_images(self.screenshot_image, text)
        
        # Convert to base64 for storage
        _, img_encoded = cv2.imencode('.png', combined_image)
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')
        
        # Create flashcard data
        flashcard = {
            'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'image': img_base64,
            'text': text,
            'created_at': datetime.now().isoformat()
        }
        
        # Load and update flashcards
        with open(os.path.join(self.data_dir, "cards.json"), 'r') as f:
            cards = json.load(f)
        cards.append(flashcard)
        with open(os.path.join(self.data_dir, "cards.json"), 'w') as f:
            json.dump(cards, f)
        
        messagebox.showinfo("Success", "Flashcard saved successfully!")
        self.setup_main_menu()

    def show_flashcards(self):
        with open(os.path.join(self.data_dir, "cards.json"), 'r') as f:
            self.cards = json.load(f)
        
        if not self.cards:
            messagebox.showinfo("Info", "No flashcards found!")
            self.setup_main_menu()
            return
        
        self.current_card_index = 0
        self.display_flashcard()

    def display_flashcard(self):
        self.clear_window()
        
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        card = self.cards[self.current_card_index]
        
        # Convert and display image
        img_data = base64.b64decode(card['image'])
        img_array = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        self.image_label = ttk.Label(frame)
        self.image_label.grid(row=0, column=0, columnspan=3, pady=5)
        self.display_image(image)
        
        # Navigation buttons
        ttk.Button(frame, text="Previous", 
                  command=self.prev_card).grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="Back to Menu", 
                  command=self.setup_main_menu).grid(row=1, column=1, pady=5)
        ttk.Button(frame, text="Next", 
                  command=self.next_card).grid(row=1, column=2, pady=5)

    def next_card(self):
        if self.current_card_index < len(self.cards) - 1:
            self.current_card_index += 1
            self.display_flashcard()

    def prev_card(self):
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.display_flashcard()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FlashcardSystem()
    app.run()