'''
Image labeller GUI for repeatability study, Desktop version
Matt Butler 2021
Harper Adams University.
mbutler@harper-adams.ac.uk

based on https://github.com/AlexeyAB/Yolo_mark
'''

box_size = 35
directory = 'images' ## you could change these 
doneDir = "done" 

import cv2 # not found? Try: pip install opencv-python 
import numpy as np ## treating images as arrays of numbers 
import time
import datetime
import os ## get file names and folders 
import platform ## windows or linux 
import sys 
import csv 

print('Running under ' + platform.system())


if (platform.system()=='Windows'):
    windows = True
    # just for icon change to pointer over buttons on Windows only
    import win32api # not found? Try: pip install pypiwin32
    import win32con
else:
    windows = False



print ('Using '+ directory + ' folder')
        
saving = False
undoing = False
freezing = False
pls_save = False
pls_undo = False
pls_instruct = False
pls_freeze = False


boxes = [] ## held in a list, and resets 

WHITE = (255,255,255)
BLACK = (0,0,0)
RED =  (0,0,255)
save_colour = WHITE
undo_colour = WHITE
freeze_colour = WHITE
font = cv2.FONT_HERSHEY_COMPLEX
font_size = 1
font_color = WHITE
font_thickness = 1
s_text = 'SAVE'
u_text = 'UNDO'
f_text = 'FREEZE'
stx,sty = 8,35
utx,uty = 5,35
ftx,fty = 5,35

work_file = '' ## name of file 



# Make a message window
#msg_window = np.zeros((720,1280,3))#(image.shape[0],image.shape[1],3))


# Welcome message
def show_instructions(time):
    global image,pls_instruct
    pls_instruct = False
    cv2.putText(msg_window, 'Press <Esc> or <q> to quit program', (20,int(msg_window.shape[0]/2)), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Left-click to box a stem', (20,40), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Backspace> to delete last', (20,80), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Del> to reset', (20,120), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <s> to skip picture)', (20,160), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Enter> to save all', (20,200), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <n> to view progress', (20,240), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, '(Right-click to see this message again)', (20,int(msg_window.shape[0]/2)+ 80), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.imshow("Viewmaster",msg_window)
    cv2.waitKey(time)

#show_instructions(8000) # hit any key to cut this short

drawing = False

px = 0
py = 0


# Adding Function Attached To Mouse Callback ## this happens everytime you move the mouse or click 
def draw(event,x,y,flags,params):
    global stem_number,drawing,image,cam,save_colour, undo_colour,saving,undoing,boxes,widows, \
	pls_save,pls_undo,pls_instruct,pls_freeze,freeze_colour,freezing,px,py,frame_data

    # Right mouse button down
    if (event==cv2.EVENT_RBUTTONDOWN):
        print('Right button press')
        #show_instructions(5000)
        pls_instruct = True
        return

    # Left Mouse Button Down Pressed
    if(event==cv2.EVENT_LBUTTONDOWN):
        if not (saving or undoing or freezing):
            drawing = True
        if saving:
            #save_yolo()
            pls_save = True
            return
        if undoing:
            #undo_last()
            pls_undo = True
            return
        if freezing:
            pls_freeze = True
            return

        #print ('click down')
        print ('Pointer centre: '+str(x)+', '+str(y))

        if(drawing==True):

            # for single point box creation
            if x > box_size:
                tlx = x-box_size
            else:
                tlx = 1
                
            if image.shape[1] > (x + box_size):
                brx = x + box_size
            else:
                brx = image.shape[1]-1

            if y > box_size:
                tly = y-box_size
            else:
                tly = 1

            if image.shape[0] > (y + box_size):
                bry = y + box_size
            else:
                bry = image.shape[0]-1
               
            pt3 = (tlx, tly)
            pt4 = (brx, bry)
            boxes.append([pt3,pt4])
            
            for coords in boxes:
                print (coords)

        
    if(event==cv2.EVENT_MOUSEMOVE):# moving
        px = x
        py = y
        if False:#((x < 105) and (y < 55)):
            save_colour = (227,188,0)
            if windows:
                win32api.SetCursor(win32api.LoadCursor(0, win32con.IDC_ARROW))
            saving = True
        else:
            save_colour = WHITE
            saving = False
        if False:#((x > image.shape[1] - 105) and (y < 55)):
            undo_colour = (0,0,255)
            if windows:
                win32api.SetCursor(win32api.LoadCursor(0, win32con.IDC_ARROW))
            undoing = True
        else:
            undo_colour = WHITE
            undoing = False

        if False:#((x > int((image.shape[1])/2) - int((freeze_button.shape[1])/2)) and (x < int((image.shape[1])/2) + int((freeze_button.shape[1])/2)) and (y < 55)):
            freeze_colour = (0,255,255)
            if windows:
               win32api.SetCursor(win32api.LoadCursor(0, win32con.IDC_ARROW))
            freezing = True
        else:
            freeze_colour = WHITE
            freezing = False

    if(event==cv2.EVENT_LBUTTONUP):
        drawing = False
        print ('click up')
        



now = datetime.datetime.now()
outDir = "i_yolo_data/" + now.strftime("%Y-%m-%d")
confDir = "i_chk_data/" + now.strftime("%Y-%m-%d")

if not os.path.exists(outDir):
    os.makedirs(outDir)
if not os.path.exists(confDir):
    os.makedirs(confDir)
if not os.path.exists(doneDir):
    os.makedirs(doneDir)


def save_yolo():
    global save_image,numsnaps,boxes,image,pls_save,outDir,confDir,just_saved
    pls_save = False

    if (len(boxes) > 0):
        print ('Saving')
        cv2.imwrite(outDir +"/" + work_file,save_image)
        cv2.imwrite(confDir +"/" + work_file_core + ".png",image)
    
        if len(boxes) > 0:
            # save yolo text {0,x(centre),y(centre),w,h} all as proportions of image size
            yolo_txt = open(outDir +"/" + work_file_core + ".txt", 'a')
            print ('Saved: '+ str(numsnaps))
            n=1
            for bb in boxes:
                
                w=(bb[1][0]-bb[0][0])/image.shape[1]
                h=(bb[1][1]-bb[0][1])/image.shape[0]
                x=(bb[0][0]/image.shape[1])+ (w/2)
                y=(bb[0][1]/image.shape[0])+ (h/2)
                data = str(0)+' '+str(x)+' '+str(y)+' '+str(w)+' '+str(h)
                if n != len(boxes):
                    data = data + '\n'
                n=n+1
                yolo_txt.write(data)
            yolo_txt.close()    
            boxes = []


        msg_window = np.zeros((image.shape[0],image.shape[1],3))
        cv2.putText(msg_window, 'Saved ' + work_file_core + '.txt', (20,int(msg_window.shape[0]/2)), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
        cv2.imshow("Viewmaster",msg_window)
        cv2.waitKey(2000)
        just_saved = True
        
    else:
        print('Nothing to save')
        cv2.putText(image, 'Nothing to save!', (160,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
        cv2.imshow("Viewmaster",image)
        cv2.waitKey(2000)

def undo_last():
    global boxes,pls_undo
    pls_undo = False

    if len(boxes) > 0:
        boxes.pop()
    else:
        cv2.putText(image, 'No boxes to remove!', (110,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
        cv2.imshow("Viewmaster",image)         
        cv2.waitKey(2000)

    print('Undo pressed')


def undo_all():
    global boxes
    boxes = []
    print('Undone')

def report_num_of_snaps():
    global image
    snaps =  (len([name for name in os.listdir(confDir) if os.path.isfile(os.path.join(confDir, name))]))
    cv2.putText(image, str(snaps)+' snaps so far today!', (110,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
    cv2.imshow("Viewmaster",image)         
    cv2.waitKey(2000)



def label_images():
    global image,just_saved
    while(True):

        image = save_image.copy() # must continually refresh to draw on it        
        cv2.circle(image, (px, py), box_size, WHITE, 2)

        #overlay rectangles
        for coords in boxes:
            cv2.rectangle(image,pt1=coords[0],pt2=coords[1],color= WHITE,thickness=2)
            
        cv2.imshow("Viewmaster",image)
        
        #check for user instruction
        intent = cv2.waitKey(1)

        if pls_save:
            print('Please save received')
            save_yolo()
        if pls_undo:
            print('Please undo received')
            undo_last()
        if pls_instruct:
            print('Instructions requested')
            show_instructions(5000)
        if pls_freeze:
            print('Screen freeze/release requested')
            set_screen()
        
        if (intent != -1):     
            print('User intent = '+str(intent))
            
        if intent == 8:
            undo_last()
            
        if (intent == 0) or (intent == 255):
            undo_all()

        if intent == 13:
            save_yolo()
            if just_saved:
                just_saved = False
                break

        if (intent == ord('n')):
            report_num_of_snaps()

        if (intent == ord('s')): # skip pic
            break

        if (intent == 27) or (intent == ord('q')):
            print('Bye!')
            sys.exit()

# The main loop
numsnaps = 1
just_saved = False
if os.path.isdir(directory):

    # Making Window For The Image
    cv2.namedWindow("Viewmaster", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Viewmaster", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    # Adding Mouse CallBack Event
    cv2.setMouseCallback("Viewmaster",draw)

    for filename in os.listdir(directory):
        if filename.endswith(".jpg"):
            work_file = filename
            print(work_file)
            work_file_core = (os.path.splitext(work_file)[0])
            save_image = cv2.imread(directory + '/' + work_file, cv2.IMREAD_COLOR)
            label_images()
            ## move single image from "image" (directory) folder to doneDir
            os.replace(directory + '/' + work_file, doneDir + '/' + work_file) 
            continue
        else:
            continue
else:
    print('\nimage directory not found')
    try:
        raw_input("Press Enter to Exit...")
    except:
        input("Press Enter to Exit...")
    sys.exit()

cv2.destroyAllWindows()
print('\nNo more images!')
try:
    raw_input("Press Enter to Exit...")
except:
    input("Press Enter to Exit...")


