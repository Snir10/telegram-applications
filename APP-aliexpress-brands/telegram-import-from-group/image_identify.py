import cv2


def detect_item(image_path):
    # Load the image
    image = cv2.imread(image_path)

    # Define the paths to the template images
    template_paths = {
        'glasses': 'glasses_template.jpg',
        'shirt': 'shirt_template.jpg',
        'pants': 'pants_template.jpg',
        'shoes': 'shoes_template.jpg'
    }

    # Load the templates
    templates = {item: cv2.imread(path, cv2.IMREAD_GRAYSCALE) for item, path in template_paths.items()}

    # Iterate over each template and try to match it in the image
    for item, template in templates.items():
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        # Define a threshold for a match
        threshold = 0.8

        # If the maximum value exceeds the threshold, consider it a match
        if max_val > threshold:
            return item

    # If no match is found, return None
    return None


# Example usage
image_path = 'test_image.jpg'
matched_item = detect_item(image_path)
if matched_item:
    print(f"The matched item in the image is: {matched_item}")
else:
    print("No match found in the image.")