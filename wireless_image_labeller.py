'''
Image labeller GUI for repeatability study, Live wireless webcam version
Matt Butler 2021
Harper Adams University.
mbutler@harper-adams.ac.uk

based on https://github.com/AlexeyAB/Yolo_mark
'''

#wireless = False
wireless = True

# Select your camera number.
# Usually.. 0 = inbuilt, 1 = USB webcam (or use automatic selection)

choice = 1
#manual_selection = True
manual_selection = False # choice will be ignored in this case, last camera found will be selected

box_size = 35

import cv2 # not found? Try: pip install opencv-python
import numpy as np
import time
import datetime
import os
import platform
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

def list_ports():
    global windows
    """
    Test the ports and returns a tuple with the available ports and the ones that are working.
    Or just the last one found..
    """
    
    last_cam = 0
    for dev_port in range(11):
        if windows:
            camera = cv2.VideoCapture(dev_port,cv2.CAP_DSHOW)
        else:
            camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            print("No camera at port %s." %dev_port)
        else:
            is_reading, img = camera.read()

            if is_reading:
                w = camera.get(3)
                h = camera.get(4)
                camera.release()
                print("Port %s is working and reads images." %dev_port)
                last_cam = dev_port
            else:
                print("Port %s for camera is present but does not read." %dev_port)

    return last_cam #available_ports,working_ports

last_cam_found = list_ports()

# Choose at the top of the script - or let it choose the last camera
if manual_selection:
    camport = choice
    print ('selected port is ' + str(camport) + ' (manual selection)')
else:
    camport = last_cam_found
    if camport == 0:
        print ('selected port is ' + str(camport) + ' (Default)')
    else:
        print ('selected port is ' + str(camport) + ' (Last detected)')
        

# Making the buttons
save_button = np.zeros((50,100,3))
undo_button = np.zeros((50,100,3))


frozen = 0

saving = False
undoing = False
freezing = False
pls_save = False
pls_undo = False
pls_instruct = False
pls_freeze = False


boxes = []

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

numsnaps = 0

if wireless:
    cam = cv2.VideoCapture()
    print('Try streaming 1280 x 720 camera')
    cam.open('http://10.42.0.1:8081')
else:
    if windows:        
        cam = cv2.VideoCapture(camport,cv2.CAP_DSHOW)
    else:
        cam = cv2.VideoCapture(camport)

    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

ret_val, image = cam.read()
if not ret_val:
    print('\nCannot proceed without a camera')
    try:
        raw_input("Press Enter to Exit...")
    except:
        input("Press Enter to Exit...")
    sys.exit()
    
w = cam.get(3)
h = cam.get(4)
print('Camera runs at ' + str(int(w)) + 'x' + str(int(h)))

# Make a message window
msg_window = np.zeros((image.shape[0],image.shape[1],3))

stem_number = 1

def set_stem_numb(val):
    global stem_number
    stem_number = val


# Welcome message
def show_instructions(time):
    global image,pls_instruct
    pls_instruct = False
    cv2.putText(msg_window, 'Press <Esc> or <q> to quit program', (20,int(msg_window.shape[0]/2)), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Left-click to box a stem', (20,40), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Backspace> to delete last', (20,80), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Del> to reset', (20,120), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Space Bar> to Freeze (air-truth)', (20,160), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <Enter> or <s> to save all', (20,200), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, 'Press <n> to view progress', (20,240), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.putText(msg_window, '(Right-click to see this message again)', (20,int(msg_window.shape[0]/2)+ 80), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
    cv2.imshow("Viewmaster",msg_window)
    cv2.waitKey(time)

#show_instructions(8000) # hit any key to cut this short

drawing = False

px = 0
py = 0

frame_data =[]

# Adding Function Attached To Mouse Callback
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
            if not frozen:
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
            else:
                data_point = [(x, y), int(stem_number)]
                frame_data.append(data_point)
                print(frame_data)
        
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
        

# Making Window For The Image
cv2.namedWindow("Viewmaster", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Viewmaster", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
# Adding Mouse CallBack Event
cv2.setMouseCallback("Viewmaster",draw)

now = datetime.datetime.now()
outDir = "yolo_data/" + now.strftime("%Y-%m-%d")
confDir = "chk_data/" + now.strftime("%Y-%m-%d")
if not os.path.exists(outDir):
    os.makedirs(outDir)
if not os.path.exists(confDir):
    os.makedirs(confDir)

def save_yolo():
    global save_image,numsnaps,boxes,image,pls_save,frame_data,outDir,confDir
    snapnow = datetime.datetime.now()
    snaptime = snapnow.strftime("%Y-%m-%d %H.%M..%S")
    pls_save = False

    if (len(boxes) > 0) or (len(frame_data) > 0):
        print ('Saving')
        cv2.imwrite(outDir +"/" + snaptime + " n" + str(numsnaps) + "_rgb.jpg",save_image)
        cv2.imwrite(confDir +"/" + snaptime + " n" + str(numsnaps) + ".png",image)
    
        if len(boxes) > 0:
            # save yolo text {0,x(centre),y(centre),w,h} all as proportions of image size
            yolo_txt = open(outDir +"/" + snaptime + " n" + str(numsnaps) + "_rgb.txt", 'a')
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

        if len(frame_data) > 0:
            with open(outDir +"/" + snaptime + " n" + str(numsnaps) + ".csv", "w") as csv_file:
                write = csv.writer(csv_file)
                write.writerow(["Co-ords", "Stem count"])
                write.writerows(frame_data)
            frame_data = []
            
        numsnaps = numsnaps+1
        msg_window = np.zeros((image.shape[0],image.shape[1],3))
        cv2.putText(msg_window, 'Saved at ' + snaptime, (20,int(msg_window.shape[0]/2)), font, font_size, WHITE, font_thickness, cv2.LINE_AA)
        cv2.imshow("Viewmaster",msg_window)
        cv2.waitKey(2000) 
        
    else:
        print('Nothing to save')
        cv2.putText(image, 'Nothing to save!', (160,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
        cv2.imshow("Viewmaster",image)
        cv2.waitKey(2000)

    reset()

  	
def undo_last():
    global boxes,pls_undo,frame_data
    pls_undo = False

    if not frozen:
        if len(boxes) > 0:
            boxes.pop()
        else:
            cv2.putText(image, 'No boxes to remove!', (110,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
            cv2.imshow("Viewmaster",image)         
            cv2.waitKey(2000)

    else:
        if len(frame_data) > 0:
            frame_data.pop()
        else:
            cv2.putText(image, 'No plants to remove!', (110,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
            cv2.imshow("Viewmaster",image)         
            cv2.waitKey(2000)
    print('Undo pressed')

def reset():
    global frozen
    frozen = False
    #cv2.destroyAllWindows()
    #cv2.namedWindow("Viewmaster", cv2.WINDOW_NORMAL)
    #cv2.setMouseCallback("Viewmaster",draw)
    


def undo_all():
    global boxes,frame_data,frozen
    boxes = []
    frame_data = []
    print('Undone')
    reset()


def set_screen():
    global frozen,pls_freeze
    pls_freeze = False
    if not frozen:
        frozen = True
        print('Frozen')
        #cv2.createTrackbar("Stems", "Viewmaster", 1, 9, set_stem_numb)
		
def stem_num_circle():
    global px,py,stem_number,image
    print(px)
    print(py)
    print(stem_number)
    cv2.circle(image, (px, py), 20, (10, 15, 184), -1)
    cv2.putText(image, str(stem_number),  (px-10, py+10), cv2.FONT_HERSHEY_SIMPLEX, 1, BLACK, 2)

def report_num_of_snaps():
    global image
    snaps =  (len([name for name in os.listdir(confDir) if os.path.isfile(os.path.join(confDir, name))]))
    cv2.putText(image, str(snaps)+' snaps so far today!', (110,int(image.shape[0]/2)), font, 3, WHITE, 4, cv2.LINE_AA)
    cv2.imshow("Viewmaster",image)         
    cv2.waitKey(2000)
    

# The main loop
while(True):
    freeze_button = np.zeros((50,145,3))

    if not frozen:
        ret_val, image = cam.read()
        save_image = image.copy()
    else:
        image = save_image.copy()

    #add outline to buttons
    cv2.rectangle(save_button,pt1=(3,3),pt2=(save_button.shape[1]-3,save_button.shape[0]-3),color=(227,188,0),thickness=6)
    cv2.rectangle(undo_button,pt1=(3,3),pt2=(undo_button.shape[1]-3,undo_button.shape[0]-3),color=(0,0,255),thickness=6)
    if not frozen:
	    cv2.rectangle(freeze_button,pt1=(3,3),pt2=(freeze_button.shape[1]-3,freeze_button.shape[0]-3),color=(0,255,255),thickness=6)
	
    #add text to buttons
    cv2.putText(save_button, s_text, (stx,sty), font, font_size, save_colour, font_thickness, cv2.LINE_AA)
    cv2.putText(undo_button, u_text, (utx,uty), font, font_size, undo_colour, font_thickness, cv2.LINE_AA)
    if not frozen:
        cv2.putText(freeze_button, f_text, (ftx+3,fty), font, font_size, freeze_colour, font_thickness, cv2.LINE_AA)

    #add buttons
    sx_offset=sy_offset=5 #top left
    #image[sy_offset:sy_offset+save_button.shape[0], sx_offset:sx_offset+save_button.shape[1]] = save_button
    ux_offset=image.shape[1]-undo_button.shape[1]-5
    uy_offset=5
    #image[uy_offset:uy_offset+undo_button.shape[0], ux_offset:ux_offset+undo_button.shape[1]] = undo_button
    fx_offset = int((image.shape[1])/2) - int((freeze_button.shape[1])/2)
    fy_offset = 5
    if not frozen:
	    #image[fy_offset:fy_offset+undo_button.shape[0], fx_offset:fx_offset+freeze_button.shape[1]] = freeze_button
            pass

    #overlay rectangles
    for coords in boxes:
        cv2.rectangle(image,pt1=coords[0],pt2=coords[1],color= WHITE,thickness=2)

    #overlay circles
    for coords in frame_data:
        cv2.circle(image, coords[0], 20, RED, -1)
        cv2.putText(image, str(coords[1]),  (coords[0][0]-10, coords[0][1]+10), cv2.FONT_HERSHEY_SIMPLEX, 1, WHITE, 2)
    
    #show number preview or enhance pointer
    if frozen:
        cv2.circle(image, (px, py), 20, RED, -1)
        cv2.putText(image, str(stem_number),  (px-10, py-25), cv2.FONT_HERSHEY_SIMPLEX, 1, RED, 2)
    else:
        cv2.circle(image, (px, py), box_size, WHITE, 2)
        

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

    if intent == 13 or (intent == ord('s')):
        save_yolo()

    if (intent == ord('n')):
        report_num_of_snaps()

    if intent == 32:
        set_screen()

    if intent == int(ord('1')):
        stem_number = 1
        cv2.setTrackbarPos("Stems", "Viewmaster", 1)

    if intent == int(ord('2')):
        stem_number = 2
        cv2.setTrackbarPos("Stems", "Viewmaster", 2)

    if intent == int(ord('3')):
        stem_number = 3
        cv2.setTrackbarPos("Stems", "Viewmaster", 3)

    if intent == int(ord('4')):
        stem_number = 4
        cv2.setTrackbarPos("Stems", "Viewmaster", 4)
		
    if intent == int(ord('5')):
        stem_number = 5
        cv2.setTrackbarPos("Stems", "Viewmaster", 5)

    if intent == int(ord('6')):
        stem_number = 6
        cv2.setTrackbarPos("Stems", "Viewmaster", 6)

    if intent == int(ord('7')):
        stem_number = 7
        cv2.setTrackbarPos("Stems", "Viewmaster", 7)

    if intent == int(ord('8')):
        stem_number = 8
        cv2.setTrackbarPos("Stems", "Viewmaster", 8)

    if intent == int(ord('9')):
        stem_number = 9
        cv2.setTrackbarPos("Stems", "Viewmaster", 9)

    if (intent == 27) or (intent == ord('q')):
        print('Bye!')
        break
    
cv2.destroyAllWindows()
cam.release()
