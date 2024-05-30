from bottle import route, run, template, static_file, url, request
from wordcloud import WordCloud, STOPWORDS
from io import BytesIO
import matplotlib.pyplot as plt
import base64
import re
import os
import MeCab
import unicodedata

# 不要な単語のリスト
stopwords = set(STOPWORDS)
stopwords.update(['スタンプ', 
                  '写真', 
                  '動画', 
                  'メッセージ',
                  '取り消し', 
                  '不在',
                  '着信', 
                  'キャンセル', 
                  '応答', 
                  'https',  
                  'グループ',
                  'アルバム',
                  'NULL',
                  'ファイル',
                  '通話',
                  '開始',
                  'emoji'])

# MeCabを使ったトークン化の関数
def mecab_tokenizer(text):
    # テキストの正規化と前処理
    replaced_text = unicodedata.normalize("NFKC", text)
    # replaced_text = replaced_text.upper()
    replaced_text = re.sub(r'[【】 () （） 『』　「」]', '', replaced_text)  #【】 () 「」　『』の除去
    replaced_text = re.sub(r'[\[\［］\]]', ' ', replaced_text)   # ［］の除去
    replaced_text = re.sub(r'[@＠]\w+', '', replaced_text)  # メンションの除去
    replaced_text = re.sub(r'\d+\.*\d*', '', replaced_text) # 数字を除去

    # MeCabの初期化
    mecab = MeCab.Tagger()
    mecab.parse('')  # バグ回避のためのダミー呼び出し

    # トークン化とフィルタリング
    node = mecab.parseToNode(replaced_text)
    token_list = []

    while node: # トークンの終わりまでループ
        if node.surface:
            word_type = node.feature.split(',')[0]
            if word_type in ['名詞', '動詞', '形容詞', '形容動詞', '感動詞']:
                token_list.append(node.surface)
        node = node.next

    # トークンの結合と返却
    return ' '.join(token_list)

# ワードクラウドを生成する関数
def generate_wordcloud(text):

    # 日本語フォントの指定
    font_path = './static/BMbG90.ttf'
    
    # トークン化
    tokenized_text = mecab_tokenizer(text)

    # ワードクラウドの設定
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white', 
        font_path=font_path, 
        stopwords=stopwords, 
        min_word_length=2, 
        # min_font_size=12
        ).generate(tokenized_text)
    
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
            <input type="checkbox" name="overall" value="true"> 全体のワードクラウドを作成
            <input type="submit" value="分析開始">
        </form>
    '''

@route('/', method="GET") #1丁目1番地1号（トップページ）
def html_index():
    return template('test', url = url)

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root='./static')

@route('/analyze', method='POST') #分析結果のページ
def analyze():
    upload = request.files.get('upload')
    overall = request.forms.get('overall')
    if upload is not None:
        file_path = "temp.txt"
        upload.save(file_path)
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            current_speaker = None
            messages = {}
            for line in lines: # 1行ずつ読み込む
                speaker_match = re.search(r'\d{2}:\d{2}\t(.+?)\t', line) # 発言者の抽出
                if speaker_match:
                    current_speaker = speaker_match.group(1)
                    if current_speaker not in messages: # 発言者ごとにメッセージリストを作成
                        messages[current_speaker] = []
                message_content = re.search(r'\d{2}:\d{2}\t.+?\t(.+)', line) # メッセージの抽出
                if message_content and current_speaker:
                    messages[current_speaker].append(message_content.group(1))
        os.remove(file_path)

        if overall:
            # 全体のワードクラウドを生成
            all_messages = ' '.join([' '.join(msgs) for msgs in messages.values()])
            img_data_url = generate_wordcloud(all_messages)
            html_result = f'<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Word Cloud</title></head><body><h2>全体のワードクラウド</h2><img src="{img_data_url}" alt="Word Cloud"></body></html>'
        else:
            # 個人ごとのワードクラウドを生成
            html_result = '<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Word Clouds</title></head><body>'
            for speaker, msgs in messages.items():
                speaker_messages = ' '.join(msgs)
                img_data_url = generate_wordcloud(speaker_messages)
                html_result += f'<h2>{speaker}</h2><img src="{img_data_url}" alt="Word Cloud">'
            html_result += '</body></html>'

        return html_result

    else:
        return "ファイルが見つかりません。"

# サーバーを起動
run(host='localhost', port=8080)