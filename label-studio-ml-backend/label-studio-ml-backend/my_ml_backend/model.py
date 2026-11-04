from typing import List, Dict, Optional
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse
from ultralytics import YOLO
import os

class NewModel(LabelStudioMLBase):
    """Custom ML Backend model
    """
    
    def setup(self):
        """Load the YOLOv8 model"""
        model_path = os.path.join(os.path.dirname(__file__), "segformer-floorplan-final.pt")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"YOLO model file not found at: {model_path}")
       
        self.model = YOLO(model_path)
        self.set("model_version", "yolo-v8-custom")

    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ Write your inference logic here
            :param tasks: [Label Studio tasks in JSON format](https://labelstud.io/guide/task_format.html)
            :param context: [Label Studio context in JSON format](https://labelstud.io/guide/ml_create#Implement-prediction-logic)
            :return model_response
                ModelResponse(predictions=predictions) with
                predictions: [Predictions array in JSON format](https://labelstud.io/guide/export.html#Label-Studio-JSON-format-of-annotated-tasks)
        """
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
        """
        This method is called each time an annotation is created or updated
        You can run your logic here to update the model and persist it to the cache
        It is not recommended to perform long-running operations here, as it will block the main thread
        Instead, consider running a separate process or a thread (like RQ worker) to perform the training
        :param event: event type can be ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: the payload received from the event (check [Webhook event reference](https://labelstud.io/guide/webhook_reference.html))
        """

        # use cache to retrieve the data from the previous fit() runs
        old_data = self.get('my_data')
        old_model_version = self.get('model_version')
        print(f'Old data: {old_data}')
        print(f'Old model version: {old_model_version}')

        # store new data to the cache
        self.set('my_data', 'my_new_data_value')
        self.set('model_version', 'my_new_model_version')
        print(f'New data: {self.get("my_data")}')
        print(f'New model version: {self.get("model_version")}')

        print('fit() completed successfully.')

