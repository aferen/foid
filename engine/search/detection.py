# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import ColorMode, Visualizer
from detectron2.data import MetadataCatalog
import cv2
import torch


class ObjectDetection(object):
    def __init__(self, cfg, instance_mode=ColorMode.IMAGE):
        self.metadata = MetadataCatalog.get(
            cfg.DATASETS.TEST[0] if len(cfg.DATASETS.TEST) else "__unused"
        )
        self.cpu_device = torch.device("cpu")
        self.instance_mode = instance_mode
        self.predictor = DefaultPredictor(cfg)

    def detect(self,path):
        im = cv2.imread(path)
        predictions = self.predictor(im)
        return predictions,self.metadata.thing_classes
        # v = Visualizer(im[:, :, ::-1], MetadataCatalog.get(cfg.DATASETS.TRAIN[0]), scale=1)
        # v = v.draw_instance_predictions(outputs["instances"].to("cpu"))
        # cv2.imwrite(path, v.get_image()[:, :, ::-1])

        #return outputs["instances"],
        
        #cv2.imshow('Picture', v.get_image()[:, :, ::-1])
        #cv2.waitKey(0)

