from pickle import FALSE
from typing import List

import cv2
import numpy as np
import torch

from models.common import DetectMultiBackend
from utils.general import check_img_size,non_max_suppression,scale_coords, xyxy2xywh
from utils.torch_utils import select_device

class Inference(object):

    DEVIATION_X = 0
    DIRECTION = 0
    HIGH_EIGHT = 0
    LOW_EIGHT = 0
    # 目标位置
    TARGET_X = 0
    # 判断夹矿方式
    FLAG = 1

    def __init__(self,weights):
        # 加载模型
        self.device = select_device('cpu')
        self.model = DetectMultiBackend(weights, device=self.device)
        self.stride = self.model.stride 
        self.imgsz = check_img_size((320,320),s=self.stride)
        self.model.model.float()
    
    def radix_sort(arr:List[int]):
        n = len(str(max(arr)))  # 记录最大值的位数
        for k in range(n):#n轮排序
            # 每一轮生成10个列表
            bucket_list=[[] for i in range(10)]#因为每一位数字都是0~9，故建立10个桶
            for i in arr:
                # 按第k位放入到桶中
                bucket_list[i//(10**k)%10].append(i)
            # 按当前桶的顺序重排列表
            arr=[j for i in bucket_list for j in i]
        return arr

    def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleFill=False, scaleup=True, stride=32):
        # Resize and pad image while meeting stride-multiple constraints
        
        shape = im.shape[:2]  # current shape [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        if not scaleup:  # only scale down, do not scale up (for better val mAP)
            r = min(r, 1.0)

        # Compute padding
        ratio = r, r  # width, height ratios
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding
        if auto:  # minimum rectangle
            dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding
        elif scaleFill:  # stretch
            dw, dh = 0.0, 0.0
            new_unpad = (new_shape[1], new_shape[0])
            ratio = new_shape[1] / shape[1], new_shape[0] / shape[0]  # width, height ratios

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
        return im, ratio, (dw, dh)

    # 进行推理 绘制图像 结算出最优 发送数据
    def to_inference(self, frame, device, model, imgsz, stride,mode = 1, conf_thres=0.45, iou_thres=0.45):
        img_size = frame.shape
        img0 = frame 
        img = Inference.letterbox(img0,imgsz,stride=stride)[0]
        img = img.transpose((2,0,1))[::-1]
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(device)
        img = img.float()
        img /= 255.

        # 每次初始化防止数据未刷新自己走，可能会慢一些
        Inference.DEVIATION_X = 0
        Inference.DIRECTION = 0
        Inference.HIGH_EIGHT = 0
        Inference.LOW_EIGHT = 0

        if len(img.shape) == 3:
            img = img[None]

        pred = model(img)
        pred = non_max_suppression(pred, conf_thres, iou_thres, agnostic=False)
        aims = []
        confs = []
        arr = []

        for i ,det in enumerate(pred): 
            gn = torch.tensor(img0.shape)[[1,0,1,0]]
            if len(det):
                det[:,:4] = scale_coords(img.shape[2:], det[:, :4],img0.shape).round()
                for *xyxy, conf, cls in reversed(det):
                    xywh = (xyxy2xywh(torch.tensor(xyxy).view(1,4)) / gn).view(-1).tolist()
                    line = (cls, *xywh)
                    aim = ('%g ' * len(line)).rstrip() % line 
                    aim = aim.split(' ')
                    # 筛选出自信度大于70%
                    if float(conf) > 0.7:
                        aims.append(aim)
                        confs.append(float(conf))

            if len(aims):
                for i,det in enumerate(aims):
                    tag, x_center, y_center, width, height = det
                    x_center, width = float(x_center) * img_size[1], float(width) * img_size[1]
                    y_center, height = float(y_center) * img_size[0], float(height) * img_size[0]
                    top_left = (int(x_center - width * 0.5), int(y_center - height * 0.5))
                    top_right = (int(x_center + width * 0.5), int(y_center - height * 0.5))
                    bottom_right = (int(x_center + width * 0.5), int(y_center + height * 0.5))

                    Inference.draw_inference(frame, top_left, top_right, bottom_right, tag, confs, i, mode)
                    # 计算出矿石位置与目标点的距离大小
                    arr.append(int(x_center - Inference.TARGET_X)) 
                # 进行一个比较取最接近目标点的 可以用其他比较算法 这里选择了快速排序
                if abs(Inference.radix_sort(arr)[0]) < abs(Inference.radix_sort(arr)[len(arr)-1]):
                    Inference.DEVIATION_X = Inference.radix_sort(arr)[0]
                else:
                    Inference.DEVIATION_X = Inference.radix_sort(arr)[len(arr)-1]

                if mode == True:
                    cv2.putText(frame, "real_x = " + str(Inference.DEVIATION_X), (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
                # 这里进行了位运算的操作是仿照C++那边的，经过实测可以不进行位运算影响不大
                Inference.HIGH_EIGHT = (abs(Inference.DEVIATION_X) >> 8) & 0xff
                Inference.LOW_EIGHT = abs(Inference.DEVIATION_X)  & 0xff
                # 空接与非空接
                if Inference.FLAG == 1:
                    if abs(Inference.DEVIATION_X ) < 24:
                        Inference.DEVIATION_X  = 0
                else :
                    if abs(Inference.DEVIATION_X ) < 24:
                        Inference.DEVIATION_X  = 0
                if Inference.DEVIATION_X > 0:
                    Inference.DIRECTION = 1

            Inference.draw_data(frame, img_size, mode)
    # 绘制推理框
    def draw_inference(frame, top_left, top_right, bottom_right, tag, confs, i, mode = 1):
        if mode == True:
            cv2.rectangle(frame, top_left, bottom_right, (0, 255, 255), 3, 8)
            cv2.putText(frame,str(float(round(confs[i], 2))), top_right, cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.putText(frame, tag, top_left, cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 255), 4)
    # 将数据显示出来
    def draw_data(frame, img_size, mode = 1):
        if mode == True:
            cv2.putText(frame, "judge_x = " + str(Inference.DEVIATION_X), (0, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.line(frame, (Inference.TARGET_X, 0), (Inference.TARGET_X, int(img_size[0])), (255, 0, 255), 3)
            cv2.putText(frame, 'direction: ' + str(Inference.DIRECTION), (0, 160), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.putText(frame, 'high_eight: ' + str(Inference.HIGH_EIGHT), (0, 210), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)
            cv2.putText(frame, 'low_eight: ' + str(Inference.LOW_EIGHT), (0, 260), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2)