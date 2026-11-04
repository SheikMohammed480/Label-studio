from typing import List, Dict, Optional
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse
from ultralytics import YOLO
import os


class YoloModel(LabelStudioMLBase):
    def setup(self):
        self.set("model_version", "1.0")

        # Update this path to your actual .pt file
        model_path = r"D:\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend\best.pt"

        self.model = YOLO(model_path)

    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        results = []

                # ...existing code...
        for task in tasks:
            image_url = task["data"].get("image")
            print(f"Processing task ID: {task['id']}, image URL: {image_url}")

            # Download image locally from Label Studio


            local_image_path = self.get_local_path(image_url, task["id"])
            print(f"Local image path: {local_image_path}")

            detection = self.model(local_image_path, conf=0.25)[0]
            print(f"Detection: {detection}")

            image_width, image_height = detection.orig_shape[1], detection.orig_shape[0]
        # ...existing code...
            result = []
            for box in detection.boxes:
                cls = int(box.cls[0].item())
                label = self.model.names[cls]

                x1, y1, x2, y2 = box.xyxy[0].tolist()

                result.append({
                    "from_name": "label",
                    "to_name": "image",
                    "type": "rectanglelabels",
                    "value": {
                        "x": (x1 / image_width) * 100,
                        "y": (y1 / image_height) * 100,
                        "width": ((x2 - x1) / image_width) * 100,
                        "height": ((y2 - y1) / image_height) * 100,
                        "rectanglelabels": [label]
                    }
                })

            results.append({
                "result": result,
                "score": 0.85,
                "model_version": self.get("model_version")
            })
        print(f"Predictions: {results}")
        return ModelResponse(predictions=results)
