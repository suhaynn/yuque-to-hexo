# yuque-to-hexo
让语雀中的文章也能轻松同步到Hexo博客

个人习惯了用语雀写笔记，想转到个人博客做推广发现没有合适的工具帮助，且语雀的图床不允许外部引用，就借助了最近非常火的DeepSeek写了这个脚本来将图片下载并保存到本地，用起来非常丝滑，非常厉害啊，国产之光！

# 使用教程
## 导出语雀文档
保存为markdown格式，路径任意

![image](https://github.com/user-attachments/assets/6d730384-4062-45ec-95b3-67c36f9fbff3)

![image](https://github.com/user-attachments/assets/bff7ca84-9406-422f-8a19-05b1ccd66464)


## 运行脚本
### 输出路径
结果输出两项内容，一个是语雀图床替换之后的md文件，另一个是保存图片的同名文件夹

1. 可在脚本中将路径修改为你的博客_posts目录
2. 置空则保存在你的md文件所在目录
3. 也可自定义位置将这两项内容保存任意位

![image](https://github.com/user-attachments/assets/f11158a6-1b33-44d5-a3c5-ff97c26616d5)


### 拖入MD文件
hexo 文章开头需要固定格式，需要文章标题和日期，这里我多加了文章分类和标签，使用英文逗号隔开！

![image](https://github.com/user-attachments/assets/d41ae08e-d5d3-41e0-972a-f69d163cc593)


## 开始处理
有百分比进度条和下载日志

![image](https://github.com/user-attachments/assets/32ac2e95-866f-4135-b5db-8189c0faa654)


可以看到已经上传到我的博客_posts目录下了

注意！！！

如果此时你打开md文件，会发现路径少了一层图片目录，是因为如果加上了这个图片文件夹的名称则hexo会找不到对应的图片，具体的你可以试一下，目前这样子是可以用的，用就完了。

![image](https://github.com/user-attachments/assets/7bd99148-78e1-4757-ac78-d6f84cbde9d4)


## 本地服务启动
```bash
hexo g & hexo s
```
![image](https://github.com/user-attachments/assets/0ebdcbf2-0509-45e3-bc8d-c619035390f1)
可以正常访问

![image](https://github.com/user-attachments/assets/5b0efc59-d0d9-4498-80e6-fd7d74216bf5)

![image](https://github.com/user-attachments/assets/24ce4d32-f0b3-48fd-b97f-0dde3d9cec39)


# 版本更新
## 1.0.0
支持单md文件下载	不支持多文件下载

不支持多线程

目前只支持文件拖拽上去

