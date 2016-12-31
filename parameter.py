global username,password,pophost,smtphost,popport,smtpport,popssl,smtpssl
global emails,cache_path,folder_path,attach_path,file_path,cathe_folder_path,draft_path,send_path,contact_path,delete_path
global read_files,read_path,fold_config
global mails_number,force_refresh,step,message,receivers
global error,opacity, new_trans
global string,search,March_ID,attachment
cache_path='cache'
folder_path="收件夹"
send_path=''
username=''
password=''
popport='110'
smtpport='25'
popssl=False
smtpssl=False
contact_path='contact.csv'
force_refresh = False
emails=[]
March_ID=emails
string=''
search=False
new_trans = False               #当有新的需要显示时，可以抢占中断
opacity=100             #100时不透明，0时透明