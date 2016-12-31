# -*- coding:utf-8 -*-
import os
import re
import pickle
import time
import poplib
import imaplib
import chardet
import shutil
import base64
from bs4 import UnicodeDammit
from PyQt5 import QtCore,QtWidgets
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
from email import message_from_file
from threading import Thread,Lock
import smtplib
from pprint import pprint
import string
import email
import parameter as gl

APPNAME = 'PxMail v3.0'
counter = 0
mutex = Lock()

class sendingThread(QtCore.QThread):

    triggerSuccess = QtCore.pyqtSignal()
    triggerFail = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(sendingThread, self).__init__(parent)

    def run(self):
        try:
            smtp_backend = smtplib.SMTP(gl.smtphost, 25)
            if gl.smtpssl:
                smtp_backend.starttls()
            smtp_backend.login(gl.username,gl.password)
            smtp_backend.sendmail(gl.username, gl.receivers, gl.message.as_string())
        except Exception as e:
            gl.error=str(e)
            self.triggerFail.emit()
            return

        self.triggerSuccess.emit()


class loadingThread(QtCore.QThread):
    trigger1 = QtCore.pyqtSignal()
    trigger2 = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(loadingThread, self).__init__(parent)

    def run(self):
        global pop_backend
        try:
            if gl.popssl:
                pop_backend = poplib.POP3_SSL(gl.pophost,gl.popport)           #SSL加密登陆
            else:
                pop_backend = poplib.POP3(gl.pophost,gl.popport)
            pop_backend.user(gl.username)
            pop_backend.pass_(gl.password)
            resp, gl.mails_number, octets = pop_backend.list()

            self.trigger1.emit()

        except Exception as e:
            gl.error=str(e)
            print (e)
            self.trigger2.emit()


class MyThread(Thread):
    def __init__(self):
        Thread.__init__(self)

    def run(self):
        global counter, mutex,mails
        time.sleep(0.1)
        try:

            if gl.popssl:
                ipop_backend = poplib.POP3_SSL(gl.pophost,gl.popport)           #SSL加密登陆
            else:
                ipop_backend = poplib.POP3(gl.pophost,gl.popport)
            ipop_backend.user(gl.username)
            ipop_backend.pass_(gl.password)

            mutex.acquire()
            MailIndex = len(gl.mails_number)-counter
            counter += 1
            mutex.release()
            resp, lines, octets = ipop_backend.retr(MailIndex)
            msg_byte = b'\r\n'.join(lines)
            msg_content=msg_byte.decode(chardet.detect(msg_byte)['encoding'])

            msg = Parser().parsestr(msg_content)

            mails.append((len(gl.mails_number)-MailIndex+1,msg))
            gl.step=counter+1
            # print(MailIndex)

        except Exception as e:
            print (str(e)+'  Mythread' +str(counter))

#接收邮件线程
class receiveThread(QtCore.QThread):
    triggerNumber = QtCore.pyqtSignal()
    triggerFinish = QtCore.pyqtSignal()
    def __init__(self,parent=None):
        super(receiveThread, self).__init__(parent)
        self.cache=MailCache()
        self.running=True
    def run(self):
        gl.cathe_folder_path = os.path.join(gl.cache_path, gl.folder_path)
        if self.cache._is_stale(gl.folder_path) or gl.force_refresh == True :
            gl.force_refresh = False
            global mails,counter
            mails=[]
            counter=0
            threads=[]
            gl.step=0
            for i in range(len(gl.mails_number)):

                my_thread = MyThread()
                my_thread.start()
                threads.append(my_thread)

            for thread in threads:                  #回收线程
                thread.join()
                print(threads.index(thread))
                gl.step=threads.index(thread)+1
                self.triggerNumber.emit()

                    # if self.running:
                    #     resp, lines, octets = pop_backend.retr(len(gl.mails_number)-i)
                    #     msg_byte = b'\r\n'.join(lines)
                    #     msg_content=msg_byte.decode(chardet.detect(msg_byte)['encoding'])
                    #
                    #     msg = Parser().parsestr(msg_content)
                    #
                    #     mails.append((i,msg))
                    #     gl.step=i+1
                    #     self.triggerNumber.emit()
                    #
                    #     print(i)
                    # else:
                    #     return

            CleanDir(gl.cathe_folder_path)                  #清除收件夹
            for mail in mails:
                with open(os.path.join(gl.cathe_folder_path, str(mail[0]) + '.ml'), 'w') as mailcache:
                    mailcache.write(mail[1].as_string())

            self.cache._renew_state(gl.folder_path)

        gl.emails = []
        files = os.listdir(gl.cathe_folder_path)                                                       #列出目录下的文件
        files.sort(key=lambda x:int(x[:-3]))                                                  #整理文件顺序
        mail_files = [f for f in files if os.path.isfile(os.path.join(gl.cathe_folder_path, f))]
        for mail_file in mail_files:
            try:
                path=os.path.join(gl.cathe_folder_path, mail_file)
                with open(path, 'r') as mail_handle:
                    gl.emails.append({  "path": path,
                                        "message":message_from_file(mail_handle) })
            except Exception as e:
                    print(e)+'save'
        gl.March_ID=gl.emails                                   #匹配到的邮件等于所有邮件
        self.cache._commit_state()

        self.triggerFinish.emit()


    def stop(self):
        self.running=False




#搜索线程
class searchThread(QtCore.QThread):
    trigger = QtCore.pyqtSignal()
    def __init__(self, parent=None):
        super(searchThread, self).__init__(parent)

    def run(self):
        gl.March_ID=[]                                                  #匹配符合条件的邮件
        for email in gl.emails:
            info=get_info(email)
            if (gl.string in info["subject"]) or (gl.string in info["content"]) or (gl.string in info["addr"]):
                gl.March_ID.append(email)
                data=info["subject"]+info["content"]+info["addr"]
                pattern = re.compile(gl.string)
                dataMatched = re.findall(pattern, data)                        #匹配所有关键字，背景高亮
                gl.highlight.setHighlightData(dataMatched)
                gl.highlight.rehighlight()

        self.trigger.emit()







class MailCache():
    """
    Emails cache. Is totally independent from the back-end
    """
    receive = None
    state_path = ''
    cache_state = {}
    MAX_AGE = 3600

    def __init__(self,):
        gl.cache_path = os.path.join('cache', gl.username)
        gl.attach_path=os.path.join(gl.cache_path, 'attach')

        gl.fold_config = os.path.join(gl.cache_path, 'fold_config.ini')
        gl.draft_path=os.path.join(gl.cache_path, '草稿夹')
        gl.send_path=os.path.join(gl.cache_path, '已发送')
        gl.delete_path=os.path.join(gl.cache_path, '已删除')
        gl.contact_path=os.path.join(gl.cache_path, 'contact.csv')

        self.state_path = os.path.join(gl.cache_path, 'cache.state')

        if not os.path.isdir(gl.cache_path):                            #创建每个用户的目录
            os.makedirs(gl.cache_path)
        if not os.path.isdir(os.path.join(gl.cache_path, '草稿夹')):
            os.makedirs(os.path.join(gl.cache_path, '草稿夹'))
        if not os.path.isdir(os.path.join(gl.cache_path, '已删除')):
            os.makedirs(os.path.join(gl.cache_path, '已删除'))
        if not os.path.isdir(os.path.join(gl.cache_path, '收件夹')):
            os.makedirs(os.path.join(gl.cache_path, '收件夹'))
        if not os.path.isdir(os.path.join(gl.cache_path, '已发送')):
            os.makedirs(os.path.join(gl.cache_path, '已发送'))
        if not os.path.isdir(os.path.join(gl.cache_path, 'attach')):
            os.makedirs(os.path.join(gl.cache_path, 'attach'))
        if not os.path.isfile(os.path.join(gl.cache_path, 'contact.csv')):
            f=open(os.path.join(gl.cache_path, 'contact.csv'),'w')
            f.close()

        self._load_state()


    def list_mail(self, folder, force_refresh):
        folder_path = os.path.join(gl.cache_path, folder)
        if self._is_stale(folder) or force_refresh == True:
            mails = self.receive.list_mail()
            for mail in mails:
                with open(os.path.join(folder_path, str(mail[0]) + '.ml'), 'w') as mailcache:
                    mailcache.write(mail[1].as_string())
            self._renew_state(folder)
        mails = []
        files = os.listdir(folder_path)                                                       #列出目录下的文件
        files.sort(key=lambda x:int(x[:-3]))                                                  #整理文件顺序
        mail_files = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]
        for mail_file in mail_files:
            with open(os.path.join(folder_path, mail_file), 'r',encoding= 'utf-8') as mail_handle:
                mails.append(message_from_file(mail_handle))
        self._commit_state()
        return mails


    def _is_stale(self, folder):                                                #不干净，被更改过
        if folder in self.cache_state:
            return time.time() - self.cache_state[folder] > self.MAX_AGE
        else:
            return True


    def _renew_state(self, folder):
        self.cache_state[folder] = time.time()

    def _load_state(self):
        if os.path.isfile(self.state_path):
            with open(self.state_path, 'rb') as cache:
                self.cache_state = pickle.load(cache)

    def _commit_state(self):
        with open(self.state_path, 'wb') as cache:
            pickle.dump(self.cache_state, cache)

def delete_mail(index):
    if gl.popssl:
        ipop_backend = poplib.POP3_SSL(gl.pophost,gl.popport)           #SSL加密登陆
    else:
        ipop_backend = poplib.POP3(gl.pophost,gl.popport)
    ipop_backend.user(gl.username)
    ipop_backend.pass_(gl.password)

    ipop_backend.dele(len(gl.mails_number)-index)



 #清除目录下文件
def CleanDir( Dir ):
    if os.path.isdir( Dir ):
        paths = os.listdir( Dir )
        for path in paths:
            filePath = os.path.join( Dir, path )
            if os.path.isfile( filePath ):
                try:
                    os.remove( filePath )
                except os.error:
                    print( "remove %s error." %filePath )#引入logging
            elif os.path.isdir( filePath ):
                if filePath[-4:].lower() == ".svn".lower():
                    continue
                shutil.rmtree(filePath,True)
    return True




def refresh_mail():
    if gl.popssl:
        ipop_backend = poplib.POP3_SSL(gl.pophost,gl.popport)           #SSL加密登陆
    else:
        ipop_backend = poplib.POP3(gl.pophost,gl.popport)
    ipop_backend.user(gl.username)
    ipop_backend.pass_(gl.password)

    resp, gl.mails_number, octets = ipop_backend.list()



def guess_charset(msg):                             #获得字符编码方法
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
            charset=charset.split(';')[0]
    return charset
def decode_str(s):                                      #字符编码转换方法
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def decode_image_part(part, content_type):
        image_bytes = part.get_payload(decode=True)
        # image_base64 = base64.b64encode(image_bytes)
        return image_bytes
        # return '<img src="data:{0};base64,{1}">'.format(content_type,image_base64)

def get_info(msg, indent = 0):
    subject = ''
    addr = ''
    content = ''
    date=''
    body_image = ''
    html=''
    attachments=[]
    received=''
    if indent == 0:
        for header in ['From', 'Subject','Date','Received']:
            value = msg.get(header, '')
            if value:
                if header=='Subject':
                    subject = decode_str(value)
                elif header=='Date':
                    date = decode_str(value)
                elif header=='Received':
                    received = decode_str(value)
                else:
                    hdr, addr = parseaddr(value)
    for part in msg.walk():
        filename = part.get_filename()
        content_type = part.get_content_type()
        charset = guess_charset(part)
        if filename:
            filename = decode_str(filename)
            binary_data = part.get_payload(decode=True)
            file_path=os.path.join(gl.attach_path, filename)
            attachment = Attachment(filename, binary_data, file_path)
            attachments.append(attachment)

            fEx = open(file_path, 'wb')                 #写到temp文件夹里
            fEx.write(binary_data)
            fEx.close()

        elif 'image/png' in content_type \
                        or 'image/jpeg' in content_type \
                        or 'image/jpg' in content_type \
                        or 'image/gif' in content_type:
            body_image=part.get_payload(decode=True)

            #粗略的做了一下读取图片并保存到本地
            content_id = part.get('Content-ID', '').lower()
            imageName='cid:'+content_id.strip('<').strip('>')
            fEx = open(imageName, 'wb')
            fEx.write(body_image)
            fEx.close()


        elif content_type == 'text/plain':
            if charset:
                # content = part.get_payload(decode=True).decode('unicode_escape')      #处理新浪邮箱附件邮件的中文字符

                content = part.get_payload(decode=True).decode(charset)

        elif content_type == 'text/html':
            if charset:
                html = part.get_payload(decode=True).decode(charset)

    return {
        "subject": subject,
        "addr": addr,
        "content": content,
        "html":html,
        "date":date,
        "received":received,
        "body_image":body_image,
        "attachment":attachments
        }



class Attachment(object):

    def __init__(self, filename, binary_data, path='',content_type=None, content_disposition=None):
        self.filename = filename
        self.binary_data = binary_data
        self.path=path
        self.content_type = content_type
        self.content_disposition = content_disposition
