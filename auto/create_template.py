import cv2
import numpy as np

# Create a template image with white backpack on dark background
template = np.zeros((32, 32, 3), dtype=np.uint8)

# Draw simplified backpack shape in white
cv2.rectangle(template, (8, 12), (24, 26), (255, 255, 255), -1)  # Main bag
cv2.rectangle(template, (14, 6), (18, 12), (255, 255, 255), -1)  # Top handle
cv2.rectangle(template, (10, 8), (22, 10), (255, 255, 255), -1)  # Handle base

# Save the template
cv2.imwrite('assets/backpack_icon.png', template)
print("Template saved to assets/backpack_icon.png")