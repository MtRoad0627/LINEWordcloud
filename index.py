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
        # 一時ファイルとして保存
        file_path = "temp.txt"
        upload.save(file_path)
        # ファイルを読み込み、メッセージを抽出
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            current_speaker = None
            for line in lines:
                # 発言者を識別
                speaker_match = re.search(r'\d{2}:\d{2}\t(.+?)\t', line)
                if speaker_match:
                    current_speaker = speaker_match.group(1)
                    # 新しい発言者を辞書に追加
                    if current_speaker not in messages:
                        messages[current_speaker] = []
                # メッセージの内容を抽出
                message_content = re.search(r'\d{2}:\d{2}\t.+?\t(.+)', line)
                if message_content and current_speaker:
                    # メッセージを辞書に追加
                    messages[current_speaker].append(message_content.group(1))
        # 一時ファイルを削除
        os.remove(file_path)

        # 全てのメッセージを一つの文字列に結合
        all_messages = ' '.join([msg for msgs in messages.values() for msg in msgs])
        # ワードクラウドを生成
        img_data_url = generate_wordcloud(all_messages)

        # 結果を表示
        return template('<img src="{{img_data_url}}" alt="Word Cloud">', img_data_url=img_data_url)

    else:
        return "ファイルが見つかりません。"
    
# サーバーを起動
run(host='localhost', port=8080)