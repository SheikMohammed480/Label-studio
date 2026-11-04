# from typing import List, Dict, Optional
# from label_studio_ml.model import LabelStudioMLBase
# from label_studio_ml.response import ModelResponse
# from ultralytics import YOLO
# import os

# class NewModel(LabelStudioMLBase):
#     """Custom ML Backend model
#     """
    
#     def setup(self):
#         """Load the YOLOv8 model"""
#         model_path =  r"D:\label-studio\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend2\best_door.pt"
#         if not os.path.exists(model_path):
#             raise FileNotFoundError(f"YOLO model file not found at: {model_path}")
       
#         self.model = YOLO(model_path)
#         self.set("model_version", "yolo-v8-custom")

#     def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
#         """ Write your inference logic here
#             :param tasks: [Label Studio tasks in JSON format](https://labelstud.io/guide/task_format.html)
#             :param context: [Label Studio context in JSON format](https://labelstud.io/guide/ml_create#Implement-prediction-logic)
#             :return model_response
#                 ModelResponse(predictions=predictions) with
#                 predictions: [Predictions array in JSON format](https://labelstud.io/guide/export.html#Label-Studio-JSON-format-of-annotated-tasks)
#         """
#         predictions = []
 
#         for task in tasks:
#             image_url = task['data']['image']
#             image_path = self.get_local_path(image_url, task_id=task['id'])
 
#             results = self.model(image_path)[0]  # Get first result from batch
 
#             image_height, image_width = results.orig_shape[:2]
 
#             results_list = []
#             for box in results.boxes.data.tolist():  # YOLO returns [x1, y1, x2, y2, conf, cls]
#                 x1, y1, x2, y2, conf, cls = box
#                 label = self.model.names[int(cls)]
 
#                 # Convert absolute pixel coords to relative percentages
#                 results_list.append({
#                     "from_name": "label",
#                     "to_name": "image",
#                     "type": "rectanglelabels",
#                     "value": {
#                         "x": x1 / image_width * 100,
#                         "y": y1 / image_height * 100,
#                         "width": (x2 - x1) / image_width * 100,
#                         "height": (y2 - y1) / image_height * 100,
#                         "rectanglelabels": [label]
#                     },
#                     "score": float(conf)
#                 })
 
#             predictions.append({
#                 "result": results_list,
#                 "score": float(max([b[4] for b in results.boxes.data.tolist()] or [0])),
#                 "model_version": self.get("model_version")
#             })
        
#         return ModelResponse(predictions=predictions)
    
#     def fit(self, event, data, **kwargs):
#         """
#         This method is called each time an annotation is created or updated
#         You can run your logic here to update the model and persist it to the cache
#         It is not recommended to perform long-running operations here, as it will block the main thread
#         Instead, consider running a separate process or a thread (like RQ worker) to perform the training
#         :param event: event type can be ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
#         :param data: the payload received from the event (check [Webhook event reference](https://labelstud.io/guide/webhook_reference.html))
#         """

#         # use cache to retrieve the data from the previous fit() runs
#         old_data = self.get('my_data')
#         old_model_version = self.get('model_version')
#         print(f'Old data: {old_data}')
#         print(f'Old model version: {old_model_version}')

#         # store new data to the cache
#         self.set('my_data', 'my_new_data_value')
#         self.set('model_version', 'my_new_model_version')
#         print(f'New data: {self.get("my_data")}')
#         print(f'New model version: {self.get("model_version")}')

#         print('fit() completed successfully.')




# from typing import List, Dict, Optional

# from label_studio_ml.model import LabelStudioMLBase
# from label_studio_ml.response import ModelResponse

# import torch
# import numpy as np
# from PIL import Image
# from transformers import SegformerForSemanticSegmentation
# from label_studio_converter.brush import mask2rle


# class NewModel(LabelStudioMLBase):

#     def setup(self):

#         print("Loading trained SegFormer floorplan model...")

#         model_path = r"D:\label-studio\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend2\segformer-floorplan-final.pt"

#         # Create SegFormer architecture
#         self.model = SegformerForSemanticSegmentation.from_pretrained(
#             "nvidia/mit-b1",
#             num_labels=10
#         )

#         # Load trained weights
#         state_dict = torch.load(model_path, map_location="cpu")

#         self.model.load_state_dict(state_dict)
#         print(f"Model weights loaded successfully: {model_path}")

#         self.model.eval()
#         print("Model set to evaluation mode")

#         self.set("model_version", "segformer-floorplan")

#         print("Model loaded successfully")

#     def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs):

#         predictions = []

#         for task in tasks:

#             image_url = task["data"]["image"]
#             image_path = self.get_local_path(image_url)

#             image = Image.open(image_path).convert("RGB")
#             width, height = image.size

#             img = np.array(image) / 255.0
#             img = torch.tensor(img).permute(2,0,1).unsqueeze(0).float()

#             with torch.no_grad():
#                 outputs = self.model(img)

#             mask = outputs.logits.argmax(dim=1).squeeze().cpu().numpy()

#             mask = Image.fromarray(mask.astype(np.uint8))
#             mask = mask.resize((width, height), Image.NEAREST)
#             mask = np.array(mask)

#             rle = mask2rle(mask)

#             result = {
#                 "from_name": "label",
#                 "to_name": "image",
#                 "type": "brushlabels",
#                 "value": {
#                     "format": "rle",
#                     "rle": rle,
#                     "brushlabels": ["floorplan"]
#                 },
#                 "original_width": width,
#                 "original_height": height
#             }
#             confidence = float(np.mean(mask > 0))

#             predictions.append({
#             "result": [result],
#             "score": confidence,
#             "model_version": self.get("model_version")
#         })
#             print(f"result: {result}")
#             print(f"Predicted mask for task {task['id']} with model version {self.get('model_version')}")

#             print(f"Confidence score: {confidence}")

#         return ModelResponse(predictions=predictions)
  







# from typing import List, Dict, Optional
# from label_studio_ml.model import LabelStudioMLBase
# from label_studio_ml.response import ModelResponse
 
# import torch
# from PIL import Image
# import numpy as np
# import base64
# from transformers import SegformerForSemanticSegmentation, SegformerConfig, SegformerImageProcessor
 
# # Define the exact classes your model was trained on
# CLASSES = [
#     "background",
#     "double casement window",
#     "double door",
#     "glass wall",
#     "pocket door",
#     "single casement window",
#     "single door",
#     "sliding door",
#     "wall",
#     "window"
# ]
# id2label = {i: label for i, label in enumerate(CLASSES)}
# label2id = {label: i for i, label in enumerate(CLASSES)}
 
# def create_rle_mask(mask):
#     """
#     Converts a boolean/binary NumPy array (mask) into the 
#     Base64 encoded Run-Length Encoding (RLE) format that Label Studio requires.
#     """
#     mask_flat = mask.flatten(order='C')
#     rle = []
#     last_val = 0
#     count = 0
#     for val in mask_flat:
#         if val != last_val:
#             rle.extend([count, last_val])
#             count = 1
#             last_val = val
#         else:
#             count += 1
#     rle.extend([count, last_val])
#     # Pack into byte stream
#     result = []
#     for i in range(0, len(rle), 2):
#         count = rle[i]
#         val = rle[i + 1]
#         while count > 0:
#             if count > 255:
#                 # Max value in a single byte is 255
#                 current_count = 255
#                 count -= 255
#             else:
#                 current_count = count
#                 count = 0
#             # The structure is [length, values...]
#             result.append(current_count)
#             # 1 for filled (class present), 0 for empty background
#             result.append(1 if val else 0)
#     # Base64 encode the byte array
#     return base64.b64encode(bytearray(result)).decode('utf-8')
 
 
# class NewModel(LabelStudioMLBase):
 
#     def setup(self):
#         print("Loading SegFormer B1 model...")
 
#         model_path = r"D:\label-studio\label-studio-ml-backend\label-studio-ml-backend\my_ml_backend2\segformer-floorplan-final.pt"
#         base_model_id = "nvidia/mit-b1"
 
#         # 1. Load the processor (crucial for resizing/normalizing images correctly!)
#         self.processor = SegformerImageProcessor.from_pretrained(base_model_id)
 
#         # 2. Build the empty architecture configured for our 10 classes
#         config = SegformerConfig.from_pretrained(
#             base_model_id, 
#             num_labels=len(CLASSES),
#             id2label=id2label,
#             label2id=label2id
#         )
#         self.model = SegformerForSemanticSegmentation(config)
 
#         # 3. Load your custom weights into the empty architecture
#         state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
#         self.model.load_state_dict(state_dict)
 
#         self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#         self.model.to(self.device)
#         self.model.eval()
 
#         self.set("model_version", "segformer-floorplan-v1")
 
#     def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
#         predictions = []
 
#         for task in tasks:
#             image_url = task['data']['image']
#             image_path = self.get_local_path(image_url)
 
#             # Load image
#             image = Image.open(image_path).convert("RGB")
#             original_width, original_height = image.size
 
#             # Run through processor and model
#             inputs = self.processor(images=image, return_tensors="pt")
#             inputs = {k: v.to(self.device) for k, v in inputs.items()}
 
#             with torch.no_grad():
#                 outputs = self.model(**inputs)
#                 logits = outputs.logits
 
#             # Resize the logits back to the original image dimensions before argmax
#             upsampled_logits = torch.nn.functional.interpolate(
#                 logits,
#                 size=(original_height, original_width),
#                 mode="bilinear",
#                 align_corners=False,
#             )
 
#             # Get the predicted class for each pixel (shape: height, width)
#             pred_mask = upsampled_logits.argmax(dim=1)[0].cpu().numpy()
 
#             results = []
#             # Label Studio expects a separate RLE mask for each individual class detected
#             unique_classes = np.unique(pred_mask)
#             for cls_idx in unique_classes:
#                 if cls_idx == 0:
#                     continue # Skip background
#                 class_name = CLASSES[cls_idx]
#                 # Create a binary mask where ONLY this specific class is True
#                 binary_mask = (pred_mask == cls_idx)
#                 # Convert the NumPy binary mask into the Base64 RLE format Label Studio requires
#                 rle_base64_string = create_rle_mask(binary_mask)
 
#                 # IMPORTANT: These must match the 'name' attributes in your Label Studio XML configuration exactly!
#                 results.append({
#                     "from_name": "label", # Make sure this matches your XML <BrushLabels name="label"...>
#                     "to_name": "image",   # Make sure this matches your XML <Image name="image"...>
#                     "type": "brushlabels",
#                     "value": {
#                         "format": "rle",
#                         "rle": rle_base64_string,
#                         "brushlabels": [class_name]
#                     }
#                 })
 
#             predictions.append({
#                 "result": results,
#                 "model_version": self.get("model_version")
#             })
 
#         return ModelResponse(predictions=predictions)




"""
SegFormer Semantic Segmentation - Label Studio ML Backend
=========================================================

ROOT CAUSE of "array buffer allocation failed" (confirmed by inspecting
the broken auto_annotate.json vs a working manual annotation):

  The old create_rle_mask() returned a BASE64 STRING such as "/wD/AP8A...".
  When Python's json.dumps serialised this, Label Studio stored it as a
  JSON string.  The JS frontend then iterated over the string characters
  (each char is one element) and called charCodeAt() on every character,
  producing thousands of random integer "counts".  The total buffer size
  it tried to allocate was charCodeSum x canvas_width x canvas_height,
  which immediately overflows -> "array buffer allocation failed".
  Even if the allocation somehow succeeded, reading [count, value] pairs
  from character codes produces nonsense -> "can't read past EOF".

  Additionally, original_width / original_height were missing from the
  result object, and the result had no `id` or `image_rotation` fields,
  which caused secondary rendering failures.

CORRECT format (verified against working manual annotations):
  result = {
      "id": "<unique 10-char string>",           <- required
      "from_name": "label",
      "to_name": "image",
      "type": "brushlabels",
      "image_rotation": 0,                       <- required
      "original_width": <int>,                   <- required at this level
      "original_height": <int>,                  <- required at this level
      "value": {
          "format": "rle",
          "rle": [count, val, count, val, ...],  <- LIST OF INTS, NOT a string
          "brushlabels": ["<class_name>"],
      }
  }

  Prediction-level score = mean per-class confidence score (0.0-1.0).
"""

from typing import List, Dict, Optional
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse

import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import random
import string
import logging
import time

# ──────────────────────────────────────────────────────────────────────────────
#  Logging  (console + file)
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("segformer_debug.log", mode="a"),
    ],
)
logger = logging.getLogger("SegFormerModel")

from transformers import (
    SegformerForSemanticSegmentation,
    SegformerConfig,
    SegformerImageProcessor,
)

# ──────────────────────────────────────────────────────────────────────────────
#  Class definitions  (must match your training labels exactly)
# ──────────────────────────────────────────────────────────────────────────────
CLASSES = [
    "background",
    "double casement window",
    "double door",
    "glass wall",
    "pocket door",
    "single casement window",
    "single door",
    "sliding door",
    "wall",
    "window",
]
id2label = {i: label for i, label in enumerate(CLASSES)}
label2id = {label: i for i, label in enumerate(CLASSES)}
logger.info("CLASSES loaded: %s", CLASSES)


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _random_id(length: int = 10) -> str:
    """Generate a random alphanumeric ID matching Label Studio style."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


from rle_utils import create_rle_mask

# def create_rle_mask(mask: np.ndarray) -> list:
#     """
#     Encode a boolean/uint8 binary mask as Label Studio RLE.
# 
#     Returns
#     -------
#     A plain Python list of integers: [count0, val0, count1, val1, ...]
#       count : consecutive pixel run length  (1-255 per entry)
#       val   : 0 = background, 1 = foreground
# 
#     The mask is flattened row-major (C order) matching LS canvas coords.
# 
#     NEVER return a base64 string here.
#     If you return a string, Python json serialises it as a JSON string,
#     the JS frontend splits it into characters, each character's charCode
#     becomes a huge run-length count, and the buffer allocation explodes.
#     """
#     mask_flat = mask.flatten(order="C").astype(np.uint8)
#     n = len(mask_flat)
#     rle: list = []
#     i = 0
#     while i < n:
#         val = int(mask_flat[i])
#         count = 1
#         # Cap each run at 255 so the count fits in one byte
#         # when the frontend reconstructs the pixel buffer.
#         while i + count < n and mask_flat[i + count] == val and count < 255:
#             count += 1
#         rle.append(count)
#         rle.append(val)
#         i += count
#     return rle


# ──────────────────────────────────────────────────────────────────────────────
#  Label Studio ML Backend
# ──────────────────────────────────────────────────────────────────────────────
class NewModel(LabelStudioMLBase):

    # ── Model initialisation ────────────────────────────────────────────────
    def setup(self):
        logger.info("=" * 70)
        logger.info("setup() called - loading SegFormer model")

        model_path    = (
            r"D:\label-studio\label-studio-ml-backend"
            r"\label-studio-ml-backend\my_ml_backend2"
            r"\segformer-floorplan-final.pt"
        )
        base_model_id = "nvidia/mit-b1"

        logger.debug("model_path    : %s", model_path)
        logger.debug("base_model_id : %s", base_model_id)
        logger.debug("num_labels    : %d", len(CLASSES))

        # 1. Image processor
        logger.info("Loading SegformerImageProcessor from '%s'", base_model_id)
        self.processor = SegformerImageProcessor.from_pretrained(base_model_id)
        logger.info("Processor loaded OK")

        # 2. Model architecture
        logger.info("Building SegformerForSemanticSegmentation config")
        config = SegformerConfig.from_pretrained(
            base_model_id,
            num_labels=len(CLASSES),
            id2label=id2label,
            label2id=label2id,
        )
        self.model = SegformerForSemanticSegmentation(config)
        logger.info("Model architecture created OK")

        # 3. Custom weights
        logger.info("Loading custom weights from '%s'", model_path)
        state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
        self.model.load_state_dict(state_dict)
        logger.info("Custom weights loaded OK")

        # 4. Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("Using device: %s", self.device)
        self.model.to(self.device)
        self.model.eval()
        logger.info("Model moved to %s, set to eval", self.device)

        self.set("model_version", "segformer-floorplan-v1")
        logger.info("setup() complete  model_version=segformer-floorplan-v1")
        logger.info("=" * 70)

    # ── Inference ───────────────────────────────────────────────────────────
    def predict(
        self,
        tasks: List[Dict],
        context: Optional[Dict] = None,
        **kwargs,
    ) -> ModelResponse:

        logger.info("predict() called  num_tasks=%d", len(tasks))
        predictions = []

        for task_idx, task in enumerate(tasks):
            t_start   = time.time()
            task_id   = task.get("id", f"unknown-{task_idx}")
            image_url = task["data"]["image"]

            logger.info(
                "-- Task %d/%d (id=%s) --",
                task_idx + 1, len(tasks), task_id,
            )
            logger.debug("  image_url : %s", image_url)

            # ── 1. Load image ────────────────────────────────────────────
            try:
                image_path = self.get_local_path(image_url)
                logger.debug("  local_path : %s", image_path)
            except Exception as exc:
                logger.error("  get_local_path FAILED: %s", exc, exc_info=True)
                raise

            try:
                image = Image.open(image_path).convert("RGB")
                original_width, original_height = image.size   # (W, H)
                logger.debug(
                    "  Image: W=%d  H=%d  mode=%s",
                    original_width, original_height, image.mode,
                )
            except Exception as exc:
                logger.error("  Image.open FAILED: %s", exc, exc_info=True)
                raise

            # ── 2. Preprocess ────────────────────────────────────────────
            try:
                inputs = self.processor(images=image, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                logger.debug(
                    "  Processor output keys=%s  shapes=%s",
                    list(inputs.keys()),
                    {k: tuple(v.shape) for k, v in inputs.items()},
                )
            except Exception as exc:
                logger.error("  Processor FAILED: %s", exc, exc_info=True)
                raise

            # ── 3. Forward pass ──────────────────────────────────────────
            try:
                with torch.no_grad():
                    outputs = self.model(**inputs)
                logits = outputs.logits          # (1, C, H', W')
                logger.debug(
                    "  Logits shape=%s  device=%s  dtype=%s",
                    tuple(logits.shape), logits.device, logits.dtype,
                )
            except Exception as exc:
                logger.error("  Forward pass FAILED: %s", exc, exc_info=True)
                raise

            # ── 4. Upsample to original resolution ──────────────────────
            try:
                upsampled = F.interpolate(
                    logits,
                    size=(original_height, original_width),
                    mode="bilinear",
                    align_corners=False,
                )
                logger.debug("  Upsampled logits shape=%s", tuple(upsampled.shape))
            except Exception as exc:
                logger.error("  interpolate FAILED: %s", exc, exc_info=True)
                raise

            # ── 5. Probabilities + argmax ────────────────────────────────
            # softmax over class dimension -> per-pixel class probabilities
            probabilities = F.softmax(upsampled, dim=1)        # (1, C, H, W)
            pred_mask     = upsampled.argmax(dim=1)[0].cpu().numpy()  # (H, W) int
            prob_map      = probabilities[0].cpu().numpy()             # (C, H, W) float

            unique_classes = np.unique(pred_mask).tolist()
            logger.debug(
                "  pred_mask shape=%s dtype=%s unique_ids=%s",
                pred_mask.shape, pred_mask.dtype, unique_classes,
            )

            # ── 6. Build per-class result objects ────────────────────────
            results      = []
            class_scores = []

            for cls_idx in unique_classes:

                # Skip background (class 0)
                if cls_idx == 0:
                    logger.debug("  [skip] background cls_idx=0")
                    continue

                class_name  = CLASSES[cls_idx]
                binary_mask = (pred_mask == cls_idx)      # bool (H, W)
                pixel_count = int(binary_mask.sum())

                # ── Per-class confidence score ───────────────────────────
                # Mean softmax probability on the predicted pixels for this
                # class.  Range 0.0-1.0; higher = more confident placement.
                class_prob_map  = prob_map[cls_idx]       # (H, W) floats
                mean_confidence = (
                    float(class_prob_map[binary_mask].mean())
                    if pixel_count > 0
                    else 0.0
                )
                class_scores.append(mean_confidence)

                logger.debug(
                    "  Class idx=%d  name='%s'  pixels=%d  confidence=%.4f",
                    cls_idx, class_name, pixel_count, mean_confidence,
                )

                # ── RLE encode ──────────────────────────────────────────
                try:
                    rle_ints = create_rle_mask(binary_mask)
                except Exception as exc:
                    logger.error(
                        "  create_rle_mask FAILED for '%s': %s",
                        class_name, exc, exc_info=True,
                    )
                    raise

                logger.debug(
                    "  RLE '%s': list_len=%d (bitstream bytes)  first10=%s",
                    class_name,
                    len(rle_ints),
                    rle_ints[:10],
                )

                # ── Sanity check: round-trip pixel count ─────────────────
                # Legacy check removed as it doesn't apply to bitstream RLE
                # decoded_px  = sum(rle_ints[i] for i in range(0, len(rle_ints), 2))
                # expected_px = original_width * original_height * 4

                # ── Assemble result dict ─────────────────────────────────
                # Field inventory verified against Label Studio working
                # manual annotation (normal_mask_output_from_label_Studio.json):
                #   id, from_name, to_name, type, image_rotation,
                #   original_width, original_height, value.format,
                #   value.rle (list of ints), value.brushlabels
                region_id  = _random_id(10)
                result_obj = {
                    # routing
                    "id"             : region_id,
                    "from_name"      : "label",        # <BrushLabels name="label">
                    "to_name"        : "image",        # <Image name="image">
                    "type"           : "brushlabels",

                    # geometry - MUST be at result level, not inside value
                    "image_rotation" : 0,
                    "original_width" : original_width,
                    "original_height": original_height,

                    # mask payload
                    "value": {
                        "format"      : "rle",
                        "rle"         : rle_ints,      # LIST OF INTS
                        "brushlabels" : [class_name],
                    },
                }
                results.append(result_obj)

                logger.debug(
                    "  Result appended: id=%s  class='%s'  "
                    "W=%d  H=%d  confidence=%.4f",
                    region_id, class_name,
                    original_width, original_height, mean_confidence,
                )

            # ── 7. Overall prediction score ──────────────────────────────
            # Average confidence across all detected (non-background) classes.
            overall_score = float(np.mean(class_scores)) if class_scores else 0.0

            elapsed = time.time() - t_start
            logger.info(
                "  Task %d done: regions=%d  score=%.4f  elapsed=%.2fs",
                task_idx, len(results), overall_score, elapsed,
            )

            predictions.append(
                {
                    "result"       : results,
                    "score"        : overall_score,    # overall prediction confidence
                    "model_version": self.get("model_version"),
                }
            )

        logger.info("predict() complete  total_predictions=%d", len(predictions))
        return ModelResponse(predictions=predictions)

