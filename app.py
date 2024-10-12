import streamlit as st
import openai
import os
from pathlib import Path
import zipfile
from text_preprocessing import save_cleanse_text  # 前処理の関数をインポート

# ZIPファイルを解凍してテキストデータを再帰的に読み込む関数
@st.cache_data
def load_all_texts_from_zip(zip_file):
    all_texts = ""
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall("unzipped_files")  # 解凍先のディレクトリ

    for root, dirs, files in os.walk("unzipped_files"):
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

# テキストデータを処理する関数
def process_text_files():
    processed_texts = []  # 処理後のテキストを格納するリスト
    text_files = list(Path("unzipped_files").glob('**/*.txt'))  # サブフォルダも含む

    # 出力先のディレクトリを作成する
    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)
    if not tx_edit_dir.exists():
        tx_edit_dir.mkdir(parents=True, exist_ok=True)

    for text_file in text_files:
        try:
            save_cleanse_text(text_file)  # 前処理関数を呼び出し
            # 前処理後の結果をリストに追加
            processed_texts.append(f"{text_file.stem}_clns_utf-8.txt")  # 処理後のファイル名をリストに追加
        except Exception as e:
            st.error(f"ファイル {text_file} の処理に失敗しました: {e}")

    return processed_texts

# ZIPファイル名を指定してテキストを読み込む
zip_file_path = "000129.zip"

# 全テキストデータを読み込む
all_mori_ogai_texts = load_all_texts_from_zip(zip_file_path)

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
