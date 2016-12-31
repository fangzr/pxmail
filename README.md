# 软件课设：邮件管理系统


----------
## 一 开发环境 ##


| 操作系统 |   解释器   | 依赖模块 | 图形开发组件 |
|----------------|--------------|------------------|----------------------|
| Windows | python>=3.4.4 | pyqt5 | QtDesigner|

**为获得最佳用户体验，请使用Windows8，python3.4.4 运行并测试**

### 脚本执行方法 ###
 在Src目录下，运行 `python3  pxmail.py.`


### 可执行文件运行方法 ###
直接运行Bin目录下已打包好的可执行文件（pxmail.exe）


-------------------

## 二 基本特点 ##
1. 采用python3编写，编码风格良好。
2. 结构清晰，代码耦合度低，可扩展性强，其中：正则引擎，GUI，邮件解析器等，皆为通用组件。
3. 源代码注释详尽
4. 实现效率高，核心模块方法都是线性级别。
5. 跨平台，可在Linux、Windows、OSX运行

## 三 实现功能 ##

### 基本功能 ###

题目要求的基本功能全部实现：

1. 有较良好的图形界面
2. 支持邮件的收发
3. 支持邮件的转发、回复
4. 支持邮件管理：浏览、查找、删除
5. 支持QQ、sina、163、hust邮箱
6. 支持html以及文本邮件的接收显示



### 拓展功能 ###


1. 支持多附件邮件接收和发送
2. 支持邮件发信人、主题、内容检索
3. 按日期、发信人、主题邮件排序，支持升序、降序
4. 邮件搜索采用正则表达引擎
5. 实现了邮件内容语法高亮，提高用户体验
6. 支持发送图片，截屏
7. 通讯簿导入，导出，与Foxmail兼容
8. 记住密码功能，并保存本地，用户名会加密
9. 炫酷黑色皮肤，并可以切换皮肤
10. 多线程接收邮件，基本可以达到秒收


## 四 项目架构 ##

### 1. 源码目录结构 ###
       Src
        ├── pxmail.py
        ├── parameter.py
        ├── mail.py
        ├── gui.py
        ├── backend.py
        ├── syntax_pars.py
        └── ui
            ├── accountdialog.ui
            ├── composewindow.ui
            ├── Contact.ui
            ├── mainwindow.ui
            ├── receivingDialog.ui
            ├── searchDialog.ui
            └── sendDialog.ui

__简单说明：__

+ `pxmail.py` 入口主程序
+ `parameter.py` 包含了一些定义的全局变量
+ `mail.py` 邮件后端接收以及解析
+ `ui/` 界面的实现ui文件


### 2. 程序结构 ##

+ `gui.py`
 GUI主要接口，实现了登陆、浏览、发送等界面

``` python
class AccountDialog(QtWidgets.QMainWindow)		#登陆界面
class MainWindow(QtWidgets.QMainWindow):		#邮件浏览主界面          
class ComposeWindow(QtWidgets.QMainWindow)		#发送邮件界面
class ReceiveDialog(QtWidgets.QDialog)			#接收邮件对话框
class SendDialog(QtWidgets.QDialog)				#发送邮件对话框
```
####主界面MainWindow
``` python
重要接口：
def OnActivated()							#排序选项Combobox
def mailDisplay()							#邮件按排序显示目录
def save_binary_file()						#附件保存为二进制文件
def openFile()								#打开附件
def onComposeMail()							#打开发送邮件界面
def onRefresh()								#刷新邮件列表
def onContactList()							#显示联系人列表
def InitSearchEdit()						#初始化搜索框
def onReply()								#回复邮件
def onForward()								#转发邮件
def onDelete()								#删除邮件
def onFolderSelected()						#显示邮件夹目录
def onMailSelected()						#显示邮件内容
```
####登陆界面AccountDialog
``` python
重要接口：
def hideManualSet()							#隐藏手动设置
def showManualSet()							#展开手动设置
def txtuserEdited()						#文本编辑完成自动显示服务器文本
def ontextChanged()							#文本框自动补全
def onLogin()								#登陆邮箱
```
####发送界面ComposeWindow
``` python
重要接口：
def onAttachment()							#添加附件
def ontextChanged()							#文本框自动补全
def onSend()								#发送邮件
```


+ `mail.py`
包含了邮件接收、发送线程，邮件解析器，邮件缓存机制
``` python
class loadingThread(QtCore.QThread)				#登陆线程
class sendingThread(QtCore.QThread)				#邮件发送线程
class receiveThread(QtCore.QThread)				#邮件接收线程
class MailCache()								#邮件缓存、记录时间戳
def get_info(msg, indent = 0)					#邮件解码，获取内容
```
  
####邮件缓存MailCache
``` python
重要接口：
def _is_stale(self, folder)							#检测上一次时间戳
def _renew_state(self, folder)						#刷新时间戳
def _load_state(self)								#读取时间戳
def _commit_state(self)								#写入时间戳
```

  + `syntax_pars.py`
搜索引擎语法高亮机制
``` python
def format(color, style='')						#返回给定属性的格式
class PythonHighlighter(QSyntaxHighlighter)		#对Python语言的语法高亮
```




## 五 程序逻辑 ##

### 接收流程 ###
```flow
st=>start: 登陆邮箱
e=>end: 显示在前端
op=>operation: POP3协议收取邮件
cond=>condition: 刚收过邮件？

st->cond->op->e
cond(yes)->e
cond(no)->op
```

1. 先从登陆界面进入主界面
2. 调用`onFolderSelected(self, folder)`选择当前显示目录
3. 启动`receiveThread()`接收线程
4. 调用`MailCache()`创建当前用户的缓存邮件夹，记下当前时间戳
5. 若当前时间遇上一次时间戳在一个周期内，则直接显示在前端，否则就先采用POP3协议从邮件服务器收取邮件到本地
6. 调用`mailDisplay(self)`输出结果

## 六 更新日志 ##
>**2016/10/7   本次更新**：
1.实现基本的SMTP和POP3协议收发邮件
2.实现了UI界面的整体框架

>**2016/10/23  本次更新**：
1.解决了收取邮件时画面卡顿的问题
2.支持qq、sina、163、126、hust邮箱
3.增加了登陆失败提示
4.增加了回车快捷键

>**2016/11/3   本次更新**：
1.增加了显示收信人、日期、主题
2.增加了回复、转发功能
3.增加了搜索功能
4.初步尝试对界面做了小幅改动，之后还会修改

>**2016/11/10  本次更新**：
1.对邮件协议里的日期做了格式化处理
2.增加了对邮件按日期、收信人、主题排序
3.支持带附件邮件的接收，保存到本地，暂未想好如何显示到前端
4.搜索支持关键词背景高亮
5.实现了邮件内容语法高亮，提高用户体验

>**2016/11/12 本次更新**：
1.增加了附件显示，能以系统默认程序打开和另存为

>**2016/12/4 本次更新**：
1.支持多用户接受邮件，收件人以分号分隔
2.美化了登陆界面，增加了文字淡入淡出效果，提高了用户体验
3.修复了部分HTML邮件显示异常的BUG
4.添加了富文本编辑器
5.写邮件时可以保存邮件至草稿箱
6.支持html邮件发送
7.修复了QQ邮箱不能发送邮件的问题

>**2016/12/16 本次更新**：
1.完成了联系人模块
2.支持联系人导入导出csv文件，并与foxmail兼容

>**2016/12/17 本次更新**：
1.修复了删除联系人会导致界面崩溃的BUG

>**2016/12/20 本次更新**：
1.增加了记住密码机制
2.解决了频繁刷新界面会崩溃的BUG
3.解决了发送附件文件格式的问题
4.支持发送图片
5.支持接收图片
6.可以在发邮件里面添加联系人
7.发送邮件的对话框美化，加了进度条
8.可以删除邮件，并从服务器上也一并删除

>**2016/12/28 本次更新**：
1.多线程并行接收邮件，基本可以达到秒收
2.可以发送多个邮件，并可以编辑管理，删除
3.实现了多个附件的接收
4.回复和转发也支持转发附件了..

>**2016/12/31 本次更新**：
1.字体黑转白，由于部分html邮件是黑色字体，增加了可以切换皮肤的功能
2.支持邮件夹管理，添加，删除


## 七 运行截图 ##

![登陆](http://img.blog.csdn.net/20161231184516650?zNDE=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![收信](http://img.blog.csdn.net/20161231184714902?zNDE=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![联系人](http://img.blog.csdn.net/20161231184734903?zNDE=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![写邮件](http://img.blog.csdn.net/20161231184803669?zNDE=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)

![主界面](http://img.blog.csdn.net/20161231184832920?zNDE=/font/5a6L5L2T/fontsize/400/fill/I0JBQkFCMA==/dissolve/70/gravity/SouthEast)