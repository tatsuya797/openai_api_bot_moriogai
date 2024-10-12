import streamlit as st
import openai
import os
from pathlib import Path
from text_preprocessing import save_cleanse_text  # 前処理の関数をインポート

# 1. author_id を定義（前処理コードと一致させる）
author_id = '000129'

# 2. テキストデータを再帰的に読み込む関数
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

# 3. フォルダ名を指定してテキストを読み込む
txtfile_129_directory = Path("txtfile_129")  # 正しいパスに変更してください

# 4. テキストデータを処理する関数
def process_text_files():
    processed_texts = []  # 処理後のテキストを格納するリスト
    text_files = list(txtfile_129_directory.glob('**/*.txt'))  # サブフォルダも含む
    for text_file in text_files:
        st.write(f"Processing file: {text_file}")
        save_cleanse_text(text_file)  # 前処理関数を呼び出し
        # 前処理後のファイル名を組み立て
        processed_file = Path(f"./out_{author_id}/edit/{text_file.stem}_clns_utf-8.txt")
        st.write(f"Processed file path: {processed_file}")
        processed_texts.append(processed_file)  # フルパスをリストに追加

    return processed_texts

# 5. 全テキストデータを読み込む
all_mori_ogai_texts = load_all_texts_from_directory(txtfile_129_directory)

# 6. 読み込んだテキストを確認
st.text_area("テキストデータ", all_mori_ogai_texts, height=300)

# 7. 現在の作業ディレクトリを表示（デバッグ用）
current_dir = Path.cwd()
st.write(f"Current working directory: {current_dir}")

# 8. Streamlit Community Cloudの「Secrets」からOpenAI API keyを取得
try:
    openai.api_key = st.secrets["OpenAIAPI"]["openai_api_key"]
except KeyError as e:
    st.error(f"シークレットの設定に問題があります: {e}")
    st.stop()

# 9. st.session_stateを使いメッセージのやりとりを保存
if "messages" not in st.session_state:
    try:
        chatbot_setting = st.secrets["AppSettings"]["chatbot_setting"]
    except KeyError as e:
        st.error(f"シークレットの設定に問題があります: {e}")
        st.stop()
    st.session_state["messages"] = [
        {"role": "system", "content": chatbot_setting} 
    ]

# 10. チャットボットとやりとりする関数
def communicate():
    messages = st.session_state["messages"]
    user_message = {"role": "user", "content": st.session_state["user_input"]}
    messages.append(user_message)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
    except Exception as e:
        st.error(f"OpenAI API エラー: {e}")
        return

    bot_message = response["choices"][0]["message"]
    messages.append(bot_message)
    st.session_state["user_input"] = ""  # 入力欄を消去

# 11. ユーザーインターフェイスの構築
st.title("森鴎外AIアシスタント")
st.write("森鴎外の作品に基づくチャットボットです。")

# 12. テキストファイルを処理するボタン
if st.button("テキストファイルを処理する"):
    processed_texts = process_text_files()  # テキストファイルの処理を実行
    st.success("テキストファイルの処理が完了しました。")

    # 13. 処理後のディレクトリの存在を確認
    out_edit_dir = Path(f"./out_{author_id}/edit/")
    if out_edit_dir.exists():
        st.write(f"Processed files are expected in: {out_edit_dir}")
        st.write("Processed files:")
        for path in out_edit_dir.glob('*_clns_utf-8.txt'):
            st.write(path.name)
    else:
        st.warning(f"Processed directory {out_edit_dir} does not exist.")

    # 14. 処理後のテキストを表示
    st.subheader("処理後のテキスト")
    
    for processed_file in processed_texts:
        # 実際の処理結果を表示するためにファイルを読み込む
        try:
            st.write(f"Trying to read: {processed_file}")
            with open(processed_file, "r", encoding="utf-8") as f:
                processed_content = f.read()
                st.text_area(f"{processed_file.name}", processed_content, height=200)
        except FileNotFoundError:
            st.warning(f"ファイル {processed_file.name} が見つかりません。")
        except Exception as e:
            st.warning(f"ファイル {processed_file.name} の読み込み中にエラーが発生しました: {e}")

# 15. ユーザーのメッセージ入力
user_input = st.text_input("メッセージを入力してください。", key="user_input", on_change=communicate)

# 16. チャットメッセージの表示
if st.session_state["messages"]:
    messages = st.session_state["messages"]
    for message in reversed(messages[1:]):  # 直近のメッセージを上に
        speaker = "🙂" if message["role"] == "user" else "🤖"
        st.write(speaker + ": " + message["content"])
