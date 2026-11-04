from typing import List, Dict, Optional
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse
from ultralytics import YOLO
import os
 
class NewModel(LabelStudioMLBase):
    def setup(self):
        """Load the YOLOv8 model"""
        # model_path = r"D:\label-studio\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend1\best.pt"
        model_path = r"D:\label-studio\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend1\best 4.pt"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model file not found at: {model_path}")
       
        self.model = YOLO(model_path)
        self.set("model_version", "yolo-v8-custom")
 
    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        predictions = []
 
        for task in tasks:
            image_url = task['data']['image']
            image_path = self.get_local_path(image_url, task_id=task['id'])
 
            results = self.model(image_path)[0]  # Get first result from batch
 
            image_height, image_width = results.orig_shape[:2]
 
            results_list = []
            for box in results.boxes.data.tolist():  # YOLO returns [x1, y1, x2, y2, conf, cls]
                x1, y1, x2, y2, conf, cls = box
                label = self.model.names[int(cls)]
 
                # Convert absolute pixel coords to relative percentages
                results_list.append({
                    "from_name": "label",
                    "to_name": "image",
                    "type": "rectanglelabels",
                    "value": {
                        "x": x1 / image_width * 100,
                        "y": y1 / image_height * 100,
                        "width": (x2 - x1) / image_width * 100,
                        "height": (y2 - y1) / image_height * 100,
                        "rectanglelabels": [label]
                    },
                    "score": float(conf)
                })
 
            predictions.append({
                "result": results_list,
                "score": float(max([b[4] for b in results.boxes.data.tolist()] or [0])),
                "model_version": self.get("model_version")
            })
 
        return ModelResponse(predictions=predictions)
 
    def fit(self, event, data, **kwargs):
        """Optional: Called on annotation updates — can be used to retrain the model"""
        old_data = self.get('my_data')
        old_model_version = self.get('model_version')
        print(f'Old data: {old_data}')
        print(f'Old model version: {old_model_version}')
 
        # Store new data
        self.set('my_data', 'my_new_data_value')
        self.set('model_version', 'my_new_model_version')
 
        print(f'New data: {self.get("my_data")}')
        print(f'New model version: {self.get("model_version")}')
        print('fit() completed successfully.')