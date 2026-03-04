import os
import asyncio
from starlette.concurrency import run_in_threadpool
from gemini_service import analyze_image_with_gemini
from dotenv import load_dotenv

load_dotenv(override=True)

async def main():
    # Create a dummy image
    dummy_image = b"dummy_image_data_here_that_is_long_enough_hopefully_but_lets_just_pass_it"
    # Actually, we need a real image or Gemini will throw 400 Bad Request.
    # Let's find an image in the current directory if possible.
    image_files = [f for f in os.listdir(".") if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if image_files:
        with open(image_files[0], "rb") as f:
            dummy_image = f.read()
    else:
        print("No image found to test.")
        return

    print("Sending 5 concurrent requests...")
    tasks = [run_in_threadpool(analyze_image_with_gemini, dummy_image) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    success = 0
    for r in results:
        if "モック モク太郎" not in str(r):
            success += 1
            
    print(f"Successes: {success}/5")

asyncio.run(main())
