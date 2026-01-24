import pygame
import sys
import math
import random
import json
import os
import time
import requests
import urllib.request
import re
from datetime import datetime, timedelta
import threading
import socket
import hashlib

# Caching untuk animasi frame
animation_cache = {}

def cache_animation_frames():
    """Cache all animation frames for characters."""
    for character in character_frame_counts.keys():
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
        animation_frames = load_animation_frames(character, actions, character_frame_counts[character])
        animation_cache[character] = animation_frames
    print("All animation frames cached successfully.")

def load_data_in_background():
    character_data = load_character_data()
    dungeon_data = load_dungeon_data()
    gacha_data = load_gacha_data()
    daily_login_data = load_daily_login_data()
    
    print("All data loaded in background.")

SAVE_FILE = "interface_save.json"
current_interface = None
pygame.init()
pygame.mixer.init()

def play_sound_effect(action, character_type):
    """Play sound effects based on the action and character type."""
    sound_effects = {
        "Shield": "soundeffects/shield.mp3",
        "Jump": "soundeffects/jump.mp3",
        "Run": "soundeffects/run.mp3",
        "Attack_1": {
            "Magician": "soundeffects/magician1.mp3",
            "Samurai": "soundeffects/samurai1.mp3",
            "Soldier": "soundeffects/soldier1.mp3"
        },
        "Attack_2": {
            "Magician": "soundeffects/magician2.mp3",
            "Samurai": "soundeffects/samurai2.mp3",
            "Soldier": "soundeffects/soldier2.mp3"
        },
        "Attack_3": {
            "Magician": "soundeffects/magician3.mp3",
            "Samurai": "soundeffects/samurai3.mp3",
            "Soldier": "soundeffects/soldier3.mp3"
        }
    }

    if action in sound_effects:
        if isinstance(sound_effects[action], dict):
            # For attack actions, get the sound based on character type
            sound_file = sound_effects[action].get(character_type)
            if sound_file:
                sound = pygame.mixer.Sound(sound_file)
                sound.play()  # Play the sound immediately
        else:
            # For other actions
            sound = pygame.mixer.Sound(sound_effects[action])
            sound.play()  # Play the sound immediately

# Karasu Tengu frame counts
karasu_frame_counts = {
    "Attack_1": 6,
    "Attack_2": 4,
    "Attack_3": 3,
    "Dead": 6,
    "Hurt": 3,
    "Idle": 6,
    "Jump": 15,
    "Run": 8,
    "Walk": 8
}

# Karasu Tengu damage values
karasu_damage = {
    "Attack_1": 5,
    "Attack_2": 15,
    "Attack_3": 30
}

character_frame_counts = {
    "Samurai": {
        "Attack_1": 4,
        "Attack_2": 5,
        "Attack_3": 4,
        "Dead": 6,
        "Hurt": 3,
        "Idle": 6,
        "Jump": 9,
        "Run": 8,
        "Shield": 2,
        "Walk": 9
    },
    "Soldier": {
        "Attack_1": 4,
        "Attack_2": 4,
        "Attack_3": 4,
        "Dead": 4,
        "Hurt": 3,
        "Idle": 9,
        "Jump": 16,
        "Run": 8,
        "Shield": 7,
        "Walk": 8
    },
    "Magician": {
        "Attack_1": 7,
        "Attack_2": 9,
        "Attack_3": 9,
        "Dead": 4,
        "Hurt": 4,
        "Idle": 8,
        "Jump": 8,
        "Run": 8,
        "Shield": 16,
        "Walk": 7
    }
}

# Damage values for each character
character_damage = {
    "Samurai": {"Attack_1": 4, "Attack_2": 6, "Attack_3": 8},
    "Soldier": {"Attack_1": 5, "Attack_2": 7, "Attack_3": 9},
    "Magician": {"Attack_1": 6, "Attack_2": 8, "Attack_3": 10}
}

# Character attack ranges
character_ranges = {
    "Samurai": 70,    # Close range
    "Soldier": 110,   # Medium range
    "Magician": 110   # Long range
}

# Ukuran layar fisik
info = pygame.display.Info()
SCREEN_W, SCREEN_H = info.current_w, info.current_h
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("RPG Game - Custom Fullscreen")

# Ukuran virtual tetap
VIRTUAL_W, VIRTUAL_H = 800, 600
virtual_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))

# Warna
BORDER_COLOR = (10, 10, 20)
WHITE = (255, 255, 255)
BUTTON_COLOR = (40, 40, 80)
HOVER_COLOR = (80, 160, 200)
TEXT_COLOR = (255, 255, 255)
SELECTED_COLOR = (120, 200, 120)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Font
title_font = pygame.font.SysFont("Georgia", 48, bold=True)
button_font = pygame.font.SysFont("Verdana", 28)
small_font = pygame.font.SysFont("Verdana", 20)
clock = pygame.time.Clock()

# Background utama
background_image = pygame.image.load("assets/background.png").convert()
background_image = pygame.transform.smoothscale(background_image, (VIRTUAL_W, VIRTUAL_H))

# Warna pelangi
def get_rainbow_color(time_offset=0):
    t = pygame.time.get_ticks() * 0.002
    r = int(127 * (1 + math.sin(t + time_offset)))
    g = int(127 * (1 + math.sin(t + time_offset + 2)))
    b = int(127 * (1 + math.sin(t + time_offset + 4)))
    return (r, g, b)

# Tombol UI
class Button:
    def __init__(self, image_path, label, x, y, width, height, callback):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.smoothscale(self.image, (height - 20, height - 20))
        self.label = label
        self.rect = pygame.Rect(x, y, width, height)
        self.callback = callback
        
        # Animation state
        self.hover_scale = 1.0
        self.glow_alpha = 0.0
        self.last_hovered = False
        
        # Pre-render semua text dan surface untuk optimasi maksimal
        self.text_surface = button_font.render(self.label, True, TEXT_COLOR)
        self.text_shadow = button_font.render(self.label, True, (0, 0, 0))
        self.glow_text = button_font.render(self.label, True, (255, 255, 255))
        
        # Pre-calculate scaled image untuk hover state
        self.scaled_image = pygame.transform.scale(self.image, 
            (int(self.image.get_width() * 1.05), int(self.image.get_height() * 1.05)))
        
        # Pre-create glow surface
        glow_size = (width + 16, height + 16)
        self.glow_surface = pygame.Surface(glow_size, pygame.SRCALPHA)
        
        # Color constants untuk menghindari tuple creation berulang
        self.COLORS = {
            'base_normal': (47, 79, 79),
            'base_hover': (70, 130, 180),
            'border_normal': (105, 105, 105),
            'border_hover': (135, 206, 235),
            'highlight_normal': (70, 130, 180),
            'highlight_hover': (100, 149, 237),
            'shadow': (20, 20, 20),
            'inner_border': (255, 255, 255),
            'glow_base': (135, 206, 235)
        }
        
        # Pre-calculate positions
        self.image_base_x = 15
        self.text_base_x = 25 + self.image.get_width()
        
        # Corner decoration points (pre-calculated)
        self.corner_size = 8
        self._setup_corner_points()

    def _setup_corner_points(self):
        """Pre-calculate corner decoration points"""
        cs = self.corner_size
        self.corner_points = {
            'top_left': [(cs, 2), (2, 2), (2, cs)],
            'top_right': [(-cs, 2), (-2, 2), (-2, cs)],
            'bottom_left': [(2, -cs), (2, -2), (cs, -2)],
            'bottom_right': [(-cs, -2), (-2, -2), (-2, -cs)]
        }

    def _lerp(self, a, b, t):
        """Fast linear interpolation"""
        return a + (b - a) * t

    def _lerp_color(self, color1, color2, t):
        """Fast color interpolation"""
        return (
            int(color1[0] + (color2[0] - color1[0]) * t),
            int(color1[1] + (color2[1] - color1[1]) * t),
            int(color1[2] + (color2[2] - color1[2]) * t)
        )

    def draw(self, surface, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        
        # Optimized animation dengan frame rate independence
        if is_hovered != self.last_hovered:
            self.last_hovered = is_hovered
        
        # Faster animation interpolation
        target_scale = 1.02 if is_hovered else 1.0
        self.hover_scale = self._lerp(self.hover_scale, target_scale, 0.2)
        
        target_glow = 80.0 if is_hovered else 0.0
        self.glow_alpha = self._lerp(self.glow_alpha, target_glow, 0.25)
        
        # Calculate scaled rect (optimized)
        if abs(self.hover_scale - 1.0) > 0.001:
            center = self.rect.center
            new_width = int(self.rect.width * self.hover_scale)
            new_height = int(self.rect.height * self.hover_scale)
            scaled_rect = pygame.Rect(0, 0, new_width, new_height)
            scaled_rect.center = center
        else:
            scaled_rect = self.rect
        
        # Interpolate colors (optimized)
        hover_progress = (self.hover_scale - 1.0) / 0.02 if self.hover_scale > 1.0 else 0.0
        hover_progress = max(0.0, min(1.0, hover_progress))
        
        base_color = self._lerp_color(self.COLORS['base_normal'], self.COLORS['base_hover'], hover_progress)
        border_color = self._lerp_color(self.COLORS['border_normal'], self.COLORS['border_hover'], hover_progress)
        inner_highlight = self._lerp_color(self.COLORS['highlight_normal'], self.COLORS['highlight_hover'], hover_progress)
        
        # Draw glow effect (optimized - only when needed)
        if self.glow_alpha > 1.0:
            glow_rect = scaled_rect.inflate(8, 8)
            self.glow_surface.fill((0, 0, 0, 0))  # Clear surface
            glow_color = (*self.COLORS['glow_base'], int(self.glow_alpha))
            pygame.draw.rect(self.glow_surface, glow_color, 
                           (0, 0, glow_rect.width, glow_rect.height), border_radius=16)
            surface.blit(self.glow_surface, glow_rect.topleft)
        
        # Draw shadow (single operation)
        shadow_rect = scaled_rect.move(3, 3)
        pygame.draw.rect(surface, (*self.COLORS['shadow'], 150), shadow_rect, border_radius=12)
        
        # Draw main button body
        pygame.draw.rect(surface, base_color, scaled_rect, border_radius=12)
        
        # Draw inner highlight
        highlight_rect = pygame.Rect(scaled_rect.x + 3, scaled_rect.y + 3, 
                                   scaled_rect.width - 6, scaled_rect.height // 3)
        pygame.draw.rect(surface, inner_highlight, highlight_rect, border_radius=10)
        
        # Draw borders (combined operations)
        pygame.draw.rect(surface, border_color, scaled_rect, 3, border_radius=12)
        inner_border_rect = scaled_rect.inflate(-6, -6)
        pygame.draw.rect(surface, (*self.COLORS['inner_border'], 100), inner_border_rect, 1, border_radius=9)
        
        # Draw image (optimized selection)
        image_x = scaled_rect.x + self.image_base_x
        if is_hovered:
            image_y = scaled_rect.y + (scaled_rect.height - self.scaled_image.get_height()) // 2 - 2
            surface.blit(self.scaled_image, (image_x, image_y))
        else:
            image_y = scaled_rect.y + (scaled_rect.height - self.image.get_height()) // 2
            surface.blit(self.image, (image_x, image_y))
        
        # Draw text (optimized positioning)
        current_image = self.scaled_image if is_hovered else self.image
        text_x = scaled_rect.x + self.text_base_x + (current_image.get_width() - self.image.get_width())
        text_y = scaled_rect.centery - self.text_surface.get_height() // 2
        
        # Text shadow
        surface.blit(self.text_shadow, (text_x + 2, text_y + 2))
        
        # Main text (pre-rendered selection)
        if is_hovered:
            surface.blit(self.glow_text, (text_x, text_y))
        else:
            surface.blit(self.text_surface, (text_x, text_y))
        
        # Draw corner decorations (optimized with pre-calculated points)
        self._draw_corners(surface, scaled_rect, border_color)

    def _draw_corners(self, surface, rect, color):
        """Optimized corner drawing"""
        # Top-left
        points = [(rect.left + p[0], rect.top + p[1]) for p in self.corner_points['top_left']]
        pygame.draw.lines(surface, color, False, points, 2)
        
        # Top-right
        points = [(rect.right + p[0], rect.top + p[1]) for p in self.corner_points['top_right']]
        pygame.draw.lines(surface, color, False, points, 2)
        
        # Bottom-left
        points = [(rect.left + p[0], rect.bottom + p[1]) for p in self.corner_points['bottom_left']]
        pygame.draw.lines(surface, color, False, points, 2)
        
        # Bottom-right
        points = [(rect.right + p[0], rect.bottom + p[1]) for p in self.corner_points['bottom_right']]
        pygame.draw.lines(surface, color, False, points, 2)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

# Tombol musik
class MusicToggleButton:
    def __init__(self, x, y, size):
        self.on_icon = pygame.image.load("assets/music_on.png").convert_alpha()
        self.off_icon = pygame.image.load("assets/music_off.png").convert_alpha()
        self.on_icon = pygame.transform.smoothscale(self.on_icon, (size, size))
        self.off_icon = pygame.transform.smoothscale(self.off_icon, (size, size))
        self.rect = pygame.Rect(x, y, size, size)
        self.is_playing = False
        pygame.mixer.music.load("assets/musicbg.mp3")
        pygame.mixer.music.set_volume(0.5)

    def draw(self, surface):
        surface.blit(self.on_icon if self.is_playing else self.off_icon, self.rect.topleft)

    def handle_click(self, pos):
        if self.rect.collidepoint(pos):
            if self.is_playing:
                pygame.mixer.music.pause()
            else:
                if not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.unpause()
            self.is_playing = not self.is_playing

# Load animasi
def load_animation_frames(folder, actions, frame_counts):
    """Load animation frames from cache or file."""
    if folder in animation_cache:
        return animation_cache[folder]
    
    animations = {}
    for action in actions:
        try:
            sheet = pygame.image.load(f"assets/{folder}/{action}.png").convert_alpha()
            count = frame_counts.get(action, 1)
            frame_width = sheet.get_width() // count
            frame_height = sheet.get_height()
            frames = [
                sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height))
                for i in range(count)
            ]
            animations[action] = frames
        except Exception as e:
            print(f"Error loading {action} for {folder}: {e}")
            animations[action] = []
    
    # Cache the loaded animations
    animation_cache[folder] = animations
    return animations

# Enhanced Enemy class with better AI
class Enemy:
    def __init__(self, character_type, x, y):
        self.character_type = character_type
        self.pos = [x, y]
        self.hp = 100
        self.max_hp = 100
        self.mp = 100
        self.max_mp = 100
        self.action = "Idle"
        self.frame_idx = 0
        self.timer = 0
        self.last_action_time = pygame.time.get_ticks()
        self.last_mp_regen = pygame.time.get_ticks()
        self.action_cooldown = 1500  # 1.5 seconds between actions
        self.is_dead = False
        self.is_hurt = False
        self.hurt_timer = 0
        self.death_animation_complete = False
        self.is_shielding = False
        self.shield_timer = 0
        self.attack_range = character_ranges[character_type]
        self.last_attack_time = 0
        self.ai_state = "IDLE"  # AI states: IDLE, APPROACH, ATTACK, DEFEND, RETREAT
        self.state_timer = 0
        self.movement_speed = 2
        
        # Load animations
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt", "Walk"]
        self.animations = load_animation_frames(character_type, actions, character_frame_counts[character_type])
        
        # Frame delays
        self.frame_delays = {
            "Idle": 160,
            "Run": 140,
            "Jump": 150,
            "Shield": 170,
            "Attack_1": 130,
            "Attack_2": 135,
            "Attack_3": 130,
            "Dead": 170,
            "Hurt": 170,
            "Walk": 150
        }
    
    def take_damage(self, damage):
        if self.is_dead:
            return
        
        # Shield blocks 100% damage
        if self.is_shielding:
            return
            
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.action = "Dead"
            self.frame_idx = 0
            self.timer = 0
        else:
            self.is_hurt = True
            self.hurt_timer = pygame.time.get_ticks()
            self.action = "Hurt"
            self.frame_idx = 0
            self.timer = 0
            self.is_shielding = False
    
    def update_ai_state(self, player_pos):
        """Enhanced AI decision making"""
        current_time = pygame.time.get_ticks()
        distance_to_player = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)

        if current_time - self.state_timer > 2000:  # Change state every 2 seconds
            health_percentage = self.hp / self.max_hp
            
            if health_percentage < 0.3:  # Low health - more defensive
                if random.random() < 0.6:
                    self.ai_state = "DEFEND"
                elif distance_to_player > self.attack_range * 1.5:
                    self.ai_state = "APPROACH"
                else:
                    self.ai_state = "RETREAT"
            elif distance_to_player > self.attack_range:
                self.ai_state = "APPROACH"
            elif distance_to_player < self.attack_range * 0.7:
                if random.random() < 0.7:
                    self.ai_state = "ATTACK"
                else:
                    self.ai_state = "DEFEND"
            else:
                # In optimal range
                action_choice = random.random()
                if action_choice < 0.5:
                    self.ai_state = "ATTACK"
                elif action_choice < 0.8:
                    self.ai_state = "DEFEND"
                else:
                    self.ai_state = "APPROACH"
            
            self.state_timer = current_time
    
    def execute_ai_action(self, player_pos):
        """Execute action based on AI state"""
        current_time = pygame.time.get_ticks()
        distance_to_player = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)

        if self.hp < 50:  # Run when health is below 50
            self.movement_speed = 4  # Increase speed for running
        else:
            self.movement_speed = 2  # Normal speed

        if self.ai_state == "APPROACH":
            # Move towards player
            if self.pos[0] < player_pos[0]:
                self.pos[0] += self.movement_speed
            else:
                self.pos[0] -= self.movement_speed
            
            if self.pos[1] < player_pos[1]:
                self.pos[1] += self.movement_speed
            else:
                self.pos[1] -= self.movement_speed
            
            if abs(self.pos[0] - player_pos[0]) > 50 or abs(self.pos[1] - player_pos[1]) > 50:
                self.action = "Run"
            else:
                self.action = "Idle"
                
        elif self.ai_state == "RETREAT":
            # Move away from player
            if self.pos[0] < player_pos[0]:
                self.pos[0] -= self.movement_speed
            else:
                self.pos[0] += self.movement_speed
            
            if self.pos[1] < player_pos[1]:
                self.pos[1] -= self.movement_speed
            else:
                self.pos[1] += self.movement_speed
            
            self.action = "Run"
            
        elif self.ai_state == "ATTACK":
            # Choose random attack if we have MP
            if current_time - self.last_action_time > self.action_cooldown:
                attack_costs = {"Attack_1": 5, "Attack_2": 8, "Attack_3": 12}
                available_attacks = [atk for atk, cost in attack_costs.items() if self.mp >= cost]
                
                if available_attacks:
                    chosen_attack = random.choice(available_attacks)
                    self.action = chosen_attack
                    self.frame_idx = 0
                    self.timer = 0
                    self.mp -= attack_costs[chosen_attack]
                    self.last_action_time = current_time
                    self.is_shielding = False
                else:
                    self.action = "Idle"
                    
        elif self.ai_state == "DEFEND":
            # Use shield
            if self.mp >= 2:  # Small MP cost for shield
                self.action = "Shield"
                self.is_shielding = True
                self.shield_timer = current_time
                if current_time - self.last_action_time > 500:  # Drain MP slowly while shielding
                    self.mp -= 1
                    self.last_action_time = current_time
            else:
                self.action = "Idle"
                self.is_shielding = False
        else:
            # IDLE state
            self.action = "Idle"
            self.is_shielding = False
    
    def update(self, dt, player_pos):
        current_time = pygame.time.get_ticks()
        
        # MP regeneration
        if current_time - self.last_mp_regen > 2000:  # Regen MP every 2 seconds
            self.mp = min(self.max_mp, self.mp + 5)
            self.last_mp_regen = current_time
        
        # Handle death
        if self.is_dead and not self.death_animation_complete:
            self.timer += dt
            delay = self.frame_delays.get("Dead", 170)
            if self.timer >= delay:
                self.timer = 0
                if self.animations["Dead"]:
                    self.frame_idx += 1
                    if self.frame_idx >= len(self.animations["Dead"]):
                        self.death_animation_complete = True
                        self.frame_idx = len(self.animations["Dead"]) - 1
            return
        
        if self.is_dead:
            return
        
        # Handle hurt state
        if self.is_hurt:
            if current_time - self.hurt_timer > 500:  # Hurt animation duration
                self.is_hurt = False
                self.action = "Idle"
                self.frame_idx = 0
                self.timer = 0
        
        # Handle shield timeout
        if self.is_shielding and current_time - self.shield_timer > 3000:  # Shield for max 3 seconds
            self.is_shielding = False
        
        # AI behavior (only if not hurt)
        if not self.is_hurt:
            self.update_ai_state(player_pos)
            self.execute_ai_action(player_pos)
        
        # Keep enemy within screen bounds
        sprite_width = 160
        left_limit = sprite_width // 2
        right_limit = VIRTUAL_W - sprite_width // 2
        
        if self.pos[0] < left_limit:
            self.pos[0] = left_limit
        elif self.pos[0] > right_limit:
            self.pos[0] = right_limit
        
        # Update animation
        self.timer += dt
        delay = self.frame_delays.get(self.action, 130)
        if self.timer >= delay:
            self.timer = 0
            if self.animations[self.action]:
                self.frame_idx += 1
                if self.frame_idx >= len(self.animations[self.action]):
                    if "Attack" in self.action:
                        self.action = "Idle"
                        self.frame_idx = 0
                    elif self.action == "Shield" and self.is_shielding:
                        self.frame_idx = len(self.animations["Shield"]) - 1
                    else:
                        self.frame_idx = 0
    
    def draw(self, surface):
        if self.animations[self.action]:
            frame_idx = min(self.frame_idx, len(self.animations[self.action]) - 1)
            sprite = pygame.transform.scale(self.animations[self.action][frame_idx], (160, 160))
            # Flip sprite to face left (towards player)
            sprite = pygame.transform.flip(sprite, True, False)
            rect = sprite.get_rect(midbottom=(self.pos[0], self.pos[1] + 100))
            surface.blit(sprite, rect.topleft)
        
        # Draw health bar
        if not self.is_dead:
            bar_width = 100
            bar_height = 8
            bar_x = self.pos[0] - bar_width // 2
            bar_y = self.pos[1] - 180
            
            # Background bar
            pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            # Health bar
            health_width = int((self.hp / self.max_hp) * bar_width)
            pygame.draw.rect(surface, RED, (bar_x, bar_y, health_width, bar_height))
            
            # MP bar
            mp_bar_y = bar_y + 12
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, mp_bar_y, bar_width, bar_height))
            mp_width = int((self.mp / self.max_mp) * bar_width)
            pygame.draw.rect(surface, BLUE, (bar_x, mp_bar_y, mp_width, bar_height))
            
            # Enemy name and AI state
            name_text = small_font.render(f"Enemy {self.character_type}", True, WHITE)
            name_rect = name_text.get_rect(center=(self.pos[0], bar_y - 15))
            surface.blit(name_text, name_rect)
            
            # Show AI state for debugging (you can remove this)
            state_text = pygame.font.SysFont("Verdana", 12).render(self.ai_state, True, WHITE)
            state_rect = state_text.get_rect(center=(self.pos[0], bar_y - 30))
            surface.blit(state_text, state_rect)
            
            # Shield indicator
            if self.is_shielding:
                shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                shield_rect = shield_text.get_rect(center=(self.pos[0], self.pos[1] - 200))
                surface.blit(shield_text, shield_rect)
    
    def get_attack_damage(self):
        if "Attack" in self.action:
            return character_damage[self.character_type][self.action]
        return 0
    
    def is_attacking(self):
        return "Attack" in self.action and self.frame_idx > 0 and self.frame_idx < len(self.animations[self.action]) - 1
    
    def get_attack_range(self):
        return self.attack_range

# File untuk menyimpan data karakter yang sudah dibeli
CHARACTER_DATA_FILE = "character_data.json"

# Tambahkan data untuk Hero Knight
hero_knight_frame_counts = {
    "Attack_1": 5,
    "Attack_2": 4,
    "Attack_3": 4,
    "Dead": 6,
    "Hurt": 2,
    "Idle": 4,
    "Walk": 4,
    "Jump": 6,
    "Run": 7,
    "Shield": 1
}

character_frame_counts["Hero_Knight"] = hero_knight_frame_counts

# Update character damage untuk Hero Knight
character_damage["Hero_Knight"] = {"Attack_1": 15, "Attack_2": 35, "Attack_3": 50}
character_ranges["Hero_Knight"] = 90  # Medium range

# Data karakter baru dengan frame counts
new_character_frame_counts = {
    "Kitsune": {
        "Attack_1": 10,
        "Attack_2": 10,
        "Attack_3": 7,
        "Dead": 10,
        "Hurt": 2,
        "Idle": 8,
        "Jump": 10,
        "Run": 8,
        "Shield": 6,
        "Walk": 8
    },
    "Gangster": {
        "Attack_1": 6,
        "Attack_2": 4,
        "Attack_3": 6,
        "Dead": 5,
        "Hurt": 4,
        "Idle": 13,
        "Jump": 10,
        "Run": 10,
        "Shield": 7,
        "Walk": 10
    },
    "Kunoichi": {
        "Attack_1": 6,
        "Attack_2": 8,
        "Attack_3": 6,
        "Dead": 5,
        "Hurt": 2,
        "Idle": 9,
        "Jump": 10,
        "Run": 8,
        "Shield": 9,
        "Walk": 8
    }
}

# Data damage karakter baru
new_character_damage = {
    "Kitsune": {"Attack_1": 15, "Attack_2": 0, "Attack_3": 35},  # Attack_2 adalah protection
    "Gangster": {"Attack_1": 6, "Attack_2": 12, "Attack_3": 16},
    "Kunoichi": {"Attack_1": 8, "Attack_2": 16, "Attack_3": 32}
}

# Data range karakter baru
new_character_ranges = {
    "Kitsune": 80,
    "Gangster": 90,
    "Kunoichi": 100
}

# Data harga karakter
character_prices = {
    "Kitsune": 40,
    "Gangster": 30,
    "Kunoichi": 60
}

# Data deskripsi karakter
character_descriptions = {
    "Kitsune": [
        "Fire Fox Warrior",
        "Good For:",
        "- High Damage",
        "- Burning Enemy",
        "- 50% DMG Reduct",
        "- Stun and Boost"
    ],
    "Gangster": [
        "Street Fighter",
        "Good For:",
        "- Overall Damage",
        "- Knockback"
    ],
    "Kunoichi": [
        "Shadow Assassin",
        "Good For:",
        "- High Damage",
        "- Stunning",
        "- Heal HP"
    ]
}

# Merge character data
character_frame_counts.update(new_character_frame_counts)
character_damage.update(new_character_damage)
character_ranges.update(new_character_ranges)

def load_character_data():
    """Load character data from file"""
    try:
        with open("character_data.json", "r") as f:
            return json.loads(f.read())
    except:
        # Default data
        return {
            "owned_characters": ["Samurai", "Soldier", "Magician"]
        }

def save_character_data(data):
    """Save character data to file"""
    try:
        with open("character_data.json", "w") as f:
            f.write(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error saving character data: {e}")

# Martial Hero frame counts
martial_hero_frame_counts = {
    "Attack_1": 7,
    "Attack_2": 6,
    "Attack_3": 9,
    "Dead": 11,
    "Hurt": 3,
    "Idle": 10,
    "Jump": 3,
    "Run": 8,
    "Shield": 3,
    "Walk": 8
}

# Add to character_frame_counts
character_frame_counts["Martial_Hero"] = martial_hero_frame_counts

# Martial Hero damage values with Hero Cutless effect
character_damage["Martial_Hero"] = {
    "Attack_1": 35,
    "Attack_2": 70, 
    "Attack_3": 105
}

# Martial Hero range
character_ranges["Martial_Hero"] = 120  # Long range

def load_limited_data():
    """Load limited edition shop data"""
    try:
        with open("data/limited_data.json", "r") as f:
            return json.load(f)
    except:
        # Default limited data
        return {
            "last_sunday_purchase": None,
            "last_monday_purchase": None,
            "last_tuesday_purchase": None,
            "last_wednesday_purchase": None,
            "last_thursday_purchase": None,
            "last_friday_purchase": None,
            "last_saturday_purchase": None,
            "last_hour_purchases": {},  # {hour: count}
            "last_resource_purchase": None,
            "hero_knight_purchased": False,
            "hero_knight_spawn_time": None,  # Track when hero knight spawned
            "random_box_purchases": 0,
            "last_random_box_date": None,
            "mega_sale_purchased": False,
            "last_mega_sale_date": None,
            "free_sakura_purchases": 0,  # Track weekly free sakura purchases
            "last_free_sakura_reset": None
        }

def save_limited_data(data):
    """Save limited edition shop data"""
    try:
        with open("data/limited_data.json", "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving limited data: {e}")

def check_mega_sale_available():
    """Check if mega sale should be available (1% chance)"""
    return random.randint(1, 100) == 1

def check_random_box_available():
    """Check if random box should be available (5% chance)"""
    return random.randint(1, 100) <= 5

def check_free_sakura_available():
    """Check if free sakura should be available (10% chance)"""
    return random.randint(1, 100) <= 10

def check_hero_knight_spawn():
    """Check if hero knight should spawn (3% chance)"""
    return random.randint(1, 100) <= 3

def is_time_in_range(current_hour, target_hour, target_minute=0, end_minute=59):
    """Check if current time is in specified range"""
    current_time = datetime.now()
    return (current_time.hour == target_hour and 
            target_minute <= current_time.minute <= end_minute)

def is_valid_limited_time():
    """Check if current time is valid for limited edition items (1 hour duration)"""
    now = datetime.now()
    current_hour = now.hour
    
    # Valid starting hours: 6, 9, 12, 15, 18, 21, 0
    # Each lasts for 1 hour
    valid_ranges = [
        (6, 7),   # 6am-7am
        (9, 10),  # 9am-10am  
        (12, 13), # 12pm-1pm
        (15, 16), # 3pm-4pm
        (18, 19), # 6pm-7pm
        (21, 22), # 9pm-10pm
        (0, 1)    # 12am-1am
    ]
    
    for start_hour, end_hour in valid_ranges:
        if start_hour <= current_hour < end_hour:
            return True
    return False

def get_available_limited_items(limited_data):
    """Get list of available limited edition items based on time and purchase history"""
    now = datetime.now()
    current_date = now.date().isoformat()
    current_hour = now.hour
    current_minute = now.minute
    current_weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    available_items = []
    
    # Daily specials (only appear during valid time windows)
    if is_valid_limited_time():
        # 1. Sunday Special
        if current_weekday == 6:  # Sunday
            last_sunday = limited_data.get("last_sunday_purchase")
            if not last_sunday or last_sunday != current_date:
                available_items.append("Sunday_Special")
        
        # 2. Monday Special
        if current_weekday == 0:  # Monday
            last_monday = limited_data.get("last_monday_purchase")
            if not last_monday or last_monday != current_date:
                available_items.append("Monday_Special")
        
        # 3. Tuesday Special
        if current_weekday == 1:  # Tuesday
            last_tuesday = limited_data.get("last_tuesday_purchase")
            if not last_tuesday or last_tuesday != current_date:
                available_items.append("Tuesday_Special")
        
        # 4. Wednesday Special
        if current_weekday == 2:  # Wednesday
            last_wednesday = limited_data.get("last_wednesday_purchase")
            if not last_wednesday or last_wednesday != current_date:
                available_items.append("Wednesday_Special")
        
        # 5. Thursday Special
        if current_weekday == 3:  # Thursday
            last_thursday = limited_data.get("last_thursday_purchase")
            if not last_thursday or last_thursday != current_date:
                available_items.append("Thursday_Special")
        
        # 6. Friday Special
        if current_weekday == 4:  # Friday
            last_friday = limited_data.get("last_friday_purchase")
            if not last_friday or last_friday != current_date:
                available_items.append("Friday_Special")
        
        # 7. Saturday Special
        if current_weekday == 5:  # Saturday
            last_saturday = limited_data.get("last_saturday_purchase")
            if not last_saturday or last_saturday != current_date:
                available_items.append("Saturday_Special")
        
        # 8. Hourly Deal (during valid time windows)
        hour_key = f"{current_date}_{current_hour}"
        purchases_this_hour = limited_data.get("last_hour_purchases", {}).get(hour_key, 0)
        if purchases_this_hour < 3:
            available_items.append("Hourly_Deal")
        
        # 11. Random Box (5% chance during valid times)
        box_date = limited_data.get("last_random_box_date")
        box_purchases = limited_data.get("random_box_purchases", 0)
        if box_date != current_date:
            box_purchases = 0  # Reset daily counter
        if box_purchases < 5 and check_random_box_available():
            available_items.append("Random_Box")
        
        # 13. Mega Sale (1% chance during valid times)
        last_mega = limited_data.get("last_mega_sale_date")
        mega_purchased = limited_data.get("mega_sale_purchased", False)
        
        week_passed = True
        if last_mega:
            last_date = datetime.fromisoformat(last_mega).date()
            days_diff = (now.date() - last_date).days
            week_passed = days_diff >= 7
        
        if week_passed and not mega_purchased and check_mega_sale_available():
            available_items.append("Mega_Sale")
    
    # 9. Night Resource (ONLY at 10pm sharp, no duration)
    if current_hour == 22:  # 10pm ONLY
        last_resource = limited_data.get("last_resource_purchase")
        if not last_resource or last_resource != current_date:
            available_items.append("Night_Resource")
    
    # 10. Hero Knight (ONLY 3:30-4:00pm, 3% chance)
    if (current_hour == 15 and current_minute >= 30) or (current_hour == 16 and current_minute == 0):
        if not limited_data.get("hero_knight_purchased", False):
            spawn_time = limited_data.get("hero_knight_spawn_time")
            if spawn_time:
                spawn_datetime = datetime.fromisoformat(spawn_time)
                # Check if spawn was today and within valid time
                if (spawn_datetime.date() == now.date() and 
                    spawn_datetime.hour == 15 and spawn_datetime.minute >= 30):
                    available_items.append("Hero_Knight")
            else:
                # Try to spawn hero knight with 3% chance
                if check_hero_knight_spawn():
                    limited_data["hero_knight_spawn_time"] = now.isoformat()
                    available_items.append("Hero_Knight")
    
    # 12. Free Sakura (ONLY 8:00-8:05pm, 10% chance)
    if current_hour == 20 and 0 <= current_minute <= 5:  # 8:00-8:05pm
        last_reset = limited_data.get("last_free_sakura_reset")
        free_purchases = limited_data.get("free_sakura_purchases", 0)
        
        # Reset weekly counter if a week has passed
        if last_reset:
            last_reset_date = datetime.fromisoformat(last_reset).date()
            days_diff = (now.date() - last_reset_date).days
            if days_diff >= 7:
                free_purchases = 0
                limited_data["free_sakura_purchases"] = 0
                limited_data["last_free_sakura_reset"] = now.isoformat()
        elif not last_reset:
            limited_data["last_free_sakura_reset"] = now.isoformat()
        
        if free_purchases < 5 and check_free_sakura_available():
            available_items.append("Free_Sakura")
    
    return available_items

def show_inventory_popup(dungeon_data, summer_data):
    """Display inventory popup with resource icons and amounts"""
    # Create inventory popup surface - much smaller
    popup_width = 220
    popup_height = 160
    popup_surface = pygame.Surface((popup_width, popup_height))
    popup_surface.set_alpha(240)
    popup_surface.fill((30, 30, 50))
    
    # Draw popup border
    pygame.draw.rect(popup_surface, (100, 150, 255), popup_surface.get_rect(), 3)
    
    # Title
    title_text = button_font.render("INVENTORY", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(popup_width // 2, 22))
    popup_surface.blit(title_text, title_rect)
    
    # Load resource icons - smaller size
    icon_size = 24
    icons = {}
    try:
        icons['tengu_feathers'] = pygame.transform.scale(
            pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), 
            (icon_size, icon_size)
        )
    except:
        icons['tengu_feathers'] = None
        
    try:
        icons['sakura'] = pygame.transform.scale(
            pygame.image.load("assets/Drops/sakura.png").convert_alpha(), 
            (icon_size, icon_size)
        )
    except:
        icons['sakura'] = None
        
    try:
        icons['water'] = pygame.transform.scale(
            pygame.image.load("assets/Drops/water.png").convert_alpha(), 
            (icon_size, icon_size)
        )
    except:
        icons['water'] = None
        
    try:
        icons['black_water'] = pygame.transform.scale(
            pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), 
            (icon_size, icon_size)
        )
    except:
        icons['black_water'] = None
    
    # Resource data
    resources = [
        ("tengu_feathers", "Feathers", dungeon_data.get("tengu_feathers", 0)),
        ("sakura", "Sakura", summer_data.get("sakura", 0)),
        ("water", "Water", summer_data.get("water", 0)),
        ("black_water", "B.Water", summer_data.get("black_water", 0))
    ]
    
    # Display resources in 2x2 grid with compact spacing
    start_x = 15
    start_y = 45
    spacing_x = 100
    spacing_y = 40
    
    for i, (resource_key, resource_name, amount) in enumerate(resources):
        row = i // 2
        col = i % 2
        
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y
        
        # Draw icon
        if icons[resource_key]:
            popup_surface.blit(icons[resource_key], (x, y))
        else:
            # Fallback colored square
            color_map = {
                'tengu_feathers': (255, 255, 255),
                'sakura': (255, 182, 193),
                'water': (173, 216, 230),
                'black_water': (64, 64, 64)
            }
            pygame.draw.rect(popup_surface, color_map[resource_key], (x, y, icon_size, icon_size))
        
        # Draw resource name and amount with compact text
        name_text = small_font.render(resource_name, True, (255, 255, 255))
        amount_text = small_font.render(str(amount), True, (255, 255, 0))
        
        popup_surface.blit(name_text, (x + icon_size + 6, y - 2))
        popup_surface.blit(amount_text, (x + icon_size + 6, y + 12))
    
    # Position popup in center of screen
    popup_x = (VIRTUAL_W - popup_width) // 2
    popup_y = (VIRTUAL_H - popup_height) // 2
    
    return popup_surface, popup_x, popup_y

def limited_edition_shop():
    """Limited Edition Shop with time-based restrictions"""
    # Load data
    dungeon_data = load_dungeon_data()
    character_data = load_character_data()
    summer_data = load_summer_data()
    limited_data = load_limited_data()
    
    # Load background (reuse shop background)
    try:
        shop_bg = pygame.image.load("assets/shop_bg.png").convert()
        shop_bg = pygame.transform.smoothscale(shop_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        shop_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        shop_bg.fill((40, 20, 60))  # Different color for limited shop
    
    # Load icons for limited shop
    try:
        feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
        feather_icon = pygame.transform.scale(feather_icon, (30, 30))
    except:
        feather_icon = None
        
    try:
        sakura_icon = pygame.image.load("assets/Drops/sakura.png").convert_alpha()
        sakura_icon = pygame.transform.scale(sakura_icon, (30, 30))
    except:
        sakura_icon = None
        
    try:
        water_icon = pygame.image.load("assets/Drops/water.png").convert_alpha()
        water_icon = pygame.transform.scale(water_icon, (30, 30))
    except:
        water_icon = None
        
    try:
        black_water_icon = pygame.image.load("assets/Drops/blackwater.png").convert_alpha()
        black_water_icon = pygame.transform.scale(black_water_icon, (30, 30))
    except:
        black_water_icon = None
    
    # Limited shop items data
    limited_shop_data = {
        "Sunday_Special": {
            "name": "Sunday Special",
            "description": ["100 Tengu Feathers", "Available only on Sunday", "Once per week"],
            "price": 80,
            "currency": "sakura",
            "reward": {"tengu_feathers": 100}
        },
        "Monday_Special": {
            "name": "Monday Deal",
            "description": ["10 Sakura", "Available only on Monday", "Once per week"],
            "price": 10,
            "currency": "tengu_feathers",
            "reward": {"sakura": 10}
        },
        "Tuesday_Special": {
            "name": "Tuesday Exchange",
            "description": ["20 Tengu Feathers", "Choose your currency", "Available only on Tuesday", "Once per week"],
            "price": 20,
            "currency": "choice_resources", # sakura/water/black_water
            "reward": {"tengu_feathers": 20}
        },
        "Wednesday_Special": {
            "name": "Wednesday Resources",
            "description": ["40 Resources", "Choose your resource", "Available only on Wednesday", "Once per week"],
            "price": 40,
            "currency": "tengu_feathers",
            "reward": {"choice_resources": 40}
        },
        "Thursday_Special": {
            "name": "Thursday Bonus",
            "description": ["10 Tengu Feathers", "Great Exchange Rate!", "Available only on Thursday", "Once per week"],
            "price": 3,
            "currency": "sakura",
            "reward": {"tengu_feathers": 10}
        },
        "Friday_Special": {
            "name": "Friday Mega Bundle",
            "description": ["10 of Each Resource!", "10 Sakura + 10 Water", "+ 10 Black Water + 10 Feathers", "Available only on Friday", "Once per week"],
            "price": 1, # 1 of each
            "currency": "all_resources",
            "reward": {"sakura": 10, "water": 10, "black_water": 10, "tengu_feathers": 10}
        },
        "Saturday_Special": {
            "name": "Saturday Bulk",
            "description": ["50 Resources", "Choose your resource", "Available only on Saturday", "Once per week"],
            "price": 50,
            "currency": "tengu_feathers",
            "reward": {"choice_resources": 50}
        },
        "Hourly_Deal": {
            "name": "Hourly Deal", 
            "description": ["50 Tengu Feathers", "Available at specific hours", "Up to 3 times daily"],
            "price": 50,
            "currency": "water",
            "reward": {"tengu_feathers": 50}
        },
        "Night_Resource": {
            "name": "Night Resource",
            "description": ["100 Random Resources", "Available at 10 PM only", "Once per day"],
            "price": 80,
            "currency": "tengu_feathers",
            "reward": {"choice": ["sakura", "water", "black_water"], "amount": 100}
        },
        "Hero_Knight": {
            "name": "Hero Knight",
            "description": ["Legendary Character", "3:30-4:00 PM only", "3% spawn chance", "One time only"],
            "price": 1000,
            "currency": "tengu_feathers",
            "reward": {"character": "Hero_Knight"}
        },
        "Random_Box": {
            "name": "Random Box",
            "description": [
                "Mystery Contents!",
                "Possible rewards:",
                "• Tengu Feathers (50-120)",
                "• Sakura, Water, Black Water (50-120)",
                "• Gangster Character (rare)",
                "• Price: 100",
                "5 purchases per day, 5% spawn chance"
            ],
            "price": 100,
            "currency": "choice",  # Can choose currency
            "reward": {"random": True}
        },
        "Free_Sakura": {
            "name": "FREE Sakura!",
            "description": ["10 Sakura - ABSOLUTELY FREE!", "8:00-8:05 PM only", "10% spawn chance", "5 times per week"],
            "price": 0,
            "currency": "tengu_feathers",
            "reward": {"sakura": 10}
        },
        "Mega_Sale": {
            "name": "MEGA SALE!",
            "description": ["250 Tengu Feathers!", "ULTRA RARE DEAL!", "Once per week only"],
            "price": 10,
            "currency": "sakura", 
            "reward": {"tengu_feathers": 250}
        }
    }
    
    current_page = 0
    available_items = get_available_limited_items(limited_data)
    max_pages = max(0, len(available_items) - 1) if available_items else 0
    
    # UI Elements
    back_button = pygame.Rect(20, 20, 80, 40)
    inventory_button = pygame.Rect(VIRTUAL_W - 100, 70, 80, 40)  # Inventory button below limited edition
    prev_button = pygame.Rect(50, VIRTUAL_H - 80, 100, 50)
    next_button = pygame.Rect(VIRTUAL_W - 150, VIRTUAL_H - 80, 100, 50)
    buy_button = pygame.Rect(VIRTUAL_W//2 - 100, VIRTUAL_H - 140, 200, 60)
    
    # FIXED: Currency selection buttons with proper spacing - positioned globally
    base_y = VIRTUAL_H - 220  # Higher position to avoid overlap
    currency_buttons = {
        "tengu_feathers": pygame.Rect(VIRTUAL_W//2 - 200, base_y, 80, 50),
        "sakura": pygame.Rect(VIRTUAL_W//2 - 100, base_y, 80, 50), 
        "water": pygame.Rect(VIRTUAL_W//2, base_y, 80, 50),
        "black_water": pygame.Rect(VIRTUAL_W//2 + 100, base_y, 80, 50)
    }
    
    # FIXED: Resource selection buttons with proper spacing
    resource_buttons = {
        "sakura": pygame.Rect(VIRTUAL_W//2 - 150, base_y, 80, 50),
        "water": pygame.Rect(VIRTUAL_W//2 - 50, base_y, 80, 50),
        "black_water": pygame.Rect(VIRTUAL_W//2 + 50, base_y, 80, 50)
    }
    
    selected_currency = "tengu_feathers"
    selected_resource = "sakura"  # For resource selection items
    
    purchase_message = ""
    message_timer = 0
    show_inventory = False  # Flag to show/hide inventory popup
    
    while True:
        current_time = pygame.time.get_ticks()
        
        # Refresh available items periodically
        if current_time % 60000 < 100:
            available_items = get_available_limited_items(limited_data)
            max_pages = max(0, len(available_items) - 1) if available_items else 0
            if current_page > max_pages:
                current_page = max_pages
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                elif inventory_button.collidepoint((vmx, vmy)):
                    show_inventory = not show_inventory  # Toggle inventory popup
                elif prev_button.collidepoint((vmx, vmy)) and current_page > 0:
                    current_page -= 1
                elif next_button.collidepoint((vmx, vmy)) and current_page < max_pages:
                    current_page += 1
                elif buy_button.collidepoint((vmx, vmy)) and available_items:
                    # Purchase logic
                    current_item = available_items[current_page]
                    item_data = limited_shop_data[current_item]
                    success = False
                    
                    # Check if player can afford
                    can_afford = False
                    
                    if item_data["currency"] == "choice":  # Random Box
                        if selected_currency == "tengu_feathers":
                            can_afford = dungeon_data["tengu_feathers"] >= item_data["price"]
                        elif selected_currency == "sakura":
                            can_afford = summer_data["sakura"] >= item_data["price"]
                        elif selected_currency == "water":
                            can_afford = summer_data["water"] >= item_data["price"]
                        elif selected_currency == "black_water":
                            can_afford = summer_data["black_water"] >= item_data["price"]
                    elif item_data["currency"] == "choice_resources":  # Tuesday special
                        if selected_currency == "sakura":
                            can_afford = summer_data["sakura"] >= item_data["price"]
                        elif selected_currency == "water":
                            can_afford = summer_data["water"] >= item_data["price"]
                        elif selected_currency == "black_water":
                            can_afford = summer_data["black_water"] >= item_data["price"]
                    elif item_data["currency"] == "all_resources":  # Friday special
                        can_afford = (summer_data["sakura"] >= 1 and 
                                    summer_data["water"] >= 1 and 
                                    summer_data["black_water"] >= 1 and 
                                    dungeon_data["tengu_feathers"] >= 1)
                    else:
                        currency = item_data["currency"]
                        if currency == "tengu_feathers":
                            can_afford = dungeon_data["tengu_feathers"] >= item_data["price"]
                        elif currency == "sakura":
                            can_afford = summer_data["sakura"] >= item_data["price"]
                        elif currency == "water":
                            can_afford = summer_data["water"] >= item_data["price"]
                        elif currency == "black_water":
                            can_afford = summer_data["black_water"] >= item_data["price"]
                    
                    if can_afford:
                        # Deduct cost
                        if item_data["currency"] == "choice":  # Random Box
                            if selected_currency == "tengu_feathers":
                                dungeon_data["tengu_feathers"] -= item_data["price"]
                            elif selected_currency == "sakura":
                                summer_data["sakura"] -= item_data["price"]
                            elif selected_currency == "water":
                                summer_data["water"] -= item_data["price"]
                            elif selected_currency == "black_water":
                                summer_data["black_water"] -= item_data["price"]
                        elif item_data["currency"] == "choice_resources":  # Tuesday special
                            if selected_currency == "sakura":
                                summer_data["sakura"] -= item_data["price"]
                            elif selected_currency == "water":
                                summer_data["water"] -= item_data["price"]
                            elif selected_currency == "black_water":
                                summer_data["black_water"] -= item_data["price"]
                        elif item_data["currency"] == "all_resources":  # Friday special
                            summer_data["sakura"] -= 1
                            summer_data["water"] -= 1
                            summer_data["black_water"] -= 1
                            dungeon_data["tengu_feathers"] -= 1
                        else:
                            currency = item_data["currency"]
                            if currency == "tengu_feathers":
                                dungeon_data["tengu_feathers"] -= item_data["price"]
                            elif currency == "sakura":
                                summer_data["sakura"] -= item_data["price"]
                            elif currency == "water":
                                summer_data["water"] -= item_data["price"]
                            elif currency == "black_water":
                                summer_data["black_water"] -= item_data["price"]
                        
                        # Give rewards and update purchase tracking
                        now = datetime.now()
                        current_date = now.date().isoformat()
                        
                        if current_item == "Sunday_Special":
                            dungeon_data["tengu_feathers"] += item_data["reward"]["tengu_feathers"]
                            limited_data["last_sunday_purchase"] = current_date
                            purchase_message = "Sunday Special Purchased!"
                            
                        elif current_item == "Monday_Special":
                            summer_data["sakura"] += item_data["reward"]["sakura"]
                            limited_data["last_monday_purchase"] = current_date
                            purchase_message = "Monday Deal Purchased!"
                            
                        elif current_item == "Tuesday_Special":
                            dungeon_data["tengu_feathers"] += item_data["reward"]["tengu_feathers"]
                            limited_data["last_tuesday_purchase"] = current_date
                            purchase_message = "Tuesday Exchange Completed!"
                            
                        elif current_item == "Wednesday_Special":
                            summer_data[selected_resource] += item_data["reward"]["choice_resources"]
                            limited_data["last_wednesday_purchase"] = current_date
                            purchase_message = f"Wednesday Resources: +{item_data['reward']['choice_resources']} {selected_resource}!"
                            
                        elif current_item == "Thursday_Special":
                            dungeon_data["tengu_feathers"] += item_data["reward"]["tengu_feathers"]
                            limited_data["last_thursday_purchase"] = current_date
                            purchase_message = "Thursday Bonus Claimed!"
                            
                        elif current_item == "Friday_Special":
                            summer_data["sakura"] += item_data["reward"]["sakura"]
                            summer_data["water"] += item_data["reward"]["water"]
                            summer_data["black_water"] += item_data["reward"]["black_water"]
                            dungeon_data["tengu_feathers"] += item_data["reward"]["tengu_feathers"]
                            limited_data["last_friday_purchase"] = current_date
                            purchase_message = "Friday Mega Bundle Claimed!"
                            
                        elif current_item == "Saturday_Special":
                            summer_data[selected_resource] += item_data["reward"]["choice_resources"]
                            limited_data["last_saturday_purchase"] = current_date
                            purchase_message = f"Saturday Bulk: +{item_data['reward']['choice_resources']} {selected_resource}!"
                            
                        elif current_item == "Hourly_Deal":
                            dungeon_data["tengu_feathers"] += item_data["reward"]["tengu_feathers"]
                            hour_key = f"{current_date}_{now.hour}"
                            if "last_hour_purchases" not in limited_data:
                                limited_data["last_hour_purchases"] = {}
                            limited_data["last_hour_purchases"][hour_key] = limited_data["last_hour_purchases"].get(hour_key, 0) + 1
                            purchase_message = "Hourly Deal Purchased!"
                            
                        elif current_item == "Night_Resource":
                            summer_data[selected_resource] += item_data["reward"]["amount"]
                            limited_data["last_resource_purchase"] = current_date
                            purchase_message = f"Night Resource Purchased! (+{item_data['reward']['amount']} {selected_resource})"
                            
                        elif current_item == "Hero_Knight":
                            character_data["owned_characters"].append("Hero_Knight")
                            limited_data["hero_knight_purchased"] = True
                            purchase_message = "Hero Knight Obtained!"
                            
                        elif current_item == "Random_Box":
                            # Random box logic
                            rand = random.randint(1, 100)
                            if rand <= 10:  # 10% Gangster
                                if "Gangster" not in character_data["owned_characters"]:
                                    character_data["owned_characters"].append("Gangster")
                                    purchase_message = "Random Box: Gangster Character!"
                                else:
                                    purchase_message = "Random Box: Gangster (Already Owned)"
                            elif rand <= 40:  # 30% resources (40-10=30)
                                resource_types = ["tengu_feathers", "sakura", "water", "black_water"]
                                resource_type = random.choice(resource_types)
                                amount = random.randint(50, 120)
                                
                                if resource_type == "tengu_feathers":
                                    dungeon_data["tengu_feathers"] += amount
                                else:
                                    summer_data[resource_type] += amount
                                    
                                purchase_message = f"Random Box: +{amount} {resource_type}!"
                            else:  # 60% Zonk
                                purchase_message = "Random Box: Zonk! Better luck next time!"
                            
                            limited_data["random_box_purchases"] = limited_data.get("random_box_purchases", 0) + 1
                            limited_data["last_random_box_date"] = current_date
                            
                        elif current_item == "Free_Sakura":
                            summer_data["sakura"] += item_data["reward"]["sakura"]
                            limited_data["free_sakura_purchases"] = limited_data.get("free_sakura_purchases", 0) + 1
                            purchase_message = "FREE Sakura Claimed!"
                            
                        elif current_item == "Mega_Sale":
                            dungeon_data["tengu_feathers"] += item_data["reward"]["tengu_feathers"]
                            limited_data["mega_sale_purchased"] = True
                            limited_data["last_mega_sale_date"] = now.isoformat()
                            purchase_message = "MEGA SALE SUCCESS! +250 Feathers!"
                        
                        # Save all data
                        save_dungeon_data(dungeon_data)
                        save_character_data(character_data)
                        save_summer_data(summer_data)
                        save_limited_data(limited_data)
                        
                        message_timer = current_time
                        available_items = get_available_limited_items(limited_data)
                        max_pages = max(0, len(available_items) - 1) if available_items else 0
                        if current_page > max_pages:
                            current_page = max_pages
                            
                    else:
                        purchase_message = "Not enough currency!"
                        message_timer = current_time
                
                # FIXED: Currency selection button clicks with proper handling
                if available_items:
                    current_item = available_items[current_page]
                    item_data = limited_shop_data[current_item]
                    
                    # Handle Random Box currency selection (4 buttons)
                    if item_data["currency"] == "choice":  # Random Box
                        for curr_key, button in currency_buttons.items():
                            if button.collidepoint((vmx, vmy)):
                                selected_currency = curr_key
                    
                    # Handle Tuesday Special currency selection (3 resource buttons)
                    elif item_data["currency"] == "choice_resources":  # Tuesday special
                        for resource, button in resource_buttons.items():
                            if button.collidepoint((vmx, vmy)):
                                selected_currency = resource
                    
                    # Handle resource selection for Wednesday/Saturday/Night Resource (3 buttons)
                    elif current_item in ["Night_Resource", "Wednesday_Special", "Saturday_Special"]:
                        for resource, button in resource_buttons.items():
                            if button.collidepoint((vmx, vmy)):
                                selected_resource = resource
        
        # Draw background
        virtual_surface.blit(shop_bg, (0, 0))
        
        # Draw title
        title_text = title_font.render("LIMITED EDITION", True, (255, 215, 0))  # Gold color
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
        
        # Draw current time
        now = datetime.now()
        time_text = small_font.render(f"Current Time: {now.strftime('%H:%M:%S')} - {now.strftime('%A')}", True, WHITE)
        virtual_surface.blit(time_text, (20, 80))
        
        if not available_items:
            # No items available
            no_items_text = button_font.render("No Limited Items Available", True, (255, 100, 100))
            virtual_surface.blit(no_items_text, no_items_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))
            
            info_text = small_font.render("Check back later for special deals!", True, WHITE)
            virtual_surface.blit(info_text, info_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2 + 40)))
        else:
            # Draw current item
            current_item = available_items[current_page]
            item_data = limited_shop_data[current_item]
            
            item_rect = pygame.Rect(VIRTUAL_W//2 - 250, 120, 500, 280)  # Made shorter to accommodate buttons
            
            # Special colors for special items
            if current_item == "Mega_Sale":
                pygame.draw.rect(virtual_surface, (100, 20, 100), item_rect, border_radius=15)  # Purple for mega sale
                pygame.draw.rect(virtual_surface, (255, 215, 0), item_rect, 3, border_radius=15)  # Gold border
            elif current_item == "Free_Sakura":
                pygame.draw.rect(virtual_surface, (20, 100, 20), item_rect, border_radius=15)  # Green for free
                pygame.draw.rect(virtual_surface, (0, 255, 0), item_rect, 3, border_radius=15)  # Bright green border
            else:
                pygame.draw.rect(virtual_surface, (60, 40, 80), item_rect, border_radius=15)
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, item_rect, 3, border_radius=15)
            
            # Item name
            name_color = (255, 215, 0) if current_item == "Mega_Sale" else (0, 255, 0) if current_item == "Free_Sakura" else WHITE
            item_name = title_font.render(item_data["name"], True, name_color)
            virtual_surface.blit(item_name, (item_rect.x + 20, item_rect.y + 20))
            
            # Description - with proper spacing
            desc_y = item_rect.y + 70
            for i, desc_line in enumerate(item_data["description"]):
                desc_text = small_font.render(desc_line, True, WHITE)
                virtual_surface.blit(desc_text, (item_rect.x + 20, desc_y + i * 20))
            
            # Price and currency/resource selection
            price = item_data["price"]
            
            # FIXED: Proper spacing and display for all selection types
            if item_data["currency"] == "choice":  # Random Box - 4 currency buttons
                price_text = button_font.render(f"Price: {price}", True, (255, 255, 0))
                virtual_surface.blit(price_text, (item_rect.x + 20, item_rect.y + 200))
                
                # Draw currency selection label
                currency_label_text = small_font.render("Choose Currency:", True, WHITE)
                virtual_surface.blit(currency_label_text, (VIRTUAL_W//2 - 100, base_y - 30))
                
                # Draw currency selection buttons with proper spacing and icons
                for curr_key, button in currency_buttons.items():
                    color = SELECTED_COLOR if selected_currency == curr_key else BUTTON_COLOR
                    if button.collidepoint((vmx, vmy)):
                        color = HOVER_COLOR
                    
                    pygame.draw.rect(virtual_surface, color, button, border_radius=5)
                    pygame.draw.rect(virtual_surface, WHITE, button, 2, border_radius=5)
                    
                    # Draw icon and text
                    icon_x = button.x + 10
                    icon_y = button.y + 5
                    text_y = button.y + 32
                    
                    if curr_key == "tengu_feathers" and feather_icon:
                        virtual_surface.blit(feather_icon, (icon_x, icon_y))
                        curr_text = small_font.render("Feathers", True, WHITE)
                    elif curr_key == "sakura" and sakura_icon:
                        virtual_surface.blit(sakura_icon, (icon_x, icon_y))
                        curr_text = small_font.render("Sakura", True, WHITE)
                    elif curr_key == "water" and water_icon:
                        virtual_surface.blit(water_icon, (icon_x, icon_y))
                        curr_text = small_font.render("Water", True, WHITE)
                    elif curr_key == "black_water" and black_water_icon:
                        virtual_surface.blit(black_water_icon, (icon_x, icon_y))
                        curr_text = small_font.render("B.Water", True, WHITE)
                    else:
                        # Fallback text if no icon
                        curr_text = small_font.render(curr_key.replace("_", " ").title(), True, WHITE)
                    
                    text_rect = curr_text.get_rect(center=(button.centerx, text_y))
                    virtual_surface.blit(curr_text, text_rect)
            
            elif item_data["currency"] == "choice_resources":  # Tuesday special - 3 resource buttons
                price_text = button_font.render(f"Price: {price}", True, (255, 255, 0))
                virtual_surface.blit(price_text, (item_rect.x + 20, item_rect.y + 200))
                
                # Resource selection label
                resource_text = small_font.render("Choose Currency:", True, WHITE)
                virtual_surface.blit(resource_text, (VIRTUAL_W//2 - 80, base_y - 30))
                
                for resource, button in resource_buttons.items():
                    color = SELECTED_COLOR if selected_currency == resource else BUTTON_COLOR
                    if button.collidepoint((vmx, vmy)):
                        color = HOVER_COLOR
                    
                    pygame.draw.rect(virtual_surface, color, button, border_radius=5)
                    pygame.draw.rect(virtual_surface, WHITE, button, 2, border_radius=5)
                    
                    # Draw icon and text
                    icon_x = button.x + 10
                    icon_y = button.y + 5
                    text_y = button.y + 32
                    
                    if resource == "sakura" and sakura_icon:
                        virtual_surface.blit(sakura_icon, (icon_x, icon_y))
                        res_text = small_font.render("Sakura", True, WHITE)
                    elif resource == "water" and water_icon:
                        virtual_surface.blit(water_icon, (icon_x, icon_y))
                        res_text = small_font.render("Water", True, WHITE)
                    elif resource == "black_water" and black_water_icon:
                        virtual_surface.blit(black_water_icon, (icon_x, icon_y))
                        res_text = small_font.render("B.Water", True, WHITE)
                    else:
                        res_text = small_font.render(resource.replace("_", " ").title(), True, WHITE)
                    
                    text_rect = res_text.get_rect(center=(button.centerx, text_y))
                    virtual_surface.blit(res_text, text_rect)
            
            elif item_data["currency"] == "all_resources":  # Friday special
                price_text = button_font.render(f"Price: 1 of Each Resource", True, (255, 255, 0))
                virtual_surface.blit(price_text, (item_rect.x + 20, item_rect.y + 200))
                
                # Show what player has
                resources_text = small_font.render(f"You have: {summer_data.get('sakura', 0)} Sakura, {summer_data.get('water', 0)} Water, {summer_data.get('black_water', 0)} B.Water, {dungeon_data.get('tengu_feathers', 0)} Feathers", True, WHITE)
                virtual_surface.blit(resources_text, (item_rect.x + 20, item_rect.y + 225))
            
            elif current_item in ["Night_Resource", "Wednesday_Special", "Saturday_Special"]:
                price_text = button_font.render(f"Price: {price} Feathers", True, (255, 255, 0))
                virtual_surface.blit(price_text, (item_rect.x + 20, item_rect.y + 200))
                
                # Resource selection label
                resource_text = small_font.render("Choose Resource Reward:", True, WHITE)
                virtual_surface.blit(resource_text, (VIRTUAL_W//2 - 100, base_y - 30))
                
                for resource, button in resource_buttons.items():
                    color = SELECTED_COLOR if selected_resource == resource else BUTTON_COLOR
                    if button.collidepoint((vmx, vmy)):
                        color = HOVER_COLOR
                    
                    pygame.draw.rect(virtual_surface, color, button, border_radius=5)
                    pygame.draw.rect(virtual_surface, WHITE, button, 2, border_radius=5)
                    
                    # Draw icon and text
                    icon_x = button.x + 10
                    icon_y = button.y + 5
                    text_y = button.y + 32
                    
                    if resource == "sakura" and sakura_icon:
                        virtual_surface.blit(sakura_icon, (icon_x, icon_y))
                        res_text = small_font.render("Sakura", True, WHITE)
                    elif resource == "water" and water_icon:
                        virtual_surface.blit(water_icon, (icon_x, icon_y))
                        res_text = small_font.render("Water", True, WHITE)
                    elif resource == "black_water" and black_water_icon:
                        virtual_surface.blit(black_water_icon, (icon_x, icon_y))
                        res_text = small_font.render("B.Water", True, WHITE)
                    else:
                        res_text = small_font.render(resource.replace("_", " ").title(), True, WHITE)
                    
                    text_rect = res_text.get_rect(center=(button.centerx, text_y))
                    virtual_surface.blit(res_text, text_rect)
            
            else:
                # Fixed price items (Sunday, Monday, Thursday, Hourly, Hero Knight, Free Sakura, Mega Sale)
                currency = item_data["currency"]
                if current_item == "Free_Sakura":
                    price_text = button_font.render(f"Price: FREE!", True, (0, 255, 0))
                else:
                    price_text = button_font.render(f"Price: {price} {currency.replace('_', ' ').title()}", True, (255, 255, 0))
                virtual_surface.blit(price_text, (item_rect.x + 20, item_rect.y + 200))
                
                # Draw currency icon (except for free items)
                if current_item != "Free_Sakura":
                    icon_x = item_rect.x + 20 + price_text.get_width() + 10
                    if currency == "tengu_feathers" and feather_icon:
                        virtual_surface.blit(feather_icon, (icon_x, item_rect.y + 205))
                    elif currency == "sakura" and sakura_icon:
                        virtual_surface.blit(sakura_icon, (icon_x, item_rect.y + 205))
                    elif currency == "water" and water_icon:
                        virtual_surface.blit(water_icon, (icon_x, item_rect.y + 205))
                    elif currency == "black_water" and black_water_icon:
                        virtual_surface.blit(black_water_icon, (icon_x, item_rect.y + 205))
            
            # Page indicator
            if len(available_items) > 1:
                page_text = small_font.render(f"Page {current_page + 1} of {len(available_items)}", True, WHITE)
                virtual_surface.blit(page_text, page_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 50)))
        
        # Draw buttons
        # Back button
        pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        # Inventory button
        inventory_color = HOVER_COLOR if inventory_button.collidepoint((vmx, vmy)) else (100, 150, 255)
        pygame.draw.rect(virtual_surface, inventory_color, inventory_button, border_radius=8)
        inventory_text = small_font.render("Inventory", True, WHITE)
        virtual_surface.blit(inventory_text, inventory_text.get_rect(center=inventory_button.center))
        
        # Navigation buttons
        if available_items and len(available_items) > 1:
            if current_page > 0:
                prev_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, prev_color, prev_button, border_radius=8)
                prev_text = small_font.render("Previous", True, WHITE)
                virtual_surface.blit(prev_text, prev_text.get_rect(center=prev_button.center))
            
            if current_page < max_pages:
                next_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, next_color, next_button, border_radius=8)
                next_text = small_font.render("Next", True, WHITE)
                virtual_surface.blit(next_text, next_text.get_rect(center=next_button.center))
        
        # Buy button
        if available_items:
            buy_color = HOVER_COLOR if buy_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, buy_color, buy_button, border_radius=10)
            buy_text = button_font.render("BUY", True, WHITE)
            virtual_surface.blit(buy_text, buy_text.get_rect(center=buy_button.center))
        
        # Draw purchase message
        if purchase_message and current_time - message_timer < 5000:
            message_color = SELECTED_COLOR if ("Purchased!" in purchase_message or "SUCCESS!" in purchase_message or "Obtained!" in purchase_message or "Claimed!" in purchase_message or "Completed!" in purchase_message) else RED
            msg_text = button_font.render(purchase_message, True, message_color)
            virtual_surface.blit(msg_text, msg_text.get_rect(center=(VIRTUAL_W // 2, 100)))
        
        # Draw inventory popup if toggled
        if show_inventory:
            popup_surface, popup_x, popup_y = show_inventory_popup(dungeon_data, summer_data)
            virtual_surface.blit(popup_surface, (popup_x, popup_y))
        
        draw_scaled_centered()
        clock.tick(60)
        
def shop():
    """Main shop function with items and characters"""
    # Load data
    dungeon_data = load_dungeon_data()
    character_data = load_character_data()
    summer_data = load_summer_data()
    
    # Shop items and characters organized by pages (7 pages total)
    shop_pages = [
        ["Kitsune"],        # Page 1: Kitsune
        ["Gangster"],       # Page 2: Gangster  
        ["Kunoichi"],       # Page 3: Kunoichi
        ["Sakura"],         # Page 4: Sakura
        ["Water"],          # Page 5: Water  
        ["Black_Water"],    # Page 6: Black Water
        ["Martial_Hero"]    # Page 7: Martial Hero
    ]
    
    current_page = 0
    max_pages = len(shop_pages) - 1  # 6 (0-6 = 7 pages total)
    
    # Load shop background
    try:
        shop_bg = pygame.image.load("assets/shop_bg.png").convert()
        shop_bg = pygame.transform.smoothscale(shop_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        shop_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        shop_bg.fill((20, 40, 60))
    
    # Load icons
    try:
        feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
        feather_icon = pygame.transform.scale(feather_icon, (30, 30))
    except:
        feather_icon = None
        
    try:
        sakura_icon = pygame.image.load("assets/Drops/sakura.png").convert_alpha()
        sakura_icon = pygame.transform.scale(sakura_icon, (150, 150))
    except:
        sakura_icon = None
        
    try:
        water_icon = pygame.image.load("assets/Drops/water.png").convert_alpha()
        water_icon = pygame.transform.scale(water_icon, (150, 150))
    except:
        water_icon = None
        
    try:
        black_water_icon = pygame.image.load("assets/Drops/blackwater.png").convert_alpha()
        black_water_icon = pygame.transform.scale(black_water_icon, (150, 150))
    except:
        black_water_icon = None
    
    # Load character previews
    character_previews = {}
    shop_characters = ["Kitsune", "Gangster", "Kunoichi", "Martial_Hero"]
    
    for char in shop_characters:
        try:
            if char == "Martial_Hero":
                frame_count = martial_hero_frame_counts["Idle"]
            else:
                frame_count = new_character_frame_counts[char]["Idle"]
                
            idle_sheet = pygame.image.load(f"assets/{char}/Idle.png").convert_alpha()
            frame_width = idle_sheet.get_width() // frame_count
            preview = idle_sheet.subsurface(pygame.Rect(0, 0, frame_width, idle_sheet.get_height()))
            character_previews[char] = pygame.transform.scale(preview, (150, 150))
        except Exception as e:
            print(f"Error loading preview for {char}: {e}")
            placeholder = pygame.Surface((150, 150))
            placeholder.fill((100, 100, 100))
            character_previews[char] = placeholder
    
    # UI Elements
    back_button = pygame.Rect(20, 20, 80, 40)
    limited_button = pygame.Rect(VIRTUAL_W - 100, 20, 80, 40)  # Limited Edition button
    inventory_button = pygame.Rect(VIRTUAL_W - 100, 70, 80, 40)  # Inventory button below limited edition
    prev_button = pygame.Rect(50, VIRTUAL_H - 80, 100, 50)
    next_button = pygame.Rect(VIRTUAL_W - 150, VIRTUAL_H - 80, 100, 50)
    buy_button = pygame.Rect(VIRTUAL_W//2 - 100, VIRTUAL_H - 140, 200, 60)
    
    purchase_message = ""
    message_timer = 0
    show_inventory = False  # Flag to show/hide inventory popup
    
    # Item/Character data
    shop_data = {
        "Kitsune": {
            "type": "character",
            "price": 40,
            "currency": "tengu_feathers",
            "description": character_descriptions["Kitsune"]
        },
        "Gangster": {
            "type": "character", 
            "price": 30,
            "currency": "tengu_feathers",
            "description": character_descriptions["Gangster"]
        },
        "Kunoichi": {
            "type": "character",
            "price": 60, 
            "currency": "tengu_feathers",
            "description": character_descriptions["Kunoichi"]
        },
        "Sakura": {
            "type": "item",
            "price": 10,
            "currency": "tengu_feathers", 
            "description": ["Sakura Petals", "Used for crafting", "and summer events"]
        },
        "Water": {
            "type": "item",
            "price": 10,
            "currency": "tengu_feathers",
            "description": ["Pure Water", "Used for crafting", "and summer events"]
        },
        "Black_Water": {
            "type": "item", 
            "price": 10,
            "currency": "tengu_feathers",
            "description": ["Black Water", "Used for crafting", "and summer events"]
        },
        "Martial_Hero": {
            "type": "character",
            "price": 750,
            "currency": "tengu_feathers",
            "description": ["Best Character Ever", "1st ranking character", "Hero Cutless Effect", "Stun Chance"]
        }
    }
    
    while True:
        current_time = pygame.time.get_ticks()
        current_item = shop_pages[current_page][0]  # Each page has one item
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                elif limited_button.collidepoint((vmx, vmy)):
                    limited_edition_shop()  # Open Limited Edition shop
                elif inventory_button.collidepoint((vmx, vmy)):
                    show_inventory = not show_inventory  # Toggle inventory popup
                elif prev_button.collidepoint((vmx, vmy)) and current_page > 0:
                    current_page -= 1
                elif next_button.collidepoint((vmx, vmy)) and current_page < max_pages:
                    current_page += 1
                elif buy_button.collidepoint((vmx, vmy)):
                    # Attempt to buy item/character
                    item_data = shop_data[current_item]
                    
                    if item_data["type"] == "character":
                        # Character purchase logic
                        if current_item in character_data["owned_characters"]:
                            purchase_message = "Already Owned!"
                            message_timer = current_time
                        elif dungeon_data["tengu_feathers"] >= item_data["price"]:
                            # Purchase successful
                            dungeon_data["tengu_feathers"] -= item_data["price"]
                            character_data["owned_characters"].append(current_item)
                            
                            if "purchase_history" not in character_data:
                                character_data["purchase_history"] = []
                            character_data["purchase_history"].append({
                                "character": current_item,
                                "price": item_data["price"],
                                "date": datetime.now().isoformat()
                            })
                            
                            save_dungeon_data(dungeon_data)
                            save_character_data(character_data)
                            
                            purchase_message = f"{current_item} Purchased!"
                            message_timer = current_time
                        else:
                            purchase_message = "Not Enough Feathers!"
                            message_timer = current_time
                            
                    elif item_data["type"] == "item":
                        # Item purchase logic
                        if dungeon_data["tengu_feathers"] >= item_data["price"]:
                            # Purchase successful
                            dungeon_data["tengu_feathers"] -= item_data["price"]
                            
                            # Add item to summer data
                            if current_item == "Sakura":
                                summer_data["sakura"] += 1
                            elif current_item == "Water":
                                summer_data["water"] += 1
                            elif current_item == "Black_Water":
                                summer_data["black_water"] += 1
                            
                            save_dungeon_data(dungeon_data)
                            save_summer_data(summer_data)
                            
                            purchase_message = f"{current_item} Purchased!"
                            message_timer = current_time
                        else:
                            purchase_message = "Not Enough Feathers!"
                            message_timer = current_time
        
        # Draw background
        virtual_surface.blit(shop_bg, (0, 0))
        
        # Draw title
        title_text = title_font.render("SHOP", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
        
        # Draw current item/character
        item_rect = pygame.Rect(VIRTUAL_W//2 - 200, 120, 400, 300)
        pygame.draw.rect(virtual_surface, (40, 40, 80), item_rect, border_radius=15)
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, item_rect, 3, border_radius=15)
        
        # Item/Character preview
        preview_rect = (item_rect.centerx - 100, item_rect.centery - 30)
        
        if current_item in character_previews:
            virtual_surface.blit(character_previews[current_item], preview_rect)
        elif current_item == "Sakura" and sakura_icon:
            virtual_surface.blit(sakura_icon, preview_rect)
        elif current_item == "Water" and water_icon:
            virtual_surface.blit(water_icon, preview_rect)
        elif current_item == "Black_Water" and black_water_icon:
            virtual_surface.blit(black_water_icon, preview_rect)
        
        # Item/Character name
        item_name = title_font.render(current_item.replace("_", " "), True, WHITE)
        virtual_surface.blit(item_name, (item_rect.x + 220, item_rect.y + 20))
        
        # Description
        desc_y = item_rect.y + 70
        item_data = shop_data[current_item]
        for i, desc_line in enumerate(item_data["description"]):
            desc_text = small_font.render(desc_line, True, WHITE)
            virtual_surface.blit(desc_text, (item_rect.x + 220, desc_y + i * 25))
        
        # Price with spacing
        price = item_data["price"]
        price_text = button_font.render(f"Price:  {price}", True, (255, 255, 0))
        virtual_surface.blit(price_text, (item_rect.x + 220, item_rect.y + 215))
        if feather_icon:
            virtual_surface.blit(feather_icon, (item_rect.x + 325, item_rect.y + 220))
        
        # Ownership/Stock status
        if item_data["type"] == "character":
            if current_item in character_data["owned_characters"]:
                status_text = button_font.render("OWNED", True, SELECTED_COLOR)
                virtual_surface.blit(status_text, (item_rect.x + 220, item_rect.y + 250))
            else:
                status_text = button_font.render("NOT  OWNED", True, RED)
                virtual_surface.blit(status_text, (item_rect.x + 220, item_rect.y + 250))
        else:
            # For items, show current stock
            if current_item == "Sakura":
                stock = summer_data.get("sakura", 0)
            elif current_item == "Water":
                stock = summer_data.get("water", 0)
            elif current_item == "Black_Water":
                stock = summer_data.get("black_water", 0)
            else:
                stock = 0
                
            stock_text = button_font.render(f"OWNED: {stock}", True, WHITE)
            virtual_surface.blit(stock_text, (item_rect.x + 220, item_rect.y + 250))
        
        # Page indicator (now shows correct 1-7)
        page_text = small_font.render(f"Page {current_page + 1} of {max_pages + 1}", True, WHITE)
        virtual_surface.blit(page_text, page_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 50)))
        
        # Draw buttons
        # Back button
        pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        # Inventory button
        inventory_color = HOVER_COLOR if inventory_button.collidepoint((vmx, vmy)) else (100, 150, 255)
        pygame.draw.rect(virtual_surface, inventory_color, inventory_button, border_radius=8)
        inventory_text = small_font.render("Inventory", True, WHITE)
        virtual_surface.blit(inventory_text, inventory_text.get_rect(center=inventory_button.center))
        
        # Limited Edition button
        limited_color = (255, 215, 0) if limited_button.collidepoint((vmx, vmy)) else (200, 150, 0)
        pygame.draw.rect(virtual_surface, limited_color, limited_button, border_radius=8)
        limited_text = small_font.render("Limited", True, (0, 0, 0))
        virtual_surface.blit(limited_text, limited_text.get_rect(center=limited_button.center))
        
        # Previous button
        if current_page > 0:
            try:
                prev_icon = pygame.image.load("assets/previous.png").convert_alpha()
                prev_icon = pygame.transform.scale(prev_icon, (30, 30))
                prev_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, prev_color, prev_button, border_radius=8)
                virtual_surface.blit(prev_icon, (prev_button.x + 10, prev_button.y + 10))
                prev_text = small_font.render("Prev", True, WHITE)
                virtual_surface.blit(prev_text, (prev_button.x + 50, prev_button.y + 15))
            except:
                prev_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, prev_color, prev_button, border_radius=8)
                prev_text = small_font.render("Previous", True, WHITE)
                virtual_surface.blit(prev_text, prev_text.get_rect(center=prev_button.center))
        
        # Next button
        if current_page < max_pages:
            try:
                next_icon = pygame.image.load("assets/next.png").convert_alpha()
                next_icon = pygame.transform.scale(next_icon, (30, 30))
                next_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, next_color, next_button, border_radius=8)
                next_text = small_font.render("Next", True, WHITE)
                virtual_surface.blit(next_text, (next_button.x + 10, next_button.y + 15))
                virtual_surface.blit(next_icon, (next_button.x + 60, next_button.y + 10))
            except:
                next_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, next_color, next_button, border_radius=8)
                next_text = small_font.render("Next", True, WHITE)
                virtual_surface.blit(next_text, next_text.get_rect(center=next_button.center))
        
        # Buy button
        can_afford = dungeon_data["tengu_feathers"] >= item_data["price"]
        is_character_owned = (item_data["type"] == "character" and current_item in character_data["owned_characters"])
        
        if not is_character_owned:
            buy_color = BUTTON_COLOR if can_afford else (100, 100, 100)
            if can_afford:
                buy_color = HOVER_COLOR if buy_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            
            pygame.draw.rect(virtual_surface, buy_color, buy_button, border_radius=10)
            buy_text = button_font.render("BUY", True, WHITE)
            virtual_surface.blit(buy_text, buy_text.get_rect(center=buy_button.center))
        
        # Draw purchase message below item info
        if purchase_message and current_time - message_timer < 3000:
            message_color = SELECTED_COLOR if "Purchased!" in purchase_message else RED
            msg_text = button_font.render(purchase_message, True, message_color)
            virtual_surface.blit(msg_text, msg_text.get_rect(center=(VIRTUAL_W // 2, item_rect.bottom + 30)))
        
        # Draw inventory popup if toggled
        if show_inventory:
            popup_surface, popup_x, popup_y = show_inventory_popup(dungeon_data, summer_data)
            virtual_surface.blit(popup_surface, (popup_x, popup_y))
        
        draw_scaled_centered()
        clock.tick(60)
        
def character_selection_screen():
    # Musik handling - optimized
    if not pygame.mixer.music.get_busy():
        try:
            pygame.mixer.music.load("assets/characterselectbg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Could not load background music: {e}")
    
    # Load click sound once
    click_sound = None
    try:
        click_sound = pygame.mixer.Sound("soundeffects/click.mp3")
        click_sound.set_volume(0.7)
    except pygame.error as e:
        print(f"Could not load click sound: {e}")
    
    # Load data once
    try:
        character_data = load_character_data()
    except:
        character_data = {"owned_characters": ["Samurai", "Soldier", "Magician"]}
    
    try:
        login_data = load_daily_login_data()
    except:
        login_data = {"last_login": "", "consecutive_days": 0, "claimed_days": []}
        
    yurei_available = is_yurei_available()
    
    try:
        summer_data = load_summer_data()
        vampire_available = summer_data.get("vampire_unlocked", False)
    except:
        vampire_available = False
    
    # Constants - UPDATED WITH NECROMANCER IN PAGE 4
    CHARACTERS_PAGE_1 = ["Samurai", "Soldier", "Magician", "Graffiti"]
    CHARACTERS_PAGE_2 = ["Kitsune", "Gangster", "Kunoichi", "Hero_Knight", "Satyr"]
    CHARACTERS_PAGE_3 = ["Yurei", "Vampire", "Ichigo", "Swordsman"]
    CHARACTERS_PAGE_4 = ["Martial_Hero", "Wizard", "Necromancer"]  # ADDED NECROMANCER
    ALL_CHARACTERS = CHARACTERS_PAGE_1 + CHARACTERS_PAGE_2 + CHARACTERS_PAGE_3 + CHARACTERS_PAGE_4
    
    # Colors
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (70, 130, 180)
    HOVER_BLUE = (100, 150, 255)
    GRAY = (150, 150, 150)
    DARK_GRAY = (100, 100, 100)
    BG_COLOR = (30, 30, 60)
    TITLE_COLOR = (255, 215, 0)  # Static gold color for title
    
    # State variables - UPDATED MAX PAGES
    current_page = 1
    max_pages = 4  # INCREASED TO 4 PAGES
    selected_character = None
    owned_characters = character_data["owned_characters"][:]
    
    # Update owned characters based on availability
    if yurei_available and "Yurei" not in owned_characters:
        owned_characters.append("Yurei")
    elif not yurei_available and "Yurei" in owned_characters:
        owned_characters.remove("Yurei")
    
    if vampire_available and "Vampire" not in owned_characters:
        owned_characters.append("Vampire")
    elif not vampire_available and "Vampire" in owned_characters:
        owned_characters.remove("Vampire")
    
    # STATIC CACHE SYSTEM (NO ANIMATIONS)
    class StaticCache:
        def __init__(self):
            self.static_previews = {}  # Single frame per character
            self.ui_cache = {}
            self.text_cache = {}
            
        def get_preview(self, char):
            return self.static_previews.get(char)
            
        def set_preview(self, char, surface):
            self.static_previews[char] = surface
            
        def get_ui(self, key):
            return self.ui_cache.get(key)
            
        def set_ui(self, key, surface):
            self.ui_cache[key] = surface
            
        def get_text(self, key):
            return self.text_cache.get(key)
            
        def set_text(self, key, surface):
            self.text_cache[key] = surface
    
    cache = StaticCache()
    
    # ULTRA-FAST STATIC LOADING (NO ANIMATIONS)
    def load_static_assets():
        print("🚀 Loading static assets for maximum performance...")
        
        # Load fonts once
        fonts = {
            'small': pygame.font.SysFont("Verdana", 16),
            'button': pygame.font.SysFont("Verdana", 18, bold=True),
            'title': pygame.font.SysFont("Verdana", 32, bold=True),
            'popup': pygame.font.SysFont("Verdana", 20, bold=True)
        }
        
        # Frame counts for getting first idle frame - UPDATED WITH NECROMANCER
        frame_counts_batch = {
            "Hero_Knight": hero_knight_frame_counts,
            "Satyr": satyr_frame_counts,
            "Graffiti": graffiti_frame_counts,
            "Yurei": yurei_frame_counts,
            "Vampire": vampire_frame_counts,
            "Swordsman": swordsman_frame_counts,
            "Martial_Hero": martial_hero_frame_counts,
            "Wizard": wizard_frame_counts,
            "Necromancer": {  # ADDED NECROMANCER FRAME COUNTS
                "Attack_1": 47, "Attack_2": 20, "Attack_3": 47,
                "Dead": 52, "Hurt": 9, "Idle": 50, "Jump": 12,
                "Run": 10, "Shield": 12, "Walk": 10
            },
            "Ichigo": {
                "Attack_1": 4, "Attack_2": 3, "Attack_3": 4,
                "Dead": 3, "Hurt": 3, "Idle": 6, "Jump": 10,
                "Run": 8, "Shield": 2, "Walk": 8
            }
        }
        
        # Load ONLY static preview images (first frame of Idle)
        for char in ALL_CHARACTERS:
            try:
                # Get frame counts
                if char in frame_counts_batch:
                    frame_counts = frame_counts_batch[char]
                elif char in ["Kitsune", "Gangster", "Kunoichi"]:
                    frame_counts = new_character_frame_counts[char]
                else:
                    frame_counts = character_frame_counts[char]
                
                # Load ONLY the first frame of Idle (static preview)
                idle_path = f"assets/{char}/Idle.png"
                idle_sheet = pygame.image.load(idle_path).convert_alpha()
                frame_count = frame_counts["Idle"]
                frame_width = idle_sheet.get_width() // frame_count
                
                # Extract ONLY first frame
                first_frame = idle_sheet.subsurface(pygame.Rect(0, 0, frame_width, idle_sheet.get_height()))
                static_preview = pygame.transform.scale(first_frame, (120, 120)).convert_alpha()
                cache.set_preview(char, static_preview)
                
                print(f"✅ Loaded static preview for {char}")
                
            except Exception as e:
                print(f"⚠️ Error loading {char}: {e}")
                # Create placeholder
                placeholder = pygame.Surface((120, 120), pygame.SRCALPHA)
                placeholder.fill(DARK_GRAY)
                pygame.draw.rect(placeholder, WHITE, placeholder.get_rect(), 2)
                font = pygame.font.SysFont("Arial", 12)
                text = font.render(char, True, WHITE)
                text_rect = text.get_rect(center=(60, 60))
                placeholder.blit(text, text_rect)
                cache.set_preview(char, placeholder)
        
        # Load UI icons (static)
        ui_data = [
            ('lock', "assets/lock.png", (40, 40)),
            ('prev', "assets/previous.png", (30, 30)),
            ('next', "assets/next.png", (30, 30))
        ]
        
        for icon, path, size in ui_data:
            try:
                img = pygame.image.load(path).convert_alpha()
                cache.set_ui(icon, pygame.transform.scale(img, size))
            except:
                # Create fallback icon
                fallback = pygame.Surface(size, pygame.SRCALPHA)
                if icon == 'lock':
                    pygame.draw.rect(fallback, RED, fallback.get_rect(), 3)
                    pygame.draw.line(fallback, RED, (10, 15), (30, 15), 3)
                elif icon == 'prev':
                    pygame.draw.polygon(fallback, WHITE, [(25, 15), (5, 15), (15, 5), (15, 25)])
                elif icon == 'next':
                    pygame.draw.polygon(fallback, WHITE, [(5, 15), (25, 15), (15, 5), (15, 25)])
                cache.set_ui(icon, fallback)
        
        # Pre-render ALL text (static, never changes)
        static_texts = {
            'title': (fonts['title'], "Choose Your Character", TITLE_COLOR),  # STATIC TITLE
            'instruction': (fonts['small'], "Double-click to select character", WHITE),
            'locked_text': (pygame.font.SysFont("Verdana", 14), "LOCKED", RED),
            'esc_text': (pygame.font.SysFont("Verdana", 14), "Press ESC to exit", GRAY)
        }
        
        for key, (font, text, color) in static_texts.items():
            cache.set_text(key, font.render(text, True, color))
        
        # Pre-render page indicators - UPDATED FOR 4 PAGES
        for page in range(1, max_pages + 1):
            cache.set_text(f'page_{page}', fonts['button'].render(f"Page {page}/{max_pages}", True, WHITE))
        
        # Pre-render character status texts - UPDATED WITH NECROMANCER
        status_data = {
            "Hero_Knight": ("BOSS REWARD", (255, 215, 0), 12),
            "Satyr": ("DAILY LOGIN", (255, 165, 0), 12),
            "Graffiti": ("FROM REDEEM", (0, 255, 255), 12),
            "Yurei": ("GACHA", (255, 105, 180), 14),
            "Vampire": ("SUMMER EVENT 2025", (255, 69, 0), 10),
            "Ichigo": ("ENDLESS TOWER REWARD", (255, 215, 0), 12),
            "Swordsman": ("BATTLEPASS LV 5000", (138, 43, 226), 12),
            "Martial_Hero": ("LOCKED", (255, 20, 147), 12),
            "Wizard": ("STORY MILESTONE", (100, 50, 200), 12),
            "Necromancer": ("CHARACTER FUSION", (148, 0, 211), 12)  # ADDED NECROMANCER STATUS
        }
        
        for char, (text, color, size) in status_data.items():
            font = pygame.font.SysFont("Verdana", size)
            cache.set_text(f'status_{char}', font.render(text, True, color))
        
        # Pre-render character names - UPDATED WITH NECROMANCER
        display_names = {
            char: "Hero Knight" if char == "Hero_Knight" 
                  else "Martial Hero" if char == "Martial_Hero"
                  else "Wizard" if char == "Wizard"
                  else "Necromancer" if char == "Necromancer"  # ADDED NECROMANCER
                  else char 
            for char in ALL_CHARACTERS
        }
        
        for char in ALL_CHARACTERS:
            cache.set_text(f'name_{char}_owned', fonts['small'].render(display_names[char], True, WHITE))
            cache.set_text(f'name_{char}_locked', fonts['small'].render(display_names[char], True, GRAY))
            cache.set_text(f'selected_{char}', fonts['button'].render(f"Selected: {display_names[char]}", True, GREEN))
        
        print("✅ Static loading complete! Zero animations for maximum performance!")
    
    # Execute static loading
    load_static_assets()
    
    # Button definitions
    BUTTONS = {
        'prev': pygame.Rect(50, VIRTUAL_H//2 - 30, 60, 60),
        'next': pygame.Rect(VIRTUAL_W - 110, VIRTUAL_H//2 - 30, 60, 60)
    }
    
    # Click tracking for double-click
    click_data = {char: {'count': 0, 'last_time': 0} for char in ALL_CHARACTERS}
    
    # Page character mapping - UPDATED WITH NECROMANCER IN PAGE 4
    PAGE_CHARACTERS = {
        1: CHARACTERS_PAGE_1,
        2: CHARACTERS_PAGE_2,
        3: CHARACTERS_PAGE_3,
        4: CHARACTERS_PAGE_4  # NOW INCLUDES NECROMANCER
    }
    
    # Pre-calculate ALL positions (static, never changes) - UPDATED FOR PAGE 4 WITH 3 CHARACTERS
    def calc_char_positions():
        positions = {}
        
        for page_num, chars in PAGE_CHARACTERS.items():
            page_positions = {}
            start_x, start_y = 100, 200
            
            if page_num == 3:
                # Page 3 layout (2x2 grid)
                for i, char in enumerate(chars):
                    row, col = i // 2, i % 2
                    x = VIRTUAL_W//2 - 125 + col * 250
                    y = start_y + row * 200
                    page_positions[char] = pygame.Rect(x, y, 150, 180)
            elif page_num == 4:
                # Page 4 layout (3 characters in a row) - UPDATED FOR NECROMANCER
                for i, char in enumerate(chars):
                    x = VIRTUAL_W//2 - 225 + i * 225  # Adjusted spacing for 3 characters
                    y = start_y + 50  # Slightly lower
                    page_positions[char] = pygame.Rect(x, y, 150, 180)
            else:
                # Page 1 & 2 layouts
                for i, char in enumerate(chars):
                    if len(chars) == 4:
                        row, col = i // 2, i % 2
                        x = start_x + col * 300
                        y = start_y + row * 200
                    elif len(chars) == 5:
                        if i < 3:
                            x = 150 + i * 200
                            y = start_y
                        else:
                            x = 150 + 100 + (i - 3) * 200
                            y = start_y + 200
                    else:
                        row, col = i // 2, i % 2
                        x = start_x + col * 250 + 50
                        y = start_y + row * 200
                    
                    page_positions[char] = pygame.Rect(x, y, 150, 180)
            
            positions[page_num] = page_positions
        
        return positions
    
    CHARACTER_POSITIONS = calc_char_positions()
    
    # Popup system (minimal)
    popup = {'msg': '', 'start': 0, 'surface': None}
    
    def show_popup(message):
        popup['msg'] = message
        popup['start'] = pygame.time.get_ticks()
        popup['surface'] = None
    
    def draw_popup():
        if not popup['msg']:
            return
        
        elapsed = pygame.time.get_ticks() - popup['start']
        if elapsed > 2500:
            popup['msg'] = ''
            popup['surface'] = None
            return
        
        if not popup['surface']:
            popup_surf = pygame.Surface((400, 80), pygame.SRCALPHA)
            popup_surf.fill((200, 0, 0, 180))
            pygame.draw.rect(popup_surf, WHITE, popup_surf.get_rect(), 2, border_radius=8)
            
            font = pygame.font.SysFont("Verdana", 18, bold=True)
            text_surf = font.render(popup['msg'], True, WHITE)
            text_rect = text_surf.get_rect(center=(200, 40))
            popup_surf.blit(text_surf, text_rect)
            popup['surface'] = popup_surf
        
        popup_x = (VIRTUAL_W - 400) // 2
        popup_y = (VIRTUAL_H - 80) // 2
        virtual_surface.blit(popup['surface'], (popup_x, popup_y))
    
    # STATIC character box rendering (no animations)
    def draw_character_box(char, rect, mouse_pos, is_owned, is_selected):
        mx, my = mouse_pos
        hover = rect.collidepoint((mx, my))
        
        # Determine colors
        if is_selected:
            border_color, bg_color = GREEN, (60, 80, 60)
        elif hover:
            border_color = HOVER_BLUE if is_owned else GRAY
            bg_color = (50, 50, 80) if is_owned else (60, 60, 60)
        else:
            border_color = BLUE if is_owned else DARK_GRAY
            bg_color = (40, 40, 60) if is_owned else (30, 30, 30)
        
        # Draw box
        pygame.draw.rect(virtual_surface, bg_color, rect, border_radius=8)
        pygame.draw.rect(virtual_surface, border_color, rect, 2, border_radius=8)
        
        # Draw static character preview
        char_preview = cache.get_preview(char)
        if char_preview:
            preview_rect = char_preview.get_rect(center=(rect.centerx, rect.y + 70))
            
            if is_owned:
                virtual_surface.blit(char_preview, preview_rect.topleft)
            else:
                # Gray out locked characters
                grayed = char_preview.copy()
                grayed.fill((80, 80, 80), special_flags=pygame.BLEND_MULT)
                virtual_surface.blit(grayed, preview_rect.topleft)
                
                # Lock icon
                lock_icon = cache.get_ui('lock')
                if lock_icon:
                    lock_rect = lock_icon.get_rect(center=(rect.centerx + 35, rect.y + 35))
                    virtual_surface.blit(lock_icon, lock_rect.topleft)
        
        # Draw name
        name_key = f'name_{char}_{"owned" if is_owned else "locked"}'
        name_surf = cache.get_text(name_key)
        if name_surf:
            name_rect = name_surf.get_rect(center=(rect.centerx, rect.y + 160))
            virtual_surface.blit(name_surf, name_rect)
        
        # Draw status for locked characters
        if not is_owned:
            status_surf = cache.get_text(f'status_{char}') or cache.get_text('locked_text')
            if status_surf:
                status_rect = status_surf.get_rect(center=(rect.centerx, rect.y + 140))
                virtual_surface.blit(status_surf, status_rect)
    
    # ESC key handler
    def handle_escape():
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            return None
        return "continue"
    
    # MAIN LOOP - MAXIMUM PERFORMANCE (NO ANIMATIONS)
    print("🚀 Starting ultra-fast static character selection...")
    frame_count = 0
    
    while True:
        frame_count += 1
        current_time = pygame.time.get_ticks()
        
        # Handle ESC key
        exit_result = handle_escape()
        if exit_result is None:
            return None
        
        # Get mouse position (minimal calculation)
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        mouse_pos = (vmx, vmy)
        
        # Handle events (minimal processing)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Navigation
                if BUTTONS['prev'].collidepoint(mouse_pos) and current_page > 1:
                    if click_sound: click_sound.play()
                    current_page -= 1
                    selected_character = None
                elif BUTTONS['next'].collidepoint(mouse_pos) and current_page < max_pages:
                    if click_sound: click_sound.play()
                    current_page += 1
                    selected_character = None
                
                # Character selection
                char_rects = CHARACTER_POSITIONS[current_page]
                for char, rect in char_rects.items():
                    if rect.collidepoint(mouse_pos):
                        if click_sound: click_sound.play()
                        
                        if char in owned_characters:
                            # Double-click detection
                            track = click_data[char]
                            time_diff = current_time - track['last_time']
                            
                            if time_diff < 400:
                                track['count'] += 1
                                if track['count'] >= 2:
                                    return char  # INSTANT RETURN
                            else:
                                track['count'] = 1
                            
                            track['last_time'] = current_time
                            selected_character = char
                        else:
                            # Show popup - UPDATED WITH NECROMANCER
                            popup_msgs = {
                                "Hero_Knight": "Defeat Hero Knight Boss!",
                                "Satyr": "Daily Login Day 30!",
                                "Graffiti": "From Redeem!",
                                "Yurei": "Get it by gacha!",
                                "Vampire": "Summer Event 2025!",
                                "Ichigo": "Endless Tower Reward!",
                                "Swordsman": "Battlepass LV 5000!",
                                "Martial_Hero": "Get it from shop!",
                                "Wizard": "Get it by Milestone Rewards from Story Mode!",
                                "Necromancer": "Get it by Character Fusion!"  # ADDED NECROMANCER MESSAGE
                            }
                            show_popup(popup_msgs.get(char, "Buy in Shop!"))
                            selected_character = None
                        break
        
        # Reset click counts (less frequent)
        if frame_count % 120 == 0:
            for char, track in click_data.items():
                if current_time - track['last_time'] > 1500:
                    track['count'] = 0
        
        # STATIC RENDERING (NO ANIMATIONS)
        virtual_surface.fill(BG_COLOR)
        
        # STATIC TITLE (NO BLINKING/RAINBOW)
        title_surf = cache.get_text('title')
        if title_surf:
            title_rect = title_surf.get_rect(center=(VIRTUAL_W // 2, 80))
            virtual_surface.blit(title_surf, title_rect)
        
        # Page indicator (static)
        page_surf = cache.get_text(f'page_{current_page}')
        if page_surf:
            page_rect = page_surf.get_rect(center=(VIRTUAL_W // 2, 120))
            virtual_surface.blit(page_surf, page_rect)
        
        # Instruction (static)
        instruction_surf = cache.get_text('instruction')
        if instruction_surf:
            inst_rect = instruction_surf.get_rect(center=(VIRTUAL_W // 2, 140))
            virtual_surface.blit(instruction_surf, inst_rect)
        
        # Character boxes (static rendering)
        char_rects = CHARACTER_POSITIONS[current_page]
        for char, rect in char_rects.items():
            is_owned = char in owned_characters
            is_selected = (char == selected_character and is_owned)
            draw_character_box(char, rect, mouse_pos, is_owned, is_selected)
        
        # Navigation buttons
        if current_page > 1:
            prev_hover = BUTTONS['prev'].collidepoint(mouse_pos)
            prev_color = HOVER_BLUE if prev_hover else BLUE
            pygame.draw.circle(virtual_surface, prev_color, BUTTONS['prev'].center, 30)
            prev_icon = cache.get_ui('prev')
            if prev_icon:
                icon_rect = prev_icon.get_rect(center=BUTTONS['prev'].center)
                virtual_surface.blit(prev_icon, icon_rect.topleft)
        
        if current_page < max_pages:
            next_hover = BUTTONS['next'].collidepoint(mouse_pos)
            next_color = HOVER_BLUE if next_hover else BLUE
            pygame.draw.circle(virtual_surface, next_color, BUTTONS['next'].center, 30)
            next_icon = cache.get_ui('next')
            if next_icon:
                icon_rect = next_icon.get_rect(center=BUTTONS['next'].center)
                virtual_surface.blit(next_icon, icon_rect.topleft)
        
        # Selected character text
        if selected_character and selected_character in owned_characters:
            selected_surf = cache.get_text(f'selected_{selected_character}')
            if selected_surf:
                sel_rect = selected_surf.get_rect(center=(VIRTUAL_W // 2, 580))
                virtual_surface.blit(selected_surf, sel_rect)
        
        # ESC instruction
        esc_surf = cache.get_text('esc_text')
        if esc_surf:
            esc_rect = esc_surf.get_rect(bottomright=(VIRTUAL_W - 20, VIRTUAL_H - 20))
            virtual_surface.blit(esc_surf, esc_rect)
        
        # Draw popup
        draw_popup()
        
        # Final render
        draw_scaled_centered()
        clock.tick(60)

# Pause menu
def pause_menu():
    overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    overlay.set_alpha(128)
    overlay.fill((0, 0, 0))
    
    buttons = {
        "resume": pygame.Rect(VIRTUAL_W//2 - 100, 180, 200, 60),
        "restart": pygame.Rect(VIRTUAL_W//2 - 100, 260, 200, 60),
        "back": pygame.Rect(VIRTUAL_W//2 - 100, 340, 200, 60)
    }
    
    while True:
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if buttons["resume"].collidepoint((vmx, vmy)):
                    return "resume"
                elif buttons["restart"].collidepoint((vmx, vmy)):
                    return "restart"
                elif buttons["back"].collidepoint((vmx, vmy)):
                    pygame.mixer.music.stop()  # Stop the music when going back
                    return "back"
        
        # Draw overlay
        virtual_surface.blit(overlay, (0, 0))
        
        # Draw pause title
        pause_title = title_font.render("PAUSED", True, WHITE)
        virtual_surface.blit(pause_title, pause_title.get_rect(center=(VIRTUAL_W // 2, 120)))
        
        # Draw buttons
        for button_name, rect in buttons.items():
            color = HOVER_COLOR if rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, color, rect, border_radius=10)
            
            text_map = {"resume": "RESUME", "restart": "RESTART", "back": "BACK TO MENU"}
            text = button_font.render(text_map[button_name], True, WHITE)
            virtual_surface.blit(text, text.get_rect(center=rect.center))
        
        draw_scaled_centered()
        clock.tick(30)

# Game Over screen
def game_over_screen(player_won, player_name):
    overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    
    buttons = {
        "restart": pygame.Rect(VIRTUAL_W//2 - 100, 300, 200, 60),
        "menu": pygame.Rect(VIRTUAL_W//2 - 100, 380, 200, 60)
    }
    
    while True:
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if buttons["restart"].collidepoint((vmx, vmy)):
                    return "restart"
                elif buttons["menu"].collidepoint((vmx, vmy)):
                    return "menu"
        
        # Draw overlay
        virtual_surface.blit(overlay, (0, 0))
        
        # Draw game over title
        if player_won:
            add_battlepass_points()
            title_text = "VICTORY!"
            title_color = SELECTED_COLOR
            subtitle_text = f"Congratulations {player_name}!"
        else:
            title_text = "DEFEAT!"
            title_color = RED
            subtitle_text = f"Better luck next time, {player_name}!"
        
        game_over_title = title_font.render(title_text, True, title_color)
        virtual_surface.blit(game_over_title, game_over_title.get_rect(center=(VIRTUAL_W // 2, 150)))
        
        subtitle = button_font.render(subtitle_text, True, WHITE)
        virtual_surface.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 220)))
        
        # Draw buttons
        for button_name, rect in buttons.items():
            color = HOVER_COLOR if rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, color, rect, border_radius=10)
            
            text_map = {"restart": "PLAY AGAIN", "menu": "MAIN MENU"}
            text = button_font.render(text_map[button_name], True, WHITE)
            virtual_surface.blit(text, text.get_rect(center=rect.center))
        
        draw_scaled_centered()
        clock.tick(30)
    
# Gameplay saat klik tombol PLAY - OPTIMIZED VERSION
def character_screen():
    def draw_button(rect, text):
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=8)
        label = button_font.render(text, True, WHITE)
        virtual_surface.blit(label, label.get_rect(center=rect.center))

    def input_name_screen():
        input_box = pygame.Rect(200, 250, 400, 50)
        color_inactive = pygame.Color('gray')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = False
        user_text = ""
        enter_button = pygame.Rect(300, 320, 200, 50)

        keys = []
        key_w, key_h = 40, 40
        start_x = 140
        start_y = 400
        row_layout = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_idx, row in enumerate(row_layout):
            for col_idx, char in enumerate(row):
                x = start_x + col_idx * (key_w + 5)
                y = start_y + row_idx * (key_h + 5)
                rect = pygame.Rect(x, y, key_w, key_h)
                keys.append((char, rect))

        backspace_rect = pygame.Rect(start_x, start_y + 3 * (key_h + 5), 120, 40)
        enter_rect = pygame.Rect(start_x + 130, start_y + 3 * (key_h + 5), 150, 40)

        while True:
            virtual_surface.fill((30, 30, 60))

            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint((vmx, vmy)):
                        active = True
                        color = color_active
                    else:
                        active = False
                        color = color_inactive

                    for char, rect in keys:
                        if rect.collidepoint((vmx, vmy)):
                            if len(user_text) < 12:
                                user_text += char

                    if backspace_rect.collidepoint((vmx, vmy)):
                        user_text = user_text[:-1]

                    if enter_rect.collidepoint((vmx, vmy)) and user_text.strip():
                        return user_text

            txt_surface = button_font.render(user_text, True, WHITE)
            width = max(400, txt_surface.get_width() + 10)
            input_box.w = width

            pygame.draw.rect(virtual_surface, color, input_box, 2)
            virtual_surface.blit(txt_surface, (input_box.x + 5, input_box.y + 10))

            prompt = title_font.render("Enter Your Name", True, get_rainbow_color())
            virtual_surface.blit(prompt, prompt.get_rect(center=(VIRTUAL_W // 2, 180)))

            for char, rect in keys:
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=5)
                label = button_font.render(char, True, WHITE)
                virtual_surface.blit(label, label.get_rect(center=rect.center))

            pygame.draw.rect(virtual_surface, BUTTON_COLOR, backspace_rect, border_radius=5)
            bksp_text = button_font.render("Backspace", True, WHITE)
            virtual_surface.blit(bksp_text, bksp_text.get_rect(center=backspace_rect.center))

            pygame.draw.rect(virtual_surface, HOVER_COLOR if user_text.strip() else (100, 100, 100), enter_rect, border_radius=5)
            ent_text = button_font.render("Enter", True, WHITE)
            virtual_surface.blit(ent_text, ent_text.get_rect(center=enter_rect.center))

            draw_scaled_centered()
            clock.tick(30)

    # Get player name first
    name = input_name_screen()
    
    # Then character selection
    selected_character = character_selection_screen()
    
    # Game loop
    while True:
        result = gameplay_loop(name, selected_character)
        if result == "back":
            return
        elif result == "restart":
            continue  # Restart the game loop

def gameplay_loop(name, selected_character):
    PLAYER_MAX_HP = 100
    PLAYER_MAX_MP = 100
    hp = PLAYER_MAX_HP
    mp = PLAYER_MAX_MP
    last_mp_regen = pygame.time.get_ticks()
    is_shielding = False
    is_dead = False
    is_hurt = False
    hurt_timer = 0
    death_animation_complete = False
    last_attack_time = 0

    # OPTIMIZATION 1: Pre-load and cache background
    bg = pygame.image.load("assets/gamebg.png").convert()
    bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
    
    # OPTIMIZATION 2: Pre-load all animations at once
    actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
    anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])

    # OPTIMIZATION 3: Reduce frame delays for smoother animation
    frame_delays = {
        "Idle": 120,        # Reduced from 160
        "Run": 100,         # Reduced from 140
        "Jump": 110,        # Reduced from 150
        "Shield": 130,      # Reduced from 170  
        "Attack_1": 90,     # Reduced from 130
        "Attack_2": 95,     # Reduced from 135
        "Attack_3": 90,     # Reduced from 130
        "Dead": 140,        # Reduced from 170
        "Hurt": 120,        # Reduced from 170
        "Walk": 110         # Reduced from 150
    }

    action = "Idle"
    idx, timer = 0, 0
    pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
    vel = [0, 0]
    jumping = False
    jump_count = 2
    holding_shield = False

    # Create enemy
    enemy_characters = ["Samurai", "Soldier", "Magician"]
    available_enemies = [char for char in enemy_characters if char != selected_character]
    enemy_type = random.choice(available_enemies)
    enemy = Enemy(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)

    # OPTIMIZATION 4: Pre-render static UI elements
    def create_static_ui():
        # Pre-render button texts that don't change
        button_texts = {}
        button_texts['left'] = button_font.render("<", True, WHITE)
        button_texts['right'] = button_font.render(">", True, WHITE)
        button_texts['up'] = button_font.render("^", True, WHITE)
        button_texts['down'] = button_font.render("v", True, WHITE)
        button_texts['atk1'] = small_font.render("Atk 1", True, WHITE)
        button_texts['atk2'] = small_font.render("Atk 2", True, WHITE)
        button_texts['atk3'] = small_font.render("Atk 3", True, WHITE)
        button_texts['jump'] = small_font.render("Jump", True, WHITE)
        button_texts['shield'] = small_font.render("Shield", True, WHITE)
        button_texts['run'] = small_font.render("Run", True, WHITE)
        button_texts['shield_indicator'] = small_font.render("SHIELD", True, (0, 255, 255))
        return button_texts

    button_texts = create_static_ui()

    def draw_hud_optimized(name, hp, mp):
        # Use integer calculations for better performance
        hp_width = int(hp * 1.7)
        mp_width = int(mp * 1.7)
        
        # Draw HUD background
        pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 200, 90), border_radius=8)
        
        # HP bar
        pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 170, 10))
        if hp_width > 0:
            pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, hp_width, 10))
        
        # MP bar  
        pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 170, 10))
        if mp_width > 0:
            pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, mp_width, 10))
        
        # Labels - cache these renders
        hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
        virtual_surface.blit(hp_text, (15, 50))
        mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
        virtual_surface.blit(mp_text, (15, 65))
        name_text = small_font.render(name, True, WHITE)
        virtual_surface.blit(name_text, (15, 80))

    def check_collision_and_damage():
        nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
        
        # OPTIMIZATION 6: Reduce collision check frequency
        current_time = pygame.time.get_ticks()
        
        # Check if enemy is attacking and close enough to player
        if enemy.is_attacking():
            distance = abs(enemy.pos[0] - pos[0])
            attack_range = enemy.get_attack_range()
            
            if distance < attack_range:
                # Prevent multiple hits from same attack
                if current_time - enemy.last_attack_time > 600:  # Reduced from 800
                    damage = enemy.get_attack_damage()
                    
                    # Shield blocks 100% damage
                    if is_shielding:
                        damage = 0
                    
                    if damage > 0:
                        hp -= damage
                        enemy.last_attack_time = current_time
                        
                        if hp <= 0:
                            hp = 0
                            is_dead = True
                            action = "Dead"
                            idx = 0
                            timer = 0
                        else:
                            is_hurt = True
                            hurt_timer = current_time
                            action = "Hurt"
                            idx = 0
                            timer = 0
        
        # Check if player is attacking and close enough to enemy
        if "Attack" in action and idx > 0:
            distance = abs(pos[0] - enemy.pos[0])
            player_range = character_ranges[selected_character]
            
            if distance < player_range:
                if current_time - last_attack_time > 400:  # Reduced from 500
                    damage = character_damage[selected_character][action]
                    enemy.take_damage(damage)
                    last_attack_time = current_time

    # OPTIMIZATION 7: Pre-calculate button positions
    size = 60
    spacing = 10
    dir_center_x = 90
    dir_center_y = VIRTUAL_H - 280

    left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
    right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
    up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
    down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

    btn_w, btn_h = 80, 60
    action_y = VIRTUAL_H - btn_h - 10
    labels = ["atk1", "atk2", "atk3", "jump", "shield", "run"]
    action_buttons = {
        name: pygame.Rect(VIRTUAL_W - (btn_w + spacing) * (len(labels) - i), action_y, btn_w, btn_h)
        for i, name in enumerate(labels)
    }

    # Load pause/settings icon
    try:
        settings_icon = pygame.image.load("assets/gamesettings.png").convert_alpha()
        settings_icon = pygame.transform.smoothscale(settings_icon, (40, 40))
    except Exception as e:
        print(f"Error loading gamesettings.png: {e}")
        settings_icon = None

    pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)

    # OPTIMIZATION 8: Cache battle text
    battle_text = small_font.render(f"Battle: {selected_character} vs {enemy_type}", True, WHITE)
    battle_text_rect = (VIRTUAL_W//2 - battle_text.get_width()//2, 10)

    # OPTIMIZATION 9: Increase FPS and reduce some calculations
    target_fps = 90  # Increased from 60 for smoother gameplay
    
    while True:
        dt = clock.tick(target_fps)
        timer += dt
        now = pygame.time.get_ticks()

        # Check for game over conditions
        if is_dead and death_animation_complete:
            result = game_over_screen(False, name)
            if result == "restart":
                return "restart"
            elif result == "menu":
                return "back"
        
        if enemy.is_dead and enemy.death_animation_complete:
            result = game_over_screen(True, name)
            if result == "restart":
                return "restart"
            elif result == "menu":
                return "back"

        # MP regeneration - reduced frequency
        if now - last_mp_regen > 2500:  # Reduced from 3000
            mp = min(PLAYER_MAX_MP, mp + 12)  # Increased from 10
            last_mp_regen = now

        # Handle hurt state - reduced duration
        if is_hurt and now - hurt_timer > 600:  # Reduced from 800
            is_hurt = False
            if not is_dead:
                action = "Idle"
                idx = 0
                timer = 0

        # OPTIMIZATION 10: Batch event processing
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT: 
                exit_game()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "back"
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                mx, my = ((mx - ox) / scale, (my - oy) / scale)

                # Check pause button
                if pause_button.collidepoint((mx, my)):
                    pause_result = pause_menu()
                    if pause_result == "back":
                        return "back"
                    elif pause_result == "restart":
                        return "restart"

                # Don't allow actions if dead or hurt
                if is_dead or is_hurt:
                    continue

                # OPTIMIZATION 11: Faster movement and actions
                if left.collidepoint((mx, my)): 
                    vel[0] = -5; action = "Run"  # Increased from -4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif right.collidepoint((mx, my)): 
                    vel[0] = 5; action = "Run"   # Increased from 4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif up.collidepoint((mx, my)): 
                    vel[1] = -5; action = "Run"  # Increased from -4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif down.collidepoint((mx, my)): 
                    vel[1] = 5; action = "Run"   # Increased from 4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif action_buttons["atk1"].collidepoint((mx, my)):
                    if mp >= 4:  # Reduced from 5
                        action = "Attack_1"; idx = 0; timer = 0; mp -= 4
                        play_sound_effect('Attack_1', selected_character)
                        is_shielding = False
                elif action_buttons["atk2"].collidepoint((mx, my)):
                    if mp >= 6:  # Reduced from 8
                        action = "Attack_2"; idx = 0; timer = 0; mp -= 6
                        play_sound_effect('Attack_2', selected_character)
                        is_shielding = False
                elif action_buttons["atk3"].collidepoint((mx, my)):
                    if mp >= 9:  # Reduced from 12
                        action = "Attack_3"; idx = 0; timer = 0; mp -= 9
                        play_sound_effect('Attack_3', selected_character)
                        is_shielding = False
                elif action_buttons["jump"].collidepoint((mx, my)):
                    if jump_count > 0:
                        vel[1] = -12; action = "Jump"; jumping = True  # Increased from -10
                        play_sound_effect('Jump', selected_character)
                        jump_count -= 1; idx = 0; timer = 0
                        is_shielding = False
                elif action_buttons["shield"].collidepoint((mx, my)):
                    holding_shield = True; action = "Shield"; idx = 0; timer = 0
                    play_sound_effect('Shield', selected_character)
                    is_shielding = True
                elif action_buttons["run"].collidepoint((mx, my)):
                    vel[0] = 8; action = "Run"   # Increased from 6
                    play_sound_effect('Run', selected_character)
                    is_shielding = False

            if e.type == pygame.MOUSEBUTTONUP:
                if not is_dead and not is_hurt:
                    vel = [0, 0]; holding_shield = False; is_shielding = False
                    if not jumping: action = "Idle"

        # Physics update - don't update if dead
        if not is_dead:
            if jumping:
                vel[1] += 0.6  # Increased gravity from 0.5
                pos[1] += vel[1]
                if pos[1] >= VIRTUAL_H - 150:
                    pos[1] = VIRTUAL_H - 150; jumping = False
                    vel[1] = 0; jump_count = 2
                    if not is_hurt:
                        action = "Idle"
            else:
                pos[0] += vel[0]
                pos[1] += vel[1]

            # Screen boundaries
            sprite_width, sprite_height = 160, 160
            left_limit = sprite_width // 2
            right_limit = VIRTUAL_W - sprite_width // 2
            top_limit = 0
            bottom_limit = VIRTUAL_H - sprite_height

            # OPTIMIZATION 12: Simplified boundary checking
            pos[0] = max(left_limit, min(pos[0], right_limit))
            pos[1] = max(top_limit, min(pos[1], bottom_limit))
            
            # Stop at boundaries
            if pos[0] <= left_limit or pos[0] >= right_limit:
                vel[0] = 0
            if pos[1] <= top_limit or pos[1] >= bottom_limit:
                vel[1] = 0

        # Update enemy
        enemy.update(dt, pos)
        
        # Check for combat interactions
        check_collision_and_damage()

        # Update player animation
        delay = frame_delays.get(action, 100)
        if timer >= delay:
            timer = 0
            if anims[action]:
                idx += 1
                if idx >= len(anims[action]):
                    if action == "Dead":
                        death_animation_complete = True
                        idx = len(anims["Dead"]) - 1
                    elif "Attack" in action or action == "Jump":
                        if not is_hurt and not is_dead:
                            action = "Idle"; idx = 0
                    elif action == "Shield" and holding_shield:
                        idx = len(anims["Shield"]) - 1
                    elif action == "Hurt":
                        idx = len(anims["Hurt"]) - 1
                    else:
                        if not is_hurt and not is_dead:
                            action = "Idle"; idx = 0

        # OPTIMIZATION 13: Draw everything with minimal calculations
        virtual_surface.blit(bg, (0, 0))
        
        # Draw player
        if anims[action]:
            idx = min(idx, len(anims[action]) - 1)
            sprite = pygame.transform.scale(anims[action][idx], (160, 160))
            rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
            virtual_surface.blit(sprite, rect.topleft)
            
            # Shield indicator for player
            if is_shielding:
                shield_rect = button_texts['shield_indicator'].get_rect(center=(pos[0], pos[1] - 100))
                virtual_surface.blit(button_texts['shield_indicator'], shield_rect)
        
        # Draw enemy
        enemy.draw(virtual_surface)

        # Draw UI elements only if not dead
        if not is_dead:
            # Movement buttons with pre-rendered text
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, left, border_radius=8)
            virtual_surface.blit(button_texts['left'], button_texts['left'].get_rect(center=left.center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, right, border_radius=8)
            virtual_surface.blit(button_texts['right'], button_texts['right'].get_rect(center=right.center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, up, border_radius=8)
            virtual_surface.blit(button_texts['up'], button_texts['up'].get_rect(center=up.center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, down, border_radius=8)
            virtual_surface.blit(button_texts['down'], button_texts['down'].get_rect(center=down.center))
            
            # Color code attack buttons based on MP
            atk1_color = BUTTON_COLOR if mp >= 4 else (100, 100, 100)
            atk2_color = BUTTON_COLOR if mp >= 6 else (100, 100, 100)
            atk3_color = BUTTON_COLOR if mp >= 9 else (100, 100, 100)
            
            pygame.draw.rect(virtual_surface, atk1_color, action_buttons["atk1"], border_radius=8)
            virtual_surface.blit(button_texts['atk1'], button_texts['atk1'].get_rect(center=action_buttons["atk1"].center))
            
            pygame.draw.rect(virtual_surface, atk2_color, action_buttons["atk2"], border_radius=8)
            virtual_surface.blit(button_texts['atk2'], button_texts['atk2'].get_rect(center=action_buttons["atk2"].center))
            
            pygame.draw.rect(virtual_surface, atk3_color, action_buttons["atk3"], border_radius=8)
            virtual_surface.blit(button_texts['atk3'], button_texts['atk3'].get_rect(center=action_buttons["atk3"].center))
            
            # Other action buttons
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["jump"], border_radius=8)
            virtual_surface.blit(button_texts['jump'], button_texts['jump'].get_rect(center=action_buttons["jump"].center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["shield"], border_radius=8)
            virtual_surface.blit(button_texts['shield'], button_texts['shield'].get_rect(center=action_buttons["shield"].center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["run"], border_radius=8)
            virtual_surface.blit(button_texts['run'], button_texts['run'].get_rect(center=action_buttons["run"].center))

        # Draw pause button with settings icon
        if settings_icon:
            virtual_surface.blit(settings_icon, pause_button.topleft)
        else:
            gear_text = small_font.render("⚙", True, WHITE)
            virtual_surface.blit(gear_text, gear_text.get_rect(center=pause_button.center))

        draw_hud_optimized(name, hp, mp)
        
        # Draw cached battle info
        virtual_surface.blit(battle_text, battle_text_rect)
        
        draw_scaled_centered()

# Gameplay saat klik tombol PLAY - OPTIMIZED VERSION
def character_screen():
    def draw_button(rect, text):
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=8)
        label = button_font.render(text, True, WHITE)
        virtual_surface.blit(label, label.get_rect(center=rect.center))

    def input_name_screen():
        input_box = pygame.Rect(200, 250, 400, 50)
        color_inactive = pygame.Color('gray')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = False
        user_text = ""
        enter_button = pygame.Rect(300, 320, 200, 50)

        keys = []
        key_w, key_h = 40, 40
        start_x = 140
        start_y = 400
        row_layout = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_idx, row in enumerate(row_layout):
            for col_idx, char in enumerate(row):
                x = start_x + col_idx * (key_w + 5)
                y = start_y + row_idx * (key_h + 5)
                rect = pygame.Rect(x, y, key_w, key_h)
                keys.append((char, rect))

        backspace_rect = pygame.Rect(start_x, start_y + 3 * (key_h + 5), 120, 40)
        enter_rect = pygame.Rect(start_x + 130, start_y + 3 * (key_h + 5), 150, 40)

        while True:
            virtual_surface.fill((30, 30, 60))

            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint((vmx, vmy)):
                        active = True
                        color = color_active
                    else:
                        active = False
                        color = color_inactive

                    for char, rect in keys:
                        if rect.collidepoint((vmx, vmy)):
                            if len(user_text) < 12:
                                user_text += char

                    if backspace_rect.collidepoint((vmx, vmy)):
                        user_text = user_text[:-1]

                    if enter_rect.collidepoint((vmx, vmy)) and user_text.strip():
                        return user_text

            txt_surface = button_font.render(user_text, True, WHITE)
            width = max(400, txt_surface.get_width() + 10)
            input_box.w = width

            pygame.draw.rect(virtual_surface, color, input_box, 2)
            virtual_surface.blit(txt_surface, (input_box.x + 5, input_box.y + 10))

            prompt = title_font.render("Enter Your Name", True, get_rainbow_color())
            virtual_surface.blit(prompt, prompt.get_rect(center=(VIRTUAL_W // 2, 180)))

            for char, rect in keys:
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=5)
                label = button_font.render(char, True, WHITE)
                virtual_surface.blit(label, label.get_rect(center=rect.center))

            pygame.draw.rect(virtual_surface, BUTTON_COLOR, backspace_rect, border_radius=5)
            bksp_text = button_font.render("Backspace", True, WHITE)
            virtual_surface.blit(bksp_text, bksp_text.get_rect(center=backspace_rect.center))

            pygame.draw.rect(virtual_surface, HOVER_COLOR if user_text.strip() else (100, 100, 100), enter_rect, border_radius=5)
            ent_text = button_font.render("Enter", True, WHITE)
            virtual_surface.blit(ent_text, ent_text.get_rect(center=enter_rect.center))

            draw_scaled_centered()
            clock.tick(30)

    # Get player name first
    name = input_name_screen()
    
    # Then character selection
    selected_character = character_selection_screen()
    
    # Game loop
    while True:
        result = gameplay_loop(name, selected_character)
        if result == "back":
            return
        elif result == "restart":
            continue  # Restart the game loop

def gameplay_loop(name, selected_character):
    PLAYER_MAX_HP = 100
    PLAYER_MAX_MP = 100
    hp = PLAYER_MAX_HP
    mp = PLAYER_MAX_MP
    last_mp_regen = pygame.time.get_ticks()
    is_shielding = False
    is_dead = False
    is_hurt = False
    hurt_timer = 0
    death_animation_complete = False
    last_attack_time = 0

    # OPTIMIZATION 1: Pre-load and cache background
    bg = pygame.image.load("assets/gamebg.png").convert()
    bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
    
    # OPTIMIZATION 2: Pre-load all animations at once
    actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
    anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])

    # OPTIMIZATION 3: Reduce frame delays for smoother animation
    frame_delays = {
        "Idle": 120,        # Reduced from 160
        "Run": 100,         # Reduced from 140
        "Jump": 110,        # Reduced from 150
        "Shield": 130,      # Reduced from 170  
        "Attack_1": 90,     # Reduced from 130
        "Attack_2": 95,     # Reduced from 135
        "Attack_3": 90,     # Reduced from 130
        "Dead": 140,        # Reduced from 170
        "Hurt": 120,        # Reduced from 170
        "Walk": 110         # Reduced from 150
    }

    action = "Idle"
    idx, timer = 0, 0
    pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
    vel = [0, 0]
    jumping = False
    jump_count = 2
    holding_shield = False

    # Create enemy
    enemy_characters = ["Samurai", "Soldier", "Magician"]
    available_enemies = [char for char in enemy_characters if char != selected_character]
    enemy_type = random.choice(available_enemies)
    enemy = Enemy(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)

    # OPTIMIZATION 4: Pre-render static UI elements
    def create_static_ui():
        # Pre-render button texts that don't change
        button_texts = {}
        button_texts['left'] = button_font.render("<", True, WHITE)
        button_texts['right'] = button_font.render(">", True, WHITE)
        button_texts['up'] = button_font.render("^", True, WHITE)
        button_texts['down'] = button_font.render("v", True, WHITE)
        button_texts['atk1'] = small_font.render("Atk 1", True, WHITE)
        button_texts['atk2'] = small_font.render("Atk 2", True, WHITE)
        button_texts['atk3'] = small_font.render("Atk 3", True, WHITE)
        button_texts['jump'] = small_font.render("Jump", True, WHITE)
        button_texts['shield'] = small_font.render("Shield", True, WHITE)
        button_texts['run'] = small_font.render("Run", True, WHITE)
        button_texts['shield_indicator'] = small_font.render("SHIELD", True, (0, 255, 255))
        return button_texts

    button_texts = create_static_ui()

    # OPTIMIZATION 5: Simplified HUD drawing function
    def draw_hud_optimized(name, hp, mp):
        # Use integer calculations for better performance
        hp_width = int(hp * 1.7)
        mp_width = int(mp * 1.7)
        
        # Draw HUD background
        pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 200, 90), border_radius=8)
        
        # HP bar
        pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 170, 10))
        if hp_width > 0:
            pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, hp_width, 10))
        
        # MP bar  
        pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 170, 10))
        if mp_width > 0:
            pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, mp_width, 10))
        
        # Labels - cache these renders
        hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
        virtual_surface.blit(hp_text, (15, 50))
        mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
        virtual_surface.blit(mp_text, (15, 65))
        name_text = small_font.render(name, True, WHITE)
        virtual_surface.blit(name_text, (15, 80))

    def check_collision_and_damage():
        nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
        
        # OPTIMIZATION 6: Reduce collision check frequency
        current_time = pygame.time.get_ticks()
        
        # Check if enemy is attacking and close enough to player
        if enemy.is_attacking():
            distance = abs(enemy.pos[0] - pos[0])
            attack_range = enemy.get_attack_range()
            
            if distance < attack_range:
                # Prevent multiple hits from same attack
                if current_time - enemy.last_attack_time > 600:  # Reduced from 800
                    damage = enemy.get_attack_damage()
                    
                    # Shield blocks 100% damage
                    if is_shielding:
                        damage = 0
                    
                    if damage > 0:
                        hp -= damage
                        enemy.last_attack_time = current_time
                        
                        if hp <= 0:
                            hp = 0
                            is_dead = True
                            action = "Dead"
                            idx = 0
                            timer = 0
                        else:
                            is_hurt = True
                            hurt_timer = current_time
                            action = "Hurt"
                            idx = 0
                            timer = 0
        
        # Check if player is attacking and close enough to enemy
        if "Attack" in action and idx > 0:
            distance = abs(pos[0] - enemy.pos[0])
            player_range = character_ranges[selected_character]
            
            if distance < player_range:
                if current_time - last_attack_time > 400:  # Reduced from 500
                    damage = character_damage[selected_character][action]
                    enemy.take_damage(damage)
                    last_attack_time = current_time

    # OPTIMIZATION 7: Pre-calculate button positions
    size = 60
    spacing = 10
    dir_center_x = 90
    dir_center_y = VIRTUAL_H - 280

    left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
    right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
    up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
    down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

    btn_w, btn_h = 80, 60
    action_y = VIRTUAL_H - btn_h - 10
    labels = ["atk1", "atk2", "atk3", "jump", "shield", "run"]
    action_buttons = {
        name: pygame.Rect(VIRTUAL_W - (btn_w + spacing) * (len(labels) - i), action_y, btn_w, btn_h)
        for i, name in enumerate(labels)
    }

    # Load pause/settings icon
    try:
        settings_icon = pygame.image.load("assets/gamesettings.png").convert_alpha()
        settings_icon = pygame.transform.smoothscale(settings_icon, (40, 40))
    except Exception as e:
        print(f"Error loading gamesettings.png: {e}")
        settings_icon = None

    pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)

    # OPTIMIZATION 8: Cache battle text
    battle_text = small_font.render(f"Battle: {selected_character} vs {enemy_type}", True, WHITE)
    battle_text_rect = (VIRTUAL_W//2 - battle_text.get_width()//2, 10)

    # OPTIMIZATION 9: Increase FPS and reduce some calculations
    target_fps = 90  # Increased from 60 for smoother gameplay
    
    while True:
        dt = clock.tick(target_fps)
        timer += dt
        now = pygame.time.get_ticks()

        # Check for game over conditions
        if is_dead and death_animation_complete:
            result = game_over_screen(False, name)
            if result == "restart":
                return "restart"
            elif result == "menu":
                return "back"
        
        if enemy.is_dead and enemy.death_animation_complete:
            result = game_over_screen(True, name)
            if result == "restart":
                return "restart"
            elif result == "menu":
                return "back"

        # MP regeneration - reduced frequency
        if now - last_mp_regen > 2500:  # Reduced from 3000
            mp = min(PLAYER_MAX_MP, mp + 12)  # Increased from 10
            last_mp_regen = now

        # Handle hurt state - reduced duration
        if is_hurt and now - hurt_timer > 600:  # Reduced from 800
            is_hurt = False
            if not is_dead:
                action = "Idle"
                idx = 0
                timer = 0

        # OPTIMIZATION 10: Batch event processing
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT: 
                exit_game()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "back"
            if e.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                mx, my = ((mx - ox) / scale, (my - oy) / scale)

                # Check pause button
                if pause_button.collidepoint((mx, my)):
                    pause_result = pause_menu()
                    if pause_result == "back":
                        return "back"
                    elif pause_result == "restart":
                        return "restart"

                # Don't allow actions if dead or hurt
                if is_dead or is_hurt:
                    continue

                # OPTIMIZATION 11: Faster movement and actions
                if left.collidepoint((mx, my)): 
                    vel[0] = -5; action = "Run"  # Increased from -4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif right.collidepoint((mx, my)): 
                    vel[0] = 5; action = "Run"   # Increased from 4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif up.collidepoint((mx, my)): 
                    vel[1] = -5; action = "Run"  # Increased from -4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif down.collidepoint((mx, my)): 
                    vel[1] = 5; action = "Run"   # Increased from 4
                    play_sound_effect('Run', selected_character)
                    is_shielding = False
                elif action_buttons["atk1"].collidepoint((mx, my)):
                    if mp >= 4:  # Reduced from 5
                        action = "Attack_1"; idx = 0; timer = 0; mp -= 4
                        play_sound_effect('Attack_1', selected_character)
                        is_shielding = False
                elif action_buttons["atk2"].collidepoint((mx, my)):
                    if mp >= 6:  # Reduced from 8
                        action = "Attack_2"; idx = 0; timer = 0; mp -= 6
                        play_sound_effect('Attack_2', selected_character)
                        is_shielding = False
                elif action_buttons["atk3"].collidepoint((mx, my)):
                    if mp >= 9:  # Reduced from 12
                        action = "Attack_3"; idx = 0; timer = 0; mp -= 9
                        play_sound_effect('Attack_3', selected_character)
                        is_shielding = False
                elif action_buttons["jump"].collidepoint((mx, my)):
                    if jump_count > 0:
                        vel[1] = -12; action = "Jump"; jumping = True  # Increased from -10
                        play_sound_effect('Jump', selected_character)
                        jump_count -= 1; idx = 0; timer = 0
                        is_shielding = False
                elif action_buttons["shield"].collidepoint((mx, my)):
                    holding_shield = True; action = "Shield"; idx = 0; timer = 0
                    play_sound_effect('Shield', selected_character)
                    is_shielding = True
                elif action_buttons["run"].collidepoint((mx, my)):
                    vel[0] = 8; action = "Run"   # Increased from 6
                    play_sound_effect('Run', selected_character)
                    is_shielding = False

            if e.type == pygame.MOUSEBUTTONUP:
                if not is_dead and not is_hurt:
                    vel = [0, 0]; holding_shield = False; is_shielding = False
                    if not jumping: action = "Idle"

        # Physics update - don't update if dead
        if not is_dead:
            if jumping:
                vel[1] += 0.6  # Increased gravity from 0.5
                pos[1] += vel[1]
                if pos[1] >= VIRTUAL_H - 150:
                    pos[1] = VIRTUAL_H - 150; jumping = False
                    vel[1] = 0; jump_count = 2
                    if not is_hurt:
                        action = "Idle"
            else:
                pos[0] += vel[0]
                pos[1] += vel[1]

            # Screen boundaries
            sprite_width, sprite_height = 160, 160
            left_limit = sprite_width // 2
            right_limit = VIRTUAL_W - sprite_width // 2
            top_limit = 0
            bottom_limit = VIRTUAL_H - sprite_height

            # OPTIMIZATION 12: Simplified boundary checking
            pos[0] = max(left_limit, min(pos[0], right_limit))
            pos[1] = max(top_limit, min(pos[1], bottom_limit))
            
            # Stop at boundaries
            if pos[0] <= left_limit or pos[0] >= right_limit:
                vel[0] = 0
            if pos[1] <= top_limit or pos[1] >= bottom_limit:
                vel[1] = 0

        # Update enemy
        enemy.update(dt, pos)
        
        # Check for combat interactions
        check_collision_and_damage()

        # Update player animation
        delay = frame_delays.get(action, 100)
        if timer >= delay:
            timer = 0
            if anims[action]:
                idx += 1
                if idx >= len(anims[action]):
                    if action == "Dead":
                        death_animation_complete = True
                        idx = len(anims["Dead"]) - 1
                    elif "Attack" in action or action == "Jump":
                        if not is_hurt and not is_dead:
                            action = "Idle"; idx = 0
                    elif action == "Shield" and holding_shield:
                        idx = len(anims["Shield"]) - 1
                    elif action == "Hurt":
                        idx = len(anims["Hurt"]) - 1
                    else:
                        if not is_hurt and not is_dead:
                            action = "Idle"; idx = 0

        # OPTIMIZATION 13: Draw everything with minimal calculations
        virtual_surface.blit(bg, (0, 0))
        
        # Draw player
        if anims[action]:
            idx = min(idx, len(anims[action]) - 1)
            sprite = pygame.transform.scale(anims[action][idx], (160, 160))
            rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
            virtual_surface.blit(sprite, rect.topleft)
            
            # Shield indicator for player
            if is_shielding:
                shield_rect = button_texts['shield_indicator'].get_rect(center=(pos[0], pos[1] - 100))
                virtual_surface.blit(button_texts['shield_indicator'], shield_rect)
        
        # Draw enemy
        enemy.draw(virtual_surface)

        # Draw UI elements only if not dead
        if not is_dead:
            # Movement buttons with pre-rendered text
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, left, border_radius=8)
            virtual_surface.blit(button_texts['left'], button_texts['left'].get_rect(center=left.center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, right, border_radius=8)
            virtual_surface.blit(button_texts['right'], button_texts['right'].get_rect(center=right.center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, up, border_radius=8)
            virtual_surface.blit(button_texts['up'], button_texts['up'].get_rect(center=up.center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, down, border_radius=8)
            virtual_surface.blit(button_texts['down'], button_texts['down'].get_rect(center=down.center))
            
            # Color code attack buttons based on MP
            atk1_color = BUTTON_COLOR if mp >= 4 else (100, 100, 100)
            atk2_color = BUTTON_COLOR if mp >= 6 else (100, 100, 100)
            atk3_color = BUTTON_COLOR if mp >= 9 else (100, 100, 100)
            
            pygame.draw.rect(virtual_surface, atk1_color, action_buttons["atk1"], border_radius=8)
            virtual_surface.blit(button_texts['atk1'], button_texts['atk1'].get_rect(center=action_buttons["atk1"].center))
            
            pygame.draw.rect(virtual_surface, atk2_color, action_buttons["atk2"], border_radius=8)
            virtual_surface.blit(button_texts['atk2'], button_texts['atk2'].get_rect(center=action_buttons["atk2"].center))
            
            pygame.draw.rect(virtual_surface, atk3_color, action_buttons["atk3"], border_radius=8)
            virtual_surface.blit(button_texts['atk3'], button_texts['atk3'].get_rect(center=action_buttons["atk3"].center))
            
            # Other action buttons
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["jump"], border_radius=8)
            virtual_surface.blit(button_texts['jump'], button_texts['jump'].get_rect(center=action_buttons["jump"].center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["shield"], border_radius=8)
            virtual_surface.blit(button_texts['shield'], button_texts['shield'].get_rect(center=action_buttons["shield"].center))
            
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["run"], border_radius=8)
            virtual_surface.blit(button_texts['run'], button_texts['run'].get_rect(center=action_buttons["run"].center))

        # Draw pause button with settings icon
        if settings_icon:
            virtual_surface.blit(settings_icon, pause_button.topleft)
        else:
            gear_text = small_font.render("⚙", True, WHITE)
            virtual_surface.blit(gear_text, gear_text.get_rect(center=pause_button.center))

        draw_hud_optimized(name, hp, mp)
        
        # Draw cached battle info
        virtual_surface.blit(battle_text, battle_text_rect)
        
        draw_scaled_centered()

def draw_hud(name, hp, mp):
    	pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 200, 90), border_radius=8)
    	pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 170, 10))
    	pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, int(hp * 1.7), 10))
    	pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 170, 10))
    	pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, int(mp * 1.7), 10))
    	name_text = small_font.render(name, True, WHITE)
    	virtual_surface.blit(name_text, (15, 50))
                                                        
def training_loop(name, selected_char):
    # Player stats and state
    PLAYER_MAX_HP = 100
    PLAYER_MAX_MP = 100
    hp = PLAYER_MAX_HP
    mp = PLAYER_MAX_MP
    is_shielding = False
    is_dead = False
    is_hurt = False
    last_mp_regen = pygame.time.get_ticks()
    infinite_mode = False
    combo_counter = 0
    last_combo_time = 0
    dummy_active = False
    dummy_character = None
    damage_display = []

    # Load assets
    bg = pygame.image.load("assets/trainingbg.png").convert()
    bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
    actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
    anims = load_animation_frames(selected_char, actions, character_frame_counts[selected_char])

    # Animation timing
    frame_delays = {
        "Idle": 160,
        "Run": 140,
        "Jump": 150,
        "Shield": 170,
        "Attack_1": 130,
        "Attack_2": 135,
        "Attack_3": 130,
        "Dead": 170,
        "Hurt": 170
    }

    # Player state
    action = "Idle"
    idx, timer = 0, 0
    pos = [VIRTUAL_W // 2, VIRTUAL_H - 150]
    vel = [0, 0]
    jumping = False
    jump_count = 2
    last_direction = 0  # 0: idle, -1: left, 1: right
    view_mode = "2D"  # Default view mode

    # Movement controls setup
    size = 60
    spacing = 10
    dir_center_x = 90
    dir_center_y = VIRTUAL_H - 280
    left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
    right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
    up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
    down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

    # Action buttons
    btn_w, btn_h = 80, 60
    action_y = VIRTUAL_H - btn_h - 10
    action_buttons = {
        "atk1": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 6, action_y, btn_w, btn_h),
        "atk2": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 5, action_y, btn_w, btn_h),
        "atk3": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 4, action_y, btn_w, btn_h),
        "jump": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 3, action_y, btn_w, btn_h),
        "shield": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 2, action_y, btn_w, btn_h),
        "run": pygame.Rect(VIRTUAL_W - (btn_w + spacing), action_y, btn_w, btn_h),
    }

    # Training mode buttons
    pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)
    reset_button = pygame.Rect(VIRTUAL_W - 150, 120, 120, 40)
    infinite_toggle = pygame.Rect(VIRTUAL_W - 150, 170, 120, 40)
    dummy_toggle = pygame.Rect(VIRTUAL_W - 150, 220, 120, 40)
    select_button = pygame.Rect(VIRTUAL_W - 150, 270, 120, 40)  # Select button below Dummy

    clock = pygame.time.Clock()
    
    # Define running speed
    run_speed = 12  # Increased running speed

    while True:
        dt = clock.tick(60)
        timer += dt
        now = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

        # Event handling
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                exit_game()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return "back"
            if e.type == pygame.MOUSEBUTTONDOWN:
                # Training controls
                if reset_button.collidepoint((vmx, vmy)):
                    pos = [VIRTUAL_W // 2, VIRTUAL_H - 150]
                    vel = [0, 0]
                    action = "Idle"
                    idx = 0
                if dummy_toggle.collidepoint((vmx, vmy)):
                    dummy_active = not dummy_active
                    if dummy_active:
                        # Spawn dummy in the center of the screen with an offset
                        dummy_character = Enemy(random.choice(["Samurai", "Soldier", "Magician"]), VIRTUAL_W // 2 + 50, VIRTUAL_H // 2)
                if select_button.collidepoint((vmx, vmy)):
                    selected_char = character_selection_screen()
                    anims = load_animation_frames(selected_char, actions, character_frame_counts[selected_char])
                if infinite_toggle.collidepoint((vmx, vmy)):
                    infinite_mode = not infinite_mode
                if pause_button.collidepoint((vmx, vmy)):
                    return "back"

                # Movement controls
                if left.collidepoint((vmx, vmy)): 
                    vel[0] = -run_speed
                    last_direction = -1
                    action = "Run"
                    play_sound_effect("Run", selected_char)
                    is_shielding = False
                elif right.collidepoint((vmx, vmy)): 
                    vel[0] = run_speed
                    last_direction = 1
                    action = "Run"
                    play_sound_effect("Run", selected_char)
                    is_shielding = False
                elif up.collidepoint((vmx, vmy)): 
                    vel[1] = -run_speed
                    action = "Run"
                    play_sound_effect("Run", selected_char)
                    is_shielding = False
                elif down.collidepoint((vmx, vmy)): 
                    vel[1] = run_speed
                    action = "Run"
                    play_sound_effect("Run", selected_char)
                    is_shielding = False
                
                # Action buttons
                elif action_buttons["atk1"].collidepoint((vmx, vmy)):
                    action = "Attack_1"
                    play_sound_effect("Attack_1", selected_char)
                    idx = 0
                    timer = 0
                    if not infinite_mode:
                        mp -= 5
                    if dummy_active and dummy_character:
                        damage = character_damage[selected_char]["Attack_1"]
                        dummy_character.take_damage(damage)
                        damage_display.append((dummy_character.pos[0], dummy_character.pos[1], damage))
                elif action_buttons["atk2"].collidepoint((vmx, vmy)):
                    action = "Attack_2"
                    play_sound_effect("Attack_2", selected_char)
                    idx = 0
                    timer = 0
                    if not infinite_mode:
                        mp -= 8
                    if dummy_active and dummy_character:
                        damage = character_damage[selected_char]["Attack_2"]
                        dummy_character.take_damage(damage)
                        damage_display.append((dummy_character.pos[0], dummy_character.pos[1], damage))
                elif action_buttons["atk3"].collidepoint((vmx, vmy)):
                    action = "Attack_3"
                    play_sound_effect("Attack_3", selected_char)
                    idx = 0
                    timer = 0
                    if not infinite_mode:
                        mp -= 12
                    if dummy_active and dummy_character:
                        damage = character_damage[selected_char]["Attack_3"]
                        dummy_character.take_damage(damage)
                        damage_display.append((dummy_character.pos[0], dummy_character.pos[1], damage))
                elif action_buttons["jump"].collidepoint((vmx, vmy)):
                    if jump_count > 0:
                        vel[1] = -10
                        action = "Jump"
                        play_sound_effect("Jump", selected_char)
                        jumping = True
                        jump_count -= 1
                        idx = 0
                        timer = 0
                        is_shielding = False
                elif action_buttons["shield"].collidepoint((vmx, vmy)):
                    holding_shield = True
                    action = "Shield"
                    play_sound_effect("Shield", selected_char)
                    idx = 0
                    timer = 0
                    is_shielding = True
                elif action_buttons["run"].collidepoint((vmx, vmy)):
                    if last_direction != 0:
                        vel[0] = run_speed * last_direction
                    action = "Run"
                    play_sound_effect("Run", selected_char)
                    is_shielding = False

            if e.type == pygame.MOUSEBUTTONUP:
                if not is_dead and not is_hurt:
                    vel = [0, 0]
                    holding_shield = False
                    is_shielding = False
                    if not jumping:
                        action = "Idle"

        # Physics update
        if not is_dead:
            if jumping:
                vel[1] += 0.5
                pos[1] += vel[1]
                if pos[1] >= VIRTUAL_H - 150:
                    pos[1] = VIRTUAL_H - 150
                    jumping = False
                    vel[1] = 0
                    jump_count = 2
                    if not is_hurt:
                        action = "Idle"
            else:
                pos[0] += vel[0]
                pos[1] += vel[1]

            # Screen bounds
            sprite_width, sprite_height = 160, 160
            left_limit = sprite_width // 2
            right_limit = VIRTUAL_W - sprite_width // 2
            top_limit = 50
            bottom_limit = VIRTUAL_H - sprite_height

            pos[0] = max(left_limit, min(right_limit, pos[0]))
            pos[1] = max(top_limit, min(bottom_limit, pos[1]))

        # MP regeneration
        if now - last_mp_regen > 1000:  # Faster regen in training
            mp = min(PLAYER_MAX_MP, mp + (20 if infinite_mode else 10))
            last_mp_regen = now

        # Animation update
        delay = frame_delays.get(action, 130)
        if timer >= delay:
            timer = 0
            if anims[action]:
                idx += 1
                if idx >= len(anims[action]):
                    if action == "Dead":
                        idx = len(anims["Dead"]) - 1
                    elif "Attack" in action or action == "Jump":
                        action = "Idle"
                        idx = 0
                    else:
                        action = "Idle"
                        idx = 0

        # Drawing
        virtual_surface.blit(bg, (0, 0))
        
        # Draw player
        if anims[action]:
            idx = min(idx, len(anims[action]) - 1)
            sprite = pygame.transform.scale(anims[action][idx], (160, 160))
            virtual_surface.blit(sprite, (pos[0] - 80, pos[1] - 60))

        # Draw dummy if active
        if dummy_active and dummy_character:
            dummy_character.draw(virtual_surface)

            # Draw damage display
            for damage_info in damage_display:
                damage_x, damage_y, damage_value = damage_info
                damage_text = small_font.render(f"{damage_value}", True, (255, 0, 0))
                virtual_surface.blit(damage_text, (damage_x, damage_y - 20))

            # Draw total damage label
            total_damage = sum(d[2] for d in damage_display)
            total_damage_text = small_font.render(f"Total Damage: {total_damage}", True, (255, 255, 255))
            total_damage_rect = total_damage_text.get_rect(center=(dummy_character.pos[0], dummy_character.pos[1] - 40))
            virtual_surface.blit(total_damage_text, total_damage_rect)

        # Draw training UI
        draw_hud(f"{name} (Training)", hp, mp)

        # Draw directional buttons
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, left, border_radius=8)
        left_text = small_font.render("<", True, WHITE)
        virtual_surface.blit(left_text, left_text.get_rect(center=left.center))

        pygame.draw.rect(virtual_surface, BUTTON_COLOR, right, border_radius=8)
        right_text = small_font.render(">", True, WHITE)
        virtual_surface.blit(right_text, right_text.get_rect(center=right.center))

        pygame.draw.rect(virtual_surface, BUTTON_COLOR, up, border_radius=8)
        up_text = small_font.render("^", True, WHITE)
        virtual_surface.blit(up_text, up_text.get_rect(center=up.center))

        pygame.draw.rect(virtual_surface, BUTTON_COLOR, down, border_radius=8)
        down_text = small_font.render("v", True, WHITE)
        virtual_surface.blit(down_text, down_text.get_rect(center=down.center))

        # Draw action buttons
        for action_name, rect in action_buttons.items():
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=8)
            action_text = small_font.render(action_name.upper(), True, WHITE)
            virtual_surface.blit(action_text, action_text.get_rect(center=rect.center))

        # Draw training mode buttons
        pygame.draw.rect(virtual_surface, HOVER_COLOR if reset_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, reset_button, border_radius=8)
        reset_text = small_font.render("RESET", True, WHITE)
        virtual_surface.blit(reset_text, reset_text.get_rect(center=reset_button.center))

        pygame.draw.rect(virtual_surface, HOVER_COLOR if infinite_toggle.collidepoint((vmx, vmy)) else BUTTON_COLOR, infinite_toggle, border_radius=8)
        infinite_text = small_font.render("INFINITE", True, WHITE)
        virtual_surface.blit(infinite_text, infinite_text.get_rect(center=infinite_toggle.center))

        pygame.draw.rect(virtual_surface, HOVER_COLOR if dummy_toggle.collidepoint((vmx, vmy)) else BUTTON_COLOR, dummy_toggle, border_radius=8)
        dummy_text = small_font.render("DUMMY", True, WHITE)
        virtual_surface.blit(dummy_text, dummy_text.get_rect(center=dummy_toggle.center))

        # Draw select button (new button below dummy)
        pygame.draw.rect(virtual_surface, HOVER_COLOR if select_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, select_button, border_radius=8)
        select_text = small_font.render("SELECT", True, WHITE)
        virtual_surface.blit(select_text, select_text.get_rect(center=select_button.center))

        # Draw pause button
        pygame.draw.rect(virtual_surface, HOVER_COLOR if pause_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, pause_button, border_radius=20)
        pause_text = button_font.render("X", True, WHITE)
        virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))

        draw_scaled_centered()

# File untuk menyimpan data daily login
DAILY_LOGIN_FILE = "daily_login_data.json"

# Satyr frame counts
satyr_frame_counts = {
    "Attack_1": 8,
    "Attack_2": 8,
    "Attack_3": 8,
    "Dead": 4,
    "Hurt": 4,
    "Idle": 7,
    "Walk": 12,
    "Run": 12,
    "Jump": 12,
    "Shield": 7
}

character_frame_counts["Satyr"] = satyr_frame_counts

# Update character damage untuk Hero Knight
character_damage["Satyr"] = {"Attack_1": 16, "Attack_2": 16, "Attack_3": 16}
character_ranges["Satyr"] = 90  # Medium range

# Load/Save daily login data
def load_daily_login_data():
    if os.path.exists(DAILY_LOGIN_FILE):
        try:
            with open(DAILY_LOGIN_FILE, 'r') as f:
                data = json.load(f)
                return data
        except:
            pass
    return {
        "current_day": 0,
        "last_login": None,
        "total_feathers_gained": 0,
        "satyr_unlocked": False,
        "completed_cycle": False,
        "claimed_days": []  # Tambahan untuk tracking hari yang sudah diklaim
    }

def save_daily_login_data(data):
    with open(DAILY_LOGIN_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def can_claim_today(last_login_str):
    """Check if player can claim today's reward"""
    if last_login_str is None:
        return True
    
    last_login = datetime.fromisoformat(last_login_str)
    current_time = datetime.now()
    time_diff = current_time - last_login
    
    # Must wait at least 24 hours
    return time_diff >= timedelta(hours=24)

def get_reward_info(day):
    """Get reward information for specific day"""
    if day <= 28:
        return "1 Tengu Feather", 1, None
    elif day == 29:
        return "5 Tengu Feathers", 5, None
    elif day == 30:
        return "Satyr Character", 0, "Satyr"
    else:
        return "Cycle Complete", 0, None

def daily_login_preview_page(login_data):
    """New page showing detailed daily login preview with navigation"""
    current_preview_day = 1
    
    # Load icons
    try:
        feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
        feather_icon = pygame.transform.scale(feather_icon, (80, 80))
    except:
        feather_icon = None
    
    try:
        satyr_icon_sheet = pygame.image.load("assets/Satyr/Idle.png").convert_alpha()
        frame_width = satyr_icon_sheet.get_width() // 7
        satyr_icon = satyr_icon_sheet.subsurface(pygame.Rect(0, 0, frame_width, satyr_icon_sheet.get_height()))
        satyr_icon = pygame.transform.scale(satyr_icon, (120, 120))
    except:
        satyr_icon = None
    
    # Load navigation icons (transparent buttons)
    try:
        prev_icon = pygame.image.load("assets/previous.png").convert_alpha()
        prev_icon = pygame.transform.scale(prev_icon, (40, 40))
    except:
        prev_icon = None
        
    try:
        next_icon = pygame.image.load("assets/next.png").convert_alpha()
        next_icon = pygame.transform.scale(next_icon, (40, 40))
    except:
        next_icon = None
    
    # Load status icons
    try:
        claimed_icon = pygame.image.load("assets/claimed.png").convert_alpha()
        claimed_icon = pygame.transform.scale(claimed_icon, (30, 30))
    except:
        claimed_icon = None
        
    try:
        available_icon = pygame.image.load("assets/available.png").convert_alpha()
        available_icon = pygame.transform.scale(available_icon, (30, 30))
    except:
        available_icon = None
        
    try:
        pending_icon = pygame.image.load("assets/pending.png").convert_alpha()
        pending_icon = pygame.transform.scale(pending_icon, (30, 30))
    except:
        pending_icon = None
    
    # UI buttons - repositioned
    back_button = pygame.Rect(20, 50, 100, 50)  # Moved to left
    prev_button = pygame.Rect(50, VIRTUAL_H//2 - 30, 80, 60)  # Moved more to left
    next_button = pygame.Rect(VIRTUAL_W - 130, VIRTUAL_H//2 - 30, 80, 60)  # Moved more to right
    
    while True:
        virtual_surface.fill((20, 30, 50))
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                
                if prev_button.collidepoint((vmx, vmy)) and current_preview_day > 1:
                    current_preview_day -= 1
                elif next_button.collidepoint((vmx, vmy)) and current_preview_day < 30:
                    current_preview_day += 1
            
            # Handle keyboard navigation
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and current_preview_day > 1:
                    current_preview_day -= 1
                elif event.key == pygame.K_RIGHT and current_preview_day < 30:
                    current_preview_day += 1
        
        # Get current day info
        claimed_days = login_data.get("claimed_days", [])
        is_claimed = current_preview_day in claimed_days
        reward_text, feathers, character = get_reward_info(current_preview_day)
        
        # Draw title
        title_text = title_font.render("Daily Login Calendar", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
        
        # Draw day indicator
        day_text = button_font.render(f"Day {current_preview_day} / 30", True, WHITE)
        virtual_surface.blit(day_text, day_text.get_rect(center=(VIRTUAL_W // 2, 130)))
        
        # Draw status indicator with icons
        current_day = login_data.get("current_day", 0)
        next_day = current_day + 1 if current_day < 30 else 1
        
        if is_claimed:
            status_text = button_font.render("CLAIMED", True, (0, 200, 0))
            status_icon = claimed_icon
        elif current_preview_day == next_day:
            status_text = button_font.render("AVAILABLE TODAY", True, (255, 165, 0))
            status_icon = available_icon
        else:
            status_text = button_font.render("PENDING", True, (200, 100, 100))
            status_icon = pending_icon
        
        # Draw status with icon
        status_y = 160
        if status_icon:
            # Move available today icon more to the left
            if current_preview_day == next_day and not is_claimed:
                icon_rect = status_icon.get_rect(center=(VIRTUAL_W//2 - 110, status_y))
            else:
                icon_rect = status_icon.get_rect(center=(VIRTUAL_W//2 - 80, status_y))
            virtual_surface.blit(status_icon, icon_rect)
        
        text_rect = status_text.get_rect(center=(VIRTUAL_W//2 + 20, status_y))
        virtual_surface.blit(status_text, text_rect)
        
        # Draw main reward display box - adjusted size and position
        reward_box = pygame.Rect(VIRTUAL_W//2 - 250, 200, 500, 250)
        pygame.draw.rect(virtual_surface, (40, 50, 70), reward_box, border_radius=20)
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, reward_box, 4, border_radius=20)
        
        # Draw reward icon
        if character == "Satyr" and satyr_icon:
            icon_rect = satyr_icon.get_rect(center=(reward_box.centerx, reward_box.y + 80))
            virtual_surface.blit(satyr_icon, icon_rect)
            
            # Special effect for Satyr
            satyr_title = button_font.render("SPECIAL REWARD!", True, (255, 215, 0))
            virtual_surface.blit(satyr_title, satyr_title.get_rect(center=(reward_box.centerx, reward_box.y + 30)))
            
        elif feathers > 0 and feather_icon:
            icon_rect = feather_icon.get_rect(center=(reward_box.centerx, reward_box.y + 80))
            virtual_surface.blit(feather_icon, icon_rect)
            
            # Draw feather count
            if feathers > 1:
                count_bg = pygame.Rect(icon_rect.right - 20, icon_rect.top - 10, 40, 30)
                pygame.draw.rect(virtual_surface, (255, 100, 100), count_bg, border_radius=15)
                count_text = button_font.render(f"x{feathers}", True, WHITE)
                virtual_surface.blit(count_text, count_text.get_rect(center=count_bg.center))
        
        # Draw reward name - moved up
        reward_name = title_font.render(reward_text, True, SELECTED_COLOR)
        virtual_surface.blit(reward_name, reward_name.get_rect(center=(reward_box.centerx, reward_box.y + 150)))
        
        # Draw reward description - moved down a bit more but stay within box
        if character == "Satyr":
            desc_lines = [
                "Unlock the Satyr character!",
                "A powerful warrior from abyss"
            ]
            desc_color = (255, 215, 0)
        elif feathers == 5:
            desc_lines = [
                "Special bonus day!",
                "Use for buying characters in shop"
            ]
            desc_color = (100, 200, 255)
        else:
            desc_lines = [
                "Daily login reward",
                "Used for buying characters in shop"
            ]
            desc_color = WHITE
        
        for i, line in enumerate(desc_lines):
            desc_text = small_font.render(line, True, desc_color)
            virtual_surface.blit(desc_text, desc_text.get_rect(center=(reward_box.centerx, reward_box.y + 190 + i * 20)))
        
        # Draw transparent navigation buttons
        if current_preview_day > 1:
            # No background rectangle, just the icon
            if prev_icon:
                icon_rect = prev_icon.get_rect(center=prev_button.center)
                virtual_surface.blit(prev_icon, icon_rect.topleft)
            else:
                prev_text = button_font.render("◀", True, WHITE)
                virtual_surface.blit(prev_text, prev_text.get_rect(center=prev_button.center))
            
            # Draw prev day number
            prev_day_text = small_font.render(f"Day {current_preview_day - 1}", True, WHITE)
            virtual_surface.blit(prev_day_text, prev_day_text.get_rect(center=(prev_button.centerx, prev_button.bottom + 15)))
        
        if current_preview_day < 30:
            # No background rectangle, just the icon
            if next_icon:
                icon_rect = next_icon.get_rect(center=next_button.center)
                virtual_surface.blit(next_icon, icon_rect.topleft)
            else:
                next_text = button_font.render("▶", True, WHITE)
                virtual_surface.blit(next_text, next_text.get_rect(center=next_button.center))
            
            # Draw next day number
            next_day_text = small_font.render(f"Day {current_preview_day + 1}", True, WHITE)
            virtual_surface.blit(next_day_text, next_day_text.get_rect(center=(next_button.centerx, next_button.bottom + 15)))
        
        # Draw progress indicator at bottom
        progress_y = 480
        dot_size = 8
        dot_spacing = 15
        total_width = 30 * dot_spacing
        start_x = VIRTUAL_W//2 - total_width//2
        
        # Draw progress dots (simplified - show every 5th day)
        for day in range(1, 31, 5):
            x = start_x + ((day - 1) // 5) * (dot_spacing * 3)
            
            if day in claimed_days:
                color = (0, 200, 0)
            elif day == current_preview_day:
                color = SELECTED_COLOR
            else:
                color = (100, 100, 100)
            
            pygame.draw.circle(virtual_surface, color, (x, progress_y), dot_size)
            
            # Draw day number below dot
            day_num = small_font.render(str(day), True, color)
            virtual_surface.blit(day_num, day_num.get_rect(center=(x, progress_y + 20)))
        
        # Draw current position indicator
        current_x = start_x + ((current_preview_day - 1) // 5) * (dot_spacing * 3)
        if current_preview_day % 5 != 1:  # Interpolate position for days not divisible by 5
            remainder = (current_preview_day - 1) % 5
            current_x = start_x + ((current_preview_day - 1) // 5) * (dot_spacing * 3) + remainder * (dot_spacing * 3 / 5)
        
        pygame.draw.circle(virtual_surface, SELECTED_COLOR, (int(current_x), progress_y - 20), 6)
        pygame.draw.polygon(virtual_surface, SELECTED_COLOR, [
            (int(current_x), progress_y - 10),
            (int(current_x) - 5, progress_y - 15),
            (int(current_x) + 5, progress_y - 15)
        ])
        
        # Draw back button - moved to left
        pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        # Draw navigation hint - moved up
        hint_text = pygame.font.SysFont("Verdana", 14).render("Use arrow buttons to navigate", True, (150, 150, 150))
        virtual_surface.blit(hint_text, hint_text.get_rect(center=(VIRTUAL_W // 2, 550)))
        
        draw_scaled_centered()
        clock.tick(60)

def daily_login():
    """Daily login system with rewards and preview"""
    # Load daily login data
    login_data = load_daily_login_data() 
    
    # Pastikan claimed_days exist untuk backward compatibility
    if "claimed_days" not in login_data:
        login_data["claimed_days"] = list(range(1, login_data["current_day"] + 1))
        save_daily_login_data(login_data)
    
    # Load dungeon data to add feathers
    dungeon_data = load_dungeon_data()
    
    # Load character data to unlock Satyr
    character_data = load_character_data()
    
    # Check if player can claim today
    can_claim = can_claim_today(login_data["last_login"])
    
    # Load icons
    try:
        feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
        feather_icon = pygame.transform.scale(feather_icon, (50, 50))
    except:
        feather_icon = None
    
    try:
        satyr_icon_sheet = pygame.image.load("assets/Satyr/Idle.png").convert_alpha()
        frame_width = satyr_icon_sheet.get_width() // 7  # 7 frames
        satyr_icon = satyr_icon_sheet.subsurface(pygame.Rect(0, 0, frame_width, satyr_icon_sheet.get_height()))
        satyr_icon = pygame.transform.scale(satyr_icon, (80, 80))
    except:
        satyr_icon = None
    
    # UI elements
    claim_button = pygame.Rect(VIRTUAL_W//2 - 100, 450, 200, 60)
    back_button = pygame.Rect(50, 50, 100, 50)
    preview_button = pygame.Rect(VIRTUAL_W//2 - 80, 520, 160, 40)
    
    reward_claimed = False
    claim_message = ""
    message_timer = 0
    
    # Preview state
    show_preview = False
    
    while True:
        current_time = pygame.time.get_ticks()
        virtual_surface.fill((20, 30, 50))
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                
                if claim_button.collidepoint((vmx, vmy)) and can_claim and not reward_claimed:
                    # Claim reward
                    login_data["current_day"] += 1
                    login_data["last_login"] = datetime.now().isoformat()
                    
                    current_day = login_data["current_day"]
                    
                    # Add current day to claimed days
                    if current_day not in login_data["claimed_days"]:
                        login_data["claimed_days"].append(current_day)
                    
                    reward_text, feathers, character = get_reward_info(current_day)
                    
                    if feathers > 0:
                        dungeon_data["tengu_feathers"] += feathers
                        login_data["total_feathers_gained"] += feathers
                        save_dungeon_data(dungeon_data)
                        claim_message = f"Received {feathers} Tengu Feathers!"
                    
                    if character == "Satyr":
                        if "Satyr" not in character_data["owned_characters"]:
                            character_data["owned_characters"].append("Satyr")
                            save_character_data(character_data)
                        login_data["satyr_unlocked"] = True
                        claim_message = "Satyr Character Unlocked!"
                    
                    if current_day >= 30:
                        login_data["completed_cycle"] = True
                        # Reset for next cycle
                        login_data["current_day"] = 0
                        login_data["claimed_days"] = []
                    
                    save_daily_login_data(login_data)
                    reward_claimed = True
                    message_timer = current_time
                    can_claim = False
            
            # Handle scroll for preview
                if preview_button.collidepoint((vmx, vmy)):
                    daily_login_preview_page(login_data)
        
        # Draw title
        title_text = title_font.render("Daily Login", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
        
        # Draw current day info
        current_day = login_data["current_day"]
        next_day = current_day + 1 if current_day < 30 else 1
        
        day_text = button_font.render(f"Day {next_day}/30", True, WHITE)
        virtual_surface.blit(day_text, day_text.get_rect(center=(VIRTUAL_W // 2, 130)))
        
        # Draw reward preview for next day
        reward_text, feathers, character = get_reward_info(next_day)
        
        # Draw reward box
        reward_box = pygame.Rect(VIRTUAL_W//2 - 200, 160, 400, 120)
        pygame.draw.rect(virtual_surface, (40, 40, 70), reward_box, border_radius=15)
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, reward_box, 3, border_radius=15)
        
        # Draw reward icon and text
        if character == "Satyr" and satyr_icon:
            icon_rect = satyr_icon.get_rect(center=(reward_box.x + 80, reward_box.centery))
            virtual_surface.blit(satyr_icon, icon_rect)
        elif feathers > 0 and feather_icon:
            icon_rect = feather_icon.get_rect(center=(reward_box.x + 80, reward_box.centery))
            virtual_surface.blit(feather_icon, icon_rect)
            if feathers > 1:
                count_text = button_font.render(f"x{feathers}", True, WHITE)
                virtual_surface.blit(count_text, (icon_rect.right + 10, icon_rect.centery - 10))
        
        reward_name = button_font.render(reward_text, True, SELECTED_COLOR)
        virtual_surface.blit(reward_name, (reward_box.x + 150, reward_box.centery - 10))
        
        # Draw status
        if not can_claim and not reward_claimed:
            if login_data["last_login"]:
                last_login = datetime.fromisoformat(login_data["last_login"])
                next_claim = last_login + timedelta(hours=24)
                time_left = next_claim - datetime.now()
                
                if time_left.total_seconds() > 0:
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)
                    status_text = small_font.render(f"Next claim in: {hours_left}h {minutes_left}m", True, RED)
                else:
                    status_text = small_font.render("You can claim now!", True, SELECTED_COLOR)
                    can_claim = True
            else:
                status_text = small_font.render("Ready to claim!", True, SELECTED_COLOR)
        elif reward_claimed:
            status_text = small_font.render("Reward claimed today!", True, SELECTED_COLOR)
        else:
            status_text = small_font.render("Ready to claim!", True, SELECTED_COLOR)
        
        virtual_surface.blit(status_text, status_text.get_rect(center=(VIRTUAL_W // 2, 300)))
        
        # Draw claim button
        if can_claim and not reward_claimed:
            button_color = HOVER_COLOR if claim_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            pygame.draw.rect(virtual_surface, button_color, claim_button, border_radius=10)
            claim_text = button_font.render("CLAIM", True, WHITE)
            virtual_surface.blit(claim_text, claim_text.get_rect(center=claim_button.center))
        else:
            # Disabled button
            pygame.draw.rect(virtual_surface, (100, 100, 100), claim_button, border_radius=10)
            claim_text = button_font.render("CLAIMED" if reward_claimed else "WAIT", True, WHITE)
            virtual_surface.blit(claim_text, claim_text.get_rect(center=claim_button.center))
        
        # Draw preview button
        preview_color = HOVER_COLOR if preview_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, preview_color, preview_button, border_radius=8)
        preview_text = small_font.render("View Calendar", True, WHITE)
        virtual_surface.blit(preview_text, preview_text.get_rect(center=preview_button.center))
        
        # Draw progress bar
        progress_width = 300
        progress_height = 15
        progress_x = VIRTUAL_W//2 - progress_width//2
        progress_y = 330
        
        pygame.draw.rect(virtual_surface, (50, 50, 50), (progress_x, progress_y, progress_width, progress_height), border_radius=8)
        
        progress = min(current_day / 30, 1.0)
        filled_width = int(progress * progress_width)
        pygame.draw.rect(virtual_surface, SELECTED_COLOR, (progress_x, progress_y, filled_width, progress_height), border_radius=8)
        
        progress_text = small_font.render(f"Progress: {current_day}/30", True, WHITE)
        virtual_surface.blit(progress_text, progress_text.get_rect(center=(VIRTUAL_W // 2, progress_y + 25)))
        
        # Draw statistics
        stats_y = 365
        feathers_text = small_font.render(f"Total Feathers: {login_data['total_feathers_gained']}", True, WHITE)
        virtual_surface.blit(feathers_text, (50, stats_y))
        
        if login_data["satyr_unlocked"]:
            satyr_text = small_font.render("Satyr Unlocked", True, SELECTED_COLOR)
            virtual_surface.blit(satyr_text, (300, stats_y))
        
        # Draw claim message
        if claim_message and current_time - message_timer < 3000:
            msg_surface = button_font.render(claim_message, True, SELECTED_COLOR)
            msg_rect = msg_surface.get_rect(center=(VIRTUAL_W // 2, 400))
            # Draw background for message
            bg_rect = pygame.Rect(msg_rect.x - 10, msg_rect.y - 5, msg_rect.width + 20, msg_rect.height + 10)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), bg_rect, border_radius=5)
            virtual_surface.blit(msg_surface, msg_rect)
        
        # Draw back button
        pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        draw_scaled_centered()
        clock.tick(60)

# Settings
def settings_screen():
    # Initialize settings
    music_enabled = pygame.mixer.music.get_busy()
    volume = pygame.mixer.music.get_volume()
    
    # UI Elements
    slider_rect = pygame.Rect(VIRTUAL_W//2 - 150, 250, 300, 20)
    handle_radius = 15
    handle_x = slider_rect.x + int(volume * slider_rect.width)
    dragging = False
    
    # Buttons
    music_toggle_rect = pygame.Rect(VIRTUAL_W//2 - 100, 180, 200, 50)
    back_button_rect = pygame.Rect(VIRTUAL_W//2 - 100, 400, 200, 60)
    
    while True:
        virtual_surface.fill((25, 25, 45))  # Dark background
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Volume slider interaction
                handle_rect = pygame.Rect(handle_x - handle_radius, slider_rect.y - handle_radius, 
                                        handle_radius * 2, slider_rect.height + handle_radius * 2)
                if handle_rect.collidepoint((vmx, vmy)) or slider_rect.collidepoint((vmx, vmy)):
                    dragging = True
                    # Update handle position immediately
                    handle_x = max(slider_rect.x, min(slider_rect.x + slider_rect.width, vmx))
                    volume = (handle_x - slider_rect.x) / slider_rect.width
                    pygame.mixer.music.set_volume(volume)
                
                # Music toggle button
                elif music_toggle_rect.collidepoint((vmx, vmy)):
                    if music_enabled:
                        pygame.mixer.music.pause()
                        music_enabled = False
                    else:
                        if not pygame.mixer.music.get_busy():
                            try:
                                pygame.mixer.music.load("assets/musicbg.mp3")
                                pygame.mixer.music.play(-1)
                            except:
                                pass
                        else:
                            pygame.mixer.music.unpause()
                        music_enabled = True
                
                # Back button
                elif back_button_rect.collidepoint((vmx, vmy)):
                    return
            
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            
            elif event.type == pygame.MOUSEMOTION and dragging:
                # Update slider while dragging
                handle_x = max(slider_rect.x, min(slider_rect.x + slider_rect.width, vmx))
                volume = (handle_x - slider_rect.x) / slider_rect.width
                pygame.mixer.music.set_volume(volume)
        
        # Draw title
        title_text = title_font.render("SETTINGS", True, get_rainbow_color())
        title_rect = title_text.get_rect(center=(VIRTUAL_W//2, 100))
        virtual_surface.blit(title_text, title_rect)
        
        # Draw music toggle button
        music_color = SELECTED_COLOR if music_enabled else (100, 100, 100)
        if music_toggle_rect.collidepoint((vmx, vmy)):
            music_color = tuple(min(255, c + 30) for c in music_color)
        
        pygame.draw.rect(virtual_surface, music_color, music_toggle_rect, border_radius=10)
        music_text = button_font.render("MUSIC: ON" if music_enabled else "MUSIC: OFF", True, WHITE)
        music_text_rect = music_text.get_rect(center=music_toggle_rect.center)
        virtual_surface.blit(music_text, music_text_rect)
        
        # Draw volume label
        volume_label = button_font.render("VOLUME", True, WHITE)
        volume_label_rect = volume_label.get_rect(center=(VIRTUAL_W//2, 260))
        virtual_surface.blit(volume_label, volume_label_rect)
        
        # Draw volume slider track
        pygame.draw.rect(virtual_surface, (100, 100, 100), slider_rect, border_radius=10)
        
        # Draw volume slider fill
        fill_width = int((handle_x - slider_rect.x))
        if fill_width > 0:
            fill_rect = pygame.Rect(slider_rect.x, slider_rect.y, fill_width, slider_rect.height)
            pygame.draw.rect(virtual_surface, HOVER_COLOR, fill_rect, border_radius=10)
        
        # Draw volume slider handle
        handle_color = WHITE if dragging else (200, 200, 200)
        pygame.draw.circle(virtual_surface, handle_color, (int(handle_x), slider_rect.centery), handle_radius)
        pygame.draw.circle(virtual_surface, (50, 50, 50), (int(handle_x), slider_rect.centery), handle_radius, 2)
        
        # Draw volume percentage
        volume_percent = int(volume * 100)
        percent_text = small_font.render(f"{volume_percent}%", True, WHITE)
        percent_rect = percent_text.get_rect(center=(VIRTUAL_W//2, 290))
        virtual_surface.blit(percent_text, percent_rect)
        
        # Draw game version
        version_text = button_font.render("Game Version: 0.1", True, (180, 180, 180))
        version_rect = version_text.get_rect(center=(VIRTUAL_W//2, 340))
        virtual_surface.blit(version_text, version_rect)
        
        # Draw back button
        back_color = HOVER_COLOR if back_button_rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, back_color, back_button_rect, border_radius=10)
        back_text = button_font.render("BACK", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_button_rect.center)
        virtual_surface.blit(back_text, back_text_rect)
        
        # Draw credit text (keeping the original credit display)
        draw_credit_text(virtual_surface)
        
        draw_scaled_centered()
        clock.tick(60)    	                       	                   
# Fungsi lain
def draw_scaled_centered():
    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
    scaled = pygame.transform.smoothscale(virtual_surface, (int(VIRTUAL_W * scale), int(VIRTUAL_H * scale)))
    screen.fill(BORDER_COLOR)
    screen.blit(scaled, ((SCREEN_W - scaled.get_width()) // 2, (SCREEN_H - scaled.get_height()) // 2))
    pygame.display.update()

def start_game():
    thread = threading.Thread(target=load_data_in_background)
    thread.start()
    # Load and play music when the game starts
    try:
        pygame.mixer.music.load("assets/musicbg.mp3")  # Load the music file
        pygame.mixer.music.set_volume(1.0)  # Set volume to 100%
        pygame.mixer.music.play(-1)  # Play the music in a loop
    except pygame.error as e:
        print(f"Error loading music: {e}")  # Print error if music fails to load

    character_screen()

def open_settings(): 
    settings_screen()

character_frame_counts["Ichigo"] = {
    "Attack_1": 4,
    "Attack_2": 3,
    "Attack_3": 4,
    "Dead": 3,
    "Hurt": 3,
    "Idle": 6,
    "Jump": 10,
    "Run": 8,
    "Shield": 2,
    "Walk": 8,
}

character_damage["Ichigo"] = {
    "Attack_1": 25,
    "Attack_2": 50,
    "Attack_3": 75,
}

character_ranges["Ichigo"] = 110

def endless_tower():
    """Endless Tower mode with 100 stages"""
    
    # Character selection first
    selected_character = character_selection_screen()
    if not selected_character:
        return
    
    # Dialogue screen with Magician
    def dialogue_screen():
        try:
            dialogue_bg = pygame.image.load("assets/dialoguebg.png").convert()
            dialogue_bg = pygame.transform.smoothscale(dialogue_bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            dialogue_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            dialogue_bg.fill((30, 30, 60))
        
        # Load Magician idle animation
        try:
            magician_idle = load_animation_frames("Magician", ["Idle"], character_frame_counts["Magician"])
        except:
            magician_idle = {"Idle": [pygame.Surface((240, 240))]}
        
        # Load Ichigo idle animation for dialogue (reward preview)
        try:
            ichigo_idle_frames = []
            for i in range(6):  # 6 frames for Ichigo Idle
                frame_path = f"assets/Ichigo/Idle.png"
                if i == 0:  # Load the sprite sheet once
                    sprite_sheet = pygame.image.load(frame_path).convert_alpha()
                    frame_width = sprite_sheet.get_width() // 6  # Assuming 6 frames horizontally
                    frame_height = sprite_sheet.get_height()
                
                # Extract individual frame
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame = sprite_sheet.subsurface(frame_rect)
                ichigo_idle_frames.append(frame)
            
            ichigo_idle = {"Idle": ichigo_idle_frames}
        except:
            # Fallback if loading fails
            placeholder = pygame.Surface((120, 120))
            placeholder.fill((100, 100, 150))
            ichigo_idle = {"Idle": [placeholder]}
        
        # Magician positioned at center-left and larger
        magician_pos = [VIRTUAL_W // 3, VIRTUAL_H // 2 - 50]
        magician_frame = 0
        magician_timer = 0
        
        # Ichigo positioned at center-right
        ichigo_pos = [VIRTUAL_W * 2 // 3, VIRTUAL_H // 2 - 50]
        ichigo_frame = 0
        ichigo_timer = 0
        
        dialogue_text = [
            "Welcome to the Endless Tower, brave warrior!",
            "You will face 100 stages of increasingly",
            "difficult enemies. Each stage gets harder!",
            "Stages 1-99: 100 HP, 15 Attack",
            "Stage 100 Boss: 500 HP, 20 Attack",
            "Every 10 stages you get +5 damage & +50 HP!",
            "Complete stage 100 for a chance to unlock",
            "the legendary fighter ICHIGO! (1-5% chance)",
            "Good luck on your journey!"
        ]
        
        current_line = 0
        continue_button = pygame.Rect(VIRTUAL_W//2 - 100, VIRTUAL_H - 60, 200, 60)
        
        while True:
            virtual_surface.blit(dialogue_bg, (0, 0))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if continue_button.collidepoint((vmx, vmy)):
                        if current_line < len(dialogue_text) - 1:
                            current_line += 1
                        else:
                            return True  # Start tower
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return False  # Cancel
            
            # Update Magician animation
            magician_timer += clock.get_time()
            if magician_timer >= 160:  # Idle frame delay
                magician_timer = 0
                if magician_idle["Idle"]:
                    magician_frame = (magician_frame + 1) % len(magician_idle["Idle"])
            
            # Update Ichigo animation
            ichigo_timer += clock.get_time()
            if ichigo_timer >= 160:
                ichigo_timer = 0
                if ichigo_idle["Idle"]:
                    ichigo_frame = (ichigo_frame + 1) % len(ichigo_idle["Idle"])
            
            # Draw Magician (larger and positioned left)
            if magician_idle["Idle"]:
                frame_idx = min(magician_frame, len(magician_idle["Idle"]) - 1)
                sprite = pygame.transform.scale(magician_idle["Idle"][frame_idx], (200, 200))
                rect = sprite.get_rect(center=magician_pos)
                virtual_surface.blit(sprite, rect.topleft)
            
            # Draw Ichigo when showing reward message (line 7) - Single animated character
            if current_line >= 6 and ichigo_idle["Idle"]:
                frame_idx = min(ichigo_frame, len(ichigo_idle["Idle"]) - 1)
                sprite = pygame.transform.scale(ichigo_idle["Idle"][frame_idx], (160, 160))
                rect = sprite.get_rect(center=ichigo_pos)
                virtual_surface.blit(sprite, rect.topleft)
                
                # Draw Ichigo name below with glow effect
                ichigo_text = button_font.render("ICHIGO", True, (255, 215, 0))
                ichigo_name_rect = ichigo_text.get_rect(center=(ichigo_pos[0], ichigo_pos[1] + 100))
                
                # Add glow effect to Ichigo name
                glow_surface = pygame.Surface((ichigo_text.get_width() + 10, ichigo_text.get_height() + 10))
                glow_surface.set_alpha(80)
                glow_surface.fill((255, 215, 0))
                glow_rect = glow_surface.get_rect(center=ichigo_name_rect.center)
                virtual_surface.blit(glow_surface, glow_rect)
                virtual_surface.blit(ichigo_text, ichigo_name_rect)
            
            # Draw dialogue box
            dialogue_box = pygame.Rect(50, VIRTUAL_H - 200, VIRTUAL_W - 100, 120)
            pygame.draw.rect(virtual_surface, (128, 128, 128, 180), dialogue_box, border_radius=10)
            pygame.draw.rect(virtual_surface, WHITE, dialogue_box, 3, border_radius=10)
            
            # Draw current dialogue text
            text_surface = small_font.render(dialogue_text[current_line], True, WHITE)
            text_rect = text_surface.get_rect(center=(dialogue_box.centerx, dialogue_box.centery))
            virtual_surface.blit(text_surface, text_rect)
            
            # Draw continue button
            button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=10)
            
            button_text = "CONTINUE" if current_line < len(dialogue_text) - 1 else "START TOWER"
            btn_surface = button_font.render(button_text, True, WHITE)
            virtual_surface.blit(btn_surface, btn_surface.get_rect(center=continue_button.center))
            
            # Draw progress indicator
            progress_text = small_font.render(f"{current_line + 1}/{len(dialogue_text)}", True, WHITE)
            virtual_surface.blit(progress_text, (VIRTUAL_W - 100, 50))
            
            draw_scaled_centered()
            clock.tick(60)
    
    # Show dialogue, return if cancelled
    if not dialogue_screen():
        return
    
    # Entrance screen showing player vs enemy
    def entrance_screen(player_char, enemy_type, stage_num):
        try:
            entrance_bg = pygame.image.load("assets/endlessbg.png").convert()
            entrance_bg = pygame.transform.smoothscale(entrance_bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            entrance_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            entrance_bg.fill((40, 20, 60))
        
        # Load character idle animations
        try:
            player_idle = load_animation_frames(player_char, ["Attack_2"], character_frame_counts[player_char])
            enemy_idle = load_animation_frames(enemy_type, ["Attack_2"], character_frame_counts[enemy_type])
        except:
            player_idle = {"Attack_2": [pygame.Surface((200, 200))]}
            enemy_idle = {"Attack_2": [pygame.Surface((200, 200))]}
        
        # Animation states
        player_frame = 0
        enemy_frame = 0
        player_timer = 0
        enemy_timer = 0
        
        # Positions
        player_pos = [VIRTUAL_W // 4, VIRTUAL_H // 2]
        enemy_pos = [VIRTUAL_W * 3 // 4, VIRTUAL_H // 2]
        
        # VS text animation
        vs_scale = 1.0
        vs_direction = 1
        
        start_time = pygame.time.get_ticks()
        duration = 3000  # 3 seconds
        
        while pygame.time.get_ticks() - start_time < duration:
            dt = clock.get_time()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        return  # Skip entrance
            
            # Update animations
            player_timer += dt
            enemy_timer += dt
            
            if player_timer >= 160:
                player_timer = 0
                if player_idle["Attack_2"]:
                    player_frame = (player_frame + 1) % len(player_idle["Attack_2"])
            
            if enemy_timer >= 160:
                enemy_timer = 0
                if enemy_idle["Attack_2"]:
                    enemy_frame = (enemy_frame + 1) % len(enemy_idle["Attack_2"])
            
            # Update VS text animation
            vs_scale += vs_direction * 0.01
            if vs_scale >= 1.3:
                vs_direction = -1
            elif vs_scale <= 0.8:
                vs_direction = 1
            
            # Drawing
            virtual_surface.blit(entrance_bg, (0, 0))
            
            # Draw darkened overlay for dramatic effect
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            overlay.set_alpha(100)
            overlay.fill((0, 0, 0))
            virtual_surface.blit(overlay, (0, 0))
            
            # Draw player character
            if player_idle["Attack_2"]:
                frame_idx = min(player_frame, len(player_idle["Attack_2"]) - 1)
                sprite = pygame.transform.scale(player_idle["Attack_2"][frame_idx], (200, 200))
                rect = sprite.get_rect(center=player_pos)
                virtual_surface.blit(sprite, rect.topleft)
            
            # Draw enemy character
            if enemy_idle["Attack_2"]:
                frame_idx = min(enemy_frame, len(enemy_idle["Attack_2"]) - 1)
                sprite = pygame.transform.scale(enemy_idle["Attack_2"][frame_idx], (200, 200))
                # Flip enemy sprite to face player
                sprite = pygame.transform.flip(sprite, True, False)
                rect = sprite.get_rect(center=enemy_pos)
                virtual_surface.blit(sprite, rect.topleft)
            
            # Draw VS text with animation
            vs_font_size = int(48 * vs_scale)
            try:
                vs_font = pygame.font.Font(None, vs_font_size)
            except:
                vs_font = pygame.font.Font(None, 48)
            
            vs_text = vs_font.render("VS", True, (255, 215, 0))
            vs_rect = vs_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2))
            
            # Add glow effect to VS text
            glow_surface = pygame.Surface((vs_text.get_width() + 20, vs_text.get_height() + 20))
            glow_surface.set_alpha(100)
            glow_surface.fill((255, 215, 0))
            glow_rect = glow_surface.get_rect(center=vs_rect.center)
            virtual_surface.blit(glow_surface, glow_rect)
            virtual_surface.blit(vs_text, vs_rect)
            
            # Draw stage info
            stage_text = title_font.render(f"STAGE {stage_num}", True, WHITE)
            stage_rect = stage_text.get_rect(center=(VIRTUAL_W // 2, 80))
            virtual_surface.blit(stage_text, stage_rect)
            
            # Draw character names
            player_name_text = button_font.render(player_char, True, (0, 255, 255))
            player_name_rect = player_name_text.get_rect(center=(player_pos[0], player_pos[1] + 120))
            virtual_surface.blit(player_name_text, player_name_rect)
            
            enemy_name_text = button_font.render(enemy_type, True, (255, 100, 100))
            enemy_name_rect = enemy_name_text.get_rect(center=(enemy_pos[0], enemy_pos[1] + 120))
            virtual_surface.blit(enemy_name_text, enemy_name_rect)
            
            # Draw skip instruction
            skip_text = small_font.render("Press SPACE or ENTER to skip", True, (200, 200, 200))
            skip_rect = skip_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 50))
            virtual_surface.blit(skip_text, skip_rect)
            
            draw_scaled_centered()
            clock.tick(60)
    
    # Tower gameplay
    def tower_gameplay():
        # Player stats
        PLAYER_MAX_HP = 300  # Base HP for tower
        PLAYER_MAX_MP = 300
        
        # Game state variables that need to be reset on restart
        def reset_battle_state():
            nonlocal hp, mp, is_dead, is_hurt, hurt_timer, last_mp_regen, last_heal_time, death_animation_complete
            nonlocal action, idx, timer, pos, vel, jumping, jump_count, is_shielding, last_attack_time
            
            # Reset player stats
            hp = PLAYER_MAX_HP + strength_buff_hp
            mp = PLAYER_MAX_MP
            is_dead = False
            is_hurt = False
            hurt_timer = 0
            last_mp_regen = pygame.time.get_ticks()
            last_heal_time = 0
            death_animation_complete = False
            
            # Reset player animation state
            action = "Idle"
            idx = 0
            timer = 0
            pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
            vel = [0, 0]
            jumping = False
            jump_count = 2
            is_shielding = False
            last_attack_time = 0
        
        # Initial state setup
        hp = PLAYER_MAX_HP
        mp = PLAYER_MAX_MP
        
        # Buff system for every 10 stages
        strength_buff_damage = 0  # Additional damage from buffs
        strength_buff_hp = 0      # Additional HP from buffs
        
        # Game state
        current_stage = 1
        is_dead = False
        is_hurt = False
        hurt_timer = 0
        last_mp_regen = pygame.time.get_ticks()
        last_heal_time = 0
        death_animation_complete = False
        
        # Load assets
        try:
            tower_bg = pygame.image.load("assets/endlessbg.png").convert()
            tower_bg = pygame.transform.smoothscale(tower_bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            tower_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            tower_bg.fill((40, 20, 60))
        
        # Load pause icon (transparent PNG)
        try:
            pause_icon = pygame.image.load("assets/gamesettings.png").convert_alpha()
            pause_icon = pygame.transform.scale(pause_icon, (30, 30))
        except:
            pause_icon = None
        
        # Load and play tower music
        try:
            pygame.mixer.music.load("assets/endlessbg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading tower music: {e}")
        
        # Load player animations
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
        anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])
        
        frame_delays = {
            "Idle": 40, "Run": 40, "Jump": 70, "Shield": 80,
            "Attack_1": 50, "Attack_2": 55, "Attack_3": 50,
            "Dead": 100, "Hurt": 80
        }
        
        # Player animation state
        action = "Idle"
        idx, timer = 0, 0
        pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
        vel = [0, 0]
        jumping = False
        jump_count = 2
        is_shielding = False
        last_attack_time = 0
        
        # Enemy types for tower
        enemy_types = ["Gangster", "Graffiti", "Hero_Knight", "Kitsune", "Kunoichi", 
                      "Magician", "Samurai", "Satyr", "Soldier", "Vampire", "Yurei", "Ichigo"]
        
        # Create enemy for current stage
        def create_stage_enemy():
            enemy_type = random.choice(enemy_types)
            enemy = Enemy(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)
            
            # Set enemy stats based on stage
            if current_stage < 100:
                enemy.hp = 100
                enemy.max_hp = 100
                enemy.attack_damage_multiplier = 15
            else:  # Stage 100 boss
                enemy.hp = 500
                enemy.max_hp = 500
                enemy.attack_damage_multiplier = 20
                
            return enemy
        
        def apply_stage_buff(stage):
            """Apply strength buff every 10 stages (except stage 100)"""
            nonlocal strength_buff_damage, strength_buff_hp, hp, PLAYER_MAX_HP
            
            if stage % 10 == 0 and stage != 100:
                strength_buff_damage += 5
                strength_buff_hp += 50
                PLAYER_MAX_HP += 50
                hp += 50  # Heal when getting buff
                
                # Show buff notification
                buff_notification(stage)
        
        def buff_notification(stage):
            """Show buff notification screen"""
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            
            continue_button = pygame.Rect(VIRTUAL_W//2 - 100, 350, 200, 60)
            start_time = pygame.time.get_ticks()
            
            while pygame.time.get_ticks() - start_time < 3000:  # Auto-close after 3 seconds
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if continue_button.collidepoint((vmx, vmy)):
                            return
                    if event.type == pygame.KEYDOWN:
                        return  # Any key to close
                
                virtual_surface.blit(overlay, (0, 0))
                
                # Buff title
                buff_title = title_font.render("STRENGTHENED!", True, (255, 215, 0))
                virtual_surface.blit(buff_title, buff_title.get_rect(center=(VIRTUAL_W // 2, 150)))
                
                # Buff details
                stage_text = button_font.render(f"Stage {stage} Reward", True, WHITE)
                virtual_surface.blit(stage_text, stage_text.get_rect(center=(VIRTUAL_W // 2, 200)))
                
                damage_text = small_font.render("+5 Attack Damage", True, (255, 100, 100))
                virtual_surface.blit(damage_text, damage_text.get_rect(center=(VIRTUAL_W // 2, 240)))
                
                hp_text = small_font.render("+50 Max HP", True, (100, 255, 100))
                virtual_surface.blit(hp_text, hp_text.get_rect(center=(VIRTUAL_W // 2, 260)))
                
                total_text = small_font.render(f"Total Buffs: +{strength_buff_damage} DMG, +{strength_buff_hp} HP", True, (200, 200, 255))
                virtual_surface.blit(total_text, total_text.get_rect(center=(VIRTUAL_W // 2, 300)))
                
                # Continue button
                button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=10)
                
                continue_text = button_font.render("CONTINUE", True, WHITE)
                virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
                
                draw_scaled_centered()
                clock.tick(60)
        
        def ichigo_unlock_screen(success):
            """Show Ichigo unlock attempt result"""
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            overlay.set_alpha(220)
            overlay.fill((0, 0, 0))
            
            continue_button = pygame.Rect(VIRTUAL_W//2 - 100, 400, 200, 60)
            
            # Load Ichigo idle animation if successful
            ichigo_idle = None
            ichigo_frame = 0
            ichigo_timer = 0
            
            if success:
                try:
                    ichigo_idle_frames = []
                    for i in range(6):  # 6 frames for Ichigo Idle
                        frame_path = f"assets/Ichigo/Idle.png"
                        if i == 0:  # Load the sprite sheet once
                            sprite_sheet = pygame.image.load(frame_path).convert_alpha()
                            frame_width = sprite_sheet.get_width() // 6  # Assuming 6 frames horizontally
                            frame_height = sprite_sheet.get_height()
                        
                        # Extract individual frame
                        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                        frame = sprite_sheet.subsurface(frame_rect)
                        ichigo_idle_frames.append(frame)
                    
                    ichigo_idle = {"Idle": ichigo_idle_frames}
                except:
                    # Fallback if loading fails
                    placeholder = pygame.Surface((200, 200))
                    placeholder.fill((100, 100, 150))
                    ichigo_idle = {"Idle": [placeholder]}
            
            while True:
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if continue_button.collidepoint((vmx, vmy)):
                            return
                    if event.type == pygame.KEYDOWN:
                        return
                
                virtual_surface.blit(overlay, (0, 0))
                
                if success:
                    # Success screen
                    title_text = title_font.render("ICHIGO UNLOCKED!", True, (255, 215, 0))
                    virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 120)))
                    
                    success_text = button_font.render("Congratulations!", True, (0, 255, 0))
                    virtual_surface.blit(success_text, success_text.get_rect(center=(VIRTUAL_W // 2, 170)))
                    
                    # Draw animated Ichigo
                    if ichigo_idle and ichigo_idle["Idle"]:
                        ichigo_timer += clock.get_time()
                        if ichigo_timer >= 160:
                            ichigo_timer = 0
                            ichigo_frame = (ichigo_frame + 1) % len(ichigo_idle["Idle"])
                        
                        frame_idx = min(ichigo_frame, len(ichigo_idle["Idle"]) - 1)
                        sprite = pygame.transform.scale(ichigo_idle["Idle"][frame_idx], (200, 200))
                        rect = sprite.get_rect(center=(VIRTUAL_W // 2, 280))
                        virtual_surface.blit(sprite, rect.topleft)
                    
                    char_text = small_font.render("New Character Available!", True, WHITE)
                    virtual_surface.blit(char_text, char_text.get_rect(center=(VIRTUAL_W // 2, 360)))
                    
                else:
                    # Failure screen
                    title_text = title_font.render("NO LUCK THIS TIME", True, (255, 100, 100))
                    virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 200)))
                    
                    fail_text = button_font.render("Better luck next time!", True, WHITE)
                    virtual_surface.blit(fail_text, fail_text.get_rect(center=(VIRTUAL_W // 2, 250)))
                    
                    chance_text = small_font.render("Ichigo unlock chance: 1-5%", True, (200, 200, 200))
                    virtual_surface.blit(chance_text, chance_text.get_rect(center=(VIRTUAL_W // 2, 290)))
                
                # Continue button
                button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=10)
                
                continue_text = button_font.render("CONTINUE", True, WHITE)
                virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
                
                draw_scaled_centered()
                clock.tick(60)
        
        # Show entrance screen for first stage
        first_enemy_type = random.choice(enemy_types)
        entrance_screen(selected_character, first_enemy_type, current_stage)
        current_enemy = Enemy(first_enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)
        
        # Set initial enemy stats
        if current_stage < 100:
            current_enemy.hp = 100
            current_enemy.max_hp = 100
            current_enemy.attack_damage_multiplier = 15
        else:
            current_enemy.hp = 500
            current_enemy.max_hp = 500
            current_enemy.attack_damage_multiplier = 20
        
        # UI Controls
        size = 60
        spacing = 10
        dir_center_x = 90
        dir_center_y = VIRTUAL_H - 280
        
        left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
        right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
        up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
        down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)
        
        # Action buttons (including heal button)
        btn_w, btn_h = 70, 50
        action_y = VIRTUAL_H - btn_h - 10
        action_buttons = {
            "atk1": pygame.Rect(VIRTUAL_W - (btn_w + 5) * 7, action_y, btn_w, btn_h),
            "atk2": pygame.Rect(VIRTUAL_W - (btn_w + 5) * 6, action_y, btn_w, btn_h),
            "atk3": pygame.Rect(VIRTUAL_W - (btn_w + 5) * 5, action_y, btn_w, btn_h),
            "jump": pygame.Rect(VIRTUAL_W - (btn_w + 5) * 4, action_y, btn_w, btn_h),
            "shield": pygame.Rect(VIRTUAL_W - (btn_w + 5) * 3, action_y, btn_w, btn_h),
            "run": pygame.Rect(VIRTUAL_W - (btn_w + 5) * 2, action_y, btn_w, btn_h),
            "heal": pygame.Rect(VIRTUAL_W - (btn_w + 5), action_y, btn_w, btn_h),
        }
        
        pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)
        
        def check_collision_and_damage():
            nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
            
            # Enemy attacks player
            if current_enemy.is_attacking():
                distance = abs(current_enemy.pos[0] - pos[0])
                if distance < current_enemy.get_attack_range():
                    current_time = pygame.time.get_ticks()
                    if current_time - current_enemy.last_attack_time > 400:  # Faster enemy attacks
                        damage = current_enemy.attack_damage_multiplier if hasattr(current_enemy, 'attack_damage_multiplier') else 15
                        
                        if is_shielding:
                            damage = 0
                        
                        if damage > 0:
                            hp -= damage
                            current_enemy.last_attack_time = current_time
                            
                            if hp <= 0:
                                hp = 0
                                is_dead = True
                                action = "Dead"
                                idx = 0
                                timer = 0
                            else:
                                is_hurt = True
                                hurt_timer = pygame.time.get_ticks()
                                action = "Hurt"
                                idx = 0
                                timer = 0
            
            # Player attacks enemy (with strength buffs)
            if "Attack" in action and idx > 0:
                distance = abs(pos[0] - current_enemy.pos[0])
                if distance < character_ranges[selected_character]:
                    current_time = pygame.time.get_ticks()
                    if current_time - last_attack_time > 250:  # Faster player attacks
                        base_damage = character_damage[selected_character][action]
                        total_damage = base_damage + strength_buff_damage
                        current_enemy.take_damage(total_damage)
                        last_attack_time = current_time
        
        def draw_tower_hud():
            # Player HUD
            pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 220, 130), border_radius=8)
            
            # HP bar
            pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 190, 12))
            hp_width = int((hp / PLAYER_MAX_HP) * 190)
            pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, hp_width, 12))
            
            # MP bar
            pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 190, 12))
            mp_width = int((mp / PLAYER_MAX_MP) * 190)
            pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, mp_width, 12))
            
            # Stats text
            hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
            virtual_surface.blit(hp_text, (15, 50))
            mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
            virtual_surface.blit(mp_text, (15, 65))
            
            # Stage info
            stage_text = small_font.render(f"Stage: {current_stage}/100", True, WHITE)
            virtual_surface.blit(stage_text, (15, 80))
            
            character_text = small_font.render(f"Character: {selected_character}", True, WHITE)
            virtual_surface.blit(character_text, (15, 95))
            
            # Show buffs if any
            if strength_buff_damage > 0 or strength_buff_hp > 0:
                buff_text = small_font.render(f"Buffs: +{strength_buff_damage} DMG, +{strength_buff_hp} HP", True, (255, 215, 0))
                virtual_surface.blit(buff_text, (15, 110))
        
        def stage_complete_screen():
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            overlay.set_alpha(200)
            overlay.fill((0, 0, 0))
            
            continue_button = pygame.Rect(VIRTUAL_W//2 - 100, 300, 200, 60)
            
            while True:
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if continue_button.collidepoint((vmx, vmy)):
                            return True
                
                virtual_surface.blit(overlay, (0, 0))
                
                title_text = title_font.render(f"Stage {current_stage} Complete!", True, SELECTED_COLOR)
                virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 150)))
                
                if current_stage == 100:
                    victory_text = button_font.render("TOWER CONQUERED!", True, (255, 215, 0))
                    virtual_surface.blit(victory_text, victory_text.get_rect(center=(VIRTUAL_W // 2, 200)))
                    
                    # Show Ichigo unlock attempt
                    unlock_chance = random.randint(1, 100)
                    ichigo_unlocked = unlock_chance <= 5  # 1-5% chance
                    
                    if ichigo_unlocked:
                        reward_text = small_font.render("ICHIGO CHARACTER UNLOCKED!", True, (0, 255, 0))
                    else:
                        reward_text = small_font.render("No character unlock this time...", True, (255, 100, 100))
                    virtual_surface.blit(reward_text, reward_text.get_rect(center=(VIRTUAL_W // 2, 230)))
                    
                elif current_stage % 10 == 0:
                    # Show buff notification for stages 10, 20, 30, etc.
                    buff_text = button_font.render("STRENGTHENED!", True, (255, 215, 0))
                    virtual_surface.blit(buff_text, buff_text.get_rect(center=(VIRTUAL_W // 2, 200)))
                    
                    buff_details = small_font.render("+5 Attack Damage, +50 Max HP", True, WHITE)
                    virtual_surface.blit(buff_details, buff_details.get_rect(center=(VIRTUAL_W // 2, 230)))
                else:
                    next_text = button_font.render(f"Next: Stage {current_stage + 1}", True, WHITE)
                    virtual_surface.blit(next_text, next_text.get_rect(center=(VIRTUAL_W // 2, 220)))
                
                # Continue button
                button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=10)
                
                continue_text = button_font.render("CONTINUE" if current_stage < 100 else "FINISH", True, WHITE)
                virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
                
                draw_scaled_centered()
                clock.tick(30)
        
        # Main tower loop (optimized for performance)
        while current_stage <= 100:
            dt = clock.tick(120)  # Higher FPS target for smoother gameplay
            timer += dt
            now = pygame.time.get_ticks()
            
            # Check game over
            if is_dead and death_animation_complete:
                pygame.mixer.music.stop()
                result = game_over_screen(False, f"Stage {current_stage}")
                if result == "restart":
                    # Reset current battle state and restart current stage
                    reset_battle_state()
                    
                    # Recreate enemy for current stage
                    enemy_type = random.choice(enemy_types)
                    entrance_screen(selected_character, enemy_type, current_stage)
                    current_enemy = Enemy(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)
                    
                    # Set enemy stats based on current stage
                    if current_stage < 100:
                        current_enemy.hp = 100
                        current_enemy.max_hp = 100
                        current_enemy.attack_damage_multiplier = 15
                    else:
                        current_enemy.hp = 500
                        current_enemy.max_hp = 500
                        current_enemy.attack_damage_multiplier = 20
                    
                    # Restart tower music
                    try:
                        pygame.mixer.music.load("assets/endlessbg.mp3")
                        pygame.mixer.music.set_volume(1.0)
                        pygame.mixer.music.play(-1)
                    except Exception as e:
                        print(f"Error loading tower music: {e}")
                    
                    continue  # Continue with reset battle
                elif result == "menu":
                    return "back"
            
            # Check stage completion
            if current_enemy.is_dead and current_enemy.death_animation_complete:
                # Apply buffs for stages 10, 20, 30, etc. (but not 100)
                if current_stage % 10 == 0 and current_stage != 100:
                    apply_stage_buff(current_stage)
                
                if current_stage == 100:
                    # Handle Ichigo unlock attempt
                    unlock_chance = random.randint(1, 100)
                    ichigo_unlocked = unlock_chance <= 5  # 1-5% chance
                    
                    # Show stage complete first
                    stage_complete_screen()
                    
                    # Then show Ichigo unlock result
                    ichigo_unlock_screen(ichigo_unlocked)
                    
                    # Save Ichigo unlock to character roster if successful
                    if ichigo_unlocked:
                        data = load_character_data()
                        if "Ichigo" not in data["owned_characters"]:
                            data["owned_characters"].append("Ichigo")
                            save_character_data(data)
                    
                    pygame.mixer.music.stop()
                    return "completed"
                else:
                    stage_complete_screen()
                
                # Next stage
                current_stage += 1
                
                if current_stage <= 100:
                    # Show entrance screen for new stage
                    next_enemy_type = random.choice(enemy_types)
                    entrance_screen(selected_character, next_enemy_type, current_stage)
                    
                    current_enemy = Enemy(next_enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)
                    
                    # Set enemy stats for new stage
                    if current_stage < 100:
                        current_enemy.hp = 100
                        current_enemy.max_hp = 100
                        current_enemy.attack_damage_multiplier = 15
                    else:  # Stage 100 boss
                        current_enemy.hp = 500
                        current_enemy.max_hp = 500
                        current_enemy.attack_damage_multiplier = 20
                    
                    hp = min(PLAYER_MAX_HP, hp + 50)  # Heal between stages
                    mp = PLAYER_MAX_MP  # Restore MP
                    action = "Idle"
                    idx = 0
                    is_hurt = False
                    is_dead = False
            
            # MP regeneration
            if now - last_mp_regen > 2000:
                mp = min(PLAYER_MAX_MP, mp + 10)
                last_mp_regen = now
            
            # Handle hurt state (faster recovery)
            if is_hurt and now - hurt_timer > 400:  # Faster hurt recovery
                is_hurt = False
                if not is_dead:
                    action = "Idle"
                    idx = 0
                    timer = 0
            
            # Event handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    exit_game()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return "back"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    mx, my = ((mx - ox) / scale, (my - oy) / scale)
                    
                    if pause_button.collidepoint((mx, my)):
                        pause_result = pause_menu()
                        if pause_result == "back":
                            pygame.mixer.music.stop()
                            return "back"
                        elif pause_result == "restart":
                            # Reset current battle state and restart current stage
                            reset_battle_state()
                            
                            # Recreate enemy for current stage
                            enemy_type = random.choice(enemy_types)
                            entrance_screen(selected_character, enemy_type, current_stage)
                            current_enemy = Enemy(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)
                            
                            # Set enemy stats based on current stage
                            if current_stage < 100:
                                current_enemy.hp = 100
                                current_enemy.max_hp = 100
                                current_enemy.attack_damage_multiplier = 15
                            else:
                                current_enemy.hp = 500
                                current_enemy.max_hp = 500
                                current_enemy.attack_damage_multiplier = 20
                            
                            # Restart tower music
                            try:
                                pygame.mixer.music.load("assets/endlessbg.mp3")
                                pygame.mixer.music.set_volume(1.0)
                                pygame.mixer.music.play(-1)
                            except Exception as e:
                                print(f"Error loading tower music: {e}")
                            
                            continue  # Continue with reset battle
                    
                    if is_dead or is_hurt:
                        continue
                    
                    # Movement (faster and more responsive)
                    if left.collidepoint((mx, my)):
                        vel[0] = -6; action = "Run"; is_shielding = False  # Faster movement
                    elif right.collidepoint((mx, my)):
                        vel[0] = 6; action = "Run"; is_shielding = False
                    elif up.collidepoint((mx, my)):
                        vel[1] = -6; action = "Run"; is_shielding = False
                    elif down.collidepoint((mx, my)):
                        vel[1] = 6; action = "Run"; is_shielding = False
                    
                    # Actions
                    elif action_buttons["atk1"].collidepoint((mx, my)) and mp >= 5:
                        action = "Attack_1"; idx = 0; timer = 0; mp -= 5; is_shielding = False
                    elif action_buttons["atk2"].collidepoint((mx, my)) and mp >= 8:
                        action = "Attack_2"; idx = 0; timer = 0; mp -= 8; is_shielding = False
                    elif action_buttons["atk3"].collidepoint((mx, my)) and mp >= 12:
                        action = "Attack_3"; idx = 0; timer = 0; mp -= 12; is_shielding = False
                    elif action_buttons["jump"].collidepoint((mx, my)) and jump_count > 0:
                        vel[1] = -12; action = "Jump"; jumping = True; jump_count -= 1; idx = 0; timer = 0; is_shielding = False  # Higher jump
                    elif action_buttons["shield"].collidepoint((mx, my)):
                        action = "Shield"; is_shielding = True; idx = 0; timer = 0
                    elif action_buttons["run"].collidepoint((mx, my)):
                        vel[0] = 8; action = "Run"; is_shielding = False  # Faster run
                    elif action_buttons["heal"].collidepoint((mx, my)):
                        # Heal ability - 50 HP every 3 seconds (faster cooldown)
                        if now - last_heal_time > 3000:
                            hp = min(PLAYER_MAX_HP, hp + 50)
                            last_heal_time = now
                
                if e.type == pygame.MOUSEBUTTONUP:
                    if not is_dead and not is_hurt:
                        vel = [0, 0]
                        is_shielding = False
                        if not jumping:
                            action = "Idle"
            
            # Physics update (smoother and faster)
            if not is_dead:
                if jumping:
                    vel[1] += 0.6  # Slightly faster gravity
                    pos[1] += vel[1]
                    if pos[1] >= VIRTUAL_H - 150:
                        pos[1] = VIRTUAL_H - 150
                        jumping = False
                        vel[1] = 0
                        jump_count = 2
                        if not is_hurt:
                            action = "Idle"
                else:
                    pos[0] += vel[0]
                    pos[1] += vel[1]
                
                # Screen bounds
                sprite_width = 160
                left_limit = sprite_width // 2
                right_limit = VIRTUAL_W - sprite_width // 2
                pos[0] = max(left_limit, min(right_limit, pos[0]))
                pos[1] = max(0, min(VIRTUAL_H - 160, pos[1]))
            
            # Update enemy
            current_enemy.update(dt, pos)
            check_collision_and_damage()
            
            # Update player animation (faster transitions)
            delay = frame_delays.get(action, 60)  # Default faster delay
            if timer >= delay:
                timer = 0
                if anims[action]:
                    idx += 1
                    if idx >= len(anims[action]):
                        if action == "Dead":
                            death_animation_complete = True
                            idx = len(anims["Dead"]) - 1
                        elif "Attack" in action or action == "Jump":
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0
                        elif action == "Hurt":
                            idx = len(anims["Hurt"]) - 1
                        else:
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0
            
            # Drawing
            virtual_surface.blit(tower_bg, (0, 0))
            
            # Draw player
            if anims[action]:
                idx = min(idx, len(anims[action]) - 1)
                sprite = pygame.transform.scale(anims[action][idx], (160, 160))
                rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                virtual_surface.blit(sprite, rect.topleft)
                
                if is_shielding:
                    shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                    shield_rect = shield_text.get_rect(center=(pos[0], pos[1] - 100))
                    virtual_surface.blit(shield_text, shield_rect)
            
            # Draw enemy
            current_enemy.draw(virtual_surface)
            
            # Draw UI
            if not is_dead:
                # Movement buttons
                for btn, label in [(left, "<"), (right, ">"), (up, "^"), (down, "v")]:
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, btn, border_radius=8)
                    txt = button_font.render(label, True, WHITE)
                    virtual_surface.blit(txt, txt.get_rect(center=btn.center))
                
                # Action buttons with MP requirements
                button_configs = [
                    ("atk1", "Atk1", 5), ("atk2", "Atk2", 8), ("atk3", "Atk3", 12),
                    ("jump", "Jump", 0), ("shield", "Shield", 0), ("run", "Run", 0)
                ]
                
                for btn_name, label, mp_cost in button_configs:
                    color = BUTTON_COLOR if mp >= mp_cost or mp_cost == 0 else (100, 100, 100)
                    pygame.draw.rect(virtual_surface, color, action_buttons[btn_name], border_radius=8)
                    txt = small_font.render(label, True, WHITE)
                    virtual_surface.blit(txt, txt.get_rect(center=action_buttons[btn_name].center))
                
                # Heal button with cooldown indicator (faster cooldown)
                heal_available = (now - last_heal_time > 3000)  # 3 second cooldown
                heal_color = BUTTON_COLOR if heal_available else (100, 100, 100)
                pygame.draw.rect(virtual_surface, heal_color, action_buttons["heal"], border_radius=8)
                
                if heal_available:
                    heal_text = small_font.render("Heal", True, WHITE)
                else:
                    remaining = 3 - (now - last_heal_time) // 1000  # 3 second countdown
                    heal_text = small_font.render(f"{remaining}s", True, WHITE)
                virtual_surface.blit(heal_text, heal_text.get_rect(center=action_buttons["heal"].center))
            
            # Draw pause button (transparent PNG without black border)
            if pause_icon:
                icon_rect = pause_icon.get_rect(center=pause_button.center)
                virtual_surface.blit(pause_icon, icon_rect)
            else:
                # Fallback: draw transparent button without black border
                pygame.draw.rect(virtual_surface, (100, 100, 100, 128), pause_button, border_radius=20)
                pause_text = small_font.render("⚙", True, WHITE)
                virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))
            
            draw_tower_hud()
            draw_scaled_centered()
    
    # Start the tower
    result = tower_gameplay()
    pygame.mixer.music.stop()
    return result

def exit_game():
    """
    Menampilkan popup konfirmasi exit dengan gaya RPG modern (ukuran besar)
    """
    # Get current screen
    screen = pygame.display.get_surface()
    if not screen:
        pygame.quit()
        sys.exit()
    
    screen_width, screen_height = screen.get_size()
    clock = pygame.time.Clock()
    
    # Load sound effect
    try:
        click_sound = pygame.mixer.Sound("soundeffects/click.mp3")
        click_sound.set_volume(1.0)  # Adjust volume as needed
    except:
        click_sound = None
        print("Warning: Could not load click.mp3")
    
    # Popup settings (DIPERBESAR)
    popup_width, popup_height = 600, 350
    popup_x = (screen_width - popup_width) // 2
    popup_y = (screen_height - popup_height) // 2
    
    # Colors
    bg_color = (20, 20, 30)
    border_color = (255, 215, 0)  # Gold
    button_hover_yes = (50, 150, 50)
    button_hover_no = (150, 50, 50)
    button_normal = (50, 50, 70)
    
    # Fonts (DIPERBESAR)
    title_font = pygame.font.Font(None, 72)
    subtitle_font = pygame.font.Font(None, 36)
    button_font = pygame.font.Font(None, 48)
    
    # Button positions (DIPERBESAR) - CENTERED
    button_width, button_height = 200, 70
    button_y = popup_y + popup_height - 100  # Adjusted for better centering
    button_spacing = 40
    total_button_width = (button_width * 2) + button_spacing
    button_start_x = popup_x + (popup_width - total_button_width) // 2
    
    yes_rect = pygame.Rect(button_start_x, button_y, button_width, button_height)
    no_rect = pygame.Rect(button_start_x + button_width + button_spacing, button_y, button_width, button_height)
    
    # Fade overlay
    overlay = pygame.Surface((screen_width, screen_height))
    overlay.fill((0, 0, 0))
    fade_alpha = 0
    
    # Save current screen
    background = screen.copy()
    
    confirming = True
    result = False
    
    while confirming:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if yes_rect.collidepoint(mouse_pos):
                        if click_sound:
                            click_sound.play()
                        result = True
                        confirming = False
                    elif no_rect.collidepoint(mouse_pos):
                        if click_sound:
                            click_sound.play()
                        result = False
                        confirming = False
                        
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if click_sound:
                        click_sound.play()
                    result = False
                    confirming = False
                elif event.key == pygame.K_RETURN:
                    if click_sound:
                        click_sound.play()
                    result = True
                    confirming = False
        
        # Draw background
        screen.blit(background, (0, 0))
        
        # Fade effect
        if fade_alpha < 180:
            fade_alpha = min(180, fade_alpha + 15)
        overlay.set_alpha(fade_alpha)
        screen.blit(overlay, (0, 0))
        
        # Draw popup with glow effect
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        
        # Enhanced glow effect (LEBIH BESAR)
        for i in range(5, 0, -1):
            glow_rect = popup_rect.inflate(i * 6, i * 6)
            glow_alpha = 60 // i
            glow_color = (border_color[0] // 5, border_color[1] // 5, border_color[2] // 5)
            pygame.draw.rect(screen, glow_color, glow_rect, border_radius=20)
        
        # Main popup
        pygame.draw.rect(screen, bg_color, popup_rect, border_radius=15)
        pygame.draw.rect(screen, border_color, popup_rect, 4, border_radius=15)
        
        # Inner border
        inner_rect = popup_rect.inflate(-20, -20)
        pygame.draw.rect(screen, border_color, inner_rect, 2, border_radius=12)
        
        # Title with shadow effect
        shadow_offset = 3
        title_shadow = title_font.render("EXIT GAME?", True, (10, 10, 10))
        shadow_rect = title_shadow.get_rect(center=(popup_x + popup_width // 2 + shadow_offset, 
                                                   popup_y + 80 + shadow_offset))
        screen.blit(title_shadow, shadow_rect)
        
        title_text = title_font.render("EXIT GAME?", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(popup_x + popup_width // 2, popup_y + 80))
        screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = subtitle_font.render("Are you sure you want to quit?", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(popup_x + popup_width // 2, popup_y + 140))
        screen.blit(subtitle_text, subtitle_rect)
        
        # Decorative line
        line_y = popup_y + 180
        pygame.draw.line(screen, border_color, (popup_x + 50, line_y), 
                        (popup_x + popup_width - 50, line_y), 2)
        
        # YES Button with enhanced effects
        yes_hover = yes_rect.collidepoint(mouse_pos)
        yes_color = button_hover_yes if yes_hover else button_normal
        
        # Button shadow
        shadow_rect = yes_rect.copy()
        shadow_rect.y += 5
        pygame.draw.rect(screen, (10, 10, 10), shadow_rect, border_radius=10)
        
        # Button gradient effect when hover
        if yes_hover:
            for i in range(3):
                hover_rect = yes_rect.inflate(i * 2, i * 2)
                hover_color = (50 + i * 20, 150 + i * 20, 50 + i * 20)
                pygame.draw.rect(screen, hover_color, hover_rect, 1, border_radius=10)
        
        pygame.draw.rect(screen, yes_color, yes_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, yes_rect, 3, border_radius=10)
        
        yes_text = button_font.render("YES", True, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=yes_rect.center)
        screen.blit(yes_text, yes_text_rect)
        
        # NO Button with enhanced effects
        no_hover = no_rect.collidepoint(mouse_pos)
        no_color = button_hover_no if no_hover else button_normal
        
        # Button shadow
        shadow_rect = no_rect.copy()
        shadow_rect.y += 5
        pygame.draw.rect(screen, (10, 10, 10), shadow_rect, border_radius=10)
        
        # Button gradient effect when hover
        if no_hover:
            for i in range(3):
                hover_rect = no_rect.inflate(i * 2, i * 2)
                hover_color = (150 + i * 20, 50 + i * 20, 50 + i * 20)
                pygame.draw.rect(screen, hover_color, hover_rect, 1, border_radius=10)
        
        pygame.draw.rect(screen, no_color, no_rect, border_radius=10)
        pygame.draw.rect(screen, border_color, no_rect, 3, border_radius=10)
        
        no_text = button_font.render("NO", True, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=no_rect.center)
        screen.blit(no_text, no_text_rect)
        
        # Enhanced decorative corners
        corner_size = 30
        corner_thickness = 3
        corners = [
            # Top-left
            [(popup_x + 10, popup_y + corner_size), (popup_x + 10, popup_y + 10), (popup_x + corner_size, popup_y + 10)],
            # Top-right
            [(popup_x + popup_width - corner_size, popup_y + 10), (popup_x + popup_width - 10, popup_y + 10), (popup_x + popup_width - 10, popup_y + corner_size)],
            # Bottom-left
            [(popup_x + 10, popup_y + popup_height - corner_size), (popup_x + 10, popup_y + popup_height - 10), (popup_x + corner_size, popup_y + popup_height - 10)],
            # Bottom-right
            [(popup_x + popup_width - corner_size, popup_y + popup_height - 10), (popup_x + popup_width - 10, popup_y + popup_height - 10), (popup_x + popup_width - 10, popup_y + popup_height - corner_size)]
        ]
        
        for corner in corners:
            pygame.draw.lines(screen, border_color, False, corner, corner_thickness)
        
        # Additional decorative elements
        # Center ornament
        ornament_size = 20
        ornament_y = popup_y - ornament_size // 2
        pygame.draw.circle(screen, border_color, (popup_x + popup_width // 2, ornament_y), ornament_size)
        pygame.draw.circle(screen, bg_color, (popup_x + popup_width // 2, ornament_y), ornament_size - 3)
        pygame.draw.circle(screen, border_color, (popup_x + popup_width // 2, ornament_y), ornament_size // 3)
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS
    
    # Execute result
    if result:
        # Wait a bit for sound to play
        if click_sound:
            pygame.time.wait(100)
        pygame.quit()
        sys.exit()
               
# Summer Event frame counts for new characters
summer_girl_frame_counts = {
    "SummerGirl1": {
        "Attack_1": 8,
        "Idle": 9,
        "Shield": 4,
        "Walk": 12
    },
    "SummerGirl2": {
        "Attack_1": 9,
        "Idle": 7,
        "Shield": 2,
        "Walk": 12
    },
    "SummerGirl3": {
        "Attack_1": 6,
        "Idle": 6,
        "Shield": 3,
        "Walk": 12
    }
}

def load_summer_girl_animation_frames(character_name, actions, frame_counts):
    """Load animation frames specifically for Summer Girls"""
    animations = {}
    
    for action in actions:
        frames = []
        try:
            # Load the sprite sheet for this action
            sprite_sheet_path = f"assets/{character_name}/{action}.png"
            sprite_sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
            
            # Get frame count for this action
            frame_count = frame_counts.get(action, 1)
            frame_width = sprite_sheet.get_width() // frame_count
            frame_height = sprite_sheet.get_height()
            
            # Extract individual frames
            for i in range(frame_count):
                frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame = sprite_sheet.subsurface(frame_rect).copy()
                frames.append(frame)
            
            animations[action] = frames
            print(f"Loaded {len(frames)} frames for {character_name} {action}")
            
        except pygame.error as e:
            print(f"Failed to load {character_name} {action}: {e}")
            # Create placeholder frame
            placeholder = pygame.Surface((64, 64))
            if action == "Attack_1":
                placeholder.fill((255, 100, 100))  # Red for attack
            elif action == "Shield":
                placeholder.fill((100, 100, 255))  # Blue for shield
            elif action == "Walk":
                placeholder.fill((100, 255, 100))  # Green for walk
            else:  # Idle
                placeholder.fill((255, 255, 100))  # Yellow for idle
            
            animations[action] = [placeholder]
            print(f"Created placeholder for {character_name} {action}")
    
    return animations

def play_summer_music():
    """Play summer event background music"""
    try:
        pygame.mixer.music.load("assets/summer.mp3")
        pygame.mixer.music.set_volume(1.0)  # Set volume to 50%
        pygame.mixer.music.play(-1)  # Loop indefinitely
        print("Summer music started")
    except pygame.error as e:
        print(f"Failed to load summer music: {e}")

def stop_summer_music():
    """Stop summer event music"""
    try:
        pygame.mixer.music.stop()
        print("Summer music stopped")
    except:
        pass

# Vampire character frame counts
vampire_frame_counts = {
    "Attack_1": 5,
    "Attack_2": 3,
    "Attack_3": 4,
    "Dead": 8,
    "Hurt": 1,
    "Idle": 5,
    "Jump": 7,
    "Shield": 2,
    "Run": 8,
    "Walk": 8
}

character_frame_counts["Vampire"] = vampire_frame_counts

# Update character damage untuk Karakter Vampire
character_damage["Vampire"] = {"Attack_1": 17, "Attack_2": 35, "Attack_3": 40}
character_ranges["Vampire"] = 100

# Summer Girl stats
summer_girl_stats = {
    "SummerGirl1": {
        "hp": 250,
        "damage": 10,
        "shield_reduction": 0.5,
        "drop_item": "Sakura",
        "drop_chance": 0.5,
        "drop_amount": (1, 5)
    },
    "SummerGirl2": {
        "hp": 250,
        "damage": 15,
        "shield_reduction": 0.8,
        "drop_item": "Water",
        "drop_chance": 0.5,
        "drop_amount": (1, 5)
    },
    "SummerGirl3": {
        "hp": 250,
        "damage": 20,
        "shield_reduction": 1.0,
        "drop_item": "Black Water",
        "drop_chance": 0.5,
        "drop_amount": (1, 5)
    }
}

# Summer event data management
def load_summer_data():
    """Load summer event data from file"""
    try:
        with open("summer_data.json", "r") as f:
            import json
            return json.load(f)
    except:
        return {
            "sakura": 0,
            "water": 0,
            "black_water": 0,
            "free_rewards_claimed": False,
            "vampire_unlocked": False
        }

def save_summer_data(data):
    """Save summer event data to file"""
    try:
        with open("summer_data.json", "w") as f:
            import json
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving summer data: {e}")

class SummerGirl:
    def __init__(self, girl_type, x, y):
        self.girl_type = girl_type
        self.pos = [x, y]
        self.stats = summer_girl_stats[girl_type]
        self.hp = self.stats["hp"]
        self.max_hp = self.stats["hp"]
        self.action = "Idle"
        self.frame_idx = 0
        self.timer = 0
        self.last_action_time = pygame.time.get_ticks()
        self.is_dead = False
        self.is_hurt = False
        self.hurt_timer = 0
        self.death_animation_complete = False
        self.is_shielding = False
        self.shield_timer = 0
        self.last_attack_time = 0
        self.ai_state = "IDLE"
        self.state_timer = 0
        self.movement_speed = 1
        self.attack_range = 100
        
        # Load animations using specialized Summer Girl loader
        actions = ["Idle", "Walk", "Shield", "Attack_1"]
        self.animations = load_summer_girl_animation_frames(girl_type, actions, summer_girl_frame_counts[girl_type])
        
        print(f"Initialized {girl_type} with animations: {list(self.animations.keys())}")
        for action, frames in self.animations.items():
            print(f"  {action}: {len(frames)} frames")
        
        # Frame delays
        self.frame_delays = {
            "Idle": 160,
            "Walk": 150,
            "Shield": 170,
            "Attack_1": 130
        }
    
    def take_damage(self, damage):
        if self.is_dead:
            return
        
        # Apply shield reduction
        if self.is_shielding:
            damage = int(damage * (1 - self.stats["shield_reduction"]))
            
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.action = "Idle"  # Summer girls don't have death animation
            self.frame_idx = 0
            self.timer = 0
            self.death_animation_complete = True
        else:
            self.is_hurt = True
            self.hurt_timer = pygame.time.get_ticks()
    
    def update_ai_state(self, player_pos):
        """AI decision making for summer girls"""
        current_time = pygame.time.get_ticks()
        distance_to_player = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)

        if current_time - self.state_timer > 2000:
            health_percentage = self.hp / self.max_hp
            
            if distance_to_player > self.attack_range:
                self.ai_state = "APPROACH"
            elif distance_to_player < self.attack_range * 0.7:
                if random.random() < 0.6:
                    self.ai_state = "ATTACK"
                else:
                    self.ai_state = "DEFEND"
            else:
                action_choice = random.random()
                if action_choice < 0.5:
                    self.ai_state = "ATTACK"
                else:
                    self.ai_state = "DEFEND"
            
            self.state_timer = current_time
    
    def execute_ai_action(self, player_pos):
        """Execute action based on AI state"""
        current_time = pygame.time.get_ticks()
        
        if self.ai_state == "APPROACH":
            if self.pos[0] < player_pos[0]:
                self.pos[0] += self.movement_speed
            else:
                self.pos[0] -= self.movement_speed
            
            if self.pos[1] < player_pos[1]:
                self.pos[1] += self.movement_speed
            else:
                self.pos[1] -= self.movement_speed
            
            self.action = "Walk"
                
        elif self.ai_state == "ATTACK":
            if current_time - self.last_action_time > 1500:
                self.action = "Attack_1"
                self.frame_idx = 0
                self.timer = 0
                self.last_action_time = current_time
                self.is_shielding = False
                    
        elif self.ai_state == "DEFEND":
            self.action = "Shield"
            self.is_shielding = True
            self.shield_timer = current_time
        else:
            self.action = "Idle"
            self.is_shielding = False
    
    def update(self, dt, player_pos):
        current_time = pygame.time.get_ticks()
        
        if self.is_dead:
            return
        
        # Handle hurt state
        if self.is_hurt:
            if current_time - self.hurt_timer > 500:
                self.is_hurt = False
        
        # Handle shield timeout
        if self.is_shielding and current_time - self.shield_timer > 3000:
            self.is_shielding = False
        
        # AI behavior
        if not self.is_hurt:
            self.update_ai_state(player_pos)
            self.execute_ai_action(player_pos)
        
        # Keep within screen bounds
        sprite_width = 160
        left_limit = sprite_width // 2
        right_limit = VIRTUAL_W - sprite_width // 2
        
        if self.pos[0] < left_limit:
            self.pos[0] = left_limit
        elif self.pos[0] > right_limit:
            self.pos[0] = right_limit
        
        # Update animation
        self.timer += dt
        delay = self.frame_delays.get(self.action, 130)
        if self.timer >= delay:
            self.timer = 0
            # Ensure action exists in animations
            if self.action not in self.animations:
                self.action = "Idle"
            
            if self.animations.get(self.action):
                self.frame_idx += 1
                if self.frame_idx >= len(self.animations[self.action]):
                    if self.action == "Attack_1":
                        self.action = "Idle"
                        self.frame_idx = 0
                    elif self.action == "Shield" and self.is_shielding:
                        self.frame_idx = len(self.animations["Shield"]) - 1
                    else:
                        self.frame_idx = 0
    
    def draw(self, surface):
        # Ensure action exists in animations
        if self.action not in self.animations:
            self.action = "Idle"
        
        if self.animations.get(self.action):
            frame_idx = min(self.frame_idx, len(self.animations[self.action]) - 1)
            sprite = pygame.transform.scale(self.animations[self.action][frame_idx], (160, 160))
            sprite = pygame.transform.flip(sprite, True, False)
            rect = sprite.get_rect(midbottom=(self.pos[0], self.pos[1] + 100))
            surface.blit(sprite, rect.topleft)
        
        # Draw health bar
        if not self.is_dead:
            bar_width = 100
            bar_height = 8
            bar_x = self.pos[0] - bar_width // 2
            bar_y = self.pos[1] - 180
            
            pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            health_width = int((self.hp / self.max_hp) * bar_width)
            pygame.draw.rect(surface, RED, (bar_x, bar_y, health_width, bar_height))
            
            # Name
            name_text = small_font.render(self.girl_type, True, WHITE)
            name_rect = name_text.get_rect(center=(self.pos[0], bar_y - 15))
            surface.blit(name_text, name_rect)
            
            if self.is_shielding:
                shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                shield_rect = shield_text.get_rect(center=(self.pos[0], self.pos[1] - 200))
                surface.blit(shield_text, shield_rect)
    
    def get_attack_damage(self):
        if self.action == "Attack_1":
            return self.stats["damage"]
        return 0
    
    def is_attacking(self):
        return self.action == "Attack_1" and self.frame_idx > 0 and self.frame_idx < len(self.animations["Attack_1"]) - 1
    
    def get_drop_reward(self):
        """Get drop reward when defeated"""
        if random.random() < self.stats["drop_chance"]:
            min_amount, max_amount = self.stats["drop_amount"]
            amount = random.randint(min_amount, max_amount)
            return self.stats["drop_item"], amount
        return None, 0

def summer_reward_screen(item_name, amount, got_reward):
    """Screen to show reward after battle"""
    # Load background
    try:
        reward_bg = pygame.image.load("assets/summerbg.png").convert()
        reward_bg = pygame.transform.smoothscale(reward_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        reward_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        reward_bg.fill((255, 200, 100))
    
    # Load item icon if got reward
    item_icon = None
    if got_reward and item_name:
        try:
            if item_name == "Sakura":
                item_icon = pygame.image.load("assets/Drops/sakura.png").convert_alpha()
            elif item_name == "Water":
                item_icon = pygame.image.load("assets/Drops/water.png").convert_alpha()
            elif item_name == "Black Water":
                item_icon = pygame.image.load("assets/Drops/blackwater.png").convert_alpha()
            
            if item_icon:
                item_icon = pygame.transform.scale(item_icon, (120, 120))
        except:
            pass
    
    # If no icon, create placeholder
    if got_reward and not item_icon:
        item_icon = pygame.Surface((120, 120))
        item_icon.fill((100, 100, 255))
    
    continue_button = pygame.Rect(VIRTUAL_W//2 - 80, 450, 160, 50)
    
    waiting = True
    while waiting:
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint((vmx, vmy)):
                    waiting = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    waiting = False
        
        # Draw background
        virtual_surface.blit(reward_bg, (0, 0))
        
        if got_reward:
            # Victory title
            victory_text = title_font.render("Victory!", True, get_rainbow_color())
            virtual_surface.blit(victory_text, victory_text.get_rect(center=(VIRTUAL_W // 2, 120)))
            
            # Reward received text
            reward_text = button_font.render("You received:", True, WHITE)
            virtual_surface.blit(reward_text, reward_text.get_rect(center=(VIRTUAL_W // 2, 180)))
            
            # Draw item icon
            if item_icon:
                icon_rect = item_icon.get_rect(center=(VIRTUAL_W // 2, 280))
                virtual_surface.blit(item_icon, icon_rect.topleft)
            
            # Item name and amount
            item_text = title_font.render(f"{item_name} x{amount}", True, WHITE)
            virtual_surface.blit(item_text, item_text.get_rect(center=(VIRTUAL_W // 2, 350)))
        else:
            # Victory but no reward
            victory_text = title_font.render("DEFEAT", True, get_rainbow_color())
            virtual_surface.blit(victory_text, victory_text.get_rect(center=(VIRTUAL_W // 2, 200)))
            
        # Continue button
        button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=8)
        continue_text = button_font.render("CONTINUE", True, WHITE)
        virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
        
        draw_scaled_centered()
        clock.tick(60)

def summer_battle_screen(selected_character):
    """Summer event battle screen - FIXED VERSION"""
    summer_data = load_summer_data()
    selected_enemy = None
    
    # Load summer background
    try:
        summer_bg = pygame.image.load("assets/summerbg.png").convert()
        summer_bg = pygame.transform.smoothscale(summer_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        summer_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        summer_bg.fill((255, 200, 100))  # Summer orange color
    
    # Load Summer Girl idle animations for preview
    summer_girls_idle = {}
    for girl_type in ["SummerGirl1", "SummerGirl2", "SummerGirl3"]:
        try:
            idle_frames = load_animation_frames(girl_type, ["Idle"], summer_girl_frame_counts[girl_type])["Idle"]
            if idle_frames:
                summer_girls_idle[girl_type] = idle_frames
            else:
                # Create placeholder if no frames
                placeholder = pygame.Surface((120, 120))
                placeholder.fill((100, 100, 255))
                summer_girls_idle[girl_type] = [placeholder]
        except:
            # Create placeholder if assets missing
            placeholder = pygame.Surface((120, 120))
            placeholder.fill((100, 100, 255))
            summer_girls_idle[girl_type] = [placeholder]
    
    # Animation states for preview
    animation_timers = {"SummerGirl1": 0, "SummerGirl2": 0, "SummerGirl3": 0}
    animation_indices = {"SummerGirl1": 0, "SummerGirl2": 0, "SummerGirl3": 0}
    
    # Battle selection screen - CENTERED LAYOUT
    battle_buttons = {
        "girl1": pygame.Rect(VIRTUAL_W//2 - 240, 250, 150, 120),  # Centered horizontally
        "girl2": pygame.Rect(VIRTUAL_W//2 - 75, 250, 150, 120),   # Middle
        "girl3": pygame.Rect(VIRTUAL_W//2 + 90, 250, 150, 120),   # Right
        "battle": pygame.Rect(VIRTUAL_W//2 - 80, 400, 160, 50),   # Only show when enemy selected
        "back": pygame.Rect(20, 20, 80, 40)
    }
    
    while True:
        dt = clock.get_time()
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Update animations
        for girl_type in ["SummerGirl1", "SummerGirl2", "SummerGirl3"]:
            animation_timers[girl_type] += dt
            if animation_timers[girl_type] >= 160:  # Idle animation delay
                animation_timers[girl_type] = 0
                if summer_girls_idle[girl_type]:
                    animation_indices[girl_type] = (animation_indices[girl_type] + 1) % len(summer_girls_idle[girl_type])
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if battle_buttons["back"].collidepoint((vmx, vmy)):
                    return
                elif battle_buttons["girl1"].collidepoint((vmx, vmy)):
                    selected_enemy = "SummerGirl1"
                elif battle_buttons["girl2"].collidepoint((vmx, vmy)):
                    selected_enemy = "SummerGirl2"
                elif battle_buttons["girl3"].collidepoint((vmx, vmy)):
                    selected_enemy = "SummerGirl3"
                elif selected_enemy and battle_buttons["battle"].collidepoint((vmx, vmy)):
                    result = summer_battle_loop(selected_character, selected_enemy)
                    if result:
                        item, amount = result
                        # Show reward screen
                        summer_reward_screen(item, amount, True)
                        
                        # Add to inventory
                        if item == "Sakura":
                            summer_data["sakura"] += amount
                        elif item == "Water":
                            summer_data["water"] += amount
                        elif item == "Black Water":
                            summer_data["black_water"] += amount
                        save_summer_data(summer_data)
                    else:
                        # Show no reward screen
                        summer_reward_screen(None, 0, False)
        
        virtual_surface.blit(summer_bg, (0, 0))
        
        # Title
        title_text = title_font.render("Summer Battle", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 100)))
        
        # Instructions
        if not selected_enemy:
            instruction_text = button_font.render("Select an enemy to battle:", True, WHITE)
            virtual_surface.blit(instruction_text, instruction_text.get_rect(center=(VIRTUAL_W // 2, 200)))
        
        # Character selection boxes - CENTERED
        enemies = [
            ("SummerGirl1", "girl1"),
            ("SummerGirl2", "girl2"), 
            ("SummerGirl3", "girl3")
        ]
        
        for girl_type, button_key in enemies:
            rect = battle_buttons[button_key]
            
            # Highlight selected enemy
            if selected_enemy == girl_type:
                color = SELECTED_COLOR
            elif rect.collidepoint((vmx, vmy)):
                color = HOVER_COLOR
            else:
                color = BUTTON_COLOR
            
            pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
            
            # Draw animated idle sprite
            if summer_girls_idle[girl_type]:
                frame_idx = animation_indices[girl_type]
                sprite = pygame.transform.scale(summer_girls_idle[girl_type][frame_idx], (120, 120))
                sprite_rect = sprite.get_rect(center=rect.center)
                virtual_surface.blit(sprite, sprite_rect.topleft)
            
            # Enemy name below box
            name_text = small_font.render(girl_type, True, WHITE)
            virtual_surface.blit(name_text, name_text.get_rect(center=(rect.centerx, rect.bottom + 15)))
        
        # Battle button - ONLY SHOW WHEN ENEMY IS SELECTED
        if selected_enemy:
            battle_color = HOVER_COLOR if battle_buttons["battle"].collidepoint((vmx, vmy)) else SELECTED_COLOR
            pygame.draw.rect(virtual_surface, battle_color, battle_buttons["battle"], border_radius=8)
            battle_text = button_font.render("BATTLE", True, WHITE)
            virtual_surface.blit(battle_text, battle_text.get_rect(center=battle_buttons["battle"].center))
        
        # Back button
        back_color = HOVER_COLOR if battle_buttons["back"].collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, back_color, battle_buttons["back"], border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=battle_buttons["back"].center))
        
        draw_scaled_centered()
        clock.tick(60)

def summer_battle_loop(selected_character, enemy_type):
    """Summer battle gameplay loop"""
    # Player stats
    PLAYER_MAX_HP = 100
    PLAYER_MAX_MP = 100
    hp = PLAYER_MAX_HP
    mp = PLAYER_MAX_MP
    last_mp_regen = pygame.time.get_ticks()
    is_shielding = False
    is_dead = False
    is_hurt = False
    hurt_timer = 0
    death_animation_complete = False
    last_attack_time = 0

    # Load background
    try:
        bg = pygame.image.load("assets/summerbg.png").convert()
        bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        bg.fill((100, 150, 255))

    # Load player animations
    actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
    anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])

    frame_delays = {
        "Idle": 160, "Run": 140, "Jump": 150, "Shield": 170,
        "Attack_1": 130, "Attack_2": 135, "Attack_3": 130,
        "Dead": 170, "Hurt": 170
    }

    action = "Idle"
    idx, timer = 0, 0
    pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
    vel = [0, 0]
    jumping = False
    jump_count = 2
    holding_shield = False

    # Create summer girl enemy
    enemy = SummerGirl(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)

    def check_collision_and_damage():
        nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
        
        # Check if enemy is attacking
        if enemy.is_attacking():
            distance = abs(enemy.pos[0] - pos[0])
            if distance < enemy.attack_range:
                current_time = pygame.time.get_ticks()
                if current_time - enemy.last_attack_time > 800:
                    damage = enemy.get_attack_damage()
                    
                    if is_shielding:
                        damage = 0
                    
                    if damage > 0:
                        hp -= damage
                        enemy.last_attack_time = current_time
                        
                        if hp <= 0:
                            hp = 0
                            is_dead = True
                            action = "Dead"
                            idx = 0
                            timer = 0
                        else:
                            is_hurt = True
                            hurt_timer = pygame.time.get_ticks()
                            action = "Hurt"
                            idx = 0
                            timer = 0
        
        # Check if player is attacking
        if "Attack" in action and idx > 0:
            distance = abs(pos[0] - enemy.pos[0])
            player_range = character_ranges[selected_character]
            
            if distance < player_range:
                current_time = pygame.time.get_ticks()
                if current_time - last_attack_time > 500:
                    damage = character_damage[selected_character][action]
                    enemy.take_damage(damage)
                    last_attack_time = current_time

    def show_escape_message():
        """Show escape confirmation dialog"""
        # Create overlay
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        virtual_surface.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_rect = pygame.Rect(VIRTUAL_W//2 - 200, VIRTUAL_H//2 - 100, 400, 200)
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, dialog_rect, border_radius=15)
        pygame.draw.rect(virtual_surface, WHITE, dialog_rect, width=3, border_radius=15)
        
        confirm_text = small_font.render("Apakah kamu yakin ingin kabur?", True, WHITE)
        virtual_surface.blit(confirm_text, confirm_text.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H//2 - 10)))
        
        # Buttons
        yes_button = pygame.Rect(VIRTUAL_W//2 - 120, VIRTUAL_H//2 + 30, 80, 40)
        no_button = pygame.Rect(VIRTUAL_W//2 + 40, VIRTUAL_H//2 + 30, 80, 40)
        
        return yes_button, no_button

    # UI setup
    pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)
    
    # Control buttons (simplified for battle)
    size = 60
    spacing = 10
    dir_center_x = 90
    dir_center_y = VIRTUAL_H - 280

    left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
    right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
    up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
    down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

    btn_w, btn_h = 80, 60
    action_y = VIRTUAL_H - btn_h - 10
    action_buttons = {
        "atk1": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 6, action_y, btn_w, btn_h),
        "atk2": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 5, action_y, btn_w, btn_h),
        "atk3": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 4, action_y, btn_w, btn_h),
        "jump": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 3, action_y, btn_w, btn_h),
        "shield": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 2, action_y, btn_w, btn_h),
        "run": pygame.Rect(VIRTUAL_W - (btn_w + spacing), action_y, btn_w, btn_h),
    }

    # Escape dialog state
    showing_escape_dialog = False
    
    try:
        while True:
            dt = clock.tick(60)
            timer += dt
            now = pygame.time.get_ticks()

            # Check game over conditions
            if is_dead and death_animation_complete:
                return None  # Player lost
            
            if enemy.is_dead and enemy.death_animation_complete:
                add_battlepass_points()
                # Player won, get drop reward
                return enemy.get_drop_reward()

            # MP regeneration
            if now - last_mp_regen > 3000:
                mp = min(PLAYER_MAX_MP, mp + 10)
                last_mp_regen = now

            # Handle hurt state
            if is_hurt and now - hurt_timer > 800:
                is_hurt = False
                if not is_dead:
                    action = "Idle"
                    idx = 0
                    timer = 0

            for e in pygame.event.get():
                if e.type == pygame.QUIT: 
                    exit_game()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    if not showing_escape_dialog:
                        showing_escape_dialog = True
                
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    mx, my = ((mx - ox) / scale, (my - oy) / scale)

                    # Handle escape dialog
                    if showing_escape_dialog:
                        yes_button, no_button = show_escape_message()
                        if yes_button.collidepoint((mx, my)):
                            return None  # Player escaped
                        elif no_button.collidepoint((mx, my)):
                            showing_escape_dialog = False
                        continue

                    if pause_button.collidepoint((mx, my)):
                        showing_escape_dialog = True
                        continue

                    if is_dead or is_hurt:
                        continue

                    # Movement controls
                    if left.collidepoint((mx, my)): 
                        vel[0] = -4; action = "Run"
                        is_shielding = False
                    elif right.collidepoint((mx, my)): 
                        vel[0] = 4; action = "Run"
                        is_shielding = False
                    elif up.collidepoint((mx, my)): 
                        vel[1] = -4; action = "Run"
                        is_shielding = False
                    elif down.collidepoint((mx, my)): 
                        vel[1] = 4; action = "Run"
                        is_shielding = False
                    # Attack controls
                    elif action_buttons["atk1"].collidepoint((mx, my)):
                        if mp >= 5: 
                            action = "Attack_1"; idx = 0; timer = 0; mp -= 5
                            is_shielding = False
                    elif action_buttons["atk2"].collidepoint((mx, my)):
                        if mp >= 8: 
                            action = "Attack_2"; idx = 0; timer = 0; mp -= 8
                            is_shielding = False
                    elif action_buttons["atk3"].collidepoint((mx, my)):
                        if mp >= 12: 
                            action = "Attack_3"; idx = 0; timer = 0; mp -= 12
                            is_shielding = False
                    elif action_buttons["jump"].collidepoint((mx, my)):
                        if jump_count > 0:
                            vel[1] = -10; action = "Jump"; jumping = True
                            jump_count -= 1; idx = 0; timer = 0
                            is_shielding = False
                    elif action_buttons["shield"].collidepoint((mx, my)):
                        holding_shield = True; action = "Shield"; idx = 0; timer = 0
                        is_shielding = True

                if e.type == pygame.MOUSEBUTTONUP and not showing_escape_dialog:
                    if not is_dead and not is_hurt:
                        vel = [0, 0]; holding_shield = False; is_shielding = False
                        if not jumping: action = "Idle"

            # Skip game updates when showing escape dialog
            if showing_escape_dialog:
                # Still draw the game but don't update
                virtual_surface.blit(bg, (0, 0))
                
                # Draw player
                if anims[action]:
                    idx = min(idx, len(anims[action]) - 1)
                    sprite = pygame.transform.scale(anims[action][idx], (160, 160))
                    rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                    virtual_surface.blit(sprite, rect.topleft)
                
                # Draw enemy
                enemy.draw(virtual_surface)
                
                # Draw UI
                if not is_dead:
                    # Movement buttons
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, left, border_radius=8)
                    virtual_surface.blit(button_font.render("<", True, WHITE), button_font.render("<", True, WHITE).get_rect(center=left.center))
                    
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, right, border_radius=8)
                    virtual_surface.blit(button_font.render(">", True, WHITE), button_font.render(">", True, WHITE).get_rect(center=right.center))
                    
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, up, border_radius=8)
                    virtual_surface.blit(button_font.render("^", True, WHITE), button_font.render("^", True, WHITE).get_rect(center=up.center))
                    
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, down, border_radius=8)
                    virtual_surface.blit(button_font.render("v", True, WHITE), button_font.render("v", True, WHITE).get_rect(center=down.center))
                    
                    # Action buttons
                    for btn_name, rect in action_buttons.items():
                        color = BUTTON_COLOR
                        if btn_name == "atk1" and mp < 5:
                            color = (100, 100, 100)
                        elif btn_name == "atk2" and mp < 8:
                            color = (100, 100, 100)
                        elif btn_name == "atk3" and mp < 12:
                            color = (100, 100, 100)
                        
                        pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
                        text = small_font.render(btn_name.upper(), True, WHITE)
                        virtual_surface.blit(text, text.get_rect(center=rect.center))

                # Draw pause button
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, pause_button, border_radius=20)
                pause_text = button_font.render("X", True, WHITE)
                virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))

                # Draw HUD
                pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 200, 90), border_radius=8)
                pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 170, 10))
                pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, int(hp * 1.7), 10))
                pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 170, 10))
                pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, int(mp * 1.7), 10))
                
                hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
                virtual_surface.blit(hp_text, (15, 50))
                mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
                virtual_surface.blit(mp_text, (15, 65))
                
                # Show escape dialog
                yes_button, no_button = show_escape_message()
                
                # Draw dialog buttons
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                # Yes button
                yes_color = HOVER_COLOR if yes_button.collidepoint((vmx, vmy)) else RED
                pygame.draw.rect(virtual_surface, yes_color, yes_button, border_radius=8)
                yes_text = small_font.render("Ya", True, WHITE)
                virtual_surface.blit(yes_text, yes_text.get_rect(center=yes_button.center))
                
                # No button
                no_color = HOVER_COLOR if no_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
                pygame.draw.rect(virtual_surface, no_color, no_button, border_radius=8)
                no_text = small_font.render("Tidak", True, WHITE)
                virtual_surface.blit(no_text, no_text.get_rect(center=no_button.center))
                
                draw_scaled_centered()
                continue

            # Physics update
            if not is_dead:
                if jumping:
                    vel[1] += 0.5
                    pos[1] += vel[1]
                    if pos[1] >= VIRTUAL_H - 150:
                        pos[1] = VIRTUAL_H - 150; jumping = False
                        vel[1] = 0; jump_count = 2
                        if not is_hurt:
                            action = "Idle"
                else:
                    pos[0] += vel[0]
                    pos[1] += vel[1]

                # Screen bounds
                sprite_width, sprite_height = 160, 160
                left_limit = sprite_width // 2
                right_limit = VIRTUAL_W - sprite_width // 2
                top_limit = 0
                bottom_limit = VIRTUAL_H - sprite_height

                pos[0] = max(left_limit, min(right_limit, pos[0]))
                pos[1] = max(top_limit, min(bottom_limit, pos[1]))

            # Update enemy
            enemy.update(dt, pos)
            
            # Check combat
            check_collision_and_damage()

            # Update player animation
            delay = frame_delays.get(action, 130)
            if timer >= delay:
                timer = 0
                if anims[action]:
                    idx += 1
                    if idx >= len(anims[action]):
                        if action == "Dead":
                            death_animation_complete = True
                            idx = len(anims["Dead"]) - 1
                        elif "Attack" in action or action == "Jump":
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0
                        elif action == "Shield" and holding_shield:
                            idx = len(anims["Shield"]) - 1
                        elif action == "Hurt":
                            idx = len(anims["Hurt"]) - 1
                        else:
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0

            # Drawing
            virtual_surface.blit(bg, (0, 0))
            
            # Draw player
            if anims[action]:
                idx = min(idx, len(anims[action]) - 1)
                sprite = pygame.transform.scale(anims[action][idx], (160, 160))
                rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                virtual_surface.blit(sprite, rect.topleft)
                
                if is_shielding:
                    shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                    shield_rect = shield_text.get_rect(center=(pos[0], pos[1] - 100))
                    virtual_surface.blit(shield_text, shield_rect)
            
            # Draw enemy
            enemy.draw(virtual_surface)

            # Draw UI
            if not is_dead:
                # Movement buttons
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, left, border_radius=8)
                virtual_surface.blit(button_font.render("<", True, WHITE), button_font.render("<", True, WHITE).get_rect(center=left.center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, right, border_radius=8)
                virtual_surface.blit(button_font.render(">", True, WHITE), button_font.render(">", True, WHITE).get_rect(center=right.center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, up, border_radius=8)
                virtual_surface.blit(button_font.render("^", True, WHITE), button_font.render("^", True, WHITE).get_rect(center=up.center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, down, border_radius=8)
                virtual_surface.blit(button_font.render("v", True, WHITE), button_font.render("v", True, WHITE).get_rect(center=down.center))
                
                # Action buttons
                for btn_name, rect in action_buttons.items():
                    color = BUTTON_COLOR
                    if btn_name == "atk1" and mp < 5:
                        color = (100, 100, 100)
                    elif btn_name == "atk2" and mp < 8:
                        color = (100, 100, 100)
                    elif btn_name == "atk3" and mp < 12:
                        color = (100, 100, 100)
                    
                    pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
                    text = small_font.render(btn_name.upper(), True, WHITE)
                    virtual_surface.blit(text, text.get_rect(center=rect.center))

            # Draw pause button
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, pause_button, border_radius=20)
            pause_text = button_font.render("X", True, WHITE)
            virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))

            # Draw HUD
            pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 200, 90), border_radius=8)
            pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 170, 10))
            pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, int(hp * 1.7), 10))
            pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 170, 10))
            pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, int(mp * 1.7), 10))
            
            hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
            virtual_surface.blit(hp_text, (15, 50))
            mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
            virtual_surface.blit(mp_text, (15, 65))

            draw_scaled_centered()
    except:
        return None

def summer_craft_screen():
    summer_data = load_summer_data()
    
    # Load craft background
    try:
        craft_bg = pygame.image.load("assets/summerbg.png").convert()
        craft_bg = pygame.transform.smoothscale(craft_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        craft_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        craft_bg.fill((255, 200, 100))
    
    # Load Vampire idle animation
    try:
        vampire_idle = pygame.image.load("assets/Vampire/Walk.png").convert_alpha()
        frame_count = vampire_frame_counts["Walk"]
        frame_width = vampire_idle.get_width() // frame_count
        vampire_frames = []
        for i in range(frame_count):
            frame = vampire_idle.subsurface(pygame.Rect(i * frame_width, 0, frame_width, vampire_idle.get_height()))
            vampire_frames.append(pygame.transform.scale(frame, (200, 200)))
    except:
        vampire_frames = [pygame.Surface((200, 200))]
        vampire_frames[0].fill((150, 0, 150))
    
    # Load drop item icons
    drop_icons = {}
    try:
        drop_icons["Sakura"] = pygame.transform.scale(pygame.image.load("assets/Drops/sakura.png").convert_alpha(), (60, 60))
        drop_icons["Water"] = pygame.transform.scale(pygame.image.load("assets/Drops/water.png").convert_alpha(), (60, 60))
        drop_icons["Black Water"] = pygame.transform.scale(pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), (60, 60))
    except:
        for item in ["Sakura", "Water", "Black Water"]:
            icon = pygame.Surface((60, 60))
            icon.fill((100, 100, 255))
            drop_icons[item] = icon
    
    # Animation state
    vampire_frame_idx = 0
    vampire_timer = 0
    
    # UI buttons
    exchange_button = pygame.Rect(VIRTUAL_W//2 - 100, 520, 200, 60)
    back_button = pygame.Rect(20, 20, 80, 40)
    
    # Requirements
    required_sakura = 250
    required_water = 250
    required_black_water = 250
    
    # Message display
    message = ""
    message_timer = 0
    message_color = (255, 255, 255)
    
    while True:
        dt = clock.get_time()
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Update vampire animation
        vampire_timer += dt
        if vampire_timer >= 160:  # Idle animation delay
            vampire_timer = 0
            vampire_frame_idx = (vampire_frame_idx + 1) % len(vampire_frames)
        
        # Update message timer
        if message_timer > 0:
            message_timer -= dt
            if message_timer <= 0:
                message = ""
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                elif exchange_button.collidepoint((vmx, vmy)):
                    # Check if vampire already unlocked
                    if summer_data.get("vampire_unlocked", False):
                        message = "Already Owned!"
                        message_color = (255, 255, 0)  # Yellow
                        message_timer = 2000  # 2 seconds
                    # Check if player has enough materials
                    elif (summer_data["sakura"] >= required_sakura and 
                          summer_data["water"] >= required_water and 
                          summer_data["black_water"] >= required_black_water):
                        
                        # Deduct materials
                        summer_data["sakura"] -= required_sakura
                        summer_data["water"] -= required_water
                        summer_data["black_water"] -= required_black_water
                        summer_data["vampire_unlocked"] = True
                        
                        # Add Vampire to owned characters
                        try:
                            character_data = load_character_data()
                            if "Vampire" not in character_data["owned_characters"]:
                                character_data["owned_characters"].append("Vampire")
                                save_character_data(character_data)
                        except:
                            pass
                        
                        save_summer_data(summer_data)
                        
                        # Success message
                        message = "Vampire Crafted Successfully!"
                        message_color = (0, 255, 0)  # Green
                        message_timer = 3000  # 3 seconds
                    else:
                        # Not enough materials
                        message = "Not Enough Materials!"
                        message_color = (255, 0, 0)  # Red
                        message_timer = 2000  # 2 seconds
        
        # Draw background
        virtual_surface.blit(craft_bg, (0, 0))
        
        # Title
        title_text = title_font.render("Summer Craft", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
        
        # Draw Vampire character
        vampire_rect = vampire_frames[vampire_frame_idx].get_rect(center=(VIRTUAL_W // 2, 250))
        virtual_surface.blit(vampire_frames[vampire_frame_idx], vampire_rect.topleft)
        
        # Character name
        vampire_name = title_font.render("Vampire", True, WHITE)
        virtual_surface.blit(vampire_name, vampire_name.get_rect(center=(VIRTUAL_W // 2, 120)))
        
        # Requirements section - CENTERED LAYOUT
        req_title_bold = pygame.font.Font(None, 36)
        req_title_text = req_title_bold.render("Requirements:", True, (255, 255, 255))
        virtual_surface.blit(req_title_text, req_title_text.get_rect(center=(VIRTUAL_W // 2, 380)))
        
        # Draw requirements with icons - CENTERED HORIZONTALLY
        y_offset = 420
        requirements = [
            ("Sakura", required_sakura, summer_data["sakura"]),
            ("Water", required_water, summer_data["water"]),
            ("Black Water", required_black_water, summer_data["black_water"])
        ]
        
        # Calculate total width for centering
        total_width = len(requirements) * 150
        start_x = (VIRTUAL_W - total_width) // 2 + 75  # Center the group
        
        for i, (item, required, owned) in enumerate(requirements):
            x = start_x + i * 150
            
            # Draw icon - centered
            icon_rect = drop_icons[item].get_rect(center=(x, y_offset + 30))
            virtual_surface.blit(drop_icons[item], icon_rect.topleft)
            
            # Draw amount text - centered below icon
            color = SELECTED_COLOR if owned >= required else RED
            text = small_font.render(f"{owned}/{required}", True, color)
            virtual_surface.blit(text, text.get_rect(center=(x, y_offset + 75)))
        
        # Exchange button
        can_exchange = (summer_data["sakura"] >= required_sakura and 
                       summer_data["water"] >= required_water and 
                       summer_data["black_water"] >= required_black_water and
                       not summer_data.get("vampire_unlocked", False))
        
        if summer_data.get("vampire_unlocked", False):
            button_color = (100, 100, 100)
            button_text = "ALREADY OWNED"
        elif can_exchange:
            button_color = HOVER_COLOR if exchange_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            button_text = "CRAFT"
        else:
            button_color = (100, 100, 100)
            button_text = "CRAFT"
        
        pygame.draw.rect(virtual_surface, button_color, exchange_button, border_radius=10)
        text_surface = button_font.render(button_text, True, WHITE)
        virtual_surface.blit(text_surface, text_surface.get_rect(center=exchange_button.center))
        
        # Back button
        back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        # Draw message if any
        if message and message_timer > 0:
            message_text = button_font.render(message, True, message_color)
            message_rect = message_text.get_rect(center=(VIRTUAL_W//2, 490))
            # Draw background for message
            bg_rect = message_rect.inflate(40, 20)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 200), bg_rect, border_radius=10)
            pygame.draw.rect(virtual_surface, message_color, bg_rect, 2, border_radius=10)
            virtual_surface.blit(message_text, message_rect)
        
        draw_scaled_centered()
        clock.tick(60)

def summer_free_rewards_screen():
    """Summer event free rewards screen"""
    summer_data = load_summer_data()
    
    # Load background
    try:
        rewards_bg = pygame.image.load("assets/summerbg.png").convert()
        rewards_bg = pygame.transform.smoothscale(rewards_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        rewards_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        rewards_bg.fill((255, 200, 100))
    
    # Load drop icons
    drop_icons = {}
    try:
        drop_icons["Sakura"] = pygame.transform.scale(pygame.image.load("assets/Drops/sakura.png").convert_alpha(), (80, 80))
        drop_icons["Water"] = pygame.transform.scale(pygame.image.load("assets/Drops/water.png").convert_alpha(), (80, 80))
        drop_icons["Black Water"] = pygame.transform.scale(pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), (80, 80))
    except:
        for item in ["Sakura", "Water", "Black Water"]:
            icon = pygame.Surface((80, 80))
            icon.fill((100, 100, 255))
            drop_icons[item] = icon
    
    # UI buttons
    claim_button = pygame.Rect(VIRTUAL_W//2 - 100, 450, 200, 60)
    back_button = pygame.Rect(20, 20, 80, 40)
    
    while True:
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                elif claim_button.collidepoint((vmx, vmy)) and not summer_data.get("free_rewards_claimed", False):
                    # Give free rewards
                    summer_data["sakura"] += 10
                    summer_data["water"] += 10
                    summer_data["black_water"] += 10
                    summer_data["free_rewards_claimed"] = True
                    save_summer_data(summer_data)
        
        # Draw background
        virtual_surface.blit(rewards_bg, (0, 0))
        
        # Title
        title_text = title_font.render("Free Rewards", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
        
        # Subtitle
        subtitle = button_font.render("Claim your free summer materials!", True, WHITE)
        virtual_surface.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 140)))
        
        # Draw reward items
        rewards = [
            ("Sakura", 10, 200),
            ("Water", 10, 400),
            ("Black Water", 10, 600)
        ]
        
        for item, amount, x in rewards:
            # Draw icon
            icon_rect = drop_icons[item].get_rect(center=(x, 250))
            virtual_surface.blit(drop_icons[item], icon_rect.topleft)
            
            # Draw amount
            amount_text = button_font.render(f"x{amount}", True, WHITE)
            virtual_surface.blit(amount_text, amount_text.get_rect(center=(x, 320)))
            
            # Draw name with bold red-white
            name_font_bold = pygame.font.Font(None, 24)
            name_text = name_font_bold.render(item, True, (255, 255, 255))
            virtual_surface.blit(name_text, name_text.get_rect(center=(x, 350)))
        
        # Claim button
        if summer_data.get("free_rewards_claimed", False):
            button_color = (100, 100, 100)
            button_text = "CLAIMED"
        else:
            button_color = HOVER_COLOR if claim_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            button_text = "CLAIM"
        
        pygame.draw.rect(virtual_surface, button_color, claim_button, border_radius=10)
        text_surface = button_font.render(button_text, True, WHITE)
        virtual_surface.blit(text_surface, text_surface.get_rect(center=claim_button.center))
        
        # Back button
        back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        draw_scaled_centered()
        clock.tick(60)

def summer_announcements_screen():
    """Summer event announcements screen"""
    # Load background
    try:
        announce_bg = pygame.image.load("assets/summerbg.png").convert()
        announce_bg = pygame.transform.smoothscale(announce_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        announce_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        announce_bg.fill((255, 200, 100))
    
    # Load summer event image
    try:
        summer_event_img = pygame.image.load("assets/summer_event.png").convert_alpha()
        summer_event_img = pygame.transform.scale(summer_event_img, (400, 300))
    except:
        summer_event_img = pygame.Surface((400, 300))
        summer_event_img.fill((255, 100, 100))
    
    back_button = pygame.Rect(VIRTUAL_W//2 - 60, 520, 120, 50)
    
    while True:
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
        
        # Draw background
        virtual_surface.blit(announce_bg, (0, 0))
        
        # Welcome message
        welcome_text = title_font.render("Welcome to Summer Event", True, get_rainbow_color())
        virtual_surface.blit(welcome_text, welcome_text.get_rect(center=(VIRTUAL_W // 2, 100)))
        
        # Summer event image
        img_rect = summer_event_img.get_rect(center=(VIRTUAL_W // 2, 300))
        virtual_surface.blit(summer_event_img, img_rect.topleft)
        
        # Back button
        back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=10)
        back_text = button_font.render("BACK", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        draw_scaled_centered()
        clock.tick(60)

def summer_event():
    """Main summer event screen with 4 menu options"""
    # Play summer music when entering event
    play_summer_music()
    
    # Load summer background
    try:
        summer_bg = pygame.image.load("assets/summerbg.png").convert()
        summer_bg = pygame.transform.smoothscale(summer_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        summer_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        summer_bg.fill((255, 200, 100))  # Summer orange color
    
    # Load summer data for display
    summer_data = load_summer_data()
    
    # Menu buttons with more spacing
    menu_buttons = {
        "battle": pygame.Rect(VIRTUAL_W//2 - 160, 220, 320, 70),
        "craft": pygame.Rect(VIRTUAL_W//2 - 160, 310, 320, 70),
        "free_rewards": pygame.Rect(VIRTUAL_W//2 - 160, 400, 320, 70),
        "announcements": pygame.Rect(VIRTUAL_W//2 - 160, 490, 320, 70),
        "back": pygame.Rect(20, 20, 80, 40)
    }
    
    try:
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    stop_summer_music()
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_buttons["back"].collidepoint((vmx, vmy)):
                        stop_summer_music()
                        return
                    elif menu_buttons["battle"].collidepoint((vmx, vmy)):
                        # Get selected character first
                        selected_character = character_selection_screen()
                        if selected_character:
                            summer_battle_screen(selected_character)
                        # Resume summer music after battle
                        play_summer_music()
                    elif menu_buttons["craft"].collidepoint((vmx, vmy)):
                        summer_craft_screen()
                    elif menu_buttons["free_rewards"].collidepoint((vmx, vmy)):
                        summer_free_rewards_screen()
                    elif menu_buttons["announcements"].collidepoint((vmx, vmy)):
                        summer_announcements_screen()
                    
                    # Reload summer data after any menu
                    summer_data = load_summer_data()
            
            # Draw background
            virtual_surface.blit(summer_bg, (0, 0))
            
            # Title with rainbow effect
            title_text = title_font.render("Summer Event 2025", True, get_rainbow_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 100)))
            
            # Display current materials with bold red-white styling
            materials_font_bold = pygame.font.Font(None, 32)
            materials_text = materials_font_bold.render("Your Materials:", True, (255, 255, 255))
            virtual_surface.blit(materials_text, (50, 160))
            
            # Material items with bold red-white styling and spacing
            material_font_bold = pygame.font.Font(None, 24)
            sakura_text = material_font_bold.render(f"Sakura: {summer_data.get('sakura', 0)}", True, (255, 255, 255))
            virtual_surface.blit(sakura_text, (50, 200))
            
            water_text = material_font_bold.render(f"Water: {summer_data.get('water', 0)}", True, (255, 255, 255))
            virtual_surface.blit(water_text, (200, 200))
            
            black_water_text = material_font_bold.render(f"Black Water: {summer_data.get('black_water', 0)}", True, (255, 255, 255))
            virtual_surface.blit(black_water_text, (350, 200))
            
            # Draw menu buttons
            for button_name, rect in menu_buttons.items():
                if button_name == "back":
                    color = HOVER_COLOR if rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
                    pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
                    text = small_font.render("Back", True, WHITE)
                    virtual_surface.blit(text, text.get_rect(center=rect.center))
                else:
                    color = HOVER_COLOR if rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
                    pygame.draw.rect(virtual_surface, color, rect, border_radius=10)
                    
                    # Button text
                    if button_name == "battle":
                        text = button_font.render("BATTLE", True, WHITE)
                    elif button_name == "craft":
                        text = button_font.render("CRAFT", True, WHITE)
                    elif button_name == "free_rewards":
                        text = button_font.render("FREE REWARDS", True, WHITE)
                    elif button_name == "announcements":
                        text = button_font.render("ANNOUNCEMENTS", True, WHITE)
                    
                    virtual_surface.blit(text, text.get_rect(center=rect.center))
            
            draw_scaled_centered()
            clock.tick(60)
    except:
        stop_summer_music()
        raise

def character_gallery():
    character_data = load_character_data()
    owned_characters = character_data["owned_characters"][:]

    # Add special event characters if available
    if is_yurei_available() and "Yurei" not in owned_characters:
        owned_characters.append("Yurei")
    summer_data = load_summer_data()
    if summer_data.get("vampire_unlocked", False) and "Vampire" not in owned_characters:
        owned_characters.append("Vampire")
    
    # Filter characters with available sprites
    available_characters = [char for char in owned_characters if char in character_frame_counts]
    
    if not available_characters:
        no_char_message_timer = pygame.time.get_ticks()
        while pygame.time.get_ticks() - no_char_message_timer < 3000:
            virtual_surface.fill((30, 30, 60))
            title_text = title_font.render("Character Gallery", True, get_rainbow_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
            
            msg_text = button_font.render("No characters owned yet!", True, WHITE)
            virtual_surface.blit(msg_text, msg_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))
            
            back_button = pygame.Rect(20, 20, 80, 40)
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

            pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
            back_text = small_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))

            draw_scaled_centered()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint((vmx, vmy)):
                        return
            clock.tick(60)
        return

    current_char_index = 0
    max_char_index = len(available_characters) - 1

    # Load navigation icons (borderless)
    try:
        prev_icon_raw = pygame.image.load("assets/previous.png").convert_alpha()
        prev_icon = pygame.transform.scale(prev_icon_raw, (60, 60))
    except:
        prev_icon = None
    try:
        next_icon_raw = pygame.image.load("assets/next.png").convert_alpha()
        next_icon = pygame.transform.scale(next_icon_raw, (60, 60))
    except:
        next_icon = None

    # Load background image
    background_image = pygame.image.load("assets/chargallerybg.png").convert()

    # Load and play music
    pygame.mixer.music.load("assets/chargallerybg.mp3")
    pygame.mixer.music.play(-1)  # Loop the music indefinitely

    # UI Elements
    back_button = pygame.Rect(20, 20, 80, 40)
    prev_button = pygame.Rect(50 - 20, VIRTUAL_H // 2 - 30, 60, 60)  # Added space to the left
    next_button = pygame.Rect(VIRTUAL_W - 110 + 20, VIRTUAL_H // 2 - 30, 60, 60)  # Added space to the right

    # Animation state
    current_character_anim_action = "Idle"
    current_character_anim_idx = 0
    current_character_anim_timer = 0
    
    animation_cycle_actions = [
        "Idle", "Walk", "Run", "Attack_1", "Attack_2", "Attack_3", "Jump", "Shield"
    ]
    current_animation_cycle_idx = 0
    last_animation_change_time = pygame.time.get_ticks()
    animation_change_interval = 20000

    # Concise character descriptions
    manual_character_descriptions = {
        "Samurai": [
            "Katana master",
            "Precision strikes",
            "Fast counters",
            "Honor-bound"
        ],
        "Soldier": [
            "Heavy weapons",
            "Tactical combat",
            "High defense",
            "Team leader"
        ],
        "Magician": [
            "Elemental spells",
            "AoE specialist",
            "Low HP",
            "Massive damage"
        ],
        "Hero_Knight": [
            "Legendary warrior",
            "Balanced stats",
            "Boss reward",
            "Shining armor"
        ],
        "Kitsune": [
            "Fox spirit",
            "Fire magic",
            "Elusive",
            "Trickster"
        ],
        "Gangster": [
            "Street fighter",
            "Brute strength",
            "Knockout punch",
            "Unpredictable"
        ],
        "Kunoichi": [
            "Silent assassin",
            "Poison attacks",
            "Self-heal",
            "Vanishing"
        ],
        "Satyr": [
            "Forest guardian",
            "Nature magic",
            "Charge attack",
            "Daily reward"
        ],
        "Yurei": [
            "Ghostly being",
            "Dark energy",
            "Phasing",
            "Gacha exclusive"
        ],
        "Vampire": [
            "Night creature",
            "Life steal",
            "Bat swarm",
            "Event limited"
        ],
        "Ichigo": [
            "Soul warrior",
            "Energy slashes",
            "Final boss",
            "Tower reward"
        ],
        "Martial_Hero": [
            "Combat master",
            "Flurry attacks",
            "Perfect dodge",
            "Premium unlock"
        ],
        "Graffiti": [
            "Urban artist",
            "Color bombs",
            "Wall run",
            "Code redeem"
        ],
        "Wizard": [
            "Arcane master",
            "Summoning",
            "Ancient spells",
            "Story unlock"
        ],
        "Swordsman": [
            "Sword master",
            "Blade Style",
            "Close Range",
            "Battlepass unlock"
        ]
    }

    while True:
        dt = clock.get_time()
        current_time = pygame.time.get_ticks()
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

        current_character_name = available_characters[current_char_index]

        # Animation cycling
        if current_time - last_animation_change_time >= animation_change_interval:
            current_animation_cycle_idx = (current_animation_cycle_idx + 1) % len(animation_cycle_actions)
            current_character_anim_action = animation_cycle_actions[current_animation_cycle_idx]
            current_character_anim_idx = 0
            current_character_anim_timer = 0
            last_animation_change_time = current_time

        # Update animation frame
        current_character_anim_timer += dt
        
        character_animations = animation_cache.get(current_character_name, {})
        frames_for_current_action = character_animations.get(current_character_anim_action, [])

        if not frames_for_current_action:
            current_character_anim_action = "Idle"
            frames_for_current_action = character_animations.get("Idle", [])
            if not frames_for_current_action:
                current_character_anim_idx = 0
                current_character_anim_timer = 0
            
        if frames_for_current_action:
            delay = character_frame_counts.get(current_character_name, {}).get(current_character_anim_action, 160)
            if current_character_anim_timer >= delay:
                current_character_anim_timer = 0
                current_character_anim_idx = (current_character_anim_idx + 1) % len(frames_for_current_action)
        else:
            current_character_anim_idx = 0

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()  # Stop music when exiting
                    return
                if event.key == pygame.K_LEFT and current_char_index > 0:
                    current_char_index -= 1
                    current_character_anim_action = "Idle"
                    current_character_anim_idx = 0
                    current_character_anim_timer = 0
                    current_animation_cycle_idx = 0
                    last_animation_change_time = current_time
                if event.key == pygame.K_RIGHT and current_char_index < max_char_index:
                    current_char_index += 1
                    current_character_anim_action = "Idle"
                    current_character_anim_idx = 0
                    current_character_anim_timer = 0
                    current_animation_cycle_idx = 0
                    last_animation_change_time = current_time
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    pygame.mixer.music.stop()  # Stop music when back button is clicked
                    return
                elif prev_button.collidepoint((vmx, vmy)) and current_char_index > 0:
                    current_char_index -= 1
                    current_character_anim_action = "Idle"
                    current_character_anim_idx = 0
                    current_character_anim_timer = 0
                    current_animation_cycle_idx = 0
                    last_animation_change_time = current_time
                elif next_button.collidepoint((vmx, vmy)) and current_char_index < max_char_index:
                    current_char_index += 1
                    current_character_anim_action = "Idle"
                    current_character_anim_idx = 0
                    current_character_anim_timer = 0
                    current_animation_cycle_idx = 0
                    last_animation_change_time = current_time

        # Drawing
        virtual_surface.blit(background_image, (0, 0))

        # Title
        title_text = title_font.render("Character Gallery", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))

        # Character box
        char_box_rect = pygame.Rect(VIRTUAL_W // 2 - 300, 120, 600, 400)
        pygame.draw.rect(virtual_surface, (40, 40, 80), char_box_rect, border_radius=15)
        pygame.draw.rect(virtual_surface, BUTTON_COLOR, char_box_rect, 3, border_radius=15)

        # Character name
        display_name = current_character_name.replace("_", " ")
        name_text = title_font.render(display_name, True, WHITE)
        virtual_surface.blit(name_text, name_text.get_rect(center=(char_box_rect.centerx, char_box_rect.y + 40)))

        # Character sprite
        sprite_display_rect = pygame.Rect(char_box_rect.x + 50, char_box_rect.y + 100, 200, 200)
        current_frames = animation_cache.get(current_character_name, {}).get(current_character_anim_action, [])
        
        if current_frames:
            sprite = pygame.transform.scale(current_frames[current_character_anim_idx], (200, 200))
            virtual_surface.blit(sprite, sprite_display_rect.topleft)
        else:
            placeholder = pygame.Surface((200, 200))
            placeholder.fill((100, 100, 100))
            text_missing = small_font.render("No Sprite", True, WHITE)
            placeholder.blit(text_missing, text_missing.get_rect(center=(100, 100)))
            virtual_surface.blit(placeholder, sprite_display_rect.topleft)

        # Character description
        desc_title = button_font.render("Description:", True, SELECTED_COLOR)
        virtual_surface.blit(desc_title, (char_box_rect.x + 280, char_box_rect.y + 100))

        description_lines = manual_character_descriptions.get(current_character_name, [
            "No description",
            "Basic fighter"
        ])
        
        for i, line in enumerate(description_lines[:4]):
            desc_text = small_font.render(line, True, TEXT_COLOR)
            virtual_surface.blit(desc_text, (char_box_rect.x + 280, char_box_rect.y + 140 + i * 20))

        # Damage stats
        stats_title = button_font.render("Damage Stats:", True, SELECTED_COLOR)
        virtual_surface.blit(stats_title, (char_box_rect.x + 280, char_box_rect.y + 280))

        char_dmg = character_damage.get(current_character_name, {})
        attack_types = ["Attack_1", "Attack_2", "Attack_3"]
        for i, atk_type in enumerate(attack_types):
            damage_value = char_dmg.get(atk_type, 0)
            stat_text = small_font.render(f"{atk_type.replace('_', ' ')}: {damage_value}", True, TEXT_COLOR)
            virtual_surface.blit(stat_text, (char_box_rect.x + 280, char_box_rect.y + 320 + i * 20))

        # Page indicator
        page_text = small_font.render(f"Character {current_char_index + 1} / {max_char_index + 1}", True, WHITE)
        virtual_surface.blit(page_text, page_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 50)))

        # Navigation buttons
        # Back button
        pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))

        # Previous button
        if current_char_index > 0:
            prev_button_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.circle(virtual_surface, prev_button_color, prev_button.center, prev_button.width // 2)
            if prev_icon:
                virtual_surface.blit(prev_icon, prev_icon.get_rect(center=prev_button.center))
            else:
                prev_text_fallback = button_font.render("◀", True, WHITE)
                virtual_surface.blit(prev_text_fallback, prev_text_fallback.get_rect(center=prev_button.center))

        # Next button
        if current_char_index < max_char_index:
            next_button_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.circle(virtual_surface, next_button_color, next_button.center, next_button.width // 2)
            if next_icon:
                virtual_surface.blit(next_icon, next_icon.get_rect(center=next_button.center))
            else:
                next_text_fallback = button_font.render("▶", True, WHITE)
                virtual_surface.blit(next_text_fallback, next_text_fallback.get_rect(center=next_button.center))

        draw_scaled_centered()
        clock.tick(60)
        
necromancer_frame_counts = {
    "Attack_1": 47,
    "Attack_2": 20,
    "Attack_3": 47,
    "Dead": 52,
    "Hurt": 9,
    "Idle": 50,
    "Jump": 12,
    "Run": 10,
    "Shield": 12,
    "Walk": 10
}

# Di bagian atas file, setelah character_frame_counts
character_frame_delays = {}

# Frame delays for Necromancer (very fast animations)
necromancer_frame_delays = {
    "Attack_1": 1,  # Very fast attack (30ms per frame)
    "Attack_2": 1,   # Super fast special attack (25ms per frame)
    "Attack_3": 1,   # Fast heavy attack (35ms per frame)
    "Dead": 1,       # Normal death animation (80ms per frame)
    "Hurt": 1,       # Fast hurt reaction (40ms per frame)
    "Idle": 1,       # Normal idle speed (60ms per frame)
    "Jump": 1,       # Fast jump (30ms per frame)
    "Run": 1,        # Very fast running (25ms per frame)
    "Shield": 1,     # Fast shield (50ms per frame)
    "Walk": 1        # Fast walking (40ms per frame)
}

character_frame_counts["Necromancer"] = necromancer_frame_counts
character_frame_delays["Necromancer"] = necromancer_frame_delays  # Add this line
character_damage["Necromancer"] = {"Attack_1": 40, "Attack_2": 80, "Attack_3": 140}
character_ranges["Necromancer"] = 120

def character_fusion():
    print("Starting Character Fusion System...")
    
    # Load required data
    try:
        character_data = load_character_data()
        owned_characters = character_data["owned_characters"][:]
    except:
        character_data = {"owned_characters": ["Samurai", "Soldier", "Magician"]}
        owned_characters = character_data["owned_characters"][:]
    
    try:
        dungeon_data = load_dungeon_data()
    except:
        dungeon_data = {"tengu_feathers": 0, "battle_count": 0, "last_reset": datetime.now().isoformat(), "inventory": [], "stamina": 100, "last_stamina_regen": datetime.now().isoformat()}
    
    # Load and play fusion background music
    try:
        pygame.mixer.music.load("assets/fusionbg.mp3")
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1, 0.0)
    except Exception as e:
        print(f"Could not load fusion music: {e}")
    
    # Load fusion background
    fusion_bg = None
    try:
        fusion_bg_img = pygame.image.load("assets/fusionbg.png").convert()
        fusion_bg = pygame.transform.scale(fusion_bg_img, (VIRTUAL_W, VIRTUAL_H))
        print("Fusion background loaded successfully")
    except Exception as e:
        print(f"Could not load fusion background: {e}")
        # Create fallback gradient background
        fusion_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        for y in range(VIRTUAL_H):
            color_value = int(30 + (y / VIRTUAL_H) * 20)
            color = (color_value, color_value, color_value + 10)
            pygame.draw.line(fusion_bg, color, (0, y), (VIRTUAL_W, y))
        
    # Colors
    WHITE = (255, 255, 255)
    GRAY = (150, 150, 150)
    DARK_GRAY = (80, 80, 80)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (70, 130, 180)
    HOVER_BLUE = (100, 150, 255)
    GOLD = (255, 215, 0)
    BG_COLOR = (30, 30, 60)
    BOX_COLOR = (50, 50, 80)
    SELECTED_COLOR = (0, 255, 100)
    PURPLE = (128, 0, 128)
    HOVER_PURPLE = (160, 100, 160)
    
    # Fonts
    title_font = pygame.font.SysFont("Verdana", 28, bold=True)
    button_font = pygame.font.SysFont("Verdana", 16, bold=True)
    small_font = pygame.font.SysFont("Verdana", 14)
    popup_font = pygame.font.SysFont("Verdana", 20, bold=True)
    
    # Load tengu feather icon
    tengu_feather_icon = None
    tengu_feather_large = None
    try:
        tengu_feather_img = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
        tengu_feather_icon = pygame.transform.scale(tengu_feather_img, (25, 25))
        tengu_feather_large = pygame.transform.scale(tengu_feather_img, (80, 80))  # For fusion box
        print("Tengu feather icons loaded successfully")
    except Exception as e:
        print(f"Could not load tengu feather icon: {e}")
        # Create fallback icon
        tengu_feather_icon = pygame.Surface((25, 25), pygame.SRCALPHA)
        pygame.draw.ellipse(tengu_feather_icon, GOLD, pygame.Rect(3, 2, 19, 21))
        pygame.draw.ellipse(tengu_feather_icon, (200, 170, 0), pygame.Rect(5, 4, 15, 17))
        
        tengu_feather_large = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(tengu_feather_large, GOLD, pygame.Rect(10, 5, 60, 70))
        pygame.draw.ellipse(tengu_feather_large, (200, 170, 0), pygame.Rect(15, 10, 50, 60))
    
    # Animation system for characters
    class CharacterAnimation:
        def __init__(self, character_name):
            self.character_name = character_name
            self.animations = {}
            self.current_animation = "Idle"
            self.current_frame = 0
            self.frame_timer = 0
            self.frame_delay = 100
            self.loop = True
            self.load_animations()
        
        def load_animations(self):
            try:
                if self.character_name == "Necromancer":
                    frame_counts = necromancer_frame_counts
                elif self.character_name == "Wizard":
                    frame_counts = wizard_frame_counts
                else:
                    frame_counts = character_frame_counts[self.character_name]
                
                for anim_name, frame_count in frame_counts.items():
                    sheet_path = f"assets/{self.character_name}/{anim_name}.png"
                    sheet = pygame.image.load(sheet_path).convert_alpha()
                    frame_width = sheet.get_width() // frame_count
                    frame_height = sheet.get_height()
                    
                    frames = []
                    for i in range(frame_count):
                        frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                        frame = sheet.subsurface(frame_rect)
                        scaled_frame = pygame.transform.scale(frame, (120, 120))
                        frames.append(scaled_frame)
                    
                    self.animations[anim_name] = frames
                    print(f"Loaded {self.character_name} {anim_name}: {frame_count} frames")
            except Exception as e:
                print(f"Error loading {self.character_name} animations: {e}")
                # Create placeholder
                placeholder = pygame.Surface((120, 120), pygame.SRCALPHA)
                placeholder.fill(DARK_GRAY)
                pygame.draw.rect(placeholder, WHITE, placeholder.get_rect(), 2)
                text = pygame.font.SysFont("Arial", 12).render(self.character_name, True, WHITE)
                placeholder.blit(text, text.get_rect(center=(60, 60)))
                self.animations = {"Idle": [placeholder] * 50, "Attack_2": [placeholder] * 20}
        
        def set_animation(self, anim_name, loop=True):
            if anim_name in self.animations and anim_name != self.current_animation:
                self.current_animation = anim_name
                self.current_frame = 0
                self.frame_timer = 0
                self.loop = loop
        
        def update(self, dt):
            if self.current_animation not in self.animations:
                return False
            
            self.frame_timer += dt
            if self.frame_timer >= self.frame_delay:
                self.frame_timer = 0
                self.current_frame += 1
                
                if self.current_frame >= len(self.animations[self.current_animation]):
                    if not self.loop:
                        return True
                    self.current_frame = 0
            
            return False
        
        def get_current_frame(self):
            if self.current_animation in self.animations:
                frames = self.animations[self.current_animation]
                if frames and 0 <= self.current_frame < len(frames):
                    return frames[self.current_frame]
            return None
    
    # Initialize character animations
    necromancer_anim = CharacterAnimation("Necromancer")
    magician_anim = CharacterAnimation("Magician")
    wizard_anim = CharacterAnimation("Wizard")
    
    # UI Elements - Better spacing
    back_button = pygame.Rect(40, 40, 80, 40)
    inventory_button = pygame.Rect(VIRTUAL_W - 140, 40, 100, 40)
    status_button = pygame.Rect(VIRTUAL_W - 140, 95, 100, 40)
    
    # Fusion boxes - Better layout
    box_width, box_height = 140, 180
    total_width = 3 * box_width + 2 * 50  # 50px gap between boxes
    start_x = (VIRTUAL_W - total_width) // 2
    
    magician_box = pygame.Rect(start_x, 340, box_width, box_height)
    wizard_box = pygame.Rect(start_x + box_width + 50, 340, box_width, box_height)
    feather_box = pygame.Rect(start_x + 2 * (box_width + 50), 340, box_width, box_height)
    
    craft_button = pygame.Rect(VIRTUAL_W//2 - 80, 540, 160, 50)
    
    # Fusion state
    fusion_state = {
        "magician_selected": False,
        "wizard_selected": False,
        "feathers_selected": False
    }
    
    # Message system
    message = ""
    message_color = WHITE
    message_timer = 0
    show_inventory_popup = False
    show_status_popup = False
    
    # Character insertion popup system
    character_popup_active = False
    character_popup_type = ""  # "magician" or "wizard"
    character_popup_stage = "animating"  # "animating" or "completed"
    
    # Popup system for crafting result
    popup_active = False
    popup_stage = "crafting"
    
    # Load character previews (static for performance)
    character_previews = {}
    
    def load_character_preview(char_name):
        if char_name in character_previews:
            return character_previews[char_name]
        
        try:
            if char_name == "Wizard":
                frame_counts = wizard_frame_counts
            else:
                frame_counts = character_frame_counts[char_name]
            
            idle_path = f"assets/{char_name}/Idle.png"
            idle_sheet = pygame.image.load(idle_path).convert_alpha()
            frame_count = frame_counts["Idle"]
            frame_width = idle_sheet.get_width() // frame_count
            
            first_frame = idle_sheet.subsurface(pygame.Rect(0, 0, frame_width, idle_sheet.get_height()))
            preview = pygame.transform.scale(first_frame, (90, 90))
            character_previews[char_name] = preview
            return preview
        except:
            placeholder = pygame.Surface((90, 90), pygame.SRCALPHA)
            placeholder.fill(GRAY)
            pygame.draw.rect(placeholder, WHITE, placeholder.get_rect(), 2)
            font = pygame.font.SysFont("Arial", 10)
            text = font.render(char_name, True, WHITE)
            placeholder.blit(text, text.get_rect(center=(45, 45)))
            character_previews[char_name] = placeholder
            return placeholder
    
    def show_message(msg, color=WHITE, duration=3000):
        nonlocal message, message_color, message_timer
        message = msg
        message_color = color
        message_timer = pygame.time.get_ticks()
    
    def draw_fusion_box(box_rect, title, selected, preview_surface=None, hover=False):
        # Semi-transparent box background
        box_surface = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        
        if selected:
            box_color = (60, 120, 60, 200)
            border_color = GREEN
        elif hover:
            box_color = (60, 60, 100, 200)
            border_color = HOVER_BLUE
        else:
            box_color = (50, 50, 80, 180)
            border_color = GRAY
        
        # Draw box with transparency
        pygame.draw.rect(box_surface, box_color, (0, 0, box_rect.width, box_rect.height), border_radius=8)
        virtual_surface.blit(box_surface, box_rect)
        pygame.draw.rect(virtual_surface, border_color, box_rect, 2, border_radius=8)
        
        # Title
        title_surf = small_font.render(title, True, WHITE)
        title_rect = title_surf.get_rect(centerx=box_rect.centerx, y=box_rect.y + 10)
        virtual_surface.blit(title_surf, title_rect)
        
        if preview_surface:
            # Show preview
            preview_rect = preview_surface.get_rect(center=(box_rect.centerx, box_rect.centery + 15))
            virtual_surface.blit(preview_surface, preview_rect)
        else:
            # Show plus icon
            plus_size = 40
            plus_rect = pygame.Rect(0, 0, plus_size, plus_size)
            plus_rect.center = (box_rect.centerx, box_rect.centery + 15)
            
            pygame.draw.rect(virtual_surface, GRAY if not hover else WHITE, plus_rect, border_radius=4)
            
            # Plus symbol
            line_thickness = 4
            pygame.draw.line(virtual_surface, BOX_COLOR, 
                           (plus_rect.centerx - 10, plus_rect.centery),
                           (plus_rect.centerx + 10, plus_rect.centery), line_thickness)
            pygame.draw.line(virtual_surface, BOX_COLOR,
                           (plus_rect.centerx, plus_rect.centery - 10),
                           (plus_rect.centerx, plus_rect.centery + 10), line_thickness)
    
    def draw_character_popup():
        """Draw character insertion animation popup"""
        if not character_popup_active:
            return None
        
        # Semi-transparent overlay
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        virtual_surface.blit(overlay, (0, 0))
        
        # Popup box
        popup_w, popup_h = 350, 280
        popup_rect = pygame.Rect((VIRTUAL_W - popup_w)//2, (VIRTUAL_H - popup_h)//2, popup_w, popup_h)
        
        # Popup background
        popup_surface = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        pygame.draw.rect(popup_surface, (40, 40, 80, 240), (0, 0, popup_w, popup_h), border_radius=15)
        virtual_surface.blit(popup_surface, popup_rect)
        pygame.draw.rect(virtual_surface, GOLD, popup_rect, 3, border_radius=15)
        
        # Character name
        char_name = character_popup_type.upper()
        
        if character_popup_stage == "animating":
            # Show animation
            title_surf = popup_font.render(f"PREPARING {char_name}", True, GOLD)
            title_rect = title_surf.get_rect(centerx=popup_rect.centerx, y=popup_rect.y + 25)
            virtual_surface.blit(title_surf, title_rect)
            
            # Show character Attack_2 animation
            if character_popup_type == "magician":
                char_frame = magician_anim.get_current_frame()
            elif character_popup_type == "wizard":
                char_frame = wizard_anim.get_current_frame()
            
            if char_frame:
                frame_rect = char_frame.get_rect(center=(popup_rect.centerx, popup_rect.centery))
                virtual_surface.blit(char_frame, frame_rect)
            
            # Progress text
            progress_surf = small_font.render("Animation in progress...", True, WHITE)
            progress_rect = progress_surf.get_rect(centerx=popup_rect.centerx, y=popup_rect.bottom - 50)
            virtual_surface.blit(progress_surf, progress_rect)
            
        elif character_popup_stage == "completed":
            # Show completion screen
            title_surf = popup_font.render(f"{char_name} READY!", True, GREEN)
            title_rect = title_surf.get_rect(centerx=popup_rect.centerx, y=popup_rect.y + 25)
            virtual_surface.blit(title_surf, title_rect)
            
            # Show character idle frame
            if character_popup_type == "magician":
                char_frame = magician_anim.get_current_frame()
            elif character_popup_type == "wizard":
                char_frame = wizard_anim.get_current_frame()
            
            if char_frame:
                frame_rect = char_frame.get_rect(center=(popup_rect.centerx, popup_rect.centery - 10))
                virtual_surface.blit(char_frame, frame_rect)
            
            # INSERT button
            insert_button = pygame.Rect(popup_rect.centerx - 60, popup_rect.bottom - 70, 120, 40)
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            insert_hover = insert_button.collidepoint((vmx, vmy))
            insert_color = HOVER_BLUE if insert_hover else GREEN
            
            pygame.draw.rect(virtual_surface, insert_color, insert_button, border_radius=8)
            insert_surf = button_font.render("INSERT", True, WHITE)
            insert_rect = insert_surf.get_rect(center=insert_button.center)
            virtual_surface.blit(insert_surf, insert_rect)
            
            return insert_button
        
        return None
    
    def draw_popup():
        """Draw main crafting popup"""
        if not popup_active:
            return None
        
        # Semi-transparent overlay
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        virtual_surface.blit(overlay, (0, 0))
        
        # Popup box
        popup_w, popup_h = 400, 320
        popup_rect = pygame.Rect((VIRTUAL_W - popup_w)//2, (VIRTUAL_H - popup_h)//2, popup_w, popup_h)
        
        # Popup background
        popup_surface = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        pygame.draw.rect(popup_surface, (40, 40, 80, 240), (0, 0, popup_w, popup_h), border_radius=15)
        virtual_surface.blit(popup_surface, popup_rect)
        pygame.draw.rect(virtual_surface, GOLD, popup_rect, 3, border_radius=15)
        
        if popup_stage == "crafting":
            # Show crafting animation
            title_surf = popup_font.render("CRAFTING NECROMANCER", True, GOLD)
            title_rect = title_surf.get_rect(centerx=popup_rect.centerx, y=popup_rect.y + 25)
            virtual_surface.blit(title_surf, title_rect)
            
            # Show Necromancer Attack_2 animation
            necromancer_frame = necromancer_anim.get_current_frame()
            if necromancer_frame:
                popup_frame = pygame.transform.scale(necromancer_frame, (150, 150))
                frame_rect = popup_frame.get_rect(center=(popup_rect.centerx, popup_rect.centery))
                virtual_surface.blit(popup_frame, frame_rect)
            
            # Progress text
            progress_surf = small_font.render("Fusion in progress...", True, WHITE)
            progress_rect = progress_surf.get_rect(centerx=popup_rect.centerx, y=popup_rect.bottom - 50)
            virtual_surface.blit(progress_surf, progress_rect)
            
        elif popup_stage == "completed":
            # Show completion screen
            title_surf = popup_font.render("NECROMANCER CREATED!", True, GREEN)
            title_rect = title_surf.get_rect(centerx=popup_rect.centerx, y=popup_rect.y + 25)
            virtual_surface.blit(title_surf, title_rect)
            
            # Show final Necromancer frame
            necromancer_frame = necromancer_anim.get_current_frame()
            if necromancer_frame:
                popup_frame = pygame.transform.scale(necromancer_frame, (130, 130))
                frame_rect = popup_frame.get_rect(center=(popup_rect.centerx, popup_rect.centery - 10))
                virtual_surface.blit(popup_frame, frame_rect)
            
            # GET button
            get_button = pygame.Rect(popup_rect.centerx - 60, popup_rect.bottom - 70, 120, 40)
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            get_hover = get_button.collidepoint((vmx, vmy))
            get_color = HOVER_BLUE if get_hover else GREEN
            
            pygame.draw.rect(virtual_surface, get_color, get_button, border_radius=8)
            get_surf = button_font.render("GET", True, WHITE)
            get_rect = get_surf.get_rect(center=get_button.center)
            virtual_surface.blit(get_surf, get_rect)
            
            return get_button
        
        return None
    
    def draw_status_popup():
        """Draw status popup with requirements"""
        if not show_status_popup:
            return
        
        popup_w, popup_h = 480, 300
        popup_x = status_button.x - popup_w + status_button.width
        popup_y = status_button.bottom + 15
        
        # Ensure popup stays within screen bounds
        if popup_x < 10:
            popup_x = 10
        if popup_x + popup_w > VIRTUAL_W - 10:
            popup_x = VIRTUAL_W - popup_w - 10
        if popup_y + popup_h > VIRTUAL_H - 10:
            popup_y = status_button.y - popup_h - 15
        
        popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
        
        # Popup background
        popup_surface = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        pygame.draw.rect(popup_surface, (40, 40, 80, 230), (0, 0, popup_w, popup_h), border_radius=10)
        virtual_surface.blit(popup_surface, popup_rect)
        pygame.draw.rect(virtual_surface, PURPLE, popup_rect, 3, border_radius=10)
        
        # Title
        title_surf = button_font.render("FUSION STATUS", True, PURPLE)
        title_rect = title_surf.get_rect(centerx=popup_rect.centerx, y=popup_y + 20)
        virtual_surface.blit(title_surf, title_rect)
        
        # Draw dividing line
        line_y = popup_y + 50
        pygame.draw.line(virtual_surface, GRAY, (popup_x + 20, line_y), (popup_x + popup_w - 20, line_y), 2)
        
        # Requirements
        req_x = popup_x + 25
        req_y = popup_y + 70
        req_title = small_font.render("Requirements:", True, WHITE)
        virtual_surface.blit(req_title, (req_x, req_y))
        
        req_items = [
            (f"Magician: {'READY' if fusion_state['magician_selected'] else 'NEEDED'}", 
             GREEN if fusion_state['magician_selected'] else RED),
            (f"Wizard: {'READY' if fusion_state['wizard_selected'] else 'NEEDED'}", 
             GREEN if fusion_state['wizard_selected'] else RED),
            (f"250 Tengu Feathers: {'READY' if fusion_state['feathers_selected'] else 'NEEDED'}", 
             GREEN if fusion_state['feathers_selected'] else RED)
        ]
        
        for i, (text, color) in enumerate(req_items):
            req_surf = small_font.render(text, True, color)
            virtual_surface.blit(req_surf, (req_x + 15, req_y + 30 + i * 25))
        
        # Character Status
        status_x = popup_x + 250
        status_y = popup_y + 70
        status_title = small_font.render("Character Status:", True, WHITE)
        virtual_surface.blit(status_title, (status_x, status_y))
        
        status_items = [
            f"Total Characters: {len(owned_characters)}",
            f"Magician: {'Owned' if 'Magician' in owned_characters else 'Not Owned'}",
            f"Wizard: {'Owned' if 'Wizard' in owned_characters else 'Not Owned'}",
            f"Necromancer: {'Owned' if 'Necromancer' in owned_characters else 'Not Owned'}"
        ]
        
        for i, text in enumerate(status_items):
            if "Owned" in text and "Not Owned" not in text:
                color = GREEN
            elif "Not Owned" in text:
                color = RED
            else:
                color = WHITE
            
            status_surf = small_font.render(text, True, color)
            virtual_surface.blit(status_surf, (status_x + 15, status_y + 30 + i * 25))
        
        # Overall status
        overall_y = popup_y + popup_h - 70
        pygame.draw.line(virtual_surface, GRAY, (popup_x + 20, overall_y - 15), (popup_x + popup_w - 20, overall_y - 15), 2)
        
        if "Necromancer" in owned_characters:
            overall_text = "STATUS: Necromancer Already Owned"
            overall_color = GREEN
        elif can_craft():
            overall_text = "STATUS: Ready to Craft Necromancer!"
            overall_color = GOLD
        else:
            overall_text = "STATUS: Requirements Not Met"
            overall_color = RED
        
        overall_surf = button_font.render(overall_text, True, overall_color)
        overall_rect = overall_surf.get_rect(centerx=popup_rect.centerx, y=overall_y)
        virtual_surface.blit(overall_surf, overall_rect)
        
        # Close instruction
        close_hint = small_font.render("Click Status button again to close", True, GRAY)
        close_rect = close_hint.get_rect(centerx=popup_rect.centerx, y=popup_y + popup_h - 30)
        virtual_surface.blit(close_hint, close_rect)
    
    def can_craft():
        return (fusion_state["magician_selected"] and 
                fusion_state["wizard_selected"] and 
                fusion_state["feathers_selected"])
    
    # Load click sound
    click_sound = None
    try:
        click_sound = pygame.mixer.Sound("soundeffects/click.mp3")
        click_sound.set_volume(0.7)
    except:
        pass
    
    # Main loop
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.get_time()
        current_time = pygame.time.get_ticks()
        
        # Update animations
        if popup_active and popup_stage == "crafting":
            animation_complete = necromancer_anim.update(dt)
            if animation_complete:
                popup_stage = "completed"
                necromancer_anim.set_animation("Idle", loop=True)
        elif character_popup_active and character_popup_stage == "animating":
            if character_popup_type == "magician":
                anim_complete = magician_anim.update(dt)
            elif character_popup_type == "wizard":
                anim_complete = wizard_anim.update(dt)
            
            if anim_complete:
                character_popup_stage = "completed"
                if character_popup_type == "magician":
                    magician_anim.set_animation("Idle", loop=True)
                elif character_popup_type == "wizard":
                    wizard_anim.set_animation("Idle", loop=True)
        else:
            necromancer_anim.update(dt)
            magician_anim.update(dt)
            wizard_anim.update(dt)
        
        # Get mouse position
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                exit_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Character insertion popup handling
                if character_popup_active:
                    if character_popup_stage == "completed":
                        insert_button = draw_character_popup()
                        if insert_button and insert_button.collidepoint((vmx, vmy)):
                            # Insert character into fusion
                            if character_popup_type == "magician":
                                fusion_state["magician_selected"] = True
                                show_message("Magician inserted for fusion!", GREEN)
                            elif character_popup_type == "wizard":
                                fusion_state["wizard_selected"] = True
                                show_message("Wizard inserted for fusion!", GREEN)
                            
                            character_popup_active = False
                            character_popup_stage = "animating"
                            
                            if click_sound:
                                click_sound.play()
                    continue
                
                # Main crafting popup handling
                if popup_active:
                    if popup_stage == "completed":
                        get_button = draw_popup()
                        if get_button and get_button.collidepoint((vmx, vmy)):
                            # Add Necromancer
                            if "Necromancer" not in character_data["owned_characters"]:
                                character_data["owned_characters"].append("Necromancer")
                                save_character_data(character_data)
                            
                            # Reset fusion state
                            fusion_state = {
                                "magician_selected": False,
                                "wizard_selected": False,
                                "feathers_selected": False
                            }
                            
                            popup_active = False
                            popup_stage = "crafting"
                            show_message("Necromancer added to your collection!", GREEN)
                            
                            if click_sound:
                                click_sound.play()
                    continue
                
                # Back button
                if back_button.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    pygame.mixer.music.stop()
                    return
                
                # Inventory button
                if inventory_button.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    show_inventory_popup = not show_inventory_popup
                    if show_inventory_popup:
                        show_status_popup = False
                
                # Status button
                if status_button.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    show_status_popup = not show_status_popup
                    if show_status_popup:
                        show_inventory_popup = False
                
                # Fusion boxes
                if magician_box.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    
                    if "Magician" in owned_characters:
                        if not fusion_state["magician_selected"]:
                            # Start character animation popup
                            character_popup_active = True
                            character_popup_type = "magician"
                            character_popup_stage = "animating"
                            magician_anim.set_animation("Attack_2", loop=False)
                        else:
                            # Deselect
                            fusion_state["magician_selected"] = False
                            show_message("Magician removed from fusion", WHITE)
                    else:
                        show_message("You don't own the Magician character!", RED)
                
                elif wizard_box.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    
                    if "Wizard" in owned_characters:
                        if not fusion_state["wizard_selected"]:
                            # Start character animation popup
                            character_popup_active = True
                            character_popup_type = "wizard"
                            character_popup_stage = "animating"
                            wizard_anim.set_animation("Attack_2", loop=False)
                        else:
                            # Deselect
                            fusion_state["wizard_selected"] = False
                            show_message("Wizard removed from fusion", WHITE)
                    else:
                        show_message("You don't own the Wizard character!", RED)
                
                elif feather_box.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    
                    if dungeon_data["tengu_feathers"] >= 250:
                        fusion_state["feathers_selected"] = not fusion_state["feathers_selected"]
                        if fusion_state["feathers_selected"]:
                            show_message("250 Tengu Feathers reserved for fusion!", GREEN)
                        else:
                            show_message("Tengu Feathers deselected", WHITE)
                    else:
                        show_message(f"Not enough Tengu Feathers! Need 250, have {dungeon_data['tengu_feathers']}", RED)
                
                # Craft button
                elif craft_button.collidepoint((vmx, vmy)):
                    if click_sound:
                        click_sound.play()
                    
                    if can_craft():
                        if "Necromancer" not in owned_characters:
                            # Consume resources
                            dungeon_data["tengu_feathers"] -= 250
                            save_dungeon_data(dungeon_data)
                            
                            # Start crafting animation
                            popup_active = True
                            popup_stage = "crafting"
                            necromancer_anim.set_animation("Attack_2", loop=False)
                            show_message("Crafting started!", GREEN)
                        else:
                            show_message("You already own Necromancer!", RED)
                    else:
                        missing = []
                        if not fusion_state["magician_selected"]:
                            missing.append("Magician")
                        if not fusion_state["wizard_selected"]:
                            missing.append("Wizard")
                        if not fusion_state["feathers_selected"]:
                            missing.append("250 Tengu Feathers")
                        
                        show_message(f"Missing: {', '.join(missing)}", RED)
        
        # Rendering
        if fusion_bg:
            virtual_surface.blit(fusion_bg, (0, 0))
        else:
            virtual_surface.fill(BG_COLOR)
        
        # Title - moved up slightly
        title_surf = title_font.render("CHARACTER FUSION", True, GOLD)
        title_rect = title_surf.get_rect(center=(VIRTUAL_W // 2, 70))
        
        # Title background
        title_bg_rect = title_rect.inflate(30, 20)
        title_bg_surface = pygame.Surface((title_bg_rect.width, title_bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(title_bg_surface, (0, 0, 0, 150), (0, 0, title_bg_rect.width, title_bg_rect.height), border_radius=10)
        virtual_surface.blit(title_bg_surface, title_bg_rect)
        virtual_surface.blit(title_surf, title_rect)
        
        # Subtitle - updated text and moved up
        subtitle_surf = small_font.render("Combine material to create powerful character", True, WHITE)
        subtitle_rect = subtitle_surf.get_rect(center=(VIRTUAL_W // 2, 95))
        
        # Subtitle background
        subtitle_bg_rect = subtitle_rect.inflate(20, 15)
        subtitle_bg_surface = pygame.Surface((subtitle_bg_rect.width, subtitle_bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(subtitle_bg_surface, (0, 0, 0, 120), (0, 0, subtitle_bg_rect.width, subtitle_bg_rect.height), border_radius=8)
        virtual_surface.blit(subtitle_bg_surface, subtitle_bg_rect)
        virtual_surface.blit(subtitle_surf, subtitle_rect)
        
        # Necromancer preview - moved up significantly
        necromancer_preview_rect = pygame.Rect(VIRTUAL_W//2 - 80, 130, 160, 120)
        
        # Necromancer preview background
        necro_bg_surface = pygame.Surface((160, 120), pygame.SRCALPHA)
        pygame.draw.rect(necro_bg_surface, (60, 40, 80, 200), (0, 0, 160, 120), border_radius=8)
        virtual_surface.blit(necro_bg_surface, necromancer_preview_rect)
        pygame.draw.rect(virtual_surface, GOLD, necromancer_preview_rect, 2, border_radius=8)
        
        necromancer_label = button_font.render("NECROMANCER", True, GOLD)
        label_rect = necromancer_label.get_rect(centerx=necromancer_preview_rect.centerx, y=necromancer_preview_rect.y + 10)
        virtual_surface.blit(necromancer_label, label_rect)
        
        # Show Necromancer animation
        necromancer_frame = necromancer_anim.get_current_frame()
        if necromancer_frame:
            preview_frame = pygame.transform.scale(necromancer_frame, (70, 70))
            frame_rect = preview_frame.get_rect(centerx=necromancer_preview_rect.centerx, y=necromancer_preview_rect.y + 35)
            virtual_surface.blit(preview_frame, frame_rect)
        
        # Result text
        result_text = small_font.render("FUSION RESULT", True, GRAY)
        result_rect = result_text.get_rect(centerx=VIRTUAL_W//2, y=270)
        virtual_surface.blit(result_text, result_rect)
        
        # Separator line
        separator_y = 300
        pygame.draw.line(virtual_surface, GRAY, (100, separator_y), (VIRTUAL_W - 100, separator_y), 2)
        
        # Materials text
        materials_text = small_font.render("REQUIRED MATERIALS", True, WHITE)
        materials_rect = materials_text.get_rect(centerx=VIRTUAL_W//2, y=320)
        virtual_surface.blit(materials_text, materials_rect)
        
        # Fusion boxes - better spaced layout
        magician_hover = magician_box.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        wizard_hover = wizard_box.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        feather_hover = feather_box.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        
        # Draw Magician box
        magician_preview = None
        if fusion_state["magician_selected"] and "Magician" in owned_characters:
            magician_preview = load_character_preview("Magician")
        
        draw_fusion_box(magician_box, "MAGICIAN", fusion_state["magician_selected"], 
                       magician_preview, magician_hover)
        
        # Draw Wizard box
        wizard_preview = None
        if fusion_state["wizard_selected"] and "Wizard" in owned_characters:
            wizard_preview = load_character_preview("Wizard")
        
        draw_fusion_box(wizard_box, "WIZARD", fusion_state["wizard_selected"],
                       wizard_preview, wizard_hover)
        
        # Draw Feather box
        feather_preview = None
        if fusion_state["feathers_selected"] and dungeon_data["tengu_feathers"] >= 250:
            feather_display = pygame.Surface((90, 90), pygame.SRCALPHA)
            
            if tengu_feather_large:
                feather_rect = tengu_feather_large.get_rect(center=(45, 35))
                feather_display.blit(tengu_feather_large, feather_rect)
            
            feather_count_text = pygame.font.SysFont("Verdana", 14, bold=True).render("250", True, GOLD)
            count_rect = feather_count_text.get_rect(center=(45, 70))
            feather_display.blit(feather_count_text, count_rect)
            
            feather_preview = feather_display
        
        draw_fusion_box(feather_box, "TENGU FEATHERS", fusion_state["feathers_selected"],
                       feather_preview, feather_hover)
        
        # Craft button
        craft_hover = craft_button.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        craft_enabled = can_craft() and "Necromancer" not in owned_characters
        
        craft_bg_surface = pygame.Surface((craft_button.width, craft_button.height), pygame.SRCALPHA)
        
        if craft_enabled:
            craft_color = (100, 200, 100, 220) if craft_hover else (0, 180, 0, 200)
            craft_text_color = WHITE
        else:
            craft_color = (80, 80, 80, 180)
            craft_text_color = GRAY
        
        pygame.draw.rect(craft_bg_surface, craft_color, (0, 0, craft_button.width, craft_button.height), border_radius=10)
        virtual_surface.blit(craft_bg_surface, craft_button)
        pygame.draw.rect(virtual_surface, WHITE if craft_enabled else GRAY, craft_button, 3, border_radius=10)
        
        craft_text = "CRAFT" if "Necromancer" not in owned_characters else "ALREADY OWNED"
        craft_surf = button_font.render(craft_text, True, craft_text_color)
        craft_rect = craft_surf.get_rect(center=craft_button.center)
        virtual_surface.blit(craft_surf, craft_rect)
        
        # Back button
        back_hover = back_button.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        back_color = (100, 150, 255, 200) if back_hover else (70, 130, 180, 180)
        
        back_bg_surface = pygame.Surface((back_button.width, back_button.height), pygame.SRCALPHA)
        pygame.draw.rect(back_bg_surface, back_color, (0, 0, back_button.width, back_button.height), border_radius=8)
        virtual_surface.blit(back_bg_surface, back_button)
        pygame.draw.rect(virtual_surface, WHITE, back_button, 2, border_radius=8)
        
        back_surf = small_font.render("Back", True, WHITE)
        back_rect = back_surf.get_rect(center=back_button.center)
        virtual_surface.blit(back_surf, back_rect)
        
        # Inventory button
        inv_hover = inventory_button.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        
        if show_inventory_popup:
            inv_color = (0, 200, 0, 200) if not inv_hover else (100, 255, 100, 220)
        else:
            inv_color = (100, 150, 255, 200) if inv_hover else (70, 130, 180, 180)
        
        inv_bg_surface = pygame.Surface((inventory_button.width, inventory_button.height), pygame.SRCALPHA)
        pygame.draw.rect(inv_bg_surface, inv_color, (0, 0, inventory_button.width, inventory_button.height), border_radius=8)
        virtual_surface.blit(inv_bg_surface, inventory_button)
        pygame.draw.rect(virtual_surface, WHITE, inventory_button, 2, border_radius=8)
        
        # Draw tengu feather icon in button
        if tengu_feather_icon:
            icon_rect = tengu_feather_icon.get_rect(center=(inventory_button.x + 22, inventory_button.centery))
            virtual_surface.blit(tengu_feather_icon, icon_rect)
        
        inv_text = "Close" if show_inventory_popup else "Inventory"
        inv_surf = small_font.render(inv_text, True, WHITE)
        inv_rect = inv_surf.get_rect(center=(inventory_button.x + 68, inventory_button.centery))
        virtual_surface.blit(inv_surf, inv_rect)
        
        # Status button
        status_hover = status_button.collidepoint((vmx, vmy)) and not popup_active and not character_popup_active
        
        if show_status_popup:
            status_color = (0, 200, 0, 200) if not status_hover else (100, 255, 100, 220)
        else:
            status_color = (160, 100, 160, 200) if status_hover else (128, 0, 128, 180)
        
        status_bg_surface = pygame.Surface((status_button.width, status_button.height), pygame.SRCALPHA)
        pygame.draw.rect(status_bg_surface, status_color, (0, 0, status_button.width, status_button.height), border_radius=8)
        virtual_surface.blit(status_bg_surface, status_button)
        pygame.draw.rect(virtual_surface, WHITE, status_button, 2, border_radius=8)
        
        # Draw status icon (mini chart/bars)
        status_icon_rect = pygame.Rect(status_button.x + 18, status_button.centery - 8, 16, 16)
        for i in range(3):
            bar_height = (i + 1) * 4
            bar_rect = pygame.Rect(status_icon_rect.x + i * 4, status_icon_rect.bottom - bar_height, 3, bar_height)
            pygame.draw.rect(virtual_surface, WHITE, bar_rect)
        
        status_text = "Close" if show_status_popup else "Status"
        status_surf = small_font.render(status_text, True, WHITE)
        status_rect = status_surf.get_rect(center=(status_button.x + 68, status_button.centery))
        virtual_surface.blit(status_surf, status_rect)
        
        # Show inventory popup
        if show_inventory_popup:
            popup_w, popup_h = 280, 140
            popup_x = inventory_button.x - popup_w + inventory_button.width
            popup_y = inventory_button.bottom + 15
            
            # Ensure popup stays within screen bounds
            if popup_x < 10:
                popup_x = 10
            if popup_x + popup_w > VIRTUAL_W - 10:
                popup_x = VIRTUAL_W - popup_w - 10
            if popup_y + popup_h > VIRTUAL_H - 10:
                popup_y = inventory_button.y - popup_h - 15
            
            popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
            
            # Inventory popup background
            inv_popup_surface = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
            pygame.draw.rect(inv_popup_surface, (40, 40, 80, 240), (0, 0, popup_w, popup_h), border_radius=10)
            virtual_surface.blit(inv_popup_surface, popup_rect)
            pygame.draw.rect(virtual_surface, GOLD, popup_rect, 3, border_radius=10)
            
            # Title
            inv_title = small_font.render("Current Inventory:", True, WHITE)
            virtual_surface.blit(inv_title, (popup_x + 20, popup_y + 20))
            
            # Feather count with icon
            if tengu_feather_icon:
                feather_rect = tengu_feather_icon.get_rect(x=popup_x + 20, y=popup_y + 50)
                virtual_surface.blit(tengu_feather_icon, feather_rect)
            
            feather_count_text = button_font.render(f"{dungeon_data['tengu_feathers']}", True, GOLD)
            virtual_surface.blit(feather_count_text, (popup_x + 55, popup_y + 50))
            
            feather_label = small_font.render("Tengu Feathers", True, WHITE)
            virtual_surface.blit(feather_label, (popup_x + 20, popup_y + 80))
            
            # Show requirement status
            req_text = f"Need 250 for fusion ({dungeon_data['tengu_feathers']}/250)"
            req_color = GREEN if dungeon_data['tengu_feathers'] >= 250 else RED
            req_surf = small_font.render(req_text, True, req_color)
            virtual_surface.blit(req_surf, (popup_x + 20, popup_y + 100))
            
            # Close instruction
            close_hint = small_font.render("Click Inventory again to close", True, GRAY)
            virtual_surface.blit(close_hint, (popup_x + 20, popup_y + 120))
        
        # Draw message
        if message and current_time - message_timer < 3000:
            msg_surf = button_font.render(message, True, message_color)
            msg_rect = msg_surf.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 40))
            
            # Message background
            bg_rect = msg_rect.inflate(30, 20)
            msg_bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(msg_bg_surface, (0, 0, 0, 200), (0, 0, bg_rect.width, bg_rect.height), border_radius=10)
            virtual_surface.blit(msg_bg_surface, bg_rect)
            pygame.draw.rect(virtual_surface, message_color, bg_rect, 2, border_radius=10)
            
            virtual_surface.blit(msg_surf, msg_rect)
        
        # Draw popups (status popup first, then character popup, then crafting popup on top)
        draw_status_popup()
        
        if character_popup_active:
            draw_character_popup()
        
        if popup_active:
            draw_popup()
        
        # Final render
        draw_scaled_centered()
        clock.tick(60)

# Supporting functions remain the same
def check_fusion_requirements():
    """
    Check if player meets fusion requirements.
    Returns dict with requirement status.
    """
    try:
        character_data = load_character_data()
        owned_characters = character_data["owned_characters"][:]
    except:
        owned_characters = []
    
    try:
        dungeon_data = load_dungeon_data()
        tengu_feathers = dungeon_data.get("tengu_feathers", 0)
    except:
        tengu_feathers = 0
    
    return {
        "has_magician": "Magician" in owned_characters,
        "has_wizard": "Wizard" in owned_characters,
        "has_enough_feathers": tengu_feathers >= 250,
        "current_feathers": tengu_feathers,
        "can_fusion": ("Magician" in owned_characters and 
                      "Wizard" in owned_characters and 
                      tengu_feathers >= 250),
        "has_necromancer": "Necromancer" in owned_characters
    }

def get_fusion_progress_text():
    """
    Get text describing fusion progress for UI elements.
    """
    requirements = check_fusion_requirements()
    
    if requirements["has_necromancer"]:
        return "Necromancer: Already Owned", (0, 255, 0)
    
    if requirements["can_fusion"]:
        return "Necromancer: Ready to Craft!", (255, 215, 0)
    
    missing = []
    if not requirements["has_magician"]:
        missing.append("Magician")
    if not requirements["has_wizard"]:
        missing.append("Wizard")
    if not requirements["has_enough_feathers"]:
        missing.append(f"Feathers ({requirements['current_feathers']}/250)")
    
    return f"Missing: {', '.join(missing)}", (255, 100, 100)

def show_fusion_notification():
    """
    Show notification when fusion becomes available.
    Call this when requirements are met.
    """
    requirements = check_fusion_requirements()
    
    if requirements["can_fusion"] and not requirements["has_necromancer"]:
        print("FUSION AVAILABLE: You can now craft Necromancer!")
        return True
    return False

def save_fusion_progress(fusion_state):
    """
    Save fusion progress to file (optional feature).
    """
    try:
        import json
        with open("fusion_progress.json", "w") as f:
            json.dump(fusion_state, f)
    except:
        pass

def load_fusion_progress():
    """
    Load fusion progress from file (optional feature).
    """
    try:
        import json
        with open("fusion_progress.json", "r") as f:
            return json.load(f)
    except:
        return {
            "magician_selected": False,
            "wizard_selected": False,
            "feathers_selected": False
        }             
                                       
def story_mode():
    character_frame_counts_idle = {
        "Samurai": 6,
        "Soldier": 9,
        "Magician": 8,
        "Graffiti": 7,
        "Kitsune": 8,
        "Kunoichi": 9,
        "Gangster": 13
    }
    
    # CHARACTER UNLOCK REQUIREMENTS
    CHARACTER_UNLOCK_REQUIREMENTS = {
        "Samurai": 0,      # Default unlocked
        "Soldier": 25,     # Unlock at stage 25
        "Magician": 50,    # Unlock at stage 50
        "Graffiti": 75,    # Unlock at stage 75
        "Kitsune": 100,    # Unlock at stage 100
        "Kunoichi": 150,   # Unlock at stage 150
        "Gangster": 250    # Unlock at stage 250
    }
    
    def is_character_unlocked(character, story_data):
        """Check if character is unlocked based on story progress"""
        required_stage = CHARACTER_UNLOCK_REQUIREMENTS.get(character, 0)
        max_completed = max(story_data["completed_stages"]) if story_data["completed_stages"] else 0
        return max_completed >= required_stage
    
    def get_character_unlock_progress(character, story_data):
        """Get unlock progress for a character"""
        required_stage = CHARACTER_UNLOCK_REQUIREMENTS.get(character, 0)
        max_completed = max(story_data["completed_stages"]) if story_data["completed_stages"] else 0
        
        if required_stage == 0:
            return "UNLOCKED"
        elif max_completed >= required_stage:
            return "UNLOCKED"
        else:
            return f"{max_completed}/{required_stage}"
    
    def story_character_selection_screen():
        """Character selection screen for story mode with enhanced visuals"""
        # Load story data to check unlock status
        story_data = load_story_data()
        
        characters = ["Samurai", "Soldier", "Magician", "Graffiti", "Kitsune", "Kunoichi", "Gangster"]
        selected = 0
        
        # Find first unlocked character as default selection
        for i, char in enumerate(characters):
            if is_character_unlocked(char, story_data):
                selected = i
                break
        
        back_button = pygame.Rect(20, 20, 80, 40)
        
        # Character description
        char_descriptions = {
            "Samurai": "Master of the blade. Balanced fighter with honorable spirit.",
            "Soldier": "Tactical warrior. High damage and military precision.",
            "Magician": "Arcane spellcaster. Powerful magic attacks and mystical abilities.",
            "Graffiti": "Street artist fighter. Creative combat style with urban flair.",
            "Kitsune": "Mystical fox spirit. Agile with supernatural powers.",
            "Kunoichi": "Shadow ninja. Stealth-based combat and swift strikes.",
            "Gangster": "Street boss. Heavy hitting with intimidating presence."
        }
        
        # Load lock icon
        lock_icon = None
        try:
            lock_icon = pygame.image.load("assets/lock.png").convert_alpha()
            lock_icon = pygame.transform.scale(lock_icon, (50, 50))
        except:
            pass
        
        # Track double click
        last_click_time = 0
        last_clicked_character = None
        
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint((vmx, vmy)):
                        return None
                    
                    # Check character card clicks
                    card_width = 140
                    card_height = 180
                    cards_per_row = 4
                    start_x = (VIRTUAL_W - (cards_per_row * card_width + (cards_per_row - 1) * 20)) // 2
                    
                    for i, char in enumerate(characters):
                        if i < 4:  # First row
                            x = start_x + i * (card_width + 20)
                            y = 180
                        else:  # Second row
                            x = start_x + (i - 4) * (card_width + 20) + 70  # Center the remaining 3
                            y = 380
                        
                        card_rect = pygame.Rect(x, y, card_width, card_height)
                        if card_rect.collidepoint((vmx, vmy)):
                            # Check for double click
                            if (last_clicked_character == char and 
                                current_time - last_click_time < 500):  # 500ms for double click
                                if is_character_unlocked(char, story_data):
                                    return char
                            else:
                                selected = i
                                last_clicked_character = char
                                last_click_time = current_time
            
            # Background gradient
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = int(25 + ratio * 35)
                g = int(35 + ratio * 45) 
                b = int(60 + ratio * 80)
                pygame.draw.line(virtual_surface, (r, g, b), (0, y), (VIRTUAL_W, y))
            
            # Title
            title = title_font.render("SELECT CHARACTER", True, get_rainbow_color())
            virtual_surface.blit(title, title.get_rect(center=(VIRTUAL_W // 2, 60)))
            
            # Story progress info
            max_completed = max(story_data["completed_stages"]) if story_data["completed_stages"] else 0
            progress_text = small_font.render(f"Story Progress: Stage {max_completed} completed", True, WHITE)
            virtual_surface.blit(progress_text, progress_text.get_rect(center=(VIRTUAL_W // 2, 100)))
            
            # Character cards
            card_width = 140
            card_height = 180
            cards_per_row = 4
            start_x = (VIRTUAL_W - (cards_per_row * card_width + (cards_per_row - 1) * 20)) // 2
            
            for i, char in enumerate(characters):
                # Calculate position
                if i < 4:  # First row
                    x = start_x + i * (card_width + 20)
                    y = 180
                else:  # Second row
                    x = start_x + (i - 4) * (card_width + 20) + 70  # Center the remaining 3
                    y = 380
                
                card_rect = pygame.Rect(x, y, card_width, card_height)
                
                # Check if character is unlocked
                is_unlocked = is_character_unlocked(char, story_data)
                unlock_progress = get_character_unlock_progress(char, story_data)
                
                # Card colors based on status
                if is_unlocked:
                    if i == selected:
                        card_color = SELECTED_COLOR
                        border_color = (255, 255, 0)
                        border_width = 4
                    else:
                        card_color = BUTTON_COLOR
                        border_color = WHITE
                        border_width = 2
                    text_color = WHITE
                else:
                    card_color = (60, 60, 60)  # Locked color
                    border_color = (100, 100, 100)
                    border_width = 2
                    text_color = (150, 150, 150)
                
                # Draw card
                pygame.draw.rect(virtual_surface, card_color, card_rect, border_radius=10)
                pygame.draw.rect(virtual_surface, border_color, card_rect, border_width, border_radius=10)
                
                # Character sprite or lock icon
                sprite_rect = pygame.Rect(x + 10, y + 10, 120, 100)
                
                if is_unlocked:
                    # Try to load and animate character sprite
                    sprite_loaded = False
                    possible_paths = [
                        f"assets/{char}/Idle.png",
                        f"assets/{char}/idle.png",
                        f"assets/{char.lower()}/Idle.png",
                        f"assets/{char.lower()}/idle.png"
                    ]
                    
                    for sprite_path in possible_paths:
                        try:
                            sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                            frame_count = character_frame_counts_idle.get(char, 6)
                            frame_width = sprite_sheet.get_width() // frame_count
                            
                            # Animate based on time
                            frame_time = 150  # milliseconds per frame
                            current_frame = (current_time // frame_time) % frame_count
                            
                            # Get current frame
                            frame_surface = pygame.Surface((frame_width, sprite_sheet.get_height()), pygame.SRCALPHA)
                            frame_rect = pygame.Rect(current_frame * frame_width, 0, frame_width, sprite_sheet.get_height())
                            frame_surface.blit(sprite_sheet, (0, 0), frame_rect)
                            
                            # Scale to fit
                            scaled_sprite = pygame.transform.scale(frame_surface, (100, 80))
                            sprite_pos = (x + 20, y + 20)
                            virtual_surface.blit(scaled_sprite, sprite_pos)
                            sprite_loaded = True
                            break
                        except:
                            continue
                    
                    if not sprite_loaded:
                        # Create placeholder for unlocked character
                        character_colors = {
                            "Samurai": (220, 50, 50), "Soldier": (50, 150, 50),
                            "Magician": (100, 50, 200), "Graffiti": (255, 150, 50),
                            "Kitsune": (255, 150, 100), "Gangster": (80, 80, 80),
                            "Kunoichi": (150, 50, 200)
                        }
                        color = character_colors.get(char, (150, 150, 150))
                        pygame.draw.rect(virtual_surface, color, sprite_rect, border_radius=5)
                        
                        # Character initial
                        initial = button_font.render(char[0], True, WHITE)
                        virtual_surface.blit(initial, initial.get_rect(center=sprite_rect.center))
                else:
                    # Locked character - show animated Idle sprite with lock overlay
                    sprite_loaded = False
                    possible_paths = [
                        f"assets/{char}/Idle.png",
                        f"assets/{char}/idle.png",
                        f"assets/{char.lower()}/Idle.png",
                        f"assets/{char.lower()}/idle.png"
                    ]
                    
                    for sprite_path in possible_paths:
                        try:
                            sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                            frame_count = character_frame_counts_idle.get(char, 6)
                            frame_width = sprite_sheet.get_width() // frame_count
                            
                            # Animate based on time
                            frame_time = 150  # milliseconds per frame
                            current_frame = (current_time // frame_time) % frame_count
                            
                            # Get current frame
                            frame_surface = pygame.Surface((frame_width, sprite_sheet.get_height()), pygame.SRCALPHA)
                            frame_rect = pygame.Rect(current_frame * frame_width, 0, frame_width, sprite_sheet.get_height())
                            frame_surface.blit(sprite_sheet, (0, 0), frame_rect)
                            
                            # Scale to fit and apply dark overlay
                            scaled_sprite = pygame.transform.scale(frame_surface, (100, 80))
                            
                            # Create dark overlay for locked character
                            overlay = pygame.Surface((100, 80))
                            overlay.set_alpha(150)
                            overlay.fill((0, 0, 0))
                            
                            sprite_pos = (x + 20, y + 20)
                            virtual_surface.blit(scaled_sprite, sprite_pos)
                            virtual_surface.blit(overlay, sprite_pos)
                            sprite_loaded = True
                            break
                        except:
                            continue
                    
                    if not sprite_loaded:
                        # Create dark placeholder for locked character
                        pygame.draw.rect(virtual_surface, (40, 40, 40), sprite_rect, border_radius=5)
                    
                    # Show lock icon
                    if lock_icon:
                        lock_rect = lock_icon.get_rect(center=sprite_rect.center)
                        virtual_surface.blit(lock_icon, lock_rect)
                    else:
                        lock_text = title_font.render("🔒", True, (100, 100, 100))
                        virtual_surface.blit(lock_text, lock_text.get_rect(center=sprite_rect.center))
                
                # Character name
                name_text = small_font.render(char, True, text_color)
                name_rect = name_text.get_rect(center=(x + card_width // 2, y + 125))
                virtual_surface.blit(name_text, name_rect)
                
                # Unlock status/progress
                if is_unlocked:
                    status_text = small_font.render("UNLOCKED", True, SELECTED_COLOR)
                else:
                    required_stage = CHARACTER_UNLOCK_REQUIREMENTS[char]
                    status_text = small_font.render(f"Stage {required_stage}", True, (200, 100, 100))
                
                status_rect = status_text.get_rect(center=(x + card_width // 2, y + 145))
                virtual_surface.blit(status_text, status_rect)
                
                # Progress for locked characters
                if not is_unlocked:
                    progress_text = small_font.render(unlock_progress, True, (150, 150, 150))
                    progress_rect = progress_text.get_rect(center=(x + card_width // 2, y + 165))
                    virtual_surface.blit(progress_text, progress_rect)
            
            # Selected character info panel
            if is_character_unlocked(characters[selected], story_data):
                info_panel = pygame.Rect(50, 120, VIRTUAL_W - 100, 50)
                pygame.draw.rect(virtual_surface, (40, 40, 80, 200), info_panel, border_radius=10)
                
                char_desc = char_descriptions.get(characters[selected], "A skilled warrior.")
                desc_text = small_font.render(char_desc, True, WHITE)
                virtual_surface.blit(desc_text, desc_text.get_rect(center=info_panel.center))
            
            # Back button
            back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
            back_text = small_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
            
            # Instructions
            instruction = small_font.render("Double-click to select character", True, (200, 200, 200))
            virtual_surface.blit(instruction, instruction.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 20)))
            
            draw_scaled_centered()
            clock.tick(60)
    
    def load_story_data():
        """Load story mode progress"""
        try:
            with open("story_data.json", "r") as f:
                return json.load(f)
        except:
            return {
                "current_stage": 1,
                "completed_stages": [],
                "total_rewards": {
                    "sakura": 0,
                    "water": 0,
                    "black_water": 0,
                    "tengu_feathers": 0
                },
                "claimed_milestones": []  # Track claimed milestone rewards
            }
    
    def save_story_data(data):
        """Save story mode progress"""
        try:
            with open("story_data.json", "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving story data: {e}")
       
    def check_milestone_rewards(story_data):
        """Check and award milestone rewards"""
        milestones = {
            10: {"tengu_feathers": 5},
            25: {"sakura": 5},
            50: {"water": 5},
            75: {"black_water": 5},
            100: {"tengu_feathers": 15},
            150: {"sakura": 10},
            200: {"water": 10},
            300: {"tengu_feathers": 25, "sakura": 15, "water": 15, "black_water": 15, "wizard_unlock": True}  # ADDED WIZARD UNLOCK
        }
        
        completed_stages = story_data["completed_stages"]
        claimed_milestones = story_data.get("claimed_milestones", [])
        new_rewards = {}
        wizard_unlocked = False
        
        for milestone_stage, rewards in milestones.items():
            if milestone_stage in completed_stages and milestone_stage not in claimed_milestones:
                for reward_type, amount in rewards.items():
                    if reward_type == "wizard_unlock":
                        wizard_unlocked = True
                        # Unlock Wizard character
                        try:
                            character_data = load_character_data()
                            if "Wizard" not in character_data["owned_characters"]:
                                character_data["owned_characters"].append("Wizard")
                                save_character_data(character_data)
                        except:
                            pass
                    else:
                        if reward_type not in new_rewards:
                            new_rewards[reward_type] = 0
                        new_rewards[reward_type] += amount
                        story_data["total_rewards"][reward_type] += amount
                
                claimed_milestones.append(milestone_stage)
        
        story_data["claimed_milestones"] = claimed_milestones
        
        # Return both rewards and wizard unlock status
        if wizard_unlocked:
            new_rewards["wizard_unlock"] = True
        
        return new_rewards
    
    def show_milestone_rewards(new_rewards):
        """Show milestone reward popup - CENTERED VERSION WITH WIZARD UNLOCK"""
        if not new_rewards:
            return
            
        # Load reward icons
        reward_icons = {}
        try:
            reward_icons["sakura"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/sakura.png").convert_alpha(), (50, 50))
            reward_icons["water"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/water.png").convert_alpha(), (50, 50))
            reward_icons["black_water"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), (50, 50))
            reward_icons["tengu_feathers"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), (50, 50))
        except:
            # Create placeholder icons
            for reward in ["sakura", "water", "black_water", "tengu_feathers"]:
                icon = pygame.Surface((50, 50))
                icon.fill((100, 150, 200))
                reward_icons[reward] = icon
        
        # Load Wizard character icon if unlocked
        wizard_icon = None
        if "wizard_unlock" in new_rewards:
            try:
                wizard_idle = pygame.image.load("assets/Wizard/Idle.png").convert_alpha()
                frame_width = wizard_idle.get_width() // 6  # 6 frames for Wizard Idle
                first_frame = wizard_idle.subsurface(pygame.Rect(0, 0, frame_width, wizard_idle.get_height()))
                wizard_icon = pygame.transform.scale(first_frame, (80, 80))
            except:
                # Create placeholder
                wizard_icon = pygame.Surface((80, 80))
                wizard_icon.fill((100, 50, 200))
                pygame.draw.rect(wizard_icon, (255, 255, 255), wizard_icon.get_rect(), 3)
        
        # Semi-transparent overlay
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        
        # Centered popup box - larger for Wizard unlock
        popup_width = 500 if "wizard_unlock" in new_rewards else 450
        popup_height = 350 if "wizard_unlock" in new_rewards else 300
        popup_x = (VIRTUAL_W - popup_width) // 2
        popup_y = (VIRTUAL_H - popup_height) // 2
        
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        continue_button = pygame.Rect(popup_x + popup_width//2 - 75, popup_y + popup_height - 60, 150, 40)
        
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if continue_button.collidepoint((vmx, vmy)):
                        return
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                        return
            
            # Draw current screen first (milestone screen background)
            # Background gradient
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = int(25 + ratio * 35)
                g = int(35 + ratio * 45) 
                b = int(60 + ratio * 80)
                pygame.draw.line(virtual_surface, (r, g, b), (0, y), (VIRTUAL_W, y))
            
            # Draw overlay
            virtual_surface.blit(overlay, (0, 0))
            
            # Draw centered popup box
            pygame.draw.rect(virtual_surface, (50, 50, 100, 250), popup_rect, border_radius=20)
            pygame.draw.rect(virtual_surface, (255, 215, 0), popup_rect, 4, border_radius=20)
            
            # Title - centered in popup
            title = title_font.render("MILESTONE", True, get_rainbow_color())
            title_rect = title.get_rect(center=(popup_x + popup_width//2, popup_y + 40))
            virtual_surface.blit(title, title_rect)
            
            # Subtitle
            subtitle = button_font.render("Achievement Unlocked!", True, (255, 215, 0))
            subtitle_rect = subtitle.get_rect(center=(popup_x + popup_width//2, popup_y + 80))
            virtual_surface.blit(subtitle, subtitle_rect)
            
            # Special handling for Wizard unlock
            if "wizard_unlock" in new_rewards:
                # Wizard unlock section
                wizard_title = button_font.render("NEW CHARACTER UNLOCKED!", True, (255, 100, 255))
                wizard_title_rect = wizard_title.get_rect(center=(popup_x + popup_width//2, popup_y + 120))
                virtual_surface.blit(wizard_title, wizard_title_rect)
                
                # Wizard icon
                if wizard_icon:
                    wizard_rect = wizard_icon.get_rect(center=(popup_x + popup_width//2, popup_y + 170))
                    virtual_surface.blit(wizard_icon, wizard_rect)
                
                # Wizard name
                wizard_name = button_font.render("WIZARD", True, (255, 255, 255))
                wizard_name_rect = wizard_name.get_rect(center=(popup_x + popup_width//2, popup_y + 220))
                virtual_surface.blit(wizard_name, wizard_name_rect)
                
                # Other rewards display (smaller, below Wizard)
                reward_start_y = popup_y + 250
                other_rewards = {k: v for k, v in new_rewards.items() if k != "wizard_unlock"}
                
                if other_rewards:
                    reward_count = len(other_rewards)
                    if reward_count <= 4:
                        # Single row
                        total_width = reward_count * 80
                        start_x = popup_x + (popup_width - total_width) // 2 + 40
                        
                        for i, (reward_type, amount) in enumerate(other_rewards.items()):
                            reward_x = start_x + i * 80
                            reward_y = reward_start_y
                            
                            # Draw small reward icon
                            if reward_type in reward_icons:
                                small_icon = pygame.transform.scale(reward_icons[reward_type], (30, 30))
                                icon_rect = small_icon.get_rect(center=(reward_x, reward_y))
                                virtual_surface.blit(small_icon, icon_rect)
                            
                            # Draw small amount text
                            amount_text = small_font.render(f"x{amount}", True, (255, 215, 0))
                            amount_text_rect = amount_text.get_rect(center=(reward_x, reward_y + 20))
                            virtual_surface.blit(amount_text, amount_text_rect)
            else:
                # Regular rewards display (original logic)
                reward_count = len(new_rewards)
                start_y = popup_y + 120
                
                if reward_count <= 2:
                    # Single row for 1-2 rewards
                    total_width = reward_count * 180
                    start_x = popup_x + (popup_width - total_width) // 2 + 90
                    
                    for i, (reward_type, amount) in enumerate(new_rewards.items()):
                        reward_x = start_x + i * 180
                        reward_y = start_y
                        
                        # Draw reward icon centered
                        if reward_type in reward_icons:
                            icon_rect = reward_icons[reward_type].get_rect(center=(reward_x, reward_y))
                            virtual_surface.blit(reward_icons[reward_type], icon_rect)
                        
                        # Draw reward text below icon
                        reward_name = reward_type.replace("_", " ").title()
                        reward_text = button_font.render(f"{reward_name}", True, WHITE)
                        reward_text_rect = reward_text.get_rect(center=(reward_x, reward_y + 40))
                        virtual_surface.blit(reward_text, reward_text_rect)
                        
                        amount_text = button_font.render(f"x{amount}", True, (255, 215, 0))
                        amount_text_rect = amount_text.get_rect(center=(reward_x, reward_y + 65))
                        virtual_surface.blit(amount_text, amount_text_rect)
                        
                else:
                    # Two rows for 3+ rewards (for stage 300 with regular rewards)
                    items_per_row = 2
                    row1_items = list(new_rewards.items())[:items_per_row]
                    row2_items = list(new_rewards.items())[items_per_row:]
                    
                    # Row 1
                    row1_width = len(row1_items) * 180
                    row1_start_x = popup_x + (popup_width - row1_width) // 2 + 90
                    
                    for i, (reward_type, amount) in enumerate(row1_items):
                        reward_x = row1_start_x + i * 180
                        reward_y = start_y
                        
                        if reward_type in reward_icons:
                            icon_rect = reward_icons[reward_type].get_rect(center=(reward_x, reward_y))
                            virtual_surface.blit(reward_icons[reward_type], icon_rect)
                        
                        reward_name = reward_type.replace("_", " ").title()
                        reward_text = small_font.render(f"{reward_name} x{amount}", True, WHITE)
                        reward_text_rect = reward_text.get_rect(center=(reward_x, reward_y + 35))
                        virtual_surface.blit(reward_text, reward_text_rect)
                    
                    # Row 2
                    row2_width = len(row2_items) * 180
                    row2_start_x = popup_x + (popup_width - row2_width) // 2 + 90
                    
                    for i, (reward_type, amount) in enumerate(row2_items):
                        reward_x = row2_start_x + i * 180
                        reward_y = start_y + 80
                        
                        if reward_type in reward_icons:
                            icon_rect = reward_icons[reward_type].get_rect(center=(reward_x, reward_y))
                            virtual_surface.blit(reward_icons[reward_type], icon_rect)
                        
                        reward_name = reward_type.replace("_", " ").title()
                        reward_text = small_font.render(f"{reward_name} x{amount}", True, WHITE)
                        reward_text_rect = reward_text.get_rect(center=(reward_x, reward_y + 35))
                        virtual_surface.blit(reward_text, reward_text_rect)
            
            # Continue button - centered at bottom
            button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=10)
            
            continue_text = button_font.render("CONTINUE", True, WHITE)
            continue_text_rect = continue_text.get_rect(center=continue_button.center)
            virtual_surface.blit(continue_text, continue_text_rect)
            
            # Instruction text
            instruction_text = small_font.render("Press SPACE/ENTER or click CONTINUE", True, (200, 200, 200))
            instruction_rect = instruction_text.get_rect(center=(popup_x + popup_width//2, popup_y + popup_height - 20))
            virtual_surface.blit(instruction_text, instruction_rect)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def show_milestone_screen(story_data):
        """Show milestone progress screen with pagination"""
        milestones = {
            10: {"tengu_feathers": 5},
            25: {"sakura": 5},
            50: {"water": 5},
            75: {"black_water": 5},
            100: {"tengu_feathers": 15},
            150: {"sakura": 10},
            200: {"water": 10},
            300: {"tengu_feathers": 25, "sakura": 15, "water": 15, "black_water": 15}
        }
        
        completed_stages = story_data["completed_stages"]
        claimed_milestones = story_data.get("claimed_milestones", [])
        current_page = 1  # 1 = milestone page, 2 = wizard page
        
        # Load navigation buttons
        next_button_img = None
        prev_button_img = None
        try:
            next_button_img = pygame.image.load("assets/next.png").convert_alpha()
            next_button_img = pygame.transform.scale(next_button_img, (40, 40))
            prev_button_img = pygame.image.load("assets/previous.png").convert_alpha()
            prev_button_img = pygame.transform.scale(prev_button_img, (40, 40))
        except:
            # Create placeholder buttons
            next_button_img = pygame.Surface((40, 40))
            next_button_img.fill((100, 150, 200))
            pygame.draw.polygon(next_button_img, WHITE, [(10, 10), (30, 20), (10, 30)])
            prev_button_img = pygame.Surface((40, 40))
            prev_button_img.fill((100, 150, 200))
            pygame.draw.polygon(prev_button_img, WHITE, [(30, 10), (10, 20), (30, 30)])
        
        # Load Wizard animation
        wizard_frames = []
        try:
            wizard_idle = pygame.image.load("assets/Wizard/Idle.png").convert_alpha()
            frame_width = wizard_idle.get_width() // 6  # 6 frames
            for i in range(6):
                frame = wizard_idle.subsurface(pygame.Rect(i * frame_width, 0, frame_width, wizard_idle.get_height()))
                scaled_frame = pygame.transform.scale(frame, (120, 120))
                wizard_frames.append(scaled_frame)
        except:
            # Create placeholder frames
            for i in range(6):
                frame = pygame.Surface((120, 120))
                frame.fill((100, 50, 200))
                pygame.draw.rect(frame, (255, 255, 255), frame.get_rect(), 3)
                wizard_frames.append(frame)
        
        # Load reward icons
        reward_icons = {}
        try:
            reward_icons["sakura"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/sakura.png").convert_alpha(), (25, 25))
            reward_icons["water"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/water.png").convert_alpha(), (25, 25))
            reward_icons["black_water"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), (25, 25))
            reward_icons["tengu_feathers"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), (25, 25))
        except:
            for reward in ["sakura", "water", "black_water", "tengu_feathers"]:
                icon = pygame.Surface((25, 25))
                icon.fill((100, 150, 200))
                reward_icons[reward] = icon
        
        # Button positions
        back_button = pygame.Rect(10, 15, 80, 35)
        next_button = pygame.Rect(VIRTUAL_W - 60, VIRTUAL_H // 2 - 20, 40, 40)
        prev_button = pygame.Rect(20, VIRTUAL_H // 2 - 20, 40, 40)
        
        # Animation variables
        animation_timer = 0
        frame_duration = 10  # frames per animation frame
        
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint((vmx, vmy)):
                        return
                    if next_button.collidepoint((vmx, vmy)) and current_page == 1:
                        current_page = 2
                    if prev_button.collidepoint((vmx, vmy)) and current_page == 2:
                        current_page = 1
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_RIGHT and current_page == 1:
                        current_page = 2
                    if event.key == pygame.K_LEFT and current_page == 2:
                        current_page = 1
            
            # Update animation
            animation_timer += 1
            
            # Background gradient
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = int(25 + ratio * 35)
                g = int(35 + ratio * 45) 
                b = int(60 + ratio * 80)
                pygame.draw.line(virtual_surface, (r, g, b), (0, y), (VIRTUAL_W, y))
            
            if current_page == 1:
                # Page 1 - Milestone rewards
                title = title_font.render("MILESTONE REWARDS", True, get_rainbow_color())
                virtual_surface.blit(title, title.get_rect(center=(VIRTUAL_W // 2, 60)))
                
                # Milestone grid (2 columns, 4 rows)
                start_x = 100
                start_y = 120
                col_width = 300
                row_height = 100
                
                milestone_list = list(milestones.keys())
                
                for i, milestone_stage in enumerate(milestone_list):
                    col = i % 2
                    row = i // 2
                    
                    x = start_x + col * col_width
                    y = start_y + row * row_height
                    
                    # Milestone box
                    milestone_rect = pygame.Rect(x, y, 280, 90)
                    
                    # Determine status and color
                    if milestone_stage in claimed_milestones:
                        color = (100, 200, 100)  # Green - Claimed
                        status = "CLAIMED"
                        text_color = WHITE
                    elif milestone_stage in completed_stages:
                        color = (255, 215, 0)  # Gold - Available to claim
                        status = "READY"
                        text_color = (0, 0, 0)
                    else:
                        color = (80, 80, 80)  # Gray - Not reached
                        status = "LOCKED"
                        text_color = (150, 150, 150)
                    
                    pygame.draw.rect(virtual_surface, color, milestone_rect, border_radius=10)
                    pygame.draw.rect(virtual_surface, WHITE, milestone_rect, 2, border_radius=10)
                    
                    # Milestone stage number
                    stage_text = button_font.render(f"Stage {milestone_stage}", True, text_color)
                    virtual_surface.blit(stage_text, (x + 10, y + 10))
                    
                    # Status
                    status_text = small_font.render(status, True, text_color)
                    virtual_surface.blit(status_text, (x + 180, y + 10))
                    
                    # Rewards
                    rewards = milestones[milestone_stage]
                    reward_y = y + 35
                    reward_x = x + 10
                    
                    if milestone_stage == 300:
                        # Layout khusus untuk 4 rewards di stage 300
                        reward_items = list(rewards.items())
                        for idx, (reward_type, amount) in enumerate(reward_items):
                            row_idx = idx // 2
                            col_idx = idx % 2
                            
                            item_x = x + 80 + col_idx * 110
                            item_y = y + 35 + row_idx * 25
                            
                            if reward_type in reward_icons:
                                virtual_surface.blit(reward_icons[reward_type], (item_x, item_y))
                                item_x += 30
                            
                            reward_text = small_font.render(f"{amount}", True, text_color)
                            virtual_surface.blit(reward_text, (item_x, item_y + 2))
                    else:
                        # Layout normal untuk milestone lainnya
                        for reward_type, amount in rewards.items():
                            if reward_type in reward_icons:
                                virtual_surface.blit(reward_icons[reward_type], (reward_x, reward_y))
                                reward_x += 30
                            
                            reward_text = small_font.render(f"{amount}", True, text_color)
                            virtual_surface.blit(reward_text, (reward_x, reward_y + 2))
                            reward_x += 45
                    
                    # Progress for current milestone
                    if milestone_stage not in completed_stages and milestone_stage not in claimed_milestones:
                        max_completed = max(completed_stages) if completed_stages else 0
                        progress_text = small_font.render(f"({max_completed}/{milestone_stage})", True, text_color)
                        
                        if milestone_stage == 300:
                            virtual_surface.blit(progress_text, (x + 10, y + 60))
                        else:
                            virtual_surface.blit(progress_text, (x + 10, y + 65))
                
                # Next button
                if next_button_img:
                    virtual_surface.blit(next_button_img, next_button)
                else:
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, next_button, border_radius=5)
                    pygame.draw.polygon(virtual_surface, WHITE, [
                        (next_button.centerx - 10, next_button.centery - 10),
                        (next_button.centerx + 10, next_button.centery),
                        (next_button.centerx - 10, next_button.centery + 10)
                    ])
                
            else:
                # Page 2 - Wizard unlock
                title = title_font.render("CHARACTER UNLOCK", True, get_rainbow_color())
                virtual_surface.blit(title, title.get_rect(center=(VIRTUAL_W // 2, 60)))
                
                # Wizard unlock box - centered
                wizard_box = pygame.Rect(VIRTUAL_W // 2 - 200, 150, 400, 250)
                
                # Determine status and color for stage 300 wizard unlock
                if 300 in claimed_milestones:
                    color = (100, 200, 100)  # Green - Unlocked
                    status = "UNLOCKED"
                    text_color = WHITE
                elif 300 in completed_stages:
                    color = (255, 215, 0)  # Gold - Available
                    status = "AVAILABLE"
                    text_color = (0, 0, 0)
                else:
                    color = (80, 80, 80)  # Gray - Locked
                    status = "LOCKED"
                    text_color = (150, 150, 150)
                
                pygame.draw.rect(virtual_surface, color, wizard_box, border_radius=15)
                pygame.draw.rect(virtual_surface, WHITE, wizard_box, 3, border_radius=15)
                
                # Stage 300 text
                stage_text = button_font.render("Stage 300", True, text_color)
                stage_rect = stage_text.get_rect(center=(wizard_box.centerx, wizard_box.y + 30))
                virtual_surface.blit(stage_text, stage_rect)
                
                # Status
                status_text = small_font.render(status, True, text_color)
                status_rect = status_text.get_rect(center=(wizard_box.centerx, wizard_box.y + 60))
                virtual_surface.blit(status_text, status_rect)
                
                # Animated Wizard sprite
                current_frame = (animation_timer // frame_duration) % len(wizard_frames)
                wizard_frame = wizard_frames[current_frame]
                wizard_rect = wizard_frame.get_rect(center=(wizard_box.centerx, wizard_box.y + 140))
                virtual_surface.blit(wizard_frame, wizard_rect)
                
                # Character unlock text
                unlock_text1 = small_font.render("New Character unlocked", True, text_color)
                unlock_text2 = small_font.render("by reaching stage 300!", True, text_color)
                unlock_rect1 = unlock_text1.get_rect(center=(wizard_box.centerx, wizard_box.y + 185))
                unlock_rect2 = unlock_text2.get_rect(center=(wizard_box.centerx, wizard_box.y + 205))
                virtual_surface.blit(unlock_text1, unlock_rect1)
                virtual_surface.blit(unlock_text2, unlock_rect2)

                # Progress for stage 300
                if 300 not in completed_stages and 300 not in claimed_milestones:
                    max_completed = max(completed_stages) if completed_stages else 0
                    progress_text = small_font.render(f"Progress: {max_completed}/300", True, text_color)
                    progress_rect = progress_text.get_rect(center=(wizard_box.centerx, wizard_box.y + 235))
                    virtual_surface.blit(progress_text, progress_rect)
                
                # Previous button
                if prev_button_img:
                    virtual_surface.blit(prev_button_img, prev_button)
                else:
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, prev_button, border_radius=5)
                    pygame.draw.polygon(virtual_surface, WHITE, [
                        (prev_button.centerx + 10, prev_button.centery - 10),
                        (prev_button.centerx - 10, prev_button.centery),
                        (prev_button.centerx + 10, prev_button.centery + 10)
                    ])
            
            # Back button
            back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
            back_text = small_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
            
            # Page indicator
            page_text = small_font.render(f"Page {current_page}/2", True, WHITE)
            page_rect = page_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 30))
            virtual_surface.blit(page_text, page_rect)
            
            draw_scaled_centered()
            clock.tick(60)

    def show_pre_battle_dialog(character, stage):
        character_dialogs = {
            "Samurai": [
                "The way of the sword is the way of honor!",
                "My blade shall cut through this darkness!",
                "For honor and justice, I will not falter!",
                "The cherry blossoms witness my resolve!",
                "This battle will test my bushido spirit!"
            ],
            "Soldier": [
                "Orders received, engaging the enemy!",
                "No retreat, no surrender, soldier!",
                "For the squad, for victory!",
                "This is what I trained for!",
                "Tactical advantage: mine to take!"
            ],
            "Magician": [
                "The arcane energies flow through me!",
                "Magic is the ultimate power!",
                "My spells shall bend reality itself!",
                "The mystical arts demand respect!",
                "Ancient wisdom guides my magic!"
            ],
            "Graffiti": [
                "Time to paint the town... with victory!",
                "My art speaks through action!",
                "Street smart and battle ready!",
                "This is my canvas, this is my fight!",
                "Urban warfare is my specialty!"
            ],
            "Kitsune": [
                "Nine tails, infinite power!",
                "The fox spirit awakens within me!",
                "Cunning and grace shall triumph!",
                "My transformation is complete!",
                "Mystical fox fire burns bright!"
            ],
            "Gangster": [
                "Business is business, nothing personal!",
                "Time to show them who runs this turf!",
                "My reputation precedes me!",
                "Street justice is the only justice!",
                "Nobody crosses my territory!"
            ],
            "Kunoichi": [
                "Shadows are my faithful allies!",
                "The way of the ninja is silent death!",
                "Stealth and precision over brute force!",
                "My training has prepared me for this!",
                "The darkness conceals my true power!"
            ]
        }
        
        # Get random dialog for the character
        if character in character_dialogs:
            dialog_text = random.choice(character_dialogs[character])
        else:
            dialog_text = "Ready for battle!"
        
        # Load character Idle sprite sheet and slice it into frames
        idle_frames = []
        
        possible_paths = [
            f"assets/{character}/Idle.png",
            f"assets/{character}/idle.png",
            f"assets/{character.lower()}/Idle.png",
            f"assets/{character.lower()}/idle.png"
        ]
        
        sprite_sheet_loaded = False
        for sprite_path in possible_paths:
            try:
                sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
                
                frame_count = character_frame_counts_idle.get(character, 6)
                sheet_width = sprite_sheet.get_width()
                sheet_height = sprite_sheet.get_height()
                frame_width = sheet_width // frame_count
                frame_height = sheet_height
                
                for i in range(frame_count):
                    x = i * frame_width
                    y = 0
                    
                    frame_surface = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
                    frame_rect = pygame.Rect(x, y, frame_width, frame_height)
                    frame_surface.blit(sprite_sheet, (0, 0), frame_rect)
                    
                    target_size = 200
                    if frame_width > frame_height:
                        scale_factor = target_size / frame_width
                        new_width = target_size
                        new_height = int(frame_height * scale_factor)
                    else:
                        scale_factor = target_size / frame_height
                        new_height = target_size
                        new_width = int(frame_width * scale_factor)
                    
                    scaled_frame = pygame.transform.smoothscale(frame_surface, (new_width, new_height))
                    idle_frames.append(scaled_frame)
                
                sprite_sheet_loaded = True
                break
                
            except:
                continue
        
        # If no sprite sheet loaded, create a placeholder
        if not sprite_sheet_loaded or not idle_frames:
            character_info = {
                "Samurai": {"color": (220, 50, 50), "symbol": "⚔", "bg_color": (255, 200, 200)},
                "Soldier": {"color": (50, 150, 50), "symbol": "★", "bg_color": (200, 255, 200)},
                "Magician": {"color": (100, 50, 200), "symbol": "✦", "bg_color": (200, 200, 255)},
                "Graffiti": {"color": (255, 150, 50), "symbol": "◆", "bg_color": (255, 255, 100)},
                "Kitsune": {"color": (255, 150, 100), "symbol": "◉", "bg_color": (255, 220, 200)},
                "Gangster": {"color": (80, 80, 80), "symbol": "♠", "bg_color": (150, 150, 150)},
                "Kunoichi": {"color": (150, 50, 200), "symbol": "◈", "bg_color": (220, 200, 255)}
            }
            
            char_info = character_info.get(character, {"color": (150, 150, 150), "symbol": "?", "bg_color": (200, 200, 200)})
            
            frame_count = character_frame_counts_idle.get(character, 6)
            for i in range(frame_count):
                placeholder = pygame.Surface((200, 200), pygame.SRCALPHA)
                
                import math
                size_variation = int(5 * math.sin((i / frame_count) * 2 * math.pi))
                base_radius = 80 + size_variation
                
                pygame.draw.circle(placeholder, char_info["bg_color"], (100, 100), base_radius + 10)
                pygame.draw.circle(placeholder, char_info["color"], (100, 100), base_radius)
                pygame.draw.circle(placeholder, WHITE, (100, 100), base_radius, 3)
                
                symbol_font = pygame.font.Font(None, 48)
                symbol_text = symbol_font.render(char_info["symbol"], True, WHITE)
                symbol_rect = symbol_text.get_rect(center=(100, 85))
                placeholder.blit(symbol_text, symbol_rect)
                
                name_font = pygame.font.Font(None, 20)
                name_text = name_font.render(character, True, WHITE)
                name_rect = name_text.get_rect(center=(100, 115))
                placeholder.blit(name_text, name_rect)
                
                idle_frames.append(placeholder)
        
        # Create dialog background with gradient
        dialog_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        for y in range(VIRTUAL_H):
            ratio = y / VIRTUAL_H
            r = int(20 + ratio * 30)
            g = int(20 + ratio * 30)  
            b = int(40 + ratio * 60)
            pygame.draw.line(dialog_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
            dialog_box = pygame.Rect(50, VIRTUAL_H - 160, VIRTUAL_W - 100, 120)
        character_pos = (VIRTUAL_W // 2, VIRTUAL_H // 2 - 80)
        
        frame_idx = 0
        frame_timer = 0
        total_frames = len(idle_frames)
        base_animation_time = 2000
        frame_delay = base_animation_time // total_frames
        
        revealed_text = ""
        text_complete = False
        
        continue_button = pygame.Rect(VIRTUAL_W - 180, dialog_box.bottom - 50, 120, 40)
        
        start_time = pygame.time.get_ticks()
        
        while True:
            dt = clock.tick(60)
            current_time = pygame.time.get_ticks()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if text_complete:
                            return
                        else:
                            revealed_text = dialog_text
                            text_complete = True
                    elif event.key == pygame.K_ESCAPE:
                        return
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                    
                    if text_complete and continue_button.collidepoint((vmx, vmy)):
                        return
                    elif not text_complete:
                        revealed_text = dialog_text
                        text_complete = True
            
            # Update frame animation
            frame_timer += dt
            if frame_timer >= frame_delay and len(idle_frames) > 1:
                frame_timer = 0
                frame_idx = (frame_idx + 1) % len(idle_frames)
            
            # Update text reveal animation
            if not text_complete:
                chars_to_show = min(len(dialog_text), 
                                  int((current_time - start_time) / 50))
                revealed_text = dialog_text[:chars_to_show]
                
                if len(revealed_text) >= len(dialog_text):
                    text_complete = True
            
            # Drawing
            virtual_surface.blit(dialog_bg, (0, 0))
            
            stage_title = title_font.render(f"STAGE {stage}", True, get_rainbow_color())
            virtual_surface.blit(stage_title, stage_title.get_rect(center=(VIRTUAL_W // 2, 60)))
            
            pre_battle_text = button_font.render("Character Dialogue", True, WHITE)
            virtual_surface.blit(pre_battle_text, pre_battle_text.get_rect(center=(VIRTUAL_W // 2, 100)))
            
            # Draw character sprite with animation
            if idle_frames and len(idle_frames) > 0:
                current_frame = idle_frames[frame_idx]
                char_rect = current_frame.get_rect(center=character_pos)
                
                import math
                glow_intensity = int(30 + 20 * math.sin(current_time * 0.005))
                
                glow_colors = {
                    "Samurai": (255, 100, 100),
                    "Soldier": (100, 255, 100),
                    "Magician": (150, 100, 255),
                    "Graffiti": (255, 200, 100),
                    "Kitsune": (255, 150, 200),
                    "Gangster": (200, 200, 200),
                    "Kunoichi": (200, 100, 255)
                }
                
                glow_color = glow_colors.get(character, (255, 255, 255))
                glow_surface = pygame.Surface((280, 280), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*glow_color, glow_intensity), (140, 140), 140)
                glow_rect = glow_surface.get_rect(center=character_pos)
                virtual_surface.blit(glow_surface, glow_rect)
                
                virtual_surface.blit(current_frame, char_rect)
            
            # Character name below sprite
            char_name = button_font.render(character.upper(), True, WHITE)
            char_name_rect = char_name.get_rect(center=(VIRTUAL_W // 2, character_pos[1] + 130))
            
            name_bg = pygame.Rect(char_name_rect.x - 15, char_name_rect.y - 8, 
                                 char_name_rect.width + 30, char_name_rect.height + 16)
            
            name_bg_colors = {
                "Samurai": (100, 20, 20),
                "Soldier": (20, 100, 20),
                "Magician": (40, 20, 100),
                "Graffiti": (100, 80, 20),
                "Kitsune": (100, 60, 80),
                "Gangster": (60, 60, 60),
                "Kunoichi": (80, 40, 100)
            }
            
            bg_color = name_bg_colors.get(character, (50, 50, 50))
            pygame.draw.rect(virtual_surface, bg_color, name_bg, border_radius=8)
            pygame.draw.rect(virtual_surface, WHITE, name_bg, 2, border_radius=8)
            
            virtual_surface.blit(char_name, char_name_rect)
            
            # Draw dialog box
            pygame.draw.rect(virtual_surface, (40, 40, 80, 220), dialog_box, border_radius=15)
            pygame.draw.rect(virtual_surface, WHITE, dialog_box, 3, border_radius=15)
            
            # Draw dialog text with word wrapping
            words = revealed_text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (' ' if current_line else '') + word
                text_width = button_font.size(test_line)[0]
                
                if text_width < dialog_box.width - 40:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(current_line)
            
            line_height = 28
            start_y = dialog_box.y + 25
            
            for i, line in enumerate(lines[:4]):
                line_surface = button_font.render(line, True, WHITE)
                virtual_surface.blit(line_surface, (dialog_box.x + 20, start_y + i * line_height))
            
            # Draw continue instruction or button
            if text_complete:
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                button_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, button_color, continue_button, border_radius=8)
                
                continue_text = small_font.render("CONTINUE", True, WHITE)
                virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
                
                instruction_text = small_font.render("Press SPACE/ENTER or click CONTINUE", True, (200, 200, 200))
                virtual_surface.blit(instruction_text, (dialog_box.x + 20, dialog_box.bottom - 25))
            else:
                dots_cycle = ["", ".", "..", "..."]
                dots = dots_cycle[(current_time // 300) % 4]
                indicator_text = small_font.render(f"{character} is speaking{dots}", True, (150, 150, 150))
                virtual_surface.blit(indicator_text, (dialog_box.x + 20, dialog_box.bottom - 25))
            
            draw_scaled_centered()

    def stage_selection_screen(story_data):
        """Stage selection screen with RPG style map"""
        try:
            story_bg = pygame.image.load("assets/storybg.png").convert()
            story_bg = pygame.transform.smoothscale(story_bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            story_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = int(25 + ratio * 35)
                g = int(35 + ratio * 45) 
                b = int(60 + ratio * 80)
                pygame.draw.line(story_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
        
        current_stage = story_data["current_stage"]
        completed_stages = story_data["completed_stages"]
        
        current_page = 0
        stages_per_page = 4
        total_pages = (300 + stages_per_page - 1) // stages_per_page
        
        selected_stage = None
        
        back_button = pygame.Rect(20, 20, 100, 50)
        start_button = pygame.Rect(VIRTUAL_W//2 - 100, 515, 200, 60)
        milestone_button = pygame.Rect(VIRTUAL_W - 150, 20, 120, 50)
        
        prev_button = pygame.Rect(VIRTUAL_W//2 - 200, 470, 60, 60)
        next_button = pygame.Rect(VIRTUAL_W//2 + 140, 470, 60, 60)
        
        # Load navigation icons
        try:
            prev_icon = pygame.image.load("assets/previous.png").convert_alpha()
            prev_icon = pygame.transform.scale(prev_icon, (50, 50))
        except:
            prev_icon = None
            
        try:
            next_icon = pygame.image.load("assets/next.png").convert_alpha()
            next_icon = pygame.transform.scale(next_icon, (50, 50))
        except:
            next_icon = None
        
        stage_buttons = {}
        
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if back_button.collidepoint((vmx, vmy)):
                        return None
                    elif start_button.collidepoint((vmx, vmy)) and selected_stage and selected_stage <= current_stage and selected_stage not in completed_stages:
                        return selected_stage
                    elif milestone_button.collidepoint((vmx, vmy)):
                        show_milestone_screen(story_data)
                    elif prev_button.collidepoint((vmx, vmy)) and current_page > 0:
                        current_page -= 1
                        selected_stage = None
                    elif next_button.collidepoint((vmx, vmy)) and current_page < total_pages - 1:
                        current_page += 1
                        selected_stage = None
                    
                    for stage, rect in stage_buttons.items():
                        if rect.collidepoint((vmx, vmy)):
                            selected_stage = stage
            
            virtual_surface.blit(story_bg, (0, 0))
            
            title_text = title_font.render("STORY MODE", True, get_rainbow_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
            
            progress_text = button_font.render(f"Progress: {len(completed_stages)}/300 Stages Completed", True, WHITE)
            virtual_surface.blit(progress_text, progress_text.get_rect(center=(VIRTUAL_W // 2, 130)))
            
            page_text = small_font.render(f"Page {current_page + 1}/{total_pages}", True, WHITE)
            virtual_surface.blit(page_text, page_text.get_rect(center=(VIRTUAL_W // 2, 150)))
            
            stage_area = pygame.Rect(40, 180, VIRTUAL_W - 80, 280)
            pygame.draw.rect(virtual_surface, (40, 40, 80, 180), stage_area, border_radius=15)
            pygame.draw.rect(virtual_surface, WHITE, stage_area, 3, border_radius=15)
            
            start_stage = current_page * stages_per_page + 1
            end_stage = min(300, start_stage + stages_per_page - 1)
            
            stage_buttons.clear()
            for i, stage in enumerate(range(start_stage, end_stage + 1)):
                box_width = 150
                total_boxes_width = 4 * box_width + 3 * 20
                start_x = stage_area.x + (stage_area.width - total_boxes_width) // 2
                
                x = start_x + i * (box_width + 20)
                y = stage_area.centery - 80
                rect = pygame.Rect(x, y, box_width, 160)
                stage_buttons[stage] = rect
                
                if stage in completed_stages:
                    color = (100, 200, 100)
                    text_color = WHITE
                    status = "COMPLETED"
                elif stage <= current_stage:
                    color = (255, 215, 0)
                    text_color = (0, 0, 0)
                    status = "AVAILABLE"
                else:
                    color = (80, 80, 80)
                    text_color = (150, 150, 150)
                    status = "LOCKED"
                
                if stage == selected_stage:
                    border_color = (255, 255, 0)
                    border_width = 5
                else:
                    border_color = WHITE
                    border_width = 2
                
                pygame.draw.rect(virtual_surface, color, rect, border_radius=10)
                pygame.draw.rect(virtual_surface, border_color, rect, border_width, border_radius=10)
                
                stage_num_text = button_font.render(str(stage), True, text_color)
                virtual_surface.blit(stage_num_text, stage_num_text.get_rect(center=(rect.centerx, rect.y + 35)))
                
                status_text = small_font.render(status, True, text_color)
                virtual_surface.blit(status_text, status_text.get_rect(center=(rect.centerx, rect.y + 70)))
                
                if stage in completed_stages:
                    symbol_text = small_font.render("DONE", True, text_color)
                    virtual_surface.blit(symbol_text, symbol_text.get_rect(center=(rect.centerx, rect.y + 95)))
                    completed_text = small_font.render("Cannot Replay", True, text_color)
                    virtual_surface.blit(completed_text, completed_text.get_rect(center=(rect.centerx, rect.y + 135)))
                elif stage <= current_stage:
                    symbol_text = small_font.render("FIGHT", True, text_color)
                    virtual_surface.blit(symbol_text, symbol_text.get_rect(center=(rect.centerx, rect.y + 95)))
                else:
                    symbol_text = small_font.render("LOCK", True, text_color)
                    virtual_surface.blit(symbol_text, symbol_text.get_rect(center=(rect.centerx, rect.y + 110)))
            
            # Navigation arrows with icons
            if current_page > 0:
                arrow_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, arrow_color, prev_button, border_radius=30)
                
                if prev_icon:
                    icon_rect = prev_icon.get_rect(center=prev_button.center)
                    virtual_surface.blit(prev_icon, icon_rect)
                else:
                    prev_text = button_font.render("<", True, WHITE)
                    virtual_surface.blit(prev_text, prev_text.get_rect(center=prev_button.center))
            
            if current_page < total_pages - 1:
                arrow_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, arrow_color, next_button, border_radius=30)
                
                if next_icon:
                    icon_rect = next_icon.get_rect(center=next_button.center)
                    virtual_surface.blit(next_icon, icon_rect)
                else:
                    next_text = button_font.render(">", True, WHITE)
                    virtual_surface.blit(next_text, next_text.get_rect(center=next_button.center))
                
            # Selected stage info and start button
            if selected_stage:
                info_text = button_font.render(f"Selected Stage: {selected_stage}", True, WHITE)
                virtual_surface.blit(info_text, info_text.get_rect(center=(VIRTUAL_W // 2, 495)))
                
                # Start button
                if selected_stage <= current_stage and selected_stage not in completed_stages:
                    start_color = HOVER_COLOR if start_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
                    button_text = "START STAGE"
                else:
                    start_color = (100, 100, 100)
                    if selected_stage in completed_stages:
                        button_text = "COMPLETED"
                    else:
                        button_text = "LOCKED"
                        
                pygame.draw.rect(virtual_surface, start_color, start_button, border_radius=10)
                start_text = button_font.render(button_text, True, WHITE)
                virtual_surface.blit(start_text, start_text.get_rect(center=start_button.center))
            
            # Back button
            back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
            back_text = small_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
            
            # Milestone button
            milestone_color = HOVER_COLOR if milestone_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            pygame.draw.rect(virtual_surface, milestone_color, milestone_button, border_radius=8)
            milestone_text = small_font.render("MILESTONE", True, WHITE)
            virtual_surface.blit(milestone_text, milestone_text.get_rect(center=milestone_button.center))
            
            draw_scaled_centered()
            clock.tick(60)

    def story_battle(stage, selected_character):
        """Story mode battle system"""
        # Load and play story music
        try:
            pygame.mixer.music.load("assets/storybg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading story music: {e}")
        
        # Load battle background
        try:
            battle_bg = pygame.image.load("assets/storybattlebg.png").convert()
            battle_bg = pygame.transform.smoothscale(battle_bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            # Create dynamic background based on stage
            battle_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            base_color = ((stage * 3) % 255, (stage * 5) % 255, (stage * 7) % 255)
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = max(20, int(base_color[0] * ratio * 0.3))
                g = max(20, int(base_color[1] * ratio * 0.3))
                b = max(40, int(base_color[2] * ratio * 0.5))
                pygame.draw.line(battle_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
        
        # Player setup - Enhanced for story mode
        PLAYER_MAX_HP = 300
        PLAYER_MAX_MP = 200
        hp = PLAYER_MAX_HP
        mp = PLAYER_MAX_MP
        last_mp_regen = pygame.time.get_ticks()
        last_heal_time = 0
        heal_cooldown = 3000
        is_shielding = False
        is_dead = False
        is_hurt = False
        hurt_timer = 0
        death_animation_complete = False
        last_attack_time = 0
        
        # Load player animations
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
        anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])
        
        # Faster frame delays for story mode
        frame_delays = {
            "Idle": 100, "Run": 60, "Jump": 100, "Shield": 130,
            "Attack_1": 150, "Attack_2": 160, "Attack_3": 155,
            "Dead": 140, "Hurt": 100
        }
        
        # Player state
        action = "Idle"
        idx, timer = 0, 0
        pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
        vel = [0, 0]
        jumping = False
        jump_count = 2
        holding_shield = False
        
        # Create story enemy with enhanced stats
        enemy_characters = ["Samurai", "Soldier", "Magician", "Graffiti", "Kitsune", "Gangster", "Kunoichi"]
        enemy_type = random.choice(enemy_characters)
        enemy = Enemy(enemy_type, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)
        
        # Enhanced enemy stats for story mode
        enemy.hp = 150
        enemy.max_hp = 150
        enemy.movement_speed = 3 + (stage // 10)
        enemy.action_cooldown = max(800, 1500 - (stage * 5))
        
        # Story mode specific enemy damage
        story_enemy_damage = 25
        
        # Override enemy damage method
        def get_story_enemy_damage():
            return story_enemy_damage
        enemy.get_attack_damage = get_story_enemy_damage
        
        def check_collision_and_damage():
            nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
            
            # Enemy attacks player
            if enemy.is_attacking():
                distance = abs(enemy.pos[0] - pos[0])
                attack_range = enemy.get_attack_range()
                
                if distance < attack_range:
                    current_time = pygame.time.get_ticks()
                    if current_time - enemy.last_attack_time > 600:
                        damage = enemy.get_attack_damage()
                        
                        if is_shielding:
                            damage = 0
                        
                        if damage > 0:
                            hp -= damage
                            enemy.last_attack_time = current_time
                            
                            if hp <= 0:
                                hp = 0
                                is_dead = True
                                action = "Dead"
                                idx = 0
                                timer = 0
                            else:
                                is_hurt = True
                                hurt_timer = pygame.time.get_ticks()
                                action = "Hurt"
                                idx = 0
                                timer = 0
            
            # Player attacks enemy
            if "Attack" in action and idx > 0:
                distance = abs(pos[0] - enemy.pos[0])
                player_range = character_ranges[selected_character]
                
                if distance < player_range:
                    current_time = pygame.time.get_ticks()
                    if current_time - last_attack_time > 300:
                        damage = character_damage[selected_character][action]
                        enemy.take_damage(damage)
                        last_attack_time = current_time
        
        def draw_story_hud():
            # Enhanced HUD for story mode
            hud_bg = pygame.Rect(10, 10, 280, 120)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 200), hud_bg, border_radius=10)
            pygame.draw.rect(virtual_surface, WHITE, hud_bg, 2, border_radius=10)
            
            # HP bar (larger)
            pygame.draw.rect(virtual_surface, (100, 100, 100), (20, 25, 220, 15))
            hp_width = int((hp / PLAYER_MAX_HP) * 220)
            pygame.draw.rect(virtual_surface, (255, 0, 0), (20, 25, hp_width, 15))
            
            # MP bar
            pygame.draw.rect(virtual_surface, (50, 50, 50), (20, 45, 220, 15))
            mp_width = int((mp / PLAYER_MAX_MP) * 220)
            pygame.draw.rect(virtual_surface, (0, 0, 255), (20, 45, mp_width, 15))
            
            # Text labels
            hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
            virtual_surface.blit(hp_text, (20, 65))
            mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
            virtual_surface.blit(mp_text, (20, 85))
            
            # Character info
            character_text = small_font.render(f"Character: {selected_character}", True, WHITE)
            virtual_surface.blit(character_text, (20, 105))
            
            # Heal cooldown indicator
            current_time = pygame.time.get_ticks()
            heal_ready = (current_time - last_heal_time) >= heal_cooldown
            if heal_ready:
                heal_status_text = small_font.render("HEAL: Ready", True, SELECTED_COLOR)
            else:
                remaining = (heal_cooldown - (current_time - last_heal_time)) // 1000 + 1
                heal_status_text = small_font.render(f"HEAL: {remaining}s", True, RED)
            virtual_surface.blit(heal_status_text, (150, 85))
        
        # Enhanced UI setup with heal button
        size = 55
        spacing = 8
        dir_center_x = 80
        dir_center_y = VIRTUAL_H - 280

        left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
        right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
        up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
        down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

        # Action buttons including heal
        btn_w, btn_h = 75, 55
        action_y = VIRTUAL_H - btn_h - 8
        heal_y = action_y - btn_h - 8  # Heal button above other buttons
        
        action_buttons = {
            "atk1": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 6, action_y, btn_w, btn_h),
            "atk2": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 5, action_y, btn_w, btn_h),
            "atk3": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 4, action_y, btn_w, btn_h),
            "jump": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 3, action_y, btn_w, btn_h),
            "shield": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 2, action_y, btn_w, btn_h),
            "run": pygame.Rect(VIRTUAL_W - (btn_w + spacing), action_y, btn_w, btn_h),
            "heal": pygame.Rect(VIRTUAL_W - (btn_w + spacing), heal_y, btn_w, btn_h),
        }

        pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)
        
        # Main battle loop
        while True:
            dt = clock.tick(90)  # Higher FPS for smoother story mode
            timer += dt
            now = pygame.time.get_ticks()

            # Check battle end conditions
            if is_dead and death_animation_complete:
                pygame.mixer.music.stop()
                return show_story_result(False, stage, None, 0)
            
            if enemy.is_dead and enemy.death_animation_complete:
                # Generate random reward
                reward_types = ["sakura", "water", "black_water", "tengu_feathers"]
                reward_type = random.choice(reward_types)
                reward_amount = random.randint(1, 2)
                
                pygame.mixer.music.stop()
                return show_story_result(True, stage, reward_type, reward_amount)

            # Enhanced MP regeneration for story mode
            if now - last_mp_regen > 1500:  # Faster MP regen
                mp = min(PLAYER_MAX_MP, mp + 20)
                last_mp_regen = now

            # Handle hurt state
            if is_hurt and now - hurt_timer > 500:  # Faster recovery
                is_hurt = False
                if not is_dead:
                    action = "Idle"
                    idx = 0
                    timer = 0

            # Event handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    exit_game()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return "escape"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    mx, my = ((mx - ox) / scale, (my - oy) / scale)

                    if pause_button.collidepoint((mx, my)):
                        pause_result = pause_menu()
                        if pause_result == "back":
                            pygame.mixer.music.stop()
                            return "escape"
                        elif pause_result == "restart":
                            return story_battle(stage, selected_character)

                    if is_dead or is_hurt:
                        continue

                    # Enhanced movement controls
                    if left.collidepoint((mx, my)):
                        vel[0] = -6; action = "Run"; is_shielding = False
                    elif right.collidepoint((mx, my)):
                        vel[0] = 6; action = "Run"; is_shielding = False
                    elif up.collidepoint((mx, my)):
                        vel[1] = -6; action = "Run"; is_shielding = False
                    elif down.collidepoint((mx, my)):
                        vel[1] = 6; action = "Run"; is_shielding = False
                    # Action buttons
                    elif action_buttons["atk1"].collidepoint((mx, my)):
                        if mp >= 8:  # Reduced MP cost for story mode
                            action = "Attack_1"; idx = 0; timer = 0; mp -= 8; is_shielding = False
                    elif action_buttons["atk2"].collidepoint((mx, my)):
                        if mp >= 12:
                            action = "Attack_2"; idx = 0; timer = 0; mp -= 12; is_shielding = False
                    elif action_buttons["atk3"].collidepoint((mx, my)):
                        if mp >= 16:
                            action = "Attack_3"; idx = 0; timer = 0; mp -= 16; is_shielding = False
                    elif action_buttons["jump"].collidepoint((mx, my)):
                        if jump_count > 0:
                            vel[1] = -14; action = "Jump"; jumping = True
                            jump_count -= 1; idx = 0; timer = 0; is_shielding = False
                    elif action_buttons["shield"].collidepoint((mx, my)):
                        holding_shield = True; action = "Shield"; idx = 0; timer = 0; is_shielding = True
                    elif action_buttons["run"].collidepoint((mx, my)):
                        vel[0] = 10; action = "Run"; is_shielding = False
                    elif action_buttons["heal"].collidepoint((mx, my)):
                        # Heal ability
                        if (now - last_heal_time) >= heal_cooldown:
                            hp = min(PLAYER_MAX_HP, hp + 50)
                            last_heal_time = now

                if e.type == pygame.MOUSEBUTTONUP:
                    if not is_dead and not is_hurt:
                        vel = [0, 0]; holding_shield = False; is_shielding = False
                        if not jumping: action = "Idle"

            # Enhanced physics
            if not is_dead:
                if jumping:
                    vel[1] += 0.7  # Adjusted gravity
                    pos[1] += vel[1]
                    if pos[1] >= VIRTUAL_H - 150:
                        pos[1] = VIRTUAL_H - 150; jumping = False
                        vel[1] = 0; jump_count = 2
                        if not is_hurt: action = "Idle"
                else:
                    pos[0] += vel[0]
                    pos[1] += vel[1]

                # Screen bounds
                sprite_width = 160
                left_limit = sprite_width // 2
                right_limit = VIRTUAL_W - sprite_width // 2
                pos[0] = max(left_limit, min(right_limit, pos[0]))
                pos[1] = max(50, min(VIRTUAL_H - 160, pos[1]))

            # Update enemy
            enemy.update(dt, pos)
            check_collision_and_damage()

            # Update player animation
            delay = frame_delays.get(action, 90)
            if timer >= delay:
                timer = 0
                if anims[action]:
                    idx += 1
                    if idx >= len(anims[action]):
                        if action == "Dead":
                            death_animation_complete = True
                            idx = len(anims["Dead"]) - 1
                        elif "Attack" in action or action == "Jump":
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0
                        elif action == "Shield" and holding_shield:
                            idx = len(anims["Shield"]) - 1
                        elif action == "Hurt":
                            idx = len(anims["Hurt"]) - 1
                        else:
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0

            # Drawing
            virtual_surface.blit(battle_bg, (0, 0))
            
            # Draw player
            if anims[action]:
                frame_idx = min(idx, len(anims[action]) - 1)
                sprite = pygame.transform.scale(anims[action][frame_idx], (160, 160))
                rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                virtual_surface.blit(sprite, rect.topleft)
                
                if is_shielding:
                    shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                    shield_rect = shield_text.get_rect(center=(pos[0], pos[1] - 100))
                    virtual_surface.blit(shield_text, shield_rect)
            
            # Draw enemy
            enemy.draw(virtual_surface)

            # Draw controls
            if not is_dead:
                # Movement buttons
                for btn, symbol in [(left, "<"), (right, ">"), (up, "^"), (down, "v")]:
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, btn, border_radius=8)
                    txt = button_font.render(symbol, True, WHITE)
                    virtual_surface.blit(txt, txt.get_rect(center=btn.center))
                
                # Action buttons with enhanced visual feedback
                button_configs = [
                    ("atk1", "ATK1", 8), ("atk2", "ATK2", 12), ("atk3", "ATK3", 16),
                    ("jump", "JUMP", 0), ("shield", "SHIELD", 0), ("run", "RUN", 0)
                ]
                
                for btn_key, label, mp_cost in button_configs:
                    btn = action_buttons[btn_key]
                    
                    # Button color based on MP availability
                    if mp_cost > 0 and mp < mp_cost:
                        btn_color = (100, 100, 100)  # Disabled
                        text_color = (150, 150, 150)
                    else:
                        btn_color = BUTTON_COLOR
                        text_color = WHITE
                    
                    pygame.draw.rect(virtual_surface, btn_color, btn, border_radius=8)
                    pygame.draw.rect(virtual_surface, WHITE, btn, 2, border_radius=8)
                    
                    txt = small_font.render(label, True, text_color)
                    virtual_surface.blit(txt, txt.get_rect(center=btn.center))
                    
                    if mp_cost > 0:
                        mp_txt = small_font.render(str(mp_cost), True, (100, 200, 255))
                        virtual_surface.blit(mp_txt, (btn.x + 2, btn.y + 2))
                
                # Heal button with cooldown indicator
                heal_btn = action_buttons["heal"]
                current_time = pygame.time.get_ticks()
                heal_ready = (current_time - last_heal_time) >= heal_cooldown
                
                if heal_ready:
                    heal_color = SELECTED_COLOR
                    heal_text_color = WHITE
                    heal_label = "HEAL"
                else:
                    heal_color = (100, 100, 100)
                    heal_text_color = (150, 150, 150)
                    remaining = max(0, heal_cooldown - (current_time - last_heal_time)) // 1000 + 1
                    heal_label = f"HEAL\n{remaining}s"
                
                pygame.draw.rect(virtual_surface, heal_color, heal_btn, border_radius=8)
                pygame.draw.rect(virtual_surface, WHITE, heal_btn, 2, border_radius=8)
                
                heal_txt = small_font.render("HEAL", True, heal_text_color)
                virtual_surface.blit(heal_txt, heal_txt.get_rect(center=(heal_btn.centerx, heal_btn.centery - 5)))
                
                if not heal_ready:
                    cooldown_txt = small_font.render(f"{remaining}s", True, heal_text_color)
                    virtual_surface.blit(cooldown_txt, cooldown_txt.get_rect(center=(heal_btn.centerx, heal_btn.centery + 10)))

            # Draw pause button
            pause_color = HOVER_COLOR if pause_button.collidepoint(pygame.mouse.get_pos()) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, pause_color, pause_button, border_radius=8)
            pause_text = small_font.render("||", True, WHITE)
            virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))

            # Draw stage info
            stage_info = button_font.render(f"STAGE {stage}", True, get_rainbow_color())
            virtual_surface.blit(stage_info, stage_info.get_rect(center=(VIRTUAL_W // 2, 30)))

            # Draw story HUD
            draw_story_hud()

            draw_scaled_centered()
       
    def show_story_result(victory, stage, reward_type, reward_amount):
        """Enhanced story mode result screen with rewards"""
        # Load reward icons
        reward_icons = {}
        try:
            reward_icons["sakura"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/sakura.png").convert_alpha(), (80, 80))
            reward_icons["water"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/water.png").convert_alpha(), (80, 80))
            reward_icons["black_water"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), (80, 80))
            reward_icons["tengu_feathers"] = pygame.transform.scale(
                pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), (80, 80))
        except:
            # Create placeholder icons
            for reward in ["sakura", "water", "black_water", "tengu_feathers"]:
                icon = pygame.Surface((80, 80))
                icon.fill((100, 150, 200))
                reward_icons[reward] = icon

        # Update story data if victory
        story_data = load_story_data()
        milestone_rewards = {}
        
        if victory:
            # Add to completed stages
            if stage not in story_data["completed_stages"]:
                story_data["completed_stages"].append(stage)
            
            # Update current stage
            story_data["current_stage"] = max(story_data["current_stage"], stage + 1)
            
            # Add reward to story data AND to actual game resources
            if reward_type:
                story_data["total_rewards"][reward_type] += reward_amount
                
                # Add reward to dungeon_data and summer_data
                try:
                    if reward_type == "tengu_feathers":
                        dungeon_data = load_dungeon_data()
                        dungeon_data["tengu_feathers"] += reward_amount
                        save_dungeon_data(dungeon_data)
                    elif reward_type in ["sakura", "water", "black_water"]:
                        summer_data = load_summer_data()
                        summer_data[reward_type] += reward_amount
                        save_summer_data(summer_data)
                except Exception as e:
                    print(f"Error updating game resources: {e}")
            
            # Check for milestone rewards
            milestone_rewards = check_milestone_rewards(story_data)
            
            # Add milestone rewards to game resources
            if milestone_rewards:
                try:
                    dungeon_data = load_dungeon_data()
                    summer_data = load_summer_data()
                    
                    for reward_type, amount in milestone_rewards.items():
                        if reward_type == "tengu_feathers":
                            dungeon_data["tengu_feathers"] += amount
                        elif reward_type in ["sakura", "water", "black_water"]:
                            summer_data[reward_type] += amount
                    
                    save_dungeon_data(dungeon_data)
                    save_summer_data(summer_data)
                except Exception as e:
                    print(f"Error updating milestone rewards: {e}")
            
            # Save data
            save_story_data(story_data)

        # Create result background
        result_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        if victory:
            # Victory gradient (green-gold)
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = int(20 + ratio * 200)
                g = int(100 + ratio * 155)
                b = int(20 + ratio * 50)
                pygame.draw.line(result_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
        else:
            # Defeat gradient (red-dark)
            for y in range(VIRTUAL_H):
                ratio = y / VIRTUAL_H
                r = int(80 + ratio * 100)
                g = int(20 + ratio * 30)
                b = int(20 + ratio * 30)
                pygame.draw.line(result_bg, (r, g, b), (0, y), (VIRTUAL_W, y))

        continue_button = pygame.Rect(VIRTUAL_W//2 - 100, 450, 200, 60)
        retry_button = pygame.Rect(VIRTUAL_W//2 - 50, 450, 100, 60)
        menu_button = pygame.Rect(VIRTUAL_W//2 + 120, 450, 100, 60)

        # Show milestone rewards first if any
        if milestone_rewards:
            show_milestone_rewards(milestone_rewards)

        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if continue_button.collidepoint((vmx, vmy)):
                        return "continue"
                    elif retry_button.collidepoint((vmx, vmy)):
                        return "retry"
                    elif menu_button.collidepoint((vmx, vmy)):
                        return "menu"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        return "continue"
                    elif event.key == pygame.K_ESCAPE:
                        return "menu"

            # Draw result screen
            virtual_surface.blit(result_bg, (0, 0))

            # Title
            if victory:
                title_text = title_font.render("VICTORY!", True, get_rainbow_color())
                subtitle = button_font.render(f"Stage {stage} Completed!", True, WHITE)
            else:
                title_text = title_font.render("DEFEAT!", True, (255, 100, 100))
                subtitle = button_font.render(f"Stage {stage} Failed", True, WHITE)

            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
            virtual_surface.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 140)))

            if victory:
                # Result panel
                result_panel = pygame.Rect(VIRTUAL_W//2 - 200, 180, 400, 220)
                pygame.draw.rect(virtual_surface, (40, 40, 80, 220), result_panel, border_radius=15)
                pygame.draw.rect(virtual_surface, WHITE, result_panel, 3, border_radius=15)

                # Stage reward
                if reward_type:
                    reward_title = button_font.render("STAGE REWARD", True, (255, 215, 0))
                    virtual_surface.blit(reward_title, reward_title.get_rect(center=(VIRTUAL_W // 2, 210)))

                    # Draw reward icon and amount
                    if reward_type in reward_icons:
                        icon_rect = reward_icons[reward_type].get_rect(center=(VIRTUAL_W // 2, 260))
                        virtual_surface.blit(reward_icons[reward_type], icon_rect)

                    reward_name = reward_type.replace("_", " ").title()
                    reward_text = button_font.render(f"{reward_name} x{reward_amount}", True, WHITE)
                    virtual_surface.blit(reward_text, reward_text.get_rect(center=(VIRTUAL_W // 2, 320)))

                # Progress info
                progress_text = small_font.render(f"Completed Stages: {len(story_data['completed_stages'])}/300", True, WHITE)
                virtual_surface.blit(progress_text, progress_text.get_rect(center=(VIRTUAL_W // 2, 360)))

                # Next stage info
                if story_data["current_stage"] <= 300:
                    next_text = small_font.render(f"Next Stage: {story_data['current_stage']}", True, SELECTED_COLOR)
                    virtual_surface.blit(next_text, next_text.get_rect(center=(VIRTUAL_W // 2, 380)))
                else:
                    complete_text = small_font.render("ALL STAGES COMPLETED!", True, get_rainbow_color())
                    virtual_surface.blit(complete_text, complete_text.get_rect(center=(VIRTUAL_W // 2, 380)))

            # Buttons
            if victory:
                # Continue button
                continue_color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
                pygame.draw.rect(virtual_surface, continue_color, continue_button, border_radius=10)
                continue_text = button_font.render("CONTINUE", True, WHITE)
                virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
            else:
                # Retry button for defeat
                retry_color = HOVER_COLOR if retry_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, retry_color, retry_button, border_radius=10)
                retry_text = small_font.render("RETRY", True, WHITE)
                virtual_surface.blit(retry_text, retry_text.get_rect(center=retry_button.center))

            draw_scaled_centered()
            clock.tick(60)

    # Main story mode flow
    story_data = load_story_data()
    
    while True:
        # Character selection
        selected_character = story_character_selection_screen()
        if selected_character is None:
            return  # Back to main menu
        
        # Stage selection
        selected_stage = stage_selection_screen(story_data)
        if selected_stage is None:
            continue  # Back to character selection
        
        # Pre-battle dialog
        show_pre_battle_dialog(selected_character, selected_stage)
        
        # Battle
        battle_result = story_battle(selected_stage, selected_character)
        
        if battle_result == "escape":
            continue  # Back to stage selection
        elif battle_result == "continue":
            # Reload story data and continue
            story_data = load_story_data()
            continue
        elif battle_result == "retry":
            # Retry the same stage
            show_pre_battle_dialog(selected_character, selected_stage)
            battle_result = story_battle(selected_stage, selected_character)
            
            if battle_result == "continue":
                story_data = load_story_data()
                continue
            elif battle_result in ["menu", "escape"]:
                return
        elif battle_result == "menu":
            return  # Back to main menu
            
def add_battlepass_points():
    """Add random battlepass points after each battle"""
    try:
        battlepass_data = load_battlepass_data()
        
        # Random points between 1-5
        points_earned = random.randint(1, 5)
        battlepass_data["points"] += points_earned
        
        # Cap at maximum 5000 points
        if battlepass_data["points"] > 5000:
            battlepass_data["points"] = 5000
        
        save_battlepass_data(battlepass_data)
        
        # Return points earned for display purposes
        return points_earned
    except Exception as e:
        print(f"Error adding battlepass points: {e}")
        return 0

def get_battlepass_points():
    """Get current battlepass points"""
    try:
        battlepass_data = load_battlepass_data()
        return battlepass_data.get("points", 0)
    except:
        return 0

def reset_battlepass_if_needed():
    """Reset battlepass if 30 days have passed"""
    try:
        battlepass_data = load_battlepass_data()
        last_reset = datetime.fromisoformat(battlepass_data["last_reset"])
        
        # Check if 30 days have passed
        if (datetime.now() - last_reset).days >= 30:
            # Reset battlepass
            battlepass_data = {
                "points": 0,
                "claimed_rewards": [],
                "last_reset": datetime.now().isoformat()
            }
            save_battlepass_data(battlepass_data)
            return True
        return False
    except Exception as e:
        print(f"Error checking battlepass reset: {e}")
        return False

# Swordsman character frame counts
swordsman_frame_counts = {
    "Attack_1": 3,
    "Attack_2": 6,
    "Attack_3": 12,
    "Dead": 23,
    "Hurt": 6,
    "Idle": 10,
    "Jump": 6,
    "Shield": 11,
    "Run": 10,
    "Walk": 10
}

character_frame_counts["Swordsman"] = swordsman_frame_counts

# Update character damage untuk Karakter Swordsman
character_damage["Swordsman"] = {"Attack_1": 30, "Attack_2": 60, "Attack_3": 90}
character_ranges["Swordsman"] = 110

# Template untuk karakter Wizard
wizard_frame_counts = {
    "Attack_1": 8,
    "Attack_2": 8,
    "Attack_3": 8,
    "Dead": 7,
    "Hurt": 4,
    "Idle": 6,
    "Jump": 2,
    "Run": 8,
    "Shield": 2,
    "Walk": 8
}

character_frame_counts["Wizard"] = wizard_frame_counts

# Update character damage untuk Karakter Wizard
character_damage["Wizard"] = {"Attack_1": 25, "Attack_2": 50, "Attack_3": 95}
character_ranges["Wizard"] = 120

def load_battlepass_data():
    """Load battlepass progress data"""
    try:
        with open("battlepass_data.json", "r") as f:
            data = json.load(f)
            # Ensure all required keys exist
            if "points" not in data:
                data["points"] = 0
            if "claimed_rewards" not in data:
                data["claimed_rewards"] = []
            if "last_reset" not in data:
                data["last_reset"] = datetime.now().isoformat()
            return data
    except:
        # Create default data if file doesn't exist
        return {
            "points": 0,
            "claimed_rewards": [],
            "last_reset": datetime.now().isoformat()
        }

def save_battlepass_data(data):
    """Save battlepass progress data"""
    try:
        with open("battlepass_data.json", "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving battlepass data: {e}")

def battlepass():
    """Battlepass system with rewards - Level 5000"""
    # Check for reset first
    reset_battlepass_if_needed()
    
    # Load data
    battlepass_data = load_battlepass_data()
    character_data = load_character_data()
    dungeon_data = load_dungeon_data()
    summer_data = load_summer_data()
    
    # Battlepass background
    try:
        bp_bg = pygame.image.load("assets/battlepassbg.png").convert()
        bp_bg = pygame.transform.smoothscale(bp_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        bp_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        # Create gradient background
        for y in range(VIRTUAL_H):
            color_ratio = y / VIRTUAL_H
            r = int(30 + color_ratio * 40)
            g = int(20 + color_ratio * 50)
            b = int(50 + color_ratio * 60)
            pygame.draw.line(bp_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
    
    # Load resource icons
    try:
        feather_icon = pygame.transform.scale(
            pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), (40, 40))
        sakura_icon = pygame.transform.scale(
            pygame.image.load("assets/Drops/sakura.png").convert_alpha(), (40, 40))
        water_icon = pygame.transform.scale(
            pygame.image.load("assets/Drops/water.png").convert_alpha(), (40, 40))
        black_water_icon = pygame.transform.scale(
            pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), (40, 40))
        point_icon = pygame.Surface((40, 40))
        pygame.draw.circle(point_icon, (255, 215, 0), (20, 20), 18)
        
        # Swordsman icon
        swordsman_icon = pygame.image.load("assets/Swordsman/Idle.png").convert_alpha()
        frame_width = swordsman_icon.get_width() // swordsman_frame_counts["Idle"]
        swordsman_icon = swordsman_icon.subsurface(pygame.Rect(0, 0, frame_width, swordsman_icon.get_height()))
        swordsman_icon = pygame.transform.scale(swordsman_icon, (40, 40))
    except:
        # Placeholder icons
        feather_icon = pygame.Surface((40, 40))
        feather_icon.fill((255, 200, 100))
        sakura_icon = pygame.Surface((40, 40))
        sakura_icon.fill((255, 192, 203))
        water_icon = pygame.Surface((40, 40))
        water_icon.fill((100, 150, 255))
        black_water_icon = pygame.Surface((40, 40))
        black_water_icon.fill((50, 50, 50))
        point_icon = pygame.Surface((40, 40))
        pygame.draw.circle(point_icon, (255, 215, 0), (20, 20), 18)
        swordsman_icon = pygame.Surface((40, 40))
        swordsman_icon.fill((150, 150, 200))
    
    # Define rewards structure - Level 5000 system
    rewards = {
        # Page 1 (300-1500)
        300: {"tengu_feathers": 5, "icon": feather_icon},
        600: {"water": 5, "icon": water_icon},
        900: {"black_water": 5, "icon": black_water_icon},
        1200: {"tengu_feathers": 10, "icon": feather_icon},
        1500: {"sakura": 5, "icon": sakura_icon},
        
        # Page 2 (1800-3000)
        1800: {"tengu_feathers": 15, "icon": feather_icon},
        2100: {"water": 10, "icon": water_icon},
        2400: {"black_water": 10, "icon": black_water_icon},
        2700: {"sakura": 10, "icon": sakura_icon},
        3000: {"points": 200, "icon": point_icon},
        
        # Page 3 (3300-4500)
        3300: {"tengu_feathers": 25, "icon": feather_icon},
        3600: {"water": 25, "icon": water_icon},
        3900: {"black_water": 25, "icon": black_water_icon},
        4200: {"sakura": 25, "icon": sakura_icon},
        4500: {"points": 400, "icon": point_icon},
        
        # Page 4 (4600-5000)
        4600: {"tengu_feathers": 50, "icon": feather_icon},
        4700: {"water": 50, "icon": water_icon},
        4800: {"black_water": 50, "icon": black_water_icon},
        4900: {"sakura": 50, "icon": sakura_icon},
        5000: {"character": "Swordsman", "icon": swordsman_icon}
    }
    
    # Pages setup
    pages = [
        [300, 600, 900, 1200, 1500],          # Page 1
        [1800, 2100, 2400, 2700, 3000],       # Page 2
        [3300, 3600, 3900, 4200, 4500],       # Page 3
        [4600, 4700, 4800, 4900, 5000]        # Page 4
    ]
    
    current_page = 0
    max_pages = len(pages)
    
    # UI Elements
    back_button = pygame.Rect(20, 20, 80, 40)
    prev_button = pygame.Rect(50, VIRTUAL_H//2 - 30, 60, 60)
    next_button = pygame.Rect(VIRTUAL_W - 110, VIRTUAL_H//2 - 30, 60, 60)
    
    # Load navigation icons
    try:
        prev_icon = pygame.transform.scale(
            pygame.image.load("assets/previous.png").convert_alpha(), (40, 40))
        next_icon = pygame.transform.scale(
            pygame.image.load("assets/next.png").convert_alpha(), (40, 40))
    except:
        prev_icon = None
        next_icon = None
    
    # Message system
    message = ""
    message_color = WHITE
    message_timer = 0
    
    # Sound effect
    try:
        claim_sound = pygame.mixer.Sound("soundeffects/click.mp3")
        claim_sound.set_volume(0.7)
    except:
        claim_sound = None
    
    def claim_reward(level):
        nonlocal message, message_color, message_timer, battlepass_data, dungeon_data, summer_data, character_data
        
        if level in battlepass_data["claimed_rewards"]:
            message = f"Level {level} reward already claimed!"
            message_color = RED
            message_timer = pygame.time.get_ticks()
            return
        
        if battlepass_data["points"] < level:
            message = f"Need {level} points! You have {battlepass_data['points']}"
            message_color = RED
            message_timer = pygame.time.get_ticks()
            return
        
        # Play claim sound
        if claim_sound:
            claim_sound.play()
        
        # Process reward
        reward = rewards[level]
        reward_text = []
        
        if "tengu_feathers" in reward:
            dungeon_data["tengu_feathers"] += reward["tengu_feathers"]
            save_dungeon_data(dungeon_data)
            reward_text.append(f"{reward['tengu_feathers']} Tengu Feathers")
        
        if "sakura" in reward:
            summer_data["sakura"] += reward["sakura"]
            save_summer_data(summer_data)
            reward_text.append(f"{reward['sakura']} Sakura")
        
        if "water" in reward:
            summer_data["water"] += reward["water"]
            save_summer_data(summer_data)
            reward_text.append(f"{reward['water']} Water")
        
        if "black_water" in reward:
            summer_data["black_water"] += reward["black_water"]
            save_summer_data(summer_data)
            reward_text.append(f"{reward['black_water']} Black Water")
        
        if "points" in reward:
            battlepass_data["points"] += reward["points"]
            if battlepass_data["points"] > 5000:
                battlepass_data["points"] = 5000
            reward_text.append(f"+{reward['points']} Bonus Points")
        
        if "character" in reward:
            if reward["character"] not in character_data["owned_characters"]:
                character_data["owned_characters"].append(reward["character"])
                save_character_data(character_data)
                reward_text.append(f"{reward['character']} Character Unlocked!")
            else:
                # Already have Swordsman, give bonus points instead
                bonus_points = 1000
                battlepass_data["points"] += bonus_points
                if battlepass_data["points"] > 5000:
                    battlepass_data["points"] = 5000
                reward_text.append(f"Already own Swordsman - Bonus {bonus_points} Points!")
        
        # Mark as claimed
        battlepass_data["claimed_rewards"].append(level)
        save_battlepass_data(battlepass_data)
        
        message = f"Claimed: {', '.join(reward_text)}"
        message_color = SELECTED_COLOR
        message_timer = pygame.time.get_ticks()
    
    while True:
        current_time = pygame.time.get_ticks()
        virtual_surface.blit(bp_bg, (0, 0))
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    return
                
                # Navigation
                if prev_button.collidepoint((vmx, vmy)) and current_page > 0:
                    current_page -= 1
                elif next_button.collidepoint((vmx, vmy)) and current_page < max_pages - 1:
                    current_page += 1
                
                # Check reward clicks
                current_rewards = pages[current_page]
                for i, level in enumerate(current_rewards):
                    x = 100 + i * 120
                    y = 250
                    reward_rect = pygame.Rect(x, y, 100, 120)
                    if reward_rect.collidepoint((vmx, vmy)):
                        claim_reward(level)
        
        # Draw title
        title_text = title_font.render("BATTLE PASS", True, get_rainbow_color())
        virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
        
        # Draw points
        points_text = button_font.render(f"Points: {battlepass_data['points']}/5000", True, WHITE)
        virtual_surface.blit(points_text, points_text.get_rect(center=(VIRTUAL_W // 2, 100)))
        
        # Progress bar for overall battlepass
        progress_width = 600
        progress_height = 20
        progress_x = (VIRTUAL_W - progress_width) // 2
        progress_y = 130
        
        pygame.draw.rect(virtual_surface, (50, 50, 50), (progress_x, progress_y, progress_width, progress_height))
        filled_width = int((battlepass_data['points'] / 5000) * progress_width)
        pygame.draw.rect(virtual_surface, SELECTED_COLOR, (progress_x, progress_y, filled_width, progress_height))
        pygame.draw.rect(virtual_surface, WHITE, (progress_x, progress_y, progress_width, progress_height), 2)
        
        # Draw current page rewards
        current_rewards = pages[current_page]
        for i, level in enumerate(current_rewards):
            x = 100 + i * 120
            y = 250
            
            # Reward box
            reward_rect = pygame.Rect(x, y, 100, 120)
            
            # Check status
            is_claimed = level in battlepass_data["claimed_rewards"]
            can_claim = battlepass_data["points"] >= level and not is_claimed
            
            # Box color based on hover state
            if reward_rect.collidepoint((vmx, vmy)):
                if is_claimed:
                    box_color = (70, 70, 70)
                    border_color = (120, 120, 120)
                elif can_claim:
                    box_color = (70, 120, 70)
                    border_color = (100, 255, 100)
                else:
                    box_color = (100, 60, 60)
                    border_color = (170, 120, 120)
            else:
                if is_claimed:
                    box_color = (50, 50, 50)
                    border_color = (100, 100, 100)
                elif can_claim:
                    box_color = (50, 100, 50)
                    border_color = SELECTED_COLOR
                else:
                    box_color = (80, 40, 40)
                    border_color = (150, 100, 100)
            
            pygame.draw.rect(virtual_surface, box_color, reward_rect, border_radius=10)
            pygame.draw.rect(virtual_surface, border_color, reward_rect, 3, border_radius=10)
            
            # Level number
            level_text = button_font.render(str(level), True, WHITE)
            virtual_surface.blit(level_text, level_text.get_rect(center=(x + 50, y + 20)))
            
            # Reward icon
            reward = rewards[level]
            if "icon" in reward:
                icon_rect = reward["icon"].get_rect(center=(x + 50, y + 60))
                if is_claimed:
                    # Gray out claimed rewards
                    grayed_icon = reward["icon"].copy()
                    grayed_icon.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)
                    virtual_surface.blit(grayed_icon, icon_rect)
                else:
                    virtual_surface.blit(reward["icon"], icon_rect)
            
            # Reward amount/name
            reward_info = ""
            if "tengu_feathers" in reward:
                reward_info = f"x{reward['tengu_feathers']}"
            elif "sakura" in reward:
                reward_info = f"x{reward['sakura']}"
            elif "water" in reward:
                reward_info = f"x{reward['water']}"
            elif "black_water" in reward:
                reward_info = f"x{reward['black_water']}"
            elif "points" in reward:
                reward_info = f"+{reward['points']}pts"
            elif "character" in reward:
                reward_info = reward["character"]
            
            info_color = (150, 150, 150) if is_claimed else WHITE
            info_text = small_font.render(reward_info, True, info_color)
            virtual_surface.blit(info_text, info_text.get_rect(center=(x + 50, y + 95)))
            
            # Status indicator
            if is_claimed:
                status_text = small_font.render("CLAIMED", True, (100, 255, 100))
                virtual_surface.blit(status_text, status_text.get_rect(center=(x + 50, y + 110)))
            elif can_claim:
                # Blinking effect for claimable rewards
                if (current_time // 500) % 2:
                    status_text = small_font.render("CLAIM!", True, (255, 255, 0))
                    virtual_surface.blit(status_text, status_text.get_rect(center=(x + 50, y + 110)))
        
        # Draw navigation buttons
        if current_page > 0:
            prev_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, prev_color, prev_button, border_radius=30)
            if prev_icon:
                icon_rect = prev_icon.get_rect(center=prev_button.center)
                virtual_surface.blit(prev_icon, icon_rect)
            else:
                prev_text = button_font.render("<", True, WHITE)
                virtual_surface.blit(prev_text, prev_text.get_rect(center=prev_button.center))
        
        if current_page < max_pages - 1:
            next_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, next_color, next_button, border_radius=30)
            if next_icon:
                icon_rect = next_icon.get_rect(center=next_button.center)
                virtual_surface.blit(next_icon, icon_rect)
            else:
                next_text = button_font.render(">", True, WHITE)
                virtual_surface.blit(next_text, next_text.get_rect(center=next_button.center))
        
        # Page indicator
        page_text = small_font.render(f"Page {current_page + 1}/{max_pages}", True, WHITE)
        virtual_surface.blit(page_text, page_text.get_rect(center=(VIRTUAL_W // 2, 400)))
        
        # Reset timer info
        try:
            last_reset = datetime.fromisoformat(battlepass_data["last_reset"])
            next_reset = last_reset + timedelta(days=30)
            days_left = max(0, (next_reset - datetime.now()).days)
            reset_text = small_font.render(f"Resets in: {days_left} days", True, (200, 200, 200))
            virtual_surface.blit(reset_text, reset_text.get_rect(center=(VIRTUAL_W // 2, 420)))
        except:
            reset_text = small_font.render("Reset info unavailable", True, (200, 200, 200))
            virtual_surface.blit(reset_text, reset_text.get_rect(center=(VIRTUAL_W // 2, 420)))
        
        # Instructions
        info_text = small_font.render("Point grt from 1vs1, summer and dungeon. Each battle gets random battle points", True, (180, 180, 180))
        virtual_surface.blit(info_text, info_text.get_rect(center=(VIRTUAL_W // 2, 450)))
        
        # Total points info
        total_text = small_font.render(f"Total Points: {battlepass_data['points']}", True, (160, 160, 160))
        virtual_surface.blit(total_text, total_text.get_rect(center=(VIRTUAL_W // 2, 470)))
        
        # Draw message
        if message and current_time - message_timer < 4000:
            msg_surface = button_font.render(message, True, message_color)
            msg_rect = msg_surface.get_rect(center=(VIRTUAL_W // 2, 500))
            
            # Background for message
            bg_rect = msg_rect.inflate(40, 20)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), bg_rect, border_radius=10)
            virtual_surface.blit(msg_surface, msg_rect)
        
        # Draw back button
        back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
        back_text = small_font.render("Back", True, WHITE)
        virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
        
        draw_scaled_centered()
        clock.tick(60)

def expedition():
    """Expedition system for gathering resources"""
    import time
    import json
    import os
    import random  # Tambahkan import random
    
    # Load and play background music
    try:
        pygame.mixer.music.load("assets/expeditionbg.mp3")
        pygame.mixer.music.play(-1)  # Loop indefinitely
        pygame.mixer.music.set_volume(1.0)
    except:
        pass  # Music file not found, continue without music
    
    # Load data
    try:
        dungeon_data = load_dungeon_data()
    except:
        dungeon_data = {"tengu_feathers": 0}
    
    try:
        summer_data = load_summer_data()
    except:
        summer_data = {"sakura": 0, "water": 0, "black_water": 0}
    
    # Load expedition data
    def load_expedition_data():
        try:
            with open("expedition_data.json", "r") as f:
                return json.load(f)
        except:
            return {"active_expeditions": []}
    
    def save_expedition_data(data):
        try:
            with open("expedition_data.json", "w") as f:
                json.dump(data, f)
        except:
            pass
    
    expedition_data = load_expedition_data()
    
    # Expedition background
    try:
        expedition_bg = pygame.image.load("assets/expeditionbg.png").convert()
        expedition_bg = pygame.transform.smoothscale(expedition_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        expedition_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        # Create gradient background
        for y in range(VIRTUAL_H):
            color_ratio = y / VIRTUAL_H
            r = int(15 + color_ratio * 25)
            g = int(40 + color_ratio * 35)
            b = int(25 + color_ratio * 45)
            pygame.draw.line(expedition_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
    
    # Load resource icons
    resource_icons = {}
    icon_size = (45, 45)
    try:
        resource_icons["tengu_feathers"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), icon_size)
        resource_icons["sakura"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/sakura.png").convert_alpha(), icon_size)
        resource_icons["water"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/water.png").convert_alpha(), icon_size)
        resource_icons["black_water"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), icon_size)
    except:
        colors = [(255, 100, 100), (255, 192, 203), (100, 150, 255), (50, 50, 50)]
        for i, resource in enumerate(["tengu_feathers", "sakura", "water", "black_water"]):
            icon = pygame.Surface(icon_size, pygame.SRCALPHA)
            pygame.draw.circle(icon, colors[i], (icon_size[0]//2, icon_size[1]//2), icon_size[0]//2)
            resource_icons[resource] = icon
    
    # Expedition state
    selected_resource = None
    message = ""
    message_color = WHITE
    message_timer = 0
    
    # UI Layout
    back_button = pygame.Rect(15, 15, 100, 45)
    
    # Header section
    header_y = 70
    
    # Resource selection section
    resource_section_y = 140
    resource_buttons = {}
    button_width = 160
    button_height = 130
    spacing = 30
    total_width = 4 * button_width + 3 * spacing
    start_x = (VIRTUAL_W - total_width) // 2
    
    resources = ["tengu_feathers", "sakura", "water", "black_water"]
    for i, resource in enumerate(resources):
        x = start_x + i * (button_width + spacing)
        resource_buttons[resource] = pygame.Rect(x, resource_section_y, button_width, button_height)
    
    # Expedition button
    expedition_button = pygame.Rect(VIRTUAL_W//2 - 140, 300, 280, 60)
    
    # Active expeditions section
    active_section_y = 380
    
    # Resource names for display
    resource_names = {
        "tengu_feathers": "Tengu Feathers",
        "sakura": "Sakura Petals",
        "water": "Pure Water",
        "black_water": "Black Water"
    }
    
    def get_resource_amount(resource):
        if resource == "tengu_feathers":
            return dungeon_data.get("tengu_feathers", 0)
        else:
            return summer_data.get(resource, 0)
    
    def update_resource_amount(resource, new_amount):
        if resource == "tengu_feathers":
            dungeon_data["tengu_feathers"] = new_amount
            save_dungeon_data(dungeon_data)
        else:
            summer_data[resource] = new_amount
            save_summer_data(summer_data)
    
    def get_expedition_duration(amount):
        """Get expedition duration based on amount found"""
        if 1 <= amount <= 5:
            return 30 * 60  # 30 minutes in seconds
        elif 6 <= amount <= 10:
            return 60 * 60  # 1 hour in seconds
        elif 11 <= amount <= 15:
            return 2 * 60 * 60  # 2 hours in seconds
        elif 16 <= amount <= 20:
            return 3 * 60 * 60  # 3 hours in seconds
        return 30 * 60  # Default 30 minutes
    
    def has_active_expedition():
        """Check if player has any active expedition"""
        return len(expedition_data.get("active_expeditions", [])) > 0
    
    def get_active_expedition_resource():
        """Get the resource of current active expedition"""
        active_expeditions = expedition_data.get("active_expeditions", [])
        if active_expeditions:
            return active_expeditions[0]["resource"]
        return None
    
    def check_completed_expeditions():
        """Check and complete finished expeditions"""
        current_time = time.time()
        completed_expeditions = []
        completed_resources = []
        
        for i, exp in enumerate(expedition_data["active_expeditions"]):
            if current_time >= exp["end_time"]:
                # Complete expedition
                resource = exp["resource"]
                amount = exp["amount"]
                current_amount = get_resource_amount(resource)
                update_resource_amount(resource, current_amount + amount)
                
                completed_expeditions.append(i)
                completed_resources.append((resource, amount))
        
        # Remove completed expeditions (reverse order to maintain indices)
        for i in reversed(completed_expeditions):
            expedition_data["active_expeditions"].pop(i)
        
        if completed_expeditions:
            save_expedition_data(expedition_data)
            
            # Show completion message for completed expedition
            if completed_resources:
                resource, amount = completed_resources[0]
                return f"Expedition completed! Received {amount} {resource_names[resource]}"
        
        return None
    
    def format_time_remaining(seconds):
        """Format seconds into readable time format"""
        if seconds <= 0:
            return "Completed!"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def draw_button_with_shadow(surface, rect, color, hover_color, is_hovered, border_radius=8):
        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=border_radius)
        
        # Draw button
        button_color = hover_color if is_hovered else color
        pygame.draw.rect(surface, button_color, rect, border_radius=border_radius)
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=border_radius)
    
    def draw_expedition_progress_bar(surface, rect, progress, color):
        """Draw progress bar for expedition"""
        # Background
        pygame.draw.rect(surface, (40, 40, 40), rect, border_radius=5)
        
        # Progress fill
        if progress > 0:
            fill_width = int(rect.width * progress)
            fill_rect = pygame.Rect(rect.x, rect.y, fill_width, rect.height)
            pygame.draw.rect(surface, color, fill_rect, border_radius=5)
        
        # Border
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=5)
    
    def draw_text_with_outline(surface, text, font, color, outline_color, pos, center=True):
        """Draw text with outline for better readability"""
        # Draw outline
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline_surf = font.render(text, True, outline_color)
                    if center:
                        outline_rect = outline_surf.get_rect(center=(pos[0] + dx, pos[1] + dy))
                    else:
                        outline_rect = (pos[0] + dx, pos[1] + dy)
                    surface.blit(outline_surf, outline_rect)
        
        # Draw main text
        text_surf = font.render(text, True, color)
        if center:
            text_rect = text_surf.get_rect(center=pos)
        else:
            text_rect = pos
        surface.blit(text_surf, text_rect)
    
    # Main game loop
    while True:
        current_time_ms = pygame.time.get_ticks()
        current_time_s = time.time()
        
        # Check for completed expeditions and show completion message
        completion_message = check_completed_expeditions()
        if completion_message:
            message = completion_message
            message_color = (100, 255, 150)
            message_timer = pygame.time.get_ticks()
        
        virtual_surface.blit(expedition_bg, (0, 0))
        
        # Mouse handling
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Update message timer
        if message_timer > 0 and current_time_ms - message_timer > 4000:
            message = ""
            message_timer = 0
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    pygame.mixer.music.stop()
                    return
                
                # Resource selection
                for resource, rect in resource_buttons.items():
                    if rect.collidepoint((vmx, vmy)):
                        # Only allow selection if no active expedition
                        if not has_active_expedition():
                            selected_resource = resource
                
                # Expedition button
                if expedition_button.collidepoint((vmx, vmy)):
                    # Start expedition logic
                    if not selected_resource:
                        message = "Please select a resource first!"
                        message_color = (255, 200, 0)
                        message_timer = pygame.time.get_ticks()
                    elif has_active_expedition():
                        message = "You must wait for your current expedition to complete!"
                        message_color = (255, 150, 150)
                        message_timer = pygame.time.get_ticks()
                    else:
                        # Start expedition
                        amount_found = random.randint(1, 20)
                        duration = get_expedition_duration(amount_found)
                        end_time = time.time() + duration
                        
                        # Add to active expeditions (only one at a time)
                        new_expedition = {
                            "resource": selected_resource,
                            "amount": amount_found,
                            "start_time": time.time(),
                            "end_time": end_time,
                            "duration": duration
                        }
                        
                        expedition_data["active_expeditions"] = [new_expedition]  # Replace any existing expedition
                        save_expedition_data(expedition_data)
                        
                        # Show success message
                        duration_text = ""
                        if duration == 30 * 60:
                            duration_text = "30 minutes"
                        elif duration == 60 * 60:
                            duration_text = "1 hour"
                        elif duration == 2 * 60 * 60:
                            duration_text = "2 hours"
                        elif duration == 3 * 60 * 60:
                            duration_text = "3 hours"
                        
                        message = f"Expedition started! Found {amount_found} {resource_names[selected_resource]} - {duration_text}"
                        message_color = (100, 255, 150)
                        message_timer = pygame.time.get_ticks()
                        
                        # Reset selection after starting expedition
                        selected_resource = None
        
        # Draw header section
        draw_text_with_outline(virtual_surface, "EXPEDITION CENTER", title_font, WHITE, (0, 0, 0), (VIRTUAL_W // 2, header_y))
        
        subtitle_text = small_font.render("Send expeditions to gather resources • Only one expedition at a time", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(VIRTUAL_W // 2, header_y + 30))
        virtual_surface.blit(subtitle_text, subtitle_rect)
        
        # Draw resource selection section
        section_title = small_font.render("SELECT RESOURCE TO GATHER", True, (255, 215, 0))
        title_rect = section_title.get_rect(center=(VIRTUAL_W // 2, resource_section_y - 15))
        virtual_surface.blit(section_title, title_rect)
        
        # Get current active expedition resource
        active_resource = get_active_expedition_resource()
        
        for resource, rect in resource_buttons.items():
            current_amount = get_resource_amount(resource)
            is_hovered = rect.collidepoint((vmx, vmy))
            is_selected = selected_resource == resource
            
            # Check status
            is_current_active = (active_resource == resource)
            has_any_active = has_active_expedition()
            
            if is_current_active:
                color = (80, 80, 40)  # Current active color
                hover_color = (80, 80, 40)
                text_color = (200, 200, 150)
                status_text = "ACTIVE"
                status_color = (255, 255, 150)
                can_interact = False
            elif has_any_active:
                color = (60, 40, 40)  # Blocked by other active expedition
                hover_color = (60, 40, 40)
                text_color = (150, 150, 150)
                status_text = "BLOCKED"
                status_color = (200, 150, 150)
                can_interact = False
            elif is_selected:
                color = (70, 130, 180)
                hover_color = (100, 149, 237)
                text_color = WHITE
                status_text = "SELECTED"
                status_color = (150, 200, 255)
                can_interact = True
            else:
                color = (60, 60, 80)
                hover_color = (80, 80, 100)
                text_color = WHITE
                status_text = "AVAILABLE"
                status_color = (200, 200, 200)
                can_interact = True
            
            draw_button_with_shadow(virtual_surface, rect, color, hover_color, is_hovered and can_interact)
            
            # Draw resource icon
            if resource in resource_icons:
                icon_rect = resource_icons[resource].get_rect(center=(rect.centerx, rect.y + 35))
                if not can_interact:
                    # Draw grayed out icon
                    icon_copy = resource_icons[resource].copy()
                    icon_copy.fill((120, 120, 120), special_flags=pygame.BLEND_MULT)
                    virtual_surface.blit(icon_copy, icon_rect)
                else:
                    virtual_surface.blit(resource_icons[resource], icon_rect)
            
            # Draw resource name
            name_text = small_font.render(resource_names[resource], True, text_color)
            name_rect = name_text.get_rect(center=(rect.centerx, rect.y + 75))
            virtual_surface.blit(name_text, name_rect)
            
            # Draw current amount
            amount_text = small_font.render(f"Own: {current_amount}", True, (180, 180, 180))
            amount_rect = amount_text.get_rect(center=(rect.centerx, rect.y + 95))
            virtual_surface.blit(amount_text, amount_rect)
            
            # Draw status
            status_surface = small_font.render(status_text, True, status_color)
            status_rect = status_surface.get_rect(center=(rect.centerx, rect.bottom - 15))
            virtual_surface.blit(status_surface, status_rect)
        
        # Draw expedition button
        can_start = selected_resource is not None and not has_active_expedition()
        is_hovered = expedition_button.collidepoint((vmx, vmy)) and can_start
        
        if can_start:
            color = (34, 139, 34)
            hover_color = (50, 205, 50)
        else:
            color = (80, 80, 80)
            hover_color = (80, 80, 80)
        
        draw_button_with_shadow(virtual_surface, expedition_button, color, hover_color, is_hovered, 10)
        
        expedition_text = button_font.render("START EXPEDITION", True, WHITE)
        expedition_rect = expedition_text.get_rect(center=expedition_button.center)
        virtual_surface.blit(expedition_text, expedition_rect)
        
        # Draw active expeditions section
        if expedition_data["active_expeditions"]:
            active_title = button_font.render("ACTIVE EXPEDITION", True, (255, 215, 0))
            active_title_rect = active_title.get_rect(center=(VIRTUAL_W // 2, active_section_y))
            virtual_surface.blit(active_title, active_title_rect)
            
            y_offset = active_section_y + 35
            exp = expedition_data["active_expeditions"][0]  # Only one expedition
            resource = exp["resource"]
            amount = exp["amount"]
            end_time = exp["end_time"]
            
            time_remaining = end_time - current_time_s
            progress = max(0, min(1, 1 - (time_remaining / exp["duration"])))
            
            # Expedition panel
            panel_width = 650
            panel_height = 85
            panel_x = (VIRTUAL_W - panel_width) // 2
            panel_rect = pygame.Rect(panel_x, y_offset, panel_width, panel_height)
            
            pygame.draw.rect(virtual_surface, (40, 40, 60), panel_rect, border_radius=10)
            pygame.draw.rect(virtual_surface, (100, 100, 120), panel_rect, 2, border_radius=10)
            
            # Resource icon
            if resource in resource_icons:
                icon_rect = resource_icons[resource].get_rect(center=(panel_x + 40, y_offset + 42))
                virtual_surface.blit(resource_icons[resource], icon_rect)
            
            # Expedition info
            info_x = panel_x + 85
            resource_text = button_font.render(f"{resource_names[resource]}", True, WHITE)
            virtual_surface.blit(resource_text, (info_x, y_offset + 8))
            
            amount_text = small_font.render(f"Amount: {amount}", True, (200, 200, 200))
            virtual_surface.blit(amount_text, (info_x, y_offset + 35))
            
            time_text = small_font.render(f"Time: {format_time_remaining(time_remaining)}", True, (150, 200, 255))
            virtual_surface.blit(time_text, (info_x, y_offset + 58))
            
            # Progress bar
            progress_rect = pygame.Rect(panel_x + 400, y_offset + 30, 200, 25)
            progress_color = (100, 255, 150) if progress >= 1.0 else (100, 150, 255)
            draw_expedition_progress_bar(virtual_surface, progress_rect, progress, progress_color)
            
            # Progress percentage
            progress_text = small_font.render(f"{int(progress * 100)}%", True, WHITE)
            progress_text_rect = progress_text.get_rect(center=(progress_rect.centerx, progress_rect.centery))
            virtual_surface.blit(progress_text, progress_text_rect)
        
        # Draw message
        if message and message_timer > 0:
            time_passed = current_time_ms - message_timer
            if time_passed > 3500:
                fade_ratio = 1.0 - (time_passed - 3500) / 500
                alpha = max(0, int(255 * fade_ratio))
            else:
                alpha = 255
            
            if alpha > 0:
                msg_surface = button_font.render(message, True, message_color)
                msg_rect = msg_surface.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H - 80))
                
                bg_rect = msg_rect.inflate(80, 40)
                bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(bg_surface, (*message_color[:3], min(100, alpha//2)), bg_surface.get_rect(), border_radius=12)
                pygame.draw.rect(bg_surface, (*message_color[:3], alpha), bg_surface.get_rect(), 3, border_radius=12)
                
                virtual_surface.blit(bg_surface, bg_rect.topleft)
                
                if alpha < 255:
                    msg_surface.set_alpha(alpha)
                virtual_surface.blit(msg_surface, msg_rect)
        
        # Draw back button
        is_back_hovered = back_button.collidepoint((vmx, vmy))
        draw_button_with_shadow(virtual_surface, back_button, (100, 100, 120), (130, 130, 150), is_back_hovered)
        
        back_text = button_font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=back_button.center)
        virtual_surface.blit(back_text, back_rect)
        
        draw_scaled_centered()
        clock.tick(60)

def investment():
    """Investment system for game resources"""
    import math  # Add this import at the beginning
    
    # Load and play background music
    try:
        pygame.mixer.music.load("assets/investbg.mp3")
        pygame.mixer.music.play(-1)  # Loop indefinitely
        pygame.mixer.music.set_volume(1.0)
    except:
        pass  # Music file not found, continue without music
    
    # Load data
    try:
        dungeon_data = load_dungeon_data()
    except:
        dungeon_data = {"tengu_feathers": 0}
    
    try:
        summer_data = load_summer_data()
    except:
        summer_data = {"sakura": 0, "water": 0, "black_water": 0}
    
    # Investment background
    try:
        investment_bg = pygame.image.load("assets/investmentbg.png").convert()
        investment_bg = pygame.transform.smoothscale(investment_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        investment_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        # Create gradient background
        for y in range(VIRTUAL_H):
            color_ratio = y / VIRTUAL_H
            r = int(20 + color_ratio * 30)
            g = int(30 + color_ratio * 40)
            b = int(50 + color_ratio * 60)
            pygame.draw.line(investment_bg, (r, g, b), (0, y), (VIRTUAL_W, y))
    
    # Load resource icons
    resource_icons = {}
    icon_size = (40, 40)
    try:
        resource_icons["tengu_feathers"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha(), icon_size)
        resource_icons["sakura"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/sakura.png").convert_alpha(), icon_size)
        resource_icons["water"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/water.png").convert_alpha(), icon_size)
        resource_icons["black_water"] = pygame.transform.scale(
            pygame.image.load("assets/Drops/blackwater.png").convert_alpha(), icon_size)
    except:
        colors = [(255, 100, 100), (255, 192, 203), (100, 150, 255), (50, 50, 50)]
        for i, resource in enumerate(["tengu_feathers", "sakura", "water", "black_water"]):
            icon = pygame.Surface(icon_size, pygame.SRCALPHA)
            pygame.draw.circle(icon, colors[i], (icon_size[0]//2, icon_size[1]//2), icon_size[0]//2)
            resource_icons[resource] = icon
    
    # Investment state
    selected_resource = None
    investment_amount = 20
    message = ""
    message_color = WHITE
    message_timer = 0
    
    # UI Layout
    back_button = pygame.Rect(15, 15, 100, 45)
    
    # Header section
    header_y = 100
    
    # Resource selection section
    resource_section_y = 180
    resource_buttons = {}
    button_width = 160
    button_height = 100
    spacing = 20
    total_width = 4 * button_width + 3 * spacing
    start_x = (VIRTUAL_W - total_width) // 2
    
    resources = ["tengu_feathers", "sakura", "water", "black_water"]
    for i, resource in enumerate(resources):
        x = start_x + i * (button_width + spacing)
        resource_buttons[resource] = pygame.Rect(x, resource_section_y, button_width, button_height)
    
    # Amount selection section
    amount_section_y = 320
    amount_buttons = {}
    amounts = [20, 30, 40, 50, 60]
    amount_button_width = 70
    amount_button_height = 45
    amount_total_width = 5 * amount_button_width + 4 * 15
    amount_start_x = (VIRTUAL_W - amount_total_width) // 2
    
    for i, amount in enumerate(amounts):
        x = amount_start_x + i * (amount_button_width + 15)
        amount_buttons[amount] = pygame.Rect(x, amount_section_y, amount_button_width, amount_button_height)
    
    # Investment preview section
    preview_section_y = 390
    
    # Invest button
    invest_button = pygame.Rect(VIRTUAL_W//2 - 120, 440, 240, 55)
    
    # Message section
    message_section_y = 520
    
    # Resource names for display
    resource_names = {
        "tengu_feathers": "Tengu\nFeathers",
        "sakura": "Sakura\nPetals",
        "water": "Pure\nWater",
        "black_water": "Black\nWater"
    }
    
    def get_resource_amount(resource):
        if resource == "tengu_feathers":
            return dungeon_data.get("tengu_feathers", 0)
        else:
            return summer_data.get(resource, 0)
    
    def update_resource_amount(resource, new_amount):
        if resource == "tengu_feathers":
            dungeon_data["tengu_feathers"] = new_amount
            save_dungeon_data(dungeon_data)
        else:
            summer_data[resource] = new_amount
            save_summer_data(summer_data)
    
    def calculate_investment_result(amount):
        success = random.random() < 0.5
        if success:
            return int(amount * 1.5), True
        else:
            return int(amount * 0.5), False
    
    def show_insufficient_resources_screen(resource_name):
        """Show insufficient resources screen for 1.5 seconds"""
        start_time = pygame.time.get_ticks()
        
        # Create dark overlay background
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        overlay.fill((20, 20, 30))
        
        while True:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_time
            
            # Auto close after 1.5 seconds
            if elapsed >= 1500:
                break
            
            # Handle events (allow manual close)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return  # Allow manual close
            
            # Draw background
            virtual_surface.blit(overlay, (0, 0))
            
            # Create warning panel
            panel_width = 500
            panel_height = 300
            panel_x = (VIRTUAL_W - panel_width) // 2
            panel_y = (VIRTUAL_H - panel_height) // 2
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            
            # Draw panel with gradient
            panel_surface = pygame.Surface((panel_width, panel_height))
            for y in range(panel_height):
                ratio = y / panel_height
                r = int(80 + ratio * 20)
                g = int(40 + ratio * 10)
                b = int(40 + ratio * 10)
                pygame.draw.line(panel_surface, (r, g, b), (0, y), (panel_width, y))
            
            virtual_surface.blit(panel_surface, panel_rect.topleft)
            
            # Draw panel border with glow effect
            pygame.draw.rect(virtual_surface, (255, 100, 100), panel_rect, 4, border_radius=15)
            pygame.draw.rect(virtual_surface, (255, 150, 150), panel_rect, 2, border_radius=15)
            
            # Warning icon (triangle with exclamation)
            icon_size = 60
            icon_x = panel_x + panel_width // 2
            icon_y = panel_y + 60
            
            # Triangle
            triangle_points = [
                (icon_x, icon_y - icon_size // 2),
                (icon_x - icon_size // 2, icon_y + icon_size // 2),
                (icon_x + icon_size // 2, icon_y + icon_size // 2)
            ]
            pygame.draw.polygon(virtual_surface, (255, 200, 0), triangle_points)
            pygame.draw.polygon(virtual_surface, (255, 255, 100), triangle_points, 3)
            
            # Exclamation mark
            exclamation_rect = pygame.Rect(icon_x - 4, icon_y - 15, 8, 20)
            pygame.draw.rect(virtual_surface, (200, 50, 50), exclamation_rect, border_radius=4)
            pygame.draw.circle(virtual_surface, (200, 50, 50), (icon_x, icon_y + 15), 4)
            
            # Title - menggunakan button_font yang lebih kecil
            title_text = button_font.render("INSUFFICIENT RESOURCES", True, (255, 100, 100))
            title_rect = title_text.get_rect(center=(icon_x, panel_y + 130))
            
            # Pastikan title tidak keluar dari panel
            if title_rect.width > panel_width - 40:  # 20px margin dari kiri kanan
                # Jika masih terlalu besar, gunakan small_font
                title_text = small_font.render("INSUFFICIENT RESOURCES", True, (255, 100, 100))
                title_rect = title_text.get_rect(center=(icon_x, panel_y + 130))
                
                # Jika masih terlalu besar, pecah menjadi dua baris
                if title_rect.width > panel_width - 40:
                    title_line1 = small_font.render("INSUFFICIENT", True, (255, 100, 100))
                    title_line2 = small_font.render("RESOURCES", True, (255, 100, 100))
                    
                    title_rect1 = title_line1.get_rect(center=(icon_x, panel_y + 120))
                    title_rect2 = title_line2.get_rect(center=(icon_x, panel_y + 140))
                    
                    virtual_surface.blit(title_line1, title_rect1)
                    virtual_surface.blit(title_line2, title_rect2)
                else:
                    virtual_surface.blit(title_text, title_rect)
            else:
                virtual_surface.blit(title_text, title_rect)
            
            # Message
            message_lines = [
                f"You don't have enough {resource_name}",
                f"Required: {investment_amount}",
                f"Available: {get_resource_amount(selected_resource)}"
            ]
            
            y_offset = panel_y + 170
            for line in message_lines:
                if "Required:" in line:
                    color = (255, 150, 150)
                elif "Available:" in line:
                    color = (150, 150, 255)
                else:
                    color = WHITE
                
                # Gunakan small_font untuk message agar pasti muat
                line_text = small_font.render(line, True, color)
                line_rect = line_text.get_rect(center=(icon_x, y_offset))
                
                # Pastikan text tidak keluar dari panel
                if line_rect.width > panel_width - 40:
                    # Jika terlalu panjang, potong text
                    words = line.split()
                    if len(words) > 1:
                        # Coba dengan kata yang lebih pendek
                        short_line = ' '.join(words[:2]) + "..."
                        line_text = small_font.render(short_line, True, color)
                        line_rect = line_text.get_rect(center=(icon_x, y_offset))
                
                virtual_surface.blit(line_text, line_rect)
                y_offset += 25  # Spacing yang lebih kecil
            
            # Progress bar showing auto-close timer
            progress_width = min(300, panel_width - 40)  # Maksimal 300 atau lebar panel - margin
            progress_height = 8
            progress_x = (VIRTUAL_W - progress_width) // 2
            progress_y = panel_y + panel_height - 40
            
            # Background bar
            progress_bg = pygame.Rect(progress_x, progress_y, progress_width, progress_height)
            pygame.draw.rect(virtual_surface, (60, 60, 60), progress_bg, border_radius=4)
            
            # Progress fill
            progress_ratio = elapsed / 1500
            fill_width = int(progress_width * progress_ratio)
            if fill_width > 0:
                progress_fill = pygame.Rect(progress_x, progress_y, fill_width, progress_height)
                # Color changes from red to yellow as time progresses
                r = int(255 - progress_ratio * 100)
                g = int(100 + progress_ratio * 155)
                b = 100
                pygame.draw.rect(virtual_surface, (r, g, b), progress_fill, border_radius=4)
            
            # Auto-close text - diperkecil agar muat
            remaining = (1500 - elapsed) / 1000
            
            # Pulsing effect for the panel border
            pulse = 0.7 + 0.3 * abs(math.sin(elapsed * 0.01))
            pulse_color = tuple(int(c * pulse) for c in (255, 100, 100))
            pygame.draw.rect(virtual_surface, pulse_color, panel_rect, 2, border_radius=15)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def perform_investment():
        nonlocal message, message_color, message_timer
        
        if not selected_resource:
            message = "Please select a resource first!"
            message_color = (255, 200, 0)
            message_timer = pygame.time.get_ticks()
            return
        
        current_amount = get_resource_amount(selected_resource)
        
        if current_amount < investment_amount:
            # Show insufficient resources screen instead of message
            resource_display_name = resource_names[selected_resource].replace('\n', ' ')
            show_insufficient_resources_screen(resource_display_name)
            return
        
        # Perform investment
        new_current = current_amount - investment_amount
        update_resource_amount(selected_resource, new_current)
        
        result_amount, success = calculate_investment_result(investment_amount)
        final_amount = new_current + result_amount
        update_resource_amount(selected_resource, final_amount)
        
        # Show result
        if success:
            profit = result_amount - investment_amount
            message = f"SUCCESS! Profit: +{profit} resources"
            message_color = (100, 255, 150)
        else:
            loss = investment_amount - result_amount
            message = f"FAILED! Loss: -{loss} resources"
            message_color = (255, 120, 120)
        
        message_timer = pygame.time.get_ticks()
    
    def draw_button_with_shadow(surface, rect, color, hover_color, is_hovered, border_radius=8):
        # Draw shadow
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=border_radius)
        
        # Draw button
        button_color = hover_color if is_hovered else color
        pygame.draw.rect(surface, button_color, rect, border_radius=border_radius)
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=border_radius)
    
    while True:
        current_time = pygame.time.get_ticks()
        virtual_surface.blit(investment_bg, (0, 0))
        
        # Mouse handling
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Update message timer
        if message_timer > 0 and current_time - message_timer > 3500:
            message = ""
            message_timer = 0
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint((vmx, vmy)):
                    pygame.mixer.music.stop()
                    return
                
                # Resource selection
                for resource, rect in resource_buttons.items():
                    if rect.collidepoint((vmx, vmy)):
                        selected_resource = resource
                
                # Amount selection
                for amount, rect in amount_buttons.items():
                    if rect.collidepoint((vmx, vmy)):
                        if selected_resource and get_resource_amount(selected_resource) >= amount:
                            investment_amount = amount
                
                # Invest button
                if invest_button.collidepoint((vmx, vmy)):
                    perform_investment()
        
        # Draw main interface
        # Draw header section
        title_text = title_font.render("INVESTMENT CENTER", True, WHITE)
        title_rect = title_text.get_rect(center=(VIRTUAL_W // 2, header_y))
        virtual_surface.blit(title_text, title_rect)
        
        subtitle_text = small_font.render("Risk your resources for potential rewards • 50% Success Rate", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(VIRTUAL_W // 2, header_y + 40))
        virtual_surface.blit(subtitle_text, subtitle_rect)
        
        # Draw resource selection section
        section_title = button_font.render("SELECT RESOURCE", True, (255, 215, 0))
        virtual_surface.blit(section_title, (start_x, resource_section_y - 35))
        
        for resource, rect in resource_buttons.items():
            current_amount = get_resource_amount(resource)
            is_hovered = rect.collidepoint((vmx, vmy))
            is_selected = selected_resource == resource
            
            if is_selected:
                color = (70, 130, 180)
                hover_color = (100, 149, 237)
            else:
                color = (60, 60, 80)
                hover_color = (80, 80, 100)
            
            draw_button_with_shadow(virtual_surface, rect, color, hover_color, is_hovered)
            
            if resource in resource_icons:
                icon_rect = resource_icons[resource].get_rect(center=(rect.centerx, rect.y + 30))
                virtual_surface.blit(resource_icons[resource], icon_rect)
            
            lines = resource_names[resource].split('\n')
            for i, line in enumerate(lines):
                name_text = small_font.render(line, True, WHITE)
                name_rect = name_text.get_rect(center=(rect.centerx, rect.y + 60 + i * 15))
                virtual_surface.blit(name_text, name_rect)
            
            amount_text = small_font.render(f"Own: {current_amount}", True, (200, 200, 200))
            amount_rect = amount_text.get_rect(center=(rect.centerx, rect.bottom - 12))
            virtual_surface.blit(amount_text, amount_rect)
        
        # Draw amount selection section
        amount_title = button_font.render("INVESTMENT AMOUNT", True, (255, 215, 0))
        virtual_surface.blit(amount_title, (amount_start_x, amount_section_y - 35))
        
        for amount, rect in amount_buttons.items():
            can_invest = selected_resource and get_resource_amount(selected_resource) >= amount
            is_hovered = rect.collidepoint((vmx, vmy)) and can_invest
            is_selected = investment_amount == amount
            
            if not can_invest:
                color = (40, 40, 40)
                hover_color = (40, 40, 40)
                text_color = (100, 100, 100)
            elif is_selected:
                color = (34, 139, 34)
                hover_color = (50, 205, 50)
                text_color = WHITE
            else:
                color = (60, 60, 80)
                hover_color = (80, 80, 100)
                text_color = WHITE
            
            draw_button_with_shadow(virtual_surface, rect, color, hover_color, is_hovered, 6)
            
            amount_text = button_font.render(str(amount), True, text_color)
            amount_rect = amount_text.get_rect(center=rect.center)
            virtual_surface.blit(amount_text, amount_rect)
        
        # Draw investment preview
        if selected_resource and investment_amount:
            success_result = int(investment_amount * 1.5)
            failure_result = int(investment_amount * 0.5)
            profit = success_result - investment_amount
            loss = investment_amount - failure_result
            
            preview_bg = pygame.Rect(VIRTUAL_W//2 - 200, preview_section_y - 5, 400, 35)
            pygame.draw.rect(virtual_surface, (30, 30, 50, 180), preview_bg, border_radius=8)
            pygame.draw.rect(virtual_surface, (100, 100, 120), preview_bg, 2, border_radius=8)
            
            preview_text = small_font.render(f"Success: +{profit} • Failure: -{loss}", True, WHITE)
            preview_rect = preview_text.get_rect(center=preview_bg.center)
            virtual_surface.blit(preview_text, preview_rect)
        
        # Draw invest button
        can_invest = (selected_resource and 
                     get_resource_amount(selected_resource) >= investment_amount)
        
        is_hovered = invest_button.collidepoint((vmx, vmy)) and can_invest
        
        if can_invest:
            color = (220, 20, 60)
            hover_color = (255, 69, 0)
        else:
            color = (80, 80, 80)
            hover_color = (80, 80, 80)
        
        draw_button_with_shadow(virtual_surface, invest_button, color, hover_color, is_hovered, 10)
        
        invest_text = button_font.render("INVEST NOW", True, WHITE)
        invest_rect = invest_text.get_rect(center=invest_button.center)
        virtual_surface.blit(invest_text, invest_rect)
        
        # Draw message (only for success/failure, not insufficient resources)
        if message and message_timer > 0:
            time_passed = current_time - message_timer
            if time_passed > 3000:
                fade_ratio = 1.0 - (time_passed - 3000) / 500
                alpha = max(0, int(255 * fade_ratio))
            else:
                alpha = 255
            
            if alpha > 0:
                msg_surface = button_font.render(message, True, message_color)
                msg_rect = msg_surface.get_rect(center=(VIRTUAL_W // 2, message_section_y))
                
                bg_rect = msg_rect.inflate(60, 30)
                bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(bg_surface, (*message_color[:3], min(100, alpha//2)), bg_surface.get_rect(), border_radius=12)
                pygame.draw.rect(bg_surface, (*message_color[:3], alpha), bg_surface.get_rect(), 3, border_radius=12)
                
                virtual_surface.blit(bg_surface, bg_rect.topleft)
                
                if alpha < 255:
                    msg_surface.set_alpha(alpha)
                virtual_surface.blit(msg_surface, msg_rect)
        
        # Draw current resources panel
        panel_rect = pygame.Rect(20, VIRTUAL_H - 70, VIRTUAL_W - 40, 50)
        pygame.draw.rect(virtual_surface, (20, 20, 40, 200), panel_rect, border_radius=8)
        pygame.draw.rect(virtual_surface, (100, 100, 120), panel_rect, 2, border_radius=8)
        
        resources_title = small_font.render("Current Resources:", True, (255, 215, 0))
        virtual_surface.blit(resources_title, (30, VIRTUAL_H - 65))
        
        x_offset = 30
        for i, resource in enumerate(resources):
            amount = get_resource_amount(resource)
            display_name = resource_names[resource].replace('\n', ' ')
            
            if resource == selected_resource:
                text_color = (100, 255, 150)
            else:
                text_color = WHITE
            
            resource_text = small_font.render(f"{display_name}: {amount}", True, text_color)
            virtual_surface.blit(resource_text, (x_offset, VIRTUAL_H - 45))
            x_offset += 180
        
        # Draw back button
        is_back_hovered = back_button.collidepoint((vmx, vmy))
        draw_button_with_shadow(virtual_surface, back_button, (100, 100, 120), (130, 130, 150), is_back_hovered)
        
        back_text = button_font.render("Back", True, WHITE)
        back_rect = back_text.get_rect(center=back_button.center)
        virtual_surface.blit(back_text, back_rect)
        
        draw_scaled_centered()
        clock.tick(60)            
                                    
# Gacha data file
GACHA_DATA_FILE = "gacha_data.json"

# Yurei frame counts
yurei_frame_counts = {
    "Attack_1": 4,
    "Attack_2": 7,
    "Attack_3": 7,
    "Dead": 4,
    "Hurt": 3,
    "Idle": 5,
    "Jump": 5,
    "Run": 5,
    "Shield": 4,
    "Walk": 5
}

character_frame_counts["Yurei"] = yurei_frame_counts

# Yurei damage values
character_damage["Yurei"] = {
       "Attack_1": 20,
       "Attack_2": 30,
       "Attack_3": 45
}   

# Yurei attack range
character_ranges["Yurei"] = 90  # Adjust the range as needed

# Load/Save gacha data
def load_gacha_data():
    if os.path.exists(GACHA_DATA_FILE):
        try:
            with open(GACHA_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "yurei_permanent": False,
        "yurei_trial_end": "",
        "gacha_history": []
    }

def save_gacha_data(data):
    with open(GACHA_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_yurei_trial_status():
    """Check if Yurei trial has expired"""
    gacha_data = load_gacha_data()
    
    if gacha_data["yurei_trial_end"]:
        try:
            end_time = datetime.fromisoformat(gacha_data["yurei_trial_end"])
            if datetime.now() > end_time:
                # Trial expired, remove trial status
                gacha_data["yurei_trial_end"] = ""
                save_gacha_data(gacha_data)
                return False
            return True
        except:
            return False
    return False

def is_yurei_available():
    """Check if Yurei is currently available (permanent or trial active)"""
    gacha_data = load_gacha_data()
    return gacha_data["yurei_permanent"] or check_yurei_trial_status()

def get_red_white_color(time_offset=0):
    """Generate alternating red-white color for title"""
    import math
    time_factor = (pygame.time.get_ticks() + time_offset) * 0.005
    color_value = int(127 + 128 * math.sin(time_factor))
    return (255, color_value, color_value)

def gacha():
    """Enhanced gacha function with improved visual effects and optimizations"""
    # Import datetime at the top to avoid conflicts
    import datetime
    from datetime import timedelta
    import math
    import random
    
    # Initialize and play background music
    try:
        pygame.mixer.music.load("assets/gachabg.mp3")
        pygame.mixer.music.set_volume(1.0)  # Set volume to 50%
        pygame.mixer.music.play(-1)  # Loop indefinitely
    except pygame.error as e:
        print(f"Could not load background music: {e}")
    
    # Load necessary data
    global particle_systems
    particle_systems = []
    dungeon_data = load_dungeon_data()
    gacha_data = load_gacha_data()
    
    # Pre-cache surfaces for better performance
    cached_backgrounds = {}
    particle_systems = []
    
    # Load gacha background with caching
    def get_background(bg_type="main"):
        if bg_type not in cached_backgrounds:
            try:
                if bg_type == "main":
                    bg = pygame.image.load("assets/gachabg.png").convert()
                    cached_backgrounds[bg_type] = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
                else:
                    # Create different gradient backgrounds
                    bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
                    if bg_type == "spinning":
                        colors = [(40, 20, 80), (100, 50, 140)]
                    elif bg_type == "results":
                        colors = [(60, 30, 100), (100, 50, 160)]
                    else:
                        colors = [(20, 10, 60), (60, 30, 120)]
                    
                    for y in range(VIRTUAL_H):
                        ratio = y / VIRTUAL_H
                        r = int(colors[0][0] + ratio * (colors[1][0] - colors[0][0]))
                        g = int(colors[0][1] + ratio * (colors[1][1] - colors[0][1]))
                        b = int(colors[0][2] + ratio * (colors[1][2] - colors[0][2]))
                        pygame.draw.line(bg, (r, g, b), (0, y), (VIRTUAL_W, y))
                    cached_backgrounds[bg_type] = bg
            except:
                # Fallback gradient
                bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
                for y in range(VIRTUAL_H):
                    color_ratio = y / VIRTUAL_H
                    r = int(20 + color_ratio * 40)
                    g = int(10 + color_ratio * 30)
                    b = int(60 + color_ratio * 80)
                    pygame.draw.line(bg, (r, g, b), (0, y), (VIRTUAL_W, y))
                cached_backgrounds[bg_type] = bg
        return cached_backgrounds[bg_type]
    
    # Load and cache Yurei preview
    yurei_preview = None
    try:
        idle_sheet = pygame.image.load("assets/Yurei/Idle.png").convert_alpha()
        frame_width = idle_sheet.get_width() // yurei_frame_counts["Idle"]
        preview = idle_sheet.subsurface(pygame.Rect(0, 0, frame_width, idle_sheet.get_height()))
        yurei_preview = pygame.transform.scale(preview, (100, 100))
    except Exception as e:
        print(f"Error loading Yurei preview: {e}")
        yurei_preview = pygame.Surface((100, 100))
        yurei_preview.fill((150, 150, 200))
    
    # Load and cache Tengu Feather icon
    try:
        feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
        feather_icon = pygame.transform.scale(feather_icon, (30, 30))
    except:
        feather_icon = None
    
    # Enhanced particle system
    class Particle:
        def __init__(self, x, y, vx, vy, color, size, life):
            self.x, self.y = x, y
            self.vx, self.vy = vx, vy
            self.color = color
            self.size = size
            self.life = life
            self.max_life = life
            
        def update(self):
            self.x += self.vx
            self.y += self.vy
            self.vy += 0.1  # Gravity
            self.life -= 1
            self.vx *= 0.99  # Air resistance
            
        def draw(self, surface):
            if self.life > 0:
                alpha = int(255 * (self.life / self.max_life))
                color = (*self.color[:3], alpha) if len(self.color) == 4 else self.color
                size = max(1, int(self.size * (self.life / self.max_life)))
                pygame.draw.circle(surface, color, (int(self.x), int(self.y)), size)
    
    def create_particles(x, y, count, color_base):
        """Create particle burst effect"""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(2, 5)
            
            # Color variation
            color = [max(0, min(255, c + random.randint(-30, 30))) for c in color_base]
            size = random.randint(2, 6)
            life = random.randint(30, 60)
            
            particle_systems.append(Particle(x, y, vx, vy, color, size, life))
    
    def update_and_draw_particles(surface):
        global particle_systems
        alive_particles = []
        for particle in particle_systems:
            particle.update()
            if particle.life > 0:
                particle.draw(surface)
                alive_particles.append(particle)
        particle_systems = alive_particles
    
    # Enhanced button with hover effects
    class EnhancedButton:
        def __init__(self, rect, text, font, cost_text="", enabled_color=BUTTON_COLOR, disabled_color=(100, 100, 100)):
            self.rect = rect
            self.text = text
            self.font = font
            self.cost_text = cost_text
            self.enabled_color = enabled_color
            self.disabled_color = disabled_color
            self.hover_scale = 1.0
            self.pulse = 0
            
        def update(self, dt):
            self.pulse += dt * 0.005
            
        def draw(self, surface, enabled, hovered, mx, my):
            # Smooth hover animation
            target_scale = 1.05 if hovered and enabled else 1.0
            self.hover_scale += (target_scale - self.hover_scale) * 0.2
            
            # Draw button with scale effect
            scaled_rect = pygame.Rect(self.rect)
            if self.hover_scale != 1.0:
                center = self.rect.center
                scaled_rect.width = int(self.rect.width * self.hover_scale)
                scaled_rect.height = int(self.rect.height * self.hover_scale)
                scaled_rect.center = center
            
            # Button color with pulse effect for enabled buttons
            color = self.enabled_color if enabled else self.disabled_color
            if enabled and hovered:
                pulse_brightness = int(30 * math.sin(self.pulse))
                color = tuple(min(255, c + pulse_brightness) for c in HOVER_COLOR)
            
            # Draw shadow
            shadow_rect = scaled_rect.copy()
            shadow_rect.x += 3
            shadow_rect.y += 3
            pygame.draw.rect(surface, (20, 20, 20), shadow_rect, border_radius=10)
            
            # Draw main button
            pygame.draw.rect(surface, color, scaled_rect, border_radius=10)
            if enabled:
                pygame.draw.rect(surface, (255, 255, 255), scaled_rect, 2, border_radius=10)
            
            # Draw text
            main_text = self.font.render(self.text, True, WHITE)
            text_rect = main_text.get_rect(center=(scaled_rect.centerx, scaled_rect.centery - 12))
            surface.blit(main_text, text_rect)
            
            if self.cost_text:
                cost_surface = small_font.render(self.cost_text, True, WHITE)
                cost_rect = cost_surface.get_rect(center=(scaled_rect.centerx, scaled_rect.centery + 18))
                surface.blit(cost_surface, cost_rect)
    
    # Animation states
    spin_animation = 0
    spinning = False
    spin_results = []
    show_results = False
    result_timer = 0
    screen_shake = 0
    
    def gacha_main_screen():
        nonlocal spinning, spin_animation, spin_results, show_results, result_timer, screen_shake
        
        # Enhanced UI buttons
        buttons = {
            'spin_1x': EnhancedButton(pygame.Rect(120, 350, 160, 80), "1x SPIN", button_font, "10 Feathers"),
            'spin_3x': EnhancedButton(pygame.Rect(320, 350, 160, 80), "3x SPIN", button_font, "30 Feathers"),
            'rewards': EnhancedButton(pygame.Rect(520, 350, 160, 80), "REWARDS", button_font),
            'history': EnhancedButton(pygame.Rect(50, 450, 120, 50), "HISTORY", small_font),
            'back': EnhancedButton(pygame.Rect(50, 50, 80, 50), "Back", small_font)
        }
        
        machine_glow = 0
        last_time = pygame.time.get_ticks()
        
        while True:
            current_time = pygame.time.get_ticks()
            dt = current_time - last_time
            last_time = current_time
            
            # Apply screen shake
            shake_offset_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
            shake_offset_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
            screen_shake = max(0, screen_shake - 1)
            
            # Get mouse position
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            # Handle spinning animation
            if spinning:
                return show_spinning_screen()
            
            # Update animations
            machine_glow += dt * 0.003
            for button in buttons.values():
                button.update(dt)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN and not spinning:
                    if buttons['back'].rect.collidepoint((vmx, vmy)):
                        # Stop music when returning
                        pygame.mixer.music.stop()
                        return "back"
                    elif buttons['rewards'].rect.collidepoint((vmx, vmy)):
                        show_reward_list()
                    elif buttons['history'].rect.collidepoint((vmx, vmy)):
                        show_gacha_history()
                    elif buttons['spin_1x'].rect.collidepoint((vmx, vmy)):
                        if dungeon_data["tengu_feathers"] >= 10:
                            # Create particles and screen shake
                            create_particles(buttons['spin_1x'].rect.centerx, buttons['spin_1x'].rect.centery, 15, (255, 215, 0))
                            screen_shake = 5
                            # Perform 1x spin
                            dungeon_data["tengu_feathers"] -= 10
                            save_dungeon_data(dungeon_data)
                            spin_results = [perform_single_gacha()]
                            spinning = True
                            spin_animation = 0
                        else:
                            show_insufficient_feathers_notification(10)
                    elif buttons['spin_3x'].rect.collidepoint((vmx, vmy)):
                        if dungeon_data["tengu_feathers"] >= 30:
                            # Create more particles and stronger shake
                            create_particles(buttons['spin_3x'].rect.centerx, buttons['spin_3x'].rect.centery, 25, (255, 0, 255))
                            screen_shake = 8
                            # Perform 3x spin
                            dungeon_data["tengu_feathers"] -= 30
                            save_dungeon_data(dungeon_data)
                            spin_results = [perform_single_gacha() for _ in range(3)]
                            spinning = True
                            spin_animation = 0
                        else:
                            show_insufficient_feathers_notification(30)
            
            # Draw background with shake offset
            bg = get_background("main")
            virtual_surface.blit(bg, (shake_offset_x, shake_offset_y))
            
            # Draw animated title with multiple effects
            title_color = get_red_white_color(current_time * 0.3)
            title_text = title_font.render("GACHA", True, title_color)
            
            # Add glow effect to title
            for i in range(3):
                glow_color = tuple(max(0, c - i * 50) for c in title_color)
                glow_text = title_font.render("GACHA", True, glow_color)
                glow_pos = (VIRTUAL_W // 2 - title_text.get_width() // 2 + shake_offset_x + i, 80 + shake_offset_y + i)
                virtual_surface.blit(glow_text, glow_pos)
            
            # Draw shadow
            title_shadow = title_font.render("GACHA", True, (50, 0, 0))
            virtual_surface.blit(title_shadow, (VIRTUAL_W // 2 - title_text.get_width() // 2 + 3 + shake_offset_x, 80 + 3 + shake_offset_y))
            virtual_surface.blit(title_text, (VIRTUAL_W // 2 - title_text.get_width() // 2 + shake_offset_x, 80 + shake_offset_y))
            
            # Enhanced gacha machine with glow effects
            machine_rect = pygame.Rect(VIRTUAL_W//2 - 100 + shake_offset_x, 150 + shake_offset_y, 200, 150)
            
            # Machine glow effect
            glow_intensity = int(50 + 30 * math.sin(machine_glow))
            for i in range(5):
                glow_rect = machine_rect.inflate(i * 8, i * 8)
                glow_color = (100 + glow_intensity - i * 20, 50 + glow_intensity // 2 - i * 10, 150 + glow_intensity - i * 30)
                glow_color = tuple(max(0, min(255, c)) for c in glow_color)
                pygame.draw.rect(virtual_surface, glow_color, glow_rect, border_radius=20 + i)
            
            # Main machine body
            pygame.draw.rect(virtual_surface, (100, 50, 150), machine_rect, border_radius=20)
            pygame.draw.rect(virtual_surface, (150, 100, 200), machine_rect, 5, border_radius=20)
            
            # Machine details
            detail_rect = pygame.Rect(machine_rect.x + 20, machine_rect.y + 20, machine_rect.width - 40, 20)
            pygame.draw.rect(virtual_surface, (200, 150, 250), detail_rect, border_radius=10)
            
            # Animated Yurei preview
            if yurei_preview:
                preview_rect = yurei_preview.get_rect(center=machine_rect.center)
                # Add floating animation
                float_offset = int(5 * math.sin(current_time * 0.002))
                preview_rect.y += float_offset
                virtual_surface.blit(yurei_preview, preview_rect.topleft)
            
            # Enhanced Tengu Feather display
            feather_bg = pygame.Rect(VIRTUAL_W // 2 - 160 + shake_offset_x, 450 + shake_offset_y, 320, 45)
            
            # Feather count glow based on amount
            feather_count = dungeon_data['tengu_feathers']
            if feather_count >= 30:
                glow_color = (0, 255, 0)  # Green glow for rich
            elif feather_count >= 10:
                glow_color = (255, 255, 0)  # Yellow glow for medium
            else:
                glow_color = (255, 0, 0)  # Red glow for poor
            
            # Draw glow
            for i in range(3):
                glow_rect = feather_bg.inflate(i * 4, i * 4)
                alpha_color = tuple(c // (i + 2) for c in glow_color)
                pygame.draw.rect(virtual_surface, alpha_color, glow_rect, border_radius=8 + i)
            
            pygame.draw.rect(virtual_surface, (150, 0, 0), feather_bg, border_radius=8)
            pygame.draw.rect(virtual_surface, (255, 255, 255), feather_bg, 3, border_radius=8)
            
            # Animated feather text
            feather_text = button_font.render(f"Tengu Feathers: {feather_count}", True, (255, 255, 255))
            feather_shadow = button_font.render(f"Tengu Feathers: {feather_count}", True, (0, 0, 0))
            text_x = feather_bg.centerx - feather_text.get_width() // 2
            if feather_icon:
                text_x -= 20
            
            virtual_surface.blit(feather_shadow, (text_x + 2, feather_bg.centery - feather_text.get_height() // 2 + 2))
            virtual_surface.blit(feather_text, (text_x, feather_bg.centery - feather_text.get_height() // 2))
            
            if feather_icon:
                # Animated feather icon
                icon_x = text_x + feather_text.get_width() + 10
                icon_y = feather_bg.centery - feather_icon.get_height() // 2
                icon_bounce = int(3 * math.sin(current_time * 0.004))
                virtual_surface.blit(feather_icon, (icon_x, icon_y + icon_bounce))
            
            # Draw enhanced buttons
            for button_name, button in buttons.items():
                hovered = button.rect.collidepoint((vmx, vmy))
                
                if button_name == 'spin_1x':
                    enabled = dungeon_data["tengu_feathers"] >= 10
                elif button_name == 'spin_3x':
                    enabled = dungeon_data["tengu_feathers"] >= 30
                else:
                    enabled = True
                
                button.draw(virtual_surface, enabled, hovered, vmx, vmy)
            
            # Update and draw particles
            update_and_draw_particles(virtual_surface)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def show_spinning_screen():
        """Enhanced spinning screen with multiple visual effects"""
        nonlocal spinning, spin_animation, spin_results, show_results, result_timer
        
        spin_timer = 0
        max_spin_time = 30
        
        # Create spinning particles
        for _ in range(50):
            create_particles(random.randint(50, VIRTUAL_W-50), random.randint(50, VIRTUAL_H-50), 1, (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))
        
        while spinning:
            current_time = pygame.time.get_ticks()
            spin_bg = get_background("spinning")
            virtual_surface.blit(spin_bg, (0, 0))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
            
            # Update spinning animation with easing
            progress = spin_timer / max_spin_time
            eased_progress = 1 - (1 - progress) ** 3  # Ease out cubic
            spin_animation += 20 - (eased_progress * 15)  # Slow down over time
            spin_timer += 1
            
            if spin_timer >= max_spin_time:
                # Create result particles
                colors = [(255, 215, 0), (255, 0, 255), (0, 255, 255), (0, 255, 0), (150, 150, 150)]
                for result in spin_results:
                    if result["type"] == "grand":
                        create_particles(VIRTUAL_W // 2, VIRTUAL_H // 2, 30, colors[0])
                    elif result["type"] == "main":
                        create_particles(VIRTUAL_W // 2, VIRTUAL_H // 2, 20, colors[1])
                
                spinning = False
                show_results = True
                result_timer = current_time
                spin_animation = 0
                return show_results_screen()
            
            # Multiple spinning elements for rich visual
            center_x, center_y = VIRTUAL_W // 2, VIRTUAL_H // 2
            
            # Outer ring
            for i in range(12):
                angle = math.radians(spin_animation + i * 30)
                radius = 150
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                size = 15 + int(10 * math.sin(spin_animation * 0.1 + i))
                colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
                color = colors[i % len(colors)]
                pygame.draw.circle(virtual_surface, color, (int(x), int(y)), size)
            
            # Middle ring
            for i in range(8):
                angle = math.radians(-spin_animation * 0.8 + i * 45)
                radius = 100
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                pygame.draw.circle(virtual_surface, (255, 255, 255), (int(x), int(y)), 12)
                pygame.draw.circle(virtual_surface, (100, 100, 100), (int(x), int(y)), 8)
            
            # Center spinning disc
            center_size = 60 + int(10 * math.sin(spin_animation * 0.05))
            pygame.draw.circle(virtual_surface, get_rainbow_color(current_time * 0.01), (center_x, center_y), center_size)
            pygame.draw.circle(virtual_surface, (255, 255, 255), (center_x, center_y), center_size - 10, 5)
            
            # Spinning title with rainbow effect
            spin_title = title_font.render("SPINNING...", True, get_rainbow_color(current_time * 0.02))
            
            # Add dramatic glow to title
            for i in range(5):
                glow_color = tuple(max(0, c - i * 30) for c in get_rainbow_color(current_time * 0.02))
                glow_title = title_font.render("SPINNING...", True, glow_color)
                glow_x = VIRTUAL_W // 2 - spin_title.get_width() // 2 + random.randint(-2, 2)
                glow_y = 100 + random.randint(-2, 2) + i
                virtual_surface.blit(glow_title, (glow_x, glow_y))
            
            virtual_surface.blit(spin_title, (VIRTUAL_W // 2 - spin_title.get_width() // 2, 100))
            
            # Enhanced progress bar with effects
            progress = spin_timer / max_spin_time
            progress_rect = pygame.Rect(VIRTUAL_W // 2 - 200, VIRTUAL_H - 120, 400, 30)
            
            # Progress bar glow
            for i in range(3):
                glow_rect = progress_rect.inflate(i * 6, i * 6)
                glow_color = get_rainbow_color(current_time * 0.01)
                glow_color = tuple(c // (i + 2) for c in glow_color)
                pygame.draw.rect(virtual_surface, glow_color, glow_rect, border_radius=15 + i)
            
            pygame.draw.rect(virtual_surface, (50, 50, 50), progress_rect, border_radius=15)
            progress_fill = pygame.Rect(progress_rect.x + 3, progress_rect.y + 3, int((progress_rect.width - 6) * progress), progress_rect.height - 6)
            pygame.draw.rect(virtual_surface, get_rainbow_color(current_time * 0.01), progress_fill, border_radius=12)
            
            # Percentage text with glow
            progress_text = button_font.render(f"{int(progress * 100)}%", True, WHITE)
            for i in range(3):
                glow_text = button_font.render(f"{int(progress * 100)}%", True, get_rainbow_color(current_time * 0.01))
                virtual_surface.blit(glow_text, (VIRTUAL_W // 2 - progress_text.get_width() // 2 + i, VIRTUAL_H - 70 + i))
            virtual_surface.blit(progress_text, (VIRTUAL_W // 2 - progress_text.get_width() // 2, VIRTUAL_H - 70))
            
            # Update and draw particles
            update_and_draw_particles(virtual_surface)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def show_results_screen():
        """Enhanced results screen with animations"""
        result_timer = pygame.time.get_ticks()
        continue_button = EnhancedButton(pygame.Rect(VIRTUAL_W // 2 - 120, VIRTUAL_H - 80, 240, 60), "CONTINUE", button_font)
        
        # Result entrance animation
        result_animations = []
        for i, result in enumerate(spin_results):
            result_animations.append({
                'delay': i * 30,  # Stagger entrance
                'scale': 0.0,
                'target_scale': 1.0,
                'bounce': 0
            })
        
        while True:
            current_time = pygame.time.get_ticks()
            time_since_start = current_time - result_timer
            
            results_bg = get_background("results")
            virtual_surface.blit(results_bg, (0, 0))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if continue_button.rect.collidepoint((vmx, vmy)):
                        return gacha_main_screen()
            
            continue_button.update(current_time - result_timer)
            
            # Animated results title
            results_title = title_font.render("GACHA RESULTS", True, get_red_white_color(current_time * 0.3))
            for i in range(3):
                glow_color = tuple(max(0, c - i * 40) for c in get_red_white_color(current_time * 0.3))
                glow_title = title_font.render("GACHA RESULTS", True, glow_color)
                virtual_surface.blit(glow_title, (VIRTUAL_W // 2 - results_title.get_width() // 2 + i, 80 + i))
            virtual_surface.blit(results_title, (VIRTUAL_W // 2 - results_title.get_width() // 2, 80))
            
            # Show results with entrance animations
            for i, result in enumerate(spin_results):
                anim = result_animations[i]
                
                # Update animation
                if time_since_start > anim['delay']:
                    if anim['scale'] < anim['target_scale']:
                        anim['scale'] += 0.05
                        if anim['scale'] >= anim['target_scale']:
                            anim['scale'] = anim['target_scale']
                            anim['bounce'] = 10  # Add bounce when reaching target
                
                if anim['bounce'] > 0:
                    anim['bounce'] -= 1
                    anim['scale'] = anim['target_scale'] + (anim['bounce'] * 0.02)
                
                if anim['scale'] <= 0:
                    continue
                
                y_offset = 150 + i * 120
                
                # Determine colors and effects based on rarity
                if result["type"] == "grand":
                    color = (255, 215, 0)
                    bg_color = (100, 80, 0)
                    # Special grand prize effects
                    if time_since_start > anim['delay']:
                        create_particles(VIRTUAL_W // 2, y_offset + 45, 3, color)
                elif result["type"] == "main":
                    color = (255, 0, 255)
                    bg_color = (80, 0, 80)
                elif result["type"] == "second":
                    color = (0, 255, 255)
                    bg_color = (0, 80, 80)
                elif result["type"] == "last":
                    color = (0, 255, 0)
                    bg_color = (0, 80, 0)
                else:  # zonk
                    color = (150, 150, 150)
                    bg_color = (50, 50, 50)
                
                # Calculate scaled dimensions
                base_width, base_height = 500, 100
                scaled_width = int(base_width * anim['scale'])
                scaled_height = int(base_height * anim['scale'])
                
                result_rect = pygame.Rect(VIRTUAL_W//2 - scaled_width//2, y_offset, scaled_width, scaled_height)
                
                # Enhanced glow effect
                for glow in range(5):
                    glow_rect = result_rect.inflate(glow * 8, glow * 8)
                    glow_alpha = 255 - (glow * 50)
                    glow_color = tuple(max(0, min(255, c - glow * 30)) for c in color)
                    pygame.draw.rect(virtual_surface, glow_color, glow_rect, border_radius=20)
                
                # Main result box
                pygame.draw.rect(virtual_surface, bg_color, result_rect, border_radius=15)
                pygame.draw.rect(virtual_surface, color, result_rect, 4, border_radius=15)
                
                # Scale text based on animation
                if anim['scale'] > 0.5:  # Only show text when sufficiently scaled
                    text_scale = min(1.0, (anim['scale'] - 0.5) * 2)
                    
                    # Rarity text
                    rarity_text = button_font.render(result["rarity"], True, color)
                    if text_scale < 1.0:
                        scaled_rarity = pygame.transform.scale(rarity_text, 
                            (int(rarity_text.get_width() * text_scale), 
                             int(rarity_text.get_height() * text_scale)))
                        virtual_surface.blit(scaled_rarity, (result_rect.x + 15, result_rect.y + 15))
                    else:
                        virtual_surface.blit(rarity_text, (result_rect.x + 15, result_rect.y + 15))
                    
                    # Item name
                    item_text = button_font.render(result["item"], True, WHITE)
                    if text_scale < 1.0:
                        scaled_item = pygame.transform.scale(item_text,
                            (int(item_text.get_width() * text_scale),
                             int(item_text.get_height() * text_scale)))
                        virtual_surface.blit(scaled_item, (result_rect.x + 15, result_rect.y + 50))
                    else:
                        virtual_surface.blit(item_text, (result_rect.x + 15, result_rect.y + 50))
                    
                    # Feather icon for feather rewards
                    if "Tengu Feather" in result["item"] and feather_icon and text_scale == 1.0:
                        icon_x = result_rect.x + 15 + item_text.get_width() + 15
                        icon_y = result_rect.y + 48
                        virtual_surface.blit(feather_icon, (icon_x, icon_y))
                
                # Special message for zonk
                if result["type"] == "zonk" and anim['scale'] == 1.0:
                    zonk_msg = small_font.render("Unfortunately you are unlucky, please try again!", True, RED)
                    virtual_surface.blit(zonk_msg, (result_rect.x + 20, result_rect.bottom + 10))
            
            # Draw continue button
            hovered = continue_button.rect.collidepoint((vmx, vmy))
            continue_button.draw(virtual_surface, True, hovered, vmx, vmy)
            
            # Update and draw particles
            update_and_draw_particles(virtual_surface)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def perform_single_gacha():
        """Enhanced gacha roll with history tracking"""
        rand = random.random() * 100
        result = None
        
        if rand < 0.5:  # 0.5% Grand Prize
            gacha_data["yurei_permanent"] = True
            save_gacha_data(gacha_data)
            result = {"type": "grand", "item": "Yurei (Permanent)", "rarity": "★★★★★ JACKPOT!"}
        elif rand < 2.5:  # 2% Main Prize
            if not gacha_data["yurei_permanent"]:
                trial_end = datetime.datetime.now() + timedelta(hours=3)
                gacha_data["yurei_trial_end"] = trial_end.isoformat()
                save_gacha_data(gacha_data)
                result = {"type": "main", "item": "Yurei (3 Hours)", "rarity": "★★★★ RARE!"}
            else:
                feathers = random.choice([4, 6])
                dungeon_data["tengu_feathers"] += feathers
                save_dungeon_data(dungeon_data)
                result = {"type": "second", "item": f"{feathers} Tengu Feathers", "rarity": "★★★ GOOD!"}
        elif rand < 12.5:  # 10% Second Prize
            feathers = random.choice([2, 4, 6])
            dungeon_data["tengu_feathers"] += feathers
            save_dungeon_data(dungeon_data)
            result = {"type": "second", "item": f"{feathers} Tengu Feathers", "rarity": "★★★ GOOD!"}
        elif rand < 27.5:  # 15% Last Prize
            feathers = random.choice([1, 2])
            dungeon_data["tengu_feathers"] += feathers
            save_dungeon_data(dungeon_data)
            result = {"type": "last", "item": f"{feathers} Tengu Feathers", "rarity": "★★ OK"}
        else:  # 72.5% Zonk
            result = {"type": "zonk", "item": "Nothing", "rarity": "★ BAD LUCK"}
        
        # Enhanced history tracking
        if "gacha_history" not in gacha_data:
            gacha_data["gacha_history"] = []
        
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "result": result.copy(),
            "feathers_before": dungeon_data["tengu_feathers"] + (10 if len(spin_results) == 0 else 30), # Approximate
            "feathers_after": dungeon_data["tengu_feathers"]
        }
        gacha_data["gacha_history"].append(history_entry)
        
        # Keep only last 100 entries to prevent file bloat
        if len(gacha_data["gacha_history"]) > 100:
            gacha_data["gacha_history"] = gacha_data["gacha_history"][-100:]
        
        save_gacha_data(gacha_data)
        return result
    
    def show_insufficient_feathers_notification(required_feathers):
        """Enhanced notification with better animations"""
        notification_timer = 0
        max_notification_time = 180  # 3 seconds
        notification_scale = 0.0
        pulse = 0
        
        # Create warning particles
        create_particles(VIRTUAL_W // 2, VIRTUAL_H // 2, 20, (255, 0, 0))
        
        while notification_timer < max_notification_time:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return
            
            # Update animations
            target_scale = 1.0 if notification_timer < max_notification_time - 30 else max(0, 1.0 - (notification_timer - (max_notification_time - 30)) / 30)
            notification_scale += (target_scale - notification_scale) * 0.15
            pulse += 0.2
            notification_timer += 1
            
            # Draw background with particles
            bg = get_background("main")
            virtual_surface.blit(bg, (0, 0))
            
            # Update and draw particles first
            update_and_draw_particles(virtual_surface)
            
            # Semi-transparent overlay with pulsing effect
            overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            overlay_alpha = int(150 + 30 * math.sin(pulse))
            overlay.set_alpha(overlay_alpha)
            overlay.fill((0, 0, 0))
            virtual_surface.blit(overlay, (0, 0))
            
            if notification_scale > 0:
                # Scaled notification box
                base_width, base_height = 450, 250
                scaled_width = int(base_width * notification_scale)
                scaled_height = int(base_height * notification_scale)
                
                notification_rect = pygame.Rect(
                    VIRTUAL_W // 2 - scaled_width // 2,
                    VIRTUAL_H // 2 - scaled_height // 2,
                    scaled_width, scaled_height
                )
                
                # Enhanced glow effect
                for i in range(6):
                    glow_rect = notification_rect.inflate(i * 8, i * 8)
                    glow_intensity = int(100 + 50 * math.sin(pulse * 0.5))
                    glow_color = (glow_intensity, max(0, glow_intensity - 50), max(0, glow_intensity - 100))
                    pygame.draw.rect(virtual_surface, glow_color, glow_rect, border_radius=20)
                
                # Main notification box
                pygame.draw.rect(virtual_surface, (150, 0, 0), notification_rect, border_radius=15)
                pygame.draw.rect(virtual_surface, (255, 255, 255), notification_rect, 5, border_radius=15)
                
                # Only draw text when sufficiently scaled
                if notification_scale > 0.7:
                    text_alpha = min(1.0, (notification_scale - 0.7) / 0.3)
                    
                    # Warning title with pulse effect
                    title_color = get_red_white_color(current_time * 0.3)
                    title_text = button_font.render("INSUFFICIENT FEATHERS!", True, title_color)
                    title_rect = title_text.get_rect(center=(notification_rect.centerx, notification_rect.y + 50))
                    virtual_surface.blit(title_text, title_rect)
                    
                    # Current feathers
                    current_text = small_font.render(f"You have: {dungeon_data['tengu_feathers']} Tengu Feathers", True, WHITE)
                    current_rect = current_text.get_rect(center=(notification_rect.centerx, notification_rect.centery - 10))
                    virtual_surface.blit(current_text, current_rect)
                    
                    # Required feathers with emphasis
                    required_color = (255, 100 + int(50 * math.sin(pulse)), 100 + int(50 * math.sin(pulse)))
                    required_text = small_font.render(f"Required: {required_feathers} Tengu Feathers", True, required_color)
                    required_rect = required_text.get_rect(center=(notification_rect.centerx, notification_rect.centery + 20))
                    virtual_surface.blit(required_text, required_rect)
                    
                    # Animated feather icon
                    if feather_icon:
                        icon_bounce = int(5 * math.sin(pulse * 0.3))
                        icon_rect = feather_icon.get_rect(center=(notification_rect.centerx, notification_rect.centery + 60))
                        icon_rect.y += icon_bounce
                        virtual_surface.blit(feather_icon, icon_rect.topleft)
                    
                    # Close instruction
                    close_text = small_font.render("Click anywhere to close", True, (200, 200, 200))
                    close_rect = close_text.get_rect(center=(notification_rect.centerx, notification_rect.bottom - 30))
                    virtual_surface.blit(close_text, close_rect)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def show_gacha_history():
        """Display gacha history with filtering and stats"""
        history_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        history_bg.fill((15, 15, 35))
        
        close_button = EnhancedButton(pygame.Rect(VIRTUAL_W - 120, 20, 100, 50), "Close", small_font)
        clear_button = EnhancedButton(pygame.Rect(20, VIRTUAL_H - 70, 120, 50), "Clear History", small_font, enabled_color=(150, 50, 50))
        
        scroll_offset = 0
        max_scroll = 0
        
        history = gacha_data.get("gacha_history", [])
        if not history:
            # Show empty state
            while True:
                virtual_surface.blit(history_bg, (0, 0))
                
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit_game()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if close_button.rect.collidepoint((vmx, vmy)):
                            return
                
                # Title
                title_text = title_font.render("GACHA HISTORY", True, get_red_white_color())
                virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
                
                # Empty message
                empty_text = button_font.render("No gacha history yet!", True, (150, 150, 150))
                virtual_surface.blit(empty_text, empty_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))
                
                # Close button
                hovered = close_button.rect.collidepoint((vmx, vmy))
                close_button.draw(virtual_surface, True, hovered, vmx, vmy)
                
                draw_scaled_centered()
                clock.tick(60)
        
        # Calculate stats
        total_spins = len(history)
        grand_prizes = sum(1 for h in history if h["result"]["type"] == "grand")
        main_prizes = sum(1 for h in history if h["result"]["type"] == "main")
        zonks = sum(1 for h in history if h["result"]["type"] == "zonk")
        
        while True:
            current_time = pygame.time.get_ticks()
            virtual_surface.blit(history_bg, (0, 0))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_button.rect.collidepoint((vmx, vmy)):
                        return
                    elif clear_button.rect.collidepoint((vmx, vmy)):
                        gacha_data["gacha_history"] = []
                        save_gacha_data(gacha_data)
                        return
                elif event.type == pygame.MOUSEWHEEL:
                    scroll_offset = max(0, min(max_scroll, scroll_offset - event.y * 30))
            
            # Title with animation
            title_text = title_font.render("GACHA HISTORY", True, get_red_white_color(current_time * 0.3))
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
            
            # Stats panel
            stats_rect = pygame.Rect(50, 100, VIRTUAL_W - 100, 100)
            pygame.draw.rect(virtual_surface, (30, 30, 60), stats_rect, border_radius=10)
            pygame.draw.rect(virtual_surface, (100, 100, 200), stats_rect, 3, border_radius=10)
            
            stats_text = [
                f"Total Spins: {total_spins}",
                f"Grand Prizes: {grand_prizes} ({grand_prizes/max(1,total_spins)*100:.1f}%)",
                f"Main Prizes: {main_prizes} ({main_prizes/max(1,total_spins)*100:.1f}%)",
                f"Zonks: {zonks} ({zonks/max(1,total_spins)*100:.1f}%)"
            ]
            
            for i, stat in enumerate(stats_text):
                color = WHITE
                if "Grand" in stat:
                    color = (255, 215, 0)
                elif "Main" in stat:
                    color = (255, 0, 255)
                elif "Zonks" in stat:
                    color = (255, 100, 100)
                
                stat_surface = small_font.render(stat, True, color)
                virtual_surface.blit(stat_surface, (stats_rect.x + 20, stats_rect.y + 20 + i * 20))
            
            # History entries
            y_start = 220
            entry_height = 60
            visible_entries = (VIRTUAL_H - y_start - 80) // entry_height
            max_scroll = max(0, (len(history) - visible_entries) * entry_height)
            
            for i, entry in enumerate(history[-min(50, len(history)):]):  # Show last 50 entries
                entry_y = y_start + i * entry_height - scroll_offset
                
                if entry_y < y_start - entry_height or entry_y > VIRTUAL_H:
                    continue
                
                # Entry background
                entry_rect = pygame.Rect(50, entry_y, VIRTUAL_W - 100, entry_height - 5)
                
                result = entry["result"]
                if result["type"] == "grand":
                    bg_color = (100, 80, 0)
                    border_color = (255, 215, 0)
                elif result["type"] == "main":
                    bg_color = (80, 0, 80)
                    border_color = (255, 0, 255)
                elif result["type"] == "zonk":
                    bg_color = (60, 30, 30)
                    border_color = (150, 150, 150)
                else:
                    bg_color = (40, 40, 60)
                    border_color = (100, 200, 200)
                
                pygame.draw.rect(virtual_surface, bg_color, entry_rect, border_radius=8)
                pygame.draw.rect(virtual_surface, border_color, entry_rect, 2, border_radius=8)
                
                # Entry details
                timestamp = entry["timestamp"][:19].replace("T", " ")  # Format datetime
                time_text = small_font.render(timestamp, True, (200, 200, 200))
                virtual_surface.blit(time_text, (entry_rect.x + 10, entry_rect.y + 5))
                
                item_text = small_font.render(f"{result['rarity']} {result['item']}", True, border_color)
                virtual_surface.blit(item_text, (entry_rect.x + 10, entry_rect.y + 25))
            
            # Scroll indicator
            if max_scroll > 0:
                scroll_bar_height = max(20, int((visible_entries / len(history)) * (VIRTUAL_H - y_start - 80)))
                scroll_bar_y = y_start + int((scroll_offset / max_scroll) * (VIRTUAL_H - y_start - 80 - scroll_bar_height))
                scroll_bar_rect = pygame.Rect(VIRTUAL_W - 20, scroll_bar_y, 15, scroll_bar_height)
                pygame.draw.rect(virtual_surface, (100, 100, 200), scroll_bar_rect, border_radius=7)
            
            # Buttons
            hovered_close = close_button.rect.collidepoint((vmx, vmy))
            close_button.draw(virtual_surface, True, hovered_close, vmx, vmy)
            
            hovered_clear = clear_button.rect.collidepoint((vmx, vmy))
            clear_button.draw(virtual_surface, True, hovered_clear, vmx, vmy)
            
            draw_scaled_centered()
            clock.tick(60)
    
    def show_reward_list():
        """Show reward list screen with updated chances"""
        reward_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        reward_bg.fill((20, 20, 40))
        
        close_button = pygame.Rect(VIRTUAL_W - 100, 50, 80, 50)
        
        while True:
            virtual_surface.blit(reward_bg, (0, 0))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_button.collidepoint((vmx, vmy)):
                        return
            
            # Draw title with red-white color
            title_text = title_font.render("REWARD LIST", True, get_red_white_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 60)))
            
            # Draw reward categories with updated chances
            rewards = [
                {"name": "Grand Prize", "chance": "0.5%", "items": ["Yurei (Permanent)"], "color": (255, 215, 0), "rarity": "5 Stars"},
                {"name": "Main Prize", "chance": "2%", "items": ["Yurei (3 Hours)"], "color": (255, 0, 255), "rarity": "4 Stars"},
                {"name": "Second Prize", "chance": "10%", "items": ["2 Tengu Feathers", "4 Tengu Feathers", "6 Tengu Feathers"], "color": (0, 255, 255), "rarity": "3 Stars"},
                {"name": "Last Prize", "chance": "15%", "items": ["1 Tengu Feather", "2 Tengu Feathers"], "color": (0, 255, 0), "rarity": "2 Stars"},
                {"name": "Zonk", "chance": "72.5%", "items": ["Nothing (Bad Luck)"], "color": (150, 150, 150), "rarity": "1 Star"}
            ]
            
            y_start = 120
            for i, reward in enumerate(rewards):
                y_offset = y_start + i * 90
                
                # Draw category box
                category_rect = pygame.Rect(50, y_offset, VIRTUAL_W - 100, 80)
                pygame.draw.rect(virtual_surface, (40, 40, 60), category_rect, border_radius=10)
                pygame.draw.rect(virtual_surface, reward["color"], category_rect, 3, border_radius=10)
                
                # Category name and chance
                name_text = button_font.render(f"{reward['name']} ({reward['chance']})", True, reward["color"])
                virtual_surface.blit(name_text, (category_rect.x + 10, category_rect.y + 10))
                
                # Rarity text
                rarity_text = small_font.render(reward["rarity"], True, reward["color"])
                virtual_surface.blit(rarity_text, (category_rect.x + 10, category_rect.y + 35))
                
                # Items
                items_text = small_font.render(" | ".join(reward["items"]), True, WHITE)
                virtual_surface.blit(items_text, (category_rect.x + 10, category_rect.y + 55))
                
                # Show Yurei preview for character rewards
                if "Yurei" in reward["items"][0] and yurei_preview:
                    preview_rect = yurei_preview.get_rect(center=(category_rect.right - 60, category_rect.centery))
                    virtual_surface.blit(pygame.transform.scale(yurei_preview, (60, 60)), preview_rect.topleft)
                
                # Show feather icon for feather rewards
                elif "Tengu Feather" in reward["items"][0] and feather_icon:
                    icon_rect = feather_icon.get_rect(center=(category_rect.right - 60, category_rect.centery))
                    virtual_surface.blit(pygame.transform.scale(feather_icon, (40, 40)), icon_rect.topleft)
            
            # Draw close button
            color_close = HOVER_COLOR if close_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, color_close, close_button, border_radius=8)
            close_text = small_font.render("Close", True, WHITE)
            virtual_surface.blit(close_text, close_text.get_rect(center=close_button.center))
            
            draw_scaled_centered()
            clock.tick(60)
    
    # Start gacha main screen
    try:
        return gacha_main_screen()
    finally:
        # Always stop music when exiting gacha function
        pygame.mixer.music.stop()   

# Add Graffiti character
graffiti_frame_counts = {
    "Attack_1": 6,
    "Attack_2": 10,
    "Attack_3": 10,
    "Dead": 9,
    "Hurt": 4,
    "Idle": 7,
    "Jump": 9,
    "Run": 10,
    "Shield": 18,
    "Walk": 10
}

# Add Graffiti damage values
graffiti_damage = {
    "Attack_1": 5,
    "Attack_2": 8,
    "Attack_3": 10
}

# Add Graffiti range
graffiti_range = 100  # Medium range

# Update character frame counts dictionary to include Graffiti
character_frame_counts["Graffiti"] = graffiti_frame_counts

# Update character damage dictionary to include Graffiti
character_damage["Graffiti"] = graffiti_damage

# Update character ranges dictionary to include Graffiti
character_ranges["Graffiti"] = graffiti_range

def load_redeem_data():
    """Load redeem data from local file"""
    if os.path.exists("redeem_data.json"):
        try:
            with open("redeem_data.json", 'r') as f:
                return json.load(f)
        except:
            pass
    return {"used_codes": []}

def save_redeem_data(data):
    """Save redeem data to local file"""
    with open("redeem_data.json", 'w') as f:
        json.dump(data, f, indent=2)

def validate_redeem_code_format(code):
    """Validate redeem code format: More flexible validation"""
    # Remove spaces and convert to uppercase
    code = code.strip().upper()
    
    # Check if code contains only valid characters (letters, numbers, hyphens)
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-')
    if not all(c in valid_chars for c in code):
        return False
    
    # Check minimum length (at least 4 characters)
    if len(code) < 4:
        return False
    
    # Check maximum length (reasonable limit)
    if len(code) > 25:
        return False
    
    # Must contain at least one letter or number
    if not any(c.isalnum() for c in code):
        return False
    
    return True

def fetch_redeem_codes_online():
    """Fetch redeem codes from online JSON"""
    try:
        response = requests.get("https://mhtpsg.github.io/theslayer/redeem_code.json", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error fetching redeem codes: {e}")
    
    # Fallback offline codes for testing/development
    return {
        "codes": {
            "TENG-UFEA-THER-CODE": {
                "reward_type": "tengu_feather",
                "amount": 3,
                "description": "3 Tengu Feathers"
            },
            "CHAR-GRAFF-FREE-2025": {
                "reward_type": "character",
                "character": "Graffiti",
                "description": "Graffiti Character"
            }
        }
    }

class CustomKeyboard:
    def __init__(self):
        self.visible = False
        self.keys = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', '-'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', 'DEL', 'SPACE']
        ]
        self.key_width = 50
        self.key_height = 45
        self.key_margin = 4
        self.keyboard_height = len(self.keys) * (self.key_height + self.key_margin) + 40
        self.start_y = VIRTUAL_H - self.keyboard_height if self.visible else VIRTUAL_H - 50
        self.animation_progress = 0.0
        self.animating = False
        self.animation_speed = 8.0
        
    def toggle(self):
        """Toggle keyboard visibility with animation"""
        self.visible = not self.visible
        self.animating = True
        
    def update_animation(self, dt):
        """Update keyboard slide animation"""
        if self.animating:
            target_progress = 1.0 if self.visible else 0.0
            
            if self.animation_progress < target_progress:
                self.animation_progress = min(1.0, self.animation_progress + self.animation_speed * dt / 1000)
            elif self.animation_progress > target_progress:
                self.animation_progress = max(0.0, self.animation_progress - self.animation_speed * dt / 1000)
            
            # Stop animation when reached target
            if abs(self.animation_progress - target_progress) < 0.01:
                self.animation_progress = target_progress
                self.animating = False
        
        # Calculate current Y position based on animation
        hidden_y = VIRTUAL_H
        visible_y = VIRTUAL_H - self.keyboard_height
        self.start_y = hidden_y + (visible_y - hidden_y) * self.animation_progress
        
    def get_toggle_button_rect(self):
        """Get the toggle button rectangle"""
        button_width = 120
        button_height = 40
        button_x = VIRTUAL_W // 2 - button_width // 2
        button_y = self.start_y - 45
        return pygame.Rect(button_x, button_y, button_width, button_height)
        
    def draw_toggle_button(self, surface, vmx, vmy):
        """Draw the keyboard toggle button"""
        toggle_rect = self.get_toggle_button_rect()
        
        # Button color based on hover
        button_color = HOVER_COLOR if toggle_rect.collidepoint(vmx, vmy) else BUTTON_COLOR
        
        # Draw button
        pygame.draw.rect(surface, button_color, toggle_rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, toggle_rect, 2, border_radius=8)
        
        # Draw button text and icon
        text = "Keyboard" if self.visible else "Keyboard"
        text_surface = small_font.render(text, True, WHITE)
        text_rect = text_surface.get_rect(center=toggle_rect.center)
        surface.blit(text_surface, text_rect)
        
        return toggle_rect.collidepoint(vmx, vmy)
        
    def draw(self, surface, vmx, vmy):
        """Draw the keyboard"""
        if self.animation_progress <= 0:
            return None
            
        # Draw keyboard background with transparency based on animation
        kb_bg = pygame.Rect(10, self.start_y, VIRTUAL_W - 20, self.keyboard_height)
        
        # Create surface with alpha for fade effect
        keyboard_surface = pygame.Surface((kb_bg.width, kb_bg.height))
        keyboard_surface.set_alpha(int(255 * self.animation_progress))
        
        # Draw background
        pygame.draw.rect(keyboard_surface, (25, 25, 35), (0, 0, kb_bg.width, kb_bg.height), border_radius=15)
        pygame.draw.rect(keyboard_surface, WHITE, (0, 0, kb_bg.width, kb_bg.height), 2, border_radius=15)
        
        # Draw title
        title_text = small_font.render("The Slayer Keyboard", True, WHITE)
        title_rect = title_text.get_rect(center=(kb_bg.width // 2, 20))
        keyboard_surface.blit(title_text, title_rect)
        
        clicked_key = None
        
        # Draw keys
        for row_idx, row in enumerate(self.keys):
            row_width = len(row) * self.key_width + (len(row) - 1) * self.key_margin
            row_start_x = (kb_bg.width - row_width) // 2
            
            for col_idx, key in enumerate(row):
                key_x = row_start_x + col_idx * (self.key_width + self.key_margin)
                key_y = 40 + row_idx * (self.key_height + self.key_margin)
                
                # Adjust key width for special keys
                current_key_width = self.key_width
                if key in ['DEL', 'SPACE']:
                    current_key_width = self.key_width * 1.5
                
                key_rect = pygame.Rect(key_x, key_y, current_key_width, self.key_height)
                global_key_rect = pygame.Rect(kb_bg.x + key_x, kb_bg.y + key_y, current_key_width, self.key_height)
                
                # Determine key color
                if key == 'DEL':
                    key_color = (120, 40, 40)  # Red for delete
                elif key == 'SPACE':
                    key_color = (40, 80, 120)  # Blue for space
                elif key == '-':
                    key_color = (80, 80, 40)   # Yellow for dash
                else:
                    key_color = (50, 50, 60)   # Default gray
                
                # Hover effect
                if global_key_rect.collidepoint(vmx, vmy):
                    key_color = tuple(min(255, c + 30) for c in key_color)
                    clicked_key = key
                
                # Draw key
                pygame.draw.rect(keyboard_surface, key_color, key_rect, border_radius=6)
                pygame.draw.rect(keyboard_surface, WHITE, key_rect, 1, border_radius=6)
                
                # Draw key text
                display_text = key
                if key == 'SPACE':
                    display_text = 'SPC'
                elif key == 'DEL':
                    display_text = 'DEL'
                
                key_text = small_font.render(display_text, True, WHITE)
                text_rect = key_text.get_rect(center=key_rect.center)
                keyboard_surface.blit(key_text, text_rect)
        
        # Blit keyboard surface to main surface
        surface.blit(keyboard_surface, kb_bg.topleft)
        
        return clicked_key
        
    def handle_key_input(self, key, input_text):
        """Handle key input and return modified text"""
        if key == 'DEL':
            return input_text[:-1] if input_text else input_text
        elif key == 'SPACE':
            # Allow space but with reasonable limit
            return input_text + ' ' if len(input_text) < 25 else input_text
        elif key and len(input_text) < 25:  # Increased limit to 25 characters
            return input_text + key
        return input_text

def redeem_code():
    try:
        character_data = load_character_data()
    except:
        character_data = {"owned_characters": ["Samurai", "Soldier", "Magician"]}
    
    try:
        dungeon_data = load_dungeon_data()
    except:
        dungeon_data = {"tengu_feathers": 0, "battle_count": 0, "last_reset": datetime.now().isoformat(), "inventory": [], "stamina": 100, "last_stamina_regen": datetime.now().isoformat()}
    
    try:
        summer_data = load_summer_data()
    except:
        summer_data = {"sakura": 0, "water": 0, "black_water": 0}
    
    redeem_data = load_redeem_data()
    
    # Input variables
    input_text = ""
    input_active = False
    cursor_visible = True
    cursor_timer = 0
    
    # Custom keyboard
    keyboard = CustomKeyboard()
    
    # UI elements - Make input box wider to accommodate longer codes
    input_box = pygame.Rect(VIRTUAL_W//2 - 250, 200, 500, 50)
    redeem_button = pygame.Rect(VIRTUAL_W//2 - 100, 270, 200, 60)
    back_button = pygame.Rect(50, 50, 80, 40)
    
    # Message system
    message = ""
    message_color = WHITE
    message_timer = 0
    
    # Loading state
    is_loading = False
    loading_dots = 0
    loading_timer = 0
    
    # Pre-render static text surfaces to avoid re-rendering every frame
    title_surface = title_font.render("REDEEM CODE", True, WHITE)  # We'll apply rainbow later
    instruction1_surface = small_font.render("Enter your redeem code (letters, numbers, and hyphens allowed)", True, WHITE)
    instruction2_surface = small_font.render("Get codes from https://discord.gg/scNgmKpFBE", True, (200, 200, 200))
    placeholder_surface = small_font.render("Tap here to enter code...", True, (150, 150, 150))
    back_surface = small_font.render("Back", True, WHITE)
    
    # Cache for rendered text to avoid re-rendering
    text_cache = {}
    last_input_text = ""
    cached_input_surface = None
    
    # Performance optimization: reduce rainbow calculation frequency
    rainbow_timer = 0
    cached_rainbow_color = get_rainbow_color()
    
    # Threading for network requests
    import threading
    network_result = {"data": None, "error": None, "completed": False}
    
    def fetch_codes_thread(code):
        try:
            online_codes = fetch_redeem_codes_online()
            network_result["data"] = online_codes
            network_result["completed"] = True
        except Exception as e:
            network_result["error"] = str(e)
            network_result["completed"] = True
    
    while True:
        current_time = pygame.time.get_ticks()
        dt = clock.get_time()
        
        # Clear screen once
        virtual_surface.fill((20, 30, 50))
        
        # Calculate mouse position once
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Update keyboard animation
        keyboard.update_animation(dt)
        
        # Update cursor blinking
        cursor_timer += dt
        if cursor_timer >= 500:
            cursor_visible = not cursor_visible
            cursor_timer = 0
        
        # Update loading animation
        if is_loading:
            loading_timer += dt
            if loading_timer >= 500:
                loading_dots = (loading_dots + 1) % 4
                loading_timer = 0
        
        # Update rainbow color less frequently for better performance
        rainbow_timer += dt
        if rainbow_timer >= 50:  # Update every 50ms instead of every frame
            cached_rainbow_color = get_rainbow_color()
            rainbow_timer = 0
        
        # Check if network request completed
        if is_loading and network_result["completed"]:
            is_loading = False
            code = input_text.strip().upper()
            
            if network_result["error"]:
                message = "Network error! Check your connection"
                message_color = RED
                message_timer = current_time
            elif network_result["data"] and code in network_result["data"].get("codes", {}):
                reward_info = network_result["data"]["codes"][code]
                
                # Process reward (same logic as before but optimized)
                success = False
                
                if reward_info["reward_type"] == "tengu_feather":
                    amount = reward_info.get("amount", 1)
                    dungeon_data["tengu_feathers"] += amount
                    save_dungeon_data(dungeon_data)
                    message = f"Success! Received {amount} Tengu Feathers"
                    success = True
                    
                elif reward_info["reward_type"] == "character":
                    character_name = reward_info.get("character", "")
                    if character_name and character_name not in character_data["owned_characters"]:
                        character_data["owned_characters"].append(character_name)
                        save_character_data(character_data)
                        message = f"Success! Unlocked {character_name} character"
                        success = True
                    elif character_name in character_data["owned_characters"]:
                        message = f"You already own {character_name}!"
                        message_color = (255, 165, 0)
                    else:
                        message = "Invalid character reward!"
                        message_color = RED
                
                elif reward_info["reward_type"] in ["sakura", "water", "black_water"]:
                    amount = reward_info.get("amount", 1)
                    summer_data[reward_info["reward_type"]] += amount
                    save_summer_data(summer_data)
                    resource_name = reward_info["reward_type"].replace("_", " ").title()
                    message = f"Success! Received {amount} {resource_name}"
                    success = True
                
                elif reward_info["reward_type"] == "summer_materials":
                    rewards = reward_info.get("rewards", {})
                    reward_messages = []
                    
                    for resource, amount in rewards.items():
                        if resource in summer_data:
                            summer_data[resource] += amount
                            resource_name = resource.replace("_", " ").title()
                            reward_messages.append(f"{amount} {resource_name}")
                    
                    if reward_messages:
                        save_summer_data(summer_data)
                        message = f"Success! Received: {', '.join(reward_messages)}"
                        success = True
                    else:
                        message = "No valid rewards found!"
                        message_color = RED
                
                if success:
                    message_color = SELECTED_COLOR
                    redeem_data["used_codes"].append(code)
                    save_redeem_data(redeem_data)
                    input_text = ""
                    last_input_text = ""  # Reset cache
                    cached_input_surface = None
                
                message_timer = current_time
            else:
                message = "Invalid or expired code!"
                message_color = RED
                message_timer = current_time
            
            # Reset network result
            network_result = {"data": None, "error": None, "completed": False}
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if input box is clicked
                if input_box.collidepoint((vmx, vmy)):
                    input_active = True
                    if not keyboard.visible:
                        keyboard.toggle()
                else:
                    input_active = False
                
                # Check keyboard toggle button
                if keyboard.draw_toggle_button(virtual_surface, vmx, vmy):
                    keyboard.toggle()
                
                # Check keyboard key clicks
                if keyboard.visible:
                    clicked_key = keyboard.draw(virtual_surface, vmx, vmy)
                    if clicked_key:
                        new_text = keyboard.handle_key_input(clicked_key, input_text)
                        if new_text != input_text:
                            input_text = new_text
                            cached_input_surface = None  # Invalidate cache
                
                # Back button
                if back_button.collidepoint((vmx, vmy)):
                    return
                
                # Redeem button
                if redeem_button.collidepoint((vmx, vmy)) and not is_loading:
                    if input_text.strip():
                        code = input_text.strip().upper()
                        
                        if not validate_redeem_code_format(code):
                            message = "Invalid code format! Use letters, numbers, and hyphens only"
                            message_color = RED
                            message_timer = current_time
                        elif code in redeem_data["used_codes"]:
                            message = "Code already used!"
                            message_color = RED
                            message_timer = current_time
                        else:
                            # Start loading and network request in thread
                            is_loading = True
                            message = "Validating code"
                            message_color = WHITE
                            message_timer = current_time
                            
                            # Start network request in separate thread
                            thread = threading.Thread(target=fetch_codes_thread, args=(code,))
                            thread.daemon = True
                            thread.start()
                    else:
                        message = "Please enter a redeem code!"
                        message_color = RED
                        message_timer = current_time
            
            # Hardware keyboard support (optimized)
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_BACKSPACE:
                    if input_text:
                        input_text = input_text[:-1]
                        cached_input_surface = None
                elif event.key == pygame.K_RETURN:
                    pass  # Could trigger redeem here
                elif event.unicode.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-":
                    if len(input_text) < 25:
                        input_text += event.unicode.upper()
                        cached_input_surface = None
        
        # Draw title with cached rainbow color
        title_colored = title_font.render("REDEEM CODE", True, cached_rainbow_color)
        virtual_surface.blit(title_colored, title_colored.get_rect(center=(VIRTUAL_W // 2, 80)))
        
        # Draw pre-rendered instructions
        virtual_surface.blit(instruction1_surface, instruction1_surface.get_rect(center=(VIRTUAL_W // 2, 130)))
        virtual_surface.blit(instruction2_surface, instruction2_surface.get_rect(center=(VIRTUAL_W // 2, 150)))
        
        # Draw input box
        input_color = HOVER_COLOR if input_active else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, input_color, input_box, border_radius=8)
        pygame.draw.rect(virtual_surface, WHITE, input_box, 2, border_radius=8)
        
        # Draw input text with caching
        if input_text:
            # Only re-render if text changed
            if input_text != last_input_text or cached_input_surface is None:
                cached_input_surface = button_font.render(input_text, True, WHITE)
                last_input_text = input_text
            
            text_width = cached_input_surface.get_width()
            
            if text_width > input_box.width - 20:
                offset = text_width - (input_box.width - 20)
                clip_surface = pygame.Surface((input_box.width - 20, input_box.height - 10))
                clip_surface.blit(cached_input_surface, (-offset, 0))
                virtual_surface.blit(clip_surface, (input_box.x + 10, input_box.y + 15))
            else:
                virtual_surface.blit(cached_input_surface, (input_box.x + 10, input_box.y + 15))
        else:
            virtual_surface.blit(placeholder_surface, (input_box.x + 10, input_box.y + 18))
        
        # Draw cursor
        if input_active and cursor_visible:
            if input_text:
                text_width = cached_input_surface.get_width() if cached_input_surface else 0
                cursor_x = min(input_box.x + 10 + text_width, input_box.x + input_box.width - 10)
            else:
                cursor_x = input_box.x + 10
            pygame.draw.line(virtual_surface, WHITE, (cursor_x, input_box.y + 10), (cursor_x, input_box.y + 40), 2)
        
        # Draw redeem button
        button_hover = redeem_button.collidepoint((vmx, vmy))
        
        if is_loading:
            button_color = (100, 100, 100)
            button_text = f"Loading{'.' * loading_dots}"
        else:
            button_color = HOVER_COLOR if button_hover else BUTTON_COLOR
            button_text = "REDEEM"
        
        pygame.draw.rect(virtual_surface, button_color, redeem_button, border_radius=10)
        
        # Cache button text rendering
        cache_key = f"redeem_{button_text}"
        if cache_key not in text_cache:
            text_cache[cache_key] = button_font.render(button_text, True, WHITE)
        
        virtual_surface.blit(text_cache[cache_key], text_cache[cache_key].get_rect(center=redeem_button.center))
        
        # Draw back button
        back_hover = back_button.collidepoint((vmx, vmy))
        pygame.draw.rect(virtual_surface, HOVER_COLOR if back_hover else BUTTON_COLOR, back_button, border_radius=8)
        virtual_surface.blit(back_surface, back_surface.get_rect(center=back_button.center))
        
        # Draw keyboard (optimized)
        keyboard.draw_toggle_button(virtual_surface, vmx, vmy)
        keyboard.draw(virtual_surface, vmx, vmy)
        
        # Draw message
        if message and current_time - message_timer < 5000:
            msg_y = 350 if keyboard.visible else 400
            cache_key = f"msg_{message}_{message_color}"
            if cache_key not in text_cache:
                text_cache[cache_key] = button_font.render(message, True, message_color)
            virtual_surface.blit(text_cache[cache_key], text_cache[cache_key].get_rect(center=(VIRTUAL_W // 2, msg_y)))
        
        # Draw current resources info (only when keyboard is mostly hidden)
        if keyboard.animation_progress < 0.5:
            try:
                # Cache resource text
                resource_texts = [
                    f"Current Tengu Feathers: {dungeon_data['tengu_feathers']}",
                    f"Owned Characters: {len(character_data['owned_characters'])}",
                    f"Sakura: {summer_data['sakura']}",
                    f"Water: {summer_data['water']}",
                    f"Black Water: {summer_data['black_water']}"
                ]
                
                y_positions = [VIRTUAL_H - 120, VIRTUAL_H - 100, VIRTUAL_H - 80, VIRTUAL_H - 60, VIRTUAL_H - 40]
                
                for i, text in enumerate(resource_texts):
                    if text not in text_cache:
                        text_cache[text] = small_font.render(text, True, WHITE)
                    virtual_surface.blit(text_cache[text], (50, y_positions[i]))
            except:
                pass
        
        # Clean text cache periodically to prevent memory leaks
        if len(text_cache) > 100:
            text_cache.clear()
        
        draw_scaled_centered()
        clock.tick(60)

# Hero Knight Boss class - Improved Performance
class HeroKnightBoss:
    def __init__(self, x, y):
        self.character_type = "Hero_Knight"
        self.pos = [x, y]
        self.hp = 3000
        self.max_hp = 3000
        self.mp = 200
        self.max_mp = 200
        self.action = "Idle"
        self.frame_idx = 0
        self.timer = 0
        self.last_action_time = pygame.time.get_ticks()
        self.last_mp_regen = pygame.time.get_ticks()
        self.action_cooldown = 800  # Reduced from 1200 to 800ms for faster actions
        self.is_dead = False
        self.is_hurt = False
        self.hurt_timer = 0
        self.death_animation_complete = False
        self.is_shielding = False
        self.shield_timer = 0
        self.shield_start_time = 0
        self.attack_range = 100
        self.last_attack_time = 0
        self.ai_state = "IDLE"
        self.state_timer = 0
        self.movement_speed = 5  # Increased from 3 to 5
        self.is_boss = True
        
        # Load animations
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt", "Walk"]
        self.animations = load_animation_frames("Hero_Knight", actions, hero_knight_frame_counts)
        
        # Frame delays - Made faster for smoother animation
        self.frame_delays = {
            "Idle": 120,     # Reduced from 200
            "Run": 60,       # Reduced from 100
            "Jump": 80,      # Reduced from 150
            "Shield": 120,   # Reduced from 200
            "Attack_1": 70,  # Reduced from 120
            "Attack_2": 75,  # Reduced from 130
            "Attack_3": 80,  # Reduced from 140
            "Dead": 150,     # Reduced from 200
            "Hurt": 100,     # Reduced from 150
            "Walk": 70       # Reduced from 100
        }
    
    def take_damage(self, damage):
        if self.is_dead:
            return
        
        # Shield blocks 100% damage
        if self.is_shielding:
            return
            
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.action = "Dead"
            self.frame_idx = 0
            self.timer = 0
        else:
            self.is_hurt = True
            self.hurt_timer = pygame.time.get_ticks()
            self.action = "Hurt"
            self.frame_idx = 0
            self.timer = 0
            self.is_shielding = False
    
    def update_ai_state(self, player_pos):
        """Enhanced Boss AI - Faster decision making"""
        current_time = pygame.time.get_ticks()
        distance_to_player = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)

        # Faster state changes for more dynamic behavior
        if current_time - self.state_timer > 1000:  # Reduced from 1500 to 1000ms
            health_percentage = self.hp / self.max_hp
            
            if health_percentage < 0.2:  # Critical health - more aggressive
                if random.random() < 0.85:  # Increased aggression
                    self.ai_state = "ATTACK"
                else:
                    self.ai_state = "DEFEND"
            elif health_percentage < 0.5:  # Low health - balanced but faster
                if distance_to_player > self.attack_range:
                    self.ai_state = "APPROACH"
                elif random.random() < 0.7:  # Increased attack chance
                    self.ai_state = "ATTACK"
                else:
                    self.ai_state = "DEFEND"
            else:  # High health - more dynamic
                if distance_to_player > self.attack_range * 1.2:
                    self.ai_state = "APPROACH"
                elif distance_to_player < self.attack_range * 0.8:
                    action_choice = random.random()
                    if action_choice < 0.6:  # More attacks
                        self.ai_state = "ATTACK"
                    elif action_choice < 0.85:
                        self.ai_state = "DEFEND"
                    else:
                        self.ai_state = "RETREAT"
                else:
                    self.ai_state = "ATTACK"
            
            self.state_timer = current_time
    
    def execute_ai_action(self, player_pos):
        """Execute Boss actions - Optimized for smoother movement"""
        current_time = pygame.time.get_ticks()
        distance_to_player = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)

        if self.ai_state == "APPROACH":
            # Smoother movement towards player
            dx = player_pos[0] - self.pos[0]
            dy = player_pos[1] - self.pos[1]
            
            # Normalize movement for consistent speed
            if dx != 0:
                self.pos[0] += self.movement_speed if dx > 0 else -self.movement_speed
            if dy != 0:
                self.pos[1] += self.movement_speed if dy > 0 else -self.movement_speed
            
            self.action = "Run"
                
        elif self.ai_state == "RETREAT":
            # Smoother retreat movement
            dx = player_pos[0] - self.pos[0]
            dy = player_pos[1] - self.pos[1]
            
            if dx != 0:
                self.pos[0] += -self.movement_speed if dx > 0 else self.movement_speed
            if dy != 0:
                self.pos[1] += -self.movement_speed if dy > 0 else self.movement_speed
            
            self.action = "Run"
            
        elif self.ai_state == "ATTACK":
            # Faster, more frequent attacks
            if current_time - self.last_action_time > self.action_cooldown:
                attack_costs = {"Attack_1": 8, "Attack_2": 12, "Attack_3": 16}  # Reduced MP costs
                
                # Boss prefers stronger attacks when low on health
                health_percentage = self.hp / self.max_hp
                if health_percentage < 0.3:
                    available_attacks = ["Attack_3", "Attack_2", "Attack_1"]
                elif health_percentage < 0.6:
                    available_attacks = ["Attack_2", "Attack_3", "Attack_1"]
                else:
                    available_attacks = ["Attack_1", "Attack_2", "Attack_3"]
                
                for attack in available_attacks:
                    if self.mp >= attack_costs[attack]:
                        self.action = attack
                        self.frame_idx = 0
                        self.timer = 0
                        self.mp -= attack_costs[attack]
                        self.last_action_time = current_time
                        self.is_shielding = False
                        break
                else:
                    self.action = "Idle"
                    
        elif self.ai_state == "DEFEND":
            # Faster shield activation
            if self.mp >= 3 and not self.is_shielding:  # Reduced MP cost
                self.action = "Shield"
                self.is_shielding = True
                self.shield_timer = current_time
                self.shield_start_time = current_time
                self.mp -= 3
            elif self.is_shielding and current_time - self.shield_start_time > 2000:  # Reduced shield time
                self.is_shielding = False
                self.action = "Idle"
            elif not self.is_shielding:
                self.action = "Idle"
        else:
            # IDLE state
            self.action = "Idle"
            self.is_shielding = False
    
    def update(self, dt, player_pos):
        current_time = pygame.time.get_ticks()
        
        # Faster MP regeneration
        if current_time - self.last_mp_regen > 1000:  # Reduced from 1500 to 1000ms
            self.mp = min(self.max_mp, self.mp + 15)  # Increased regen amount
            self.last_mp_regen = current_time
        
        # Handle death
        if self.is_dead and not self.death_animation_complete:
            self.timer += dt
            delay = self.frame_delays.get("Dead", 150)
            if self.timer >= delay:
                self.timer = 0
                if self.animations["Dead"]:
                    self.frame_idx += 1
                    if self.frame_idx >= len(self.animations["Dead"]):
                        self.death_animation_complete = True
                        self.frame_idx = len(self.animations["Dead"]) - 1
            return
        
        if self.is_dead:
            return
        
        # Handle hurt state - Faster recovery
        if self.is_hurt:
            if current_time - self.hurt_timer > 250:  # Reduced from 400ms
                self.is_hurt = False
                self.action = "Idle"
                self.frame_idx = 0
                self.timer = 0
        
        # Handle shield timeout
        if self.is_shielding and current_time - self.shield_start_time > 2000:
            self.is_shielding = False
        
        # AI behavior (only if not hurt)
        if not self.is_hurt:
            self.update_ai_state(player_pos)
            self.execute_ai_action(player_pos)
        
        # Keep boss within screen bounds
        sprite_width = 160
        left_limit = sprite_width // 2
        right_limit = VIRTUAL_W - sprite_width // 2
        
        if self.pos[0] < left_limit:
            self.pos[0] = left_limit
        elif self.pos[0] > right_limit:
            self.pos[0] = right_limit
        
        # Optimized animation update
        self.timer += dt
        delay = self.frame_delays.get(self.action, 80)
        if self.timer >= delay:
            self.timer = 0
            if self.animations[self.action]:
                self.frame_idx += 1
                if self.frame_idx >= len(self.animations[self.action]):
                    if "Attack" in self.action:
                        self.action = "Idle"
                        self.frame_idx = 0
                    elif self.action == "Shield" and self.is_shielding:
                        self.frame_idx = len(self.animations["Shield"]) - 1
                    else:
                        self.frame_idx = 0
    
    def draw(self, surface):
        if self.animations[self.action]:
            frame_idx = min(self.frame_idx, len(self.animations[self.action]) - 1)
            sprite = pygame.transform.scale(self.animations[self.action][frame_idx], (160, 160))
            # Flip sprite to face left (towards player)
            sprite = pygame.transform.flip(sprite, True, False)
            rect = sprite.get_rect(midbottom=(self.pos[0], self.pos[1] + 100))
            surface.blit(sprite, rect.topleft)
        
        # Draw health bar (larger for boss)
        if not self.is_dead:
            bar_width = 150
            bar_height = 12
            bar_x = self.pos[0] - bar_width // 2
            bar_y = self.pos[1] - 200
            
            # Background bar
            pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            # Health bar
            health_width = int((self.hp / self.max_hp) * bar_width)
            health_color = RED if self.hp / self.max_hp < 0.3 else (255, 165, 0) if self.hp / self.max_hp < 0.6 else (0, 255, 0)
            pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))
            
            # MP bar
            mp_bar_y = bar_y + 16
            pygame.draw.rect(surface, (50, 50, 50), (bar_x, mp_bar_y, bar_width, bar_height))
            mp_width = int((self.mp / self.max_mp) * bar_width)
            pygame.draw.rect(surface, BLUE, (bar_x, mp_bar_y, mp_width, bar_height))
            
            # Boss name and health text
            name_text = button_font.render("HERO KNIGHT", True, (255, 215, 0))  # Gold color
            name_rect = name_text.get_rect(center=(self.pos[0], bar_y - 20))
            surface.blit(name_text, name_rect)
            
            health_text = pygame.font.SysFont("Verdana", 14).render(f"HP: {self.hp}/{self.max_hp}", True, WHITE)
            health_rect = health_text.get_rect(center=(self.pos[0], bar_y - 35))
            surface.blit(health_text, health_rect)
            
            # Shield indicator
            if self.is_shielding:
                shield_text = button_font.render("BOSS SHIELD", True, (0, 255, 255))
                shield_rect = shield_text.get_rect(center=(self.pos[0], self.pos[1] - 220))
                surface.blit(shield_text, shield_rect)
    
    def get_attack_damage(self):
        if "Attack" in self.action:
            damage_values = {"Attack_1": 8, "Attack_2": 12, "Attack_3": 16}
            return damage_values[self.action]
        return 0
    
    def is_attacking(self):
        return "Attack" in self.action and self.frame_idx > 0 and self.frame_idx < len(self.animations[self.action]) - 1
    
    def get_attack_range(self):
        return self.attack_range

def boss_gameplay_loop(name, selected_character):
    """Boss battle gameplay loop - Optimized for better performance"""
    PLAYER_MAX_HP = 300
    PLAYER_MAX_MP = 300
    hp = PLAYER_MAX_HP
    mp = PLAYER_MAX_MP
    last_mp_regen = pygame.time.get_ticks()
    is_shielding = False
    is_dead = False
    is_hurt = False
    hurt_timer = 0
    death_animation_complete = False
    last_attack_time = 0
    last_heal_time = 0
    heal_cooldown = 3000  # Reduced from 4000 to 3000ms
    heal_amount = 60      # Increased from 50

    # Store original music state to restore later
    original_music_playing = False
    try:
        original_music_playing = pygame.mixer.music.get_busy()
    except:
        pass

    # Load and play Hero Knight boss music
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load("assets/heroknightbg.mp3")
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1)
        print("Hero Knight boss music loaded successfully!")
    except pygame.error as e:
        print(f"Could not load Hero Knight boss music: {e}")

    # Load Hero Knight boss battle background
    try:
        bg = pygame.image.load("assets/heroknightbg.png").convert()
        bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
        print("Hero Knight boss background loaded successfully!")
    except pygame.error as e:
        print(f"Could not load Hero Knight boss background: {e}")
        # Fallback backgrounds
        try:
            bg = pygame.image.load("assets/bossbg.png").convert()
            bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            try:
                bg = pygame.image.load("assets/gamebg.png").convert()
                bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
            except:
                bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
                for y in range(VIRTUAL_H):
                    color_val = int(30 + (y / VIRTUAL_H) * 50)
                    pygame.draw.line(bg, (color_val, color_val//2, color_val//3), (0, y), (VIRTUAL_W, y))

    actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
    anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])

    # Faster frame delays for smoother player animation
    frame_delays = {
        "Idle": 100,     # Reduced from 160
        "Run": 80,       # Reduced from 140
        "Jump": 90,      # Reduced from 150
        "Shield": 100,   # Reduced from 170
        "Attack_1": 80,  # Reduced from 130
        "Attack_2": 85,  # Reduced from 135
        "Attack_3": 80,  # Reduced from 130
        "Dead": 120,     # Reduced from 170
        "Hurt": 100,     # Reduced from 170
        "Walk": 90       # Reduced from 150
    }

    action = "Idle"
    idx, timer = 0, 0
    pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
    vel = [0, 0]
    jumping = False
    jump_count = 2
    holding_shield = False

    # Create Hero Knight Boss
    boss = HeroKnightBoss(VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)

    def draw_boss_hud(name, hp, mp):
        # Player HUD (enhanced for boss fight)
        pygame.draw.rect(virtual_surface, (0, 0, 0), (10, 10, 220, 110), border_radius=8)
        # HP bar
        pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 25, 190, 12))
        pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 25, int((hp/PLAYER_MAX_HP) * 190), 12))
        # MP bar  
        pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 42, 190, 12))
        pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 42, int((mp/PLAYER_MAX_MP) * 190), 12))
        
        # Labels
        hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
        virtual_surface.blit(hp_text, (15, 60))
        mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
        virtual_surface.blit(mp_text, (15, 75))
        name_text = small_font.render(f"{name} vs HERO KNIGHT", True, WHITE)
        virtual_surface.blit(name_text, (15, 90))
        
        # Heal cooldown indicator
        current_time = pygame.time.get_ticks()
        heal_ready = current_time - last_heal_time >= heal_cooldown
        heal_text = small_font.render(f"HEAL: {'READY' if heal_ready else f'{((heal_cooldown - (current_time - last_heal_time)) // 1000) + 1}s'}", True, (0, 255, 0) if heal_ready else RED)
        virtual_surface.blit(heal_text, (15, 105))

    def check_boss_collision_and_damage():
        nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
        
        # Check if boss is attacking and close enough to player
        if boss.is_attacking():
            distance = abs(boss.pos[0] - pos[0])
            attack_range = boss.get_attack_range()
            
            if distance < attack_range:
                current_time = pygame.time.get_ticks()
                if current_time - boss.last_attack_time > 400:  # Reduced from 600ms
                    damage = boss.get_attack_damage()
                    
                    if is_shielding:
                        damage = 0
                    
                    if damage > 0:
                        hp -= damage
                        boss.last_attack_time = current_time
                        
                        if hp <= 0:
                            hp = 0
                            is_dead = True
                            action = "Dead"
                            idx = 0
                            timer = 0
                        else:
                            is_hurt = True
                            hurt_timer = pygame.time.get_ticks()
                            action = "Hurt"
                            idx = 0
                            timer = 0
        
        # Check if player is attacking boss
        if "Attack" in action and idx > 0:
            distance = abs(pos[0] - boss.pos[0])
            player_range = character_ranges[selected_character]
            
            if distance < player_range:
                current_time = pygame.time.get_ticks()
                if current_time - last_attack_time > 300:  # Reduced from 500ms
                    damage = character_damage[selected_character][action]
                    boss.take_damage(damage)
                    last_attack_time = current_time

    # UI Setup - Optimized button sizes for faster interaction
    size = 55  # Slightly smaller for faster touch
    spacing = 8
    dir_center_x = 85
    dir_center_y = VIRTUAL_H - 270

    left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
    right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
    up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
    down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

    btn_w, btn_h = 75, 55  # Optimized button size
    action_y = VIRTUAL_H - btn_h - 8
    heal_y = action_y - btn_h - 8
    
    action_buttons = {
        "atk1": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 6, action_y, btn_w, btn_h),
        "atk2": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 5, action_y, btn_w, btn_h),
        "atk3": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 4, action_y, btn_w, btn_h),
        "jump": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 3, action_y, btn_w, btn_h),
        "shield": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 2, action_y, btn_w, btn_h),
        "run": pygame.Rect(VIRTUAL_W - (btn_w + spacing), action_y, btn_w, btn_h),
        "heal": pygame.Rect(VIRTUAL_W - (btn_w + spacing), heal_y, btn_w, btn_h),
    }

    pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)

    def cleanup_and_restore_music():
        """Clean up boss music and restore original music if needed"""
        try:
            pygame.mixer.music.stop()
            if original_music_playing:
                try:
                    pygame.mixer.music.load("assets/mainmenubg.mp3")
                    pygame.mixer.music.play(-1)
                except:
                    pass
        except:
            pass

    try:
        while True:
            dt = clock.tick(90)  # Increased from 60 to 90 FPS for smoother gameplay
            timer += dt
            now = pygame.time.get_ticks()

            # Check for game over conditions
            if is_dead and death_animation_complete:
                cleanup_and_restore_music()
                result = game_over_screen(False, name)
                if result == "restart":
                    return "restart"
                elif result == "menu":
                    return "back"
            
            if boss.is_dead and boss.death_animation_complete:
                # Check for Hero Knight character unlock (1-2% chance)
                unlock_chance = random.random()
                if unlock_chance <= 0.02:
                    character_data = load_character_data()
                    if "Hero_Knight" not in character_data["owned_characters"]:
                        character_data["owned_characters"].append("Hero_Knight")
                        save_character_data(character_data)
                        cleanup_and_restore_music()
                        unlock_screen(name)
                
                cleanup_and_restore_music()
                result = game_over_screen(True, name)
                if result == "restart":
                    return "restart"
                elif result == "menu":
                    return "back"

            # Faster MP regeneration
            if now - last_mp_regen > 2000:  # Reduced from 2500ms
                mp = min(PLAYER_MAX_MP, mp + 20)  # Increased from 15
                last_mp_regen = now

            # Handle hurt state - Faster recovery
            if is_hurt and now - hurt_timer > 600:  # Reduced from 800ms
                is_hurt = False
                if not is_dead:
                    action = "Idle"
                    idx = 0
                    timer = 0

            for e in pygame.event.get():
                if e.type == pygame.QUIT: 
                    cleanup_and_restore_music()
                    exit_game()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    cleanup_and_restore_music()
                    return "back"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    mx, my = ((mx - ox) / scale, (my - oy) / scale)

                    if pause_button.collidepoint((mx, my)):
                        pause_result = pause_menu()
                        if pause_result == "back":
                            cleanup_and_restore_music()
                            return "back" 
                        elif pause_result == "restart":
                            cleanup_and_restore_music()
                            return "restart"

                    if is_dead or is_hurt:
                        continue

                    # Movement controls - Faster movement
                    if left.collidepoint((mx, my)): 
                        vel[0] = -6; action = "Run"; is_shielding = False  # Increased from -4
                    elif right.collidepoint((mx, my)): 
                        vel[0] = 6; action = "Run"; is_shielding = False   # Increased from 4
                    elif up.collidepoint((mx, my)): 
                        vel[1] = -6; action = "Run"; is_shielding = False  # Increased from -4
                    elif down.collidepoint((mx, my)): 
                        vel[1] = 6; action = "Run"; is_shielding = False   # Increased from 4
                    
                    # Action buttons - Reduced MP costs for faster gameplay
                    elif action_buttons["atk1"].collidepoint((mx, my)):
                        if mp >= 3:  # Reduced from 5
                            action = "Attack_1"; idx = 0; timer = 0; mp -= 3; is_shielding = False
                    elif action_buttons["atk2"].collidepoint((mx, my)):
                        if mp >= 5:  # Reduced from 8
                            action = "Attack_2"; idx = 0; timer = 0; mp -= 5; is_shielding = False
                    elif action_buttons["atk3"].collidepoint((mx, my)):
                        if mp >= 8:  # Reduced from 12
                            action = "Attack_3"; idx = 0; timer = 0; mp -= 8; is_shielding = False
                    elif action_buttons["jump"].collidepoint((mx, my)):
                        if jump_count > 0:
                            vel[1] = -12; action = "Jump"; jumping = True  # Increased jump power
                            jump_count -= 1; idx = 0; timer = 0; is_shielding = False
                    elif action_buttons["shield"].collidepoint((mx, my)):
                        holding_shield = True; action = "Shield"; idx = 0; timer = 0; is_shielding = True
                    elif action_buttons["run"].collidepoint((mx, my)):
                        vel[0] = 8; action = "Run"; is_shielding = False  # Increased from 6
                    elif action_buttons["heal"].collidepoint((mx, my)):
                        if now - last_heal_time >= heal_cooldown:
                            hp = min(PLAYER_MAX_HP, hp + heal_amount)
                            last_heal_time = now

                if e.type == pygame.MOUSEBUTTONUP:
                    if not is_dead and not is_hurt:
                        vel = [0, 0]; holding_shield = False; is_shielding = False
                        if not jumping: action = "Idle"

            # Physics update - Improved physics
            if not is_dead:
                if jumping:
                    vel[1] += 0.6  # Slightly increased gravity
                    pos[1] += vel[1]
                    if pos[1] >= VIRTUAL_H - 150:
                        pos[1] = VIRTUAL_H - 150; jumping = False
                        vel[1] = 0; jump_count = 2
                        if not is_hurt:
                            action = "Idle"
                else:
                    pos[0] += vel[0]
                    pos[1] += vel[1]

                # Keep player within bounds
                sprite_width, sprite_height = 160, 160
                left_limit = sprite_width // 2
                right_limit = VIRTUAL_W - sprite_width // 2
                top_limit = 0
                bottom_limit = VIRTUAL_H - sprite_height

                if pos[0] < left_limit:
                    pos[0] = left_limit
                    vel[0] = -vel[0] * 0.3  # Reduced bounce
                elif pos[0] > right_limit:
                    pos[0] = right_limit
                    vel[0] = -vel[0] * 0.3

                if pos[1] < top_limit:
                    pos[1] = top_limit
                    vel[1] = -vel[1] * 0.3
                elif pos[1] > bottom_limit:
                    pos[1] = bottom_limit
                    vel[1] = -vel[1] * 0.3

            # Update boss
            boss.update(dt, pos)
            
            # Check combat interactions
            check_boss_collision_and_damage()

            # Update player animation - Optimized
            delay = frame_delays.get(action, 80)
            if timer >= delay:
                timer = 0
                if anims[action]:
                    idx += 1
                    if idx >= len(anims[action]):
                        if action == "Dead":
                            death_animation_complete = True
                            idx = len(anims["Dead"]) - 1
                        elif "Attack" in action or action == "Jump":
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0
                        elif action == "Shield" and holding_shield:
                            idx = len(anims["Shield"]) - 1
                        elif action == "Hurt":
                            idx = len(anims["Hurt"]) - 1
                        else:
                            if not is_hurt and not is_dead:
                                action = "Idle"; idx = 0

            # Draw everything
            virtual_surface.blit(bg, (0, 0))
            
            # Draw player
            if anims[action]:
                idx = min(idx, len(anims[action]) - 1)
                sprite = pygame.transform.scale(anims[action][idx], (160, 160))
                rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                virtual_surface.blit(sprite, rect.topleft)
                
                if is_shielding:
                    shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                    shield_rect = shield_text.get_rect(center=(pos[0], pos[1] - 100))
                    virtual_surface.blit(shield_text, shield_rect)
            
            # Draw boss
            boss.draw(virtual_surface)

            # Draw UI elements only if not dead
            if not is_dead:
                # Movement buttons
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, left, border_radius=8)
                txt = button_font.render("<", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=left.center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, right, border_radius=8)
                txt = button_font.render(">", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=right.center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, up, border_radius=8)
                txt = button_font.render("^", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=up.center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, down, border_radius=8)
                txt = button_font.render("v", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=down.center))
                
                # Attack buttons with reduced MP requirements
                atk1_color = BUTTON_COLOR if mp >= 3 else (100, 100, 100)  # Reduced from 5
                atk2_color = BUTTON_COLOR if mp >= 5 else (100, 100, 100)  # Reduced from 8
                atk3_color = BUTTON_COLOR if mp >= 8 else (100, 100, 100)  # Reduced from 12
                
                pygame.draw.rect(virtual_surface, atk1_color, action_buttons["atk1"], border_radius=8)
                txt = small_font.render("Atk 1", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["atk1"].center))
                
                pygame.draw.rect(virtual_surface, atk2_color, action_buttons["atk2"], border_radius=8)
                txt = small_font.render("Atk 2", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["atk2"].center))
                
                pygame.draw.rect(virtual_surface, atk3_color, action_buttons["atk3"], border_radius=8)
                txt = small_font.render("Atk 3", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["atk3"].center))
                
                # Other action buttons
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["jump"], border_radius=8)
                txt = small_font.render("Jump", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["jump"].center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["shield"], border_radius=8)
                txt = small_font.render("Shield", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["shield"].center))
                
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, action_buttons["run"], border_radius=8)
                txt = small_font.render("Run", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["run"].center))
                
                # Heal button
                heal_ready = now - last_heal_time >= heal_cooldown
                heal_color = BUTTON_COLOR if heal_ready else (100, 100, 100)
                pygame.draw.rect(virtual_surface, heal_color, action_buttons["heal"], border_radius=8)
                txt = small_font.render("Heal", True, WHITE)
                virtual_surface.blit(txt, txt.get_rect(center=action_buttons["heal"].center))

            # Draw pause button
            try:
                settings_icon = pygame.image.load("assets/gamesettings.png").convert_alpha()
                settings_icon = pygame.transform.smoothscale(settings_icon, (40, 40))
                virtual_surface.blit(settings_icon, pause_button.topleft)
            except:
                gear_text = small_font.render("⚙", True, WHITE)
                virtual_surface.blit(gear_text, gear_text.get_rect(center=pause_button.center))

            draw_boss_hud(name, hp, mp)
            
            # Draw boss battle title with special effects
            battle_text = button_font.render("BOSS BATTLE: HERO KNIGHT", True, (255, 215, 0))
            # Add glow effect
            glow_surface = pygame.Surface((battle_text.get_width() + 4, battle_text.get_height() + 4))
            glow_surface.set_alpha(100)
            glow_text = button_font.render("BOSS BATTLE: HERO KNIGHT", True, (255, 215, 0))
            glow_surface.blit(glow_text, (2, 2))
            virtual_surface.blit(glow_surface, (VIRTUAL_W//2 - glow_surface.get_width()//2, 8))
            virtual_surface.blit(battle_text, (VIRTUAL_W//2 - battle_text.get_width()//2, 10))
            
            # Add epic subtitle
            subtitle_text = small_font.render("LEGENDARY ENCOUNTER ", True, (255, 255, 255))
            virtual_surface.blit(subtitle_text, (VIRTUAL_W//2 - subtitle_text.get_width()//2, 35))
            
            draw_scaled_centered()

    except Exception as e:
        print(f"Error in boss battle: {e}")
        cleanup_and_restore_music()
        return "back"

def hero_knight_boss():
    """Hero Knight Boss Battle - Enhanced for better performance"""
    # Get player name and character
    def input_name_screen():
        input_box = pygame.Rect(200, 250, 400, 50)
        color_inactive = pygame.Color('gray')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = False
        user_text = ""

        keys = []
        key_w, key_h = 40, 40
        start_x = 140
        start_y = 400
        row_layout = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_idx, row in enumerate(row_layout):
            for col_idx, char in enumerate(row):
                x = start_x + col_idx * (key_w + 5)
                y = start_y + row_idx * (key_h + 5)
                rect = pygame.Rect(x, y, key_w, key_h)
                keys.append((char, rect))

        backspace_rect = pygame.Rect(start_x, start_y + 3 * (key_h + 5), 120, 40)
        enter_rect = pygame.Rect(start_x + 130, start_y + 3 * (key_h + 5), 150, 40)

        while True:
            virtual_surface.fill((30, 30, 60))

            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint((vmx, vmy)):
                        active = True
                        color = color_active
                    else:
                        active = False
                        color = color_inactive

                    for char, rect in keys:
                        if rect.collidepoint((vmx, vmy)):
                            if len(user_text) < 12:
                                user_text += char

                    if backspace_rect.collidepoint((vmx, vmy)):
                        user_text = user_text[:-1]

                    if enter_rect.collidepoint((vmx, vmy)) and user_text.strip():
                        return user_text

            txt_surface = button_font.render(user_text, True, WHITE)
            width = max(400, txt_surface.get_width() + 10)
            input_box.w = width

            pygame.draw.rect(virtual_surface, color, input_box, 2)
            virtual_surface.blit(txt_surface, (input_box.x + 5, input_box.y + 10))

            prompt = title_font.render("Enter Your Name", True, get_rainbow_color())
            virtual_surface.blit(prompt, prompt.get_rect(center=(VIRTUAL_W // 2, 180)))

            for char, rect in keys:
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=5)
                label = button_font.render(char, True, WHITE)
                virtual_surface.blit(label, label.get_rect(center=rect.center))

            pygame.draw.rect(virtual_surface, BUTTON_COLOR, backspace_rect, border_radius=5)
            bksp_text = button_font.render("Backspace", True, WHITE)
            virtual_surface.blit(bksp_text, bksp_text.get_rect(center=backspace_rect.center))

            pygame.draw.rect(virtual_surface, HOVER_COLOR if user_text.strip() else (100, 100, 100), enter_rect, border_radius=5)
            ent_text = button_font.render("Enter", True, WHITE)
            virtual_surface.blit(ent_text, ent_text.get_rect(center=enter_rect.center))

            draw_scaled_centered()
            clock.tick(60)  # Smooth input experience

    # Get player info
    name = input_name_screen()
    selected_character = character_selection_screen()
    if not selected_character:
        return "back"
    
    # Boss battle loop
    while True:
        result = boss_gameplay_loop(name, selected_character)
        if result == "back":
            return "back"
        elif result == "restart":
            continue

def unlock_screen(player_name):
    """Screen shown when Hero Knight is unlocked - Optimized"""
    overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    
    continue_button = pygame.Rect(VIRTUAL_W//2 - 100, 400, 200, 60)
    
    # Animation variables
    start_time = pygame.time.get_ticks()
    
    # Play unlock sound effect if available
    try:
        unlock_sound = pygame.mixer.Sound("assets/unlock.wav")
        unlock_sound.play()
    except:
        pass
    
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - start_time
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if continue_button.collidepoint((vmx, vmy)) or elapsed > 4000:  # Reduced from 5000ms
                    return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN or elapsed > 4000:
                    return

        # Draw overlay
        virtual_surface.blit(overlay, (0, 0))
        
        # Animated title with pulsing effect
        pulse = abs(math.sin(elapsed * 0.006)) * 0.3 + 0.7  # Slightly faster pulse
        title_color = [int(255 * pulse), int(215 * pulse), int(0 * pulse)]
        unlock_title = title_font.render("CHARACTER UNLOCKED!", True, title_color)
        virtual_surface.blit(unlock_title, unlock_title.get_rect(center=(VIRTUAL_W // 2, 150)))
        
        # Character name with golden glow
        char_text = button_font.render("⚔️ HERO KNIGHT ⚔️", True, (255, 215, 0))
        # Add glow effect
        glow_surface = pygame.Surface((char_text.get_width() + 4, char_text.get_height() + 4))
        glow_surface.set_alpha(150)
        glow_text = button_font.render("⚔️ HERO KNIGHT ⚔️", True, (255, 165, 0))
        glow_surface.blit(glow_text, (2, 2))
        virtual_surface.blit(glow_surface, (VIRTUAL_W//2 - glow_surface.get_width()//2, 218))
        virtual_surface.blit(char_text, char_text.get_rect(center=(VIRTUAL_W // 2, 220)))
        
        # Congratulations message
        congrats_text = small_font.render(f"🎉 Congratulations {player_name}! 🎉", True, WHITE)
        virtual_surface.blit(congrats_text, congrats_text.get_rect(center=(VIRTUAL_W // 2, 270)))
        
        # Unlock message
        unlock_msg = small_font.render("You have unlocked the legendary Hero Knight!", True, WHITE)
        virtual_surface.blit(unlock_msg, unlock_msg.get_rect(center=(VIRTUAL_W // 2, 300)))
        
        # Rarity message with sparkle effect
        rarity_text = small_font.render("✨ Unlock Rate: 1-2% (Very Rare!) ✨", True, (255, 215, 0))
        virtual_surface.blit(rarity_text, rarity_text.get_rect(center=(VIRTUAL_W // 2, 330)))
        
        # Hero Knight stats preview
        stats_title = small_font.render("Hero Knight Stats:", True, (200, 200, 200))
        virtual_surface.blit(stats_title, stats_title.get_rect(center=(VIRTUAL_W // 2, 360)))
        
        stats_text = [
            "Attack 1: 12 damage",
            "Attack 2: 16 damage", 
            "Attack 3: 25 damage",
            "Range: Medium (100)"
        ]
        
        for i, stat in enumerate(stats_text):
            stat_render = pygame.font.SysFont("Verdana", 12).render(stat, True, (150, 150, 150))
            virtual_surface.blit(stat_render, stat_render.get_rect(center=(VIRTUAL_W // 2, 375 + i * 15)))
        
        # Continue button (appears after 1.5 seconds - faster)
        if elapsed > 1500:  # Reduced from 2000ms
            color = HOVER_COLOR if continue_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            pygame.draw.rect(virtual_surface, color, continue_button, border_radius=10)
            continue_text = button_font.render("CONTINUE", True, WHITE)
            virtual_surface.blit(continue_text, continue_text.get_rect(center=continue_button.center))
            
            # Add instruction text
            instruction = pygame.font.SysFont("Verdana", 11).render("Press SPACE or click to continue", True, (180, 180, 180))
            virtual_surface.blit(instruction, instruction.get_rect(center=(VIRTUAL_W // 2, 480)))
        
        # Optimized particle effects
        if elapsed > 800:  # Start particles earlier
            for i in range(8):  # Reduced particle count for better performance
                sparkle_x = VIRTUAL_W // 2 + math.sin(elapsed * 0.012 + i) * (100 + i * 10)
                sparkle_y = 200 + math.cos(elapsed * 0.01 + i) * 50
                sparkle_alpha = abs(math.sin(elapsed * 0.025 + i)) * 200  # Slightly less alpha
                sparkle_size = int(abs(math.sin(elapsed * 0.018 + i)) * 3) + 1
                
                if sparkle_alpha > 50:  # Only draw visible sparkles
                    sparkle_surface = pygame.Surface((sparkle_size * 2, sparkle_size * 2))
                    sparkle_surface.set_alpha(sparkle_alpha)
                    pygame.draw.circle(sparkle_surface, (255, 255, 255), (sparkle_size, sparkle_size), sparkle_size)
                    virtual_surface.blit(sparkle_surface, (sparkle_x - sparkle_size, sparkle_y - sparkle_size))
        
        draw_scaled_centered()
        clock.tick(75)  # Increased FPS for smoother animation
        
DUNGEON_DATA_FILE = "dungeon_data.json"

# Frame counts for new bosses
fire_worm_frame_counts = {
    "Attack_1": 16, "Dead": 8, "Hurt": 3, "Idle": 9, 
    "Run": 9, "Shield": 3, "Walk": 9
}

flying_demon_frame_counts = {
    "Attack_1": 8, "Dead": 6, "Hurt": 4, "Idle": 4,
    "Run": 4, "Shield": 4, "Walk": 4
}

skeleton_frame_counts = {
    "Attack_1": 8, "Attack_2": 8, "Attack_3": 6, "Dead": 4,
    "Hurt": 4, "Idle": 4, "Run": 4, "Shield": 4, "Walk": 4
}

# Damage values for new bosses
fire_worm_damage = {"Attack_1": 15}
flying_demon_damage = {"Attack_1": 30}
skeleton_damage = {"Attack_1": 12, "Attack_2": 16, "Attack_3": 25}

# Load/Save dungeon data
def load_dungeon_data():
    if os.path.exists(DUNGEON_DATA_FILE):
        try:
            with open(DUNGEON_DATA_FILE, 'r') as f:
                data = json.load(f)
                # Add stamina system if not exists
                if "stamina" not in data:
                    data["stamina"] = 100
                if "last_stamina_regen" not in data:
                    data["last_stamina_regen"] = datetime.now().isoformat()
                return data
        except:
            pass
    return {
        "tengu_feathers": 0,
        "battle_count": 0,
        "last_reset": datetime.now().isoformat(),
        "inventory": [],
        "stamina": 100,
        "last_stamina_regen": datetime.now().isoformat()
    }

def save_dungeon_data(data):
    with open(DUNGEON_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def update_stamina(dungeon_data):
    """Update stamina based on time passed"""
    current_time = datetime.now()
    last_regen = datetime.fromisoformat(dungeon_data["last_stamina_regen"])
    time_diff = current_time - last_regen
    
    # Regenerate 20 stamina every 10 minutes
    minutes_passed = time_diff.total_seconds() / 60
    stamina_to_add = int(minutes_passed / 10) * 20
    
    if stamina_to_add > 0:
        dungeon_data["stamina"] = min(100, dungeon_data["stamina"] + stamina_to_add)
        # Update last regen time to account for used regeneration
        regeneration_intervals = stamina_to_add // 20
        dungeon_data["last_stamina_regen"] = (last_regen + timedelta(minutes=regeneration_intervals * 10)).isoformat()
        save_dungeon_data(dungeon_data)

# Base Boss class
class Boss:
    def __init__(self, boss_type, difficulty="Easy"):
        self.boss_type = boss_type
        self.difficulty = difficulty
        self.setup_stats()
        self.pos = [VIRTUAL_W * 3 // 4, VIRTUAL_H - 150]
        self.action = "Idle"
        self.frame_idx = 0
        self.timer = 0
        self.is_dead = False
        self.is_hurt = False
        self.hurt_timer = 0
        self.death_animation_complete = False
        self.last_attack_time = 0
        self.movement_speed = 3
        self.ai_state = "APPROACH"
        self.state_timer = 0
        self.attack_range = 100
        self.last_action_time = 0
        self.action_cooldown = 1000
        
        # Status effects
        self.burning_timer = 0
        self.burning_damage = 0
        self.bloodsteal_chance = 0
        
        # Load animations and setup
        self.load_animations()
        self.setup_frame_delays()
    
    def setup_stats(self):
        """Setup HP and other stats based on boss type and difficulty"""
        stats = {
            "karasu": {"Easy": 250, "Medium": 500, "Hard": 1000},
            "fire_worm": {"Easy": 400, "Medium": 800, "Hard": 1600},
            "flying_demon": {"Easy": 250, "Medium": 500, "Hard": 1000},
            "skeleton": {"Easy": 1200, "Medium": 2500, "Hard": 5000}
        }
        
        self.max_hp = stats[self.boss_type][self.difficulty]
        self.hp = self.max_hp
    
    def load_animations(self):
        """Load animations based on boss type"""
        frame_counts = {
            "karasu": karasu_frame_counts,
            "fire_worm": fire_worm_frame_counts,
            "flying_demon": flying_demon_frame_counts,
            "skeleton": skeleton_frame_counts
        }
        
        paths = {
            "karasu": "Dungeons/Karasu_tengu",
            "fire_worm": "Dungeons/Fire_worm",
            "flying_demon": "Dungeons/Flying_demon",
            "skeleton": "Dungeons/Skeleton"
        }
        
        actions = list(frame_counts[self.boss_type].keys())
        self.animations = load_animation_frames(paths[self.boss_type], actions, frame_counts[self.boss_type])
    
    def setup_frame_delays(self):
        """Setup frame delays for animations"""
        self.frame_delays = {
            "Idle": 160, "Run": 120, "Jump": 100, "Walk": 140,
            "Attack_1": 120, "Attack_2": 110, "Attack_3": 130,
            "Dead": 180, "Hurt": 150, "Shield": 170
        }
    
    def take_damage(self, damage):
        if self.is_dead:
            return False
        
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.action = "Dead"
            self.frame_idx = 0
            self.timer = 0
            return True
        else:
            self.is_hurt = True
            self.hurt_timer = pygame.time.get_ticks()
            self.action = "Hurt"
            self.frame_idx = 0
            self.timer = 0
        
        return True
    
    def update_ai(self, player_pos):
        """AI behavior"""
        current_time = pygame.time.get_ticks()
        distance_to_player = math.sqrt((self.pos[0] - player_pos[0])**2 + (self.pos[1] - player_pos[1])**2)
        
        if current_time - self.state_timer > 1500:
            if distance_to_player > self.attack_range:
                self.ai_state = "APPROACH"
            elif distance_to_player < self.attack_range * 0.8:
                if random.random() < 0.7:
                    self.ai_state = "ATTACK"
                else:
                    self.ai_state = "IDLE"
            else:
                action_choice = random.random()
                if action_choice < 0.5:
                    self.ai_state = "ATTACK"
                elif action_choice < 0.7:
                    self.ai_state = "APPROACH"
                else:
                    self.ai_state = "IDLE"
            
            self.state_timer = current_time
    
    def execute_ai_action(self, player_pos):
        """Execute AI actions"""
        current_time = pygame.time.get_ticks()
        
        if self.ai_state == "APPROACH":
            if self.pos[0] < player_pos[0]:
                self.pos[0] += self.movement_speed
            else:
                self.pos[0] -= self.movement_speed
            
            if self.pos[1] < player_pos[1]:
                self.pos[1] += self.movement_speed
            else:
                self.pos[1] -= self.movement_speed
            
            self.action = "Run"
            
        elif self.ai_state == "ATTACK":
            if current_time - self.last_action_time > self.action_cooldown:
                attacks = [key for key in self.animations.keys() if "Attack" in key]
                if attacks:
                    chosen_attack = random.choice(attacks)
                    self.action = chosen_attack
                    self.frame_idx = 0
                    self.timer = 0
                    self.last_action_time = current_time
                
        elif self.ai_state == "IDLE":
            self.action = "Idle"
    
    def update(self, dt, player_pos):
        current_time = pygame.time.get_ticks()
        
        # Handle death
        if self.is_dead and not self.death_animation_complete:
            self.timer += dt
            delay = self.frame_delays.get("Dead", 180)
            if self.timer >= delay:
                self.timer = 0
                if self.animations["Dead"]:
                    self.frame_idx += 1
                    if self.frame_idx >= len(self.animations["Dead"]):
                        self.death_animation_complete = True
                        self.frame_idx = len(self.animations["Dead"]) - 1
            return
        
        if self.is_dead:
            return
        
        # Handle hurt state
        if self.is_hurt:
            if current_time - self.hurt_timer > 500:
                self.is_hurt = False
                self.action = "Idle"
                self.frame_idx = 0
                self.timer = 0
        
        # AI behavior (only if not hurt)
        if not self.is_hurt:
            self.update_ai(player_pos)
            self.execute_ai_action(player_pos)
        
        # Keep boss within screen bounds
        sprite_width = 160
        left_limit = sprite_width // 2
        right_limit = VIRTUAL_W - sprite_width // 2
        
        if self.pos[0] < left_limit:
            self.pos[0] = left_limit
        elif self.pos[0] > right_limit:
            self.pos[0] = right_limit
        
        # Update animation
        self.timer += dt
        delay = self.frame_delays.get(self.action, 130)
        if self.timer >= delay:
            self.timer = 0
            if self.animations[self.action]:
                self.frame_idx += 1
                if self.frame_idx >= len(self.animations[self.action]):
                    if "Attack" in self.action:
                        self.action = "Idle"
                        self.frame_idx = 0
                    else:
                        self.frame_idx = 0
    
    def draw(self, surface):
        if self.animations[self.action]:
            frame_idx = min(self.frame_idx, len(self.animations[self.action]) - 1)
            sprite = pygame.transform.scale(self.animations[self.action][frame_idx], (160, 160))
            # Flip sprite to face left (towards player)
            sprite = pygame.transform.flip(sprite, True, False)
            rect = sprite.get_rect(midbottom=(self.pos[0], self.pos[1] + 100))
            surface.blit(sprite, rect.topleft)
        
        # Draw boss health bar
        bar_width = 200
        bar_height = 15
        bar_x = self.pos[0] - bar_width // 2
        bar_y = self.pos[1] - 200
        
        # Background bar
        pygame.draw.rect(surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        # Health bar with color coding
        health_percentage = self.hp / self.max_hp
        if health_percentage > 0.6:
            health_color = (0, 255, 0)  # Green
        elif health_percentage > 0.3:
            health_color = (255, 255, 0)  # Yellow
        else:
            health_color = (255, 0, 0)  # Red
            
        health_width = int(health_percentage * bar_width)
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Boss name and HP text
        boss_names = {
            "karasu": "Karasu Tengu",
            "fire_worm": "Fire Worm", 
            "flying_demon": "Flying Demon",
            "skeleton": "Skeleton"
        }
        name_text = button_font.render(f"{boss_names[self.boss_type]} ({self.difficulty})", True, WHITE)
        name_rect = name_text.get_rect(center=(self.pos[0], bar_y - 20))
        surface.blit(name_text, name_rect)
        
        hp_text = small_font.render(f"{self.hp}/{self.max_hp}", True, WHITE)
        hp_rect = hp_text.get_rect(center=(self.pos[0], bar_y + 25))
        surface.blit(hp_text, hp_rect)
        
        # Status effects display
        status_y = self.pos[1] - 230
        if self.burning_timer > 0:
            burn_text = small_font.render("BURNING", True, (255, 100, 0))
            burn_rect = burn_text.get_rect(center=(self.pos[0], status_y))
            surface.blit(burn_text, burn_rect)
    
    def get_attack_damage(self):
        if "Attack" in self.action:
            damage_tables = {
                "karasu": karasu_damage,
                "fire_worm": fire_worm_damage,
                "flying_demon": flying_demon_damage,
                "skeleton": skeleton_damage
            }
            return damage_tables[self.boss_type].get(self.action, 0)
        return 0
    
    def is_attacking(self):
        return "Attack" in self.action and self.frame_idx > 0 and self.frame_idx < len(self.animations[self.action]) - 1
    
    def apply_special_effects(self, player):
        """Apply special effects based on boss type"""
        if self.boss_type == "fire_worm" and "Attack" in self.action:
            # Burning effect
            player["burning_timer"] = pygame.time.get_ticks() + 5000  # 5 seconds
            player["burning_damage"] = 15
        
        elif self.boss_type == "flying_demon" and "Attack" in self.action:
            # Bloodsteal effect
            if random.random() < 0.5:  # 50% chance
                stolen_hp = 20
                self.hp = min(self.max_hp, self.hp + stolen_hp)
                return stolen_hp
        
        return 0

# Legacy Karasu Tengu class for backward compatibility
class KarasuTengu(Boss):
    def __init__(self, difficulty="Easy"):
        super().__init__("karasu", difficulty)
        # Add Karasu-specific attributes
        self.damage_boost = 0
        self.damage_boost_timer = 0
        self.defense_boost = False
        self.defense_boost_timer = 0
        self.recover_used = False
        self.absolute_defend = False
        self.absolute_defend_timer = 0
        self.taunt_timer = 0
    
    def take_damage(self, damage):
        if self.is_dead or self.absolute_defend:
            return False
        
        # Apply defense boost if active
        if self.defense_boost:
            damage = int(damage * 0.5)
        
        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            self.action = "Dead"
            self.frame_idx = 0
            self.timer = 0
            return True
        else:
            self.is_hurt = True
            self.hurt_timer = pygame.time.get_ticks()
            self.action = "Hurt"
            self.frame_idx = 0
            self.timer = 0
            
            # Check for special abilities at 50% HP
            if self.hp <= self.max_hp // 2 and not self.recover_used:
                if random.random() < 0.6:  # 60% chance to recover
                    self.recover()
                else:
                    self.activate_absolute_defend()
        
        return True
    
    def recover(self):
        """Recovery ability - heal HP once"""
        heal_amount = random.randint(25, 50)
        self.hp = min(self.max_hp, self.hp + heal_amount)
        self.recover_used = True
        self.defense_boost = True
        self.defense_boost_timer = pygame.time.get_ticks()
        self.damage_boost = 5
        self.damage_boost_timer = pygame.time.get_ticks()
    
    def activate_absolute_defend(self):
        """Absolute Defense ability"""
        self.absolute_defend = True
        self.absolute_defend_timer = pygame.time.get_ticks()
        self.taunt_timer = pygame.time.get_ticks()

def dungeon():
    """Main dungeon function"""
    # Load dungeon data
    dungeon_data = load_dungeon_data()
    
    # Update stamina based on time passed
    update_stamina(dungeon_data)
    
    # Check if 5 hours have passed since last reset for battle count
    last_reset = datetime.fromisoformat(dungeon_data["last_reset"])
    if datetime.now() - last_reset >= timedelta(hours=5):
        dungeon_data["battle_count"] = 0
        dungeon_data["last_reset"] = datetime.now().isoformat()
        save_dungeon_data(dungeon_data)
                                     
    def dungeon_selection_screen():
        """Dungeon selection screen with navigation - Optimized for smooth performance"""
        
        # Pre-load and cache all assets once
        assets_cache = {}
        
        # Load background
        try:
            dungeon_bg = pygame.image.load("assets/dungeon_menu.png").convert()
            dungeon_bg = pygame.transform.smoothscale(dungeon_bg, (VIRTUAL_W, VIRTUAL_H))
            assets_cache['dungeon_bg'] = dungeon_bg
        except:
            dungeon_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            dungeon_bg.fill((20, 20, 40))
            assets_cache['dungeon_bg'] = dungeon_bg
        
        # Load navigation buttons
        try:
            prev_btn = pygame.image.load("assets/previous.png").convert_alpha()
            prev_btn = pygame.transform.scale(prev_btn, (50, 50))
            assets_cache['prev_btn'] = prev_btn
        except:
            assets_cache['prev_btn'] = None
        
        try:
            next_btn = pygame.image.load("assets/next.png").convert_alpha()
            next_btn = pygame.transform.scale(next_btn, (50, 50))
            assets_cache['next_btn'] = next_btn
        except:
            assets_cache['next_btn'] = None
        
        # Load coming soon image
        try:
            coming_soon_img = pygame.image.load("assets/comingsoon.png").convert_alpha()
            coming_soon_img = pygame.transform.scale(coming_soon_img, (120, 120))
            assets_cache['coming_soon_img'] = coming_soon_img
        except:
            assets_cache['coming_soon_img'] = None
        
        # Load feather icon
        try:
            feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
            feather_icon = pygame.transform.scale(feather_icon, (40, 40))
            assets_cache['feather_icon'] = feather_icon
        except:
            assets_cache['feather_icon'] = None
        
        # Pre-load and optimize boss animations
        boss_animations = {}
        boss_info = {
            "karasu": ("Dungeons/Karasu_tengu", "Karasu Tengu"),
            "fire_worm": ("Dungeons/Fire_worm", "Fire Worm"),
            "flying_demon": ("Dungeons/Flying_demon", "Flying Demon"),
            "skeleton": ("Dungeons/Skeleton", "Skeleton")
        }
        
        frame_counts = {
            "karasu": 6, "fire_worm": 9, "flying_demon": 4, "skeleton": 4
        }
        
        for boss_key, (path, name) in boss_info.items():
            try:
                idle_sheet = pygame.image.load(f"assets/{path}/Idle.png").convert_alpha()
                sheet_width = idle_sheet.get_width()
                frame_width = sheet_width // frame_counts[boss_key]
                frame_height = idle_sheet.get_height()
                
                # Pre-extract and convert all frames for better performance
                frames = []
                for i in range(frame_counts[boss_key]):
                    frame_rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA).convert_alpha()
                    frame.blit(idle_sheet, (0, 0), frame_rect)
                    scaled_frame = pygame.transform.scale(frame, (100, 100)).convert_alpha()
                    frames.append(scaled_frame)
                
                boss_animations[boss_key] = {
                    'frames': frames,
                    'frame_count': frame_counts[boss_key],
                    'current_frame': 0,
                    'animation_timer': 0,
                    'animation_speed': 150
                }
            except:
                boss_animations[boss_key] = None
        
        # Pre-render static text elements
        static_texts = {}
        
        # Define dungeon layouts for each page
        dungeons_page1 = [
            {"type": "karasu", "name": "Karasu Tengu", "available": True},
            {"type": "fire_worm", "name": "Fire Worm", "available": True},
            {"type": "flying_demon", "name": "Flying Demon", "available": True}
        ]
        
        dungeons_page2 = [
            {"type": "skeleton", "name": "Skeleton", "available": True},
            {"type": "empty", "name": "Not Available", "available": False},
            {"type": "empty", "name": "Not Available", "available": False}
        ]
        
        current_page = 0
        pages = [dungeons_page1, dungeons_page2]
        
        # Pre-calculate positions (moved down by 50 pixels)
        dungeon_rects = [
            pygame.Rect(100, 250, 180, 200),  # Changed from 200 to 250
            pygame.Rect(320, 250, 180, 200),  # Changed from 200 to 250
            pygame.Rect(540, 250, 180, 200),  # Changed from 200 to 250
        ]
        
        nav_y = VIRTUAL_H - 70
        button_spacing = 150
        center_x = VIRTUAL_W // 2
        
        prev_rect = pygame.Rect(center_x - button_spacing, nav_y, 60, 60)
        next_rect = pygame.Rect(center_x + button_spacing - 60, nav_y, 60, 60)
        inventory_button = pygame.Rect(50, 50, 120, 50)
        back_button = pygame.Rect(VIRTUAL_W - 100, 50, 80, 50)
        
        # State variables
        selected_dungeon = None
        battle_button = None
        not_available_timer = 0
        last_frame_time = pygame.time.get_ticks()
        
        # Pre-render commonly used texts
        def update_static_texts():
            static_texts['page'] = small_font.render(f"Page {current_page + 1}/{len(pages)}", True, WHITE)
            static_texts['inventory'] = small_font.render("Inventory", True, WHITE)
            static_texts['back'] = small_font.render("Back", True, WHITE)
            static_texts['battle'] = button_font.render("BATTLE", True, WHITE)
            static_texts['not_available'] = small_font.render("Not Available", True, (150, 150, 150))
            static_texts['battles_used'] = small_font.render("BATTLES USED", True, RED)
            static_texts['no_stamina'] = small_font.render("NO STAMINA", True, RED)
            static_texts['nav_prev'] = small_font.render("<", True, WHITE)
            static_texts['nav_next'] = small_font.render(">", True, WHITE)
        
        update_static_texts()
        
        while True:
            current_time = pygame.time.get_ticks()
            delta_time = current_time - last_frame_time
            last_frame_time = current_time
            
            # Only update animations every few frames to reduce CPU load
            if delta_time >= 16:  # Cap at ~60 FPS
                for boss_key, animation in boss_animations.items():
                    if animation and current_time - animation['animation_timer'] >= animation['animation_speed']:
                        animation['current_frame'] = (animation['current_frame'] + 1) % animation['frame_count']
                        animation['animation_timer'] = current_time
            
            # Efficient input handling
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Navigation buttons
                    if prev_rect.collidepoint((vmx, vmy)) and current_page > 0:
                        current_page -= 1
                        selected_dungeon = None
                        battle_button = None
                        update_static_texts()
                    elif next_rect.collidepoint((vmx, vmy)) and current_page < len(pages) - 1:
                        current_page += 1
                        selected_dungeon = None
                        battle_button = None
                        update_static_texts()
                    
                    # Dungeon selection
                    else:
                        current_dungeons = pages[current_page]
                        for i, dungeon in enumerate(current_dungeons):
                            if i < len(dungeon_rects) and dungeon_rects[i].collidepoint((vmx, vmy)):
                                if dungeon["available"] and dungeon["type"] != "empty":
                                    if dungeon_data["battle_count"] < 10 and dungeon_data["stamina"] >= 20:
                                        selected_dungeon = dungeon["type"]
                                        battle_button = pygame.Rect(dungeon_rects[i].x, dungeon_rects[i].bottom + 10, dungeon_rects[i].width, 50)
                                elif not dungeon["available"] or dungeon["type"] == "empty":
                                    not_available_timer = current_time
                                break
                        
                        # Battle button
                        if battle_button and battle_button.collidepoint((vmx, vmy)) and selected_dungeon:
                            return boss_difficulty_screen(selected_dungeon)
                        
                        # Other buttons
                        elif inventory_button.collidepoint((vmx, vmy)):
                            show_inventory(dungeon_data)
                        elif back_button.collidepoint((vmx, vmy)):
                            return "back"
            
            # Fast rendering - use cached surfaces
            virtual_surface.blit(assets_cache['dungeon_bg'], (0, 0))
            
            # Draw title with rainbow effect (optimize if needed)
            title_text = title_font.render("DUNGEON", True, get_rainbow_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
            
            # Draw pre-rendered page indicator
            virtual_surface.blit(static_texts['page'], (VIRTUAL_W // 2 - static_texts['page'].get_width() // 2, 120))
            
            # Efficient battle/stamina info rendering
            battles_left = 10 - dungeon_data["battle_count"]
            if battles_left > 0:
                battle_text = small_font.render(f"Battles Left: {battles_left}/10", True, WHITE)
            else:
                next_reset = last_reset + timedelta(hours=5)
                time_left = next_reset - datetime.now()
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                
                battle_text = small_font.render(f"Reset in: {hours_left}h {minutes_left}m", True, RED)
            
            virtual_surface.blit(battle_text, (20, 140))
            
            # Draw stamina info
            stamina_text = small_font.render(f"Stamina: {dungeon_data['stamina']}/100", True, WHITE)
            virtual_surface.blit(stamina_text, (20, 160))
            
            # Calculate next stamina regen time (only if stamina < 100)
            if dungeon_data['stamina'] < 100:
                last_regen = datetime.fromisoformat(dungeon_data["last_stamina_regen"])
                next_regen = last_regen + timedelta(minutes=10)
                time_to_regen = next_regen - datetime.now()
                if time_to_regen.total_seconds() > 0:
                    minutes_left = int(time_to_regen.total_seconds() // 60)
                    seconds_left = int(time_to_regen.total_seconds() % 60)
                    regen_text = small_font.render(f"Next regen: {minutes_left}m {seconds_left}s", True, (150, 150, 255))
                    virtual_surface.blit(regen_text, (20, 180))
            
            # Draw feather count
            feather_text = small_font.render(f"Tengu Feathers: {dungeon_data['tengu_feathers']}", True, WHITE)
            virtual_surface.blit(feather_text, (500, 140))
            if assets_cache['feather_icon']:
                virtual_surface.blit(assets_cache['feather_icon'], (680, 135))
            
            # Efficient dungeon rendering
            current_dungeons = pages[current_page]
            for i, dungeon in enumerate(current_dungeons):
                if i >= len(dungeon_rects):
                    continue
                    
                rect = dungeon_rects[i]
                can_battle = (dungeon_data["battle_count"] < 10 and 
                             dungeon_data["stamina"] >= 20 and 
                             dungeon["available"] and 
                             dungeon["type"] != "empty")
                
                # Determine color once
                if dungeon["type"] == "empty" or not dungeon["available"]:
                    color = (60, 60, 60)
                elif can_battle:
                    if selected_dungeon == dungeon["type"]:
                        color = SELECTED_COLOR
                    elif rect.collidepoint((vmx, vmy)):
                        color = HOVER_COLOR
                    else:
                        color = BUTTON_COLOR
                else:
                    color = (100, 100, 100)
                
                # Fast rectangle drawing
                pygame.draw.rect(virtual_surface, color, rect, border_radius=10)
                
                # Content rendering based on type
                if dungeon["type"] == "empty" or not dungeon["available"]:
                    # Draw coming soon image
                    if assets_cache['coming_soon_img']:
                        img_rect = assets_cache['coming_soon_img'].get_rect(center=(rect.centerx, rect.centery - 10))
                        virtual_surface.blit(assets_cache['coming_soon_img'], img_rect)
                    
                    # Draw pre-rendered "Not Available" text
                    text_rect = static_texts['not_available'].get_rect(center=(rect.centerx, rect.bottom - 20))
                    virtual_surface.blit(static_texts['not_available'], text_rect)
                else:
                    # Draw animated boss sprite
                    animation = boss_animations.get(dungeon["type"])
                    if animation and animation['frames']:
                        current_frame = animation['frames'][animation['current_frame']]
                        sprite_rect = current_frame.get_rect(center=(rect.centerx, rect.centery - 30))
                        virtual_surface.blit(current_frame, sprite_rect)
                    
                    # Draw dungeon name (cache if possible)
                    name_key = f"name_{dungeon['type']}"
                    if name_key not in static_texts:
                        static_texts[name_key] = small_font.render(dungeon["name"], True, WHITE)
                    
                    name_rect = static_texts[name_key].get_rect(center=(rect.centerx, rect.bottom - 30))
                    virtual_surface.blit(static_texts[name_key], name_rect)
                    
                    # Draw status for unavailable dungeons
                    if not can_battle:
                        if dungeon_data["battle_count"] >= 10:
                            status_rect = static_texts['battles_used'].get_rect(center=(rect.centerx, rect.bottom - 10))
                            virtual_surface.blit(static_texts['battles_used'], status_rect)
                        else:
                            status_rect = static_texts['no_stamina'].get_rect(center=(rect.centerx, rect.bottom - 10))
                            virtual_surface.blit(static_texts['no_stamina'], status_rect)
            
            # Draw battle button if selected
            if battle_button and selected_dungeon:
                battle_color = HOVER_COLOR if battle_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, battle_color, battle_button, border_radius=8)
                battle_rect = static_texts['battle'].get_rect(center=battle_button.center)
                virtual_surface.blit(static_texts['battle'], battle_rect)
            
            # Efficient navigation button rendering
            if current_page > 0:
                if assets_cache['prev_btn']:
                    virtual_surface.blit(assets_cache['prev_btn'], prev_rect)
                else:
                    nav_color = HOVER_COLOR if prev_rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
                    pygame.draw.rect(virtual_surface, nav_color, prev_rect, border_radius=25)
                    prev_text_rect = static_texts['nav_prev'].get_rect(center=prev_rect.center)
                    virtual_surface.blit(static_texts['nav_prev'], prev_text_rect)
            
            if current_page < len(pages) - 1:
                if assets_cache['next_btn']:
                    virtual_surface.blit(assets_cache['next_btn'], next_rect)
                else:
                    nav_color = HOVER_COLOR if next_rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
                    pygame.draw.rect(virtual_surface, nav_color, next_rect, border_radius=25)
                    next_text_rect = static_texts['nav_next'].get_rect(center=next_rect.center)
                    virtual_surface.blit(static_texts['nav_next'], next_text_rect)
            
            # Show "Not Available" message with timer
            if not_available_timer > 0 and current_time - not_available_timer < 2000:
                not_available_popup = button_font.render("Not Available", True, RED)
                virtual_surface.blit(not_available_popup, not_available_popup.get_rect(center=(VIRTUAL_W // 2, 600)))
            
            # Draw other buttons with hover effects
            inv_color = HOVER_COLOR if inventory_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, inv_color, inventory_button, border_radius=8)
            inv_rect = static_texts['inventory'].get_rect(center=inventory_button.center)
            virtual_surface.blit(static_texts['inventory'], inv_rect)
            
            back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=8)
            back_rect = static_texts['back'].get_rect(center=back_button.center)
            virtual_surface.blit(static_texts['back'], back_rect)
            
            # Final render
            draw_scaled_centered()
            clock.tick(60)
    
    def boss_difficulty_screen(boss_type):
        """Difficulty selection for any boss"""
        difficulties = ["Easy", "Medium", "Hard"]
        difficulty_rects = {}
        
        for i, diff in enumerate(difficulties):
            x = 150 + i * 200
            y = 250
            difficulty_rects[diff] = pygame.Rect(x, y, 180, 120)
        
        back_button = pygame.Rect(50, 50, 80, 50)
        
        # Boss stats for display
        boss_stats = {
            "karasu": {
                "Easy": {"hp": "250 HP", "reward": "1-2 Feathers"},
                "Medium": {"hp": "500 HP", "reward": "2-4 Feathers"},
                "Hard": {"hp": "1000 HP", "reward": "4-5 Feathers"}
            },
            "fire_worm": {
                "Easy": {"hp": "400 HP", "reward": "1 Feathers (50%)"},
                "Medium": {"hp": "800 HP", "reward": "2-4 Feathers (25%)"},
                "Hard": {"hp": "1600 HP", "reward": "5-8 Feathers (10%)"}
            },
            "flying_demon": {
                "Easy": {"hp": "250 HP", "reward": "1 Feathers (15%)"},
                "Medium": {"hp": "500 HP", "reward": "1-2 Feathers (30%)"},
                "Hard": {"hp": "1000 HP", "reward": "2-4 Feathers (50%)"}
            },
            "skeleton": {
                "Easy": {"hp": "1200 HP", "reward": "2-4 Feathers (15%)"},
                "Medium": {"hp": "2500 HP", "reward": "4-6 Feathers (30%)"},
                "Hard": {"hp": "5000 HP", "reward": "6-8 Feathers (40%)"}
            }
        }
        
        boss_names = {
            "karasu": "Karasu Tengu",
            "fire_worm": "Fire Worm",
            "flying_demon": "Flying Demon", 
            "skeleton": "Skeleton"
        }
        
        while True:
            virtual_surface.fill((30, 30, 60))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for diff, rect in difficulty_rects.items():
                        if rect.collidepoint((vmx, vmy)):
                            selected_character = character_selection_screen()
                            if selected_character:
                                return boss_battle(boss_type, diff, selected_character)
                    if back_button.collidepoint((vmx, vmy)):
                        return
            
            # Draw title
            title_text = title_font.render(f"Select Difficulty - {boss_names[boss_type]}", True, get_rainbow_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 120)))
            
            # Draw stamina cost warning
            stamina_warning = button_font.render("Battle Cost: 20 Stamina", True, (255, 255, 0))
            virtual_surface.blit(stamina_warning, stamina_warning.get_rect(center=(VIRTUAL_W // 2, 170)))
            
            # Draw difficulty options
            for diff, rect in difficulty_rects.items():
                color = HOVER_COLOR if rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, color, rect, border_radius=10)
                
                diff_text = button_font.render(diff, True, WHITE)
                virtual_surface.blit(diff_text, diff_text.get_rect(center=(rect.centerx, rect.y + 25)))
                
                hp_text = small_font.render(boss_stats[boss_type][diff]["hp"], True, WHITE)
                virtual_surface.blit(hp_text, hp_text.get_rect(center=(rect.centerx, rect.y + 55)))
                
                reward_text = small_font.render(boss_stats[boss_type][diff]["reward"], True, WHITE)
                virtual_surface.blit(reward_text, reward_text.get_rect(center=(rect.centerx, rect.y + 80)))
                
                # Add special effect descriptions
                if boss_type == "fire_worm":
                    effect_text = small_font.render("Burning Effect", True, (255, 100, 0))
                    virtual_surface.blit(effect_text, effect_text.get_rect(center=(rect.centerx, rect.y + 100)))
                elif boss_type == "flying_demon":
                    effect_text = small_font.render("Bloodsteal", True, (200, 0, 0))
                    virtual_surface.blit(effect_text, effect_text.get_rect(center=(rect.centerx, rect.y + 100)))
                elif boss_type == "skeleton":
                    effect_text = small_font.render("Cutless Effect", True, (150, 150, 0))
                    virtual_surface.blit(effect_text, effect_text.get_rect(center=(rect.centerx, rect.y + 100)))
            
            # Draw back button
            pygame.draw.rect(virtual_surface, HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR, back_button, border_radius=8)
            back_text = small_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
            
            draw_scaled_centered()
            clock.tick(60)
                   
    def show_inventory(data):
        """Show inventory screen"""
        inventory_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        inventory_bg.fill((20, 30, 50))
        
        # Button positioning with proper spacing
        close_button = pygame.Rect(VIRTUAL_W - 120, 30, 90, 50)
        
        try:
            feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
            feather_icon = pygame.transform.scale(feather_icon, (80, 80))  # Made slightly bigger
        except:
            feather_icon = None
        
        while True:
            virtual_surface.blit(inventory_bg, (0, 0))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if close_button.collidepoint((vmx, vmy)):
                        return
            
            # Draw title with proper spacing from top
            title_text = title_font.render("INVENTORY", True, get_rainbow_color())
            title_rect = title_text.get_rect(center=(VIRTUAL_W // 2, 60))
            virtual_surface.blit(title_text, title_rect)
            
            # Draw subtitle/description
            subtitle_text = small_font.render("Collected items from dungeon battles", True, (200, 200, 200))
            subtitle_rect = subtitle_text.get_rect(center=(VIRTUAL_W // 2, 95))
            virtual_surface.blit(subtitle_text, subtitle_rect)
            
            # Main inventory container with better spacing
            container_rect = pygame.Rect(50, 130, VIRTUAL_W - 100, VIRTUAL_H - 180)
            pygame.draw.rect(virtual_surface, (30, 40, 70), container_rect, border_radius=15)
            pygame.draw.rect(virtual_surface, (100, 100, 150), container_rect, width=2, border_radius=15)
            
            # Item section - Tengu Feather
            item_y_start = 160
            item_rect = pygame.Rect(80, item_y_start, VIRTUAL_W - 160, 120)
            
            # Item background with hover effect
            item_hover = item_rect.collidepoint((vmx, vmy))
            item_color = (60, 70, 120) if item_hover else (50, 60, 110)
            pygame.draw.rect(virtual_surface, item_color, item_rect, border_radius=12)
            pygame.draw.rect(virtual_surface, (120, 120, 180), item_rect, width=2, border_radius=12)
            
            # Item icon with proper positioning
            icon_x = item_rect.x + 20
            icon_y = item_rect.y + 20
            
            if feather_icon:
                # Icon background circle
                icon_center = (icon_x + 40, icon_y + 40)
                pygame.draw.circle(virtual_surface, (70, 80, 130), icon_center, 45)
                pygame.draw.circle(virtual_surface, (150, 150, 200), icon_center, 45, 2)
                virtual_surface.blit(feather_icon, (icon_x, icon_y))
            
            # Item information with better spacing
            info_x = icon_x + 100
            info_y = item_rect.y + 15
            
            # Item name (larger, more prominent)
            item_name = button_font.render("Tengu Feather", True, (255, 255, 255))
            virtual_surface.blit(item_name, (info_x, info_y))
            
            # Rarity indicator (without emoji)
            rarity_text = small_font.render("RARE MATERIAL", True, (255, 215, 0))
            virtual_surface.blit(rarity_text, (info_x, info_y + 30))
            
            # Item description with line breaks
            desc_y = info_y + 55
            item_desc1 = small_font.render("The white-brown fur of a powerful monster,", True, (220, 220, 220))
            virtual_surface.blit(item_desc1, (info_x, desc_y))
            
            item_desc2 = small_font.render("Karasu Tengu. You're lucky to get it!", True, (220, 220, 220))
            virtual_surface.blit(item_desc2, (info_x, desc_y + 20))
            
            # Usage information
            item_use = small_font.render("Used for: Material for shop crafting", True, (150, 255, 150))
            virtual_surface.blit(item_use, (info_x, desc_y + 45))
            
            # Quantity display (right side with better styling)
            quantity_bg_rect = pygame.Rect(item_rect.right - 120, item_rect.y + 30, 100, 60)
            pygame.draw.rect(virtual_surface, (80, 90, 140), quantity_bg_rect, border_radius=8)
            pygame.draw.rect(virtual_surface, (180, 180, 220), quantity_bg_rect, width=2, border_radius=8)
            
            quantity_label = small_font.render("Owned:", True, (200, 200, 200))
            quantity_label_rect = quantity_label.get_rect(center=(quantity_bg_rect.centerx, quantity_bg_rect.y + 15))
            virtual_surface.blit(quantity_label, quantity_label_rect)
            
            quantity_text = button_font.render(f"{data['tengu_feathers']}", True, (255, 255, 100))
            quantity_rect = quantity_text.get_rect(center=(quantity_bg_rect.centerx, quantity_bg_rect.y + 40))
            virtual_surface.blit(quantity_text, quantity_rect)
            
            # Empty slots placeholder for future items
            empty_slot_y = item_y_start + 140
            for i in range(2):
                slot_rect = pygame.Rect(80, empty_slot_y + (i * 90), VIRTUAL_W - 160, 80)
                pygame.draw.rect(virtual_surface, (30, 35, 60), slot_rect, border_radius=10)
                pygame.draw.rect(virtual_surface, (80, 80, 120), slot_rect, width=1, border_radius=10)
                
                # Empty slot icon
                empty_icon_center = (slot_rect.x + 50, slot_rect.centery)
                pygame.draw.circle(virtual_surface, (40, 45, 70), empty_icon_center, 25)
                pygame.draw.circle(virtual_surface, (100, 100, 140), empty_icon_center, 25, 2)
                
                # Empty slot text
                empty_text = small_font.render("Empty Slot", True, (120, 120, 140))
                virtual_surface.blit(empty_text, (slot_rect.x + 90, slot_rect.centery - 10))
            
            # Draw close button with better styling
            close_hover = close_button.collidepoint((vmx, vmy))
            close_color = (200, 80, 80) if close_hover else (150, 60, 60)
            pygame.draw.rect(virtual_surface, close_color, close_button, border_radius=10)
            pygame.draw.rect(virtual_surface, (255, 255, 255), close_button, width=2, border_radius=10)
            
            close_text = button_font.render("CLOSE", True, WHITE)
            close_rect = close_text.get_rect(center=close_button.center)
            virtual_surface.blit(close_text, close_rect)
            
            draw_scaled_centered()
            clock.tick(60)

    def boss_battle(boss_type, difficulty, selected_character):
        """Main battle function against any boss"""
        # Consume stamina before battle
        dungeon_data["stamina"] -= 20
        save_dungeon_data(dungeon_data)
        
        # Load battle music
        try:
            pygame.mixer.music.load("assets/dungeonbg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading dungeon music: {e}")
        
        # Load battle background
        try:
            battle_bg = pygame.image.load("assets/dungeonbg.png").convert()
            battle_bg = pygame.transform.smoothscale(battle_bg, (VIRTUAL_W, VIRTUAL_H))
        except:
            battle_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
            battle_bg.fill((40, 20, 20))
        
        # Player setup
        PLAYER_MAX_HP = 100
        PLAYER_MAX_MP = 100
        hp = PLAYER_MAX_HP
        mp = PLAYER_MAX_MP
        last_mp_regen = pygame.time.get_ticks()
        last_heal_time = 0
        is_shielding = False
        is_dead = False
        is_hurt = False
        hurt_timer = 0
        death_animation_complete = False
        last_attack_time = 0
        
        # Status effects
        burning_timer = 0
        burning_damage = 0
        cutless_timer = 0
        cutless_damage = 0
        
        # Load player animations
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
        anims = load_animation_frames(selected_character, actions, character_frame_counts[selected_character])
        
        frame_delays = {
            "Idle": 160, "Run": 100, "Jump": 120, "Shield": 170,
            "Attack_1": 110, "Attack_2": 115, "Attack_3": 120,
            "Dead": 170, "Hurt": 170
        }
        
        # Player state
        action = "Idle"
        idx, timer = 0, 0
        pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]
        vel = [0, 0]
        jumping = False
        jump_count = 2
        holding_shield = False
        
        # Create boss based on type
        if boss_type == "karasu":
            boss = KarasuTengu(difficulty)
        else:
            boss = Boss(boss_type, difficulty)
        
        # UI setup
        size = 50
        spacing = 8
        dir_center_x = 80
        dir_center_y = VIRTUAL_H - 200
        
        left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
        right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
        up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
        down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)
        
        # Action buttons
        btn_w, btn_h = 70, 50
        action_y = VIRTUAL_H - btn_h - 10
        action_buttons = {
            "atk1": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 7, action_y, btn_w, btn_h),
            "atk2": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 6, action_y, btn_w, btn_h),
            "atk3": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 5, action_y, btn_w, btn_h),
            "jump": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 4, action_y, btn_w, btn_h),
            "shield": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 3, action_y, btn_w, btn_h),
            "run": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 2, action_y, btn_w, btn_h),
            "heal": pygame.Rect(VIRTUAL_W - (btn_w + spacing), action_y, btn_w, btn_h),
        }
        
        pause_button = pygame.Rect(VIRTUAL_W - 50, 10, 40, 40)
        
        def check_collision_and_damage():
            nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
            nonlocal burning_timer, burning_damage, cutless_timer, cutless_damage
            
            # Check if boss is attacking and close enough to player
            if boss.is_attacking():
                distance = abs(boss.pos[0] - pos[0])
                if distance < boss.attack_range:
                    current_time = pygame.time.get_ticks()
                    if current_time - boss.last_attack_time > 600:
                        damage = boss.get_attack_damage()
                        
                        # Shield blocks 100% damage
                        if is_shielding:
                            damage = 0
                        
                        if damage > 0:
                            # Apply special effects
                            if boss_type == "fire_worm":
                                burning_timer = current_time + 5000  # 5 seconds
                                burning_damage = 15
                            elif boss_type == "flying_demon":
                                # Bloodsteal - boss heals
                                if random.random() < 0.5:  # 50% chance
                                    boss.hp = min(boss.max_hp, boss.hp + 20)
                            elif boss_type == "skeleton":
                                # Cutless effect - additional damage over time
                                cutless_timer = current_time + 3000  # 3 seconds
                                cutless_damage = 8
                                damage += cutless_damage  # Additional immediate damage
                            
                            hp -= damage
                            boss.last_attack_time = current_time
                            
                            if hp <= 0:
                                hp = 0
                                is_dead = True
                                action = "Dead"
                                idx = 0
                                timer = 0
                            else:
                                is_hurt = True
                                hurt_timer = pygame.time.get_ticks()
                                action = "Hurt"
                                idx = 0
                                timer = 0
            
            # Check if player is attacking and close enough to boss
            if "Attack" in action and idx > 0:
                distance = abs(pos[0] - boss.pos[0])
                player_range = character_ranges[selected_character]
                
                if distance < player_range:
                    current_time = pygame.time.get_ticks()
                    if current_time - last_attack_time > 400:
                        damage = character_damage[selected_character][action]
                        if boss.take_damage(damage):
                            last_attack_time = current_time
        
        def update_status_effects():
            nonlocal hp, burning_timer, burning_damage, cutless_timer, cutless_damage
            current_time = pygame.time.get_ticks()
            
            # Burning effect
            if burning_timer > 0 and current_time < burning_timer:
                if current_time % 1000 < 50:  # Tick damage every second
                    hp = max(0, hp - burning_damage)
                    if hp <= 0:
                        return True  # Player died
            elif burning_timer > 0:
                burning_timer = 0
                burning_damage = 0
            
            # Cutless effect
            if cutless_timer > 0 and current_time < cutless_timer:
                if current_time % 500 < 50:  # Tick damage every 0.5 seconds
                    hp = max(0, hp - cutless_damage)
                    if hp <= 0:
                        return True  # Player died
            elif cutless_timer > 0:
                cutless_timer = 0
                cutless_damage = 0
            
            return False
        
        def draw_battle_hud():
            # Player HUD
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), (10, 10, 220, 140), border_radius=8)
            
            # HP bar
            pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 180, 12))
            pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, int(hp * 1.8), 12))
            
            # MP bar
            pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 180, 12))
            pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, int(mp * 1.8), 12))
            
            # Labels
            hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
            virtual_surface.blit(hp_text, (15, 52))
            mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
            virtual_surface.blit(mp_text, (15, 67))
            name_text = small_font.render(f"{selected_character}", True, WHITE)
            virtual_surface.blit(name_text, (15, 82))
            
            # Heal cooldown indicator
            current_time = pygame.time.get_ticks()
            heal_cooldown_remaining = max(0, 2000 - (current_time - last_heal_time))
            if heal_cooldown_remaining > 0:
                cooldown_text = small_font.render(f"Heal: {heal_cooldown_remaining//1000 + 1}s", True, RED)
                virtual_surface.blit(cooldown_text, (15, 97))
            
            # Status effects
            status_y = 112
            if burning_timer > 0:
                burn_text = small_font.render("BURNING", True, (255, 100, 0))
                virtual_surface.blit(burn_text, (15, status_y))
                status_y += 15
            
            if cutless_timer > 0:
                cut_text = small_font.render("CUTLESS", True, (255, 255, 0))
                virtual_surface.blit(cut_text, (15, status_y))
        
        # Movement speeds
        move_speed = 8
        run_speed = 12
        
        # Main battle loop
        while True:
            dt = clock.tick(60)
            timer += dt
            now = pygame.time.get_ticks()
            
            # Update status effects
            if update_status_effects():
                if not is_dead:
                    is_dead = True
                    action = "Dead"
                    idx = 0
                    timer = 0
            
            # Check for game over conditions
            if is_dead and death_animation_complete:
                dungeon_data["battle_count"] += 1
                save_dungeon_data(dungeon_data)
                pygame.mixer.music.stop()
                return show_battle_result(False, boss_type, difficulty, 0)
            
            if boss.is_dead and boss.death_animation_complete:
                dungeon_data["battle_count"] += 1
                
                # Calculate feather drops based on boss type
                feathers_gained = calculate_feather_drops(boss_type, difficulty)
                
                dungeon_data["tengu_feathers"] += feathers_gained
                save_dungeon_data(dungeon_data)
                pygame.mixer.music.stop()
                return show_battle_result(True, boss_type, difficulty, feathers_gained)
            
            # MP regeneration
            if now - last_mp_regen > 2000:
                mp = min(PLAYER_MAX_MP, mp + 15)
                last_mp_regen = now
            
            # Handle hurt state
            if is_hurt and now - hurt_timer > 600:
                is_hurt = False
                if not is_dead:
                    action = "Idle"
                    idx = 0
                    timer = 0
            
            # Event handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    exit_game()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    return "back"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    mx, my = ((mx - ox) / scale, (my - oy) / scale)
                    
                    if pause_button.collidepoint((mx, my)):
                        pygame.mixer.music.stop()
                        return "back"
                    
                    # Don't allow actions if dead or hurt
                    if is_dead or is_hurt:
                        continue
                    
                    # Movement controls
                    if left.collidepoint((mx, my)):
                        vel[0] = -move_speed
                        action = "Run"
                        is_shielding = False
                    elif right.collidepoint((mx, my)):
                        vel[0] = move_speed
                        action = "Run"
                        is_shielding = False
                    elif up.collidepoint((mx, my)):
                        vel[1] = -move_speed
                        action = "Run"
                        is_shielding = False
                    elif down.collidepoint((mx, my)):
                        vel[1] = move_speed
                        action = "Run"
                        is_shielding = False
                    
                    # Action buttons
                    elif action_buttons["atk1"].collidepoint((mx, my)):
                        if mp >= 5:
                            action = "Attack_1"
                            idx = 0
                            timer = 0
                            mp -= 5
                            is_shielding = False
                    elif action_buttons["atk2"].collidepoint((mx, my)):
                        if mp >= 8:
                            action = "Attack_2"
                            idx = 0
                            timer = 0
                            mp -= 8
                            is_shielding = False
                    elif action_buttons["atk3"].collidepoint((mx, my)):
                        if mp >= 12:
                            action = "Attack_3"
                            idx = 0
                            timer = 0
                            mp -= 12
                            is_shielding = False
                    elif action_buttons["jump"].collidepoint((mx, my)):
                        if jump_count > 0:
                            vel[1] = -12
                            action = "Jump"
                            jumping = True
                            jump_count -= 1
                            idx = 0
                            timer = 0
                            is_shielding = False
                    elif action_buttons["shield"].collidepoint((mx, my)):
                        holding_shield = True
                        action = "Shield"
                        idx = 0
                        timer = 0
                        is_shielding = True
                    elif action_buttons["run"].collidepoint((mx, my)):
                        vel[0] = run_speed if pos[0] < boss.pos[0] else -run_speed
                        action = "Run"
                        is_shielding = False
                    elif action_buttons["heal"].collidepoint((mx, my)):
                        if now - last_heal_time > 2000:  # 2 second cooldown
                            hp = min(PLAYER_MAX_HP, hp + 50)
                            last_heal_time = now
                
                if e.type == pygame.MOUSEBUTTONUP:
                    if not is_dead and not is_hurt:
                        vel = [0, 0]
                        holding_shield = False
                        is_shielding = False
                        if not jumping:
                            action = "Idle"
            
            # Physics update
            if not is_dead:
                if jumping:
                    vel[1] += 0.6
                    pos[1] += vel[1]
                    if pos[1] >= VIRTUAL_H - 150:
                        pos[1] = VIRTUAL_H - 150
                        jumping = False
                        vel[1] = 0
                        jump_count = 2
                        if not is_hurt:
                            action = "Idle"
                else:
                    pos[0] += vel[0]
                    pos[1] += vel[1]
                
                # Screen bounds
                sprite_width, sprite_height = 160, 160
                left_limit = sprite_width // 2
                right_limit = VIRTUAL_W - sprite_width // 2
                top_limit = 50
                bottom_limit = VIRTUAL_H - sprite_height
                
                pos[0] = max(left_limit, min(right_limit, pos[0]))
                pos[1] = max(top_limit, min(bottom_limit, pos[1]))
            
            # Update boss
            boss.update(dt, pos)
            
            # Check combat interactions
            check_collision_and_damage()
            
            # Update player animation
            delay = frame_delays.get(action, 130)
            if timer >= delay:
                timer = 0
                if anims[action]:
                    idx += 1
                    if idx >= len(anims[action]):
                        if action == "Dead":
                            death_animation_complete = True
                            idx = len(anims["Dead"]) - 1
                        elif "Attack" in action or action == "Jump":
                            if not is_hurt and not is_dead:
                                action = "Idle"
                                idx = 0
                        elif action == "Shield" and holding_shield:
                            idx = len(anims["Shield"]) - 1
                        elif action == "Hurt":
                            idx = len(anims["Hurt"]) - 1
                        else:
                            if not is_hurt and not is_dead:
                                action = "Idle"
                                idx = 0
            
            # Drawing
            virtual_surface.blit(battle_bg, (0, 0))
            
            # Draw player
            if anims[action]:
                frame_idx = min(idx, len(anims[action]) - 1)
                sprite = pygame.transform.scale(anims[action][frame_idx], (160, 160))
                rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                virtual_surface.blit(sprite, rect.topleft)
                
                # Shield indicator for player
                if is_shielding:
                    shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                    shield_rect = shield_text.get_rect(center=(pos[0], pos[1] - 100))
                    virtual_surface.blit(shield_text, shield_rect)
            
            # Draw boss
            boss.draw(virtual_surface)
            
            # Draw UI elements only if not dead
            if not is_dead:
                # Movement buttons
                for button, symbol in [(left, "<"), (right, ">"), (up, "^"), (down, "v")]:
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, button, border_radius=8)
                    txt = small_font.render(symbol, True, WHITE)
                    virtual_surface.blit(txt, txt.get_rect(center=button.center))
                
                # Action buttons with MP cost indicators
                mp_costs = {"atk1": 5, "atk2": 8, "atk3": 12, "jump": 0, "shield": 0, "run": 0, "heal": 0}
                button_labels = {"atk1": "Atk1", "atk2": "Atk2", "atk3": "Atk3", "jump": "Jump", "shield": "Shield", "run": "Run", "heal": "Heal"}
                
                for btn_name, rect in action_buttons.items():
                    cost = mp_costs[btn_name]
                    if btn_name == "heal":
                        can_use = now - last_heal_time > 2000
                        color = BUTTON_COLOR if can_use else (100, 100, 100)
                    else:
                        can_use = mp >= cost
                        color = BUTTON_COLOR if can_use else (100, 100, 100)
                    
                    pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
                    txt = small_font.render(button_labels[btn_name], True, WHITE)
                    virtual_surface.blit(txt, txt.get_rect(center=rect.center))
            
            # Draw pause button
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, pause_button, border_radius=20)
            pause_text = small_font.render("X", True, WHITE)
            virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))
            
            # Draw HUD
            draw_battle_hud()
            
            # Draw battle info
            boss_names = {
                "karasu": "Karasu Tengu",
                "fire_worm": "Fire Worm",
                "flying_demon": "Flying Demon",
                "skeleton": "Skeleton"
            }
            battle_info = small_font.render(f"Battle: {selected_character} vs {boss_names[boss_type]} ({difficulty})", True, WHITE)
            virtual_surface.blit(battle_info, (VIRTUAL_W//2 - battle_info.get_width()//2, 10))
            
            draw_scaled_centered()
    
    def calculate_feather_drops(boss_type, difficulty):
        """Calculate feather drops based on boss type and difficulty"""
        drop_chances = {
            "karasu": {
                "Easy": (1, 2, 1.0),    # min, max, base_chance
                "Medium": (2, 4, 1.0),
                "Hard": (4, 5, 1.0)
            },
            "fire_worm": {
                "Easy": (1, 1, 0.5),    # 50% chance
                "Medium": (2, 4, 0.25), # 25% chance
                "Hard": (5, 8, 0.1)     # 10% chance
            },
            "flying_demon": {
                "Easy": (1, 1, 0.15),   # 15% chance
                "Medium": (1, 2, 0.30), # 30% chance
                "Hard": (2, 4, 0.50)    # 50% chance
            },
            "skeleton": {
                "Easy": (2, 4, 0.15),   # 15% chance
                "Medium": (4, 6, 0.30), # 30% chance
                "Hard": (6, 8, 0.40)    # 40% chance
            }
        }
        
        min_drop, max_drop, chance = drop_chances[boss_type][difficulty]
        
        # Check if player gets any drops
        if random.random() < chance:
            return random.randint(min_drop, max_drop)
        else:
            return 0  # No drops (zonk)
    
    def show_battle_result(victory, boss_type, difficulty, feathers_gained):
        """Show battle result screen"""
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        
        try:
            feather_icon = pygame.image.load("assets/Drops/tengu_feather.png").convert_alpha()
            feather_icon = pygame.transform.scale(feather_icon, (50, 50))
        except:
            feather_icon = None
        
        boss_names = {
            "karasu": "Karasu Tengu",
            "fire_worm": "Fire Worm",
            "flying_demon": "Flying Demon",
            "skeleton": "Skeleton"
        }
        
        buttons = {
            "continue": pygame.Rect(VIRTUAL_W//2 - 100, 450, 200, 60)
        }
        
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if buttons["continue"].collidepoint((vmx, vmy)):
                        return "continue"
            
            # Draw overlay
            virtual_surface.blit(overlay, (0, 0))
            
            # Draw result title
            if victory:
                add_battlepass_points()
                title_text = "VICTORY!"
                title_color = SELECTED_COLOR
                subtitle_text = f"{boss_names[boss_type]} ({difficulty}) Defeated!"
            else:
                title_text = "DEFEAT!"
                title_color = RED
                subtitle_text = f"You were defeated by {boss_names[boss_type]} ({difficulty})"
            
            result_title = title_font.render(title_text, True, title_color)
            virtual_surface.blit(result_title, result_title.get_rect(center=(VIRTUAL_W // 2, 150)))
            
            subtitle = button_font.render(subtitle_text, True, WHITE)
            virtual_surface.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 220)))
            
            # Show rewards or unlucky message
            if victory:
                if feathers_gained > 0:
                    reward_text = button_font.render("Rewards:", True, WHITE)
                    virtual_surface.blit(reward_text, reward_text.get_rect(center=(VIRTUAL_W // 2, 280)))
                    
                    if feather_icon:
                        virtual_surface.blit(feather_icon, (VIRTUAL_W // 2 - 80, 310))
                    
                    feather_text = button_font.render(f"Tengu Feather x{feathers_gained}", True, SELECTED_COLOR)
                    virtual_surface.blit(feather_text, feather_text.get_rect(center=(VIRTUAL_W // 2 + 20, 335)))
                else:
                    # Zonk message
                    unlucky_text = button_font.render("You're unlucky! Try to battle again", True, RED)
                    virtual_surface.blit(unlucky_text, unlucky_text.get_rect(center=(VIRTUAL_W // 2, 300)))
                    
                    no_drop_text = small_font.render("No items dropped this time!", True, WHITE)
                    virtual_surface.blit(no_drop_text, no_drop_text.get_rect(center=(VIRTUAL_W // 2, 330)))
            
            # Draw continue button
            color = HOVER_COLOR if buttons["continue"].collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, color, buttons["continue"], border_radius=10)
            
            continue_text = button_font.render("CONTINUE", True, WHITE)
            virtual_surface.blit(continue_text, continue_text.get_rect(center=buttons["continue"].center))
            
            draw_scaled_centered()
            clock.tick(30)
    
    # Legacy function for backward compatibility
    def karasu_difficulty_screen():
        """Legacy function that redirects to boss_difficulty_screen"""
        return boss_difficulty_screen("karasu")
    
    def karasu_battle(difficulty, selected_character):
        """Legacy function that redirects to boss_battle"""
        return boss_battle("karasu", difficulty, selected_character)
    
    # Main dungeon flow
    while True:
        result = dungeon_selection_screen()
        if result == "back":
            return
        elif result == "continue":
            continue
        else:
            # Handle any other results
            continue
            
def tournament():
    """Tournament mode: 1v1 battles for 3 rounds with lobby and shop system"""
    
    # Load tournament data
    def load_tournament_data():
        try:
            with open("tournament_data.json", "r") as f:
                return json.load(f)
        except:
            return {
                "stamina": 100,
                "last_stamina_regen": datetime.now().isoformat(),
                "coins": 0
            }
    
    def save_tournament_data(data):
        with open("tournament_data.json", "w") as f:
            json.dump(data, f)
    
    def load_summer_data():
        try:
            with open("summer_data.json", "r") as f:
                return json.load(f)
        except:
            return {"sakura": 0, "water": 0, "black_water": 0}
    
    def save_summer_data(data):
        with open("summer_data.json", "w") as f:
            json.dump(data, f)
    
    def load_dungeon_data():
        try:
            with open("dungeon_data.json", "r") as f:
                return json.load(f)
        except:
            return {"tengu_feathers": 0}
    
    def save_dungeon_data(data):
        with open("dungeon_data.json", "w") as f:
            json.dump(data, f)
    
    # Tournament shop function
    def tournament_shop():
        tournament_data = load_tournament_data()
        summer_data = load_summer_data()
        dungeon_data = load_dungeon_data()
        
        # Load and play background music
        try:
            pygame.mixer.music.load("assets/musicbg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Error loading background music: {e}")
        
        # Load background image
        try:
            shop_bg = pygame.image.load("assets/background.png").convert()
            shop_bg = pygame.transform.smoothscale(shop_bg, (VIRTUAL_W, VIRTUAL_H))
        except pygame.error as e:
            print(f"Error loading background image: {e}")
            shop_bg = None
        
        shop_page = 0
        max_pages = 2  # We have 2 pages now
        
        # Shop items divided into pages: [name, price, asset_path, data_key, data_file]
        shop_pages = [
            [  # Page 1
                ["Sakura", 1, "assets/Drops/sakura.png", "sakura", "summer"],
                ["Water", 1, "assets/Drops/water.png", "water", "summer"]
            ],
            [  # Page 2
                ["Black Water", 1, "assets/Drops/blackwater.png", "black_water", "summer"],
                ["Tengu Feather", 2, "assets/Drops/tengu_feather.png", "tengu_feathers", "dungeon"]
            ]
        ]
        
        while True:
            # Draw background
            if shop_bg:
                virtual_surface.blit(shop_bg, (0, 0))
            else:
                virtual_surface.fill((20, 30, 50))
            
            # Calculate mouse position
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            # Draw title (no icons)
            title_text = title_font.render("Tournament Shop", True, get_rainbow_color())
            virtual_surface.blit(title_text, title_text.get_rect(center=(VIRTUAL_W // 2, 80)))
            
            # Draw page indicator
            page_text = button_font.render(f"Page {shop_page + 1} of {max_pages}", True, WHITE)
            virtual_surface.blit(page_text, page_text.get_rect(center=(VIRTUAL_W // 2, 120)))
            
            # Draw navigation buttons
            prev_button = pygame.Rect(VIRTUAL_W // 2 - 200, 140, 100, 40)
            next_button = pygame.Rect(VIRTUAL_W // 2 + 100, 140, 100, 40)
            
            # Previous button
            prev_color = HOVER_COLOR if prev_button.collidepoint((vmx, vmy)) and shop_page > 0 else BUTTON_COLOR
            if shop_page == 0:
                prev_color = (100, 100, 100)
            pygame.draw.rect(virtual_surface, prev_color, prev_button, border_radius=8)
            prev_text = button_font.render("Previous", True, WHITE if shop_page > 0 else (160, 160, 160))
            virtual_surface.blit(prev_text, prev_text.get_rect(center=prev_button.center))
            
            # Next button
            next_color = HOVER_COLOR if next_button.collidepoint((vmx, vmy)) and shop_page < max_pages - 1 else BUTTON_COLOR
            if shop_page == max_pages - 1:
                next_color = (100, 100, 100)
            pygame.draw.rect(virtual_surface, next_color, next_button, border_radius=8)
            next_text = button_font.render("Next", True, WHITE if shop_page < max_pages - 1 else (160, 160, 160))
            virtual_surface.blit(next_text, next_text.get_rect(center=next_button.center))
            
            # Draw shop items for current page (2 items in a 1x2 grid)
            current_items = shop_pages[shop_page]
            start_x = VIRTUAL_W // 2 - 200
            start_y = 220
            
            item_boxes = []
            buy_buttons = []
            
            for i, item in enumerate(current_items):
                name, price, asset_path, data_key, data_file = item
                
                # Calculate position (2 items side by side)
                x = start_x + i * 220
                y = start_y
                
                # Item box
                item_box = pygame.Rect(x, y, 180, 160)
                item_boxes.append((item_box, i))
                
                # Draw item box
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, item_box, border_radius=15)
                pygame.draw.rect(virtual_surface, WHITE, item_box, 3, border_radius=15)
                
                # Draw item image
                try:
                    item_img = pygame.image.load(asset_path).convert_alpha()
                    item_img = pygame.transform.scale(item_img, (80, 80))
                    img_rect = item_img.get_rect(center=(x + 90, y + 50))
                    virtual_surface.blit(item_img, img_rect)
                except:
                    # Fallback if image not found
                    pygame.draw.rect(virtual_surface, (100, 100, 100), (x + 50, y + 10, 80, 80))
                    fallback_text = small_font.render("IMG", True, WHITE)
                    virtual_surface.blit(fallback_text, fallback_text.get_rect(center=(x + 90, y + 50)))
                
                # Draw item name
                name_text = button_font.render(name, True, WHITE)
                virtual_surface.blit(name_text, name_text.get_rect(center=(x + 90, y + 100)))
                
                # Draw price with coin icon
                price_y = y + 125
                try:
                    coin_img = pygame.image.load("assets/Drops/coin.png").convert_alpha()
                    coin_img = pygame.transform.scale(coin_img, (25, 25))
                    virtual_surface.blit(coin_img, (x + 60, price_y - 12))
                    
                    price_text = button_font.render(f"{price}", True, WHITE)
                    virtual_surface.blit(price_text, (x + 90, price_y - 8))
                except:
                    price_text = button_font.render(f"{price} coins", True, WHITE)
                    virtual_surface.blit(price_text, price_text.get_rect(center=(x + 90, price_y)))
                
                # Buy button
                buy_button = pygame.Rect(x + 20, y + 180, 140, 40)
                buy_buttons.append((buy_button, i))

                buy_color = HOVER_COLOR if buy_button.collidepoint((vmx, vmy)) and tournament_data["coins"] >= price else BUTTON_COLOR
                if tournament_data["coins"] < price:
                    buy_color = (100, 100, 100)
                
                pygame.draw.rect(virtual_surface, buy_color, buy_button, border_radius=8)
                buy_text = button_font.render("Buy", True, WHITE)
                virtual_surface.blit(buy_text, buy_text.get_rect(center=buy_button.center))
            
            # Draw coin info
            coin_info_bg = pygame.Rect(30, VIRTUAL_H - 100, 220, 70)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), coin_info_bg, border_radius=10)
            
            try:
                coin_img = pygame.image.load("assets/Drops/coin.png").convert_alpha()
                coin_img = pygame.transform.scale(coin_img, (35, 35))
                virtual_surface.blit(coin_img, (40, VIRTUAL_H - 85))
                
                coin_text = button_font.render(f": {tournament_data['coins']}", True, WHITE)
                virtual_surface.blit(coin_text, (80, VIRTUAL_H - 75))
            except:
                coin_text = button_font.render(f"Coins: {tournament_data['coins']}", True, WHITE)
                virtual_surface.blit(coin_text, (40, VIRTUAL_H - 75))
            
            # Back button
            back_button = pygame.Rect(VIRTUAL_W // 2 - 60, VIRTUAL_H - 80, 120, 50)
            back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=10)
            back_text = button_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Navigation buttons
                    if prev_button.collidepoint((vmx, vmy)) and shop_page > 0:
                        shop_page -= 1
                    elif next_button.collidepoint((vmx, vmy)) and shop_page < max_pages - 1:
                        shop_page += 1
                    
                    # Back button
                    elif back_button.collidepoint((vmx, vmy)):
                        return
                    
                    # Buy buttons - BUG FIX APPLIED HERE
                    for buy_button, item_index in buy_buttons:
                        if buy_button.collidepoint((vmx, vmy)):
                            item = current_items[item_index]
                            name, price, asset_path, data_key, data_file = item
                            
                            if tournament_data["coins"] >= price:
                                # Kurangi coin terlebih dahulu
                                tournament_data["coins"] -= price
                                
                                # Tambahkan item ke inventory yang sesuai
                                if data_file == "summer":
                                    summer_data[data_key] += 1
                                    save_summer_data(summer_data)
                                elif data_file == "dungeon":
                                    dungeon_data[data_key] += 1
                                    save_dungeon_data(dungeon_data)
                                
                                # PENTING: Selalu simpan tournament_data setelah mengubah coin
                                save_tournament_data(tournament_data)
                                                                                       
            draw_scaled_centered()
            clock.tick(60)
    
    # Tournament lobby function
    def tournament_lobby():
        tournament_data = load_tournament_data()
        
        # Load and play background music
        try:
            pygame.mixer.music.load("assets/musicbg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Error loading background music: {e}")
        
        # Load background image
        try:
            lobby_bg = pygame.image.load("assets/background.png").convert()
            lobby_bg = pygame.transform.smoothscale(lobby_bg, (VIRTUAL_W, VIRTUAL_H))
        except pygame.error as e:
            print(f"Error loading background image: {e}")
            lobby_bg = None
        
        # Update stamina regeneration
        current_time = datetime.now()
        
        try:
            last_regen = datetime.fromisoformat(tournament_data["last_stamina_regen"])
            time_diff = current_time - last_regen
            minutes_passed = time_diff.total_seconds() / 60
            stamina_to_add = int(minutes_passed / 20) * 10  # 10 stamina per 20 minutes
            
            if stamina_to_add > 0:
                tournament_data["stamina"] = min(100, tournament_data["stamina"] + stamina_to_add)
                tournament_data["last_stamina_regen"] = current_time.isoformat()
                save_tournament_data(tournament_data)
        except:
            tournament_data["last_stamina_regen"] = current_time.isoformat()
            save_tournament_data(tournament_data)
        
        selected_character = None
        
        while True:
            # Draw background
            if lobby_bg:
                virtual_surface.blit(lobby_bg, (0, 0))
            else:
                virtual_surface.fill((20, 30, 50))
            
            # Calculate mouse position
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            # Draw title (no icons)
            title_text1 = title_font.render("Tournament", True, get_rainbow_color())
            title_text2 = title_font.render("Lobby", True, get_rainbow_color())
            virtual_surface.blit(title_text1, title_text1.get_rect(center=(VIRTUAL_W // 2, 60)))
            virtual_surface.blit(title_text2, title_text2.get_rect(center=(VIRTUAL_W // 2, 100)))

            
            # Character selection box
            char_box = pygame.Rect(VIRTUAL_W // 2 - 120, 150, 240, 180)
            char_box_color = HOVER_COLOR if char_box.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, char_box_color, char_box, border_radius=15)
            pygame.draw.rect(virtual_surface, WHITE, char_box, 3, border_radius=15)
            
            if selected_character:
                # Draw selected character
                try:
                    char_preview = pygame.image.load(f"assets/{selected_character}/Idle.png").convert_alpha()
                    frame_count = character_frame_counts[selected_character]["Idle"]
                    frame_width = char_preview.get_width() // frame_count
                    char_sprite = char_preview.subsurface(pygame.Rect(0, 0, frame_width, char_preview.get_height()))
                    char_sprite = pygame.transform.scale(char_sprite, (120, 120))
                    sprite_rect = char_sprite.get_rect(center=(char_box.centerx, char_box.centery - 20))
                    virtual_surface.blit(char_sprite, sprite_rect)
                    
                    char_name_text = button_font.render(selected_character, True, WHITE)
                    virtual_surface.blit(char_name_text, char_name_text.get_rect(center=(char_box.centerx, char_box.bottom - 30)))
                except:
                    plus_text = title_font.render(selected_character, True, WHITE)
                    virtual_surface.blit(plus_text, plus_text.get_rect(center=char_box.center))
            else:
                # Draw + symbol
                plus_text = title_font.render("+", True, WHITE)
                virtual_surface.blit(plus_text, plus_text.get_rect(center=char_box.center))
                
                select_text = button_font.render("Select Character", True, WHITE)
                virtual_surface.blit(select_text, select_text.get_rect(center=(char_box.centerx, char_box.bottom - 30)))
            
            # Stamina display
            stamina_bg = pygame.Rect(VIRTUAL_W // 2 - 180, 350, 360, 80)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), stamina_bg, border_radius=12)
            
            stamina_text = button_font.render("Stamina", True, WHITE)
            virtual_surface.blit(stamina_text, stamina_text.get_rect(center=(VIRTUAL_W // 2, 370)))
            
            # Stamina bar
            stamina_bar_bg = pygame.Rect(VIRTUAL_W // 2 - 150, 390, 300, 25)
            pygame.draw.rect(virtual_surface, (100, 100, 100), stamina_bar_bg, border_radius=12)
            
            stamina_fill_width = int((tournament_data["stamina"] / 100) * 300)
            stamina_bar = pygame.Rect(VIRTUAL_W // 2 - 150, 390, stamina_fill_width, 25)
            pygame.draw.rect(virtual_surface, SELECTED_COLOR, stamina_bar, border_radius=12)
            
            stamina_value_text = button_font.render(f"{tournament_data['stamina']}/100", True, WHITE)
            virtual_surface.blit(stamina_value_text, stamina_value_text.get_rect(center=(VIRTUAL_W // 2, 402)))
            
            # Start Tournament button
            start_button = pygame.Rect(VIRTUAL_W // 2 - 120, 450, 240, 60)
            can_start = selected_character and tournament_data["stamina"] >= 10
            start_color = HOVER_COLOR if start_button.collidepoint((vmx, vmy)) and can_start else BUTTON_COLOR
            if not can_start:
                start_color = (100, 100, 100)
            
            pygame.draw.rect(virtual_surface, start_color, start_button, border_radius=12)
            start_text = button_font.render("Start Tournament", True, WHITE if can_start else (160, 160, 160))
            virtual_surface.blit(start_text, start_text.get_rect(center=start_button.center))
            
            if not can_start and selected_character:
                warning_text = small_font.render("Need 10 stamina to start", True, RED)
                virtual_surface.blit(warning_text, warning_text.get_rect(center=(VIRTUAL_W // 2, 530)))
            elif not selected_character:
                warning_text = small_font.render("Select a character first", True, RED)
                virtual_surface.blit(warning_text, warning_text.get_rect(center=(VIRTUAL_W // 2, 530)))
            
            # Tournament Shop button
            shop_button = pygame.Rect(VIRTUAL_W - 180, 50, 150, 50)
            shop_color = HOVER_COLOR if shop_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, shop_color, shop_button, border_radius=10)
            shop_text = button_font.render("Shop", True, WHITE)
            virtual_surface.blit(shop_text, shop_text.get_rect(center=shop_button.center))
            
            # Back button
            back_button = pygame.Rect(50, 50, 100, 50)
            back_color = HOVER_COLOR if back_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, back_color, back_button, border_radius=10)
            back_text = button_font.render("Back", True, WHITE)
            virtual_surface.blit(back_text, back_text.get_rect(center=back_button.center))
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Character selection
                    if char_box.collidepoint((vmx, vmy)):
                        selected_character = character_selection_screen()
                    
                    # Start tournament
                    elif start_button.collidepoint((vmx, vmy)) and can_start:
                        tournament_data["stamina"] -= 10
                        save_tournament_data(tournament_data)
                        return selected_character
                    
                    # Tournament shop
                    elif shop_button.collidepoint((vmx, vmy)):
                        tournament_shop()
                    
                    # Back button
                    elif back_button.collidepoint((vmx, vmy)):
                        return None
            
            draw_scaled_centered()
            clock.tick(60)

    # Start with lobby
    selected_character = tournament_lobby()
    if not selected_character:
        return
    
    # Tournament state
    player_wins = 0
    enemy_wins = 0
    current_round = 1
    max_rounds = 3
    
    # Character selection
    player_characters = [selected_character]
    enemy_characters = []
    
    # Show waiting screen
    def show_waiting_screen():
        wait_time = 3000  # 3 seconds
        start_time = pygame.time.get_ticks()
        
        while pygame.time.get_ticks() - start_time < wait_time:
            virtual_surface.fill((30, 30, 60))
            
            # Animated loading text
            elapsed = pygame.time.get_ticks() - start_time
            dots = "." * ((elapsed // 500) % 4)  # Cycle through 0-3 dots
            
            waiting_text = title_font.render(f"Preparing Tournament{dots}", True, get_rainbow_color())
            virtual_surface.blit(waiting_text, waiting_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2)))
            
            subtitle_text = button_font.render("Setting up opponents...", True, WHITE)
            virtual_surface.blit(subtitle_text, subtitle_text.get_rect(center=(VIRTUAL_W // 2, VIRTUAL_H // 2 + 60)))
            
            # Progress bar
            progress = (elapsed / wait_time) * 100
            bar_width = 300
            bar_height = 20
            bar_x = VIRTUAL_W // 2 - bar_width // 2
            bar_y = VIRTUAL_H // 2 + 120
            
            pygame.draw.rect(virtual_surface, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(virtual_surface, SELECTED_COLOR, (bar_x, bar_y, int(bar_width * progress / 100), bar_height))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
            
            draw_scaled_centered()
            clock.tick(60)
    
    # Show waiting screen
    show_waiting_screen()
    
    # Remaining rounds - random character selection for player
    all_characters = ["Samurai", "Soldier", "Magician"]
    for _ in range(2):
        random_char = random.choice(all_characters)
        player_characters.append(random_char)
    
    # Enemy team gets random characters for all rounds
    for _ in range(3):
        enemy_char = random.choice(all_characters)
        enemy_characters.append(enemy_char)
    
    # Get player name
    def input_name_screen():
        input_box = pygame.Rect(200, 250, 400, 50)
        color_inactive = pygame.Color('gray')
        color_active = pygame.Color('dodgerblue2')
        color = color_inactive
        active = False
        user_text = ""
        
        keys = []
        key_w, key_h = 40, 40
        start_x = 140
        start_y = 400
        row_layout = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_idx, row in enumerate(row_layout):
            for col_idx, char in enumerate(row):
                x = start_x + col_idx * (key_w + 5)
                y = start_y + row_idx * (key_h + 5)
                rect = pygame.Rect(x, y, key_w, key_h)
                keys.append((char, rect))

        backspace_rect = pygame.Rect(start_x, start_y + 3 * (key_h + 5), 120, 40)
        enter_rect = pygame.Rect(start_x + 130, start_y + 3 * (key_h + 5), 150, 40)

        while True:
            virtual_surface.fill((30, 30, 60))

            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if input_box.collidepoint((vmx, vmy)):
                        active = True
                        color = color_active
                    else:
                        active = False
                        color = color_inactive

                    for char, rect in keys:
                        if rect.collidepoint((vmx, vmy)):
                            if len(user_text) < 12:
                                user_text += char

                    if backspace_rect.collidepoint((vmx, vmy)):
                        user_text = user_text[:-1]

                    if enter_rect.collidepoint((vmx, vmy)) and user_text.strip():
                        return user_text

            txt_surface = button_font.render(user_text, True, WHITE)
            width = max(400, txt_surface.get_width() + 10)
            input_box.w = width

            pygame.draw.rect(virtual_surface, color, input_box, 2)
            virtual_surface.blit(txt_surface, (input_box.x + 5, input_box.y + 10))

            prompt = title_font.render("Enter Your Name", True, get_rainbow_color())
            virtual_surface.blit(prompt, prompt.get_rect(center=(VIRTUAL_W // 2, 180)))

            for char, rect in keys:
                pygame.draw.rect(virtual_surface, BUTTON_COLOR, rect, border_radius=5)
                label = button_font.render(char, True, WHITE)
                virtual_surface.blit(label, label.get_rect(center=rect.center))

            pygame.draw.rect(virtual_surface, BUTTON_COLOR, backspace_rect, border_radius=5)
            bksp_text = button_font.render("Backspace", True, WHITE)
            virtual_surface.blit(bksp_text, bksp_text.get_rect(center=backspace_rect.center))

            pygame.draw.rect(virtual_surface, HOVER_COLOR if user_text.strip() else (100, 100, 100), enter_rect, border_radius=5)
            ent_text = button_font.render("Enter", True, WHITE)
            virtual_surface.blit(ent_text, ent_text.get_rect(center=enter_rect.center))

            draw_scaled_centered()
            clock.tick(30)

    name = input_name_screen()
    
    def show_round_preview(round_num, player_char, enemy_char):
        """Show preview screen before each round"""
        preview_timer = pygame.time.get_ticks()
        
        while pygame.time.get_ticks() - preview_timer < 3000:  # Show for 3 seconds
            virtual_surface.fill((20, 20, 40))
            
            # Round title
            round_text = title_font.render(f"ROUND {round_num}", True, get_rainbow_color())
            virtual_surface.blit(round_text, round_text.get_rect(center=(VIRTUAL_W // 2, 150)))
            
            # Tournament score
            score_text = button_font.render(f"Score - You: {player_wins} | Enemy: {enemy_wins}", True, WHITE)
            virtual_surface.blit(score_text, score_text.get_rect(center=(VIRTUAL_W // 2, 200)))
            
            # Character matchup
            vs_text = button_font.render(f"{player_char} VS {enemy_char}", True, WHITE)
            virtual_surface.blit(vs_text, vs_text.get_rect(center=(VIRTUAL_W // 2, 280)))
            
            # Character previews
            try:
                # Player character preview
                player_preview = pygame.image.load(f"assets/{player_char}/Idle.png").convert_alpha()
                frame_count = character_frame_counts[player_char]["Idle"]
                frame_width = player_preview.get_width() // frame_count
                player_sprite = player_preview.subsurface(pygame.Rect(0, 0, frame_width, player_preview.get_height()))
                player_sprite = pygame.transform.scale(player_sprite, (120, 120))
                virtual_surface.blit(player_sprite, (VIRTUAL_W // 4 - 60, 320))
                
                # Enemy character preview
                enemy_preview = pygame.image.load(f"assets/{enemy_char}/Idle.png").convert_alpha()
                frame_count = character_frame_counts[enemy_char]["Idle"]
                frame_width = enemy_preview.get_width() // frame_count
                enemy_sprite = enemy_preview.subsurface(pygame.Rect(0, 0, frame_width, enemy_preview.get_height()))
                enemy_sprite = pygame.transform.scale(enemy_sprite, (120, 120))
                enemy_sprite = pygame.transform.flip(enemy_sprite, True, False)
                virtual_surface.blit(enemy_sprite, (3 * VIRTUAL_W // 4 - 60, 320))
            except:
                pass
            
            # Ready message
            ready_text = small_font.render("Get Ready...", True, WHITE)
            virtual_surface.blit(ready_text, ready_text.get_rect(center=(VIRTUAL_W // 2, 480)))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
            
            draw_scaled_centered()
            clock.tick(60)
            
    def show_emoji_menu():
        """Show emoji chat menu"""
        emoji_options = ["GG", "Noob", "Go Away", "LOL", "Mhtpsg"]
        emoji_responses = {
            "GG": "Thanks, you're GG too",
            "Noob": "isn't that backwards?",
            "Go Away": "im will go on you hehe :v",
            "LOL": "why are you so laughing?",
            "Mhtpsg": "dont forget to join discord!"
        }
        
        # Create emoji menu overlay
        overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        
        # Emoji button positions
        emoji_buttons = {}
        for i, emoji in enumerate(emoji_options):
            x = VIRTUAL_W // 2 - 150
            y = 200 + i * 60
            emoji_buttons[emoji] = pygame.Rect(x, y, 300, 50)
        
        close_button = pygame.Rect(VIRTUAL_W // 2 - 50, 500, 100, 40)
        selected_emoji = None
        
        while True:
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for emoji, rect in emoji_buttons.items():
                        if rect.collidepoint((vmx, vmy)):
                            selected_emoji = emoji
                            return emoji_responses[emoji]
                    
                    if close_button.collidepoint((vmx, vmy)):
                        return None
            
            # Draw overlay
            virtual_surface.blit(overlay, (0, 0))
            
            # Draw title
            emoji_title = button_font.render("Choose Emoji", True, WHITE)
            virtual_surface.blit(emoji_title, emoji_title.get_rect(center=(VIRTUAL_W // 2, 150)))
            
            # Draw emoji buttons
            for emoji, rect in emoji_buttons.items():
                color = HOVER_COLOR if rect.collidepoint((vmx, vmy)) else BUTTON_COLOR
                pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
                
                emoji_text = button_font.render(emoji, True, WHITE)
                virtual_surface.blit(emoji_text, emoji_text.get_rect(center=rect.center))
            
            # Draw close button
            close_color = HOVER_COLOR if close_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, close_color, close_button, border_radius=8)
            close_text = button_font.render("Close", True, WHITE)
            virtual_surface.blit(close_text, close_text.get_rect(center=close_button.center))
            
            draw_scaled_centered()
            clock.tick(60)
    
    def tournament_battle(round_num, player_char, enemy_char):
        """Single 1v1 battle with enhanced features"""
        nonlocal player_wins, enemy_wins
        
        # Show round preview
        show_round_preview(round_num, player_char, enemy_char)
        
        # Load and play tournament music
        try:
            pygame.mixer.music.load("assets/tournamentbg.mp3")
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
        except pygame.error as e:
            print(f"Error loading tournament music: {e}")
        
        # Initialize battle
        PLAYER_MAX_HP = 100
        PLAYER_MAX_MP = 100
        hp = PLAYER_MAX_HP
        mp = PLAYER_MAX_MP
        last_mp_regen = pygame.time.get_ticks()
        is_shielding = False
        is_dead = False
        is_hurt = False
        hurt_timer = 0
        death_animation_complete = False
        last_attack_time = 0
        
        # Chat system variables
        enemy_message = ""
        enemy_message_timer = 0
        enemy_message_duration = 3000

        # Load background
        bg = pygame.image.load("assets/tournament_background.png").convert()
        bg = pygame.transform.smoothscale(bg, (VIRTUAL_W, VIRTUAL_H))
        
        # Load player animations
        actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3", "Dead", "Hurt"]
        player_anims = load_animation_frames(player_char, actions, character_frame_counts[player_char])

        frame_delays = {
            "Idle": 160, "Run": 100, "Jump": 150, "Shield": 170,
            "Attack_1": 130, "Attack_2": 135, "Attack_3": 130,
            "Dead": 170, "Hurt": 170
        }

        action = "Idle"
        idx, timer = 0, 0
        pos = [VIRTUAL_W // 4, VIRTUAL_H - 150]  # Player starts on left
        vel = [0, 0]
        jumping = False
        jump_count = 2
        holding_shield = False

        # Create enhanced enemy with fast run ability
        class TournamentEnemy(Enemy):
            def __init__(self, character_type, x, y):
                super().__init__(character_type, x, y)
                self.fast_run_timer = 0
                self.fast_run_duration = 10000  # 10 seconds
                self.is_fast_running = False
                self.fast_run_triggered = False
                
            def update(self, dt, player_pos):
                # Check if enemy should start fast running (30% HP)
                if not self.fast_run_triggered and self.hp <= 30:
                    self.fast_run_triggered = True
                    self.is_fast_running = True
                    self.fast_run_timer = pygame.time.get_ticks()
                    self.ai_state = "RETREAT"  # Force retreat when fast running
                
                # Update fast run state
                if self.is_fast_running:
                    if pygame.time.get_ticks() - self.fast_run_timer > self.fast_run_duration:
                        self.is_fast_running = False
                    else:
                        self.movement_speed = 8  # Much faster movement
                
                # Call parent update
                super().update(dt, player_pos)
            
            def draw(self, surface):
                # Call parent draw
                super().draw(surface)
                
                # Show fast run indicator
                if self.is_fast_running:
                    time_left = self.fast_run_duration - (pygame.time.get_ticks() - self.fast_run_timer)
                    seconds_left = time_left // 1000
                    fast_run_text = small_font.render(f"FAST RUN: {seconds_left}s", True, (255, 255, 0))
                    fast_run_rect = fast_run_text.get_rect(center=(self.pos[0], self.pos[1] - 220))
                    surface.blit(fast_run_text, fast_run_rect)

        enemy = TournamentEnemy(enemy_char, VIRTUAL_W * 3 // 4, VIRTUAL_H - 150)

        def draw_tournament_hud():
            # Tournament info
            tournament_bg = pygame.Rect(VIRTUAL_W // 2 - 150, 10, 300, 80)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), tournament_bg, border_radius=8)
            
            # Round info
            round_text = button_font.render(f"ROUND {round_num}/{max_rounds}", True, WHITE)
            virtual_surface.blit(round_text, round_text.get_rect(center=(VIRTUAL_W // 2, 25)))
            
            # Score
            score_text = small_font.render(f"You: {player_wins} - Enemy: {enemy_wins}", True, WHITE)
            virtual_surface.blit(score_text, score_text.get_rect(center=(VIRTUAL_W // 2, 45)))
            
            # Current matchup
            matchup_text = small_font.render(f"{player_char} vs {enemy_char}", True, WHITE)
            virtual_surface.blit(matchup_text, matchup_text.get_rect(center=(VIRTUAL_W // 2, 65)))
            
            # Player HUD
            hud_bg = pygame.Rect(10, 10, 200, 90)
            pygame.draw.rect(virtual_surface, (0, 0, 0, 180), hud_bg, border_radius=8)
            
            # HP bar
            pygame.draw.rect(virtual_surface, (100, 100, 100), (15, 20, 170, 10))
            hp_width = int((hp / PLAYER_MAX_HP) * 170)
            pygame.draw.rect(virtual_surface, (255, 0, 0), (15, 20, hp_width, 10))
            
            # MP bar  
            pygame.draw.rect(virtual_surface, (50, 50, 50), (15, 35, 170, 10))
            mp_width = int((mp / PLAYER_MAX_MP) * 170)
            pygame.draw.rect(virtual_surface, (0, 0, 255), (15, 35, mp_width, 10))
            
            # Labels
            hp_text = small_font.render(f"HP: {hp}/{PLAYER_MAX_HP}", True, WHITE)
            virtual_surface.blit(hp_text, (15, 50))
            mp_text = small_font.render(f"MP: {mp}/{PLAYER_MAX_MP}", True, WHITE)
            virtual_surface.blit(mp_text, (15, 65))
            name_text = small_font.render(f"{name}", True, WHITE)
            virtual_surface.blit(name_text, (15, 80))
            
            # Draw enemy message if active
            if enemy_message and pygame.time.get_ticks() - enemy_message_timer < enemy_message_duration:
                message_bg = pygame.Rect(VIRTUAL_W // 2 - 200, VIRTUAL_H - 150, 400, 60)
                pygame.draw.rect(virtual_surface, (0, 0, 0, 200), message_bg, border_radius=8)
                pygame.draw.rect(virtual_surface, WHITE, message_bg, 2, border_radius=8)
                
                message_text = small_font.render(f"Enemy: {enemy_message}", True, WHITE)
                virtual_surface.blit(message_text, message_text.get_rect(center=message_bg.center))

        def check_collision_and_damage():
            nonlocal hp, is_hurt, hurt_timer, is_dead, action, idx, timer, last_attack_time
            
            # Check if enemy is attacking and close enough to player
            if enemy.is_attacking():
                distance = abs(enemy.pos[0] - pos[0])
                attack_range = enemy.get_attack_range()
                
                if distance < attack_range:
                    current_time = pygame.time.get_ticks()
                    if current_time - enemy.last_attack_time > 800:
                        damage = enemy.get_attack_damage()
                        
                        if is_shielding:
                            damage = 0
                        
                        if damage > 0:
                            hp -= damage
                            enemy.last_attack_time = current_time
                            
                            if hp <= 0:
                                hp = 0
                                is_dead = True
                                action = "Dead"
                                idx = 0
                                timer = 0
                            else:
                                is_hurt = True
                                hurt_timer = pygame.time.get_ticks()
                                action = "Hurt"
                                idx = 0
                                timer = 0
            
            # Check if player is attacking and close enough to enemy
            if "Attack" in action and idx > 0:
                distance = abs(pos[0] - enemy.pos[0])
                player_range = character_ranges[player_char]
                
                if distance < player_range:
                    current_time = pygame.time.get_ticks()
                    if current_time - last_attack_time > 500:
                        damage = character_damage[player_char][action]
                        enemy.take_damage(damage)
                        last_attack_time = current_time

        # UI setup with faster movement
        size = 60
        spacing = 10
        dir_center_x = 90
        dir_center_y = VIRTUAL_H - 280

        left = pygame.Rect(dir_center_x - size - spacing, dir_center_y, size, size)
        right = pygame.Rect(dir_center_x + size + spacing, dir_center_y, size, size)
        up = pygame.Rect(dir_center_x, dir_center_y - size - spacing, size, size)
        down = pygame.Rect(dir_center_x, dir_center_y + size + spacing, size, size)

        btn_w, btn_h = 80, 60
        action_y = VIRTUAL_H - btn_h - 10
        action_buttons = {
            "atk1": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 6, action_y, btn_w, btn_h),
            "atk2": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 5, action_y, btn_w, btn_h),
            "atk3": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 4, action_y, btn_w, btn_h),
            "jump": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 3, action_y, btn_w, btn_h),
            "shield": pygame.Rect(VIRTUAL_W - (btn_w + spacing) * 2, action_y, btn_w, btn_h),
            "run": pygame.Rect(VIRTUAL_W - (btn_w + spacing), action_y, btn_w, btn_h),
        }

        pause_button = pygame.Rect(VIRTUAL_W - 50, 100, 40, 40)
        emoji_button = pygame.Rect(VIRTUAL_W - 50, 150, 40, 40)  # New emoji button

        # Battle loop
        while True:
            dt = clock.tick(60)
            timer += dt
            now = pygame.time.get_ticks()

            # Check battle end conditions
            if is_dead and death_animation_complete:
                pygame.mixer.music.stop()  # Stop music when player loses
                enemy_wins += 1
                return "player_lost"
            
            if enemy.is_dead and enemy.death_animation_complete:
                pygame.mixer.music.stop()  # Stop music when enemy loses
                player_wins += 1
                return "player_won"

            # MP regeneration
            if now - last_mp_regen > 3000:
                mp = min(PLAYER_MAX_MP, mp + 10)
                last_mp_regen = now

            # Handle hurt state
            if is_hurt and now - hurt_timer > 800:
                is_hurt = False
                if not is_dead:
                    action = "Idle"
                    idx = 0
                    timer = 0

            # Event handling
            for e in pygame.event.get():
                if e.type == pygame.QUIT: 
                    exit_game()
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()  # Stop music when escaping
                    return "escape"
                if e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                    ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                    oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                    mx, my = ((mx - ox) / scale, (my - oy) / scale)

                    if pause_button.collidepoint((mx, my)):
                        pause_result = pause_menu()
                        if pause_result == "back":
                            pygame.mixer.music.stop()  # Stop music when going back
                            return "escape"
                        elif pause_result == "restart":
                            return "restart"
                    
                    # Handle emoji button click
                    if emoji_button.collidepoint((mx, my)):
                        enemy_response = show_emoji_menu()
                        if enemy_response:
                            enemy_message = enemy_response
                            enemy_message_timer = pygame.time.get_ticks()

                    # Don't allow actions if dead or hurt
                    if is_dead or is_hurt:
                        continue

                    # Movement controls with increased speed
                    if left.collidepoint((mx, my)): 
                        vel[0] = -8  # Increased speed
                        action = "Run"
                        play_sound_effect("Run", player_char)
                        is_shielding = False
                    elif right.collidepoint((mx, my)): 
                        vel[0] = 8  # Increased speed
                        action = "Run"
                        play_sound_effect("Run", player_char)
                        is_shielding = False
                    elif up.collidepoint((mx, my)): 
                        vel[1] = -8  # Increased speed
                        action = "Run"
                        play_sound_effect("Run", player_char)
                        is_shielding = False
                    elif down.collidepoint((mx, my)): 
                        vel[1] = 8  # Increased speed
                        action = "Run"
                        play_sound_effect("Run", player_char)
                        is_shielding = False
                    elif action_buttons["atk1"].collidepoint((mx, my)):
                        if mp >= 5: 
                            action = "Attack_1"
                            play_sound_effect("Attack_1", player_char)
                            idx = 0
                            timer = 0
                            mp -= 5
                            is_shielding = False
                    elif action_buttons["atk2"].collidepoint((mx, my)):
                        if mp >= 8: 
                            action = "Attack_2"
                            play_sound_effect("Attack_2", player_char)
                            idx = 0
                            timer = 0
                            mp -= 8
                            is_shielding = False
                    elif action_buttons["atk3"].collidepoint((mx, my)):
                        if mp >= 12: 
                            action = "Attack_3"
                            play_sound_effect("Attack_3", player_char)
                            idx = 0
                            timer = 0
                            mp -= 12
                            is_shielding = False
                    elif action_buttons["jump"].collidepoint((mx, my)):
                        if jump_count > 0:
                            vel[1] = -12
                            action = "Jump"
                            play_sound_effect("Jump", player_char)
                            jumping = True
                            jump_count -= 1
                            idx = 0
                            timer = 0
                            is_shielding = False
                    elif action_buttons["shield"].collidepoint((mx, my)):
                        holding_shield = True
                        action = "Shield"
                        play_sound_effect("Shield", player_char)
                        idx = 0
                        timer = 0
                        is_shielding = True
                    elif action_buttons["run"].collidepoint((mx, my)):
                        vel[0] = 12  # Even faster run speed
                        action = "Run"
                        play_sound_effect("Run", player_char)
                        is_shielding = False

                if e.type == pygame.MOUSEBUTTONUP:
                    if not is_dead and not is_hurt:
                        vel = [0, 0]
                        holding_shield = False
                        is_shielding = False
                        if not jumping: 
                            action = "Idle"

            # Physics update
            if not is_dead:
                if jumping:
                    vel[1] += 0.5
                    pos[1] += vel[1]
                    if pos[1] >= VIRTUAL_H - 150:
                        pos[1] = VIRTUAL_H - 150
                        jumping = False
                        vel[1] = 0
                        jump_count = 2
                        if not is_hurt:
                            action = "Idle"
                else:
                    pos[0] += vel[0]
                    pos[1] += vel[1]

                # Screen boundaries
                sprite_width = 160
                left_limit = sprite_width // 2
                right_limit = VIRTUAL_W - sprite_width // 2
                top_limit = 0
                bottom_limit = VIRTUAL_H - sprite_width

                pos[0] = max(left_limit, min(right_limit, pos[0]))
                pos[1] = max(top_limit, min(bottom_limit, pos[1]))

            # Update enemy
            enemy.update(dt, pos)
            
            # Check combat
            check_collision_and_damage()

            # Update player animation
            delay = frame_delays.get(action, 130)
            if timer >= delay:
                timer = 0
                if player_anims[action]:
                    idx += 1
                    if idx >= len(player_anims[action]):
                        if action == "Dead":
                            death_animation_complete = True
                            idx = len(player_anims["Dead"]) - 1
                        elif "Attack" in action or action == "Jump":
                            if not is_hurt and not is_dead:
                                action = "Idle"
                                idx = 0
                        elif action == "Shield" and holding_shield:
                            idx = len(player_anims["Shield"]) - 1
                        elif action == "Hurt":
                            idx = len(player_anims["Hurt"]) - 1
                        else:
                            if not is_hurt and not is_dead:
                                action = "Idle"
                                idx = 0

            # Drawing
            virtual_surface.blit(bg, (0, 0))
            
            # Draw player
            if player_anims[action]:
                frame_idx = min(idx, len(player_anims[action]) - 1)
                sprite = pygame.transform.scale(player_anims[action][frame_idx], (160, 160))
                rect = sprite.get_rect(midbottom=(pos[0], pos[1] + 100))
                virtual_surface.blit(sprite, rect.topleft)
                
                if is_shielding:
                    shield_text = small_font.render("SHIELD", True, (0, 255, 255))
                    shield_rect = shield_text.get_rect(center=(pos[0], pos[1] - 100))
                    virtual_surface.blit(shield_text, shield_rect)
            
            # Draw enemy
            enemy.draw(virtual_surface)

            # Draw UI controls
            if not is_dead:
                # Movement buttons
                for btn, symbol in [(left, "<"), (right, ">"), (up, "^"), (down, "v")]:
                    pygame.draw.rect(virtual_surface, BUTTON_COLOR, btn, border_radius=8)
                    txt = button_font.render(symbol, True, WHITE)
                    virtual_surface.blit(txt, txt.get_rect(center=btn.center))
                
                # Action buttons with MP cost indication
                button_configs = [
                    ("atk1", "ATK1", 5), ("atk2", "ATK2", 8), ("atk3", "ATK3", 12),
                    ("jump", "JUMP", 0), ("shield", "SHIELD", 0), ("run", "RUN", 0)
                ]
                
                for btn_name, label, cost in button_configs:
                    rect = action_buttons[btn_name]
                    available = mp >= cost if cost > 0 else True
                    color = BUTTON_COLOR if available else (100, 100, 100)
                    
                    pygame.draw.rect(virtual_surface, color, rect, border_radius=8)
                    text = small_font.render(label, True, WHITE if available else (160, 160, 160))
                    virtual_surface.blit(text, text.get_rect(center=rect.center))

            # Draw pause button
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, pause_button, border_radius=20)
            pause_text = small_font.render("||", True, WHITE)
            virtual_surface.blit(pause_text, pause_text.get_rect(center=pause_button.center))
            
            # Draw emoji button
            pygame.draw.rect(virtual_surface, BUTTON_COLOR, emoji_button, border_radius=20)
            try:
                emoji_image = pygame.image.load("assets/emoji.png")
                emoji_image = pygame.transform.scale(emoji_image, (emoji_button.width - 10, emoji_button.height - 10))
                emoji_rect = emoji_image.get_rect(center=emoji_button.center)
                virtual_surface.blit(emoji_image, emoji_rect)
            except pygame.error:
                emoji_text = small_font.render(":)", True, WHITE)
                virtual_surface.blit(emoji_text, emoji_text.get_rect(center=emoji_button.center))
                
            draw_tournament_hud()
            draw_scaled_centered()
            
    def show_tournament_result():
        """Show final tournament result"""
        # Stop music when tournament ends
        pygame.mixer.music.stop()
        
        # Award coin if player wins tournament (3 wins)
        if player_wins >= 3:
            tournament_data = load_tournament_data()
            tournament_data["coins"] += 1
            save_tournament_data(tournament_data)
            
            title_text = "TOURNAMENT VICTORY!"
            title_color = SELECTED_COLOR
            subtitle_text = f"Congratulations {name}! You won {player_wins}-{enemy_wins}!"
            reward_text = "You earned 1 coin!"
        else:
            title_text = "TOURNAMENT DEFEAT!"
            title_color = RED
            subtitle_text = f"You lost {player_wins}-{enemy_wins}. Better luck next time!"
            reward_text = "No coins earned. Win 3 rounds to get a coin!"

        # Show result screen
        result_timer = pygame.time.get_ticks()
        while pygame.time.get_ticks() - result_timer < 5000:  # Show for 5 seconds
            virtual_surface.fill((20, 20, 40))
            
            # Draw title
            tournament_title = title_font.render(title_text, True, title_color)
            virtual_surface.blit(tournament_title, tournament_title.get_rect(center=(VIRTUAL_W // 2, 200)))
            
            # Draw subtitle
            subtitle = button_font.render(subtitle_text, True, WHITE)
            virtual_surface.blit(subtitle, subtitle.get_rect(center=(VIRTUAL_W // 2, 280)))
            
            # Draw reward info
            reward = small_font.render(reward_text, True, SELECTED_COLOR if player_wins >= 3 else RED)
            virtual_surface.blit(reward, reward.get_rect(center=(VIRTUAL_W // 2, 320)))
            
            # Draw match results
            for i in range(min(current_round - 1, max_rounds)):
                if i < len(player_characters) and i < len(enemy_characters):
                    round_result = f"Round {i+1}: {player_characters[i]} vs {enemy_characters[i]}"
                    result_text = small_font.render(round_result, True, WHITE)
                    virtual_surface.blit(result_text, result_text.get_rect(center=(VIRTUAL_W // 2, 370 + i * 25)))
            
            # Continue message
            continue_text = small_font.render("Tournament will end automatically...", True, WHITE)
            virtual_surface.blit(continue_text, continue_text.get_rect(center=(VIRTUAL_W // 2, 480)))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
            
            draw_scaled_centered()
            clock.tick(60)

    # Main tournament loop
    while current_round <= max_rounds and player_wins < 3 and enemy_wins < 3:
        player_char = player_characters[current_round - 1]
        enemy_char = enemy_characters[current_round - 1]
        
        battle_result = tournament_battle(current_round, player_char, enemy_char)
        
        if battle_result == "escape":
            pygame.mixer.music.stop()  # Stop music when escaping
            return
        elif battle_result == "restart":
            return tournament()  # Restart entire tournament
        
        current_round += 1
        
        # Check if tournament is decided early (best of 3)
        if player_wins >= 3 or enemy_wins >= 3:
            break
    
    # Show final tournament result
    show_tournament_result()
	
def training_mode():
    name = "Player"  # You can also ask for input for the name if needed
    selected_char = character_selection_screen()
    if selected_char:
        # Load and play training music
        try:
            pygame.mixer.music.load("assets/trainingmusicbg.mp3")  # Load the training music
            pygame.mixer.music.set_volume(1.0)  # Set volume to 100%
            pygame.mixer.music.play(-1)  # Play the music in a loop
        except pygame.error as e:
            print(f"Error loading training music: {e}")  # Print error if music fails to load

        while True:
            result = training_loop(name, selected_char)
            if result == "back":
                pygame.mixer.music.stop()  # Stop the music when going back
                return
                                    
# Buat font untuk teks kredit
credit_font = pygame.font.SysFont("Georgia", 25, bold=True)  # Teks tebal
discord_font = pygame.font.SysFont("Georgia", 20)  # Teks biasa

# Fungsi untuk menggambar teks
def draw_credit_text(surface):
    # Teks merah sebagai bayangan
    credit_text_shadow = credit_font.render("@Made by Mhtpsg", True, (255, 0, 0))  # Teks merah
    discord_text_shadow = discord_font.render("Join Discord: https://discord.gg/scNgmKpFBE", True, (255, 0, 0))  # Teks merah

    # Teks putih di atasnya
    credit_text = credit_font.render("@Made by Mhtpsg", True, WHITE)  # Teks putih
    discord_text = discord_font.render("Join Discord: https://discord.gg/scNgmKpFBE", True, WHITE)  # Teks putih

    # Gambar bayangan merah
    surface.blit(credit_text_shadow, (12, 12))  # Offset sedikit untuk bayangan
    surface.blit(discord_text_shadow, (12, 42))  # Offset sedikit untuk bayangan

    # Gambar teks putih
    surface.blit(credit_text, (10, 10))  # Posisi teks kredit
    surface.blit(discord_text, (10, 40))  # Posisi teks Discord

def load_saved_interface():
    global current_interface
    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                current_interface = data.get('interface', None)
        else:
            current_interface = None
    except Exception as e:
        print(f"Error loading interface: {e}")
        current_interface = None

# Function untuk save interface
def save_interface(interface_char):
    global current_interface
    current_interface = interface_char
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump({'interface': interface_char}, f)
    except Exception as e:
        print(f"Error saving interface: {e}")
        
# Main menu
# File untuk menyimpan data akun
ACCOUNTS_FILE = "accounts.json"
SETTINGS_FILE = "user_settings.json"

class VirtualKeyboard:
    def __init__(self):
        self.is_visible = False
        self.key_width = 35  # Ukuran diperkecil dari 45 ke 35
        self.key_height = 35  # Ukuran diperkecil dari 45 ke 35
        self.key_margin = 4   # Margin diperkecil dari 5 ke 4
        self.start_x = 20     # Mulai dari kiri (20px dari edge)
        self.start_y = 280    # Posisi Y keyboard
        self.keyboard_width = VIRTUAL_W - 40  # Full width minus padding
        
        # Layout keyboard - angka di atas, huruf di bawah
        self.number_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        self.letter_rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]
        
        self.shift_pressed = False
        self.key_rects = {}
        self.special_keys = {}
        self._create_keyboard_layout()
    
    def _create_keyboard_layout(self):
        # Clear existing rects
        self.key_rects.clear()
        self.special_keys.clear()
        
        # Calculate key width untuk full width layout
        available_width = self.keyboard_width - (len(self.number_keys) - 1) * self.key_margin
        calculated_key_width = available_width // len(self.number_keys)
        
        # Use the smaller of calculated width or default width
        actual_key_width = min(calculated_key_width, self.key_width)
        
        # Row 1: Numbers (1-0) - Full width
        total_numbers_width = len(self.number_keys) * actual_key_width + (len(self.number_keys) - 1) * self.key_margin
        number_start_x = self.start_x + (self.keyboard_width - total_numbers_width) // 2
        
        for i, key in enumerate(self.number_keys):
            x = number_start_x + i * (actual_key_width + self.key_margin)
            y = self.start_y
            self.key_rects[key] = pygame.Rect(x, y, actual_key_width, self.key_height)
        
        # Row 2-4: Letters (QWERTY layout) - Full width per row
        for row_idx, row in enumerate(self.letter_rows):
            # Calculate width for this row
            row_available_width = self.keyboard_width - (len(row) - 1) * self.key_margin
            row_key_width = min(row_available_width // len(row), actual_key_width)
            
            # Center the row
            total_row_width = len(row) * row_key_width + (len(row) - 1) * self.key_margin
            row_start_x = self.start_x + (self.keyboard_width - total_row_width) // 2
            
            for col_idx, key in enumerate(row):
                x = row_start_x + col_idx * (row_key_width + self.key_margin)
                y = self.start_y + (row_idx + 2) * (self.key_height + self.key_margin + 8)
                self.key_rects[key] = pygame.Rect(x, y, row_key_width, self.key_height)
        
        # Special keys row - NAIK KE ATAS masuk dalam kotak keyboard
        special_y = self.start_y + 5 * (self.key_height + self.key_margin + 8) - 70  # NAIK 20px
        special_key_width = 80
        
        # SPACE (center, wider)
        space_width = 100
        space_x = self.start_x + (self.keyboard_width - space_width) // 7
        self.special_keys['SPACE'] = pygame.Rect(space_x, special_y, space_width, self.key_height)
        
        # DEL (left side)
        del_x = self.start_x
        self.special_keys['DEL'] = pygame.Rect(del_x, special_y, special_key_width, self.key_height)
        
        # Row kedua special keys - NAIK KE ATAS
        second_special_y = special_y + self.key_height + self.key_margin + 25 - 20  # NAIK 20px
        
        # Button A (below DEL) - GANTI NAMA JADI "A"
        a_x = self.start_x
        a_y = second_special_y
        self.special_keys['A'] = pygame.Rect(a_x, a_y, special_key_width, self.key_height)
        
        # CLEAR (center) - PINDAH KE TEMPAT ENTER (kanan)
        clear_x = self.start_x + self.keyboard_width - special_key_width
        clear_y = special_y  # Sejajar dengan DEL dan SPACE
        self.special_keys['CLEAR'] = pygame.Rect(clear_x, clear_y, special_key_width, self.key_height)
        
        # CLOSE (below CLEAR) - GANTI NAMA DARI HIDE JADI CLOSE
        close_x = clear_x
        close_y = second_special_y
        self.special_keys['CLOSE'] = pygame.Rect(close_x, close_y, special_key_width, self.key_height)
    
    def show(self):
        """Show keyboard"""
        self.is_visible = True
    
    def hide(self):
        """Hide keyboard"""
        self.is_visible = False
    
    def toggle(self):
        """Toggle keyboard visibility"""
        self.is_visible = not self.is_visible
    
    def handle_click(self, pos, input_text, max_length=20):
        if not self.is_visible:
            return input_text, False
        
        # Check special keys first
        if self.special_keys['DEL'].collidepoint(pos):
            return input_text[:-1] if input_text else "", False
        
        if self.special_keys['SPACE'].collidepoint(pos):
            if len(input_text) < max_length:
                return input_text + " ", False
            return input_text, False
        
        # Button A functionality (bisa diubah sesuai kebutuhan)
        if 'A' in self.special_keys and self.special_keys['A'].collidepoint(pos):
            if len(input_text) < max_length:
                return input_text + "a", False
            return input_text, False
        
        if 'CLEAR' in self.special_keys and self.special_keys['CLEAR'].collidepoint(pos):
            return "", False
        
        if 'CLOSE' in self.special_keys and self.special_keys['CLOSE'].collidepoint(pos):
            self.hide()
            return input_text, False
        
        # Check regular keys
        for key, rect in self.key_rects.items():
            if rect.collidepoint(pos):
                if len(input_text) < max_length:
                    if self.shift_pressed and key.isalpha():
                        return input_text + key.upper(), False
                    else:
                        return input_text + key.lower(), False
        
        return input_text, False
    
    def draw(self, surface, mouse_pos):
        if not self.is_visible:
            return
        
        # Draw keyboard background - Full width dengan ukuran yang disesuaikan
        keyboard_bg = pygame.Rect(
            self.start_x - 10, 
            self.start_y - 15, 
            self.keyboard_width + 20, 
            5 * (self.key_height + self.key_margin + 8) + 30  # Kurangi tinggi karena button naik
        )
        pygame.draw.rect(surface, (35, 35, 55), keyboard_bg, border_radius=12)
        pygame.draw.rect(surface, WHITE, keyboard_bg, 2, border_radius=12)
        
        # Draw regular keys
        for key, rect in self.key_rects.items():
            is_hovered = rect.collidepoint(mouse_pos)
            color = (90, 110, 160) if is_hovered else (70, 80, 110)
            
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, rect, 1, border_radius=6)
            
            display_key = key.upper() if self.shift_pressed and key.isalpha() else key
            key_text = small_font.render(display_key, True, WHITE)
            text_rect = key_text.get_rect(center=rect.center)
            surface.blit(key_text, text_rect)
        
        # Draw special keys
        special_key_labels = {
            'DEL': 'DEL',
            'SPACE': 'SPACE',
            'A': 'A',
            'CLEAR': 'DEL ALL',    # Button pink
            'CLOSE': 'CLOSE'   # Button merah (dulu HIDE)
        }
        
        for key_name, rect in self.special_keys.items():
            is_hovered = rect.collidepoint(mouse_pos)
            
            if key_name == 'DEL':
                color = (160, 110, 80) if is_hovered else (130, 90, 60)  # Orange
            elif key_name == 'SPACE':
                color = (90, 110, 160) if is_hovered else (70, 80, 110)  # Blue
            elif key_name == 'A':
                color = (90, 110, 160) if is_hovered else (70, 80, 110)  # Blue seperti huruf biasa
            elif key_name == 'CLEAR':
                color = (200, 100, 150) if is_hovered else (170, 80, 130)  # Pink
            elif key_name == 'CLOSE':
                color = (180, 80, 80) if is_hovered else (150, 60, 60)  # Red
            else:
                color = (90, 110, 160) if is_hovered else (70, 80, 110)
            
            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(surface, WHITE, rect, 1, border_radius=6)
            
            label = special_key_labels[key_name]
            # Use smaller font for special keys
            key_text = small_font.render(label, True, WHITE)
            text_rect = key_text.get_rect(center=rect.center)
            surface.blit(key_text, text_rect)

def hash_password(password):
    """Hash password menggunakan SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_accounts():
    """Load akun dari file"""
    if os.path.exists(ACCOUNTS_FILE):
        try:
            with open(ACCOUNTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_accounts(accounts):
    """Save akun ke file"""
    try:
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump(accounts, f, indent=2)
        return True
    except:
        return False

def load_user_settings():
    """Load user settings"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_settings(settings):
    """Save user settings"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except:
        return False

def check_remember_me():
    """Check if user should be automatically logged in"""
    settings = load_user_settings()
    return settings.get('remember_me', False), settings.get('saved_username', '')

def set_remember_me(username, remember):
    """Set remember me settings"""
    settings = load_user_settings()
    settings['remember_me'] = remember
    settings['saved_username'] = username if remember else ''
    save_user_settings(settings)

def show_message_box(message, duration=2000):
    """Show temporary message box"""
    start_time = pygame.time.get_ticks()
    
    while pygame.time.get_ticks() - start_time < duration:
        virtual_surface.fill((30, 30, 60))
        
        # Message box
        box_width = min(500, VIRTUAL_W - 40)
        box_height = 100
        box_x = (VIRTUAL_W - box_width) // 2
        box_y = (VIRTUAL_H - box_height) // 2
        
        message_box = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(virtual_surface, (50, 50, 80), message_box, border_radius=15)
        pygame.draw.rect(virtual_surface, WHITE, message_box, 3, border_radius=15)
        
        # Message text
        text_surface = button_font.render(message, True, WHITE)
        text_rect = text_surface.get_rect(center=message_box.center)
        virtual_surface.blit(text_surface, text_rect)
        
        draw_scaled_centered()
        clock.tick(60)
        
        # Handle events to prevent blocking
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()

def register_screen():
    """Halaman register"""
    keyboard = VirtualKeyboard()
    username = ""
    password = ""
    confirm_password = ""
    active_field = "username"
    
    # Input field rectangles
    username_rect = pygame.Rect(VIRTUAL_W//2 - 150, 100, 300, 40)
    password_rect = pygame.Rect(VIRTUAL_W//2 - 150, 150, 300, 40)
    confirm_rect = pygame.Rect(VIRTUAL_W//2 - 150, 200, 300, 40)
    
    # Button rectangles
    register_btn = pygame.Rect(VIRTUAL_W//2 - 100, 250, 200, 35)
    back_btn = pygame.Rect(50, 50, 100, 35)
    
    # KEYBOARD BUTTON - letakkan di bawah
    keyboard_btn = pygame.Rect(VIRTUAL_W//2 - 75, 295, 150, 35)
    
    while True:
        virtual_surface.fill((30, 30, 60))
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check keyboard button FIRST
                if keyboard_btn.collidepoint((vmx, vmy)):
                    keyboard.toggle()
                    continue
                
                # Check field selection
                if username_rect.collidepoint((vmx, vmy)):
                    active_field = "username"
                elif password_rect.collidepoint((vmx, vmy)):
                    active_field = "password"
                elif confirm_rect.collidepoint((vmx, vmy)):
                    active_field = "confirm_password"
                elif back_btn.collidepoint((vmx, vmy)):
                    return login_screen()
                elif register_btn.collidepoint((vmx, vmy)):
                    # Validate registration
                    if not username or not password:
                        show_message_box("Username and password required!")
                        continue
                    
                    if password != confirm_password:
                        show_message_box("Passwords do not match!")
                        continue
                    
                    if len(username) < 3:
                        show_message_box("Username must be at least 3 characters!")
                        continue
                    
                    if len(password) < 4:
                        show_message_box("Password must be at least 4 characters!")
                        continue
                    
                    # Check if username exists
                    accounts = load_accounts()
                    if username in accounts:
                        show_message_box("Username already exists!")
                        continue
                    
                    # Create account
                    accounts[username] = {
                        'password': hash_password(password),
                        'created': pygame.time.get_ticks()
                    }
                    
                    if save_accounts(accounts):
                        show_message_box("Account created successfully!")
                        return login_screen()
                    else:
                        show_message_box("Failed to create account!")
                
                # Handle keyboard input - ONLY if keyboard visible
                elif keyboard.is_visible:
                    if active_field == "username":
                        new_username, should_submit = keyboard.handle_click((vmx, vmy), username, 15)
                        username = new_username
                    elif active_field == "password":
                        new_password, should_submit = keyboard.handle_click((vmx, vmy), password, 20)
                        password = new_password
                    elif active_field == "confirm_password":
                        new_confirm, should_submit = keyboard.handle_click((vmx, vmy), confirm_password, 20)
                        confirm_password = new_confirm
        
        # Draw title
        title = title_font.render("REGISTER", True, get_rainbow_color())
        title_rect = title.get_rect(center=(VIRTUAL_W//2, 60))
        virtual_surface.blit(title, title_rect)
        
        # Draw input fields
        fields = [
            ("Username:", username_rect, username, active_field == "username"),
            ("Password:", password_rect, "*" * len(password), active_field == "password"),
            ("Confirm:", confirm_rect, "*" * len(confirm_password), active_field == "confirm_password")
        ]
        
        for label, rect, text, is_active in fields:
            # Draw label
            label_surface = small_font.render(label, True, WHITE)
            virtual_surface.blit(label_surface, (rect.x, rect.y - 20))
            
            # Draw field
            color = (100, 150, 100) if is_active else (70, 70, 100)
            pygame.draw.rect(virtual_surface, color, rect, border_radius=5)
            pygame.draw.rect(virtual_surface, WHITE, rect, 2, border_radius=5)
            
            # Draw text
            if text:
                text_surface = small_font.render(text, True, WHITE)
                virtual_surface.blit(text_surface, (rect.x + 10, rect.y + 12))
        
        # Draw buttons
        for btn, label, hover_color in [(register_btn, "REGISTER", (100, 150, 100)), (back_btn, "BACK", (150, 100, 100))]:
            is_hovered = btn.collidepoint((vmx, vmy))
            color = hover_color if is_hovered else (70, 70, 100)
            
            pygame.draw.rect(virtual_surface, color, btn, border_radius=8)
            pygame.draw.rect(virtual_surface, WHITE, btn, 2, border_radius=8)
            
            btn_text = small_font.render(label, True, WHITE)
            text_rect = btn_text.get_rect(center=btn.center)
            virtual_surface.blit(btn_text, text_rect)
        
        # Draw KEYBOARD BUTTON
        kb_is_hovered = keyboard_btn.collidepoint((vmx, vmy))
        kb_color = (120, 120, 200) if kb_is_hovered else (80, 80, 150)
        if keyboard.is_visible:
            kb_color = (200, 120, 120)  # Red when keyboard is visible
        
        pygame.draw.rect(virtual_surface, kb_color, keyboard_btn, border_radius=8)
        pygame.draw.rect(virtual_surface, WHITE, keyboard_btn, 2, border_radius=8)
        
        kb_text = small_font.render("KEYBOARD", True, WHITE)
        kb_text_rect = kb_text.get_rect(center=keyboard_btn.center)
        virtual_surface.blit(kb_text, kb_text_rect)
        
        # Draw keyboard if visible
        keyboard.draw(virtual_surface, (vmx, vmy))
        
        draw_scaled_centered()
        clock.tick(60)

def login_screen():
    """Halaman login"""
    keyboard = VirtualKeyboard()
    username = ""
    password = ""
    active_field = "username"
    remember_me = False
    
    # Check if remember me is active
    is_remembered, saved_username = check_remember_me()
    if is_remembered and saved_username:
        # Auto login
        global current_interface
        if current_interface:
            new_screen(current_interface)
        else:
            choose_interface()
        return
    
    # Input field rectangles
    username_rect = pygame.Rect(VIRTUAL_W//2 - 150, 100, 300, 40)
    password_rect = pygame.Rect(VIRTUAL_W//2 - 150, 150, 300, 40)
    
    # Button rectangles
    login_btn = pygame.Rect(VIRTUAL_W//2 - 100, 220, 200, 35)
    register_btn = pygame.Rect(VIRTUAL_W//2 - 100, 265, 200, 35)
    
    # Remember me checkbox
    checkbox_rect = pygame.Rect(VIRTUAL_W//2 - 150, 185, 20, 20)
    
    # KEYBOARD BUTTON - letakkan di bawah
    keyboard_btn = pygame.Rect(VIRTUAL_W//2 - 75, 310, 150, 35)
    
    while True:
        virtual_surface.fill((30, 30, 60))
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check keyboard button FIRST
                if keyboard_btn.collidepoint((vmx, vmy)):
                    keyboard.toggle()
                    continue
                
                # Check field selection
                if username_rect.collidepoint((vmx, vmy)):
                    active_field = "username"
                elif password_rect.collidepoint((vmx, vmy)):
                    active_field = "password"
                elif checkbox_rect.collidepoint((vmx, vmy)):
                    remember_me = not remember_me
                elif login_btn.collidepoint((vmx, vmy)):
                    # Validate login
                    if not username or not password:
                        show_message_box("Username and password required!")
                        continue
                    
                    accounts = load_accounts()
                    if username not in accounts:
                        show_message_box("Username not found!")
                        continue
                    
                    if accounts[username]['password'] != hash_password(password):
                        show_message_box("Incorrect password!")
                        continue
                    
                    # Login successful
                    set_remember_me(username, remember_me)
                    show_message_box("Login successful!")
                    
                    # Proceed to game
                    if current_interface:
                        new_screen(current_interface)
                    else:
                        choose_interface()
                    return
                    
                elif register_btn.collidepoint((vmx, vmy)):
                    return register_screen()
                
                # Handle keyboard input - ONLY if keyboard visible
                elif keyboard.is_visible:
                    if active_field == "username":
                        new_username, should_submit = keyboard.handle_click((vmx, vmy), username, 15)
                        username = new_username
                    elif active_field == "password":
                        new_password, should_submit = keyboard.handle_click((vmx, vmy), password, 20)
                        password = new_password
        
        # Draw title
        title = title_font.render("LOGIN", True, get_rainbow_color())
        title_rect = title.get_rect(center=(VIRTUAL_W//2, 60))
        virtual_surface.blit(title, title_rect)
        
        # Draw input fields
        fields = [
            ("Username:", username_rect, username, active_field == "username"),
            ("Password:", password_rect, "*" * len(password), active_field == "password")
        ]
        
        for label, rect, text, is_active in fields:
            # Draw label
            label_surface = small_font.render(label, True, WHITE)
            virtual_surface.blit(label_surface, (rect.x, rect.y - 20))
            
            # Draw field
            color = (100, 150, 100) if is_active else (70, 70, 100)
            pygame.draw.rect(virtual_surface, color, rect, border_radius=5)
            pygame.draw.rect(virtual_surface, WHITE, rect, 2, border_radius=5)
            
            # Draw text
            if text:
                text_surface = small_font.render(text, True, WHITE)
                virtual_surface.blit(text_surface, (rect.x + 10, rect.y + 12))
        
        # Draw remember me checkbox
        checkbox_color = (100, 150, 100) if remember_me else (70, 70, 100)
        pygame.draw.rect(virtual_surface, checkbox_color, checkbox_rect, border_radius=3)
        pygame.draw.rect(virtual_surface, WHITE, checkbox_rect, 2, border_radius=3)
        
        if remember_me:
            # Draw checkmark
            pygame.draw.line(virtual_surface, WHITE, 
                           (checkbox_rect.x + 5, checkbox_rect.y + 10),
                           (checkbox_rect.x + 8, checkbox_rect.y + 13), 2)
            pygame.draw.line(virtual_surface, WHITE,
                           (checkbox_rect.x + 8, checkbox_rect.y + 13),
                           (checkbox_rect.x + 15, checkbox_rect.y + 6), 2)
        
        # Remember me label
        remember_text = small_font.render("Remember Me", True, WHITE)
        virtual_surface.blit(remember_text, (checkbox_rect.x + 30, checkbox_rect.y + 2))
        
        # Draw buttons
        for btn, label, hover_color in [(login_btn, "LOGIN", (100, 150, 100)), (register_btn, "REGISTER", (100, 100, 150))]:
            is_hovered = btn.collidepoint((vmx, vmy))
            color = hover_color if is_hovered else (70, 70, 100)
            
            pygame.draw.rect(virtual_surface, color, btn, border_radius=8)
            pygame.draw.rect(virtual_surface, WHITE, btn, 2, border_radius=8)
            
            btn_text = small_font.render(label, True, WHITE)
            text_rect = btn_text.get_rect(center=btn.center)
            virtual_surface.blit(btn_text, text_rect)
        
        # Draw KEYBOARD BUTTON
        kb_is_hovered = keyboard_btn.collidepoint((vmx, vmy))
        kb_color = (120, 120, 200) if kb_is_hovered else (80, 80, 150)
        if keyboard.is_visible:
            kb_color = (200, 120, 120)  # Red when keyboard is visible
        
        pygame.draw.rect(virtual_surface, kb_color, keyboard_btn, border_radius=8)
        pygame.draw.rect(virtual_surface, WHITE, keyboard_btn, 2, border_radius=8)
        
        kb_text = small_font.render("KEYBOARD", True, WHITE)
        kb_text_rect = kb_text.get_rect(center=keyboard_btn.center)
        virtual_surface.blit(kb_text, kb_text_rect)
        
        # Draw keyboard if visible
        keyboard.draw(virtual_surface, (vmx, vmy))
        
        draw_scaled_centered()
        clock.tick(60)

def main_menu():
    # Animation variables
    title_alpha = 0
    title_scale = 0.5
    particle_list = []
    glow_pulse = 0
    button_hover_scale = 1.0
    sword_angle = 0
    
    # Title animation
    text, idx, last, speed = "", 0, 0, 40
    full = "THE SLAYER"
    play_message = "TAP THE SCREEN TO PLAY"
    
    # Particle effect for background
    class Particle:
        def __init__(self):
            self.x = random.randint(0, VIRTUAL_W)
            self.y = random.randint(0, VIRTUAL_H)
            self.size = random.randint(1, 3)
            self.speed = random.uniform(0.5, 2)
            self.alpha = random.randint(100, 255)
            self.color = random.choice([
                (255, 215, 0),   # Gold
                (255, 140, 0),   # Dark orange
                (255, 69, 0),    # Red-orange
                (138, 43, 226)   # Purple
            ])
        
        def update(self):
            self.y += self.speed
            if self.y > VIRTUAL_H:
                self.y = 0
                self.x = random.randint(0, VIRTUAL_W)
        
        def draw(self, surface):
            s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, self.alpha), (self.size, self.size), self.size)
            surface.blit(s, (self.x - self.size, self.y - self.size))
    
    # Initialize particles (optimized count)
    for _ in range(30):  # Reduced from potential higher count
        particle_list.append(Particle())
    
    # Create music button
    music_button = MusicToggleButton(VIRTUAL_W - 60, 20, 40)
    
    # Sword decorations position
    sword_left_x = VIRTUAL_W // 2 - 200
    sword_right_x = VIRTUAL_W // 2 + 200
    sword_y = 120
    
    # Animation timer
    animation_start = pygame.time.get_ticks()
    
    while True:
        current_time = pygame.time.get_ticks()
        elapsed = current_time - animation_start
        
        # Draw background with darkened overlay
        virtual_surface.blit(background_image, (0, 0))
        
        # Dark overlay for better contrast
        dark_overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H), pygame.SRCALPHA)
        dark_overlay.fill((0, 0, 0, 120))
        virtual_surface.blit(dark_overlay, (0, 0))
        
        # Update and draw particles
        for particle in particle_list:
            particle.update()
            particle.draw(virtual_surface)
        
        # Glowing pulse effect
        glow_pulse = (math.sin(elapsed * 0.003) + 1) / 2  # 0 to 1
        
        # Animate title appearance
        if title_alpha < 255:
            title_alpha = min(255, title_alpha + 5)
        if title_scale < 1.0:
            title_scale = min(1.0, title_scale + 0.02)
        
        # Sword rotation animation
        sword_angle = math.sin(elapsed * 0.002) * 5  # Subtle swing
        
        # Draw decorative swords
        draw_decorative_sword(virtual_surface, sword_left_x, sword_y, -sword_angle, True)
        draw_decorative_sword(virtual_surface, sword_right_x, sword_y, sword_angle, False)
        
        # Animate title text typing
        if idx < len(full) and current_time - last > speed:
            text += full[idx]
            idx += 1
            last = current_time
        
        # Draw title with multiple layers for depth
        if text:
            # Outer glow
            glow_intensity = int(50 + glow_pulse * 50)
            for offset in range(8, 0, -2):
                glow_color = (255, 140, 0, glow_intensity // (offset // 2))
                glow_surf = pygame.Surface((VIRTUAL_W, 200), pygame.SRCALPHA)
                glow_text = title_font.render(text, True, glow_color[:3])
                glow_text.set_alpha(glow_color[3])
                glow_rect = glow_text.get_rect(center=(VIRTUAL_W//2 + offset//2, 120 + offset//2))
                
                # Scale effect
                if title_scale < 1.0:
                    w, h = glow_text.get_size()
                    scaled_w = int(w * title_scale)
                    scaled_h = int(h * title_scale)
                    glow_text = pygame.transform.scale(glow_text, (scaled_w, scaled_h))
                    glow_rect = glow_text.get_rect(center=(VIRTUAL_W//2, 120))
                
                virtual_surface.blit(glow_text, glow_rect)
            
            # Deep shadow
            shadow = title_font.render(text, True, (20, 0, 0))
            shadow.set_alpha(200)
            shadow_rect = shadow.get_rect(center=(VIRTUAL_W//2 + 4, 120 + 4))
            
            if title_scale < 1.0:
                w, h = shadow.get_size()
                shadow = pygame.transform.scale(shadow, (int(w * title_scale), int(h * title_scale)))
                shadow_rect = shadow.get_rect(center=(VIRTUAL_W//2 + 4, 120 + 4))
            
            virtual_surface.blit(shadow, shadow_rect)
            
            # Main title with rainbow/gradient effect
            rainbow = title_font.render(text, True, get_rainbow_color())
            rainbow.set_alpha(title_alpha)
            title_rect = rainbow.get_rect(center=(VIRTUAL_W//2, 120))
            
            if title_scale < 1.0:
                w, h = rainbow.get_size()
                rainbow = pygame.transform.scale(rainbow, (int(w * title_scale), int(h * title_scale)))
                title_rect = rainbow.get_rect(center=(VIRTUAL_W//2, 120))
            
            virtual_surface.blit(rainbow, title_rect)
            
            # Golden highlight on top
            highlight = title_font.render(text, True, (255, 255, 200))
            highlight.set_alpha(int(100 + glow_pulse * 50))
            highlight_rect = highlight.get_rect(center=(VIRTUAL_W//2, 118))
            
            if title_scale < 1.0:
                w, h = highlight.get_size()
                highlight = pygame.transform.scale(highlight, (int(w * title_scale), int(h * title_scale)))
                highlight_rect = highlight.get_rect(center=(VIRTUAL_W//2, 118))
            
            virtual_surface.blit(highlight, highlight_rect)
        
        # Get mouse position for hover effect
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Draw animated play button/message
        tap_rect = pygame.Rect(0, 0, 400, 70)
        tap_rect.center = (VIRTUAL_W//2, VIRTUAL_H//2 + 50)
        
        # Check hover
        is_hovering = tap_rect.collidepoint(vmx, vmy)
        if is_hovering:
            button_hover_scale = min(1.15, button_hover_scale + 0.05)
        else:
            button_hover_scale = max(1.0, button_hover_scale - 0.05)
        
        # Draw button background with glow
        button_surf = pygame.Surface((tap_rect.width, tap_rect.height), pygame.SRCALPHA)
        
        # Glow layers
        for i in range(3):
            glow_rect = pygame.Rect(i*4, i*4, tap_rect.width - i*8, tap_rect.height - i*8)
            alpha = int((150 - i * 30) * (1 + glow_pulse * 0.3))
            pygame.draw.rect(button_surf, (255, 140, 0, alpha), glow_rect, border_radius=15)
        
        # Main button
        main_button_rect = pygame.Rect(12, 12, tap_rect.width - 24, tap_rect.height - 24)
        pygame.draw.rect(button_surf, (139, 0, 0, 200), main_button_rect, border_radius=12)
        pygame.draw.rect(button_surf, (255, 215, 0, 255), main_button_rect, 3, border_radius=12)
        
        # Scale button on hover
        if button_hover_scale > 1.0:
            scaled_w = int(tap_rect.width * button_hover_scale)
            scaled_h = int(tap_rect.height * button_hover_scale)
            button_surf = pygame.transform.scale(button_surf, (scaled_w, scaled_h))
            scaled_rect = button_surf.get_rect(center=tap_rect.center)
            virtual_surface.blit(button_surf, scaled_rect)
        else:
            virtual_surface.blit(button_surf, tap_rect)
        
        # Draw button text
        tap_message = button_font.render(play_message, True, (255, 215, 0))
        tap_message_rect = tap_message.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H//2 + 50))
        
        # Text shadow
        tap_shadow = button_font.render(play_message, True, (0, 0, 0))
        tap_shadow_rect = tap_shadow.get_rect(center=(VIRTUAL_W//2 + 2, VIRTUAL_H//2 + 52))
        virtual_surface.blit(tap_shadow, tap_shadow_rect)
        virtual_surface.blit(tap_message, tap_message_rect)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check music button first
                music_button.handle_click((vmx, vmy))
                # Check if clicking play button
                if tap_rect.collidepoint(vmx, vmy):
                    login_screen()
        
        # Draw music button
        music_button.draw(virtual_surface)
        
        # Draw credit text with fade-in
        if elapsed > 1000:  # Show after 1 second
            credit_alpha = min(255, (elapsed - 1000) // 4)
            draw_credit_text(virtual_surface, credit_alpha)
        
        draw_scaled_centered()
        clock.tick(60)


def draw_decorative_sword(surface, x, y, angle, flip):
    """Draw decorative sword with glow effect"""
    # Create sword surface
    sword_surf = pygame.Surface((30, 150), pygame.SRCALPHA)
    
    # Blade
    blade_points = [(15, 0), (20, 100), (15, 100), (10, 100)]
    pygame.draw.polygon(sword_surf, (192, 192, 192), blade_points)
    pygame.draw.polygon(sword_surf, (255, 255, 255), blade_points, 2)
    
    # Guard
    pygame.draw.rect(sword_surf, (218, 165, 32), (5, 100, 20, 8))
    pygame.draw.rect(sword_surf, (255, 215, 0), (5, 100, 20, 8), 1)
    
    # Handle
    pygame.draw.rect(sword_surf, (139, 69, 19), (12, 108, 6, 30))
    
    # Pommel
    pygame.draw.circle(sword_surf, (218, 165, 32), (15, 145), 8)
    pygame.draw.circle(sword_surf, (255, 215, 0), (15, 145), 8, 2)
    
    # Rotate sword
    rotated = pygame.transform.rotate(sword_surf, angle)
    if flip:
        rotated = pygame.transform.flip(rotated, True, False)
    
    # Add glow
    glow_surf = pygame.Surface((rotated.get_width() + 20, rotated.get_height() + 20), pygame.SRCALPHA)
    glow_rect = rotated.get_rect(center=(glow_surf.get_width()//2, glow_surf.get_height()//2))
    
    # Glow layers
    for i in range(5, 0, -1):
        glow_copy = rotated.copy()
        glow_copy.set_alpha(30 // i)
        glow_offset = glow_rect.inflate(i * 4, i * 4)
        glow_surf.blit(glow_copy, glow_offset)
    
    glow_surf.blit(rotated, glow_rect)
    
    # Draw to main surface
    final_rect = glow_surf.get_rect(center=(x, y))
    surface.blit(glow_surf, final_rect)


def draw_credit_text(surface, alpha=255):
    """Draw credit text with specified alpha"""
    if 'credit_font' in globals():
        credit_text = credit_font.render("Game Version : 0.1", True, (200, 200, 200))
        credit_text.set_alpha(alpha)
        credit_rect = credit_text.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H - 30))
        
        # Shadow
        shadow = credit_font.render("Game Version : 0.1", True, (0, 0, 0))
        shadow.set_alpha(alpha // 2)
        shadow_rect = shadow.get_rect(center=(VIRTUAL_W//2 + 1, VIRTUAL_H - 29))
        
        surface.blit(shadow, shadow_rect)
        surface.blit(credit_text, credit_rect)
        
def choose_interface():
    characters = ["Samurai", "Soldier", "Magician"]
    selected_character = None
    character_previews = {}
    
    # Load preview sprites for each character
    for char in characters:
        try:
            idle_sheet = pygame.image.load(f"assets/{char}/Idle.png").convert_alpha()
            frame_count = character_frame_counts[char]["Idle"]
            frame_width = idle_sheet.get_width() // frame_count
            preview = idle_sheet.subsurface(pygame.Rect(0, 0, frame_width, idle_sheet.get_height()))
            character_previews[char] = pygame.transform.scale(preview, (120, 120))
        except Exception as e:
            print(f"Error loading preview for {char}: {e}")
            placeholder = pygame.Surface((120, 120))
            placeholder.fill((100, 100, 100))
            character_previews[char] = placeholder
    
    # Character selection rectangles
    char_rects = {}
    start_x = 150
    for i, char in enumerate(characters):
        x = start_x + i * 200
        y = 200
        char_rects[char] = pygame.Rect(x, y, 150, 180)
    
    select_button = pygame.Rect(VIRTUAL_W//2 - 100, 450, 200, 60)
    
    while True:
        virtual_surface.fill((30, 30, 60))
        
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check character selection
                for char, rect in char_rects.items():
                    if rect.collidepoint((vmx, vmy)):
                        selected_character = char
                
                # Check select button
                if select_button.collidepoint((vmx, vmy)) and selected_character:
                    save_interface(selected_character)  # Save interface yang dipilih
                    new_screen(selected_character)
                    return
        
        # Draw title
        title = title_font.render("Choose Your Interface", True, get_rainbow_color())
        virtual_surface.blit(title, title.get_rect(center=(VIRTUAL_W // 2, 100)))
        
        # Draw character options
        for char, rect in char_rects.items():
            if char == selected_character:
                border_color = SELECTED_COLOR
                bg_color = (60, 80, 60)
            elif rect.collidepoint((vmx, vmy)):
                border_color = HOVER_COLOR
                bg_color = (50, 50, 80)
            else:
                border_color = BUTTON_COLOR
                bg_color = (40, 40, 60)
            
            pygame.draw.rect(virtual_surface, bg_color, rect, border_radius=10)
            pygame.draw.rect(virtual_surface, border_color, rect, 3, border_radius=10)
            
            if char in character_previews:
                preview_rect = character_previews[char].get_rect(center=(rect.centerx, rect.y + 70))
                virtual_surface.blit(character_previews[char], preview_rect.topleft)
            
            name_text = small_font.render(char, True, WHITE)
            name_rect = name_text.get_rect(center=(rect.centerx, rect.y + 160))
            virtual_surface.blit(name_text, name_rect)
        
        # Draw select button
        if selected_character:
            selection_text = button_font.render("Selected Interface", True, SELECTED_COLOR)
            virtual_surface.blit(selection_text, selection_text.get_rect(center=(VIRTUAL_W // 2, 400)))
            
            button_color = HOVER_COLOR if select_button.collidepoint((vmx, vmy)) else SELECTED_COLOR
            pygame.draw.rect(virtual_surface, button_color, select_button, border_radius=10)
            select_text = button_font.render("SELECT", True, WHITE)
            virtual_surface.blit(select_text, select_text.get_rect(center=select_button.center))
        else:
            instruction_text = small_font.render("Click on a character to select interface", True, WHITE)
            virtual_surface.blit(instruction_text, instruction_text.get_rect(center=(VIRTUAL_W // 2, 400)))
        
        draw_scaled_centered()
        clock.tick(30)
                
def maintenance_screen():
    """Display maintenance screen when game is under maintenance"""
    # Load maintenance background (sama seperti menu background)
    try:
        maintenance_bg = pygame.image.load("assets/menubg.png").convert()
        maintenance_bg = pygame.transform.smoothscale(maintenance_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        maintenance_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        maintenance_bg.fill((30, 30, 60))
    
    # Create a darker overlay for maintenance feel
    overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 0))
    
    # Maintenance check interval (10 seconds)
    last_maintenance_check = 0
    maintenance_check_interval = 10000
    
    # Animation for maintenance text
    pulse_timer = 0
    pulse_direction = 1
    
    while True:
        current_time = pygame.time.get_ticks()
        
        # Check maintenance status periodically
        if current_time - last_maintenance_check > maintenance_check_interval:
            if not is_maintenance_active():
                return  # Exit maintenance screen and go to main menu
            last_maintenance_check = current_time
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F5:  # F5 to manually check maintenance status
                    if not is_maintenance_active():
                        return
        
        # Draw background
        virtual_surface.blit(maintenance_bg, (0, 0))
        virtual_surface.blit(overlay, (0, 0))
        
        # Update pulse animation
        pulse_timer += clock.get_time()
        if pulse_timer >= 30:  # Smooth animation
            pulse_timer = 0
            pulse_alpha = abs(pygame.time.get_ticks() % 2000 - 1000) / 1000.0
        
        # Draw maintenance message box
        box_width = min(700, VIRTUAL_W - 40)
        box_height = 400
        box_x = (VIRTUAL_W - box_width) // 2
        box_y = (VIRTUAL_H - box_height) // 2
        
        maintenance_box = pygame.Rect(box_x, box_y, box_width, box_height)
        
        # Draw box with glowing effect
        pygame.draw.rect(virtual_surface, (40, 40, 60), maintenance_box, border_radius=20)
        pygame.draw.rect(virtual_surface, (255, 165, 0), maintenance_box, 4, border_radius=20)
        
        # Draw maintenance title with rainbow effect
        title_text = title_font.render("UNDER MAINTENANCE", True, get_rainbow_color())
        title_rect = title_text.get_rect(center=(VIRTUAL_W//2, box_y + 80))
        virtual_surface.blit(title_text, title_rect)
        
        # Draw maintenance message
        messages = [
            "The game is currently under maintenance.",
            "",
            "Please check back later!",
            "",
            "Follow us for updates:",
            "Discord: https://discord.gg/scNgmKpFBE",
            "Youtube: @kodokers-channel",
            ""
        ]
        
        for i, message in enumerate(messages):
            if message:  # Skip empty lines for spacing
                if "Follow us" in message or "Discord" in message or "Twitter" in message:
                    color = (100, 200, 255)  # Light blue for social media
                elif "Press F5" in message:
                    # Pulsing effect for F5 instruction
                    alpha = int(255 * (0.5 + 0.5 * abs(pygame.time.get_ticks() % 2000 - 1000) / 1000.0))
                    color = (255, 255, 100, alpha)  # Yellow with pulsing
                    text_surface = small_font.render(message, True, (255, 255, 100))
                    text_surface.set_alpha(alpha)
                else:
                    color = WHITE
                
                if "Press F5" not in message:
                    text_surface = small_font.render(message, True, color)
                
                text_rect = text_surface.get_rect(center=(VIRTUAL_W//2, box_y + 150 + i * 25))
                virtual_surface.blit(text_surface, text_rect)
        
        # Draw animated dots
        dots_text = "Checking for updates"
        dot_count = (pygame.time.get_ticks() // 500) % 4
        animated_text = dots_text + "." * dot_count
        
        dots_surface = small_font.render(animated_text, True, (150, 150, 150))
        dots_rect = dots_surface.get_rect(center=(VIRTUAL_W//2, box_y + box_height - 50))
        virtual_surface.blit(dots_surface, dots_rect)
        
        draw_scaled_centered()
        clock.tick(60)

def check_internet_connection():
    """Check if internet connection is available"""
    try:
        # Try to connect to Google DNS with a very short timeout
        import socket
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except:
        return False

def internet_connection_screen():
    """Display screen when no internet connection is available"""
    # Load background
    try:
        connection_bg = pygame.image.load("assets/menubg.png").convert()
        connection_bg = pygame.transform.smoothscale(connection_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        connection_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        connection_bg.fill((30, 30, 60))
    
    # Create overlay
    overlay = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 0))
    
    # Retry button
    retry_button = pygame.Rect(VIRTUAL_W//2 - 100, VIRTUAL_H//2 + 100, 200, 50)
    
    # Animation for connection status
    pulse_timer = 0
    
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
                ox = (SCREEN_W - VIRTUAL_W * scale) / 2
                oy = (SCREEN_H - VIRTUAL_H * scale) / 2
                vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
                
                if retry_button.collidepoint((vmx, vmy)):
                    # Check internet connection when retry is clicked
                    if check_internet_connection():
                        return True  # Connection successful, exit this screen
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Allow retry with Enter or Space key
                    if check_internet_connection():
                        return True
        
        # Get mouse position
        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
        
        # Draw background
        virtual_surface.blit(connection_bg, (0, 0))
        virtual_surface.blit(overlay, (0, 0))
        
        # Update pulse animation
        pulse_timer += clock.get_time()
        pulse_alpha = abs(pygame.time.get_ticks() % 2000 - 1000) / 1000.0
        
        # Draw connection message box
        box_width = min(600, VIRTUAL_W - 40)
        box_height = 350
        box_x = (VIRTUAL_W - box_width) // 2
        box_y = (VIRTUAL_H - box_height) // 2
        
        connection_box = pygame.Rect(box_x, box_y, box_width, box_height)
        
        # Draw box with glowing effect
        pygame.draw.rect(virtual_surface, (40, 40, 60), connection_box, border_radius=20)
        pygame.draw.rect(virtual_surface, (255, 100, 100), connection_box, 4, border_radius=20)
        
        # Draw connection title with pulsing effect
        title_alpha = int(255 * (0.7 + 0.3 * pulse_alpha))
        title_color = (255, 100, 100, title_alpha)
        medium_font = pygame.font.Font(None, 32)  # Ukuran 32 pixel
        title_text = medium_font.render("NO INTERNET CONNECTION", True, (255, 100, 100))
        title_text.set_alpha(title_alpha)
        title_rect = title_text.get_rect(center=(VIRTUAL_W//2, box_y + 70))
        virtual_surface.blit(title_text, title_rect)

        # Draw connection message
        messages = [
            "",
            "You need an internet connection to play this game.",
            "",
            "Please check your connection and try again:",
            "",
            "• Check your WiFi or mobile data",
            "• Make sure you're connected to the internet",
            "• Try moving to a better signal area",
            ""
        ]
        
        for i, message in enumerate(messages):
            if message:
                if message.startswith("•"):
                    color = (200, 200, 255)  # Light blue for bullet points
                    text_surface = small_font.render(message, True, color)
                else:
                    color = WHITE
                    text_surface = small_font.render(message, True, color)
                
                text_rect = text_surface.get_rect(center=(VIRTUAL_W//2, box_y + 110 + i * 22))
                virtual_surface.blit(text_surface, text_rect)
        
        # Draw retry button with hover effect
        button_color = HOVER_COLOR if retry_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, button_color, retry_button, border_radius=10)
        pygame.draw.rect(virtual_surface, WHITE, retry_button, 2, border_radius=10)
        
        retry_text = button_font.render("RETRY", True, WHITE)
        retry_rect = retry_text.get_rect(center=retry_button.center)
        virtual_surface.blit(retry_text, retry_rect)
        
        # Draw animated connecting dots
        dots_text = ""
        dot_count = (pygame.time.get_ticks() // 500) % 4
        animated_text = dots_text + "." * dot_count
        
        dots_surface = small_font.render(animated_text, True, (150, 150, 150))
        dots_rect = dots_surface.get_rect(center=(VIRTUAL_W//2, box_y + box_height - 40))
        virtual_surface.blit(dots_surface, dots_rect)
        
        draw_scaled_centered()
        clock.tick(60)

def is_maintenance_active():
    """Check if maintenance is active - optimized with timeout"""
    try:
        with urllib.request.urlopen("https://mhtpsg.github.io/theslayer/button_timer_config.json", timeout=2) as response:
            data = json.loads(response.read().decode())
            return data.get("maintenance", False)
    except:
        return False  # If can't check, assume no maintenance

def check_maintenance_and_start():
    """Check maintenance status before starting main menu"""
    # First check internet connection
    if not check_internet_connection():
        internet_connection_screen()
    
    # Show loading screen while checking
    virtual_surface.fill((30, 30, 60))
    
    # Draw loading message
    loading_text = button_font.render("Checking game status...", True, WHITE)
    loading_rect = loading_text.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H//2))
    virtual_surface.blit(loading_text, loading_rect)
    
    # Draw loading animation
    dots = "" * ((pygame.time.get_ticks() // 300) % 4)
    dots_text = small_font.render(dots, True, WHITE)
    dots_rect = dots_text.get_rect(center=(VIRTUAL_W//2, VIRTUAL_H//2 + 40))
    virtual_surface.blit(dots_text, dots_rect)
    
    draw_scaled_centered()
    
    # Check maintenance status
    if is_maintenance_active():
        maintenance_screen()
    
    # If we reach here, maintenance is over or not active
    return

def require_internet_connection(func):
    """Decorator to require internet connection for functions"""
    def wrapper(*args, **kwargs):
        if not check_internet_connection():
            internet_connection_screen()
        return func(*args, **kwargs)
    return wrapper

def new_screen(selected_interface_char=None):
    # First check maintenance status and internet connection
    check_maintenance_and_start()
    
    # Load menu background
    try:
        menu_bg = pygame.image.load("assets/menubg.png").convert()
        menu_bg = pygame.transform.smoothscale(menu_bg, (VIRTUAL_W, VIRTUAL_H))
    except:
        menu_bg = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        menu_bg.fill((30, 30, 60))

    # Load interface character animation if provided
    interface_anims = None
    interface_action = "Run"
    interface_idx = 0
    interface_timer = 0
    show_animation_menu = False
    
    # Button timer configuration
    button_config = {}
    config_last_update = 0
    config_cache_duration = 300000  # 5 minutes in milliseconds (for fallback only)
    
    # Default configuration (fallback) - UPDATED with maintenance, summer event, and tournament
    default_config = {
        "maintenance": False,  # Default maintenance status
        "hero_knight_boss": {"start_hour": 6, "end_hour": 18, "name": "Hero Knight (BOSS)"},
        "investment": {"start_hour": 6, "end_hour": 21, "name": "Investment"},
        "expedition": {"start_hour": 18, "end_hour": 23, "name": "Expedition"},
        "character_fusion": {"start_hour": 20, "end_hour": 22, "name": "Character Fusion"},
        "tournament": {
            "time_slots": [
                {"start_hour": 16, "end_hour": 18},  # 4 PM - 6 PM
                {"start_hour": 21, "end_hour": 23}   # 9 PM - 11 PM
            ],
            "name": "Tournament"
        },
        "summer_event": {
            "start_hour": 6, 
            "end_hour": 23, 
            "name": "Summer Event",
            "date_restrictions": {
                "2025": {"start_month": 8, "start_day": 19, "end_month": 11, "end_day": 19},
                "default": {"start_month": 7, "start_day": 1, "end_month": 10, "end_day": 1}
            }
        }
    }
    
    # Cache for button availability to reduce calculations
    button_availability_cache = {}
    last_minute_checked = -1
    
    def load_button_config():
        nonlocal button_config, config_last_update
        current_time = pygame.time.get_ticks()
        
        # Check internet connection before trying to load config
        if not check_internet_connection():
            return False
        
        # Only use cache duration for network requests, always allow fresh data
        try:
            with urllib.request.urlopen("https://mhtpsg.github.io/theslayer/button_timer_config.json", timeout=1) as response:
                data = json.loads(response.read().decode())
                button_config = data
                config_last_update = current_time
                return True
        except:
            if not button_config:  # Only use default if no config loaded yet
                button_config = default_config
                config_last_update = current_time
            return False
    
    def is_summer_event_date_available():
        """Check if current date falls within Summer Event period"""
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        if "summer_event" not in button_config:
            return True
            
        config = button_config["summer_event"]
        if "date_restrictions" not in config:
            return True
            
        date_config = config["date_restrictions"]
        
        # Check for specific year configuration (like 2025)
        if str(current_year) in date_config:
            year_config = date_config[str(current_year)]
        else:
            # Use default configuration for other years
            year_config = date_config.get("default", {})
        
        if not year_config:
            return True
            
        start_month = year_config.get("start_month", 1)
        start_day = year_config.get("start_day", 1)
        end_month = year_config.get("end_month", 12)
        end_day = year_config.get("end_day", 31)
        
        # Create date objects for comparison
        try:
            start_date = datetime(current_year, start_month, start_day)
            end_date = datetime(current_year, end_month, end_day)
            current_date = datetime(current_year, current_month, current_day)
            
            return start_date <= current_date <= end_date
        except ValueError:
            # Invalid date configuration, allow access
            return True
    
    def is_button_available(button_key):
        if button_key not in button_config:
            return True
        
        # Special handling for summer event
        if button_key == "summer_event":
            if not is_summer_event_date_available():
                return False
        
        # Use cached result if within the same minute
        current_minute = datetime.now().replace(second=0, microsecond=0)
        cache_key = (button_key, current_minute)
        
        if cache_key in button_availability_cache:
            return button_availability_cache[cache_key]
        
        config = button_config[button_key]
        current_hour = datetime.now().hour
        
        # Special handling for tournament with multiple time slots
        if button_key == "tournament" and "time_slots" in config:
            available = False
            for slot in config["time_slots"]:
                start_hour = slot["start_hour"]
                end_hour = slot["end_hour"]
                
                if start_hour <= end_hour:
                    if start_hour <= current_hour <= end_hour:
                        available = True
                        break
                else:
                    # Handle overnight period
                    if current_hour >= start_hour or current_hour <= end_hour:
                        available = True
                        break
        else:
            # Regular single time slot handling
            start_hour = config["start_hour"]
            end_hour = config["end_hour"]
            
            if start_hour <= end_hour:
                available = start_hour <= current_hour <= end_hour
            else:
                # Handle overnight period (like 23-5)
                available = current_hour >= start_hour or current_hour <= end_hour
        
        # Cache the result
        button_availability_cache[cache_key] = available
        
        # Clean old cache entries (keep only last 2 minutes)
        keys_to_remove = [k for k in button_availability_cache.keys() 
                         if k[1] < current_minute - timedelta(minutes=2)]
        for key in keys_to_remove:
            del button_availability_cache[key]
        
        return available
        
    def get_next_available_time(button_key):
        if button_key not in button_config:
            return ""
        
        # Special handling for summer event
        if button_key == "summer_event":
            if not is_summer_event_date_available():
                return get_next_summer_event_date()
        
        config = button_config[button_key]
        now = datetime.now()
        current_hour = now.hour
        
        # Special handling for tournament with multiple time slots
        if button_key == "tournament" and "time_slots" in config:
            # Check if currently in any available slot
            for slot in config["time_slots"]:
                start_hour = slot["start_hour"]
                end_hour = slot["end_hour"]
                
                if start_hour <= end_hour:
                    if start_hour <= current_hour <= end_hour:
                        return "Available now"
                else:
                    if current_hour >= start_hour or current_hour <= end_hour:
                        return "Available now"
            
            # Find next available slot
            next_times = []
            for slot in config["time_slots"]:
                start_hour = slot["start_hour"]
                
                if current_hour < start_hour:
                    # Same day
                    next_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                    next_times.append(next_time)
                else:
                    # Next day
                    next_time = (now + timedelta(days=1)).replace(hour=start_hour, minute=0, second=0, microsecond=0)
                    next_times.append(next_time)
            
            # Return the earliest next time
            if next_times:
                earliest = min(next_times)
                return earliest.strftime("%H:%M")
        else:
            # Regular single time slot handling
            start_hour = config["start_hour"]
            end_hour = config["end_hour"]
            
            if start_hour <= end_hour:
                if current_hour < start_hour:
                    next_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                elif current_hour > end_hour:
                    next_time = (now + timedelta(days=1)).replace(hour=start_hour, minute=0, second=0, microsecond=0)
                else:
                    return "Available now"
            else:
                if end_hour < current_hour < start_hour:
                    next_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
                else:
                    return "Available now"
            
            return next_time.strftime("%H:%M")
        
        return ""
    
    def get_next_summer_event_date():
        """Get the next available date for Summer Event"""
        now = datetime.now()
        current_year = now.year
        
        if "summer_event" not in button_config:
            return "Check configuration"
            
        config = button_config["summer_event"]
        if "date_restrictions" not in config:
            return "Check configuration"
            
        date_config = config["date_restrictions"]
        
        # Check if we're in 2025 and past the 2025 period
        if current_year == 2025:
            year_config = date_config.get("2025", {})
            if year_config:
                end_month = year_config.get("end_month", 11)
                end_day = year_config.get("end_day", 19)
                
                # If past 2025 period, show next year's period
                if now.month > end_month or (now.month == end_month and now.day > end_day):
                    next_year = current_year + 1
                    default_config_dates = date_config.get("default", {})
                    if default_config_dates:
                        start_month = default_config_dates.get("start_month", 7)
                        start_day = default_config_dates.get("start_day", 1)
                        return f"July {start_day}, {next_year}"
                
                # If before 2025 period, show 2025 start date
                if now.month < year_config.get("start_month", 8) or \
                   (now.month == year_config.get("start_month", 8) and now.day < year_config.get("start_day", 19)):
                    return f"August {year_config.get('start_day', 19)}, {current_year}"
        
        # For years after 2025 or if not in valid period
        default_config_dates = date_config.get("default", {})
        if default_config_dates:
            start_month = default_config_dates.get("start_month", 7)
            start_day = default_config_dates.get("start_day", 1)
            end_month = default_config_dates.get("end_month", 10)
            end_day = default_config_dates.get("end_day", 1)
            
            # If before the period this year
            if now.month < start_month or (now.month == start_month and now.day < start_day):
                return f"July {start_day}, {current_year}"
            # If past the period this year
            elif now.month > end_month or (now.month == end_month and now.day > end_day):
                return f"July {start_day}, {current_year + 1}"
        
        return "Check configuration"
                     
    def show_unavailable_message(button_name, button_key):
        if button_key == "summer_event" and not is_summer_event_date_available():
            next_date = get_next_summer_event_date()
            message = f"Summer Event is not currently active. Next available: {next_date}"
        elif button_key == "tournament" and "time_slots" in button_config[button_key]:
            # Special message for tournament with multiple time slots
            config = button_config[button_key]
            time_slots_text = []
            for slot in config["time_slots"]:
                start_hour = slot["start_hour"]
                end_hour = slot["end_hour"]
                time_slots_text.append(f"{start_hour:02d}:00 - {end_hour:02d}:00")
            
            slots_str = " and ".join(time_slots_text)
            next_time = get_next_available_time(button_key)
            message = f"{button_name} is only available during: {slots_str}. Next available: {next_time}"
        else:
            next_time = get_next_available_time(button_key)
            if next_time != "Available now":
                config = button_config[button_key]
                start_hour = config["start_hour"]
                end_hour = config["end_hour"]
                
                if start_hour <= end_hour:
                    time_range = f"{start_hour:02d}:00 - {end_hour:02d}:00"
                else:
                    time_range = f"{start_hour:02d}:00 - {end_hour:02d}:00 (next day)"
                
                message = f"{button_name} is only available from {time_range}. Next available: {next_time}"
            else:
                message = f"{button_name} is currently unavailable."
        
        show_message_popup(message)
    
    def show_message_popup(message):
        # Create popup overlay
        popup_surface = pygame.Surface((VIRTUAL_W, VIRTUAL_H))
        popup_surface.set_alpha(180)
        popup_surface.fill((0, 0, 0))
        
        # Message box
        box_width = min(600, VIRTUAL_W - 40)
        box_height = 200
        box_x = (VIRTUAL_W - box_width) // 2
        box_y = (VIRTUAL_H - box_height) // 2
        
        message_box = pygame.Rect(box_x, box_y, box_width, box_height)
        ok_button = pygame.Rect(box_x + box_width//2 - 50, box_y + box_height - 60, 100, 40)
        
        popup_running = True
        while popup_running:
            # Draw main screen behind popup
            virtual_surface.blit(menu_bg, (0, 0))
            
            mx, my = pygame.mouse.get_pos()
            scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
            ox = (SCREEN_W - VIRTUAL_W * scale) / 2
            oy = (SCREEN_H - VIRTUAL_H * scale) / 2
            vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit_game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if ok_button.collidepoint((vmx, vmy)):
                        popup_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                        popup_running = False
            
            # Draw popup
            virtual_surface.blit(popup_surface, (0, 0))
            pygame.draw.rect(virtual_surface, (40, 40, 60), message_box, border_radius=15)
            pygame.draw.rect(virtual_surface, WHITE, message_box, 3, border_radius=15)
            
            # Draw message text (word wrapped)
            words = message.split(' ')
            lines = []
            current_line = ""
            max_width = box_width - 40
            
            for word in words:
                test_line = current_line + word + " " if current_line else word + " "
                text_width = small_font.size(test_line)[0]
                if text_width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.strip())
                        current_line = word + " "
                    else:
                        lines.append(word)
                        current_line = ""
            if current_line:
                lines.append(current_line.strip())
            
            # Draw lines
            for i, line in enumerate(lines):
                text_surface = small_font.render(line, True, WHITE)
                text_rect = text_surface.get_rect(center=(VIRTUAL_W//2, box_y + 40 + i * 25))
                virtual_surface.blit(text_surface, text_rect)
            
            # Draw OK button
            button_color = HOVER_COLOR if ok_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, button_color, ok_button, border_radius=8)
            ok_text = button_font.render("OK", True, WHITE)
            virtual_surface.blit(ok_text, ok_text.get_rect(center=ok_button.center))
            
            draw_scaled_centered()
            clock.tick(60)
    
    # Modified callback functions with internet check
    def hero_knight_boss_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        if is_button_available("hero_knight_boss"):
            hero_knight_boss()
        else:
            show_unavailable_message("Hero Knight (BOSS)", "hero_knight_boss")
    
    def investment_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        if is_button_available("investment"):
            investment()
        else:
            show_unavailable_message("Investment", "investment")
    
    def expedition_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        if is_button_available("expedition"):
            expedition()
        else:
            show_unavailable_message("Expedition", "expedition")
    
    def character_fusion_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        if is_button_available("character_fusion"):
            character_fusion()
        else:
            show_unavailable_message("Character Fusion", "character_fusion")
    
    def summer_event_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        if is_button_available("summer_event"):
            summer_event()
        else:
            show_unavailable_message("Summer Event", "summer_event")
    
    # Add internet check to all other button functions
    def start_game_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        start_game()
    
    def training_mode_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        training_mode()
    
    def open_settings_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        open_settings()
    
    def story_mode_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        story_mode()
    
    def shop_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        shop()
    
    def tournament_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        if is_button_available("tournament"):
            tournament()
        else:
            show_unavailable_message("Tournament", "tournament")
    
    def dungeon_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        dungeon()
    
    def gacha_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        gacha()
    
    def daily_login_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        daily_login()
    
    def redeem_code_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        redeem_code()
        
    def endless_tower_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        endless_tower()
    
    def battlepass_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        battlepass()
    
    def character_gallery_with_check():
        if not check_internet_connection():
            internet_connection_screen()
            return
        character_gallery()
    
    if selected_interface_char:
        try:
            actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3"]
            interface_anims = load_animation_frames(selected_interface_char, actions, character_frame_counts[selected_interface_char])
        except Exception as e:
            print(f"Error loading interface character: {e}")

    # Define buttons for each page with internet check
    buttons_page_1 = [
        Button("assets/1v1.png", "1 vs 1", VIRTUAL_W//2 - 160, 200, 320, 70, start_game_with_check),
        Button("assets/training.png", "Training Mode", VIRTUAL_W//2 - 160, 300, 320, 70, training_mode_with_check),
        Button("assets/settings.png", "Settings", VIRTUAL_W//2 - 160, 400, 320, 70, open_settings_with_check),
        Button("assets/exit.png", "Exit", VIRTUAL_W//2 - 160, 500, 320, 70, exit_game),
    ]

    buttons_page_2 = [
        Button("assets/story_mode.png", "Story Mode", VIRTUAL_W//2 - 160, 200, 320, 70, story_mode_with_check),
        Button("assets/shop.png", "Shop", VIRTUAL_W//2 - 160, 300, 320, 70, shop_with_check),
        Button("assets/tournament.png", "Tournament", VIRTUAL_W//2 - 160, 400, 320, 70, tournament_with_check),
        Button("assets/dungeon.png", "Dungeon", VIRTUAL_W//2 - 160, 500, 320, 70, dungeon_with_check),
    ]
    
    buttons_page_3 = [
        Button("assets/katana.png", "Hero Knight (BOSS)", VIRTUAL_W//2 - 160, 200, 320, 70, hero_knight_boss_with_check),
        Button("assets/gacha.png", "Gacha", VIRTUAL_W//2 - 160, 300, 320, 70, gacha_with_check),
        Button("assets/daily_login.png", "Daily Login", VIRTUAL_W//2 - 160, 400, 320, 70, daily_login_with_check),
        Button("assets/redeem.png", "Redeem Code", VIRTUAL_W//2 - 160, 500, 320, 70, redeem_code_with_check),
    ]

    buttons_page_4 = [
        Button("assets/summer_event.png", "Summer Event", VIRTUAL_W//2 - 160, 200, 320, 70, summer_event_with_check),
        Button("assets/endless_tower.png", "Endless Tower", VIRTUAL_W//2 - 160, 300, 320, 70, endless_tower_with_check),
        Button("assets/investment.png", "Investment", VIRTUAL_W//2 - 160, 400, 320, 70, investment_with_check),
        Button("assets/expedition.png", "Expedition", VIRTUAL_W//2 - 160, 500, 320, 70, expedition_with_check),
    ]

    buttons_page_5 = [
        Button("assets/battlepass.png", "Battlepass", VIRTUAL_W//2 - 160, 200, 320, 70, battlepass_with_check),
        Button("assets/character_gallery.png", "Character Gallery", VIRTUAL_W//2 - 160, 300, 320, 70, character_gallery_with_check),
        Button("assets/character_fusion.png", "Character Fusion", VIRTUAL_W//2 - 160, 400, 320, 70, character_fusion_with_check),
        #Button("assets/button12.png", "BUTTON 12", VIRTUAL_W//2 - 160, 500, 320, 70, None),
    ]

    buttons_page_6 = [
        #Button("assets/button13.png", "BUTTON 13", VIRTUAL_W//2 - 160, 200, 320, 70, None),
        #Button("assets/button14.png", "BUTTON 14", VIRTUAL_W//2 - 160, 300, 320, 70, None),
        #Button("assets/button15.png", "BUTTON 15", VIRTUAL_W//2 - 160, 400, 320, 70, None),
        #Button("assets/button16.png", "BUTTON 16", VIRTUAL_W//2 - 160, 500, 320, 70, None),
    ]

    buttons_page_7 = [
        #Button("assets/button17.png", "BUTTON 17", VIRTUAL_W//2 - 160, 200, 320, 70, None),
        #Button("assets/button18.png", "BUTTON 18", VIRTUAL_W//2 - 160, 300, 320, 70, None),
        #Button("assets/button19.png", "BUTTON 19", VIRTUAL_W//2 - 160, 400, 320, 70, None),
        #Button("assets/button20.png", "BUTTON 20", VIRTUAL_W//2 - 160, 500, 320, 70, None),
    ]

    buttons_page_8 = [
        #Button("assets/button21.png", "BUTTON 21", VIRTUAL_W//2 - 160, 200, 320, 70, None),
        #Button("assets/button22.png", "BUTTON 22", VIRTUAL_W//2 - 160, 300, 320, 70, None),
        #Button("assets/button23.png", "BUTTON 23", VIRTUAL_W//2 - 160, 400, 320, 70, None),
        #Button("assets/button24.png", "BUTTON 24", VIRTUAL_W//2 - 160, 500, 320, 70, None),
    ]

    buttons_page_9 = [
        #Button("assets/button25.png", "BUTTON 25", VIRTUAL_W//2 - 160, 200, 320, 70, None),
        #Button("assets/button26.png", "BUTTON 26", VIRTUAL_W//2 - 160, 300, 320, 70, None),
        #Button("assets/button27.png", "BUTTON 27", VIRTUAL_W//2 - 160, 400, 320, 70, None),
        #Button("assets/button28.png", "BUTTON 28", VIRTUAL_W//2 - 160, 500, 320, 70, None),
    ]

    buttons_page_10 = [
        #Button("assets/button29.png", "BUTTON 29", VIRTUAL_W//2 - 160, 200, 320, 70, None),
        #Button("assets/button30.png", "BUTTON 30", VIRTUAL_W//2 - 160, 300, 320, 70, None),
        #Button("assets/button31.png", "BUTTON 31", VIRTUAL_W//2 - 160, 400, 320, 70, None),
        #Button("assets/button32.png", "BUTTON 32", VIRTUAL_W//2 - 160, 500, 320, 70, None),
    ]
    
    # Load initial button configuration
    load_button_config()
    
    current_page = 1
    # Posisi button next dan previous bertumpuk di kanan
    next_button = Button("assets/next.png", "Next", VIRTUAL_W - 160, VIRTUAL_H - 100, 140, 50, None)
    previous_button = Button("assets/previous.png", "Prev", VIRTUAL_W - 160, VIRTUAL_H - 160, 140, 50, None)
    
    # Animation selector button
    select_animation_button = pygame.Rect(20, VIRTUAL_H - 100, 180, 40)
    # Change interface button
    change_interface_button = pygame.Rect(20, VIRTUAL_H - 50, 180, 40)
    
    # Animation menu rectangles
    animation_actions = ["Idle", "Run", "Jump", "Shield", "Attack_1", "Attack_2", "Attack_3"]
    animation_buttons = {}
    for i, action in enumerate(animation_actions):
        x = 220
        y = 150 + i * 45
        animation_buttons[action] = pygame.Rect(x, y, 200, 35)

    # Timer for periodic config updates - reduced frequency
    last_config_update_attempt = 0
    config_update_interval = 30000  # Try to update config every 30 seconds instead of 5 minutes
    
    # Maintenance check timer
    last_maintenance_check = 0
    maintenance_check_interval = 60000  # Check maintenance every 60 seconds during gameplay
    
    # Internet connection check timer
    last_internet_check = 0
    internet_check_interval = 10000  # Check internet every 10 seconds during gameplay

    while True:
        current_time = pygame.time.get_ticks()
        current_minute = datetime.now().minute
        
        # Periodic internet connection check during gameplay
        if current_time - last_internet_check > internet_check_interval:
            if not check_internet_connection():
                internet_connection_screen()
                # After reconnecting, reload config
                load_button_config()
            last_internet_check = current_time
        
        # Periodic maintenance check during gameplay
        if current_time - last_maintenance_check > maintenance_check_interval:
            if is_maintenance_active():
                maintenance_screen()  # Go to maintenance screen if maintenance is active
                # After returning from maintenance, reload config
                load_button_config()
            last_maintenance_check = current_time
        
        # Periodic config update (but don't block if network is slow)
        if current_time - last_config_update_attempt > config_update_interval:
            load_button_config()  # This now has timeout=1 so it won't lag
            last_config_update_attempt = current_time

        # Clear availability cache if minute changed (for real-time updates)
        if last_minute_checked != current_minute:
            button_availability_cache.clear()
            last_minute_checked = current_minute

        virtual_surface.blit(menu_bg, (0, 0))
        
        # Update interface character animation
        if interface_anims:
            interface_timer += clock.get_time()
            if interface_timer >= 160:
                interface_timer = 0
                if interface_anims[interface_action]:
                    interface_idx += 1
                    if interface_idx >= len(interface_anims[interface_action]):
                        interface_idx = 0
        
        # Draw interface character on the left
        if interface_anims and interface_anims[interface_action]:
            char_sprite = pygame.transform.scale(interface_anims[interface_action][interface_idx], (200, 200))
            char_pos = (10, VIRTUAL_H//2 - 125)  # Left side position
            virtual_surface.blit(char_sprite, char_pos)
            
            # Draw character name below with spacing
            char_name_text = button_font.render(f"{selected_interface_char}", True, WHITE)
            name_rect = char_name_text.get_rect(center=(char_pos[0] + 100, char_pos[1] + 220))
            virtual_surface.blit(char_name_text, name_rect)
            
            # Draw "Interface:" text below character name
            interface_label = small_font.render("Interface:", True, WHITE)
            interface_rect = interface_label.get_rect(center=(char_pos[0] + 100, char_pos[1] + 250))
            virtual_surface.blit(interface_label, interface_rect)
        
        # Draw title
        title_text = title_font.render("Game Menu", True, get_rainbow_color())
        title_rect = title_text.get_rect(center=(VIRTUAL_W//2, 100))
        virtual_surface.blit(title_text, title_rect)

        mx, my = pygame.mouse.get_pos()
        scale = min(SCREEN_W / VIRTUAL_W, SCREEN_H / VIRTUAL_H)
        ox = (SCREEN_W - VIRTUAL_W * scale) / 2
        oy = (SCREEN_H - VIRTUAL_H * scale) / 2
        vmx, vmy = ((mx - ox) / scale, (my - oy) / scale)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit_game()
            if event.type == pygame.KEYDOWN:
                # Add F5 hotkey to manually check maintenance
                if event.key == pygame.K_F5:
                    if not check_internet_connection():
                        internet_connection_screen()
                        load_button_config()
                    elif is_maintenance_active():
                        maintenance_screen()
                        load_button_config()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check animation selector button
                if select_animation_button.collidepoint((vmx, vmy)) and selected_interface_char:
                    if not check_internet_connection():
                        internet_connection_screen()
                    else:
                        show_animation_menu = not show_animation_menu
                
                # Check change interface button
                elif change_interface_button.collidepoint((vmx, vmy)):
                    if not check_internet_connection():
                        internet_connection_screen()
                    else:
                        new_interface = character_selection_screen()
                        if new_interface:
                            save_interface(new_interface)
                            new_screen(new_interface)
                            return
                
                # Check animation selection if menu is open
                elif show_animation_menu:
                    for action, rect in animation_buttons.items():
                        if rect.collidepoint((vmx, vmy)):
                            interface_action = action
                            interface_idx = 0
                            interface_timer = 0
                            show_animation_menu = False
                            break
                
                # Regular menu buttons
                elif not show_animation_menu:
                    if current_page == 1:
                        for b in buttons_page_1:
                            if b.is_clicked((vmx, vmy)):
                                b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1                       
                    elif current_page == 2:
                        for b in buttons_page_2:
                            if b.is_clicked((vmx, vmy)):
                                b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1
                    elif current_page == 3:
                        for b in buttons_page_3:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1     
                    elif current_page == 4:
                        for b in buttons_page_4:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1
                    elif current_page == 5:
                        for b in buttons_page_5:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1       
                    elif current_page == 6:
                        for b in buttons_page_6:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1
                    elif current_page == 7:
                        for b in buttons_page_7:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1
                    elif current_page == 8:
                        for b in buttons_page_8:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1
                    elif current_page == 9:
                        for b in buttons_page_9:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if next_button.is_clicked((vmx, vmy)) and current_page < 10:
                            current_page += 1
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1
                    elif current_page == 10:
                        for b in buttons_page_10:
                            if b.is_clicked((vmx, vmy)):
                                if b.callback:
                                    b.callback()
                        if previous_button.is_clicked((vmx, vmy)) and current_page > 1:
                            current_page -= 1

        # Draw animation selector button
        if selected_interface_char:
            button_color = HOVER_COLOR if select_animation_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
            pygame.draw.rect(virtual_surface, button_color, select_animation_button, border_radius=10)
            select_anim_text = small_font.render("SELECT ANIMATION", True, WHITE)
            virtual_surface.blit(select_anim_text, select_anim_text.get_rect(center=select_animation_button.center))

        # Draw change interface button
        button_color = HOVER_COLOR if change_interface_button.collidepoint((vmx, vmy)) else BUTTON_COLOR
        pygame.draw.rect(virtual_surface, button_color, change_interface_button, border_radius=10)
        change_text = small_font.render("CHANGE INTERFACE", True, WHITE)
        virtual_surface.blit(change_text, change_text.get_rect(center=change_interface_button.center))

        # Draw animation selection menu if open
        if show_animation_menu and selected_interface_char:
            # Draw semi-transparent overlay
            overlay = pygame.Surface((240, 330))
            overlay.set_alpha(220)
            overlay.fill((20, 20, 40))
            virtual_surface.blit(overlay, (210, 140))
            
            # Draw menu title
            menu_title = button_font.render("Select Animation", True, WHITE)
            virtual_surface.blit(menu_title, (220, 150))
            
            # Draw animation buttons
            for action, rect in animation_buttons.items():
                if action == interface_action:
                    button_color = SELECTED_COLOR
                elif rect.collidepoint((vmx, vmy)):
                    button_color = HOVER_COLOR
                else:
                    button_color = BUTTON_COLOR
                
                pygame.draw.rect(virtual_surface, button_color, rect, border_radius=8)
                action_text = small_font.render(action.replace("_", " "), True, WHITE)
                virtual_surface.blit(action_text, action_text.get_rect(center=rect.center))

        # Function to get button key from callback (optimized)
        button_key_map = {
            hero_knight_boss_with_check: "hero_knight_boss",
            investment_with_check: "investment",
            expedition_with_check: "expedition",
            character_fusion_with_check: "character_fusion",
            summer_event_with_check: "summer_event",
            tournament_with_check: "tournament"  # Added tournament
        }

        def get_button_key(callback_func):
            return button_key_map.get(callback_func, None)

        # Function to get button rect based on page and index (optimized)
        def get_button_rect(page, index):
            return pygame.Rect(VIRTUAL_W//2 - 160, 200 + (index * 100), 320, 70)

        # Optimized button drawing function
        def draw_button_with_status(button, page, index, mouse_pos):
            # First draw the button normally
            button.draw(virtual_surface, mouse_pos)
            
            # Check if button has time restrictions
            button_key = get_button_key(button.callback)
            
            # If button is time-restricted and not available, add overlay
            if button_key and not is_button_available(button_key):
                button_rect = get_button_rect(page, index)
                
                # Create and apply dark overlay
                dark_surface = pygame.Surface((button_rect.width, button_rect.height))
                dark_surface.set_alpha(150)
                dark_surface.fill((50, 50, 50))
                virtual_surface.blit(dark_surface, (button_rect.x, button_rect.y))
                
                # Draw border
                pygame.draw.rect(virtual_surface, (150, 150, 150), button_rect, 2, border_radius=10)
                
                # Draw "LOCKED" text - moved up
                lock_text = small_font.render("LOCKED", True, (255, 100, 100))
                lock_rect = lock_text.get_rect(center=(button_rect.centerx, button_rect.centery - 5))
                virtual_surface.blit(lock_text, lock_rect)
                
                # Draw next available time - moved up
                next_time = get_next_available_time(button_key)
                if next_time != "Available now":
                    # For summer event, show different format
                    if button_key == "summer_event" and not is_summer_event_date_available():
                        time_text = pygame.font.Font(None, 18).render(f"Next: {next_time}", True, (200, 200, 200))
                    else:
                        time_text = pygame.font.Font(None, 18).render(f"Next: {next_time}", True, (200, 200, 200))
                    time_rect = time_text.get_rect(center=(button_rect.centerx, button_rect.centery + 15))
                    virtual_surface.blit(time_text, time_rect)

        # Draw buttons based on current page (only if animation menu is not open)
        if not show_animation_menu:
            # Create a mapping for cleaner code
            page_buttons = {
                1: buttons_page_1,
                2: buttons_page_2,
                3: buttons_page_3,
                4: buttons_page_4,
                5: buttons_page_5,
                6: buttons_page_6,
                7: buttons_page_7,
                8: buttons_page_8,
                9: buttons_page_9,
                10: buttons_page_10
            }
            
            # Draw buttons for current page
            if current_page in page_buttons:
                for i, b in enumerate(page_buttons[current_page]):
                    draw_button_with_status(b, current_page, i, (vmx, vmy))
            
            # Draw navigation buttons
            if current_page < 10:
                next_button.draw(virtual_surface, (vmx, vmy))
            if current_page > 1:
                previous_button.draw(virtual_surface, (vmx, vmy))

        draw_scaled_centered()
        clock.tick(60)
       
cache_animation_frames()        
load_saved_interface()        
main_menu()
