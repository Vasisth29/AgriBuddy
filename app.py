from flask import Flask, render_template, request, url_for, send_from_directory, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
import json
from utils import get_recommendations, get_production_df, crop_df, CROP_NAMES_HINDI
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import cv2
import tensorflow as tf

app = Flask(__name__)

# Get the base directory (where app.py is located)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'Uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- LOAD MODELS AND INDICES AT STARTUP ---
print("TensorFlow version:", tf.__version__)
print(f"Base directory: {BASE_DIR}")
print("Attempting to load soil model and indices...")
try:
    model_path = os.path.join(BASE_DIR, 'models', 'soil_model.h5')
    indices_path = os.path.join(BASE_DIR, 'models', 'class_indices.json')
    print(f"Loading model from: {model_path}")
    print(f"Model file exists: {os.path.exists(model_path)}")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    if not os.path.exists(indices_path):
        raise FileNotFoundError(f"Indices file not found at: {indices_path}")
    # Try loading with compile=False for TensorFlow 2.20+ compatibility
    try:
        soil_model = load_model(model_path, compile=False)
    except Exception as e1:
        print(f"Warning: Failed to load with compile=False, trying default: {e1}")
        soil_model = load_model(model_path)
    print("Soil model loaded successfully.")
    with open(indices_path, 'r') as f:
        soil_class_indices = json.load(f)
        soil_class_names = {v: k for k, v in soil_class_indices.items()}
    print("Soil class indices loaded successfully.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to load soil model or class indices: {e}")
    import traceback
    traceback.print_exc()
    soil_model, soil_class_names = None, {}

# Global variables for lazy loading disease model
disease_model = None
disease_class_names = None

# Load rainfall data
try:
    df = pd.read_csv(os.path.join(BASE_DIR, "Sub_Division_IMD_2017.csv"))
    df.columns = df.columns.str.strip()
    month_columns = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    df_melted = df.melt(id_vars=["SUBDIVISION", "YEAR"], var_name="MONTH", value_name="RAINFALL")
    df_melted = df_melted[df_melted['MONTH'].isin(month_columns)]
    df_melted = df_melted.dropna(subset=["RAINFALL"])
    historical_mean = df_melted['RAINFALL'].mean()
    sub_historical_mean = df_melted.groupby('SUBDIVISION')['RAINFALL'].mean().to_dict()
    month_num = {'JAN':1, 'FEB':2, 'MAR':3, 'APR':4, 'MAY':5, 'JUN':6, 'JUL':7, 'AUG':8, 'SEP':9, 'OCT':10, 'NOV':11, 'DEC':12}
except Exception as e:
    print(f"Warning: Rainfall data not loaded: {e}")
    df, df_melted, historical_mean = pd.DataFrame(), pd.DataFrame(), 233.30
    sub_historical_mean = {}

# --- Corrected list of States and UTs ---
STATE_NAMES_ENGLISH = [
    'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar',
    'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli and Daman and Diu', 'Delhi', 'Goa',
    'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jammu and Kashmir', 'Jharkhand', 'Karnataka',
    'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya',
    'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal'
]

STATE_NAMES_HINDI = {
    'Andaman and Nicobar Islands': 'अंडमान और निकोबार द्वीप समूह',
    'Andhra Pradesh': 'आंध्र प्रदेश',
    'Arunachal Pradesh': 'अरुणाचल प्रदेश',
    'Assam': 'असम',
    'Bihar': 'बिहार',
    'Chandigarh': 'चंडीगढ़',
    'Chhattisgarh': 'छत्तीसगढ़',
    'Dadra and Nagar Haveli and Daman and Diu': 'दादरा और नगर हवेली और दमन और दीव',
    'Delhi': 'दिल्ली',
    'Goa': 'गोवा',
    'Gujarat': 'गुजरात',
    'Haryana': 'हरियाणा',
    'Himachal Pradesh': 'हिमाचल प्रदेश',
    'Jammu and Kashmir': 'जम्मू और कश्मीर',
    'Jharkhand': 'झारखंड',
    'Karnataka': 'कर्नाटक',
    'Kerala': 'केरल',
    'Ladakh': 'लद्दाख',
    'Lakshadweep': 'लक्षद्वीप',
    'Madhya Pradesh': 'मध्य प्रदेश',
    'Maharashtra': 'महाराष्ट्र',
    'Manipur': 'मणिपुर',
    'Meghalaya': 'मेघालय',
    'Mizoram': 'मिजोरम',
    'Nagaland': 'नागालैंड',
    'Odisha': 'ओडिशा',
    'Puducherry': 'पुडुचेरी',
    'Punjab': 'पंजाब',
    'Rajasthan': 'राजस्थान',
    'Sikkim': 'सिक्किम',
    'Tamil Nadu': 'तमिलनाडु',
    'Telangana': 'तेलंगाना',
    'Tripura': 'त्रिपुरा',
    'Uttar Pradesh': 'उत्तर प्रदेश',
    'Uttarakhand': 'उत्तराखंड',
    'West Bengal': 'पश्चिम बंगाल'
}

production_df = get_production_df()
available_states_in_data = sorted(production_df['State_Name'].str.strip().unique()) if not production_df.empty else []
STATES_FOR_DROPDOWN = [
    {'english': eng, 'hindi': STATE_NAMES_HINDI.get(eng, eng)}
    for eng in STATE_NAMES_ENGLISH if eng in available_states_in_data
]

# Load merged_df
try:
    merged_df = pd.read_csv(os.path.join(BASE_DIR, "merged_crop_data.csv"))
    merged_df.columns = merged_df.columns.str.strip()
    print("Merged data loaded successfully.")
except Exception as e:
    print(f"Warning: Failed to load merged_crop_data.csv: {e}")
    merged_df = pd.DataFrame()

# Get static files list with absolute path and create case-insensitive mapping
static_images_dir = os.path.join(BASE_DIR, 'static', 'crop_images')
static_files = []
crop_image_map = {}  # Maps lowercase crop name to actual filename
if os.path.exists(static_images_dir):
    actual_files = [f for f in os.listdir(static_images_dir) if f.endswith('.jpg')]
    static_files = [f.lower() for f in actual_files]
    # Create mapping: lowercase name -> actual filename
    for actual_file in actual_files:
        crop_image_map[actual_file.lower()] = actual_file
    print(f"Found {len(static_files)} crop images in {static_images_dir}")
else:
    print(f"WARNING: Static images directory not found: {static_images_dir}")

# Subdivision to state mapping
subdivision_to_state = {
    "Andaman & Nicobar Islands": "Andaman and Nicobar Islands",
    "Arunachal Pradesh": "Arunachal Pradesh",
    "Assam & Meghalaya": "Assam",
    "Naga Manipur Mizoram & Tripura": "Manipur",
    "Sub Himalayan West Bengal & Sikkim": "West Bengal",
    "Gangetic West Bengal": "West Bengal",
    "Orissa": "Odisha",
    "Jharkhand": "Jharkhand",
    "Bihar": "Bihar",
    "East Uttar Pradesh": "Uttar Pradesh",
    "West Uttar Pradesh": "Uttar Pradesh",
    "Uttarakhand": "Uttarakhand",
    "Haryana Delhi & Chandigarh": "Haryana",
    "Punjab": "Punjab",
    "Himachal Pradesh": "Himachal Pradesh",
    "Jammu & Kashmir": "Jammu and Kashmir",
    "West Rajasthan": "Rajasthan",
    "East Rajasthan": "Rajasthan",
    "West Madhya Pradesh": "Madhya Pradesh",
    "East Madhya Pradesh": "Madhya Pradesh",
    "Gujarat Region": "Gujarat",
    "Saurashtra & Kutch": "Gujarat",
    "Konkan & Goa": "Goa",
    "Madhya Maharashtra": "Maharashtra",
    "Marathwada": "Maharashtra",
    "Vidharbha": "Maharashtra",
    "Chhattisgarh": "Chhattisgarh",
    "Coastal Andhra Pradesh": "Andhra Pradesh",
    "Telangana": "Telangana",
    "Rayalseema": "Andhra Pradesh",
    "Tamil Nadu & Pondicherry": "Tamil Nadu",
    "Coastal Karnataka": "Karnataka",
    "North Interior Karnataka": "Karnataka",
    "South Interior Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Lakshadweep": "Kerala"
}

# Default crops for seasons
default_crops = {
    'Kharif': ['rice', 'maize', 'cotton'],
    'Rabi': ['wheat', 'chickpea', 'mustard'],
    'Zaid': ['watermelon', 'muskmelon', 'bittergourd'],
    'Unknown': ['potato', 'onion', 'banana']
}

# Load custom problems JSON
try:
    plant_problems_path = os.path.join(BASE_DIR, 'static', 'plant_problems.json')
    plant_problems = json.load(open(plant_problems_path))
except Exception as e:
    print(f"Warning: Failed to load plant_problems.json: {e}")
    plant_problems = {}

def load_disease_model():
    global disease_model, disease_class_names
    if disease_model is None or disease_class_names is None:
        try:
            model_path = os.path.join(BASE_DIR, 'models', 'plant_disease_model.h5')
            json_path = os.path.join(BASE_DIR, 'models', 'disease_class_names.json')
            print(f"Loading disease model from: {model_path}")
            print(f"Disease model file exists: {os.path.exists(model_path)}")
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Disease model file not found at: {model_path}")
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"Disease class names file not found at: {json_path}")
            # Try loading with compile=False for TensorFlow 2.20+ compatibility
            try:
                disease_model = load_model(model_path, compile=False)
            except Exception as e1:
                print(f"Warning: Failed to load with compile=False, trying default: {e1}")
                disease_model = load_model(model_path)
            with open(json_path, 'r') as f:
                disease_class_indices = json.load(f)
                disease_class_names = list(disease_class_indices.keys())
            print("Disease model loaded successfully.")
        except Exception as e:
            print(f"Error loading disease model: {e}")
            import traceback
            traceback.print_exc()
            disease_model, disease_class_names = None, []

def compute_crop_yields(merged_df, state_name, crop_recs):
    if merged_df.empty or 'Crop' not in merged_df.columns or 'Yield' not in merged_df.columns or 'State_Name' not in merged_df.columns:
        for rec in crop_recs:
            rec['national_yield'] = 0.0
            rec['state_yield'] = 0.0
        return

    crop_mapping = {
        'pigeonpeas': 'arhar/tur',
        'chickpea': 'gram',
        'mungbean': 'moong(green gram)',
        'blackgram': 'urad',
        'lentil': 'masoor',
        'mothbeans': 'moth',
        'groundnut': 'groundnut',
        'tobacco': 'tobacco',
        'wheat': 'wheat',
        'safflower': 'safflower',
        'banana': 'banana',
        'sugarcane': 'sugarcane',
        'coconut': 'coconut',
    }

    for rec in crop_recs:
        crop_lower = rec['name'].lower().strip()
        crop_lower_mapped = crop_mapping.get(crop_lower, crop_lower)

        national_mask = merged_df['Crop'].str.lower().str.strip() == crop_lower_mapped
        national_yield = merged_df.loc[national_mask, 'Yield'].mean()
        rec['national_yield'] = round(national_yield, 2) if pd.notna(national_yield) and national_yield > 0 else 0.0

        state_mask = (merged_df['State_Name'].str.strip() == state_name) & (merged_df['Crop'].str.lower().str.strip() == crop_lower_mapped)
        state_yield = merged_df.loc[state_mask, 'Yield'].mean()
        rec['state_yield'] = round(state_yield, 2) if pd.notna(state_yield) and state_yield > 0 else 0.0

def compute_seasonal_success(recommendations):
    season_to_yields = {}
    for rec in recommendations:
        if 'state_yield' in rec and rec['state_yield'] > 0:
            season = rec['details'].get('season', 'Unknown')
            if season not in season_to_yields:
                season_to_yields[season] = []
            season_to_yields[season].append(rec['state_yield'])
    
    seasonal_success = {}
    for season, yields in season_to_yields.items():
        avg_success = sum(yields) / len(yields)
        seasonal_success[season] = round(avg_success, 2)
    
    return [{'season': season, 'success': success} for season, success in seasonal_success.items()]

def compute_regional_popularity(recommendations):
    return [{'crop': rec['name'].title(), 'yield': rec['state_yield']} for rec in recommendations if rec.get('state_yield', 0) > 0]

# Simple readiness probe that does not collide with UI routes
@app.route('/healthz')
def health_check():
    return jsonify({"status": "ok"})

@app.route('/Uploads/<filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"Error serving uploaded file: {e}")
        return "File not found", 404

@app.route('/', defaults={'tab': 'home'}, methods=['GET', 'POST'])
@app.route('/<tab>', methods=['GET', 'POST'])
def index(tab):
    result = None
    recommendations = None
    error_message = None
    selected_state = None
    rainfall_result = None
    rainfall_classification = None
    season = None
    crop_suggestions = None
    rainfall_error = None
    health_result = None
    health_error = None
    health_image_path = None
    irrigation_recommendation = None
    historical_avg = None
    predicted_rainfall = None
    rec_yield_data = []
    seasonal_success_data = []
    regional_popularity_data = []

    if tab == 'recommendation':
        if request.method == 'POST':
            # Get file and state from form
            img_file = request.files.get('image')
            state_name = request.form.get('state')
            selected_state = state_name
            
            # Debug logging for troubleshooting
            print(f"DEBUG Recommendation: POST received")
            print(f"DEBUG: Files in request: {list(request.files.keys())}")
            print(f"DEBUG: img_file exists: {img_file is not None}")
            if img_file:
                print(f"DEBUG: img_file.filename: {img_file.filename}")
                print(f"DEBUG: img_file.content_type: {getattr(img_file, 'content_type', 'N/A')}")
            print(f"DEBUG: state_name: {state_name}")
            
            # Validate file upload
            file_uploaded = False
            if img_file:
                filename = getattr(img_file, 'filename', None)
                if filename and filename.strip():
                    file_uploaded = True
            
            # Validate inputs
            if not file_uploaded or not state_name:
                if not file_uploaded and not state_name:
                    error_message = "Please upload a soil image and select your state."
                elif not file_uploaded:
                    error_message = "Please upload a soil image. Make sure to select a file before clicking submit."
                else:
                    error_message = "Please select your state."
            else:
                # Generate unique filename to avoid conflicts
                import uuid
                file_ext = os.path.splitext(img_file.filename)[1] or '.jpg'
                unique_filename = f"{uuid.uuid4()}{file_ext}"
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    print(f"DEBUG: Saving file to: {img_path}")
                    img_file.save(img_path)
                    print(f"DEBUG: File saved successfully, size: {os.path.getsize(img_path)} bytes")
                    
                    predicted_class = predict_soil(img_path)
                    print(f"DEBUG: Predicted soil type: {predicted_class}")
                    
                    if '___' in predicted_class or 'Unknown' in predicted_class:
                        predicted_class = "Alluvial_Soil"
                    
                    recommendations, error_message = get_recommendations(state_name, predicted_class)
                    print(f"DEBUG: Got {len(recommendations) if recommendations else 0} recommendations")
                    
                    if recommendations:
                        result = {
                            'soil_type': predicted_class.replace('_', ' ').title(),
                            'state': state_name.title()
                        }
                        compute_crop_yields(merged_df, state_name, recommendations)
                        rec_yield_data = [{'crop': rec['name'].title(), 'state': rec['state_yield'], 'national': rec['national_yield']} for rec in recommendations]
                        seasonal_success_data = compute_seasonal_success(recommendations)
                        regional_popularity_data = compute_regional_popularity(recommendations)
                    else:
                        error_message = error_message or "No recommendations found for this soil type and state."
                except Exception as e:
                    error_message = f"Error processing image: {str(e)}"
                    print(f"DEBUG: Exception occurred: {str(e)}")
                    import traceback
                    traceback.print_exc()

    elif tab == 'rainfall':
        if request.method == 'POST':
            subdivision = request.form.get('subdivision')
            year = request.form.get('year')
            month = request.form.get('month')
            if not all([subdivision, year, month]):
                rainfall_error = "Please fill all fields: Subdivision, Year, and Month."
            else:
                try:
                    year_int = int(year)
                except ValueError:
                    rainfall_error = "Invalid year input. Please enter a number."
                else:
                    existing_data = df_melted[(df_melted["SUBDIVISION"] == subdivision) & 
                                             (df_melted["YEAR"] == year_int) & 
                                             (df_melted["MONTH"] == month)]
                    if not existing_data.empty:
                        rainfall = existing_data['RAINFALL'].values[0]
                    else:
                        df_sub = df_melted[df_melted['SUBDIVISION'] == subdivision].copy()
                        df_sub['MONTH_NUM'] = df_sub['MONTH'].map(month_num)
                        df_sub['ds'] = pd.to_datetime(df_sub['YEAR'].astype(str) + '-' + df_sub['MONTH_NUM'].astype(str) + '-01')
                        df_sub = df_sub.sort_values('ds')
                        df_sub = df_sub.groupby('ds')[['RAINFALL']].mean().reset_index()
                        df_sub = df_sub.set_index('ds')
                        y = df_sub['RAINFALL']
                        if len(y) < 12:
                            rainfall = sub_historical_mean.get(subdivision, historical_mean)
                        else:
                            try:
                                model_hw = ExponentialSmoothing(y, seasonal='add', seasonal_periods=12, initialization_method='heuristic')
                                fitted = model_hw.fit()
                                target_ds = pd.to_datetime(f"{year_int}-{month_num[month]}-01")
                                last_date = df_sub.index.max()
                                if target_ds <= last_date:
                                    rainfall = sub_historical_mean.get(subdivision, historical_mean)
                                else:
                                    months_diff = (target_ds.year - last_date.year) * 12 + (target_ds.month - last_date.month)
                                    forecast_vals = fitted.forecast(months_diff)
                                    rainfall = forecast_vals.iloc[-1] if not forecast_vals.empty and not np.isnan(forecast_vals.iloc[-1]) else sub_historical_mean.get(subdivision, historical_mean)
                            except Exception as e:
                                print(f"Warning: Holt-Winters failed for {subdivision}: {e}")
                                rainfall = sub_historical_mean.get(subdivision, historical_mean)
                    predicted_rainfall = float(rainfall)
                    rainfall_result = f"Prediction: {rainfall:.2f} mm"

                    historical_data = df_melted[(df_melted["SUBDIVISION"] == subdivision) & (df_melted["MONTH"] == month)]
                    historical_avg = float(historical_data['RAINFALL'].mean() if not historical_data.empty else sub_historical_mean.get(subdivision, historical_mean))
                    anomaly_status = ""
                    if historical_avg > 0:
                        deviation = ((predicted_rainfall - historical_avg) / historical_avg) * 100
                        if abs(deviation) > 20:
                            anomaly_status = f" (Anomaly: {deviation:.1f}% from historical average of {historical_avg:.2f} mm)"

                    rainfall_classification = "Low" if predicted_rainfall < 33 else "Medium" if predicted_rainfall <= 413 else "High"
                    rainfall_classification += f" rainfall ({predicted_rainfall:.2f} mm){anomaly_status}"

                    month_to_season = {
                        'JUN': 'Kharif', 'JUL': 'Kharif', 'AUG': 'Kharif', 'SEP': 'Kharif',
                        'OCT': 'Rabi', 'NOV': 'Rabi', 'DEC': 'Rabi', 'JAN': 'Rabi', 'FEB': 'Rabi', 'MAR': 'Rabi',
                        'APR': 'Zaid', 'MAY': 'Zaid'
                    }
                    season = month_to_season.get(month, 'Unknown')
                    dummy_soil = "Alluvial Soil"
                    state_name = subdivision_to_state.get(subdivision, subdivision.replace('&', 'and'))
                    all_recommendations, _ = get_recommendations(state_name, dummy_soil)
                    crop_suggestions = [c for c in all_recommendations if c.get('details', {}).get('season', '').lower() == season.lower()][:3]
                    if not crop_suggestions and season != 'Unknown':
                        crop_suggestions = all_recommendations[:3]
                    if not crop_suggestions:
                        defaults = default_crops.get(season, [])
                        for name in defaults:
                            if name in [x.lower() for x in crop_df['label'].tolist()]:
                                details = crop_df[crop_df['label'].str.lower() == name].iloc[0]
                                crop_suggestions.append({
                                    'name': name,
                                    'details': {
                                        'season': season,
                                        'temp': details['temperature'],
                                        'rain': details['rainfall'],
                                        'ph': details['ph'],
                                        'hindi_name': CROP_NAMES_HINDI.get(name, "N/A")
                                    }
                                })

                    irrigation_recommendation = ""
                    if crop_suggestions:
                        ideal_rain = crop_suggestions[0]['details'].get('rain', 0)
                        if predicted_rainfall < ideal_rain * 0.8:
                            irrigation_recommendation = f"Irrigation recommended: Predicted rainfall ({predicted_rainfall:.2f} mm) is below the ideal ({ideal_rain} mm) for {crop_suggestions[0]['name']}."
                        elif predicted_rainfall > ideal_rain * 1.2:
                            irrigation_recommendation = f"Irrigation not needed: Predicted rainfall ({predicted_rainfall:.2f} mm) exceeds the ideal ({ideal_rain} mm) for {crop_suggestions[0]['name']}."
                        else:
                            irrigation_recommendation = f"Irrigation may not be necessary: Predicted rainfall ({predicted_rainfall:.2f} mm) is close to the ideal ({ideal_rain} mm) for {crop_suggestions[0]['name']}."

    elif tab == 'health':
        if request.method == 'POST' and 'leaf_image' in request.files:
            leaf_file = request.files.get('leaf_image')
            if not leaf_file or not leaf_file.filename:
                health_error = "Please upload a leaf image."
            else:
                leaf_path = os.path.join(app.config['UPLOAD_FOLDER'], leaf_file.filename)
                try:
                    leaf_file.save(leaf_path)
                    health_image_path = url_for('uploaded_file', filename=leaf_file.filename)
                    general_issue = predict_disease(leaf_path)
                    issue_info = plant_problems.get(general_issue, {'description': 'Unknown issue', 'solutions': 'Consult an expert or test soil.'})
                    health_result = {
                        'issue': general_issue,
                        'description': issue_info['description'],
                        'solutions': issue_info['solutions']
                    }
                except Exception as e:
                    health_error = f"Error during analysis: {str(e)}"

    return render_template(
        'index.html',
        tab=tab,
        states=STATES_FOR_DROPDOWN,
        result=result,
        recommendations=recommendations,
        error_message=error_message,
        selected_state=selected_state,
        rainfall_result=rainfall_result,
        rainfall_classification=rainfall_classification,
        season=season,
        crop_suggestions=crop_suggestions,
        rainfall_error=rainfall_error,
        subdivisions=df['SUBDIVISION'].unique().tolist() if not df.empty else [],
        static_files=static_files,
        crop_image_map=crop_image_map,
        health_result=health_result,
        health_error=health_error,
        health_image_path=health_image_path,
        irrigation_recommendation=irrigation_recommendation,
        historical_avg=historical_avg,
        predicted_rainfall=predicted_rainfall,
        merged_df=merged_df,
        rec_yield_data=rec_yield_data,
        seasonal_success_data=seasonal_success_data,
        regional_popularity_data=regional_popularity_data
    )

def predict_soil(img_path):
    if soil_model is None or not soil_class_names:
        return "Soil model not loaded"
    try:
        img = image.load_img(img_path, target_size=(128, 128))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0
        prediction = soil_model.predict(img_array, verbose=0)
        class_idx = np.argmax(prediction[0])
        predicted_class = soil_class_names.get(class_idx, "Unknown Soil")
        return predicted_class
    except Exception as e:
        print(f"Error during soil prediction: {e}")
        return "Could not process image"

def predict_disease(img_path):
    load_disease_model()
    if disease_model is None or not disease_class_names:
        return "Model not loaded"
    try:
        img = cv2.imread(img_path)
        if img is None:
            raise ValueError("Invalid image file")
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 40, 40])
        upper_green = np.array([85, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            if w > 20 and h > 20:
                leaf_img = img[y:y+h, x:x+w]
                leaf_img = cv2.resize(leaf_img, (224, 224))
            else:
                leaf_img = cv2.resize(img, (224, 224))
        else:
            leaf_img = cv2.resize(img, (224, 224))
        leaf_img = cv2.cvtColor(leaf_img, cv2.COLOR_BGR2RGB)
        img_array = image.img_to_array(leaf_img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        prediction = disease_model.predict(img_array, verbose=0)
        class_idx = np.argmax(prediction[0])
        confidence = np.max(prediction[0])
        if confidence >= 0.3 and class_idx < len(disease_class_names):
            predicted_class = disease_class_names[class_idx]
            general_issue = predicted_class.split('___')[-1].replace('_', ' ').strip()
            general_issue = ' '.join(word.capitalize() for word in general_issue.split())
            return general_issue
        hsv = cv2.cvtColor(leaf_img, cv2.COLOR_RGB2HSV)
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        yellow_ratio = cv2.countNonZero(yellow_mask) / (224 * 224)
        purple_lower = np.array([130, 50, 50])
        purple_upper = np.array([160, 255, 255])
        purple_mask = cv2.inRange(hsv, purple_lower, purple_upper)
        purple_ratio = cv2.countNonZero(purple_mask) / (224 * 224)
        brown_lower = np.array([10, 100, 20])
        brown_upper = np.array([20, 255, 200])
        brown_mask = cv2.inRange(hsv, brown_lower, brown_upper)
        brown_ratio = cv2.countNonZero(brown_mask) / (224 * 224)
        green_lower = np.array([35, 50, 50])
        green_upper = np.array([85, 255, 255])
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        green_ratio = cv2.countNonZero(green_mask) / (224 * 224)
        pale_lower = np.array([30, 30, 100])
        pale_upper = np.array([60, 100, 255])
        pale_mask = cv2.inRange(hsv, pale_lower, pale_upper)
        pale_ratio = cv2.countNonZero(pale_mask) / (224 * 224)
        if yellow_ratio > 0.2 and green_ratio > 0.3:
            return "Magnesium Deficiency"
        elif pale_ratio > 0.25:
            return "Iron Deficiency"
        elif yellow_ratio > 0.2:
            return "Nitrogen Deficiency"
        elif purple_ratio > 0.15:
            return "Phosphorus Deficiency"
        elif brown_ratio > 0.2:
            return "Potassium Deficiency"
        else:
            return "Unknown Issue"
    except Exception as e:
        print(f"Image processing error: {str(e)}")
        return "Unknown Issue"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    app.run(host='0.0.0.0', port=port, debug=debug)