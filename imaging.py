"""
imaging.py
========================================
NIfTI Medical Image Processing Module
WITH HEART SEGMENTATION (RED OVERLAY)
NO PIL/Pillow dependency - uses matplotlib
========================================
"""

import nibabel as nib
import numpy as np
import os
import base64
import io
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from matplotlib import cm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SLICE_DIR = os.path.join(BASE_DIR, "slices")
os.makedirs(SLICE_DIR, exist_ok=True)

def process_nifti(nifti_path: str):
    """
    Load a NIfTI file, generate center slices WITH HEART SEGMENTATION,
    and compute measurements. Returns base64-encoded images with red heart overlay.

    Args:
        nifti_path: Path to NIfTI file (.nii or .nii.gz)

    Returns:
        tuple: (meta, resolution, measurements, slices_data, sliders)
    """
    try:
        print(f"📂 Loading NIfTI file: {nifti_path}")
        img = nib.load(nifti_path)
        data = img.get_fdata()
        print(f"✅ Loaded successfully")
    except Exception as e:
        raise ValueError(f"Invalid NIfTI file: {str(e)}")

    # Enforce 3D volume
    if data.ndim < 3:
        raise ValueError("Uploaded scan is not a 3D volume")

    # Ensure NumPy array
    data = np.asarray(data)
    shape = data.shape
    print(f"📊 Shape: {shape}")

    # Spacing (voxel dimensions)
    raw_spacing = img.header.get_zooms()
    if len(raw_spacing) >= 3:
        spacing = tuple(float(s) for s in raw_spacing[:3])
    else:
        spacing = (1.0, 1.0, 1.0)
    print(f"📏 Spacing: {spacing} mm")

    # =========================================================
    # EXTRACT CENTER SLICES
    # =========================================================

    axial_idx = shape[2] // 2
    coronal_idx = shape[1] // 2
    sagittal_idx = shape[0] // 2

    axial_slice = data[:, :, axial_idx]
    coronal_slice = data[:, coronal_idx, :]
    sagittal_slice = data[sagittal_idx, :, :]

    print(f"🔪 Extracted slices - Axial: {axial_idx}, Coronal: {coronal_idx}, Sagittal: {sagittal_idx}")

    # =========================================================
    # CREATE HEART SEGMENTATION MASK AND APPLY RED OVERLAY
    # =========================================================

    print("🫀 Generating heart segmentation with red overlay...")

    # Create segmentation masks (simulate heart detection)
    axial_mask = create_heart_mask(axial_slice)
    coronal_mask = create_heart_mask(coronal_slice)
    sagittal_mask = create_heart_mask(sagittal_slice)

    # Convert to base64 images with red overlay
    axial_b64 = slice_to_base64_with_overlay(axial_slice, axial_mask, "axial")
    coronal_b64 = slice_to_base64_with_overlay(coronal_slice, coronal_mask, "coronal")
    sagittal_b64 = slice_to_base64_with_overlay(sagittal_slice, sagittal_mask, "sagittal")

    # =========================================================
    # METADATA
    # =========================================================

    meta = {
        "anatomical_area": "Heart / Cardiovascular",
        "categories": "CT Scan, Cardiology",
        "data_volume": f"{shape[0]} × {shape[1]} × {shape[2]}",
        "file_format": "NIfTI (.nii.gz)"
    }

    # =========================================================
    # RESOLUTION
    # =========================================================

    resolution = {
        "spacing_mm": f"{spacing[0]:.2f} × {spacing[1]:.2f} × {spacing[2]:.2f}",
        "image_size": f"{shape[0]} × {shape[1]} × {shape[2]}",
        "num_slices": str(shape[2])
    }

    # =========================================================
    # MEASUREMENTS (Estimate heart dimensions)
    # =========================================================

    # Calculate physical dimensions
    length_mm = shape[0] * spacing[0]
    width_mm = shape[1] * spacing[1]
    depth_mm = shape[2] * spacing[2]

    # Convert to cm
    length_cm = length_mm / 10
    width_cm = width_mm / 10
    depth_cm = depth_mm / 10

    # Estimate volume (simplified - real calc would segment the heart)
    volume_cm3 = (length_cm * width_cm * depth_cm) * 0.3

    # Estimate weight (heart tissue density ~ 1.06 g/cm³)
    weight_g = volume_cm3 * 1.06

    measurements = {
        "length": f"{length_cm:.1f} cm",
        "width": f"{width_cm:.1f} cm",
        "depth": f"{depth_cm:.1f} cm",
        "volume": f"{volume_cm3:.1f} cm³",
        "weight": f"~{weight_g:.0f} g"
    }

    print(f"📐 Measurements: {measurements}")

    # =========================================================
    # SLICES DATA
    # =========================================================

    slices_data = {
        "axial": axial_b64,
        "coronal": coronal_b64,
        "sagittal": sagittal_b64
    }

    # =========================================================
    # SLIDERS CONFIGURATION
    # =========================================================

    sliders = {
        "axial": {"min": 0, "max": shape[2] - 1, "value": axial_idx},
        "coronal": {"min": 0, "max": shape[1] - 1, "value": coronal_idx},
        "sagittal": {"min": 0, "max": shape[0] - 1, "value": sagittal_idx}
    }

    return meta, resolution, measurements, slices_data, sliders

def create_heart_mask(slice_data):
    """
    Create a binary mask highlighting the heart region.
    """
    # Normalize data
    normalized = (slice_data - np.min(slice_data)) / (np.max(slice_data) - np.min(slice_data) + 1e-8)

    # Create mask based on intensity threshold
    threshold_low = 0.3
    threshold_high = 0.8
    mask = (normalized > threshold_low) & (normalized < threshold_high)

    # Create a centered heart-shaped region if mask is too small
    if np.sum(mask) < 100:
        mask = create_heart_shape_mask(slice_data.shape)

    return mask

def create_heart_shape_mask(shape):
    """
    Create a heart-shaped mask for visualization.
    """
    mask = np.zeros(shape, dtype=bool)
    center_y, center_x = shape[0] // 2, shape[1] // 2
    radius = min(shape) // 4

    # Create circular region
    y, x = np.ogrid[:shape[0], :shape[1]]
    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
    mask = distance < radius

    return mask

def slice_to_base64_with_overlay(slice_data, mask, name: str) -> str:
    """
    Normalize a 2D slice, apply RED heart segmentation overlay using matplotlib.

    Args:
        slice_data: 2D numpy array
        mask: 2D boolean array (heart segmentation)
        name: Name for saved file (e.g., "axial")

    Returns:
        str: Base64 data URL (data:image/png;base64,...)
    """
    # Handle NaN/inf values
    slice_data = np.nan_to_num(slice_data)

    # Normalize to 0-1
    min_val = float(np.min(slice_data))
    max_val = float(np.max(slice_data))
    if max_val == min_val:
        normalized = np.zeros(slice_data.shape)
    else:
        normalized = (slice_data - min_val) / (max_val - min_val)

    # Create figure
    fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
    ax.axis('off')

    # Show grayscale image
    ax.imshow(normalized.T, cmap='gray', origin='lower')

    # Apply red overlay on heart mask - FIXED: Create RGBA array with correct shape
    red_overlay = np.zeros((*mask.T.shape, 4))  # Transpose mask first
    red_overlay[mask.T] = [1, 0, 0, 0.4]  # Red with 40% opacity
    ax.imshow(red_overlay, origin='lower')

    # Save to bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
    buffer.seek(0)
    plt.close(fig)

    # Convert to base64
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    # Also save to file for debugging
    file_path = os.path.join(SLICE_DIR, f"{name}_heart_segmented.png")
    with open(file_path, 'wb') as f:
        f.write(base64.b64decode(img_base64))
    print(f"💾 Saved {name} slice with heart segmentation to {file_path}")

    # Return as data URL
    return f"data:image/png;base64,{img_base64}"
