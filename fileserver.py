#coding=utf8
from flask import Flask,render_template,request,jsonify,abort,send_from_directory,g,make_response,Response,send_file
import xml.etree.cElementTree as ET
import flask_bootstrap,re,os,hashlib,time,sqlite3,collections
from pathlib import Path
from flask_wtf import FlaskForm
from flask_wtf.file import FileField,file_required
from wtforms import StringField, SubmitField
from datetime import datetime
from wtforms.validators import DataRequired
from urllib.parse import quote,unquote


app=Flask(__name__)
flask_bootstrap.Bootstrap(app)
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY']='igidgeri8345fggjj238wq546'
app.config['UPLOAD_FOLDER']=r'上传目录'
app.config['MAX_CONTENT_LENGTH'] = 6*1024 * 1024 * 1024+1024
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
basedir=os.path.abspath((os.path.dirname(__file__)))
ApachelogDir=r"C:\Apache24\logs"
ALLOWED_EXTENSIONS = ["doc","docx","pdf","zip","rar","txt","png","jpg","xlsx","gif","xls","exe","ppt","pptx","7z","mp4","avi","iso","torrent","flv","ts","mkv"]
Video_File_Path= r"D:\视频\WEB视频"
Film_Type={".mp4":"video/mp4",".ogg":"video/ogg",".webm":"video/webm",".weba":"audio/webm",".mkv":"video/webm",".mpd":"application/dash+xml"}

bak_keyword_list=set()
with open(f'{basedir}\敏感词库.txt',newline='',encoding='utf-8') as e:
    for x in e.readlines():
        bak_keyword_list.add(x.replace('\r\n',''))

def sizedisplay(size):    #按文件kb,mb,gb逻辑返回相应值
    if size<1024:
        return f"{size} Bytes"
    elif size<1024*1024:
        return f"{round(size/1024,1)} KB"
    elif size<1024*1024*1024:
        return f"{round(size/1024/1024,1)} MB"
    else:
        return f"{round(size/1024/1024/1024,1)} GB"

class uploadfile(FlaskForm):
    fileupload = FileField(label='',validators=[file_required(),],render_kw={"style":"width:600px;border:1px solid #96c2f1;background:#eff7ff;float:left;font-size:16px;"})
    submit = SubmitField('上传',render_kw={"style":"clear:both;background-color:#006699;margin-left:10px;color:#cccccc;padding:4px 10px 4px 10px;font-size:16px;"})

def allowed_file(filename):             #新增关键词过滤
    if '.' in filename:
        filename_safe=True
        for x1 in bak_keyword_list:
            if x1 in filename:
                filename_safe=False
                break
        return filename.split('.')[-1].lower() in ALLOWED_EXTENSIONS and filename_safe


def get_uploaddir_info(): #定义一个函数，在需要的路由处调用，返回一个目录下文件信息的字典
    file_info_dict={}
    file_list=[]
    file_path = Path(basedir).joinpath(app.config['UPLOAD_FOLDER'])
    for x in file_path.iterdir():
        if x.is_file():
            file_mtime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x.stat().st_mtime))
            file_list.append([x.name,sizedisplay(x.stat().st_size),file_mtime])
    file_list.sort(key=lambda x:x[2], reverse=True) #按时间进行排序
    file_list=[[x[0],x[1],x[2][:10]] for x in file_list] #截取时间字段，仅保留年月日
    file_info_dict['file_list']=file_list
    file_info_dict['total_file']=len(file_list)
    return file_info_dict

@app.route('/')
def index():
    upload_file_form=uploadfile() #实例化表单以在前端显示
    return render_template('upload.html', form=upload_file_form, file_info_dict=get_uploaddir_info())

@app.route('/api/upload',methods=['POST'],strict_slashes=False)
def api_upload():
    file_save_path= f"{basedir}\{app.config['UPLOAD_FOLDER']}"
    upload_object=request.files['fileupload']
    save_file_name = upload_object.filename
    if upload_object and allowed_file(upload_object.filename) and (save_file_name not in [x[0] for x in get_uploaddir_info().get('file_list')]):
        upload_object.save(os.path.join(file_save_path, save_file_name))
        #print(f"文件 {f.filename} 由{request.remote_addr}于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}进行上传")
        return "<h1>上传文件成功！</h1>"
    else:
        return "<h1>上传失败！可能有同名文件、文件太大、非可上传类型及其它异常情况！</h1>"

@app.route('/api/checkfile/')
def checkfile():
    check_result={}
    file_name=request.args.get('name')
    file_size=request.args.get('size')
    has_samename = file_name in [x[0] for x in get_uploaddir_info().get('file_list')]
    if allowed_file(file_name):
        check_result['filetype']=1
    else:
        check_result['filetype'] = 0
    if has_samename:
        check_result['has_samename']=1
    else:
        check_result['has_samename']=0
    if file_size.isdigit():
        file_size=int(file_size)
    else:
        file_size=0
    if file_size<=app.config['MAX_CONTENT_LENGTH']-1024:
        check_result['filesize']=0
    else:
        check_result['filesize'] = 1
    return jsonify(check_result)

@app.route('/download/<filename>', methods=['GET'])
def download(filename):
    if request.method=="GET":
        file_path=Path(basedir).joinpath(app.config['UPLOAD_FOLDER']).joinpath(filename)
        if file_path.is_file():
            #with open(f'{ApachelogDir}\请求文件记录.txt', mode='a+') as f:
            with open(f'{basedir}\请求文件记录.txt', mode='a+') as f: #临时用，正式用请注释掉并启用上一行
                f.write(
                    f"文件 {filename} 由{request.remote_addr}于{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}进行下载\n")
            return send_file(str(file_path), as_attachment=True)

@app.route('/View_Film',methods=['GET','POST'])
def View_Film():
    if request.method=='GET':
        file_info_dict= {} #创建有序字典，以便前端可拿某种方式排序的数据 collections.OrderedDict()
        file_list_include_Path=[]
        file_path = Path(Video_File_Path)
        for x in file_path.iterdir():
            if x.is_file():
                y = x.suffix.lower()
                if y in Film_Type:
                    file_mtime=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x.stat().st_mtime))
                    #file_list.append({'title':x.stem,'filename':x.name,'filesize':sizedisplay(x.stat().st_size),'filetime':file_mtime,'filetype':Film_Type.get(y)})
                    file_list_include_Path.append([x, file_mtime]) #创建带Path对象列表，以便后面的数据填充
        file_list_include_Path.sort(key=lambda x:x[1], reverse=True) #按时间进行排序
        for z in file_list_include_Path: #展开，检索相应信息，填充数据
            file_info_dict[z[0].name]={'title':z[0].stem,'filesize':sizedisplay(z[0].stat().st_size),'filetime':z[0].stat().st_mtime,'filetype':Film_Type.get(z[0].suffix.lower())}
            vtt=z[0].with_name(f"{z[0].stem}.vtt") #组合替换路径里文件名但扩展名为vtt路径，作为字幕信息判断并填充
            if vtt.is_file(): #判断是否存在
                with vtt.open(encoding='utf-8') as e: #打开一个文件流，内容放到content里，以便按行读取
                    content=e.readlines()
                if len(zz:=content[2].split(':'))==2: #读取对应行，拿到幕语言信息，并填充
                    file_info_dict[z[0].name]['captions']={'Language':zz[1].replace(' ','').replace('\n',''),"vtt_file":vtt.name}

        return  render_template('view_film.html')
    else:
        file_info_dict = {}  # 创建有序字典，以便前端可拿某种方式排序的数据 collections.OrderedDict()
        file_list_include_Path = []
        file_path = Path(Video_File_Path)
        for x in file_path.iterdir():
            if x.is_file():
                y = x.suffix.lower()
                if y in Film_Type:
                    file_mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x.stat().st_mtime))
                    # file_list.append({'title':x.stem,'filename':x.name,'filesize':sizedisplay(x.stat().st_size),'filetime':file_mtime,'filetype':Film_Type.get(y)})
                    file_list_include_Path.append([x, file_mtime])  # 创建带Path对象列表，以便后面的数据填充
        file_list_include_Path.sort(key=lambda x: x[1], reverse=True)  # 按时间进行排序
        for z in file_list_include_Path:  # 展开，检索相应信息，填充数据
            file_info_dict[z[0].name] = {'title': z[0].stem, 'filesize': sizedisplay(z[0].stat().st_size),
                                         'filetime': z[0].stat().st_mtime,
                                         'filetype': Film_Type.get(z[0].suffix.lower())}
            vtt = z[0].with_name(f"{z[0].stem}.vtt")  # 组合替换路径里文件名但扩展名为vtt路径，作为字幕信息判断并填充
            if vtt.is_file():  # 判断是否存在
                with vtt.open(encoding='utf-8') as e:  # 打开一个文件流，内容放到content里，以便按行读取
                    content = e.readlines()
                if len(zz := content[2].split(':')) == 2:  # 读取对应行，拿到幕语言信息，并填充
                    file_info_dict[z[0].name]['captions'] = {'Language': zz[1].replace(' ', '').replace('\n', ''),
                                                             "vtt_file": vtt.name}

        return jsonify(file_info_dict)


@app.route('/View_Film/<path:path_part>',methods=['GET'])
def Film_Play(path_part):
    file_path=Path(Video_File_Path).joinpath(path_part)
    if file_path.is_file():
        return send_file(str(file_path), as_attachment=True)

@app.route('/test')
def test():
    return 'test'

@app.route('/robots.txt')
def robots():
    return r"""# robots.txt
User-agent: *
Disallow: /"""

@app.route('/favicon.ico')
def favicon():
    return send_file(f"{basedir}/favicon.ico",as_attachment=True)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=81,threaded=True)
