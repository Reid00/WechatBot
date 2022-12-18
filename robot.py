import itchat
import re
from itchat.content import TEXT, CARD, FRIENDS, PICTURE, RECORDING, VIDEO
from itchat.content import ATTACHMENT, SHARING, MAP, NOTE, SYSTEM
import os
import time
import json
from utils import logger


rev_tmp_dir = './data/reall_msg/'

if not os.path.exists(rev_tmp_dir):
    os.mkdir(rev_tmp_dir)

"""total_msg 格式
{
    "account1": {
        "msg_id1": {msg},
        "msg_id2": {msg},
        ...
    },
    "account2": {
        "msg_id1": {msg},
        "msg_id2": {msg},
        ...
    },
    ...
}
"""
# 所有的消息记录
total_msg = {}

# 登录的账号被定义为robotAccount
robotAccount = "@2de1be199043b35fabefd7c46c901c5c3f8b2cd60fecbecb1ffc208ee0919aa3"

# 第三方需要forward 的人员
# 这个account 是会每天变化的，amazing，改为remarkName
# forward_from_list = ["@dbb20fc28f9508243187855131e7bbb26f452257ac688e0a6fbaca690f89593e"]
forward_from_list = ["pawn"]

# robot 收到这个人的消息转发
forward_to_list = ["pawn"]

# nickName，wechatAccountMap
nick_account_map = {}

def flush_account(nick_account_map: dict):
    with open(rev_tmp_dir + "account.json", "w", encoding="utf-8") as f:
        json.dump(nick_account_map, f, ensure_ascii=False)

def load_account():
    path = rev_tmp_dir + "account.json"
    if not os.path.exists(path):
        print(f"no account json, init account")
        return
    with open(rev_tmp_dir + "account.json", "r", encoding="utf-8") as f:
        nick_account_map= json.load(f)

def flush_and_clear_total_msg(total_msg, account):
    if len(total_msg) > 15 or len(total_msg[account]) > 1000:
        log.logger.error(json.dumps(total_msg, ensure_ascii=False))
        total_msg.clear()

# ebable log
FORMAT = '%(asctime)s %(levelname)s: %(message)s'
filename = "{}.{}".format(os.path.basename(__file__).split(".")[0], "log")
# filename = "{}.{}".format("./logs/" + os.path.basename(__file__).split(".")[0], "log")
log = logger.Logger(filename, level='info')

# 缓存私聊消息
# 去掉了SYSTEM
@itchat.msg_register([TEXT, CARD, FRIENDS, PICTURE, RECORDING, VIDEO, ATTACHMENT, SHARING, MAP, NOTE], isFriendChat=True)
def cache_friend_msg(msg):

    from_account = msg['FromUserName']
    # to_account = msg['ToUserName']
    if from_account == robotAccount:
        return
    cached_msg = {}
    cached_msg["msg_recv_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    cached_msg["msg_cret_time"] = msg['CreateTime']

    # NickName 账号昵称， RemarkName 备注名称
    cached_msg["from"] = itchat.search_friends(userName=msg['FromUserName'])['RemarkName']
    cached_msg["to"] = itchat.search_friends(userName=msg['ToUserName'])['RemarkName']
    if not cached_msg["to"]:
        cached_msg["to"] = itchat.search_friends(userName=msg['ToUserName'])['NickName']

    if cached_msg["from"] not in nick_account_map:
        nick_account_map[cached_msg["from"]] = msg['FromUserName']
        flush_account(nick_account_map)

    # 已经存在但是值不相同, 直接替换(BUG: 相同的昵称会被覆盖， TODO fix this bug)
    if nick_account_map.get(cached_msg["from"]) != msg['FromUserName']:
        nick_account_map[cached_msg["from"]] = msg['FromUserName']
        
    nick_account_map["昵称加载中"] = "@dbb20fc28f9508243187855131e7bbb26f452257ac688e0a6fbaca690f89593e"

    id = msg['MsgId']
    cached_msg["id"] = id

    cached_msg["type"] = msg["Type"]
    content = None
    msg_url = None

    # 接收到文本内容：直接缓存
    if msg['Type'] == 'Text':
        content = msg['Text']

    # 接收到多媒体内容：先获取名字，再自动缓存
    if msg["Type"] in ["Picture", "Recording", "Video", "Attachment"]:
        content = msg['FileName']   # 获取多媒体文件名字
        # 'Text': <function get_download_fn.<locals>.download_fn at 0x000002399D60E670>}
        msg['Text'](rev_tmp_dir  + str(content))   # 自动缓存多媒体文件
        cached_msg["path"] = rev_tmp_dir  + str(content)

    # 接收到名片内容：先缓存昵称，再缓存性别
    if msg['Type'] == 'Card':
        content = msg['RecommendInfo']['NickName']
        if msg['RecommendInfo']['Sex'] == 1:
            content += ' 性别为男'
        else:
            content += ' 性别为女'
        # print(f"收到名片, 性别为: {content}")

    # 接收到好友邀请：直接缓存
    if msg['Type'] == 'Friends':
        content = msg['Text']
        # print(content)

    # 接收到分享链接：先缓存标题，再缓存地址
    if msg['Type'] == 'Sharing':
        content = msg['Text']
        cached_msg["msg_url"] = msg['Url']
        # print(content + '->' + msg_url)

    # 接收到地图共享：缓存经纬度和地标
    if msg['Type'] == 'Map':
        x, y, location = re.search('<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*', msg['OriContent']).group(1, 2, 3)
        if location is None:
            content = r'纬度->' + x.__str__() + '经度->' + y.__str__()
        else:
            content = r'' + location
        # print(content)

    cached_msg["content"] = content
    log.logger.info(json.dumps(cached_msg, ensure_ascii=False))
    # updated cached info
    if content is None:
        return

    if from_account not in total_msg:
        total_msg[from_account] = {}
    
    # 清理total_msg
    flush_and_clear_total_msg(total_msg, from_account)
    total_msg[from_account][id] = cached_msg
    # log.logger.error(json.dumps(total_msg, ensure_ascii=False))
# ------------------------------------------------------------------------------
# 对收到的消息进行判断处理
# -----------------------------------------------------------------------------
    # 转发消息
    if cached_msg["from"] in forward_from_list:
        account = nick_account_map.get(cached_msg["from"], "")
        if not account:
            log.logger.warn(f"""doesn't get {cached_msg["from"]} account""")
            return
        latest = total_msg[account][id]
        itchat.send_msg(f"""{latest['from']}在【{latest['msg_recv_time']}】
        因为【工作告警】, 发了一条{latest['type']}消息，内容为：{latest['content']}""",
         toUserName="filehelper") # filehelper

    # 如果robot[当前登录账号] 收到了来自reply 宿主的消息
    # 这条消息有',' 前面是账号名称，后面是内容, 且消息类型为Text
    if cached_msg["from"] in forward_to_list and msg["Type"]=="Text":
        rcv = content.split(",") or content.split("，")
        if len(rcv) < 2:
            return
        rcv_toUser = rcv[0].strip()
        rcv_msg = ",".join(rcv[1:])
        # toUserName 需要是微信id
        itchat.send_msg(rcv_msg, toUserName=nick_account_map[rcv_toUser])


@itchat.msg_register(NOTE, isFriendChat=True)
def save_recall_msg(msg):
    # 判断私聊的撤回
    if '撤回了一条消息' in msg['Content'] or "recalled a message" in msg["Content"]:
        match = re.search(r'\<msgid\>(.*?)\<\/msgid\>', msg['Content'])
        recall_msg_id = None
        if match:
            recall_msg_id = match.group(1)
        else:
            print("didn't match msg id")
            return
        
        match = re.search(r'"(.*?)" recalled a message]', msg['Content'])
        from_user = None
        if match:
            from_user = match.group(1)
        else:
            print("didn't match from user nickname")
        account = nick_account_map[from_user]

        # 从全局total_msg 里面获取recall msg
        old_msg = total_msg[account][recall_msg_id]

        itchat.send_msg('%s撤回了一条%s消息[%s]，内容为：%s' % (old_msg['from'],
         old_msg['type'], old_msg['msg_recv_time'], old_msg['content']), 
         toUserName='filehelper')

        # 分享链接还需要发送地址
        if old_msg['type'] == ' Sharing':
            itchat.send_msg('->%s' % old_msg['msg_url'], toUserName='filehelper')

        # 多媒体内容还需要发送文件
        if old_msg["type"] in ["Recording", "Attachment"]:
            itchat.send_file(rev_tmp_dir + old_msg['content'], toUserName='filehelper')   # 发送自动下载的语音或附件

        if old_msg['type'] == 'Picture':
            itchat.send_image(rev_tmp_dir + old_msg['content'], toUserName='filehelper')  # 发送自动下载的照片

        if old_msg['type'] == 'Video':
            itchat.send_video(rev_tmp_dir + old_msg['content'], toUserName='filehelper')  # 发送自动下载的视频

        # total_msg.pop(recall_msg_id)
        del total_msg[account][recall_msg_id]
    
if __name__ == "__main__":
    load_account()
    itchat.auto_login(True)
    itchat.run()
