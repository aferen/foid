# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog
import cv2


class ObjectDetection(object):
    def detect(self,path):
        im = cv2.imread(path)
        # Create config
        cfg = get_cfg()
        cfg.merge_from_file("configs/COCO-Detection/faster_rcnn_X_101_32x8d_FPN_3x.yaml")
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
        cfg.MODEL.WEIGHTS = "models/model_final_68b088.pkl"
        cfg.MODEL.DEVICE = "cpu"

        # Create predictor
        predictor = DefaultPredictor(cfg)

        # Make prediction
        outputs = predictor(im)

        v = Visualizer(im[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1)
        v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        cv2.imwrite(path, v.get_image()[:, :, ::-1])

        return outputs["instances"],MetadataCatalog.get(cfg.DATASETS.TRAIN[0]).thing_classes

        #cv2.imshow('Picture', v.get_image()[:, :, ::-1])
        #cv2.waitKey(0)

