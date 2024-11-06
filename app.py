import streamlit as st
import openai
import os
from pathlib import Path
import zipfile
import chardet  # エンコーディング自動検出ライブラリ
from aozora_preprocess import save_cleanse_text  # 前処理の関数をインポート

author_id = '000129'  # 青空文庫の作家番号
author_name = '森鴎外'  # 青空文庫の表記での作家名

# ZIPファイルを解凍してテキストデータを読み込む関数
@st.cache_data
def load_all_texts_from_zip(zip_file):
    all_texts = ""
    unzip_dir = Path("unzipped_files")
    unzip_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)  # 解凍先のディレクトリ

    text_files = list(unzip_dir.glob('**/*.txt'))
    for file_path in text_files:
        # まずバイト形式でファイルを読み込み、エンコーディングを検出
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']  # 検出されたエンコーディングを取得

        try:
            with open(file_path, "r", encoding=encoding) as f:
                all_texts += f.read() + "\n"
        except UnicodeDecodeError:
            st.warning(f"ファイル {file_path} の読み込みに失敗しました。")

    return all_texts

# テキストデータを処理する関数
def process_text_files():
    processed_texts = []  # 処理後のテキストを格納するリスト
    unzip_dir = Path("unzipped_files")
    text_files = list(unzip_dir.glob('**/*.txt'))  # サブフォルダも含む

    for text_file in text_files:
        cleaned_df = save_cleanse_text(text_file, unzip_dir)  # 前処理関数を呼び出し
        if cleaned_df is not None:
            # 整形後のテキストをリストに追加
            processed_texts.append(cleaned_df.to_string(index=False))

    return processed_texts

# すべてのZIPファイルを指定したディレクトリから読み込む
zip_files_directory = Path("000129/files")
zip_files = list(zip_files_directory.glob('*.zip'))  # ZIPファイルを取得

# 全テキストデータを読み込む（すべてのZIPファイルに対して処理を行う）
all_processed_texts = []
for zip_file_path in zip_files:
    load_all_texts_from_zip(zip_file_path)  # ZIPファイルの読み込み
    processed_texts = process_text_files()  # テキストの処理
    all_processed_texts.extend(processed_texts)  # すべての処理されたテキストを追加

# 整形後のテキストを表示
st.text_area("整形後のテキストデータ", "\n\n".join(all_processed_texts), height=300)

# Streamlit Community Cloudの「Secrets」からOpenAI API keyを取得
openai.api_key = st.secrets.OpenAIAPI.openai_api_key

# st.session_stateを使いメッセージのやりとりを保存
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": st.secrets.AppSettings.chatbot_setting} 
    ]

# チャットボットとやりとりする関数
def communicate():
    messages = st.session_state["messages"]
    user_message = {"role": "user", "content": st.session_state["user_input"]}
    messages.append(user_message)

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    bot_message = response["choices"][0]["message"]
    messages.append(bot_message)

    st.session_state["user_input"] = ""  # 入力欄をクリア

# ユーザーインターフェイス
st.title(author_name+"チャットボット")
st.write(author_name+"の作品に基づいたチャットボットです。")

# ユーザーのメッセージ入力
user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

if st.session_state["messages"]:
    messages = st.session_state["messages"]
    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂" if message["role"] == "user" else "🤖"
        st.write(speaker + ": " + message["content"])

# 整形後のテキストを表示
processed_texts = process_text_files()
for i, text in enumerate(processed_texts):
    st.text_area(f"整形後のテキスト {i+1}", text, height=300)
