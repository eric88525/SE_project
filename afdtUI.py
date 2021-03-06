from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.properties import ObjectProperty
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.scatter import Scatter
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics.transformation import Matrix
from kivy.uix.image import Image as uiImage
from PIL import Image
from kivy.uix.behaviors import ButtonBehavior
import os
from kivy.core.window import Window
from parser_afdt.se import analysis_tool

Window.minimum_height = 600
Window.minimum_width = 750


class ImageButton(ButtonBehavior, uiImage):
    def viewImage(self):
        if App.get_running_app().getDiagram != '':
            App.get_running_app().viewImage()
    pass


class UI(BoxLayout):

    pass


class DisplayImage(ScatterLayout):
    move_lock = False
    scale_lock_left = False
    scale_lock_right = False
    scale_lock_top = False
    scale_lock_bottom = False

    def on_touch_up(self, touch):
        self.move_lock = False
        self.scale_lock_left = False
        self.scale_lock_right = False
        self.scale_lock_top = False
        self.scale_lock_bottom = False
        if touch.grab_current is self:
            touch.ungrab(self)
            x = self.pos[0] / 10
            x = round(x, 0)
            x = x * 10
            y = self.pos[1] / 10
            y = round(y, 0)
            y = y * 10
            self.pos = x, y
            return super(DisplayImage, self).on_touch_up(touch)

    def transform_with_touch(self, touch):
        changed = False
        x = self.bbox[0][0]
        y = self.bbox[0][1]
        width = self.bbox[1][0]
        height = self.bbox[1][1]
        mid_x = x + width / 2
        mid_y = y + height / 2
        inner_width = width * 0.5
        inner_height = height * 0.5
        left = mid_x - (inner_width / 2)
        right = mid_x + (inner_width / 2)
        top = mid_y + (inner_height / 2)
        bottom = mid_y - (inner_height / 2)

        # just do a simple one finger drag
        if len(self._touches) == self.translation_touches:
            # _last_touch_pos has last pos in correct parent space,
            # just like incoming touch
            dx = (touch.x - self._last_touch_pos[touch][0]) \
                * self.do_translation_x
            dy = (touch.y - self._last_touch_pos[touch][1]) \
                * self.do_translation_y
            dx = dx / self.translation_touches
            dy = dy / self.translation_touches
            if (touch.x > left and touch.x < right and touch.y < top and touch.y > bottom or self.move_lock) and not self.scale_lock_left and not self.scale_lock_right and not self.scale_lock_top and not self.scale_lock_bottom:
                self.move_lock = True
                self.apply_transform(Matrix().translate(dx, dy, 0))
                changed = True

        change_x = touch.x - self.prev_x
        change_y = touch.y - self.prev_y
        anchor_sign = 1
        sign = 1
        if abs(change_x) >= 9 and not self.move_lock and not self.scale_lock_top and not self.scale_lock_bottom:
            if change_x < 0:
                sign = -1
            if (touch.x < left or self.scale_lock_left) and not self.scale_lock_right:
                self.scale_lock_left = True
                self.pos = (self.pos[0] + (sign * 10), self.pos[1])
                anchor_sign = -1
            elif (touch.x > right or self.scale_lock_right) and not self.scale_lock_left:
                self.scale_lock_right = True
            self.size[0] = self.size[0] + (sign * anchor_sign * 10)
            self.prev_x = touch.x
            changed = True
        if abs(change_y) >= 9 and not self.move_lock and not self.scale_lock_left and not self.scale_lock_right:
            if change_y < 0:
                sign = -1
            if (touch.y > top or self.scale_lock_top) and not self.scale_lock_bottom:
                self.scale_lock_top = True
            elif (touch.y < bottom or self.scale_lock_bottom) and not self.scale_lock_top:
                self.scale_lock_bottom = True
                self.pos = (self.pos[0], self.pos[1] + (sign * 10))
                anchor_sign = -1
            self.size[1] = self.size[1] + (sign * anchor_sign * 10)
            self.prev_y = touch.y
            changed = True
        return changed

    def on_touch_down(self, touch):
        x, y = touch.x, touch.y
        self.prev_x = touch.x
        self.prev_y = touch.y

        if touch.is_mouse_scrolling:
            if touch.button == 'scrolldown':
                print('down')
                # zoom in
                if self.scale < 10:
                    self.scale = self.scale * 1.1

            elif touch.button == 'scrollup':
                print('up')  # zoom out
                if self.scale > 1:
                    self.scale = self.scale * 0.8

        # if the touch isnt on the widget we do nothing
        if not self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        # let the child widgets handle the event if they want
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if super(Scatter, self).on_touch_down(touch):
            # ensure children don't have to do it themselves
            if 'multitouch_sim' in touch.profile:
                touch.multitouch_sim = True
            touch.pop()
            self._bring_to_front(touch)
            return True
        touch.pop()

        # if our child didn't do anything, and if we don't have any active
        # interaction control, then don't accept the touch.
        if not self.do_translation_x and \
                not self.do_translation_y and \
                not self.do_rotation and \
                not self.do_scale:
            return False

        if self.do_collide_after_children:
            if not self.collide_point(x, y):
                return False

        if 'multitouch_sim' in touch.profile:
            touch.multitouch_sim = True
        # grab the touch so we get all it later move events for sure
        self._bring_to_front(touch)
        touch.grab(self)
        self._touches.append(touch)
        self._last_touch_pos[touch] = touch.pos

        return True


class ButtonList(BoxLayout):

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self._on_mouse_pos)
        super(ButtonList, self).__init__(**kwargs)

    def _on_mouse_pos(self, w, p):
        if self.collide_point(p[0], p[1]) == False:
            App.get_running_app().setUserHintMessage('')

        if self.ids.importfile_btn.collide_point(p[0], p[1]):
            App.get_running_app().setUserHintMessage('Press button to import file')
            self.ids.importfile_btn.background_color = (1.0, 0.0, 0.0, 1.0)

        if self.ids.importfile_btn.collide_point(p[0], p[1]) == False:
            self.ids.importfile_btn.background_color = (1.0, 1.0, 1.0, 1.0)

        if self.ids.drawdiagram_btn.collide_point(p[0], p[1]):
            App.get_running_app().setUserHintMessage('Press button to draw diagram')
            self.ids.drawdiagram_btn.background_color = (1.0, 0, 0, 1.0)

        if self.ids.drawdiagram_btn.collide_point(p[0], p[1]) == False:
            self.ids.drawdiagram_btn.background_color = (1.0, 1.0, 1.0, 1.0)

        if self.ids.saveimage_btn.collide_point(p[0], p[1]):
            App.get_running_app().setUserHintMessage('Press button to save image')
            self.ids.saveimage_btn.background_color = (1.0, 0, 0, 1.0)

        if self.ids.saveimage_btn.collide_point(p[0], p[1]) == False:
            self.ids.saveimage_btn.background_color = (1.0, 1.0, 1.0, 1.0)

        if self.ids.clear_btn.collide_point(p[0], p[1]):
            App.get_running_app().setUserHintMessage('Press button to clear code')
            self.ids.clear_btn.background_color = (1.0, 0, 0, 1.0)

        if self.ids.clear_btn.collide_point(p[0], p[1]) == False:
            self.ids.clear_btn.background_color = (1.0, 1.0, 1.0, 1.0)

        if self.ids.userpreference_btn.collide_point(p[0], p[1]):
            App.get_running_app().setUserHintMessage(
                'Press button to setting user preference')
            self.ids.userpreference_btn.background_color = (1.0, 0, 0, 1.0)

        if self.ids.userpreference_btn.collide_point(p[0], p[1]) == False:
            self.ids.userpreference_btn.background_color = (1.0, 1.0, 1.0, 1.0)

        if self.ids.userhelp_btn.collide_point(p[0], p[1]):
            App.get_running_app().setUserHintMessage('Press button to see user help')
            self.ids.userhelp_btn.background_color = (1.0, 0, 0, 1.0)

        if self.ids.userhelp_btn.collide_point(p[0], p[1]) == False:
            self.ids.userhelp_btn.background_color = (1.0, 1.0, 1.0, 1.0)

    def draw(self):
        print('d')
        App.get_running_app().draw()

    def openFolder(self):
        App.get_running_app().openFolder()

    def importFile(self):
        App.get_running_app().importFile()

    def clear(self):
        App.get_running_app().clear()
        print(App.get_running_app().root.width,
              App.get_running_app().root.height)

    def saveFile(self):
        App.get_running_app().saveFile()

    def userhelp(self):
        App.get_running_app().show_help()

    def setting(self):
        App.get_running_app().show_setting()

    pass


class settingDialog(FloatLayout):
    ok = ObjectProperty(None)
    cancel = ObjectProperty(None)
    pass


class userHelpDialog(FloatLayout):

    ok = ObjectProperty(None)

    pass


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)


class floatImage(FloatLayout):

    pass


class DisplayCode(ScrollView):

    pass


class SysMessage(Label):

    pass


class UserHintMessage(Label):
    pass


class AFDT(App):
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    # ui font size
    codeFontSize = ObjectProperty(20)
    uiFontSize = ObjectProperty(20)
    # source path of diagram
    getDiagram = ObjectProperty('')

    def __init__(self, **kwargs):
        super(AFDT, self).__init__(**kwargs)
        self.image = None
        self.code = ''
        self.sysMessage = 'Welcome to AFDT'
        self.fileName = ''
        self.hasOpenFolder = False
        Window.bind(on_key_down=self._on_keyboard_down)
        Window.bind(on_dropfile=self._on_file_drop)

    # POP UP  function
    def show_help(self):
        content = userHelpDialog(ok=self.dismiss_popup)
        self._popup = Popup(title="help", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_setting(self):
        content = settingDialog(ok=self.set_text_size,
                                cancel=self.dismiss_popup)
        self._popup = Popup(title="User Preferences", content=content,
                            size_hint=(0.8, 0.3))
        self._popup.open()

    def set_text_size(self, text_size):
        self.UI.displayCode.font_size = text_size
        print('Txt size set to ' + text_size)
        self.dismiss_popup()
        pass

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def viewImage(self):
        content = floatImage()
        self._popup = Popup(title="Diagram", content=content,
                            size_hint=(1, 0.8), auto_dismiss=True)
        self._popup.open()

    # laod & save

    def load(self, path, filename):
        try:
            with open(os.path.join(path, filename[0]),encoding= 'utf-8') as stream:
                self.code = stream.read()
                self.UI.displayCode.text = self.code
            self.setSystemMessage('Import ' + filename[0] + ' success!')
        except:
            self.setSystemMessage('Error file type!')
            pass

        self.dismiss_popup()

    def save(self, path, filename):
        try:
            p = path + '/' + filename + '.png'
            print(p)
            self.image.save(p, 'png')
            self.dismiss_popup()
            self.setSystemMessage('Save image success')
        except:
            self.setSystemMessage(
                'Save image error!Check if you have generated the diagram')

    def _on_file_drop(self, window, file_path):
        print(file_path.decode())
        try:
            with open(file_path.decode()) as stream:
                self.code = stream.read()
                self.UI.displayCode.text = self.code
            self.setSystemMessage('Import ' + file_path.decode() + ' success!')
        except:
            self.setSystemMessage('Error file type!')
            pass
        return

    def saveFile(self):
        self.show_save()

    def setSystemMessage(self, text):
        self.UI.sysMessageLabel.text = text

    def setUserHintMessage(self, text):
        self.UI.userHintMessageLabel.text = text

    def importFile(self):
        self.show_load()

    def clear(self):
        self.setSystemMessage('Clear file success')
        self.UI.displayCode.text = ''
        self.fileName = ''
        self.code = ''
        self.image = ''
        self.getDiagram = ''

    def _on_mouse_pos(self, w, pos):

        pass
        #print (pos)

    def _on_keyboard_down(self, instance, keyboard, keycode, text, modifiers):
        if len(modifiers) > 0 and modifiers[0] == 'ctrl':
            if text == 'o':  # Ctrl+a
                print('open folder')
                self.setSystemMessage('open folder')
                self.show_load()
            elif text == 's':
                self.setSystemMessage('save img')
                print('save img')
            elif text == 'p':
                self.setSystemMessage('analyze code')
                print('analyze code')

    def draw(self):
        # self.code
        try:
            analysis_tool(code=self.code)
            self.getDiagram = './out.gv.png'
            self.image = Image.open(self.getDiagram)
            self.setSystemMessage('Generate diagram success')
            self.UI.imageButton.reload()
            # self.image.show()
        except:
            self.setSystemMessage(
                'Cannot Parse Source. Please Check You Source Code Or Try Other Program.')

    def build(self):
        self.UI = UI()
        return self.UI


A = AFDT()
A.run()
