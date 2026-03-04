import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import time

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheets_service():
    """
    Authenticates and returns the Google Sheets API service object.
    First checks the GOOGLE_CREDENTIALS_JSON environment variable (for Render deployment).
    Falls back to credentials.json in the project root if it exists (for local development).
    """
    import json
    
    # Method 1: Environment Variable (Best for Cloud/Render)
    creds_json_str = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json_str:
        try:
            creds_info = json.loads(creds_json_str)
            creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
            service = build('sheets', 'v4', credentials=creds)
            return service
        except Exception as e:
            raise Exception(f"Failed to load credentials from environment variable: {str(e)}")
            
    # Method 2: Local File (Fallback for local dev)
    creds_path = 'credentials.json'
    if os.path.exists(creds_path):
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        return service
        
    raise Exception("No Google Sheets credentials found. Please set GOOGLE_CREDENTIALS_JSON env var or provide credentials.json")

def write_to_sheets(extracted_data: dict, sheet_name="シート20"):
    """
    Writes the JSON data extracted by Gemini into the Input cells.
    - A3:B8 (枠番, 選手名)
    - A13:D18 (枠番, 1着率, 2着率, 3着率)
    """
    sheet_id = os.getenv("SPREADSHEET_ID")
    if not sheet_id:
        raise Exception("SPREADSHEET_ID is not set in environment variables.")
        
    service = get_sheets_service()
    
    horses = extracted_data.get('horses', [])
    
    # Prepare data for A3:C8 (枠番, 選手名, モーター2連対率) and D3:H8 (平均ST, 1周, 回り足, 直線, 展示)
    values_a3_c8 = []
    values_d3_h8 = []
    for i in range(6):
        if i < len(horses):
            horse = horses[i]
            
            # Format motor rate with % if it exists
            motor_val = horse.get('motor_2ren', "")
            motor_formatted = f"{motor_val}%" if motor_val else ""
            
            values_a3_c8.append([
                str(horse.get('number', "")), 
                str(horse.get('name', "")),
                str(motor_formatted)
            ])
            values_d3_h8.append([
                str(horse.get('avg_st', "")),
                str(horse.get('lap_time', "")),
                str(horse.get('turn', "")),
                str(horse.get('straight', "")),
                str(horse.get('exhibition', ""))
            ])
        else:
            values_a3_c8.append(["", "", ""])
            values_d3_h8.append(["", "", "", "", ""])
            
    # Prepare data for A13:H18 (A=Number, B=win1, C=win2, D=win3, E=kimarite1, F=kimarite2, G=kimarite3, H=kimarite4)
    # The requirement is specifically E=逃げ/逃し, F=差され/差し, G=まくられ/まくり, H=まくられ差/まくり差し
    values_a13_h18 = []
    for i in range(6):
        if i < len(horses):
            horse = horses[i]
            
            # E15:E18 (枠3-6) は未入力にする（ユーザー指定）
            kim1 = str(horse.get('kimarite_1', "")) if i < 2 else ""
            
            values_a13_h18.append([
                str(horse.get('number', "")),
                str(horse.get('win_rate_1', "")),
                str(horse.get('win_rate_2', "")),
                str(horse.get('win_rate_3', "")),
                kim1,
                str(horse.get('kimarite_2', "")),
                str(horse.get('kimarite_3', "")),
                str(horse.get('kimarite_4', ""))
            ])
        else:
            values_a13_h18.append(["", "", "", "", "", "", "", ""])

    data = [
        {
            'range': f"{sheet_name}!A3:C8",
            'values': values_a3_c8
        },
        {
            'range': f"{sheet_name}!D3:H8",
            'values': values_d3_h8
        },
        {
            'range': f"{sheet_name}!A13:H18",
            'values': values_a13_h18
        }
    ]
    
    body = {
        'valueInputOption': 'USER_ENTERED',
        'data': data
    }
    
    # Call the Sheets API
    try:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id, 
            body=body
        ).execute()
        print(f"Data successfully written to {sheet_name} cells A3:B8 and A13:D18.")
        
        # Adding a small delay to ensure Google Sheets has time to recalculate formulas
        time.sleep(2)
        
    except Exception as e:
        raise Exception(f"Failed to write to Google Sheets: {str(e)}")


def read_from_sheets(sheet_name="シート20") -> dict:
    """
    Reads the calculated dashboard results from the Spreadsheet.
    Target range:
    - I3:P8
      I = 補正1周
      J = 補正回り
      K = 補正直線
      L = 補正展示
      M = 機力合算
      N = 平均差
      O = 判定
      P = 買い目
    """
    sheet_id = os.getenv("SPREADSHEET_ID")
    if not sheet_id:
        raise Exception("SPREADSHEET_ID is not set in environment variables.")
        
    service = get_sheets_service()
    
    try:
        # Get the dashboard results range with formatting
        request = service.spreadsheets().get(
            spreadsheetId=sheet_id, 
            ranges=[f'{sheet_name}!I3:P8', f'{sheet_name}!I13:N18'],
            includeGridData=True
        )
        response = request.execute()
        
        sheets = response.get('sheets', [])
        if not sheets:
            return {"dashboard_results": []}
            
        data = sheets[0].get('data', [])
        if not data:
            return {"dashboard_results": []}
            
        row_data = data[0].get('rowData', [])
        row_data_2 = data[1].get('rowData', []) if len(data) > 1 else []
        
        results = []
        for i in range(6):
            row1 = row_data[i] if i < len(row_data) else {}
            row2 = row_data_2[i] if i < len(row_data_2) else {}
            
            # Parse cell values and background colors for I3:P8
            values1 = row1.get('values', [])
            
            def get_val(vals, idx):
                if idx < len(vals):
                    return vals[idx].get('formattedValue', "")
                return ""
                
            def get_bg(vals, idx):
                if idx < len(vals):
                    # Check effectiveFormat for computed background color
                    fmt = vals[idx].get('effectiveFormat', {})
                    bg = fmt.get('backgroundColor', {})
                    if bg:
                        r = int(bg.get('red', 1.0) * 255)
                        g = int(bg.get('green', 1.0) * 255)
                        b = int(bg.get('blue', 1.0) * 255)
                        
                        # If color is completely white, ignore it for dark mode UI
                        if r == 255 and g == 255 and b == 255:
                            return "transparent"
                        
                        return f"rgb({r}, {g}, {b})"
                return "transparent"
                
            # Parse cell values and background colors for I13:N18
            values2 = row2.get('values', [])
            
            results.append({
                "number": i + 1,
                # From I3:P8
                "hosei_lap": get_val(values1, 0),
                "hosei_lap_bg": get_bg(values1, 0),
                "hosei_turn": get_val(values1, 1),
                "hosei_turn_bg": get_bg(values1, 1),
                "hosei_straight": get_val(values1, 2),
                "hosei_straight_bg": get_bg(values1, 2),
                "hosei_exhibition": get_val(values1, 3),
                "hosei_exhibition_bg": get_bg(values1, 3),
                "kiryoku_total": get_val(values1, 4),
                "avg_diff": get_val(values1, 5),
                "judgment": get_val(values1, 6),
                "kaime": get_val(values1, 7),
                
                # From I13:N18
                "pred_win_1": get_val(values2, 0),
                "pred_win_1_bg": get_bg(values2, 0),
                "pred_win_2": get_val(values2, 1),
                "pred_win_2_bg": get_bg(values2, 1),
                "pred_win_3": get_val(values2, 2),
                "pred_win_3_bg": get_bg(values2, 2),
                "pred_rentai_3": get_val(values2, 3),
                "pred_rentai_3_bg": get_bg(values2, 3),
                "total_power": get_val(values2, 4),
                "total_power_bg": get_bg(values2, 4),
                "final_eval": get_val(values2, 5),
                "final_eval_bg": get_bg(values2, 5)
            })
            
        return {
            "dashboard_results": results
        }
        
    except Exception as e:
        raise Exception(f"Failed to read from Google Sheets: {str(e)}")
