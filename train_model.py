import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping  # Added for early stopping
from tensorflow.keras.applications import MobileNetV2  # Added for transfer learning
from tensorflow.keras.layers import GlobalAveragePooling2D  # Added for transfer learning
import os
import json

# --- CONFIGURATION ---
train_dir = 'Dataset/train'
test_dir = 'Dataset/test'
model_save_path = 'models/soil_model.h5'
class_indices_path = 'models/class_indices.json'
img_width, img_height = 128, 128
batch_size = 32
epochs = 20  # Increased max epochs; early stopping will handle termination

# --- DATA AUGMENTATION ---
# Enhanced augmentation to improve generalization and prevent overfitting
train_datagen = ImageDataGenerator(
    rescale=1./255,
    rotation_range=40,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    vertical_flip=True,  # Added vertical flip for more variety
    brightness_range=[0.8, 1.2],  # Simulate lighting changes
    channel_shift_range=0.1,  # Color shifts for robustness
    fill_mode='nearest'
)

# Test data should not be augmented, only rescaled for validation
test_datagen = ImageDataGenerator(rescale=1./255)

# --- DATA GENERATORS ---
train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical'
)

test_generator = test_datagen.flow_from_directory(
    test_dir,
    target_size=(img_width, img_height),
    batch_size=batch_size,
    class_mode='categorical'
)

# --- BUILD A MORE POWERFUL MODEL WITH TRANSFER LEARNING ---
# Use MobileNetV2 as base for better feature extraction and generalization
base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(img_width, img_height, 3))

# Freeze base layers initially
base_model.trainable = False

model = Sequential([
    base_model,
    GlobalAveragePooling2D(),
    Dense(512, activation='relu'),
    BatchNormalization(),
    Dropout(0.5),  # Dropout to prevent overfitting
    Dense(len(train_generator.class_indices), activation='softmax')  # Output layer
])

# Compile with lower learning rate for fine-tuning
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001), 
              loss='categorical_crossentropy', 
              metrics=['accuracy'])
model.summary()

# --- EARLY STOPPING CALLBACK ---
# Stop training if val_loss doesn't improve for 5 epochs
early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# --- TRAIN THE MODEL ---
print("Starting model training...")
history = model.fit(
    train_generator, 
    validation_data=test_generator, 
    epochs=epochs,
    callbacks=[early_stopping]  # Added early stopping
)

# Optional: Fine-tune by unfreezing some layers after initial training
base_model.trainable = True
for layer in base_model.layers[:-20]:  # Unfreeze last 20 layers
    layer.trainable = False

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.00001),  # Even lower LR for fine-tuning
              loss='categorical_crossentropy', 
              metrics=['accuracy'])

# Continue training with fine-tuning
model.fit(
    train_generator, 
    validation_data=test_generator, 
    epochs=epochs,
    callbacks=[early_stopping]
)

# --- SAVE THE FINAL MODEL AND CLASS INDICES ---
os.makedirs('models', exist_ok=True)
model.save(model_save_path)
with open(class_indices_path, 'w') as f:
    json.dump(train_generator.class_indices, f)

print(f"\nModel training complete!")
print(f"Model saved at {model_save_path}")
print(f"Class indices saved at {class_indices_path}")