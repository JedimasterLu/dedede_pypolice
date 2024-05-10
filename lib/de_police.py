import pyautogui
import easyocr
import cv2
import win32gui
import numpy as np
import keyboard
from lib.color_print import print_error, print_info, print_warning
from lib.nlp import NLP
from PIL import ImageFont, ImageDraw, Image

class DePolice:
    def __init__(self, img_path='', mode='window', text=''):
        self.nlp = NLP()
        self.reader = easyocr.Reader(['ch_sim','en'])
        self.img_path = img_path
        self.img = None
        self.text = text
        self.img_result = None
        if mode in ['window','fullscreen','manual','string']:
            self.mode = mode
        else:
            print_warning("WARNING: mode has to be 'window', 'fullscreen', 'manual' or 'string'. Please redefine by set_mode().")
            self.mode = None
        if mode == 'string' and text == '':
            print_warning("WARNING: when mode is 'string', text shouldn't be None. Please redefine by set_text().")
        elif text and mode != 'string':
            self.mode = 'string'

    def set_mode(self, mode):
        self.mode = mode
    
    def set_text(self, text):
        self.text = text

    def get_window_position(self) -> dict:
        hwnd = win32gui.GetForegroundWindow()
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return {'left': left, "top": top, "right": right, "bottom": bottom}

    def get_screenshot(self):
        if self.mode == 'window':
            # Get position of focused window
            img_position = self.get_window_position()
            left = img_position["left"]
            top = img_position["top"]
            right = img_position["right"]
            bottom = img_position["bottom"]
            width = right - left
            height = bottom - top
        elif self.mode == "fullscreen":
            # Get the resolution of the screen
            left = 0
            top = 0
            width, height = pyautogui.size()
        elif self.mode == "manual":
            print_info("Press 'enter' to get pt1 and pt2 ...")
            keyboard.wait('enter')
            x, y = pyautogui.position()
            pt1 = [x, y]
            print_info(f'pt1: ({x}, {y})')
            keyboard.wait('enter')
            x, y = pyautogui.position()
            pt2 = [x, y]
            print_info(f'pt2: ({x}, {y})')
            left, top = pt1[0], pt1[1]
            width, height = pt2[0] - pt1[0], pt2[1] - pt1[1]
        elif self.mode == "string":
            print_warning("WARNING: mode is 'string'. get_screenshot() will return None!")
            return
        else:
            print_error('ERROR: mode is None. get_screenshot() will return None!')
            return
        # Take screen shot and convert to np.array
        img = pyautogui.screenshot(region=[left, top, width, height])
        img = cv2.cvtColor(np.asarray(img),cv2.COLOR_RGB2BGR)
        return img
    
    def read_img(self):
        if self.img_path:
            img = cv2.imread(self.img_path)
        else:
            img = self.get_screenshot()
        self.img = img
        self.img_result = self.reader.readtext(img)
        return self.img_result

    def block_img(self):
        self.read_img()
        result = self.img_result
        blocks = [] # Gather chars from a paragraph into a block
        current_block = {
            'content': '',
            'begin' : -1,
            'end' : -1
        }
        for index, line in enumerate(result):
            if index == 0:
                current_block['content'] = line[1]
                current_block["begin"] = 0
                current_block["end"] = 0
                continue
            last_line = result[index-1]
            char_height = int(line[0][3][1]-line[0][0][1])
            last_char_height = int(last_line[0][3][1]-last_line[0][0][1])
            if abs(char_height-last_char_height) < 7 and line[0][0][1]-last_line[0][2][1] < char_height:
                current_block['content'] += line[1]
                current_block['end'] = index
            else:
                blocks.append((current_block['content'], current_block['begin'], current_block['end']))
                current_block['content'] = line[1]
                current_block['begin'] = index
                current_block["end"] = index
        if current_block:
            blocks.append((current_block['content'], current_block['begin'], current_block['end']))
        return blocks

    def judge_de(self, text):
        result = self.nlp.process(text)
        index = 0
        index_of_wrong_de = []
        info_of_wrong_de = []
        for tok, pos in zip(result['tok'], result['pos']):
            if tok in ['的','地','得']:
                if tok == '的' and pos not in ['DEG','DEC','AS','SP']:
                    correct_tok = self._pos_to_de(pos)
                    index_of_wrong_de.append(index)
                    info_of_wrong_de.append((tok, correct_tok))
                if tok == '地' and pos not in ['DEV','NN']:
                    correct_tok = self._pos_to_de(pos)
                    index_of_wrong_de.append(index)
                    info_of_wrong_de.append((tok, correct_tok))
                if tok == '得' and pos != 'DER':
                    correct_tok = self._pos_to_de(pos)
                    index_of_wrong_de.append(index)
                    info_of_wrong_de.append((tok, correct_tok))
            index += 1
        return result, index_of_wrong_de, info_of_wrong_de

    def judge(self):
        if self.mode == 'string':
            result_doc, index_of_wrong_de, info_of_wrong_de = self.judge_de(self.text)
            if not index_of_wrong_de:
                print("--------------Result----------------")
                print("No fault has been found!")
                return False, None
            else:
                print("--------------Result----------------")
                for i, tok in enumerate(result_doc['tok']):
                    if i not in index_of_wrong_de:
                        print(tok, end='')
                    else:
                        wrong_index = index_of_wrong_de.index(i)
                        print_error(f"{info_of_wrong_de[wrong_index][0]}({info_of_wrong_de[wrong_index][1]})",end='')
                return True, result_doc
        else:
            blocks = self.block_img()
            img_result = self.img_result
            img = self.img
            flg = False
            for block in blocks:
                result_doc, index_of_wrong_de, info_of_wrong_de = self.judge_de(block[0])
                if index_of_wrong_de:
                    flg = True
                    begin_index = block[1]
                    end_index = block[2]
                    for wrong_index in index_of_wrong_de:
                        wrong_i = index_of_wrong_de.index(wrong_index)
                        correct_de = info_of_wrong_de[wrong_i][1]
                        # Get the position of de in the paragraph
                        de_position = 1
                        for i in range(wrong_index):
                            de_position += len(result_doc['tok'][i])
                        # Get which img_result minor_block does the de come from
                        minor_block_index = begin_index
                        while de_position > len(img_result[minor_block_index][1]):
                            de_position -= len(img_result[minor_block_index][1])
                            minor_block_index += 1
                        # Print rectangle around the minor block
                        pt1 = (int(img_result[minor_block_index][0][0][0]),int(img_result[minor_block_index][0][0][1]))
                        pt2 = (int(img_result[minor_block_index][0][2][0]),int(img_result[minor_block_index][0][2][1]))
                        img = self.draw_line_on_fault(img, len(img_result[minor_block_index][1]), de_position, pt1, pt2, correct_de)
            cv2.imshow('detected_img',img)
            cv2.imwrite('detected_img.jpg',img)
            cv2.moveWindow('detected_img', 0, 0)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            return flg, img
            
    def _pos_to_de(self, pos):
        dic = {
            "DEG": "的",
            "DEV": "地",
            "DER": "得",
            "DEC": "的",
            "AS": "的",
            "SP": "的"
        }
        return dic[pos]
    
    def show_blocked_img(self):
        result = self.read_img()
        blocks = self.block_img()
        img = self.img
        for block in blocks:
            begin_index = block[1]
            end_index = block[2]

            width, height = pyautogui.size()
            pt2_x = pt2_y = 0
            pt1_x, pt1_y = width, height
            for index in range(begin_index,end_index+1):
                if result[index][0][0][0] < pt1_x:
                    pt1_x = result[index][0][0][0]
                if result[index][0][0][1] < pt1_y:
                    pt1_y = result[index][0][0][1]
                if result[index][0][2][0] > pt2_x:
                    pt2_x = result[index][0][2][0]
                if result[index][0][2][1] > pt2_y:
                    pt2_y = result[index][0][2][1]
            pt1 = (int(pt1_x),int(pt1_y))
            pt2 = (int(pt2_x),int(pt2_y))
            cv2.rectangle(img, pt1, pt2, (0,0,255), 1)
        cv2.imshow('blocked_img',img)
        cv2.moveWindow('blocked_img', 0, 0)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def show_marked_img(self):
        result = self.read_img()
        img = self.img
        for line in result:
            pt1 = (int(line[0][0][0]),int(line[0][0][1]))
            pt2 = (int(line[0][2][0]),int(line[0][2][1]))
            cv2.rectangle(img, pt1, pt2, (0,0,255), 1)
        cv2.imshow('marked_img',img)
        cv2.moveWindow('marked_img', 0, 0)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def draw_line_on_fault(self, img, total_len, pos, pt1, pt2, foot_text=''):
        width_per_char = (pt2[0] - pt1[0]) / total_len
        line_pt1 = (int( pt1[0] + width_per_char*(pos-1) ), pt2[1])
        line_pt2 = (int( pt1[0] + width_per_char*pos ), pt2[1])
        cv2.line(img, line_pt1, line_pt2, (0,0,255), 1)

        font = ImageFont.truetype('Deng.ttf', 12)
        img_pil = Image.fromarray(img)
        draw = ImageDraw.Draw(img_pil)
        draw.text((line_pt2[0], line_pt2[1]-6), foot_text, font=font, fill=(0, 0, 255, 0))
        img = np.array(img_pil)

        return img