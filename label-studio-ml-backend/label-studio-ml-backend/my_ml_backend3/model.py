from typing import List, Dict, Optional
import os
import logging
from ultralytics import YOLO
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse

logger = logging.getLogger(__name__)

class NewModel(LabelStudioMLBase):
    """Custom YOLO Segmentation Model for Label Studio
    """
    
    def setup(self):
        """Load the YOLO model for segmentation
        """
        # Define model path
        self.model_path = r"D:\label-studio\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend3\floorplan-seg\weights\best.pt"
        
        if not os.path.exists(self.model_path):
            logger.error(f"YOLO model file not found at: {self.model_path}")
            # Fallback to a relative path if absolute fails
            self.model_path = os.path.join(os.path.dirname(__file__), "floorplan-seg", "weights", "best.pt")
            if not os.path.exists(self.model_path):
                 raise FileNotFoundError(f"YOLO model file not found at: {self.model_path}")

        logger.info(f"Loading YOLO model from {self.model_path}")
        self.model = YOLO(self.model_path)
        self.set("model_version", "yolo-segmentation-v1")

    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ Run YOLO segmentation and return polygons
        """
        predictions = []

        # Get from_name and to_name from label config if possible
        from_name, to_name, label_type = self.get_first_tag_names()
        # Default to standard names if not found
        from_name = from_name or 'label'
        to_name = to_name or 'image'

        for task in tasks:
            image_url = task['data'].get('image') or task['data'].get('img')
            if not image_url:
                logger.warning(f"No image URL found in task {task.get('id')}")
                continue

            image_path = self.get_local_path(image_url, task_id=task.get('id'))
            
            # Run inference
            results_all = self.model(image_path)
            if not results_all:
                predictions.append({"result": [], "model_version": self.get("model_version")})
                continue
                
            results = results_all[0]
            image_height, image_width = results.orig_shape[:2]
            results_list = []

            # Check if we have masks (segmentation)
            if results.masks is not None:
                # Iterate through masks. xy contains a list of arrays (one per mask)
                for mask_xy, conf, cls in zip(results.masks.xy, results.boxes.conf, results.boxes.cls):
                    label = self.model.names[int(cls)]
                    
                    # Convert pixel coordinates to relative percentages [0, 100]
                    # Label Studio polygon expects a list of points [[x1, y1], [x2, y2], ...]
                    points = [
                        [float(x) / image_width * 100, float(y) / image_height * 100]
                        for x, y in mask_xy
                    ]

                    results_list.append({
                        "from_name": from_name,
                        "to_name": to_name,
                        "type": "polygonlabels",
                        "value": {
                            "points": points,
                            "polygonlabels": [label]
                        },
                        "score": float(conf)
                    })
            else:
                # Fallback to bounding boxes if no masks are present
                for box in results.boxes.data.tolist():
                    x1, y1, x2, y2, conf, cls = box
                    label = self.model.names[int(cls)]
                    
                    results_list.append({
                        "from_name": from_name,
                        "to_name": to_name,
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
                "model_version": self.get("model_version")
            })

        return ModelResponse(predictions=predictions)

    def get_first_tag_names(self):
        """Helper to get tag names from the project configuration"""
        if not self.parsed_label_config:
            return None, None, None
        
        for from_name, info in self.parsed_label_config.items():
            return from_name, info['to_name'][0], info['type']
        
        return None, None, None

    def fit(self, event, data, **kwargs):
        """Optional: Called on annotation updates"""
        pass
