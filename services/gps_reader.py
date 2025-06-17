from PIL import Image
import logging
import piexif

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_exif_location(image_path):
    logger.info(f"Processing image: {image_path}")
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()
        logger.info(f"EXIF data: {exif_data}")

        if not exif_data:
            logger.info("No EXIF data found")
            return None

        gps_info = exif_data.get(34853)  
        logger.info(f"GPSInfo: {gps_info}")

        if not gps_info:
            logger.info("No GPSInfo found")
            return None

        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        gps_latitude = gps_info.get(2)  
        gps_latitude_ref = gps_info.get(1)  
        gps_longitude = gps_info.get(4)  
        gps_longitude_ref = gps_info.get(3)  

        if gps_latitude and gps_longitude and gps_latitude_ref and gps_longitude_ref:
            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = -lat

            lng = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lng = -lng

            logger.info(f"Extracted coordinates: lat={lat}, lng={lng}")
            return {"lat": lat, "lng": lng}
        else:
            logger.info("GPS tags missing")
            return None

    except Exception as e:
        logger.error(f"Error extracting GPS: {e}")
        return None
    
