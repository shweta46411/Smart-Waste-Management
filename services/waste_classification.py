import openai
import requests
import io
import base64
import os
from PIL import Image
from config.settings import OPENAI_API_KEY, IWASTE_API_URL
from google.cloud import vision
import json
import streamlit as st
import base64
from dotenv import load_dotenv

# ✅ Set OpenAI API Key
openai.api_key = OPENAI_API_KEY

# ✅ Set Google Cloud Credentials
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath("gcloud_key.json")


RUNNING_IN_STREAMLIT = "STREAMLIT_SERVER_RUN_ONCE" in os.environ

if RUNNING_IN_STREAMLIT:
    if "GOOGLE_CLOUD_KEY" in st.secrets["google_cloud"]:
        google_cloud_json_str = st.secrets["google_cloud"]["GOOGLE_CLOUD_KEY"]
        google_cloud_json = json.loads(base64.b64decode(google_cloud_json_str))

        # ✅ Write to a temporary JSON file
        with open("gcloud_key.json", "w") as f:
            json.dump(google_cloud_json, f)

        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud_key.json"
        print("✅ Google Cloud credentials loaded from Streamlit Secrets (Cloud Mode)")

    else:
        raise FileNotFoundError("❌ Google Cloud credentials not found in Streamlit Secrets!")

else:
    # ✅ Load from .env for local development
    load_dotenv()
    GOOGLE_CLOUD_CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if GOOGLE_CLOUD_CREDENTIALS_PATH and os.path.exists(GOOGLE_CLOUD_CREDENTIALS_PATH):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_CLOUD_CREDENTIALS_PATH
        print(f"✅ Running Locally - Using: {GOOGLE_CLOUD_CREDENTIALS_PATH}")
    else:
        raise FileNotFoundError("❌ Google Cloud credentials not found! Check .env file.")


# ✅ Fetch Waste Categories from I-WASTE API
def get_waste_categories():
    try:
        response = requests.get(f"{IWASTE_API_URL}/categories")
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        return []

WASTE_CATEGORIES = get_waste_categories()

# ✅ Define Recology Bin Mapping
BIN_MAPPING = {
    "Recyclable": {"bin": "♻️ Blue Bin (Recycling)", "image": "assets/recology.bluebin.svg"},
    "Compostable": {"bin": "🌱 Green Bin (Compost)", "image": "assets/recology.greenbin.svg"},
    "Landfill": {"bin": "🗑 Black Bin (General Waste)", "image": "assets/recology.blackbin.svg"},
    "Hazardous": {"bin": "⚠️ Hazardous Waste Bin", "image": "assets/recology.hazardousbin.svg"}
}

# def classify_waste(waste_item):
#     """Uses OpenAI API to classify waste and suggest the correct bin."""
#     try:
#         prompt = f"""
#         You are an expert in waste classification and disposal based on Recology guidelines.
#         Classify the following waste item into one of these categories:
        
#         **Recyclable** (Blue Bin): Paper (non-waxed), cardboard, glass bottles & jars, metal cans, plastic bottles & tubs.
#         **Compostable** (Green Bin): Food scraps, soiled paper (pizza boxes, napkins), plants, tree trimmings.
#         **Landfill** (Black Bin): Non-recyclable plastics, diaper, pet waste, ceramics, foam, plastic bags,pads,menstrual.
#         **Hazardous** (Special Disposal): Batteries, electronics, chemicals, fluorescent bulbs, treated wood.
        
#         Consider the following rules:
#         - If the item is food-related and biodegradable, classify it as **Compostable**.
#         - If the item consists of clean, recyclable material (paper, glass, plastic, metal), classify it as **Recyclable**.
#         - If the item is a mix of materials, contaminated, or non-recyclable plastic, classify it as **Landfill**.
#         - If the item is toxic, electronic, or contains hazardous chemicals, classify it as **Hazardous**.
        
#         Waste Item: {waste_item}
#         """

#         client = openai.OpenAI()
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": prompt}]
#         )

#         classification_result = response.choices[0].message.content.strip()

#         # Ensure correct classification
#         for category in BIN_MAPPING.keys():
#             if category.lower() in classification_result.lower():
#                 classification_result = category
#                 break
#         else:
#             classification_result = "Landfill"

#         bin_info = BIN_MAPPING[classification_result]
#         explanation = get_waste_explanation(waste_item, classification_result)

#         return {
#             "category": classification_result,
#             "bin": bin_info["bin"],
#             "image": bin_info["image"],
#             "explanation": explanation
#         }

#     except Exception as e:
#         return {"error": f"OpenAI API Error: {str(e)}"}

def analyze_image(image_file):
    """Classifies an image into a waste category and suggests the correct bin."""
    try:
        client = vision.ImageAnnotatorClient()
        
        if isinstance(image_file, io.BytesIO):  
            content = image_file.getvalue()
        elif isinstance(image_file, str):  
            with open(image_file, "rb") as img:
                content = img.read()
        else:
            return {"error": "Invalid image input"}

        image = vision.Image(content=content)
        response = client.label_detection(image=image)
        labels = response.label_annotations

        detected_labels = [label.description.lower() for label in labels]
        classification_result = classify_waste(", ".join(detected_labels))

        return {
            "category": classification_result["category"],
            "bin": classification_result["bin"],
            "image": classification_result["image"],
            "labels": detected_labels,
            "explanation": classification_result["explanation"]
        }

    except Exception as e:
        return {"error": f"Google Vision API Error: {str(e)}"}

def classify_waste(waste_item):
    """Uses OpenAI API to classify waste and suggest the correct bin."""
    try:
        # ✅ Force strict classification
        prompt = f"""
        You are an expert in waste classification and disposal based on Recology guidelines.
        You MUST classify the following waste item into ONE of these categories:
        
        1️⃣ **Recyclable** (Blue Bin): Paper (non-waxed), cardboard, glass bottles & jars, metal cans, plastic bottles & tubs.
        2️⃣ **Compostable** (Green Bin): Food scraps, soiled paper (pizza boxes, napkins), plants, tree trimmings.
        3️⃣ **Landfill** (Black Bin): Non-recyclable plastics, diapers, pet waste, ceramics, foam, plastic bags, pads, menstrual items.
        4️⃣ **Hazardous** (Special Disposal): Batteries, electronics, chemicals, fluorescent bulbs, treated wood.

        📌 **IMPORTANT RULES:**
        - If the item is **food-related and biodegradable**, classify it as **Compostable**.
        - If the item consists of **clean, recyclable material** (paper, glass, plastic, metal), classify it as **Recyclable**.
        - If the item is **a mix of materials, contaminated, or non-recyclable plastic**, classify it as **Landfill**.
        - If the item is **toxic, electronic, or contains hazardous chemicals**, classify it as **Hazardous**.

        ⚠️ **Do NOT make up categories. Only use: Recyclable, Compostable, Landfill, or Hazardous.** 

        Waste Item: **{waste_item}**

        Respond ONLY with the category name (one of: Recyclable, Compostable, Landfill, Hazardous).
        """

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        classification_result = response.choices[0].message.content.strip()

        # ✅ Force classification into one of our predefined categories
        category = "Landfill"  # Default fallback
        for key in BIN_MAPPING.keys():
            if key.lower() in classification_result.lower():
                category = key
                break

        # ✅ Hardcoded Corrections for Common Items (Prevents OpenAI Errors)
        landfill_items = ["diaper", "pads", "menstrual", "sanitary", "napkin", "ceramic", "foam", "plastic bags"]
        compostable_items = ["food scraps", "banana peel", "vegetable", "fruit", "plant"]
        hazardous_items = ["battery", "electronics", "fluorescent", "chemical", "treated wood"]

        lower_waste_item = waste_item.lower()

        if any(item in lower_waste_item for item in landfill_items):
            category = "Landfill"
        elif any(item in lower_waste_item for item in compostable_items):
            category = "Compostable"
        elif any(item in lower_waste_item for item in hazardous_items):
            category = "Hazardous"

        # ✅ Get Bin Information
        bin_info = BIN_MAPPING[category]
        explanation = get_waste_explanation(waste_item, category)

        return {
            "category": category,
            "bin": bin_info["bin"],
            "image": bin_info["image"],
            "explanation": explanation
        }

    except Exception as e:
        return {"error": f"OpenAI API Error: {str(e)}"}

def get_waste_explanation(waste_item, category):
    """Uses OpenAI API to generate an explanation of the waste material."""
    prompt = f"""
    You are an expert in waste management and sustainability.
    
    ### Waste Item:
    {waste_item}
    
    ### Task:
    - Explain what this waste material is.
    - Describe whether it's recyclable, compostable, landfill, or hazardous.
    - Suggest proper disposal methods.
    - Explain why it belongs to the {category} category.
    - Motivate the user by explaining how proper disposal helps sustainability.
    
    Keep the explanation clear and informative.
    """
    
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        
        explanation = response.choices[0].message.content.strip()
        
        if not explanation:
            return "⚠️ No explanation available. Please try again."
        
        return explanation
    
    except Exception as e:
        return f"⚠️ Error generating explanation: {str(e)}"
