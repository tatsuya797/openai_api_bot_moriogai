# app.py
import streamlit as st
import openai
import os
from pathlib import Path
import zipfile
from text_preprocessing import save_cleanse_text  # 前処理の関数をインポート

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
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                all_texts += f.read() + "\n"
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="shift_jis") as f:
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
        save_cleanse_text(text_file)  # 前処理関数を呼び出し
        # 前処理後のファイルパスを取得
        processed_file = Path('unzipped_files/out_edit/') / f"{text_file.stem}_clns_utf-8.txt"
        if processed_file.exists():
            processed_texts.append(processed_file)
        else:
            st.warning(f"処理後のファイル {processed_file} が存在しません。")

    return processed_texts

# ZIPファイル名を指定してテキストを読み込む
zip_file_path = "000129.zip"

# 全テキストデータを読み込む（必要に応じて削除）
all_mori_ogai_texts = load_all_texts_from_zip(zip_file_path)
st.text_area("テキストデータ", all_mori_ogai_texts, height=300)

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
    st.session_state["user_input"] = ""  # 入力欄を消去

# ユーザーインターフェイスの構築
st.title("森鴎外AIアシスタント")
st.write("森鴎外の作品に基づくチャットボットです。")

# テキストファイルを処理するボタン
if st.button("テキストファイルを処理する"):
    with st.spinner("テキストファイルを処理中..."):
        processed_files = process_text_files()  # テキストファイルの処理を実行
    st.success("テキストファイルの処理が完了しました。")
    
    # 処理後のテキストを表示
    st.subheader("処理後のテキスト内容")
    for processed_file in processed_files:
        try:
            with open(processed_file, "r", encoding="utf-8") as f:
                content = f.read()
                st.text_area(f"{processed_file.name}", content, height=200)
        except Exception as e:
            st.warning(f"ファイル {processed_file} の読み込みに失敗しました。")

# ユーザーのメッセージ入力
user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

if st.session_state["messages"]:
    messages = st.session_state["messages"]
    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂" if message["role"] == "user" else "🤖"
        st.write(speaker + ": " + message["content"])
