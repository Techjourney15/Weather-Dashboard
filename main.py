import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import pygame

# Initialize pygame mixer for sounds
pygame.mixer.init()

# OpenWeatherMap API key and URL
API_KEY = "d2bb390b304cb3d38c21da9efc7bea48"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def fetch_weather(city):
    params = {'q': city, 'appid': API_KEY, 'units': 'metric'}
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Animation function for the temperature graph.
def animate_graph(frame, ax, temp_data):
    x = np.arange(0, 10, 0.1)
    y = np.sin(x + temp_data)
    ax.clear()
    ax.plot(x, y, color='blue')
    ax.set_title("Temperature Fluctuation", fontsize=14)
    ax.set_ylim(-2, 2)
    ax.set_xlim(0, 10)
    ax.tick_params(axis='both', labelsize=10)

class WeatherDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("820x700")  # Initial window size
        self.current_bg_key = 'clear'
        self.current_sound = None
        
        # Bind window close event to stop sound before closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # --- Load original background images (PIL Images) ---
        self.original_bg_images = {}
        bg_files = {
            'clear': 'sunny_background.png',
            'rain': 'rainy_background.png',
            'clouds': 'cloudy_background.png',
            'thunderstorm': 'thunderstorm_background.png'
        }
        for key, filename in bg_files.items():
            path = os.path.join("assets", filename)
            self.original_bg_images[key] = Image.open(path)
        
        # Create initial PhotoImages for backgrounds (starting with size 800x300)
        self.bg_images = {}
        for key, pil_img in self.original_bg_images.items():
            resized = pil_img.resize((800, 300), resample=Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            self.bg_images[key] = ImageTk.PhotoImage(resized, master=self.root)
        
        # --- Load weather icons (fixed size: 100x100) ---
        self.weather_icons = {}
        icon_files = {
            'clear': 'sun.png',
            'clouds': 'cloud.png',
            'rain': 'heavy-rain.png',
            'thunderstorm': 'thunder.png'
        }
        for key, filename in icon_files.items():
            path = os.path.join("assets", filename)
            img = Image.open(path)
            resized = img.resize((100, 100), resample=Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            self.weather_icons[key] = ImageTk.PhotoImage(resized, master=self.root)
        
        # --- Load background sounds ---
        self.sounds = {
            'clear': pygame.mixer.Sound(os.path.join("assets", "sunny_sound.wav")),
            'rain': pygame.mixer.Sound(os.path.join("assets", "rain_sound.wav")),
            'clouds': pygame.mixer.Sound(os.path.join("assets", "wind_sound.wav")),
            'thunderstorm': pygame.mixer.Sound(os.path.join("assets", "thunder_sound.wav"))
        }

        # --- Top Frame: Search Bar ---
        top_frame = ttk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        self.city_label = ttk.Label(top_frame, text="Enter Cities (separate by commas):", font=("Arial", 12))
        self.city_label.pack(side=tk.LEFT)
        self.city_entry = ttk.Entry(top_frame, font=("Arial", 12))
        self.city_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.search_button = ttk.Button(top_frame, text="Search", command=self.update_weather)
        self.search_button.pack(side=tk.LEFT, padx=5)

        # --- Middle Frame: Weather Display (Canvas) ---
        self.canvas = tk.Canvas(root, width=800, height=300)
        self.canvas.pack(padx=10, pady=10, fill=tk.X, expand=True)
        # Display default background and icon
        self.bg_image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_images['clear'])
        self.icon_image_id = self.canvas.create_image(50, 50, anchor=tk.NW, image=self.weather_icons['clear'])
        
        # --- Weather Information Label ---
        self.info_label = ttk.Label(root, text="No city searched", font=("Arial", 16))
        self.info_label.pack(pady=10)
        
        # --- Bottom Frame: Animated Temperature Graph ---
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas_fig.get_tk_widget().pack(padx=10, pady=10, fill=tk.X, expand=True)
        
        # Start the animation with an initial temperature value.
        self.ani = FuncAnimation(self.fig, animate_graph, fargs=(self.ax, 0), interval=1000)
        
        # Bind resize event to adjust layout and resizing
        self.root.bind('<Configure>', self.on_resize)
    
    def update_weather(self):
        cities = self.city_entry.get().strip().split(',')
        city_weather_data = []
        for city in cities:
            city = city.strip()
            if city:
                data = fetch_weather(city)
                if data:
                    weather = data['weather'][0]['main'].lower()
                    temp = data['main']['temp']
                    humidity = data['main']['humidity']
                    desc = data['weather'][0]['description']
                    city_name = data.get('name', city)
                    
                    # Collect weather info
                    city_weather_data.append({
                        'name': city_name,
                        'weather': weather,
                        'temp': temp,
                        'desc': desc,
                        'humidity': humidity
                    })
                else:
                    city_weather_data.append({'name': city, 'weather': None})

        # Clear existing weather data
        self.info_label.config(text="")

        # Update weather info for each city
        for city_data in city_weather_data:
            if city_data['weather']:
                self.display_weather(city_data)
            else:
                self.info_label.config(text=f"{city_data['name']} not found!")

    def display_weather(self, city_data):
        weather = city_data['weather']
        temp = city_data['temp']
        humidity = city_data['humidity']
        desc = city_data['desc']
        city_name = city_data['name']

        # Update background and icon images (use 'clear' as fallback)
        bg_key = weather if weather in self.bg_images else 'clear'
        self.current_bg_key = bg_key
        self.canvas.itemconfig(self.bg_image_id, image=self.bg_images[bg_key])
        icon_img = self.weather_icons.get(weather, self.weather_icons['clear'])
        self.canvas.itemconfig(self.icon_image_id, image=icon_img)
        
        # Update weather info label
        info_text = f"{city_name}: {temp}°C, {desc.capitalize()}, Humidity: {humidity}%"
        self.info_label.config(text=info_text)
        
        # Update the animated graph with the new temperature value
        self.ani.event_source.stop()  # Stop previous animation if any
        self.ani = FuncAnimation(self.fig, animate_graph, fargs=(self.ax, temp), interval=1000)  # Start new animation with updated temp
        self.canvas_fig.draw()
        
        # Play the background sound corresponding to the weather.
        if self.current_sound is not None:
            self.current_sound.stop()
        sound = self.sounds.get(bg_key)
        if sound:
            self.current_sound = sound
            self.current_sound.play(loops=-1)

    def on_resize(self, event):
        # Update canvas size based on window size.
        new_width = self.root.winfo_width() - 20
        new_height = int(new_width * 300 / 800)
        self.canvas.config(width=new_width, height=new_height)
        
        # Resize the current background image using the original PIL image.
        bg_key = self.current_bg_key if self.current_bg_key in self.original_bg_images else 'clear'
        original_img = self.original_bg_images[bg_key]
        resized = original_img.resize((new_width, new_height),
                    resample=Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
        self.bg_images[bg_key] = ImageTk.PhotoImage(resized, master=self.root)
        self.canvas.itemconfig(self.bg_image_id, image=self.bg_images[bg_key])
        
        # Adjust font sizes dynamically based on window width.
        scale_factor = new_width / 800
        new_font_size = int(8 * scale_factor)
        self.info_label.config(font=("Arial", new_font_size))
        self.city_label.config(font=("Arial", new_font_size))
        self.city_entry.config(font=("Arial", new_font_size))
        
        # Resize the weather icon size dynamically.
        icon_size = int(100 * scale_factor)
        self.weather_icons = {}
        for key, filename in {'clear': 'sun.png', 'clouds': 'cloud.png', 'rain': 'heavy-rain.png', 'thunderstorm': 'thunder.png'}.items():
            img = Image.open(os.path.join("assets", filename))
            resized = img.resize((icon_size, icon_size), resample=Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            self.weather_icons[key] = ImageTk.PhotoImage(resized, master=self.root)

        # Adjust button size and text size
        button_font_size = int(8 * scale_factor)  # Increase this number to make the button text larger
        self.search_button.config(font=("Arial", button_font_size), padx=8, pady=5)  # Increased padding
        
        # Adjust graph width to fit the window
        self.fig.set_size_inches(new_width / 100, 3)  # Change graph width based on window size
        self.canvas_fig.draw()

    def on_close(self):
        if self.current_sound:
            self.current_sound.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherDashboard(root)
    root.mainloop()

