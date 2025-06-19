# yuque-to-hexo
让语雀中的文章也能轻松同步到Hexo博客

个人习惯了用语雀写笔记，想转到个人博客做推广发现没有合适的工具帮助，且语雀的图床不允许外部引用，就写了这个脚本来将图片下载并保存到本地，借助的是DeepSeek，非常厉害

# 使用教程

## 初始化环境

初次使用请修改博客根路径为你本地hexo博客的根路径，

![image](https://github.com/user-attachments/assets/3331e623-73c4-4e2f-9515-922432c7a287)


运行脚本之后也能在图形化界面修改

![image](https://github.com/user-attachments/assets/33a2cd16-e723-4341-a442-28eea5c8613c)


## 修改hexo配置

在博客根路径的`**_config.yml**`中添加以下配置，使所有资源路径不使用绝对路径：

```plain
relative_link: true
```

![image](https://github.com/user-attachments/assets/39939762-9c5f-492d-8602-05dcc9f54182)

 自动为每篇文章创建资源文件夹

```plain
post_asset_folder: true
```

![image](https://github.com/user-attachments/assets/d9383e09-a2f5-4da2-aaf4-57202d32457d)


## 导出语雀文档

保存为markdown格式，路径任意

![image](https://github.com/user-attachments/assets/16048c55-472d-4e80-9adc-79e49c137022)


![image](https://github.com/user-attachments/assets/3601e68c-4766-42b4-837d-96b65560fabc)


## 运行脚本

### 输出路径

结果输出两项内容，一个是语雀图床替换之后的md文件，另一个是保存图片的同名文件夹

1. 自定义博客根路径之后会默认保存在\source\_posts目录下
2. 置空则保存在你的md文件所在目录
3. 也可自定义位置将这两项内容保存任意位置

![image](https://github.com/user-attachments/assets/a9f42078-4d35-46be-aa97-756afddd817b)


### 拖入MD文件

hexo 文章开头需要固定格式，需要文章标题和日期，这里我多加了文章分类和标签，使用英文逗号隔开！

注意：

1. 填写分类时会从博客根路径的\public\categories目录读取历史分类，可选中历史分类或者手动输入添加分类，逗号隔开，层级分类，从左到右级别依次递减
2. 填写标签时会从博客根路径的\public\tags目录读取历史标签，可选中历史标签或者手动输入添加标签，逗号隔开

![image](https://github.com/user-attachments/assets/8bc35c8e-1c80-4009-a7fb-b1bc22006c77)


## 开始处理

有百分比进度条和下载日志

![image](https://github.com/user-attachments/assets/5cc90308-4139-466a-9dbb-b82310119257)


可以看到已经上传到我的博客_posts目录下了

![image](https://github.com/user-attachments/assets/d88de29c-440b-4411-bd3e-7b179fd7666c)


MD文件可正常解析图片

![image](https://github.com/user-attachments/assets/8416b98b-5411-4adb-9c9e-9fc5d46ec321)


## 本地服务启动

```bash
hexo clean
hexo g & hexo s
```

![image](https://github.com/user-attachments/assets/e74671fe-86b3-4756-b17f-550b308711dd)


![image](https://github.com/user-attachments/assets/49c731ee-db49-4695-af2f-4eb5db9771d0)


没什么问题就可以同步到博客了

```bash
hexo d
```

![image](https://github.com/user-attachments/assets/046314a8-ff91-4584-b23e-df3bcee78b3f)


![image](https://github.com/user-attachments/assets/6bc1aad2-26d3-4f96-b966-9f389136dfe2)


# 版本更新

## 1.0.0

支持单md文件下载	不支持多文件下载

不支持多线程

目前只支持文件拖拽上去

