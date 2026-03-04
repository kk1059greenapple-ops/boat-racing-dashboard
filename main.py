import os
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Initialize dot env
load_dotenv(override=True)

from gemini_service import analyze_images_with_gemini
from sheets_service import write_to_sheets, read_from_sheets

app = FastAPI(title="Racing Vision & Sheets Engine API")

# Setup CORS for development testing if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static directory to serve our frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "API is running. Go to /static/index.html to view the dashboard."}


@app.post("/api/analyze")
async def analyze_racing_data(files: List[UploadFile] = File(...)):
    """
    1. Receive image file(s)
    2. Extract data via Gemini (Vision)
    3. Send data to Google Sheets (Input A3:H8)
    4. Wait/Verify calculation
    5. Read result from Google Sheets (Output I13:L18, S3:T8)
    6. Return result to frontend
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files uploaded.")
            
        image_bytes_list = []
        for file in files:
            content = await file.read()
            image_bytes_list.append(content)
            
        # Pass all images to Gemini at once for multi-modal analysis (massive speed and accuracy boost)
        extracted_data = analyze_images_with_gemini(image_bytes_list)
        
        race_info_merged = extracted_data.get("race_info", {"race_number": "-", "condition": "-"})
        all_gemini_horses = extracted_data.get("horses", [])
                
        # convert dictionary back to a sorted list
        all_gemini_horses = sorted(all_gemini_horses, key=lambda x: int(x.get("number", 99)))
        
        combined_extracted_data = {
            "race_info": race_info_merged,
            "horses": all_gemini_horses
        }
        
        # Step 3: Write combined extracted data to Google Sheets
        write_to_sheets(combined_extracted_data)
        
        # Step 4 & 5: Read the calculated results from Google Sheets
        calculated_results = read_from_sheets()
        
        # format the frontend response mapping the matched gemini horses
        # to the dashboard_results calculated by Sheets
        dash_results = calculated_results.get("dashboard_results", [])
        
        horses = []
        for i in range(6):
            horse_dict = {
                "number": i + 1,
                "name": f"未設定 {i+1}",
                "hosei_lap": "-",
                "hosei_lap_bg": "transparent",
                "hosei_turn": "-",
                "hosei_turn_bg": "transparent",
                "hosei_straight": "-",
                "hosei_straight_bg": "transparent",
                "hosei_exhibition": "-",
                "hosei_exhibition_bg": "transparent",
                "kiryoku_total": "-",
                "avg_diff": "-",
                "judgment": "-",
                "kaime": "-",
                "pred_win_1": "-",
                "pred_win_1_bg": "transparent",
                "pred_win_2": "-",
                "pred_win_2_bg": "transparent",
                "pred_win_3": "-",
                "pred_win_3_bg": "transparent",
                "pred_rentai_3": "-",
                "pred_rentai_3_bg": "transparent",
                "total_power": "-",
                "total_power_bg": "transparent",
                "final_eval": "-",
                "final_eval_bg": "transparent"
            }
            
            # Match the parsed Gemini name
            matching_gemini_horse = next((h for h in all_gemini_horses if int(h.get("number", -1)) == (i + 1)), None)
            if matching_gemini_horse:
                horse_dict["name"] = matching_gemini_horse.get("name", horse_dict["name"])
                
            # Match the dashboard results parsed from Sheets I3:P8
            matching_dash_result = next((r for r in dash_results if int(r.get("number", -1)) == (i + 1)), None)
            if matching_dash_result:
                horse_dict["hosei_lap"] = matching_dash_result.get("hosei_lap", "-")
                horse_dict["hosei_lap_bg"] = matching_dash_result.get("hosei_lap_bg", "transparent")
                
                horse_dict["hosei_turn"] = matching_dash_result.get("hosei_turn", "-")
                horse_dict["hosei_turn_bg"] = matching_dash_result.get("hosei_turn_bg", "transparent")
                
                horse_dict["hosei_straight"] = matching_dash_result.get("hosei_straight", "-")
                horse_dict["hosei_straight_bg"] = matching_dash_result.get("hosei_straight_bg", "transparent")
                
                horse_dict["hosei_exhibition"] = matching_dash_result.get("hosei_exhibition", "-")
                horse_dict["hosei_exhibition_bg"] = matching_dash_result.get("hosei_exhibition_bg", "transparent")
                
                horse_dict["kiryoku_total"] = matching_dash_result.get("kiryoku_total", "-")
                horse_dict["avg_diff"] = matching_dash_result.get("avg_diff", "-")
                horse_dict["judgment"] = matching_dash_result.get("judgment", "-")
                horse_dict["kaime"] = matching_dash_result.get("kaime", "-")
                
                horse_dict["pred_win_1"] = matching_dash_result.get("pred_win_1", "-")
                horse_dict["pred_win_1_bg"] = matching_dash_result.get("pred_win_1_bg", "transparent")
                
                horse_dict["pred_win_2"] = matching_dash_result.get("pred_win_2", "-")
                horse_dict["pred_win_2_bg"] = matching_dash_result.get("pred_win_2_bg", "transparent")
                
                horse_dict["pred_win_3"] = matching_dash_result.get("pred_win_3", "-")
                horse_dict["pred_win_3_bg"] = matching_dash_result.get("pred_win_3_bg", "transparent")
                
                horse_dict["pred_rentai_3"] = matching_dash_result.get("pred_rentai_3", "-")
                horse_dict["pred_rentai_3_bg"] = matching_dash_result.get("pred_rentai_3_bg", "transparent")
                
                horse_dict["total_power"] = matching_dash_result.get("total_power", "-")
                horse_dict["total_power_bg"] = matching_dash_result.get("total_power_bg", "transparent")
                
                horse_dict["final_eval"] = matching_dash_result.get("final_eval", "-")
                horse_dict["final_eval_bg"] = matching_dash_result.get("final_eval_bg", "transparent")
                
            horses.append(horse_dict)
            

        final_response = {
            "status": "success",
            "message": "Data processed successfully via Gemini & Sheets Engine",
            "data": {
                "race_info": race_info_merged,
                "horses": horses
            }
        }
        
        return JSONResponse(content=final_response)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

# To run locally: uvicorn main:app --reload
