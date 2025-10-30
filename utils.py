import pandas as pd
import os

# Global variables for lazy loading
_soil_df = None
_crop_df = None
_production_df = None
_climate_df = None

# English to Standardized name mapping
CROP_MAP = {
    'bajra': 'pearlmillet', 'pearl millet': 'pearlmillet', 'jowar': 'sorghum', 'sorghum': 'sorghum',
    'maize': 'maize', 'wheat': 'wheat', 'barley': 'barley', 'ragi': 'fingermillet', 'gram': 'chickpea',
    'arhar/tur': 'pigeonpeas', 'masoor': 'lentil', 'moong(green gram)': 'mungbean', 'urad': 'blackgram',
    'horse-gram': 'horsegram', 'peas & beans (pulses)': 'peas', 'groundnut': 'groundnut',
    'rapeseed & mustard': 'mustard', 'soyabean': 'soyabean', 'sunflower': 'sunflower', 'sesamum': 'sesame',
    'castor seed': 'castor', 'linseed': 'linseed', 'safflower': 'safflower', 'niger seed': 'nigerseed',
    'cotton(lint)': 'cotton', 'jute': 'jute', 'sugarcane': 'sugarcane', 'tobacco': 'tobacco',
    'potato': 'potato', 'onion': 'onion', 'arecanut': 'arecanut', 'coriander': 'coriander',
    'rice': 'rice', 'coconut': 'coconut', 'banana': 'banana', 'sweet potato': 'sweetpotato',
    'tapioca': 'tapioca', 'dry ginger': 'ginger', 'dry chillies': 'chilli', 'cashewnut': 'cashew',
    'other kharif pulses': 'mungbean', 'khesari': 'lathyrus', 'sannhamp': 'sannhemp', 'mesta': 'mesta',
    'cucumber': 'cucumber', 'watermelon': 'watermelon', 'muskmelon': 'muskmelon',
    'bitter gourd': 'bittergourd', 'bottle gourd': 'bottlegourd', 'pumpkin': 'pumpkin'
}

# Hindi names
CROP_NAMES_HINDI = {
    'arecanut': 'सुपारी', 'barley': 'जौ', 'blackgram': 'उड़द', 'castor': 'अरंडी', 'chickpea': 'चना',
    'coriander': 'धनिया', 'cotton': 'कपास', 'fingermillet': 'रागी', 'groundnut': 'मूंगफली',
    'horsegram': 'कुलथी', 'jute': 'जूट', 'lentil': 'मसूर', 'linseed': 'अलसी', 'maize': 'मक्का',
    'mungbean': 'मूंग', 'mustard': 'सरसों', 'nigerseed': 'रामतिल', 'onion': 'प्याज', 'pearlmillet': 'बाजरा',
    'peas': 'मटर', 'pigeonpeas': 'अरहर/तूर', 'potato': 'आलू', 'safflower': 'कुसुम', 'sesame': 'तिल',
    'sorghum': 'ज्वार', 'soyabean': 'सोयाबीन', 'sugarcane': 'गन्ना', 'sunflower': 'सूरजमुखी',
    'tobacco': 'तम्बाकू', 'wheat': 'गेहूं', 'rice': 'चावल', 'coconut': 'नारियल', 'banana': 'केला',
    'sweetpotato': 'शकरकंद', 'tapioca': 'टैपिओका', 'ginger': 'अदरक', 'chilli': 'मिर्च', 'cashew': 'काजू',
    'lathyrus': 'केसरी', 'mesta': 'मेस्टा', 'sannhemp': 'सनहेम्प', 'cucumber': 'खीरा',
    'watermelon': 'तरबूज', 'muskmelon': 'खरबूजा', 'bittergourd': 'कarela', 'bottlegourd': 'लौकी', 'pumpkin': 'कद्दू'
}

ALLOWED_SEASONS = {'Kharif', 'Rabi', 'Zaid', 'Whole Year'}

# --- LAZY LOAD FUNCTIONS ---
def _load_soil_df():
    global _soil_df
    if _soil_df is None:
        try:
            _soil_df = pd.read_excel('soil_nutrient_data.xlsx', engine='openpyxl')
            _soil_df.columns = _soil_df.columns.str.strip()
            print("Loaded: soil_nutrient_data.xlsx")
        except Exception as e:
            print(f"Failed to load soil_nutrient_data.xlsx: {e}")
            _soil_df = pd.DataFrame()
    return _soil_df

def _load_crop_df():
    global _crop_df
    if _crop_df is None:
        try:
            _crop_df = pd.read_csv('Crop_recommendation.csv')
            _crop_df.columns = _crop_df.columns.str.strip()
            print("Loaded: Crop_recommendation.csv")
        except Exception as e:
            print(f"Failed to load Crop_recommendation.csv: {e}")
            _crop_df = pd.DataFrame()
    return _crop_df

def _load_production_df():
    global _production_df
    if _production_df is None:
        try:
            _production_df = pd.read_csv('crop_production.csv')
            _production_df.columns = _production_df.columns.str.strip()
            print("Loaded: crop_production.csv")
        except Exception as e:
            print(f"Failed to load crop_production.csv: {e}")
            _production_df = pd.DataFrame()
    return _production_df

def _load_climate_df():
    global _climate_df
    if _climate_df is None:
        try:
            _climate_df = pd.read_csv('state_climate.csv')
            _climate_df.columns = _climate_df.columns.str.strip()
            print("Loaded: state_climate.csv")
        except Exception as e:
            print(f"Failed to load state_climate.csv: {e}")
            _climate_df = pd.DataFrame()
    return _climate_df

# --- PUBLIC ACCESSORS ---
def get_soil_ranges(soil_type):
    soil_df = _load_soil_df()
    if soil_df.empty: return None
    soil_type_cleaned = soil_type.replace('_', ' ').strip().lower()
    search_term = soil_type_cleaned.split()[0]
    row = soil_df[soil_df['soil_type'].str.strip().str.lower().str.contains(search_term, na=False)]
    if row.empty: return None
    row_values = row.iloc[0]
    return {
        'N': (row_values['min_N'], row_values['max_N']),
        'P': (row_values['min_P'], row_values['max_P']),
        'K': (row_values['min_K'], row_values['max_K']),
        'ph': (row_values['min_pH'], row_values['max_pH'])
    }

def get_recommendations(state_name, soil_type):
    soil_df = _load_soil_df()
    crop_df = _load_crop_df()
    production_df = _load_production_df()
    climate_df = _load_climate_df()

    if production_df.empty or crop_df.empty or soil_df.empty or climate_df.empty:
        return [], "A required data file is missing."

    soil_props = get_soil_ranges(soil_type)
    if not soil_props:
        return [], f"Could not find nutrient data for soil type '{soil_type}'."

    state_name_cleaned = state_name.strip().lower()
    state_data = production_df[production_df['State_Name'].str.strip().str.lower() == state_name_cleaned]
    if state_data.empty:
        return [], f"Could not find production data for '{state_name}'."

    state_climate = None
    if not climate_df.empty:
        climate_row = climate_df[climate_df['State'].str.strip().str.lower() == state_name_cleaned]
        if not climate_row.empty:
            state_climate = climate_row.iloc[0].to_dict()

    all_season_candidates = []
    available_seasons = state_data['Season'].str.strip().unique()
    season_mapping = {
        'Autumn': 'Kharif', 'Summer': 'Zaid', 'Winter': 'Rabi', 'Whole Year': 'Whole Year',
        'Monsoon': 'Kharif', 'Post-Monsoon': 'Rabi', 'Spring': 'Zaid', 'Hot Weather': 'Zaid',
        'Kharif': 'Kharif', 'Rabi': 'Rabi', 'Zaid': 'Zaid'
    }

    for season in available_seasons:
        season_data = state_data[state_data['Season'].str.strip() == season]
        top_for_season = season_data.groupby('Crop')['Production'].sum().nlargest(10).items()
        for crop, prod in top_for_season:
            standardized_season = season_mapping.get(season.strip(), 'Whole Year')
            all_season_candidates.append({'Crop': crop, 'Season': standardized_season})

    if not all_season_candidates:
        return [], f"No crop production data could be processed for '{state_name}'."

    potential_recommendations = []
    seen_crops = set()

    for candidate in all_season_candidates:
        crop_name = candidate['Crop'].strip().lower()
        season = candidate['Season'].strip().title()
        standard_name = CROP_MAP.get(crop_name)
        if standard_name and standard_name not in seen_crops:
            crop_details_df = crop_df[crop_df['label'].str.lower() == standard_name]
            if not crop_details_df.empty:
                crop_details = crop_details_df.iloc[0]
                score = 0
                if soil_props['N'][0] <= crop_details['N'] <= soil_props['N'][1]: score += 1
                if soil_props['P'][0] <= crop_details['P'] <= soil_props['P'][1]: score += 1
                if soil_props['K'][0] <= crop_details['K'] <= soil_props['K'][1]: score += 1
                if soil_props['ph'][0] <= crop_details['ph'] <= soil_props['ph'][1]: score += 1
                if state_climate:
                    if state_climate['temp_min'] <= crop_details['temperature'] <= state_climate['temp_max']: score += 1
                    if state_climate['humidity_min'] <= crop_details['humidity'] <= state_climate['humidity_max']: score += 1
                    if state_climate['rainfall_min'] <= crop_details['rainfall'] <= state_climate['rainfall_max']: score += 1
                if score >= 2:
                    rec_item = {
                        'name': standard_name,
                        'details': {
                            'season': season,
                            'temp': crop_details['temperature'],
                            'rain': crop_details['rainfall'],
                            'ph': crop_details['ph'],
                            'hindi_name': CROP_NAMES_HINDI.get(standard_name, "N/A")
                        }
                    }
                    potential_recommendations.append(rec_item)
                    seen_crops.add(standard_name)

    if not potential_recommendations:
        top_fallback = state_data.groupby('Crop')['Production'].sum().nlargest(3).index.tolist()
        fallback_recs = []
        for crop in top_fallback:
            std_name = CROP_MAP.get(crop.strip().lower())
            if std_name:
                crop_details_df = crop_df[crop_df['label'].str.lower() == std_name]
                if not crop_details_df.empty:
                    rec_item = {
                        'name': std_name,
                        'details': {
                            'season': 'Based on Production Trends',
                            'temp': crop_details_df.iloc[0]['temperature'],
                            'rain': crop_details_df.iloc[0]['rainfall'],
                            'ph': crop_details_df.iloc[0]['ph'],
                            'hindi_name': CROP_NAMES_HINDI.get(std_name, "N/A")
                        }
                    }
                    fallback_recs.append(rec_item)
        if fallback_recs:
            return fallback_recs, "Limited match. Using top production trends."
        return [], f"No suitable crops for '{soil_type}' in '{state_name}'."

    sorted_recommendations = sorted(potential_recommendations, key=lambda x: x['details'].get('temp', 0), reverse=True)
    return sorted_recommendations[:8], None

# --- EXPOSE GLOBALS FOR app.py ---
def get_production_df():
    return _load_production_df()

# These are now accessible
crop_df = _load_crop_df()  # Exposed globally