import cv2


def save_image(image, folder, now):
    """
    Save an image using OpenCV and then resaves it using
    PIL for better compression
    """
    filename = '%s/%s.jpg'
    filepath = filename % (folder, now)
    cv2.imwrite(filepath, image, [cv2.cv.CV_IMWRITE_JPEG_QUALITY, 80])

    # Resave it with pillow to do a better compression
    # img = Image.open(filepath)
    # img.save(filepath, optimize=True, quality=80)
