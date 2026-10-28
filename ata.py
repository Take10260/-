import streamlit as st
from google import genai

# ページの設定
st.set_page_config(page_title="AI司会者付きグループ会議", layout="wide")

# セッション状態の初期化
if "room_name" not in st.session_state:
    st.session_state.room_name = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# --- サイドバー：設定エリア ---
with st.sidebar:
    st.header("⚙️ 会議の設定")
    api_key_input = st.text_input("Gemini API キーを入力", type="password", value=st.session_state.api_key)
    if api_key_input:
        st.session_state.api_key = api_key_input

    st.divider()
    
    # 部屋の作成・参加
    st.header("🚪 ルーム入室")
    room_input = st.text_input("ルーム名（例: 開発アイデア会議）", value=st.session_state.room_name)
    user_name = st.text_input("あなたの名前", value="ゲスト")
    
    if st.button("部屋に入室する"):
        if room_input and api_key_input:
            st.session_state.room_name = room_input
            st.success(f"「{room_input}」に入室しました！")
        else:
            st.error("APIキーとルーム名を入力してください。")

    st.divider()
    if st.button("🤖 Geminiに会議をまとめてもらう"):
        if not st.session_state.api_key:
            st.warning("APIキーを入力してください。")
        elif not st.session_state.messages:
            st.warning("まだ会議のログがありません。")
        else:
            with st.spinner("Geminiが会議をまとめています..."):
                try:
                    client = genai.Client(api_key=st.session_state.api_key)
                    # これまでの会話ログをまとめるプロンプト
                    chat_history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                    prompt = f"以下のグループ会議のログを読み、これまでの議論の要点、決まったこと、次に議論すべき課題を分かりやすくまとめてください。\n\n{chat_history_text}"
                    
                    response = client.models.generate_content(
                        model='models/gemini-3.8-flash',
                        contents=prompt
                    )
                    st.session_state.messages.append({"role": "AI司会者（まとめ）", "content": response.text})
                    st.rerun()
                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

# --- メイン画面 ---
st.title("🗣️ AI司会者付きグループ会議システム")

if not st.session_state.room_name:
    st.info("👈 左側のサイドバーから「APIキー」を入力し、参加したい「ルーム名」と「あなたの名前」を設定して部屋に入室してください。")
else:
    st.subheader(
    generated_header
    if "generated_header" in locals()
    else f"現在のルーム: 【 {st.session_state.room_name} 】"
)
    
    # チャット履歴の表示
    chat_container = st.container(height=450)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "AI司会者" or msg["role"] == "AI司会者（まとめ）":
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(f"**{msg['role']}**: {msg['content']}")
            else:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(f"**{msg['role']}**: {msg['content']}")

    # メッセージ入力フォーム
    if user_input := st.chat_input("メッセージを入力して発言..."):
        if not st.session_state.api_key:
            st.error("サイドバーからGemini APIキーを入力してください。")
        else:
            # ユーザーの発言を追加
            st.session_state.messages.append({"role": user_name, "content": user_input})
            
            # Gemini（AI司会者）を自動で応答させる
            try:
                client = genai.Client(api_key=st.session_state.api_key)
                
                # 会議の文脈を含めたプロンプトの作成
                system_instruction = (
                    "あなたはグループ会議の優秀なAI司会者です。"
                    "参加者たちの意見を引き出し、議論が脱線したら軌道修正し、"
                    "中立な立場で次に議論すべきポイントを問いかけてください。"
                )
                
                chat_history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
                full_prompt = f"{system_instruction}\n\nこれまでの会議の流れ:\n{chat_history_text}\n\n直前の発言者({user_name})の意見を踏まえて、AI司会者としてグループに返答・進行してください。"

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt
                )
                
                ai_response = response.text
                st.session_state.messages.append({"role": "AI司会者", "content": ai_response})
                st.rerun()
                
            except Exception as e:
                st.error(f"Gemini APIとの通信でエラーが発生しました: {e}")
                