from bottle import route, run, template, static_file, url, HTTPResponse
from bottle import get, post, request, response, error
from bottle import hook, route, response
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO
import matplotlib.pyplot as plt
import base64
import re
import os

# 発言者とメッセージを格納する辞書
messages = {}

# 不要な単語のリスト
stopwords = set(STOPWORDS)
stopwords.update(['スタンプ', '写真', '動画', '通話時間', 'unsent a message', '不在着信', '通話をキャンセルしました', '通話に応答がありませんでした', 'https', 'グループ通話が開始されました', 'emoji'])

# ワードクラウドを生成する関数
def generate_wordcloud(text):

    #日本語フォントの指定
    font_path = '/Users/ryoy/Documents/UT/3S/プログラミング応用/Ⅰ/textAnalysisApp/MoBoGa/BMbG90.ttf'

    # ワードクラウドの設定
    wordcloud = WordCloud(width=800, height=400, background_color='white', font_path=font_path, stopwords=stopwords).generate(text)
    # matplotlibを使って画像として出力
    plt.figure(figsize=(14, 6.8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.tight_layout(pad=0)
    # 画像をバイト配列としてメモリに保存
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    img_str = base64.b64encode(img_buffer.read()).decode()
    # 画像をHTMLに埋め込むためのデータURLを生成
    img_data_url = 'data:image/png;base64,' + img_str
    return img_data_url

@route('/')
def upload():
    return '''
        <form action="/analyze" method="post" enctype="multipart/form-data">
            <input type="file" name="upload" accept=".txt">
            <input type="submit" value="分析開始">
        </form>
    '''

@route('/', method="GET") #1丁目1番地1号（トップページ）
def html_index():
    return template('test', url = url)

@route('/static/<filepath:path>') #<filepath:path>を指定することで、/static/以下の全てのURLを受け付ける
def server_static(filepath): 
    return static_file(filepath, root = './static')

@route('/analyze', method='POST')
def analyze():
    upload = request.files.get('upload')
    if upload is not None:
        file_path = "temp.txt"
        upload.save(file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            current_speaker = None
            for line in lines:
                speaker_match = re.search(r'\d{2}:\d{2}\t(.+?)\t', line)
                if speaker_match:
                    current_speaker = speaker_match.group(1)
                    if current_speaker not in messages:
                        messages[current_speaker] = []
                message_content = re.search(r'\d{2}:\d{2}\t.+?\t(.+)', line)
                if message_content and current_speaker:
                    messages[current_speaker].append(message_content.group(1))
        os.remove(file_path)

        # HTMLのヘッダーを生成
        html_result = '<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Word Clouds</title></head><body>'
        
        # 各話者のワードクラウドを生成し、HTMLで表示するためのデータを準備
        for speaker, msgs in messages.items():
            speaker_messages = ' '.join(msgs)
            img_data_url = generate_wordcloud(speaker_messages)
            html_result += f'<h2>{speaker}</h2><img src="{img_data_url}" alt="Word Cloud">'
        
        # HTMLのフッターを追加
        html_result += '</body></html>'

        # 結果を表示
        return html_result

    else:
        return "ファイルが見つかりません。"
    
# サーバーを起動
run(host='localhost', port=8080)