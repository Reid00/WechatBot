import itchat
import re
from itchat.content import TEXT, CARD, FRIENDS, PICTURE, RECORDING, VIDEO
from itchat.content import ATTACHMENT, SHARING, MAP, NOTE, SYSTEM
import os
import time


rev_tmp_dir = './data/reall_msg/'

if not os.path.exists(rev_tmp_dir):
    os.mkdir(rev_tmp_dir)

class Mybot:
    msg_info= {}

    def __init__(self) -> None:
        itchat.auto_login()

    def run(self):
        itchat.run()

    @staticmethod
    @itchat.msg_register(NOTE, isFriendChat=True)
    def save_recall_msg(msg):
        # 判断私聊的撤回
        if '撤回了一条消息' in msg['Content']:
            old_msg_id = re.search(r'\<msgid\>(.*?)\<\/msgid\>', msg['Content']).group(1)
            old_msg = Mybot.msg_info[old_msg_id]
            print(old_msg_id)
            print(old_msg)

            itchat.send_msg('%s撤回了一条%s消息[%s]，内容为：%s' % (old_msg['msg_from'], old_msg['msg_type'], old_msg['msg_recv_time'], old_msg['msg_content']), toUserName='filehelper')

            # 分享链接还需要发送地址
            if old_msg['msg_type'] == ' Sharing':
                itchat.send_msg('->%s' % old_msg['msg_url'], toUserName='filehelper')

            # 多媒体内容还需要发送文件
            if old_msg['msg_type'] == 'Recording' or old_msg['msg_type'] == 'Attachment':
                itchat.send_file(rev_tmp_dir + old_msg['msg_content'], toUserName='filehelper')   # 发送自动下载的语音或附件

            if old_msg['msg_type'] == 'Picture':
                itchat.send_image(rev_tmp_dir + old_msg['msg_content'], toUserName='filehelper')  # 发送自动下载的照片

            if old_msg['msg_type'] == 'Video':
                itchat.send_video(rev_tmp_dir + old_msg['msg_content'], toUserName='filehelper')  # 发送自动下载的视频

            self.msg_info.pop(old_msg_id)

    # 缓存私聊消息
    @staticmethod
    @itchat.msg_register([TEXT, CARD, FRIENDS, PICTURE, RECORDING, VIDEO, ATTACHMENT, SHARING, MAP, NOTE, SYSTEM], isFriendChat=True)
    def handle_download_friendchat(msg):
        msg_recv_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msg_cret_time = msg['CreateTime']
        msg_from = itchat.search_friends(userName=msg['FromUserName'])['RemarkName']
        msg_to = itchat.search_friends()['NickName']
        msg_id = msg['MsgId']
        msg_content = None
        msg_url = None


        # 接收到文本内容：直接缓存
        if msg['Type'] == 'Text':
            msg_content = msg['Text']
            print(msg_content)

        # 接收到多媒体内容：先获取名字，再自动缓存
        if msg['Type'] == 'Picture' or msg['Type'] == 'Recording' or msg['Type'] == 'Video' or msg['Type'] == 'Attachment':
            msg_content = msg['FileName']   # 获取多媒体文件名字
            # print(type(msg_content))
            msg['Text'](rev_tmp_dir  + str(msg_content))   # 自动缓存多媒体文件
            print(str(msg_content))

        # 接收到名片内容：先缓存昵称，再缓存性别
        if msg['Type'] == 'Card':
            msg_content = msg['RecommendInfo']['NickName']
            if msg['RecommendInfo']['Sex'] == 1:
                msg_content += ' 性别为男'
            else:
                msg_content += ' 性别为女'
            print(msg_content)

        # 接收到好友邀请：直接缓存
        if msg['Type'] == 'Friends':
            msg_content = msg['Text']
            print(msg_content)

        # 接收到分享链接：先缓存标题，再缓存地址
        if msg['Type'] == 'Sharing':
            msg_content = msg['Text']
            msg_url = msg['Url']
            print(msg_content + '->' + msg_url)

        # 接收到地图共享：缓存经纬度和地标
        if msg['Type'] == 'Map':
            x, y, location = re.search('<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*', msg['OriContent']).group(1, 2, 3)
            if location is None:
                msg_content = r'纬度->' + x.__str__() + '经度->' + y.__str__()
            else:
                msg_content = r'' + location
            print(msg_content)

        # 缓存每条私聊消息
        Mybot.msg_info.update(
            {
                msg_id:
                    {
                        'msg_recv_time':msg_recv_time, 'msg_cret_time':msg_cret_time,
                        'msg_from':msg_from, 'msg_to':msg_to,
                        'msg_content':msg_content, 'msg_url':msg_url,
                        'msg_type':msg['Type']
                    }
            }
        )

        # # 删除过期记录
        # for mid in list(msg_info.keys()):
        #     if (msg_info[mid].get('msg_time') < time.time()-120):
        #         # 删除记录，以及对应的文件（略）
        #         del msg_info[mid]
        #     else:
        #         break

    

if __name__ == "__main__":
    bot = Mybot()
    bot.run()