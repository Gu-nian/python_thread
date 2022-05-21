import video_capture  
import function
import cv2
import numpy as np
import mvsdk
from utils.torch_utils import time_sync
import argparse
import threading

# 传入模型位置
def parse_opt():
    parser = argparse.ArgumentParser()
    # 自启动 default 要改成绝对路径
    parser.add_argument('--weights', nargs='+', type=str, default='/home/oyc/workspace/python_thread/best (3).pt', help='model path(s)')
    parser.add_argument('--is_store', nargs='+', type=int, default= 0 , help='0 NO 1 YES')
    parser.add_argument('--store_mode', nargs='+', type=int, default=0 , help='0 deal with frame 1 original frame')
    opt = parser.parse_args()
    return opt

# mode = 0 为处理后的图像 
# mode = 1 为原图
def run(Video, Fun, mode = 0):
    
    while (cv2.waitKey(1) & 0xFF) != ord('q'):
        try:
            t2 = time_sync()
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(Video.hCamera, 200)
            mvsdk.CameraImageProcess(Video.hCamera, pRawData, Video.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(Video.hCamera, pRawData)
            frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(Video.pFrameBuffer)
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth, 1 if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO8 else 3) )
            
            Fun.to_inference(frame, Fun.device, Fun.model, Fun.imgsz, Fun.stride)

            t3 = time_sync()

            if Video.IS_SAVE_VIDEO:
                try:
                    if mode == 0:
                        Video.out.write(frame)
                        cv2.imshow("frame",frame)
                    else :
                        Video.out.write(Fun.store_frame)
                        cv2.imshow("store_frame",Fun.store_frame)
                except:
                    print("Write Frame Error")

            print("Inference == " + str(1/(t3 - t2)))
        except mvsdk.CameraException as e:
            if e.error_code != mvsdk.CAMERA_STATUS_TIME_OUT:
                print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message) )
    if Video.IS_SAVE_VIDEO:
        try:
            Video.out.release()
        except:
            print("Release Frame Error")
    cv2.destroyAllWindows()
    # 关闭相机
    mvsdk.CameraUnInit(Video.hCamera)
    # 释放帧缓存
    mvsdk.CameraAlignFree(Video.pFrameBuffer)
    

if __name__ == "__main__":
    opt = parse_opt()
    # 0 不储存图像
    # 1 储存图像
    Video = video_capture.Video_capture(**vars(opt))
    Fun = function.Function(**vars(opt))

    thread2 = threading.Thread(target=(Fun.send_data),daemon=True)

    thread2.start()
    run(Video,Fun,**vars(opt))

