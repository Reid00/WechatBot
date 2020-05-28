import time
import re
import itchat
import pandas as pd
import jieba.analyse
import matplotlib.pyplot as plt
from pathlib import Path
from collections import Counter
from wordcloud import WordCloud
from skimage import io
from snownlp import SnowNLP
# from pylab import mpl
plt.rcParams['font.sans-serif'] = ['FangSong'] # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False # 解决保存图像是负号'-'显示为方块的问题

class Wechat:
    #　获取微信好友列表进行分析

    def __init__(self):
        print('login...')
        itchat.auto_login(enableCmdQR=True,hotReload=True)
        self.friends = itchat.get_friends(update=True)
        # print(self.friends)

    def analyse_gender(self):
        #　对朋友性别进行分析
        print('friends gender analyse...')
        sexs = list(map(lambda x: x['Sex'],self.friends[1:]))
        counter = Counter(sexs)  # 1 male, 2 female, 0 unknown
        dic = {1:'Male',2:'Female',0:'Unknown'}
        new_counter = dict()
        for k in counter.keys():
            new_counter[dic[k]] = counter[k]            
        print(r'性别整体数量分布:',new_counter)
        print(r'绘图value 顺序为:',list(counter.values()))
        labels = ['Female','Male','Unknown']
        colors = ['red','yellowgreen','lightskyblue']
        plt.figure(figsize=(8,5),dpi=80)
        plt.axes(aspect=1)
        plt.pie(counter.values(),labels=labels, colors=colors,labeldistance=1.1,autopct='%3.1f%%',shadow=False,startangle=90,pctdistance=0.6)
        """
        plt.pie(counts, #性别统计结果 
        labels=labels, #性别展示标签 
        colors=colors, #饼图区域配色 
        labeldistance = 1.1, #标签距离圆点距离 
        autopct = '%3.1f%%', #饼图区域文本格式 
        shadow = False, #饼图是否显示阴影 
        startangle = 90, #饼图起始角度 
        pctdistance = 0.6 #饼图区域文本距离圆点距离 
        ) 
        """
        plt.legend()
        plt.title(f'{self.friends[0]["NickName"]}的微信好友性别组成')
        plt.show()
        
        
    def analyse_signature(self):
        #　分析好友的个性签名
        signatures=''
        sentiments=[]
        pattern = re.compile('1f(\d.+)')
        for friend in self.friends:
            signature = friend['Signature']
            if signature:
                signature = signature.strip().replace('span','').replace('class','').replace('emoji','')
                signature = re.sub(pattern,'', signature)
                if len(signature)>0:
                     nlp = SnowNLP(signature)
                     sentiments.append(nlp.sentiments)
                    #  signatures += ' '.join(jieba.analyse.extract_tags(signature,5))
                     signatures += ' '.join(nlp.words)
        # print('sentiments',sentiments)
        with open('./data/signatures.txt','w',encoding='utf8') as f:
            f.write(signatures)
        
        # Signature WordCloud
        # back_mask = io.imread('./data/brige.jpg')
        back_mask = io.imread('./data/person.png')
        wordcloud = WordCloud(
            font_path='simfang.ttf',
            background_color='white',
            max_words=1200,
            mask=back_mask,
            max_font_size=75,
            random_state=45,
            width=960,
            height=720,
            margin=15
        )
        wordcloud.generate(signatures)
        plt.imshow(wordcloud)
        plt.axis('off')
        plt.show()
        wordcloud.to_file('./data/signatures.jpg')

        #signatures sentiments judgement
        pos = [sentiment for sentiment in sentiments if sentiment>0.66]
        neu = [sentiment for sentiment in sentiments if sentiment<=0.66 and sentiment >=0.33]
        neg = [sentiment for sentiment in sentiments if sentiment<0.33]
        count_pos = len(pos)
        count_neu= len(neu)
        count_neg = len(neg)

        labels = ['Negtive','Neutral','Positive']  
        values = [count_neg,count_neu,count_pos]
        # plt.rcParams['font.sans-serif'] = ['simHei'] 
        # plt.rcParams['axes.unicode_minus'] = False

        plt.xlabel(r'情感判断')
        plt.ylabel(r'频数')
        plt.xticks(range(3),labels)
        plt.legend(loc='upper right')
        plt.bar(range(3),values,color='rgb')
        plt.title(f'{self.friends[0]["NickName"]}的微信好友签名信息情感分析')
        plt.show()
        

if __name__ == "__main__":
    wechat = Wechat()
    wechat.analyse_gender()