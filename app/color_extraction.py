import cv2
import numpy as np
from sklearn.cluster import KMeans

def preprocess_image(image, size=(400, 400)):
    # Resize the image to reduce computation
    image = cv2.resize(image, size, interpolation=cv2.INTER_AREA)

    # Convert the image from BGR to RGB (OpenCV loads images in BGR)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    return image_rgb

def get_dominant_colors(image, n_colors):
    # Reshape the image to be a list of pixels
    pixels = image.reshape(-1, 3)

    # Perform K-means clustering to find the most dominant colors
    kmeans = KMeans(n_clusters=n_colors, random_state=0).fit(pixels)

    # Get the RGB values of the cluster centers
    dominant_colors = kmeans.cluster_centers_

    return dominant_colors

# Test the color clustering function
# dominant_colors = get_dominant_colors(preprocessed_image, 3)
def format_color_info(dominant_colors):
    # Convert float RGB values to int
    dominant_colors = dominant_colors.astype(int).tolist()  # Convert to list of native Python int values

    # Create a list to hold the color info
    color_info = []

    for i, color in enumerate(dominant_colors):
        # Create a dictionary for each color
        color_dict = {
            "color": f"rgb({color[0]}, {color[1]}, {color[2]})",
        }
        color_info.append(color_dict)

    return color_info

# Test the color info formatting function
# color_info = format_color_info(dominant_colors)
# print(color_info)

