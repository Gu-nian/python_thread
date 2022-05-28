模型是使用 yolov5 v6.0 的train训练的

` python3 main.py --weights best.pt `

图像尺寸在加载模型处修改

### 要是代码突然间有问题并且是与深度学习那边有关的大概率是 torch 或者 torchvision 的问题

`pip3 uninstall torch torchvision`
`pip3 install torch==1.9.0 torchvision==0.10.0`
