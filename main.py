import kivy
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty
from kivy.core.text import LabelBase
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Line, Color
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.storage.jsonstore import JsonStore

import re
import json
import threading
import requests
from requests.exceptions import ConnectionError

from utils.symbols import *
from utils.imageBase64 import saveImageFromBase64

kivy.require("1.9.0")

LabelBase.register('Ballpark', fn_regular="fonts/Ballpark.TTF")
LabelBase.register('DFPOP', fn_regular="fonts/DFPop91.ttf")

Builder.load_file("kivy_files/menu.kv")
Builder.load_file("kivy_files/text_recognition.kv")
Builder.load_file("kivy_files/handwritten_recognition.kv")
Builder.load_file("kivy_files/register.kv")
Builder.load_file("kivy_files/login.kv")
Builder.load_file("kivy_files/symbols.kv")
Builder.load_file("kivy_files/paint.kv")
Builder.load_file("kivy_files/symbol_details.kv")


def logout(self):
    if textify_app.store.exists('logged'):
        textify_app.store.delete('logged')
        textify_app.token = -1
        textify_app.manager.screens[0].logout()


def open_login(self):
    textify_app.slide_screen('login_screen', 'left')


def open_register(self):
    textify_app.slide_screen('register_screen', 'left')


def format_text(text):
    join_symbol = ' '
    non_space_regex = '[^\s]+'
    words = re.findall(non_space_regex, text)
    return join_symbol.join(words)


class Menu(Screen):

    def login(self):
        logout_btn = MenuButton(text='Logout', size_hint_y=.15, id='logout')
        logout_btn.bind(on_press=logout)
        self.ids['authentication'].clear_widgets()
        self.ids['authentication'].add_widget(logout_btn)

    def logout(self):
        login_button = MenuButton(text='Login', size_hint_y=.15, id='login')
        register_button = MenuButton(text='Register', size_hint_y=.15, id='register')
        login_button.bind(on_press=open_login)
        register_button.bind(on_press=open_register)
        self.ids['authentication'].clear_widgets()
        self.ids['authentication'].add_widget(login_button)
        self.ids['authentication'].add_widget(register_button)


class MenuButton(Button):
    pass


class LoadingPopup(Popup):
    pass


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class DrawInput(Widget):
    def on_touch_down(self, touch):
        with self.canvas:
            Color(0, 0, 0)
            touch.ud["line"] = Line(points=(touch.x, touch.y), width=5)

    def on_touch_move(self, touch):
        try:
            touch.ud["line"].points += (touch.x, touch.y)
        except:
            pass


class RegisterScreen(Screen):
    email = StringProperty()
    password = StringProperty()
    confirmation = StringProperty()
    response = StringProperty()

    def register(self):
        try:
            response = requests.post(textify_app.server_url + '/textify/register',
                                     data={'email': self.email, 'password': self.password,
                                           'confirmation': self.confirmation})

            if response.status_code == 200:
                textify_app.slide_screen('menu', 'right')
                textify_app.login(response.text)
            else:
                Popup(title='Error!', content=Label(text=response.text), size_hint=(1, 0.4)).open()
        except ConnectionError:
            Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                  size_hint=(1, 0.4)).open()


class LoginScreen(Screen):
    email = StringProperty()
    password = StringProperty()
    response = StringProperty()

    def login(self):
        try:
            response = requests.post(textify_app.server_url + '/textify/login',
                                     data={'email': self.email, 'password': self.password})

            if response.status_code == 200:
                textify_app.slide_screen('menu', 'right')
                textify_app.login(response.text)
            else:
                Popup(title='Error!', content=Label(text=response.text), size_hint=(1, 0.4)).open()
        except ConnectionError:
            Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                  size_hint=(1, 0.4)).open()


class SymbolsScreen(Screen):

    def train(self):
        if textify_app.token < 0:
            textify_app.slide_screen('login_screen', 'right')
        else:
            try:
                response = requests.post(textify_app.server_url + '/textify/train',
                                         data={'user_id': str(textify_app.token)})

                if response.status_code == 200:
                    Popup(title='Success!', content=Label(text=response.text), size_hint=(1, 0.4)).open()
                else:
                    Popup(title='Error!', content=Label(text=response.text), size_hint=(1, 0.4)).open()
            except ConnectionError:
                Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                      size_hint=(1, 0.4)).open()


class PaintScreen(Screen):

    index = 1

    def clear(self, painter):
        painter.canvas.clear()

    def save(self, painter):
        name = "img-" + str(self.index) + '.png'
        filename = "symbol_images/" + name
        painter.export_to_png(filename)
        data = {'user_id': textify_app.token, 'label_index': symbols.index(textify_app.current_symbol), 'name': name}
        files = {name: open(filename, 'rb')}
        try:
            requests.post(textify_app.server_url + '/textify/drawings/upload', data=data, files=files)
            self.index += 1
            self.clear(painter)
        except ConnectionError:
            Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                  size_hint=(1, 0.4)).open()

        if self.index > 4:
            self.index = 1
            screen_manager.current = "symbol_details_screen"


class SymbolDetailsScreen(Screen):
    current_symbol = StringProperty()
    source1 = StringProperty('symbol_images/img-1.png')
    source2 = StringProperty('symbol_images/img-2.png')
    source3 = StringProperty('symbol_images/img-3.png')
    source4 = StringProperty('symbol_images/img-4.png')

    def on_pre_enter(self, *args):
        self.change_props()

    def open_paint(self):
        if textify_app.token < 0:
            textify_app.slide_screen('login_screen', 'left')
        else:
            textify_app.slide_screen('paint_screen', 'left')

    def change_props(self):
        if 'textify_app' in globals():
            self.current_symbol = textify_app.current_symbol
            try:
                response = requests.post(textify_app.server_url + '/textify/drawings',
                                         data={'userId': textify_app.token,
                                               'label': symbols.index(self.current_symbol)})
                # print(req.text)
                data = json.loads(response.text)

                for i in range(len(data)):
                    saveImageFromBase64(data[i], 'symbol_images/img-' + str(i + 1) + '.png')

                self.ids['img_1'].reload()
                self.ids['img_2'].reload()
                self.ids['img_3'].reload()
                self.ids['img_4'].reload()
            except ConnectionError:
                Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                      size_hint=(1, 0.4)).open()

    def previous(self):
        index = symbols.index(self.current_symbol) - 1

        if index > -1 and index < 26:
            self.current_symbol = symbols[index]
            textify_app.current_symbol = symbols[index]
            self.change_props()

    def next(self):
        index = symbols.index(self.current_symbol) + 1

        if index < 26 and index > -1:
            self.current_symbol = symbols[index]
            textify_app.current_symbol = symbols[index]
            self.change_props()


class TextRecognitionScreen(Screen):
    result = StringProperty("Load an image or take a picture to begin recognition...")
    loadfile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        if path and filename and filename[0]:
            files = {'img': open(filename[0], 'rb')}
            try:
                response = requests.post(textify_app.server_url + '/textify/', files=files)
                text = response.text
                self.result = format_text(text)
            except ConnectionError:
                Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                      size_hint=(1, 0.4)).open()

        self.dismiss_popup()


class HandwrittenRecognitionScreen(Screen):
    result = StringProperty("Load an image or take a picture to begin recognition...")
    loadfile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content, size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        if path and filename and filename[0]:
            files = {'img': open(filename[0], 'rb')}
            try:
                response = requests.post(textify_app.server_url + '/textify/handwritten', files=files,
                                         data={'user_id': str(textify_app.token)})
                text = response.text
                self.result = format_text(text)
            except ConnectionError:
                Popup(title='Connection error!', content=Label(text='Please check your internet connection!'),
                      size_hint=(1, 0.4)).open()

        self.dismiss_popup()

screen_manager = ScreenManager()
screen_manager.add_widget(Menu(name="menu"))
screen_manager.add_widget(TextRecognitionScreen(name="text_recognition_screen"))
screen_manager.add_widget(HandwrittenRecognitionScreen(name="handwriting_recognition_screen"))
screen_manager.add_widget(PaintScreen(name="paint_screen"))
screen_manager.add_widget(SymbolsScreen(name="symbols_screen"))
screen_manager.add_widget(SymbolDetailsScreen(name="symbol_details_screen"))
screen_manager.add_widget(RegisterScreen(name="register_screen"))
screen_manager.add_widget(LoginScreen(name="login_screen"))


class TextifyApp(App):
    manager = screen_manager
    server_url = 'http://localhost:8000'
    current_symbol = ''
    token = -1
    store = JsonStore('app_data.json')

    def slide_screen(self, screen, direction):
        self.manager.transition.direction = direction
        self.manager.transition.duration = 0.5
        self.manager.current = screen

    def build(self):
        if self.store.exists('logged'):
            self.token = self.store.get('logged')['id']
            self.manager.screens[0].login()
        else:
            self.manager.screens[0].logout()

        return self.manager

    def login(self, id):
        textify_app.store.put('logged', id=id)
        textify_app.token = id
        textify_app.manager.screens[0].login()

    def change_symbol(self, symbol):
        self.current_symbol = symbol
        PaintScreen.current_symbol = symbol

textify_app = TextifyApp()
textify_app.run()
