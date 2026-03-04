import os
from google import genai
from google.genai import types
import json

def analyze_images_with_gemini(image_bytes_list: list) -> dict:
    """
    Analyzes multiple horse racing/boat racing newspaper images simultaneously
    using Gemini Vision API and returns a single structured JSON dictionary
    containing the merged data.
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set in environment variables.")

    # Initialize the new SDK client
    client = genai.Client(api_key=api_key)

    prompt = """
    あなたはプロの競技データアナリストです。
    提供された複数のボートレースの出走表（同一レースで異なる情報タブを開いた複数の画像）から、
    すべての情報を正確に読み取って合体させ、厳密なJSON形式で出力してください。
    データが存在しない項目は 0 または 0.0、"-" として出力してください。
    【最重要ルール】
    横の行（Row）をしっかりと目で追い、画像間でデータを合体させる際は、必ず一番左の「枠番(1〜6)」と「選手名」が一致している行同士を完璧に結合してください。上下の行をまたいで合体させるミスを絶対にしないこと！

    【抽出項目】
    - 出走者情報(リスト):
      - 枠番 (number)
      - レーサー名/選手名 (name)
      - 1着率 (win_rate_1) ※%を除外した数値
      - 2着率 (win_rate_2) ※絶対に「2着率」の列の数値を抽出してください。「2連対率」と間違えないように注意してください。%を除外した数値
      - 3着率 (win_rate_3) ※%を除外した数値
      - 平均ST (avg_st)
      - 決まり手1 (kimarite_1) ※枠1は「逃げ」、枠2-6は「逃し」の列の数値。ハイフン(-)の箇所は必ず 0.0 を入力し、右の列の数値をここにズレて入れないこと！
      - 決まり手2 (kimarite_2) ※枠1は「差され」、枠2-6は「差し」の列の数値。ハイフン(-)の箇所は必ず 0.0 とし、列をズラさないこと。
      - 決まり手3 (kimarite_3) ※枠1は「まくられ」、枠2-6は「まくり」の列の数値。ハイフン(-)の箇所は必ず 0.0 とする。
      - 決まり手4 (kimarite_4) ※枠1は「まくられ差」、枠2-6は「まくり差し」の列の数値。ハイフン(-)の箇所は必ず 0.0 とする。
      - 1周 (lap_time) ※数値
      - 回り足 (turn) ※数値
      - 直線 (straight) ※数値
      - 展示 (exhibition) ※数値
      - モーター2連対率 (motor_2ren) ※モーター情報の「2連対率」の数値。%を除外した数値
    
    【JSONフォーマット例】
    {
      "horses": [
          {"number": 1, "name": "大塚 浩二", "win_rate_1": 22.2, "win_rate_2": 22.2, "win_rate_3": 22.2, "avg_st": 0.18, "kimarite_1": 22.2, "kimarite_2": 11.1, "kimarite_3": 22.2, "kimarite_4": 22.2, "lap_time": 37.63, "turn": 5.83, "straight": 7.91, "exhibition": 6.90, "motor_2ren": 39.3},
          {"number": 2, "name": "高橋 真吾", "win_rate_1": 33.3, "win_rate_2": 8.3, "win_rate_3": 0.0, "avg_st": 0.18, "kimarite_1": 41.7, "kimarite_2": 25.0, "kimarite_3": 0.0, "kimarite_4": 0.0, "lap_time": 38.69, "turn": 5.87, "straight": 8.30, "exhibition": 7.01, "motor_2ren": 36.3}
      ]
    }
    
    注意事項：
    - 最大6行のデータ（枠番1〜6の選手）を抽出してください。
    - 複数の画像から抽出する際、例えば画像Aの「枠1のデータ」と画像Bの「枠1のデータ」をマージします。絶対に「画像Aの枠1」と「画像Bの枠2」を混ぜないこと！
    - 一部の画像に「選手名」や「枠番」が写っていない場合でも、6行のテーブルの物理的な「行の高さ（インデックス）」で他の画像と位置を一致させてマージしてください。
    - JSON以外のテキスト（Markdown記法や「JSON文字列です」などの説明）は一切出力しないでください。純粋なJSON文字列のみを返してください。
    - 数字データ（〇〇率など）は可能な限り「%」を省いた数値型（float）で出力してください。
    """
    
    # Dynamically append text prompt and all images
    contents_list = [prompt]
    for img_bytes in image_bytes_list:
        contents_list.append(
            types.Part.from_bytes(
                data=img_bytes,
                mime_type="image/jpeg"
            )
        )

    # In the new SDK, we need to pass the image correctly
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents_list
    )
    
    # Clean the response text in case Gemini wraps it in markdown blocks
    clean_text = response.text.replace('```json', '').replace('```', '').strip()
    # Suppress printing Japanese to avoid UnicodeEncodeError in ascii terminals
    print("Gemini API call complete.")
    
    parsed_data = json.loads(clean_text)
    return parsed_data
