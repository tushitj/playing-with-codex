import json
import re
from dataclasses import dataclass

import cv2
import easyocr
import numpy as np

PLATE_REGEX = re.compile(r"[^A-Z0-9]")


@dataclass
class VisionResult:
    plate_text: str | None
    plate_confidence: float | None
    signature: str


class CarVisionService:
    def __init__(self):
        self.reader = easyocr.Reader(["en"], gpu=False)
        self.plate_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_russian_plate_number.xml"
        )

    @staticmethod
    def _normalize_plate(text: str) -> str:
        return PLATE_REGEX.sub("", text.upper())

    @staticmethod
    def _signature_from_image(image: np.ndarray) -> str:
        # Normalized HSV histogram as lightweight car appearance fingerprint.
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [12, 12], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return json.dumps(hist.flatten().tolist())

    def _extract_plate_roi(self, image: np.ndarray) -> np.ndarray | None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        candidates = self.plate_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3)
        if len(candidates) == 0:
            return None

        x, y, w, h = max(candidates, key=lambda box: box[2] * box[3])
        return image[y : y + h, x : x + w]

    def _ocr_plate(self, roi: np.ndarray) -> tuple[str | None, float | None]:
        results = self.reader.readtext(roi)
        if not results:
            return None, None

        text, score = max(((r[1], float(r[2])) for r in results), key=lambda r: r[1])
        plate = self._normalize_plate(text)
        if len(plate) < 4:
            return None, None
        return plate, score

    def analyze(self, image_bytes: bytes) -> VisionResult:
        arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Unable to decode image")

        signature = self._signature_from_image(image)
        roi = self._extract_plate_roi(image)

        if roi is not None:
            plate_text, plate_confidence = self._ocr_plate(roi)
            if plate_text:
                return VisionResult(plate_text=plate_text, plate_confidence=plate_confidence, signature=signature)

        # Fallback OCR on whole frame for difficult camera angles.
        plate_text, plate_confidence = self._ocr_plate(image)
        return VisionResult(plate_text=plate_text, plate_confidence=plate_confidence, signature=signature)
