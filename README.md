# 介绍
## 使用方法
` python3 main.py --weights best.pt `

-----------------
## 环境配置
### 所需环境与yolov5 v6.0相同

-----------------

## 模型训练
### 使用 yolov5 v6.0 的train训练的

----------------
## 主要修改文件
### main.py，是主要运行文件
### video_capture.py，是相机参数的修改，除了 Video_capture 的类变量；可以看看视频保存74行的颜色补偿
### to_inference.py，是推理的主要文件 init 函数处修改图像尺寸需要与训练的大小相等；to_inference 函数修改自信度，以及后续矿石位置信息的解算
### use_serial.py，与电控的通讯
-----------------

## 要是代码突然间有问题并且是与深度学习那边有关的大概率是 torch 或者 torchvision 的问题

`pip3 uninstall torch torchvision`

`pip3 install torch==1.9.0 torchvision==0.10.0`

