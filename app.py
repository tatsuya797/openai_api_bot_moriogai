import streamlit as st
import openai
import os
from pathlib import Path
from text_preprocessing import save_cleanse_text  # 前処理の関数をインポート

# テキストデータを再帰的に読み込む関数
@st.cache_data
def load_all_texts_from_directory(directory):
    all_texts = ""
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    # まずはutf-8で試す
                    with open(file_path, "r", encoding="utf-8") as f:
                        all_texts += f.read() + "\n"
                except UnicodeDecodeError:
                    try:
                        # 次にshift_jisで試す
                        with open(file_path, "r", encoding="shift_jis") as f:
                            all_texts += f.read() + "\n"
                    except UnicodeDecodeError:
                        # それでも失敗した場合はスキップ
                        st.warning(f"ファイル {file_path} の読み込みに失敗しました。")

    return all_texts

# フォルダ名を指定してテキストを読み込む
txtfile_129_directory = Path("txtfile_129")

# テキストデータを処理する関数
def process_text_files():
    processed_texts = []  # 処理後のテキストを格納するリスト
    text_files = list(txtfile_129_directory.glob('**/*.txt'))  # サブフォルダも含む
    for text_file in text_files:
        save_cleanse_text(text_file)  # 前処理関数を呼び出し
        # 前処理後の結果をリストに追加（保存場所に応じて変更）
        # ここでは仮にファイル名に基づいて読み込んでいますが、実際には適切な処理が必要です。
        processed_texts.append(f"{text_file.stem}_clns_utf-8.txt")  # 仮の処理

    return processed_texts

# 全テキストデータを読み込む
all_mori_ogai_texts = load_all_texts_from_directory(txtfile_129_directory)

# 読み込んだテキストを確認
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
    processed_texts = process_text_files()  # テキストファイルの処理を実行
    st.success("テキストファイルの処理が完了しました。")

    # 処理後のテキストを表示
    st.subheader("処理後のテキスト")
    for processed_file in processed_texts:
        st.write(processed_file)  # 各処理後のファイル名を表示

# ユーザーのメッセージ入力
user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

if st.session_state["messages"]:
    messages = st.session_state["messages"]
    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂" if message["role"] == "user" else "🤖"
        st.write(speaker + ": " + message["content"])
